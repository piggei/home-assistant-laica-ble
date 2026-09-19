"""Profile parsing helpers independent from Home Assistant."""

from __future__ import annotations

from datetime import date, datetime


ACCEPTED_BIRTH_DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")


def parse_birth_date(value: str) -> date | None:
    """Parse a supported birth-date string.

    User-facing configuration accepts both the familiar European DD/MM/YYYY
    form and ISO YYYY-MM-DD. The config flow stores the result in ISO format.
    """
    raw = value.strip()
    for fmt in ACCEPTED_BIRTH_DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None
