"""YoHealth BLE advertisement parser used by LAICA BLE scales."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass

from .const import (
    FINAL_REARM_TIMEOUT_SECONDS,
    FINAL_STATUS,
    REALTIME_STATUS,
    STABLE_WEIGHT_STATUS,
    YOHEALTH_COMPANY_ID,
)

# Home Assistant/Bleak strips the 2-byte Company ID from Manufacturer Data and
# exposes it as the dict key. The remaining YoHealth payload is therefore:
#
#   09 FF WW WW ZZ ZZ SS FF FF MM CC AA
#   |----| |---| |---|  | |----| |  |  |
#   header weight health st unk  mode ck end
#
# where weight/health are big-endian 16-bit values.
PAYLOAD_LEN = 12
HEADER = bytes((0x09, 0xFF))
TERMINATOR = 0xAA

# Company ID bytes as they appear on air / in NimBLE Manufacturer Data.
COMPANY_ID_LE_BYTES = bytes((0x02, 0xA1))

INVALID_IMPEDANCE = {0x0000, 0xFFFF}


@dataclass(frozen=True, slots=True)
class DeviceMode:
    """Decoded YoHealth mode/precision byte."""

    raw: int
    bcd_code: int | None
    device_type: str
    precision_digits: int | None


@dataclass(frozen=True, slots=True)
class YoHealthFrame:
    """Validated YoHealth manufacturer payload."""

    weight_raw: int
    weight_kg: float
    impedance: int | None
    status: int
    mode: DeviceMode
    checksum: int
    payload: bytes

    @property
    def has_body_composition(self) -> bool:
        """Return True when a usable impedance value is present."""
        return self.impedance is not None


def _read_be16(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def decode_mode(raw: int) -> DeviceMode:
    """Decode the historical YoHealth BCD-style device mode byte.

    Observed PS7002 value: 0x21 => body-composition scale, 0.1 kg precision.
    Historical application logic treated 11..19 as weight-only and 21..29 as
    body-composition device families; the units digit is the weight precision.
    """
    tens = (raw >> 4) & 0x0F
    ones = raw & 0x0F
    if tens > 9 or ones > 9:
        return DeviceMode(raw, None, "unknown", None)

    code = tens * 10 + ones
    if 10 < code < 20:
        device_type = "weight_only"
    elif 20 < code < 30:
        device_type = "body_composition"
    else:
        device_type = "unknown"

    precision = ones if ones in (1, 2) else None
    return DeviceMode(raw, code, device_type, precision)


def decode_weight(weight_raw: int, mode: DeviceMode) -> float:
    """Decode raw weight according to the YoHealth precision digit."""
    if mode.precision_digits == 2:
        return weight_raw / 100.0
    # PS7002 uses 0x21 => one decimal place. Unknown mode falls back to the
    # directly validated PS7002 /10 behavior rather than guessing another unit.
    return weight_raw / 10.0


def calculate_checksum(payload: bytes) -> int:
    """Calculate the YoHealth checksum for a Home Assistant payload.

    The protocol checksum is the low byte of the sum of the two Company ID bytes
    plus the first ten bytes of the post-company-id payload (through mode byte).
    """
    if len(payload) != PAYLOAD_LEN:
        raise ValueError(f"Expected {PAYLOAD_LEN} payload bytes")
    return (sum(COMPANY_ID_LE_BYTES) + sum(payload[:10])) & 0xFF


def parse_payload(payload: bytes) -> YoHealthFrame | None:
    """Validate and decode a post-Company-ID YoHealth payload."""
    if len(payload) != PAYLOAD_LEN:
        return None
    if payload[:2] != HEADER or payload[-1] != TERMINATOR:
        return None
    if calculate_checksum(payload) != payload[10]:
        return None

    mode = decode_mode(payload[9])
    weight_raw = _read_be16(payload, 2)
    health_raw = _read_be16(payload, 4)

    return YoHealthFrame(
        weight_raw=weight_raw,
        weight_kg=decode_weight(weight_raw, mode),
        impedance=None if health_raw in INVALID_IMPEDANCE else health_raw,
        status=payload[6],
        mode=mode,
        checksum=payload[10],
        payload=payload,
    )


def parse_manufacturer_data(
    manufacturer_data: Mapping[int, bytes],
) -> YoHealthFrame | None:
    """Extract and parse YoHealth data from Bleak manufacturer data."""
    payload = manufacturer_data.get(YOHEALTH_COMPANY_ID)
    if payload is None:
        return None
    return parse_payload(bytes(payload))


def is_discovery_manufacturer_data(manufacturer_data: Mapping[int, bytes]) -> bool:
    """Return whether an advertisement identifies a YoHealth-compatible scale.

    Discovery intentionally uses only the public Company ID and protocol header.
    A scale can advertise transient/incomplete frames while waking; requiring a
    fully checksum-valid measurement here can cause Home Assistant to consume the
    Bluetooth discovery match and then abort the flow before a final frame arrives.
    Runtime measurements remain strictly validated by ``parse_manufacturer_data``.
    """
    payload = manufacturer_data.get(YOHEALTH_COMPANY_ID)
    if payload is None:
        return False
    return bytes(payload).startswith(HEADER)


def is_supported_manufacturer_data(manufacturer_data: Mapping[int, bytes]) -> bool:
    """Return whether an advertisement contains a valid YoHealth frame."""
    return parse_manufacturer_data(manufacturer_data) is not None


class StableWeightGate:
    """Track one deferred 0x82 weight-only candidate per weighing session."""

    def __init__(self) -> None:
        self._pending = False
        self._emitted = False

    @property
    def pending(self) -> bool:
        """Return whether a stable weight-only candidate is pending."""
        return self._pending

    def observe(self, frame: YoHealthFrame) -> bool:
        """Return True when a new 0x82 candidate should be scheduled.

        0x80 starts/re-arms a weighing session. A full 0x86 frame cancels any
        pending weight-only candidate and prevents a later 0x82 duplicate from
        being emitted in the same session.
        """
        if frame.status == REALTIME_STATUS:
            self._pending = False
            self._emitted = False
            return False

        if frame.status == FINAL_STATUS:
            self._pending = False
            self._emitted = True
            return False

        if frame.status != STABLE_WEIGHT_STATUS:
            return False

        if self._pending or self._emitted:
            return False

        self._pending = True
        return True

    def accept_pending(self) -> bool:
        """Consume the pending 0x82 candidate exactly once."""
        if not self._pending or self._emitted:
            return False
        self._pending = False
        self._emitted = True
        return True


class FinalMeasurementGate:
    """Emit only one final 0x86 frame per weighing session.

    Repeated advertisements are normal. Any valid non-final protocol frame
    re-arms the gate. A timeout also re-arms it if the Bluetooth scanner missed
    the preceding realtime/stable transition of a later weighing.
    """

    def __init__(self, rearm_timeout: float = FINAL_REARM_TIMEOUT_SECONDS) -> None:
        self._rearm_timeout = rearm_timeout
        self._final_emitted = False
        self._last_final_at: float | None = None

    def accept(self, frame: YoHealthFrame, now: float | None = None) -> bool:
        """Return True exactly when *frame* should create a HA measurement."""
        current = time.monotonic() if now is None else now

        if frame.status != FINAL_STATUS:
            self._final_emitted = False
            return False

        timed_out = (
            self._last_final_at is not None
            and current - self._last_final_at >= self._rearm_timeout
        )
        if self._final_emitted and not timed_out:
            return False

        self._final_emitted = True
        self._last_final_at = current
        return True
