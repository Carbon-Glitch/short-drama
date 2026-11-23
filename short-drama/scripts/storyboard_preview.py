#!/usr/bin/env python3
"""Project authoritative SHOT sound-picture fields into a review table."""

from __future__ import annotations

import argparse
import re
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creator_views import parse_storyboard


CORE_FIELDS = (
    ("目的", "purpose"),
    ("景别/机位", "framing"),
    ("运镜", "move"),
    ("起点", "start"),
    ("动作与反应", "action"),
    ("终点", "end"),
    ("声音", "sound"),
)
OPTIONAL_FIELDS = (
    ("画面文字", "screenText"),
    ("剪辑意图", "editIntent"),
    ("制作分工", "productionRole"),
    ("接镜", "join"),
)


def _decimal_text(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _clock(value: Decimal) -> str:
    minutes, seconds = divmod(value, Decimal(60))
    hours, minutes = divmod(minutes, Decimal(60))
    second_text = _decimal_text(seconds)
    if "." in second_text:
        whole, fraction = second_text.split(".", 1)
        second_text = f"{int(whole):02d}.{fraction}"
    else:
        second_text = f"{int(seconds):02d}"
    prefix = f"{int(hours):02d}:{int(minutes):02d}" if hours else f"{int(minutes):02d}"
    return f"{prefix}:{second_text}"


def _cell(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("|", "&#124;")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "<br>")
        .strip()
    )


def build_preview(document: str) -> tuple[str, list[str]]:
    board = parse_storyboard(document)
    heading = re.search(r"^#\s+(.+)$", document, re.MULTILINE)
    title = heading.group(1).strip() if heading else "当前分镜"
    warnings: list[str] = []
    rows: list[str] = []
    cursor = Decimal(0)
    total = Decimal(0)
    timeline_complete = True
    missing_durations = 0

    for shot in board["shots"]:
        seconds = Decimal(str(shot["sec"])) if shot["secDeclared"] else None
        if seconds is None:
            missing_durations += 1
            timeline_complete = False
            time_window = "待核"
            duration = "未定时长"
        else:
            total += seconds
            duration = f"{_decimal_text(seconds)}秒"
            if timeline_complete:
                time_window = f"{_clock(cursor)}–{_clock(cursor + seconds)}"
                cursor += seconds
            else:
                time_window = "待核"

        for label, key in CORE_FIELDS:
            if not str(shot.get(key, "")).strip():
                warnings.append(f"{shot['id']} 未写{label}；预览保留缺口，不代为补写")
        values = {
            key: str(shot.get(key, "")).strip() or "未写"
            for _, key in CORE_FIELDS
        }
        parts = [
            f"目的：{_cell(values['purpose'])}",
            f"摄影：{_cell(values['framing'])}；{_cell(values['move'])}",
            f"起点：{_cell(values['start'])}",
            f"动作与反应：{_cell(values['action'])}",
            f"终点：{_cell(values['end'])}",
            f"声音：{_cell(values['sound'])}",
        ]
        for label, key in OPTIONAL_FIELDS:
            value = str(shot.get(key, "")).strip()
            if value:
                parts.append(f"{label}：{_cell(value)}")
        identity = f"{shot['id']}<br>{_cell(shot['title'])}"
        rows.append(f"| {identity} | {time_window} | {duration} | {'<br>'.join(parts)} |")

    if missing_durations:
        summary = f"共 {len(board['shots'])} 镜｜计划总时长待核（{missing_durations} 镜未声明时长）"
        warnings.append("部分镜头未声明时长；无法计算完整时间轴")
    else:
        summary = f"共 {len(board['shots'])} 镜｜计划总时长 {_decimal_text(total)} 秒"
    lines = [
        "# 分镜审阅预览",
        "",
        f"{title}｜{summary}",
        "",
        "> 由当前《分镜.md》同源生成；只用于审阅，不替代分镜，也不代表媒体已验收。",
        "",
        "| 分镜号 | 时间 | 镜长 | 完整声画调度 |",
        "| --- | --- | --- | --- |",
        *rows,
        "",
    ]
    return "\n".join(lines), warnings


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="从分镜.md生成完整声画调度审阅表")
    parser.add_argument("storyboard", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="可选派生 Markdown；默认输出到终端")
    args = parser.parse_args()
    if args.output and args.output.resolve() == args.storyboard.resolve():
        parser.error("预览不能覆盖权威《分镜.md》；请改用其他输出路径或省略 --output")
    try:
        document = args.storyboard.read_text(encoding="utf-8-sig")
        preview, warnings = build_preview(document)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(preview, encoding="utf-8")
        print(args.output)
    else:
        sys.stdout.write(preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
