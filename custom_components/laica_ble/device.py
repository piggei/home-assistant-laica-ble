"""Bluetooth device adapter for LAICA/YoHealth scales."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .algorithm import BodyMetrics, UserProfile, age_on_date, calculate_body_metrics
from .const import (
    FINAL_STATUS,
    REALTIME_STATUS,
    STABLE_WEIGHT_DELAY_SECONDS,
    STABLE_WEIGHT_STATUS,
)
from .protocol import (
    FinalMeasurementGate,
    StableWeightGate,
    YoHealthFrame,
    parse_manufacturer_data,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LaicaMeasurementUpdate:
    """One accepted weighing."""

    frame: YoHealthFrame
    metrics: BodyMetrics | None
    age: int


class LaicaBluetoothDeviceData:
    """Turn BLE advertisements into complete or stable weight-only updates."""

    def __init__(self, hass: HomeAssistant, profile: UserProfile) -> None:
        profile.validate()
        self._hass = hass
        self._profile = profile
        self._final_gate = FinalMeasurementGate()
        self._stable_gate = StableWeightGate()
        self._delayed_publisher: Callable[[LaicaMeasurementUpdate], None] | None = None
        self._pending_stable_frame: YoHealthFrame | None = None
        self._pending_cancel: CALLBACK_TYPE | None = None
        self._last_status: int | None = None
        self._last_mode_raw: int | None = None
        self._last_has_impedance: bool | None = None
        self._accepted_final_count = 0
        self._accepted_weight_only_count = 0

    def set_delayed_publisher(
        self, publisher: Callable[[LaicaMeasurementUpdate], None]
    ) -> None:
        """Set callback used to publish a deferred 0x82 measurement."""
        self._delayed_publisher = publisher

    def _measurement_from_frame(self, frame: YoHealthFrame) -> LaicaMeasurementUpdate:
        """Build an accepted measurement from a validated frame."""
        today: date = dt_util.now().date()
        age = age_on_date(self._profile.birth_date, today)

        metrics: BodyMetrics | None = None
        if frame.impedance is not None and frame.status == FINAL_STATUS:
            metrics = calculate_body_metrics(
                weight_kg=frame.weight_kg,
                impedance=frame.impedance,
                height_cm=self._profile.height_cm,
                age=age,
                sex=self._profile.sex,
            )

        return LaicaMeasurementUpdate(frame=frame, metrics=metrics, age=age)

    def _cancel_pending_weight(self) -> None:
        if self._pending_cancel is not None:
            self._pending_cancel()
            self._pending_cancel = None
        self._pending_stable_frame = None

    @callback
    def _emit_pending_weight(self, _now: datetime) -> None:
        """Publish a stable 0x82 weight if no full 0x86 frame superseded it."""
        self._pending_cancel = None
        frame = self._pending_stable_frame
        self._pending_stable_frame = None
        if frame is None or not self._stable_gate.accept_pending():
            return
        if self._delayed_publisher is None:
            _LOGGER.warning("Cannot publish deferred LAICA weight: no publisher set")
            return

        self._accepted_weight_only_count += 1
        update = self._measurement_from_frame(frame)
        _LOGGER.debug(
            "Accepted stable weight-only YoHealth measurement: weight=%.2f kg, "
            "status=0x%02X, mode=0x%02X",
            frame.weight_kg,
            frame.status,
            frame.mode.raw,
        )
        self._delayed_publisher(update)

    def update(
        self, service_info: BluetoothServiceInfoBleak
    ) -> LaicaMeasurementUpdate | None:
        """Parse an advertisement and return an immediate accepted measurement."""
        frame = parse_manufacturer_data(service_info.manufacturer_data)
        if frame is None:
            return None

        self._last_status = frame.status
        self._last_mode_raw = frame.mode.raw
        self._last_has_impedance = frame.impedance is not None

        accept_final = self._final_gate.accept(frame)
        schedule_stable = self._stable_gate.observe(frame)

        if frame.status == REALTIME_STATUS:
            self._cancel_pending_weight()
            return None

        if frame.status == STABLE_WEIGHT_STATUS:
            # Keep the newest repeated 0x82 frame, but start the hold-off timer
            # only once so continuous advertisements cannot postpone it forever.
            if self._stable_gate.pending:
                self._pending_stable_frame = frame
            if schedule_stable and self._pending_cancel is None:
                self._pending_cancel = async_call_later(
                    self._hass,
                    STABLE_WEIGHT_DELAY_SECONDS,
                    self._emit_pending_weight,
                )
            return None

        if frame.status != FINAL_STATUS:
            return None

        # A full 0x86 measurement always wins over a pending 0x82 candidate.
        self._cancel_pending_weight()
        if not accept_final:
            return None

        self._accepted_final_count += 1
        update = self._measurement_from_frame(frame)
        _LOGGER.debug(
            "Accepted final YoHealth measurement: weight=%.2f kg, "
            "impedance=%s, status=0x%02X, mode=0x%02X",
            frame.weight_kg,
            frame.impedance if frame.impedance is not None else "unavailable",
            frame.status,
            frame.mode.raw,
        )
        return update

    @callback
    def stop(self) -> None:
        """Cancel a pending delayed weight update when the entry unloads."""
        self._cancel_pending_weight()

    def diagnostics(self) -> dict[str, int | bool | str | None]:
        """Return non-sensitive protocol diagnostics."""
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
            "stable_weight_pending": self._stable_gate.pending,
            "accepted_final_measurements": self._accepted_final_count,
            "accepted_weight_only_measurements": self._accepted_weight_only_count,
        }
