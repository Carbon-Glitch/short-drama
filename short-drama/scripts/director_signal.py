"""Portable, offline stage receipt for any agent with project-folder write access."""
from pathlib import Path
from datetime import datetime,timezone
from argparse import ArgumentParser
from uuid import uuid4
import json,os
STAGES=('开发','剧本','Design','分镜','资产','投产','回片','剪辑','交付')
def record(episode,actor,stage,change,message,paths=()):
    ep=Path(episode).resolve(strict=True)
    if not ep.is_dir() or stage not in STAGES or not actor.strip() or not message.strip():raise ValueError('请指定集目录、执行者、有效阶段及进展说明')
    items=[]
    for name in paths:
        p=(ep/name).resolve()
        if not p.is_relative_to(ep) or not p.is_file():raise ValueError('产物必须是本集已存在的文件')
        items.append(p.relative_to(ep).as_posix())
    d=ep/'.short-drama/progress'
    if not d.resolve().is_relative_to(ep):raise ValueError('进展目录无效')
    d.mkdir(parents=True,exist_ok=True);uid=uuid4().hex
    event=dict(id=uid,at=datetime.now(timezone.utc).isoformat(),actor=actor[:64],stage=stage,change=change[:40],message=message[:2000],paths=items)
    tmp=d/(uid+'.partial');tmp.write_text(json.dumps(event,ensure_ascii=False),encoding='utf8');os.replace(tmp,d/(uid+'.json'));return uid
if __name__=='__main__':
    p=ArgumentParser(description=__doc__);p.add_argument('episode',type=Path);p.add_argument('--actor',required=True);p.add_argument('--stage',choices=STAGES,required=True);p.add_argument('--change',choices=['开始','调整','完成','等待','返修'],required=True);p.add_argument('--message',required=True);p.add_argument('--artifact',action='append',default=[])
    a=p.parse_args();print(record(a.episode,a.actor,a.stage,a.change,a.message,a.artifact))
