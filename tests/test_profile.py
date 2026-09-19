"""Profile input parsing tests."""

from __future__ import annotations

from datetime import date

from conftest import profile


def test_parse_european_birth_date() -> None:
    assert profile.parse_birth_date("10/12/1970") == date(1970, 12, 10)


def test_parse_iso_birth_date() -> None:
    assert profile.parse_birth_date("1970-12-10") == date(1970, 12, 10)


def test_invalid_birth_date() -> None:
    assert profile.parse_birth_date("1970/12/10") is None
    assert profile.parse_birth_date("31/02/1970") is None
