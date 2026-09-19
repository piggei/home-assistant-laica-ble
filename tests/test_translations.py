"""Custom-integration translation packaging regression tests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "laica_ble"


def test_custom_component_does_not_ship_core_strings_file() -> None:
    """Custom integrations must use translations/*.json at runtime."""
    assert not (INTEGRATION / "strings.json").exists()


def test_scan_flow_translations_are_complete() -> None:
    """The manual discovery step must never fall back to raw schema keys."""
    for language in ("en", "it"):
        path = INTEGRATION / "translations" / f"{language}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        scan = data["config"]["step"]["scan"]
        assert scan["title"]
        assert scan["description"]
        assert scan["data"]["scan_now"]
        assert scan["data_description"]["scan_now"]
