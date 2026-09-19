#!/usr/bin/env python3
"""Pure-Python regression checks without requiring Home Assistant to be installed."""

from __future__ import annotations

import importlib.util
import sys
import types
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "custom_components" / "laica_ble"

# Create lightweight package shells so the pure modules can use relative imports
# without importing the Home Assistant-specific package __init__.py.
custom_components = types.ModuleType("custom_components")
custom_components.__path__ = [str(ROOT / "custom_components")]
sys.modules.setdefault("custom_components", custom_components)
laica_pkg = types.ModuleType("custom_components.laica_ble")
laica_pkg.__path__ = [str(PKG_DIR)]
sys.modules.setdefault("custom_components.laica_ble", laica_pkg)


def load(name: str):
    path = PKG_DIR / f"{name}.py"
    fullname = f"custom_components.laica_ble.{name}"
    spec = importlib.util.spec_from_file_location(fullname, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    return module


const = load("const")
algorithm = load("algorithm")
protocol = load("protocol")

# Reference PS7002 frame: 80.7 kg, impedance 665, final status 0x86.
payload = bytes.fromhex("09 FF 03 27 02 99 86 FF FF 21 15 AA")
frame = protocol.parse_payload(payload)
assert frame is not None
assert abs(frame.weight_kg - 80.7) < 1e-9
assert frame.impedance == 665
assert frame.status == 0x86
assert frame.mode.raw == 0x21
assert protocol.calculate_checksum(payload) == 0x15

# Gate must accept final once, suppress duplicate, re-arm on non-final.
gate = protocol.FinalMeasurementGate(rearm_timeout=30.0)
assert gate.accept(frame, now=100.0)
assert not gate.accept(frame, now=101.0)
realtime_payload = bytearray(payload)
realtime_payload[6] = 0x80
realtime_payload[10] = (
    sum(protocol.COMPANY_ID_LE_BYTES) + sum(realtime_payload[:10])
) & 0xFF
realtime = protocol.parse_payload(bytes(realtime_payload))
assert realtime is not None
assert not gate.accept(realtime, now=102.0)
assert gate.accept(frame, now=103.0)


# A final 0x86 frame without usable impedance is still a final weight.
no_bia = bytearray(payload)
no_bia[4:6] = bytes.fromhex("FF FF")
no_bia[10] = (sum(protocol.COMPANY_ID_LE_BYTES) + sum(no_bia[:10])) & 0xFF
no_bia_frame = protocol.parse_payload(bytes(no_bia))
assert no_bia_frame is not None
assert no_bia_frame.status == 0x86
assert no_bia_frame.impedance is None

# Corrupt checksum must be rejected.
bad = bytearray(payload)
bad[10] ^= 0x01
assert protocol.parse_payload(bytes(bad)) is None

# Historical reference vector used throughout the reverse engineering.
metrics = algorithm.calculate_body_metrics(
    weight_kg=80.7,
    impedance=665,
    height_cm=175.0,
    age=55,
    sex=const.SEX_MALE,
)
checks = {
    "BMI": (metrics.bmi, 26.351020408163266),
    "body fat": (metrics.body_fat_pct, 23.286245353159853),
    "water": (metrics.water_pct, 56.0010408921933),
    "muscle": (metrics.muscle_pct, 38.73085501858736),
    "bone": (metrics.bone_mass_kg, 2.85642400807),
    "visceral fat": (metrics.visceral_fat_pct, 10.478810408921934),
}
for label, (got, expected) in checks.items():
    assert abs(got - expected) < 1e-6, (label, got, expected)
assert metrics.body_age == 67
assert metrics.bmr_kcal_per_day == 1673

assert algorithm.age_on_date(date(1970, 12, 10), date(2026, 9, 19)) == 55
assert algorithm.age_on_date(date(1970, 12, 10), date(2026, 12, 10)) == 56

print("PASS: protocol, final-frame gate, profile age, and YoHealth algorithm")
