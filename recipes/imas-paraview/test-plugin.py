"""Verify plugin discovery and registration without creating a render window."""

import os
import sys
from importlib.metadata import version
from pathlib import Path

import imas_paraview
from paraview import servermanager
from paraview.simple import LoadPlugin

assert imas_paraview.__version__ == version("imas-paraview")

shim_dir = Path(sys.prefix) / "share" / "imas-paraview" / "plugins"
assert Path(os.environ["PV_PLUGIN_PATH"]).resolve() == shim_dir.resolve(), (
    os.environ["PV_PLUGIN_PATH"]
)

shims = sorted(shim_dir.glob("*.py"))
assert len(shims) >= 15, shims
for shim in shims:
    LoadPlugin(str(shim), remote=False)

pxm = servermanager.ProxyManager()
expected = {
    "sources": [
        "GGDReader",
        "JorekGGDReader",
        "WallLimiterReader",
        "MagneticsReader",
        "Profiles2DReader",
    ],
    "filters": ["Profiles1DMapper"],
}
for group, names in expected.items():
    for name in names:
        assert pxm.GetPrototypeProxy(group, name), f"{group}/{name} not registered"
