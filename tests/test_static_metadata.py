"""Static regression checks for Home Assistant-facing metadata."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "custom_components" / "laica_ble"


def _sensor_descriptions_dict() -> ast.Dict:
    tree = ast.parse((PKG_DIR / "sensor.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "SENSOR_DESCRIPTIONS"
            and isinstance(node.value, ast.Dict)
        ):
            return node.value
    raise AssertionError("SENSOR_DESCRIPTIONS dictionary not found")


def test_body_age_is_disabled_by_default() -> None:
    """Body age must remain opt-in in Home Assistant's entity registry."""
    descriptions = _sensor_descriptions_dict()
    for key, value in zip(descriptions.keys, descriptions.values, strict=True):
        if isinstance(key, ast.Name) and key.id == "KEY_BODY_AGE":
            assert isinstance(value, ast.Call)
            keywords = {keyword.arg: keyword.value for keyword in value.keywords}
            setting = keywords.get("entity_registry_enabled_default")
            assert isinstance(setting, ast.Constant)
            assert setting.value is False
            return
    raise AssertionError("KEY_BODY_AGE description not found")


def test_remove_hook_requests_bluetooth_rediscovery() -> None:
    """Removing the config entry must re-arm Bluetooth discovery."""
    tree = ast.parse((PKG_DIR / "__init__.py").read_text(encoding="utf-8"))
    remove_fn = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "async_remove_entry"
        ),
        None,
    )
    assert remove_fn is not None
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "async_rediscover_address"
        for node in ast.walk(remove_fn)
    )
