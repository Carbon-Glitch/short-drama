#!/usr/bin/env python3
"""Offline self-test for multi-episode source intake."""

from __future__ import annotations

import json
import tempfile
import sys
from pathlib import Path

from episode_intake import build_index, slice_episode, verify_index, write_index

MINIMUM_PYTHON = (3, 9)
if sys.version_info < MINIMUM_PYTHON:
    raise SystemExit("selftest.py requires Python 3.9 or newer")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_adaptation_crosswalk() -> None:
    example = Path(__file__).resolve().parents[1] / "assets" / "adaptation-map.example.jsonl"
    record = json.loads(example.read_text(encoding="utf-8").splitlines()[0])
    required = {
        "source_candidate_id",
        "payoff_ids",
        "production_load",
        "preserved_facts",
        "unresolved",
    }
    require(
        required <= record.keys()
        and record["source_candidate_id"]
        and record["payoff_ids"]
        and record["adaptation_decision"]["disposition"] == "change_carrier",
        "adaptation example preserves the novel-candidate crosswalk",
    )


def main() -> int:
    check_adaptation_crosswalk()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "episodes.md"
        index = root / "index.json"
        source.write_text("第1集 开端\n行动一。\n第2集 反转\n行动二。\n", encoding="utf-8")

        document = build_index(source, source_ref="输入/episodes.md")
        require(document["episode_count"] == 2, "episode count")
        require(document["problems"] == [], "valid episode index")
        write_index(index, document)
        require(verify_index(index, source)["verified"] is True, "fresh index")
        require(
            slice_episode(index, source, "EP002").startswith("第2集".encode()),
            "verified episode slice",
        )

        source.write_text(source.read_text(encoding="utf-8") + "变更。\n", encoding="utf-8")
        require(verify_index(index, source)["verified"] is False, "source drift")

    print("6 self-tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
