#!/usr/bin/env python3
"""Optional finishing tools; editorial choices remain in the cut list.

Routes to a pinned, MIT-licensed subset of kajisho5/ffmpeg-skill. No installer,
cloud service, global PATH edit, or second project schema is involved.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BACKEND = HERE / "ffmpeg_backend"
TOOLS = ("probe", "fit", "audio", "loudness", "color", "look", "edit")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ffmpeg-bin", type=Path,
        help="Directory containing ffmpeg and ffprobe; otherwise use SHORT_DRAMA_FFMPEG_BIN or PATH",
    )
    parser.add_argument("--version", action="store_true", help="Print the pinned backend source")
    parser.add_argument("tool", nargs="?", choices=TOOLS)
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Tool arguments; TOOL --help lists them")
    options = parser.parse_args(argv)
    if options.version:
        print((BACKEND / "UPSTREAM.json").read_text(encoding="utf-8"))
        return 0
    if options.tool is None:
        parser.error("choose a tool: " + ", ".join(TOOLS))
    if options.tool != "edit" and sys.version_info < (3, 10):
        parser.error("the optional ffmpeg-skill backend requires Python 3.10+")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    selected = options.ffmpeg_bin or env.get("SHORT_DRAMA_FFMPEG_BIN")
    if selected:
        folder = Path(selected).expanduser().resolve()
        suffix = ".exe" if os.name == "nt" else ""
        missing = [name for name in ("ffmpeg", "ffprobe") if not (folder / (name + suffix)).is_file()]
        if missing:
            print(json.dumps({"ok": False, "error": "missing tools", "directory": str(folder),
                              "missing": missing}), file=sys.stderr)
            return 2
        env["PATH"] = str(folder) + os.pathsep + env.get("PATH", "")
    script = HERE / "edit_tool.py" if options.tool == "edit" else BACKEND / (options.tool + ".py")
    # A subprocess keeps the backend's generic _common imports out of the
    # native editor's module namespace and preserves its output and exit code.
    return subprocess.call([sys.executable, str(script), *options.args], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
