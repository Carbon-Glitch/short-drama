"""Transactional, local creative project store. No provider or renderer dependencies."""
from __future__ import annotations

from contextlib import contextmanager, nullcontext
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import time
from uuid import uuid4
from dialogue import sync_dialogue


KINDS = frozenset({"project_settings", "episode", "scene", "character", "look", "location", "prop",
                   "dialogue", "shot", "submission", "media", "cut_binding", "note", "document", "design", "image_prompt"})


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


class Conflict(Exception):
    def __init__(self, current):
        super().__init__("内容已被更新；你的修改仍可保留并比较。")
        self.current = current


class ProjectStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.path = self.root / ".short-drama/state/project.sqlite"

    @classmethod
    def create(cls, root, title):
        store = cls(root)
        if store.path.exists():
            raise ValueError("项目已存在")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("请输入项目名称")
        store.path.parent.mkdir(parents=True, exist_ok=True)
        with store.connection() as db:
            db.executescript("""
              CREATE TABLE project(id TEXT PRIMARY KEY, title TEXT NOT NULL,
                revision INTEGER NOT NULL, schema_version INTEGER NOT NULL);
              CREATE TABLE entity(id TEXT PRIMARY KEY, kind TEXT NOT NULL,
                data TEXT NOT NULL, revision INTEGER NOT NULL, stale INTEGER NOT NULL);
              CREATE TABLE dependency(source TEXT NOT NULL, target TEXT NOT NULL,
                fields TEXT NOT NULL, source_revision INTEGER NOT NULL,
                PRIMARY KEY(source,target),
                FOREIGN KEY(source) REFERENCES entity(id),
                FOREIGN KEY(target) REFERENCES entity(id));
              CREATE TABLE event(id INTEGER PRIMARY KEY, actor TEXT NOT NULL,
                before_state TEXT NOT NULL, after_state TEXT NOT NULL, created REAL NOT NULL);
              CREATE TABLE snapshot(id TEXT PRIMARY KEY, title TEXT NOT NULL,
                revision INTEGER NOT NULL, content TEXT NOT NULL, created REAL NOT NULL);
              CREATE TABLE draft(actor TEXT NOT NULL, entity TEXT NOT NULL,
                base_revision INTEGER NOT NULL, content TEXT NOT NULL, updated REAL NOT NULL,
                PRIMARY KEY(actor,entity));
              CREATE TABLE undo_stack(position INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL);
              CREATE TABLE redo_stack(position INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL);
            """)
            db.execute("INSERT INTO project VALUES(?,?,0,1)", (str(uuid4()), title.strip()))
        return store

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _state(self, db):
        project = dict(db.execute("SELECT * FROM project").fetchone())
        entities = [{**dict(r), "data": json.loads(r["data"]), "stale": bool(r["stale"])}
                    for r in db.execute("SELECT * FROM entity ORDER BY id")]
        dependencies = [{**dict(r), "fields": json.loads(r["fields"])}
                        for r in db.execute("SELECT * FROM dependency ORDER BY source,target")]
        return {"project": project, "entities": entities, "dependencies": dependencies}

    def state(self):
        with self.connection() as db:
            return self._state(db)

    @staticmethod
    def _validate(state):
        entities = {e["id"]: e for e in state["entities"]}
        for entity in entities.values():
            if entity["kind"] not in KINDS or not isinstance(entity["data"], dict):
                raise ValueError("未知对象类型或无效内容")
            encoded(entity["data"])
            document=entity['data'].get('document_id')
            if document and (document not in entities or entities[document]['kind']!='document' or
                    entity['data'].get('parent_id')!=entities[document]['data'].get('parent_id')):
                raise ValueError('条目的所属文档无效')
            parent = entity["data"].get("parent_id")
            if parent and parent not in entities:
                raise ValueError("所属对象不存在")
            seen = {entity["id"]}
            while parent:
                if parent in seen:
                    raise ValueError("不能把对象移入自身的下级")
                seen.add(parent)
                parent = entities[parent]["data"].get("parent_id")
        for dep in state["dependencies"]:
            if dep["source"] not in entities or dep["target"] not in entities:
                raise ValueError("引用的对象不存在")
            if dep["source"] == dep["target"]:
                raise ValueError("对象不能依赖自身")
            if not isinstance(dep["fields"], list) or any(not isinstance(f, str) for f in dep["fields"]):
                raise ValueError("引用字段必须是字符串列表")

    @staticmethod
    def _invalidate(state, changes):
        entities = {e["id"]: e for e in state["entities"]}
        queue = list(changes.items())
        visited = set()
        while queue:
            source, fields = queue.pop(0)
            for dep in state["dependencies"]:
                if dep["source"] != source:
                    continue
                # None means a previously affected derived object; all its dependents need review.
                if fields is not None and dep["fields"] and not set(dep["fields"]) & fields:
                    continue
                target = dep["target"]
                if target in visited:
                    continue
                visited.add(target)
                entities[target]["stale"] = True
                queue.append((target, None))

    @staticmethod
    def _write(db, state):
        db.execute("DELETE FROM dependency")
        db.execute("DELETE FROM entity")
        db.executemany("INSERT INTO entity VALUES(?,?,?,?,?)", [
            (e["id"], e["kind"], encoded(e["data"]), e["revision"], int(e["stale"]))
            for e in state["entities"]])
        db.executemany("INSERT INTO dependency VALUES(?,?,?,?)", [
            (d["source"], d["target"], encoded(d["fields"]), d["source_revision"])
            for d in state["dependencies"]])
        db.execute("UPDATE project SET revision=?", (state["project"]["revision"],))

    def apply(self, expected_revision, operations, actor="user", connection=None):
        """Apply the entire command batch or none of it; clients retain drafts on conflict."""
        if not isinstance(operations, list) or not operations:
            raise ValueError("修改不能为空")
        with (nullcontext(connection) if connection is not None else self.connection()) as db:
            if connection is None:db.execute("BEGIN IMMEDIATE")
            before = self._state(db)
            if before["project"]["revision"] != expected_revision:
                raise Conflict(before)
            state = deepcopy(before)
            entities = {e["id"]: e for e in state["entities"]}
            revision = expected_revision + 1
            changes = {}
            for operation in operations:
                action = operation.get("type")
                identity = operation.get("id")
                if action == "create":
                    identity = identity or str(uuid4())
                    if not isinstance(identity, str) or not identity or identity in entities:
                        raise ValueError("对象ID无效或已存在")
                    entities[identity] = {"id": identity, "kind": operation["kind"],
                        "data": deepcopy(operation.get("data", {})), "revision": revision, "stale": False}
                elif action == "update":
                    entity = entities[identity]
                    patch = operation["patch"]
                    if entity["kind"]=="dialogue" and entity["data"].get("derived_from_scene"):
                        raise ValueError("请修改所属场景正文，对白关联由系统同步")
                    if not isinstance(patch, dict):
                        raise ValueError("修改内容必须是对象")
                    if entity['kind']=='document' and entity['data'].get('structured') and 'original' in patch:
                        raise ValueError('请编辑具体条目，文档由条目自动生成')
                    if entity["kind"] == "media" and any(k in patch and patch[k] != entity["data"].get(k)
                            for k in ("path", "sha256", "type")):
                        raise ValueError("素材版本不能覆盖，请导入新版本")
                    fields = {k for k, v in patch.items() if entity["data"].get(k) != v}
                    entity["data"].update(deepcopy(patch))
                    if fields:
                        entity["revision"] = revision
                        if identity not in changes:
                            changes[identity] = set()
                        if changes[identity] is not None:
                            changes[identity].update(fields)
                elif action == "bind":
                    source, target = operation["source"], operation["target"]
                    if source not in entities or target not in entities:
                        raise ValueError("引用的对象不存在")
                    state["dependencies"] = [d for d in state["dependencies"]
                        if (d["source"], d["target"]) != (source, target)]
                    state["dependencies"].append({"source": source, "target": target,
                        "fields": operation.get("fields", []), "source_revision": entities[source]["revision"]})
                    entities[target]["revision"] = revision
                    entities[target]["stale"] = True
                    changes[target] = None
                elif action == "delete":
                    del entities[identity]
                    dependents = [d["target"] for d in state["dependencies"] if d["source"] == identity]
                    for target in dependents:
                        entities[target]["stale"] = True
                        changes[target] = None
                    state["dependencies"] = [d for d in state["dependencies"]
                        if identity not in (d["source"], d["target"])]
                elif action == "unbind":
                    source, target = operation["source"], operation["target"]
                    entities[target]["revision"] = revision
                    entities[target]["stale"] = True
                    state["dependencies"] = [d for d in state["dependencies"]
                        if (d["source"], d["target"]) != (source, target)]
                    changes[target] = None
                else:
                    raise ValueError("未知修改操作")
            state["entities"] = list(entities.values())
            state["project"]["revision"] = revision
            sync_dialogue(before,state,revision,changes)
            self._validate(state)
            self._invalidate(state, changes)
            self._write(db, state)
            after = self._state(db)
            db.execute("INSERT INTO event VALUES(?,?,?,?,?)",
                       (revision, actor, encoded(before), encoded(after), time.time()))
            db.execute("INSERT INTO undo_stack(event_id) VALUES(?)", (revision,))
            db.execute("DELETE FROM redo_stack")
            return after

    def review(self, identity, expected_revision, actor="user"):
        """Accept a reviewed dependency state without modifying historical outputs."""
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            before = self._state(db)
            if before["project"]["revision"] != expected_revision:
                raise Conflict(before)
            state = deepcopy(before)
            entities = {e["id"]: e for e in state["entities"]}
            entity = entities[identity]
            deps = [d for d in state["dependencies"] if d["target"] == identity]
            if any(entities[d["source"]]["stale"] for d in deps):
                raise ValueError("先处理上游的待复核内容")
            for dep in deps:
                dep["source_revision"] = entities[dep["source"]]["revision"]
            entity["stale"] = False
            state["project"]["revision"] += 1
            self._write(db, state)
            after = self._state(db)
            db.execute("INSERT INTO event VALUES(?,?,?,?,?)", (state["project"]["revision"], actor,
                encoded(before), encoded(after), time.time()))
            db.execute("INSERT INTO undo_stack(event_id) VALUES(?)", (state["project"]["revision"],))
            db.execute("DELETE FROM redo_stack")
            return after

    def undo(self, expected_revision, actor="user"):
        return self._restore(expected_revision, actor, redo=False)

    def redo(self, expected_revision, actor="user"):
        return self._restore(expected_revision, actor, redo=True)

    def _restore(self, expected_revision, actor, redo):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            before = self._state(db)
            if before["project"]["revision"] != expected_revision:
                raise Conflict(before)
            source, target = ("redo_stack", "undo_stack") if redo else ("undo_stack", "redo_stack")
            entry = db.execute(f"SELECT * FROM {source} ORDER BY position DESC LIMIT 1").fetchone()
            if entry is None:
                raise ValueError("没有可以撤销的修改")
            event = db.execute("SELECT * FROM event WHERE id=?", (entry["event_id"],)).fetchone()
            state = json.loads(event["after_state"] if redo else event["before_state"])
            state["project"]["revision"] = expected_revision + 1
            self._write(db, state)
            after = self._state(db)
            db.execute("INSERT INTO event VALUES(?,?,?,?,?)", (expected_revision + 1, actor,
                encoded(before), encoded(after), time.time()))
            db.execute(f"DELETE FROM {source} WHERE position=?", (entry["position"],))
            db.execute(f"INSERT INTO {target}(event_id) VALUES(?)", (entry["event_id"],))
            return after

    def save_draft(self, actor, identity, base_revision, content):
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO draft VALUES(?,?,?,?,?)",
                       (actor, identity, base_revision, encoded(content), time.time()))

    def drafts(self, actor):
        with self.connection() as db:
            return [{**dict(r), "content": json.loads(r["content"])}
                    for r in db.execute("SELECT * FROM draft WHERE actor=?", (actor,))]

    def clear_draft(self, actor, identity, content):
        with self.connection() as db:
            db.execute("DELETE FROM draft WHERE actor=? AND entity=? AND content=?", (actor, identity, encoded(content)))

    def freeze(self, title):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._state(db)
            identity = str(uuid4())
            db.execute("INSERT INTO snapshot VALUES(?,?,?,?,?)",
                       (identity, title, state["project"]["revision"], encoded(state), time.time()))
            return identity

    def snapshot(self, identity):
        with self.connection() as db:
            row = db.execute("SELECT content FROM snapshot WHERE id=?", (identity,)).fetchone()
            if row is None:
                raise KeyError(identity)
            return json.loads(row["content"])
