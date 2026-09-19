"""Load pure LAICA BLE modules without importing Home Assistant."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "custom_components" / "laica_ble"

# Avoid executing custom_components.laica_ble.__init__, which imports HA.
custom_components = types.ModuleType("custom_components")
custom_components.__path__ = [str(ROOT / "custom_components")]
sys.modules.setdefault("custom_components", custom_components)

package = types.ModuleType("custom_components.laica_ble")
package.__path__ = [str(PKG_DIR)]
sys.modules.setdefault("custom_components.laica_ble", package)


def load_module(name: str):
    """Load a module from the integration package without HA."""
    fullname = f"custom_components.laica_ble.{name}"
    if fullname in sys.modules:
        return sys.modules[fullname]
    spec = importlib.util.spec_from_file_location(fullname, PKG_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    return module


const = load_module("const")
algorithm = load_module("algorithm")
profile = load_module("profile")
protocol = load_module("protocol")
