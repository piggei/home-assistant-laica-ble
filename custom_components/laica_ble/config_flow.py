"""Config flow for LAICA BLE."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, override

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_ADDRESS, UnitOfLength
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BIRTH_DATE,
    CONF_HEIGHT_CM,
    CONF_SCALE_MODEL,
    CONF_SEX,
    DEFAULT_SCALE_MODEL,
    DOMAIN,
    SEX_FEMALE,
    SEX_MALE,
)
from .profile import parse_birth_date
from .protocol import is_supported_manufacturer_data


@dataclass(frozen=True, slots=True)
class Discovery:
    """One supported Bluetooth discovery."""

    title: str
    info: BluetoothServiceInfoBleak


def _device_title(info: BluetoothServiceInfoBleak) -> str:
    name = info.name or "YoHealth"
    return f"{name} ({info.address})"


def _profile_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}

    birth_date_key = (
        vol.Required(CONF_BIRTH_DATE, default=defaults[CONF_BIRTH_DATE])
        if CONF_BIRTH_DATE in defaults
        else vol.Required(CONF_BIRTH_DATE)
    )

    return vol.Schema(
        {
            vol.Required(
                CONF_SEX,
                default=defaults.get(CONF_SEX, SEX_MALE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[SEX_MALE, SEX_FEMALE],
                    translation_key="sex",
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            birth_date_key: selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                )
            ),
            vol.Required(
                CONF_HEIGHT_CM,
                default=defaults.get(CONF_HEIGHT_CM, 175.0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=80,
                    max=250,
                    step=0.1,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement=UnitOfLength.CENTIMETERS,
                )
            ),
            vol.Required(
                CONF_SCALE_MODEL,
                default=defaults.get(CONF_SCALE_MODEL, DEFAULT_SCALE_MODEL),
            ): selector.TextSelector(),
        }
    )





def _profile_errors(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate profile fields that selectors cannot fully validate."""
    errors: dict[str, str] = {}
    birth_date = parse_birth_date(str(user_input[CONF_BIRTH_DATE]))
    if birth_date is None:
        errors[CONF_BIRTH_DATE] = "invalid_birth_date"
        return errors

    today = dt_util.now().date()
    if birth_date > today:
        errors[CONF_BIRTH_DATE] = "birth_date_in_future"
        return errors

    age = today.year - birth_date.year - int(
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )
    if age > 130:
        errors[CONF_BIRTH_DATE] = "invalid_birth_date"

    model = str(user_input[CONF_SCALE_MODEL]).strip()
    if not model:
        errors[CONF_SCALE_MODEL] = "model_required"

    return errors


class LaicaBleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle LAICA BLE configuration."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovery: Discovery | None = None
        self._discovered: dict[str, Discovery] = {}

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> LaicaBleOptionsFlow:
        """Return the options flow."""
        return LaicaBleOptionsFlow()

    @override
    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle automatic Bluetooth discovery."""
        if not is_supported_manufacturer_data(discovery_info.manufacturer_data):
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovery = Discovery(_device_title(discovery_info), discovery_info)
        self.context["title_placeholders"] = {"name": self._discovery.title}
        return await self.async_step_profile()

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow manual setup by selecting a currently advertising scale."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            discovery = self._discovered[address]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            self._discovery = discovery
            self.context["title_placeholders"] = {"name": discovery.title}
            return await self.async_step_profile()

        configured = self._async_current_ids(include_ignore=False)
        for info in async_discovered_service_info(self.hass, False):
            if info.address in configured or info.address in self._discovered:
                continue
            if is_supported_manufacturer_data(info.manufacturer_data):
                self._discovered[info.address] = Discovery(_device_title(info), info)

        if not self._discovered:
            return self.async_abort(reason="no_devices_found")

        titles = {
            address: discovery.title
            for address, discovery in self._discovered.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(titles)}),
        )

    async def async_step_profile(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect the one local profile used for body-composition formulas."""
        assert self._discovery is not None
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _profile_errors(user_input)
            if not errors:
                model = str(user_input[CONF_SCALE_MODEL]).strip()
                title = model if model.lower().startswith("laica") else f"LAICA {model}"
                birth_date = parse_birth_date(str(user_input[CONF_BIRTH_DATE]))
                assert birth_date is not None
                return self.async_create_entry(
                    title=title,
                    data={CONF_ADDRESS: self._discovery.info.address},
                    options={
                        CONF_SEX: user_input[CONF_SEX],
                        CONF_BIRTH_DATE: birth_date.isoformat(),
                        CONF_HEIGHT_CM: float(user_input[CONF_HEIGHT_CM]),
                        CONF_SCALE_MODEL: model,
                    },
                )

        return self.async_show_form(
            step_id="profile",
            data_schema=_profile_schema(),
            errors=errors,
            description_placeholders={"name": self._discovery.title},
        )


class LaicaBleOptionsFlow(OptionsFlowWithReload):
    """Edit the local calculation profile."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage LAICA BLE options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _profile_errors(user_input)
            if not errors:
                model = str(user_input[CONF_SCALE_MODEL]).strip()
                title = model if model.lower().startswith("laica") else f"LAICA {model}"
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=title,
                )
                birth_date = parse_birth_date(str(user_input[CONF_BIRTH_DATE]))
                assert birth_date is not None
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_SEX: user_input[CONF_SEX],
                        CONF_BIRTH_DATE: birth_date.isoformat(),
                        CONF_HEIGHT_CM: float(user_input[CONF_HEIGHT_CM]),
                        CONF_SCALE_MODEL: model,
                    },
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_profile_schema(dict(self.config_entry.options)),
            errors=errors,
        )
