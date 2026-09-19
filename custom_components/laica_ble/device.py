"""Bluetooth device adapter for LAICA/YoHealth scales."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import logging

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

    def update(
        self, service_info: BluetoothServiceInfoBleak
    ) -> LaicaMeasurementUpdate | None:
        """Parse an advertisement and return only accepted final measurements."""
        frame = parse_manufacturer_data(service_info.manufacturer_data)
        if frame is None:
            return None

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

        _LOGGER.debug(
            "Accepted final YoHealth measurement: weight=%.2f kg, "
            "impedance=%s, status=0x%02X, mode=0x%02X",
            frame.weight_kg,
            frame.impedance if frame.impedance is not None else "unavailable",
            frame.status,
            frame.mode.raw,
        )

        return LaicaMeasurementUpdate(frame=frame, metrics=metrics, age=age)
