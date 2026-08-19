"""Compile the vendored Triangle source and bundle the binary in the wheel."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

HERE = Path(__file__).parent
SRC_DIR = HERE / "src" / "landlab_triangle" / "_triangle_src"
BIN_DIR = HERE / "src" / "landlab_triangle" / "_triangle_bin"

# triangle.c includes triangle.h before its own `#define REAL`/`VOID`, so pass
# them here. -std=gnu17 keeps K&R prototypes (gcc defaults to C23, which rejects
# them); NO_TIMER drops the Unix-only timing code.
FLAGS = ["-std=gnu17", "-O2", "-DREAL=double", "-DVOID=int", "-DNO_TIMER", "-DANSI_DECLARATORS"]


def _binary_name():
    return "triangle.exe" if os.name == "nt" else "triangle"


def _command(output):
    source = str(SRC_DIR / "triangle.c")
    if sys.platform == "win32":
        # -static: no mingw runtime DLL dependency.
        cc = os.environ.get("CC", "x86_64-w64-mingw32-gcc")
        return [cc, *FLAGS, "-static", "-o", str(output), source, "-lm"]
    cc = os.environ.get("CC", "cc")
    return [cc, *FLAGS, "-o", str(output), source, "-lm"]


class TriangleBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        output = BIN_DIR / _binary_name()

        subprocess.run(_command(output), check=True)
        if os.name != "nt":
            output.chmod(0o755)

        # Platform-specific (bundled binary) but interpreter-independent.
        from packaging.tags import sys_tags

        rel = output.relative_to(HERE).as_posix()
        build_data["pure_python"] = False
        build_data["tag"] = f"py3-none-{next(iter(sys_tags())).platform}"
        build_data.setdefault("force_include", {})[str(output)] = rel

    def finalize(self, version, build_data, artifact_path):
        shutil.rmtree(BIN_DIR, ignore_errors=True)
