"""Diagnostics support for LAICA BLE."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BIRTH_DATE,
    CONF_HEIGHT_CM,
    CONF_SCALE_MODEL,
    CONF_SEX,
    FINAL_STATUS,
    PROTOCOL_NAME,
    STABLE_WEIGHT_DELAY_SECONDS,
    STABLE_WEIGHT_STATUS,
    YOHEALTH_COMPANY_ID,
)

# Profile data and the Bluetooth address can identify a person/device. They are
# intentionally redacted from exported diagnostics.
TO_REDACT = [
    "address",
    CONF_BIRTH_DATE,
    CONF_HEIGHT_CM,
    CONF_SEX,
]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return privacy-preserving diagnostics for a config entry."""
    runtime = entry.runtime_data

    return {
        "config_entry": {
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "integration": {
            "scale_model": entry.options.get(CONF_SCALE_MODEL),
            "protocol": PROTOCOL_NAME,
            "company_id": f"0x{YOHEALTH_COMPANY_ID:04X}",
            "accepted_final_status": f"0x{FINAL_STATUS:02X}",
            "accepted_stable_weight_status": f"0x{STABLE_WEIGHT_STATUS:02X}",
            "stable_weight_delay_seconds": STABLE_WEIGHT_DELAY_SECONDS,
            "policy": "0x86_complete_or_deferred_0x82_weight_only",
        },
        "bluetooth": runtime.device_data.diagnostics(),
    }
