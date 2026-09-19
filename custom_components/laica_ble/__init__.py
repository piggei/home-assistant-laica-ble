"""LAICA BLE integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .algorithm import UserProfile
from .const import CONF_BIRTH_DATE, CONF_HEIGHT_CM, CONF_SEX
from .device import LaicaBluetoothDeviceData, LaicaMeasurementUpdate

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


@dataclass(slots=True)
class LaicaRuntimeData:
    """Runtime objects shared by platforms and diagnostics."""

    coordinator: PassiveBluetoothProcessorCoordinator[LaicaMeasurementUpdate | None]
    device_data: LaicaBluetoothDeviceData


def _profile_from_entry(entry: ConfigEntry) -> UserProfile:
    """Build the local calculation profile from config-entry options."""
    return UserProfile(
        sex=str(entry.options[CONF_SEX]),
        birth_date=date.fromisoformat(str(entry.options[CONF_BIRTH_DATE])),
        height_cm=float(entry.options[CONF_HEIGHT_CM]),
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LAICA BLE from a config entry."""
    address = entry.unique_id
    assert address is not None

    device_data = LaicaBluetoothDeviceData(hass, _profile_from_entry(entry))

    coordinator: PassiveBluetoothProcessorCoordinator[
        LaicaMeasurementUpdate | None
    ] = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        update_method=device_data.update,
        connectable=False,
    )

    device_data.set_delayed_publisher(coordinator.async_set_updated_data)

    entry.runtime_data = LaicaRuntimeData(
        coordinator=coordinator,
        device_data=device_data,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start listening only after entity platforms registered their processors.
    entry.async_on_unload(device_data.stop)
    entry.async_on_unload(coordinator.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a LAICA BLE config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Make a removed scale immediately eligible for Bluetooth rediscovery."""
    address = entry.unique_id
    if address:
        bluetooth.async_rediscover_address(hass, address)
