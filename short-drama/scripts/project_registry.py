"""Machine-local project discovery, without copying or changing creative files."""
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4


def register_project(root,title=''):
    root=Path(root).expanduser().resolve()
    directory=Path(os.environ.get('SHORT_DRAMA_PROJECT_REGISTRY',Path.home()/'.short-drama/project-registry'))
    directory.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(os.path.normcase(str(root)).encode('utf8')).hexdigest()
    destination=directory/(key+'.json')
    temporary=directory/(key+'.'+uuid4().hex+'.tmp')
    temporary.write_text(json.dumps({'path':str(root),'title':title or root.name},ensure_ascii=False),encoding='utf8')
    temporary.replace(destination)
    return key
