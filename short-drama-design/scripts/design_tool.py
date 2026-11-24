"""Inspect script/design provenance and missing downstream files; record one design pass."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys

SCENE = re.compile(r"^##\s+((?:[A-Za-z0-9]+-)*EP\d+-SC\d+)\s+(?:内外|内|外)\b", re.M)
DESIGN = re.compile(r"^##\s+场面设计\s*·\s*((?:[A-Za-z0-9]+-)*EP\d+-SC\d+)\s*$", re.M)
REF = re.compile(r"·\s*([^·；\n《》]+?\.(?:png|jpe?g|webp))《", re.I)
IMAGE = re.compile(r"^[-*]\s*(?:资产图|输入参考图)[：:]\s*(.+)$", re.M)
SHOT = re.compile(r"^##\s+SHOT-[A-Z0-9-]+\b", re.M)

def text(path):
    return path.read_text(encoding="utf-8-sig") if path.is_file() else ""

def digest(value):
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()

def creative_text(value):
    # The assets owner appends implementation bindings; these do not rewrite the design.
    return re.sub(r"^## 资产实现[^\n]*\n.*?(?=^## |\Z)", "", value, flags=re.M | re.S).strip()

def project_root(episode, root=None):
    if root:
        return Path(root).resolve()
    for candidate in (episode, *episode.parents):
        if (candidate / "short-drama.json").is_file():
            return candidate
    return episode

def image_file(path):
    if not path.is_file():
        return False
    with path.open("rb") as stream:
        head = stream.read(32)
    return (head.startswith(b"\x89PNG\r\n\x1a\n") or head.startswith(b"\xff\xd8\xff")
            or (head.startswith(b"RIFF") and head[8:12] == b"WEBP"))

def inspect(episode, root=None):
    ep = Path(episode).resolve()
    root = project_root(ep, root)
    screenplay = text(ep / "剧本.md")
    visual = text(ep / "视觉设定.md")
    creative = creative_text(visual)
    storyboard = text(ep / "分镜.md")
    project = json.loads(text(root / "short-drama.json") or "{}")
    authority = project.get("creator_authority", {})
    profile = {"format": project.get("format"), "production": authority.get("production_profile"),
               "visual": authority.get("visual_direction")}
    source_refs = {}
    for name in REF.findall(creative):
        file = root / name.strip()
        source_refs[name.strip()] = digest(file.read_bytes()) if file.is_file() else None
    inputs = {"screenplay": digest(screenplay), "design": digest(creative),
              "profile": digest(json.dumps(profile, ensure_ascii=False, sort_keys=True)),
              "references": source_refs}
    fingerprint = digest(json.dumps(inputs, ensure_ascii=False, sort_keys=True))
    receipt_file = ep / ".short-drama/design-pass.json"
    try:
        receipt = json.loads(text(receipt_file) or "{}")
    except json.JSONDecodeError:
        receipt = {}
    current = receipt.get("schema") == 1 and receipt.get("fingerprint") == fingerprint
    heads = list(SHOT.finditer(storyboard))
    shot_bodies = [storyboard[h.end():heads[i+1].start() if i+1 < len(heads) else None]
                   for i, h in enumerate(heads)]
    required = ("来源", "时长", "起点", "唯一动作", "终点")
    shots = bool(heads) and all(all(re.search(r"^[-*]\s*" + field + r"[：:]\s*\S", body, re.M)
                                              for field in required) for body in shot_bodies)
    asset_fields = re.findall(r"^[-*]\s*资产图[：:]\s*(.+)$", visual, re.M)
    fields = list(asset_fields)
    missing_shots = []
    text_choices = []
    for head, body in zip(heads, shot_bodies):
        refs = re.findall(r"^[-*]\s*输入参考图[：:]\s*(.+)$", body, re.M)
        fields.extend(refs)
        value = refs[0].strip() if len(refs) == 1 else ""
        exempt = value.rstrip("。") == "无（创作者已明确选择文生视频）"
        text_choices.append(exempt)
        required_paths = REF.findall(value)
        if not exempt and (not required_paths or any(x in value for x in ("待补", "待生成", "PLAN-"))
                           or any(not image_file(root / f.strip()) for f in required_paths)):
            missing_shots.append(head.group().split()[-1])
    paths = sorted({name.strip() for field in fields for name in REF.findall(field)})
    unresolved = [name for name in paths if not image_file(root / name)]
    pending = any(any(x in field for x in ("待补", "待生成", "PLAN-")) for field in fields)
    images = bool(paths) and not unresolved and not pending and not missing_shots
    text_only = bool(text_choices) and all(text_choices)
    missing = (["分镜"] if not shots else []) + (["实际资产图"] if not images and not text_only else [])
    stale = bool(receipt) and not current
    scenes = set(SCENE.findall(screenplay))
    designed = set(DESIGN.findall(creative))
    needs_design = bool(scenes) and (bool(missing) or stale) and not current
    if not scenes:
        next_skill = "short-drama-write"
    elif needs_design:
        next_skill = "short-drama-design"
    elif not shots:
        next_skill = "short-drama-storyboard"
    elif not images and not text_only:
        next_skill = "short-drama-assets"
    else:
        next_skill = "short-drama-video-prompts"
    waiting=None
    if (ep/'.short-drama/director.sqlite').exists():
        tools_dir=Path(__file__).resolve().parents[2]/'short-drama/scripts'
        sys.path.insert(0,str(tools_dir))
        try:
            from director_desk import blocked
            waiting=blocked(ep,{'short-drama-write':'剧本','short-drama-design':'Design','short-drama-storyboard':'分镜','short-drama-assets':'资产','short-drama-video-prompts':'投产'}[next_skill])
        finally:sys.path.remove(str(tools_dir))
    if waiting:next_skill='wait-for-director'
    return {"director_waiting":waiting,"episode": str(ep), "projectRoot": str(root), "missing": missing,
            "storyboard_present": shots, "asset_images_present": images,
            "asset_paths": paths, "missing_asset_paths": unresolved, "missing_asset_shots": missing_shots,
            "assets_intentionally_unused": text_only,
            "design_current": current, "design_stale": stale, "needs_design": needs_design,
            "missing_scene_designs": sorted(scenes - designed),
            "unknown_scene_designs": sorted(designed - scenes),
            "next_skill": next_skill, "fingerprint": fingerprint, "inputs": inputs,
            "evidence_scope": "file availability and design provenance; creative quality is observed by the Agent"}

def complete(episode, root=None):
    result = inspect(episode, root)
    if result.get("director_waiting") and result["director_waiting"] in ("开发","剧本"):
        raise ValueError("导演台等待确认："+result["director_waiting"])
    if result["next_skill"] == "short-drama-write":
        raise ValueError("先准备含真实场次的剧本。")
    if result["missing_scene_designs"] or result["unknown_scene_designs"]:
        raise ValueError("场面设计需对应当前剧本场次: " + json.dumps(
            {"missing": result["missing_scene_designs"], "unknown": result["unknown_scene_designs"]},
            ensure_ascii=False))
    ep = Path(result["episode"])
    path = ep / ".short-drama/design-pass.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": 1, "fingerprint": result["fingerprint"], "inputs": result["inputs"]}
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)
    return inspect(ep, result["projectRoot"])

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inspect", "complete"])
    parser.add_argument("episode")
    parser.add_argument("--project-root")
    args = parser.parse_args()
    result = (complete if args.command == "complete" else inspect)(args.episode, args.project_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

