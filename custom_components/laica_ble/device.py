"""Bluetooth device adapter for LAICA/YoHealth scales."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.util import dt as dt_util

from .algorithm import BodyMetrics, UserProfile, age_on_date, calculate_body_metrics
from .protocol import FinalMeasurementGate, YoHealthFrame, parse_manufacturer_data

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LaicaMeasurementUpdate:
    """One accepted final weighing."""

    frame: YoHealthFrame
    metrics: BodyMetrics | None
    age: int


class LaicaBluetoothDeviceData:
    """Turn BLE advertisements into final weighing updates."""

    def __init__(self, profile: UserProfile) -> None:
        profile.validate()
        self._profile = profile
        self._gate = FinalMeasurementGate()
        self._last_status: int | None = None
        self._last_mode_raw: int | None = None
        self._last_has_impedance: bool | None = None
        self._accepted_final_count = 0

    def update(
        self, service_info: BluetoothServiceInfoBleak
    ) -> LaicaMeasurementUpdate | None:
        """Parse an advertisement and return only accepted final measurements."""
        frame = parse_manufacturer_data(service_info.manufacturer_data)
        if frame is None:
            return None

        # Retain only non-sensitive protocol metadata for diagnostics.
        self._last_status = frame.status
        self._last_mode_raw = frame.mode.raw
        self._last_has_impedance = frame.impedance is not None

        # We intentionally observe 0x80/0x82 only to re-arm the session gate.
        # They do not update entities in v0.1.x.
        if not self._gate.accept(frame):
            return None

        today: date = dt_util.now().date()
        age = age_on_date(self._profile.birth_date, today)

        metrics: BodyMetrics | None = None
        if frame.impedance is not None:
            metrics = calculate_body_metrics(
                weight_kg=frame.weight_kg,
                impedance=frame.impedance,
                height_cm=self._profile.height_cm,
                age=age,
                sex=self._profile.sex,
            )

        self._accepted_final_count += 1

        _LOGGER.debug(
            "Accepted final YoHealth measurement: weight=%.2f kg, "
            "impedance=%s, status=0x%02X, mode=0x%02X",
            frame.weight_kg,
            frame.impedance if frame.impedance is not None else "unavailable",
            frame.status,
            frame.mode.raw,
        )

        return LaicaMeasurementUpdate(frame=frame, metrics=metrics, age=age)

    def diagnostics(self) -> dict[str, int | bool | str | None]:
        """Return non-sensitive protocol diagnostics.

        Deliberately excludes weight, impedance value, profile values and the
        raw payload because diagnostics files should not contain personal data.
        """
        return {
            "last_protocol_status": (
                f"0x{self._last_status:02X}" if self._last_status is not None else None
            ),
            "last_mode": (
                f"0x{self._last_mode_raw:02X}"
                if self._last_mode_raw is not None
                else None
            ),
            "last_frame_had_impedance": self._last_has_impedance,
            "accepted_final_measurements": self._accepted_final_count,
        }

