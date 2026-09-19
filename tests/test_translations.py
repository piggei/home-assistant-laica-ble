"""Custom-integration translation packaging regression tests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "laica_ble"


def test_custom_component_does_not_ship_core_strings_file() -> None:
    """Custom integrations must use translations/*.json at runtime."""
    assert not (INTEGRATION / "strings.json").exists()


def test_runtime_translations_cover_all_visible_config_steps() -> None:
    """All user-visible flow fields must have runtime translations."""
    expected = {
        "profile": {"birth_date", "height_cm", "scale_model", "sex"},
        "user": {"address"},
    }
    for language in ("en", "it"):
        path = INTEGRATION / "translations" / f"{language}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = data["config"]["step"]
        assert "scan" not in steps
        for step_id, fields in expected.items():
            assert steps[step_id]["title"]
            assert fields <= set(steps[step_id]["data"])
            assert all(steps[step_id]["data"][field] for field in fields)
