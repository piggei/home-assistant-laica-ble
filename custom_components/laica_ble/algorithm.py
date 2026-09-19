"""Recovered YoHealth body-composition algorithm.

This module is deliberately independent from Home Assistant. The formulas were
reconstructed from the historical YoHealth native implementation and the field
mapping was confirmed from the historical Android application that consumed the
native getHealth() result.

The implementation is for interoperability/research. It does not turn a consumer
bioimpedance scale into a medical device and the calculated values should not be
used for diagnosis or treatment decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math

from .const import SEX_FEMALE, SEX_MALE


@dataclass(frozen=True, slots=True)
class UserProfile:
    """User inputs required by the recovered YoHealth algorithm."""

    sex: str
    birth_date: date
    height_cm: float

    def validate(self) -> None:
        """Validate profile values."""
        if self.sex not in (SEX_MALE, SEX_FEMALE):
            raise ValueError(f"Unsupported sex value: {self.sex}")
        if not 80.0 <= self.height_cm <= 250.0:
            raise ValueError("Height must be between 80 and 250 cm")


@dataclass(frozen=True, slots=True)
class BodyMetrics:
    """User-facing fields emitted by the historical YoHealth algorithm."""

    bmi: float
    lean_mass_kg: float
    body_fat_pct: float
    water_pct: float
    muscle_pct: float
    bone_mass_kg: float
    visceral_fat_pct: float
    body_age: int
    bmr_kcal_per_day: int


def age_on_date(birth_date: date, on_date: date) -> int:
    """Return age in whole years on *on_date*."""
    years = on_date.year - birth_date.year
    before_birthday = (on_date.month, on_date.day) < (
        birth_date.month,
        birth_date.day,
    )
    return years - int(before_birthday)


def calculate_body_metrics(
    *,
    weight_kg: float,
    impedance: int,
    height_cm: float,
    age: int,
    sex: str,
) -> BodyMetrics:
    """Calculate the recovered YoHealth body-composition result.

    Args:
        weight_kg: Final scale weight in kilograms.
        impedance: Raw 16-bit YoHealth health/impedance value.
        height_cm: Profile height in centimetres.
        age: Profile age in whole years.
        sex: ``male`` or ``female``. These values reproduce the two branches of
            the historical proprietary algorithm; they are not an identity field.
    """
    if sex not in (SEX_MALE, SEX_FEMALE):
        raise ValueError(f"Unsupported sex value: {sex}")
    if weight_kg <= 0:
        raise ValueError("Weight must be positive")
    if not 80.0 <= height_cm <= 250.0:
        raise ValueError("Height must be between 80 and 250 cm")
    if not 0 <= impedance <= 0xFFFF:
        raise ValueError("Impedance must fit in 16 bits")
    if not 0 <= age <= 130:
        raise ValueError("Age is outside the supported range")

    male = sex == SEX_MALE
    sex_native = 0.0 if male else 1.0
    height_m = height_cm / 100.0

    bmi = weight_kg / (height_m * height_m)

    # Internal lean-mass estimate recovered from getHealth().
    lean_mass_kg = (
        0.00067 * height_cm * height_cm
        + 2.0
        + 0.53 * weight_kg
        - 0.00095 * impedance
        - 3.0 * sex_native
        - 0.05 * age
    )

    body_fat_fraction = (weight_kg - lean_mass_kg) / weight_kg

    # Low-fat correction present in the original native implementation.
    if body_fat_fraction < 0.10:
        body_fat_fraction = body_fat_fraction + 0.7 * (
            0.10 - body_fat_fraction
        )

    water_fraction = 0.73 * lean_mass_kg / weight_kg

    if male:
        muscle_pct = (
            (7.78 * height_cm + 334.0 - 9.8 * age) / weight_kg
        ) + 24.4
        bmr_unrounded = (
            13.7 * weight_kg + 5.0 * height_cm - 6.8 * age + 66.0
        )
    else:
        muscle_pct = (
            (7.74 * height_cm - 318.0 - 9.8 * age) / weight_kg
        ) + 24.4
        bmr_unrounded = (
            9.6 * weight_kg + 1.8 * height_cm - 4.7 * age + 655.0
        )

    # Native getHealth() field 4 was 30 * bone_mass. The Android consumer
    # divided it by 30 and exposed the result as boneMass.
    bone_mass_kg = (
        0.0077200001 * weight_kg
        + 0.0045 * height_cm
        + 1.95
        - 0.00636 * age
        - 0.000232 * impedance
    )
    if not male:
        bone_mass_kg *= 0.75

    # Native field 5 is a fraction. The Android app multiplied it by 100 and
    # named it visceralFatPercentage.
    visceral_fat_pct = body_fat_fraction * (0.45 if male else 0.20) * 100.0

    # Body age logic recovered directly from the final branch in getHealth().
    if age < 20:
        body_age = age
    elif bmi > 28.0:
        body_age = age + 15
    elif bmi > 26.0:
        body_age = age + 12
    elif bmi > 25.0:
        body_age = age + 7
    elif bmi > 23.0:
        body_age = age + 4
    elif age < 30:
        body_age = 18
    elif age <= 44:
        body_age = age - 12
    else:
        body_age = age - 16

    # The native implementation rounded before converting to integer. BMR is
    # positive in the supported domain, so floor(x + 0.5) reproduces C round().
    bmr_kcal_per_day = math.floor(bmr_unrounded + 0.5)

    return BodyMetrics(
        bmi=bmi,
        lean_mass_kg=lean_mass_kg,
        body_fat_pct=body_fat_fraction * 100.0,
        water_pct=water_fraction * 100.0,
        muscle_pct=muscle_pct,
        bone_mass_kg=bone_mass_kg,
        visceral_fat_pct=visceral_fat_pct,
        body_age=body_age,
        bmr_kcal_per_day=bmr_kcal_per_day,
    )
