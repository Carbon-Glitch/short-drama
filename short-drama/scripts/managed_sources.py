"""Check managed editing inputs against their canonical local entity store."""
import json
from pathlib import Path
import sqlite3
import sys
from creator_document import creative_basis

def check(root):
 root=Path(root).resolve();path=root/'.short-drama/managed-source.json'
 if not path.is_file():return None
 marker=json.loads(path.read_text(encoding='utf8'));project=(root/marker['project_root']).resolve();dbpath=project/'.short-drama/state/project.sqlite'
 if not dbpath.is_file():return {'current':False,'reason':'导演台项目数据库未找到'}
 with sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True) as db:
  entities=[{'id':id,'kind':kind,'data':json.loads(data)} for id,kind,data in db.execute('SELECT id,kind,data FROM entity')]
 current=creative_basis({'entities':entities},marker['episode'])
 changed=sorted(k for k in current.keys()|marker['basis'].keys() if current.get(k)!=marker['basis'].get(k))
 return {'current':not changed,'changed':changed,'episode':marker['episode']}
if __name__=='__main__':print(json.dumps(check(sys.argv[1]),ensure_ascii=False))
