"""Read Skill project registrations and import a source only when opened."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading

from library import DOCS

class Discovery:
    def __init__(self,library,registry=None):
        self.library=library
        self.registry=Path(registry or os.environ.get('SHORT_DRAMA_PROJECT_REGISTRY',Path.home()/'.short-drama/project-registry'))
        self.lock=threading.Lock()
        self.database=library.home/'discovered-projects.sqlite'
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS imported(source TEXT PRIMARY KEY,target TEXT NOT NULL)')

    def list(self):
        if not self.registry.is_dir():return []
        with closing(sqlite3.connect(self.database)) as db, db:imported=dict(db.execute('SELECT source,target FROM imported'))
        result=[]
        for entry in self.registry.glob('*.json'):
            try:
                record=json.loads(entry.read_text(encoding='utf-8-sig'));root=Path(record['path']).resolve()
                if not root.is_dir() or root==self.library.projects or self.library.projects in root.parents:continue
                key=hashlib.sha256(os.path.normcase(str(root)).encode('utf8')).hexdigest()
                if key in imported and (self.library.projects/imported[key]/'.short-drama/state/project.sqlite').is_file():continue
                ready=any((root/name).is_file() for name in DOCS)
                for directory in ('剧集','episodes'):
                    if (root/directory).is_dir():
                        ready=ready or any(p.is_dir() and any((p/name).is_file() for name in DOCS) for p in (root/directory).iterdir())
                config=root/'short-drama.json'
                title=json.loads(config.read_text(encoding='utf-8-sig')).get('title') if config.is_file() else record.get('title')
                result.append({'id':key,'title':title or root.name,'path':str(root),'ready':ready})
            except (OSError,ValueError,KeyError,TypeError):continue
        return sorted(result,key=lambda p:p['title'])

    def source_for(self,project):
        with closing(sqlite3.connect(self.database)) as db:
            row=db.execute('SELECT source FROM imported WHERE target=?',(project,)).fetchone()
        if not row:return None
        try:
            record=json.loads((self.registry/(row[0]+'.json')).read_text(encoding='utf-8-sig'))
            root=Path(record['path']).resolve()
            key=hashlib.sha256(os.path.normcase(str(root)).encode('utf8')).hexdigest()
            return root if key==row[0] and root.is_dir() else None
        except (OSError,ValueError,KeyError):return None

    def open(self,identity):
        with self.lock:
            with closing(sqlite3.connect(self.database)) as db, db:
                row=db.execute('SELECT target FROM imported WHERE source=?',(identity,)).fetchone()
                if row and (self.library.projects/row[0]/'.short-drama/state/project.sqlite').is_file():return row[0]
            source=next((p for p in self.list() if p['id']==identity),None)
            if not source:raise ValueError('来源项目已移动，请重新导入')
            if not source['ready']:raise ValueError('项目刚创建，首份创作文档落盘后即可打开')
            target=self.library.import_project(source['path'])
            with closing(sqlite3.connect(self.database)) as db, db:
                db.execute('INSERT OR REPLACE INTO imported VALUES(?,?)',(identity,target))
            return target
