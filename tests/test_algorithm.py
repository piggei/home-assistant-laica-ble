"""Recovered YoHealth algorithm regression tests."""

from __future__ import annotations

from datetime import date

import pytest
from conftest import algorithm, const


def test_reference_vector() -> None:
    metrics = algorithm.calculate_body_metrics(
        weight_kg=80.7,
        impedance=665,
        height_cm=175.0,
        age=55,
        sex=const.SEX_MALE,
    )

    assert metrics.bmi == pytest.approx(26.351020408163266)
    assert metrics.body_fat_pct == pytest.approx(23.286245353159853)
    assert metrics.water_pct == pytest.approx(56.0010408921933)
    assert metrics.muscle_pct == pytest.approx(38.73085501858736)
    assert metrics.bone_mass_kg == pytest.approx(2.85642400807)
    assert metrics.visceral_fat_pct == pytest.approx(10.478810408921934)
    assert metrics.body_age == 67
    assert metrics.bmr_kcal_per_day == 1673


def test_age_rollover() -> None:
    born = date(1970, 12, 10)
    assert algorithm.age_on_date(born, date(2026, 9, 19)) == 55
    assert algorithm.age_on_date(born, date(2026, 12, 10)) == 56
