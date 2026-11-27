"""Shared command interface for local Agents and the upcoming browser service."""
import argparse
import json
import sys

from store import Conflict, ProjectStore


def main():
    parser = argparse.ArgumentParser(description="Local director project commands")
    parser.add_argument("command", choices=["create", "state", "context", "apply", "undo", "redo", "entry-read", "entry-update", "generation-prepare",
                                           "draft", "drafts", "freeze", "snapshot", "review", "export", "backup",
                                           "tasks", "task-create", "task-claim", "task-finish"])
    parser.add_argument("--project", required=True)
    parser.add_argument("--actor", default="agent")
    parser.add_argument("--expected", type=int)
    parser.add_argument("--title")
    parser.add_argument("--id")
    parser.add_argument("--entry")
    parser.add_argument("--document")
    parser.add_argument("--adapter")
    parser.add_argument("--parameters",default="{}")
    parser.add_argument("--out")
    parser.add_argument("--episode")
    parser.add_argument("--scope", nargs='+')
    parser.add_argument("--skill",default="")
    args = parser.parse_args()
    try:
        store = ProjectStore(args.project)
        if args.command == 'generation-prepare':
            from library import Library
            from production import Production
            from entries import find_entry
            if not args.entry or not args.adapter:raise ValueError('请指定 --entry 和 --adapter')
            if store.root.parent.name!='projects':raise ValueError('请选择导演台作品库内的项目目录')
            library=Library(store.root.parent.parent)
            entity=find_entry(store.state(),args.entry,args.episode,args.document)
            parameters=json.load(sys.stdin) if args.parameters=='-' else json.loads(args.parameters)
            if not isinstance(parameters,dict):raise ValueError('parameters 必须是对象')
            result=Production(library).prepare(store.root.name,entity['id'],args.adapter,parameters)
        elif args.command in ('entry-read','entry-update'):
            from entries import read_entry,update_entry
            if not args.entry:raise ValueError('请指定 --entry 稳定ID或条目编号')
            result=read_entry(store,args.entry,args.episode,args.document) if args.command=='entry-read' else update_entry(store,args.entry,args.expected,json.load(sys.stdin),args.episode,args.document,args.actor)
        elif args.command=='context':
            from creative_context import context_ids,project_context
            from entries import find_entry
            state=store.state()
            selected=args.scope or ([find_entry(state,args.entry,args.episode,args.document)['id']] if args.entry else [])
            if not selected or not set(selected)<={e['id'] for e in state['entities']}:raise ValueError('请选择存在的条目 --entry 或 --scope')
            result={'revision':state['project']['revision'],'project':project_context(state,context_ids(state,selected,args.skill))}
        elif args.command.startswith('task'):
            from tasks import TaskQueue
            queue=TaskQueue(store)
            if args.command=='tasks':result=queue.list()
            elif args.command=='task-create':result={'id':queue.create(sys.stdin.read(),args.scope,args.skill)}
            elif args.command=='task-claim':result=queue.claim(args.id,args.actor)
            else:
                payload=json.load(sys.stdin)
                result=queue.finish(args.id,args.actor,payload['operations'],payload.get('message',''))
        elif args.command == "create":
            result = ProjectStore.create(args.project, args.title).state()
        elif args.command in {"export", "backup"}:
            from transfer import export_project
            if not args.out:raise ValueError("请选择导出位置")
            result=export_project(store,args.out,'backup' if args.command=='backup' else 'editable',args.episode)
        elif args.command == "state":
            result = store.state()
        elif args.command in {"apply", "undo", "redo", "review"}:
            if args.expected is None:
                raise ValueError("修改需要当前项目版本")
            if args.command == "apply":
                result = store.apply(args.expected, json.load(sys.stdin), args.actor)
            elif args.command == "review":
                result = store.review(args.id, args.expected, args.actor)
            else:
                result = getattr(store, args.command)(args.expected, args.actor)
        elif args.command == "draft":
            if not args.id or args.expected is None:
                raise ValueError("草稿需要对象与基础版本")
            store.save_draft(args.actor, args.id, args.expected, json.load(sys.stdin))
            result = {"saved": True}
        elif args.command == "drafts":
            result = store.drafts(args.actor)
        elif args.command == "freeze":
            result = {"id": store.freeze(args.title or "版本快照")}
        else:
            result = store.snapshot(args.id)
        print(json.dumps({"ok": True, "data": result}, ensure_ascii=False))
        return 0
    except Conflict as error:
        print(json.dumps({"ok": False, "error": "conflict", "message": str(error),
                          "current": error.current}, ensure_ascii=False))
        return 3
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(json.dumps({"ok": False, "error": "invalid_request", "message": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
