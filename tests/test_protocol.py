"""Protocol regression tests."""

from __future__ import annotations

from conftest import protocol

REFERENCE = bytes.fromhex("09 FF 03 27 02 99 86 FF FF 21 15 AA")


def test_reference_frame() -> None:
    frame = protocol.parse_payload(REFERENCE)
    assert frame is not None
    assert frame.weight_kg == 80.7
    assert frame.impedance == 665
    assert frame.status == 0x86
    assert frame.mode.raw == 0x21
    assert protocol.calculate_checksum(REFERENCE) == 0x15


def test_bad_checksum_is_rejected() -> None:
    payload = bytearray(REFERENCE)
    payload[10] ^= 0x01
    assert protocol.parse_payload(bytes(payload)) is None


def test_final_without_impedance_is_weight_only() -> None:
    payload = bytearray(REFERENCE)
    payload[4:6] = b"\xff\xff"
    payload[10] = (
        sum(protocol.COMPANY_ID_LE_BYTES) + sum(payload[:10])
    ) & 0xFF
    frame = protocol.parse_payload(bytes(payload))
    assert frame is not None
    assert frame.status == 0x86
    assert frame.weight_kg == 80.7
    assert frame.impedance is None


def test_gate_suppresses_duplicate_and_rearms() -> None:
    final = protocol.parse_payload(REFERENCE)
    assert final is not None
    gate = protocol.FinalMeasurementGate(rearm_timeout=30.0)
    assert gate.accept(final, now=100.0)
    assert not gate.accept(final, now=101.0)

    realtime_bytes = bytearray(REFERENCE)
    realtime_bytes[6] = 0x80
    realtime_bytes[10] = (
        sum(protocol.COMPANY_ID_LE_BYTES) + sum(realtime_bytes[:10])
    ) & 0xFF
    realtime = protocol.parse_payload(bytes(realtime_bytes))
    assert realtime is not None
    assert not gate.accept(realtime, now=102.0)
    assert gate.accept(final, now=103.0)
