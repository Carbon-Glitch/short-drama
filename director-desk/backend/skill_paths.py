"""Use one Skill source for a checkout, a portable build, or an explicit override."""
import os
from pathlib import Path

def skills_root():
    configured=os.environ.get('DIRECTOR_SKILLS_HOME')
    if configured:
        root=Path(configured).expanduser().resolve()
        if not (root/'short-drama/SKILL.md').is_file():raise ValueError('DIRECTOR_SKILLS_HOME 未指向完整短剧 Skill 套件')
        return root
    root=Path(__file__).resolve().parents[2]
    if (root/'short-drama/SKILL.md').is_file():return root
    root=Path.home()/'.agents/skills'
    if (root/'short-drama/SKILL.md').is_file():return root
    raise ValueError('未找到短剧 Skill 套件，请保留仓库中的 short-drama* 目录')
