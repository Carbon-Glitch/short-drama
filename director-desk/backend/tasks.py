"""Explicit Agent work queue with bounded write scope and source-version checks."""
import json
import time
from uuid import uuid4

from store import Conflict, encoded
from document_contract import validate_agent_fields
from creative_context import context_ids, project_context

CREATIVE_SKILLS={'write','design','storyboard','assets','image-prompts','video-prompts','review','develop','novel-analyze'}


class TaskQueue:
    def __init__(self, store):
        self.store=store
        with store.connection() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS agent_task(
                id TEXT PRIMARY KEY,prompt TEXT NOT NULL,scope TEXT NOT NULL,basis TEXT NOT NULL,
                status TEXT NOT NULL,worker TEXT,lease_until REAL,result TEXT,created REAL NOT NULL)''')
            if 'skill' not in {row[1] for row in db.execute('PRAGMA table_info(agent_task)')}:
                db.execute("ALTER TABLE agent_task ADD COLUMN skill TEXT NOT NULL DEFAULT ''")
            if 'mode' not in {row[1] for row in db.execute('PRAGMA table_info(agent_task)')}:
                db.execute("ALTER TABLE agent_task ADD COLUMN mode TEXT NOT NULL DEFAULT 'edit'")

    def list(self):
        with self.store.connection() as db:
            return [self.decode(row) for row in db.execute('SELECT * FROM agent_task ORDER BY created DESC')]

    @staticmethod
    def decode(row):
        return {**dict(row),'scope':json.loads(row['scope']),'basis':json.loads(row['basis']),
                'result':json.loads(row['result']) if row['result'] else None}

    def create(self,prompt,scope,skill='',mode='edit'):
        if not isinstance(prompt,str) or not prompt.strip():raise ValueError('写下你希望修改什么')
        if skill and skill not in CREATIVE_SKILLS:raise ValueError('未知创作职责')
        if mode not in ('edit','script_review'):raise ValueError('未知任务方式')
        if mode=='script_review':skill='review'
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE');state=self.store._state(db)
            entities={e['id']:e for e in state['entities']}
            if not scope or any(identity not in entities for identity in scope):raise ValueError('请选择需要修改的对象')
            selected=set(scope)
            while True:
                children={e['id'] for e in entities.values() if e['data'].get('parent_id') in selected or e['data'].get('document_id') in selected}
                if children<=selected:break
                selected.update(children)
            if mode=='script_review':
                selected={identity for identity in selected if entities[identity]['kind'] in ('episode','scene')}
                if not any(entities[identity]['kind']=='scene' for identity in selected):raise ValueError('请先写入剧本再首看')
            # Inputs affect the validity of a generated change even when they are read-only.
            context=context_ids(state,selected,skill) if mode=='edit' else set(selected)
            basis={identity:entities[identity]['revision'] for identity in context}
            identity=str(uuid4())
            db.execute('INSERT INTO agent_task(id,prompt,scope,basis,status,worker,lease_until,result,created,skill,mode) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                (identity,prompt.strip(),encoded(sorted(selected)),encoded(basis),'queued',None,None,None,time.time(),skill,mode))
            return identity

    def claim(self,identity,worker,seconds=300):
        if not worker or not worker.strip():raise ValueError('执行者不能为空')
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM agent_task WHERE id=?',(identity,)).fetchone()
            if not row:raise ValueError('任务不存在')
            if row['status'] not in ('queued','running') or (row['status']=='running' and row['lease_until']>time.time() and row['worker']!=worker):
                raise ValueError('任务已由其他执行者接手或已结束')
            db.execute('UPDATE agent_task SET status=?,worker=?,lease_until=? WHERE id=?',('running',worker,time.time()+seconds,identity))
            task=self.decode(db.execute('SELECT * FROM agent_task WHERE id=?',(identity,)).fetchone())
            state=self.store._state(db)
            if task['mode']=='script_review':
                # Only script content crosses the reviewer boundary, including on-disk context.
                visible=[]
                for entity in state['entities']:
                    if entity['id'] not in task['scope']:continue
                    keys=('name','code','order') if entity['kind']=='episode' else ('name','code','order','text','parent_id')
                    visible.append({'id':entity['id'],'kind':entity['kind'],'revision':entity['revision'],
                                    'data':{key:entity['data'][key] for key in keys if key in entity['data']}})
                state={'project':{'revision':state['project']['revision']},'entities':visible,'dependencies':[]}
            else:
                state=project_context(state,set(task['basis']))
            return {'task':task,'project':state}

    def cancel(self,identity):
        with self.store.connection() as db:
            row=db.execute('SELECT status FROM agent_task WHERE id=?',(identity,)).fetchone()
            if not row or row['status'] not in ('queued','running'):raise ValueError('任务已结束')
            db.execute("UPDATE agent_task SET status='cancelled',lease_until=NULL WHERE id=?",(identity,))

    def renew(self,identity,worker,seconds=90):
        with self.store.connection() as db:
            result=db.execute("UPDATE agent_task SET lease_until=? WHERE id=? AND status='running' AND worker=? AND lease_until>=?",
                              (time.time()+seconds,identity,worker,time.time()))
            return result.rowcount==1

    def fail(self,identity,worker,message,operations=None):
        with self.store.connection() as db:
            db.execute("UPDATE agent_task SET status='failed',lease_until=NULL,result=? WHERE id=? AND status='running' AND worker=?",
                       (encoded({'message':message,'operations':operations or []}),identity,worker))

    def recover(self):
        with self.store.connection() as db:
            db.execute("UPDATE agent_task SET status='failed',lease_until=NULL,result=? WHERE status='running' AND worker LIKE 'director-agent-%' AND lease_until<?",
                       (encoded({'message':'上次执行已中断，可按当前内容重试。'}),time.time()))

    def retry(self,identity):
        task=next((t for t in self.list() if t['id']==identity),None)
        if not task or task['status'] not in ('failed','cancelled'):raise ValueError('任务尚未结束')
        return self.create(task['prompt'],task['scope'],task.get('skill',''),task.get('mode','edit'))

    def finish(self,identity,worker,operations,message=''):
        # Scope validation and source checking happen in the same write transaction as the edit.
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM agent_task WHERE id=?',(identity,)).fetchone()
            if not row or row['status']!='running' or row['worker']!=worker or row['lease_until']<time.time():
                raise ValueError('任务未接手、已取消或租约已过期')
            task=self.decode(row);state=self.store._state(db);entities={e['id']:e for e in state['entities']}
            if task.get('mode')=='script_review' and operations:raise ValueError('首看任务只返回判断，不修改作品')
            if task.get('mode')=='script_review':
                episodes={identity for identity in task['scope'] if identity in entities and entities[identity]['kind']=='episode'}
                if any(e['kind']=='scene' and e['data'].get('parent_id') in episodes and e['id'] not in task['scope'] for e in entities.values()):
                    raise Conflict(state)
            if any(identity not in entities or entities[identity]['revision']!=rev for identity,rev in task['basis'].items()):
                raise Conflict(state)
            if task.get('mode')=='edit':
                current_scope=set(task['scope'])
                while True:
                    children={e['id'] for e in state['entities'] if e['data'].get('parent_id') in current_scope or e['data'].get('document_id') in current_scope}
                    if children<=current_scope:break
                    current_scope.update(children)
                if context_ids(state,current_scope,task.get('skill',''))!=set(task['basis']):
                    raise Conflict(state)
            allowed=set(task['scope'])
            kinds={identity:entity['kind'] for identity,entity in entities.items()}
            for op in operations:
                if op.get('type')=='create':
                    validate_agent_fields(op.get('kind'),op.get('data',{}))
                    kinds[op.get('id')]=op.get('kind')
                elif op.get('type')=='update' and op.get('id') in kinds:
                    validate_agent_fields(kinds[op['id']],op.get('patch',{}))
                if op.get('type')=='create':
                    if op.get('data',{}).get('parent_id') not in allowed and op.get('data',{}).get('document_id') not in allowed:raise ValueError('新增对象超出任务范围')
                    if not op.get('id'):raise ValueError('新增对象需要稳定ID')
                    allowed.add(op['id'])
                elif op.get('type') in ('bind','unbind'):
                    if op.get('target') not in allowed:raise ValueError('引用修改超出任务范围')
                elif op.get('id') not in allowed:raise ValueError('修改超出任务范围')
            after=self.store.apply(state['project']['revision'],operations,actor=worker,connection=db) if operations else state
            db.execute('UPDATE agent_task SET status=?,lease_until=NULL,result=? WHERE id=?',
                ('completed',encoded({'message':message,'revision':after['project']['revision']}),identity))
            return after
