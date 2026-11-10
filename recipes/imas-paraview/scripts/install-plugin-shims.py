"""Expose IMAS-ParaView plugins at a Python-version-independent location.

The real plugins live in site-packages, whose path depends on the Python
version and platform. For each module that defines ParaView proxies, write a
shim into $PREFIX/share/imas-paraview/plugins that re-exports those proxies,
and point PV_PLUGIN_PATH there with a static activation environment variable.
"""

import ast
import json
import os
from pathlib import Path

prefix = Path(os.environ["PREFIX"])
package = Path(os.environ["SP_DIR"]) / "imas_paraview" / "plugins"
shim_dir = prefix / "share" / "imas-paraview" / "plugins"
shim_dir.mkdir(parents=True, exist_ok=True)


def is_proxy(decorator: ast.expr) -> bool:
    # Matches @smproxy.source(...), @smproxy.filter(...), @smproxy.reader(...), ...
    node = decorator.func if isinstance(decorator, ast.Call) else decorator
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "smproxy"
    )


count = 0
for source in sorted(package.glob("*.py")):
    tree = ast.parse(source.read_text(encoding="utf-8"))
    proxies = [
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and any(map(is_proxy, node.decorator_list))
    ]
    if not proxies:
        continue
    (shim_dir / source.name).write_text(
        f"from imas_paraview.plugins.{source.stem} import {', '.join(proxies)}"
        "  # noqa: F401\n",
        encoding="utf-8",
    )
    count += 1

if count == 0:
    raise SystemExit(f"no ParaView proxies found in {package}")

env_vars = prefix / "etc" / "conda" / "env_vars.d" / "imas-paraview.json"
env_vars.parent.mkdir(parents=True, exist_ok=True)
# Use forward slashes: the prefix is rewritten at install time, and ParaView
# accepts forward slashes on Windows as well.
env_vars.write_text(
    json.dumps({"PV_PLUGIN_PATH": shim_dir.as_posix()}, indent=2) + "\n",
    encoding="utf-8",
)
