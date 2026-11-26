"""Shared command interface for local Agents and the upcoming browser service."""
import argparse
import json
import sys

from store import Conflict, ProjectStore


def main():
    parser = argparse.ArgumentParser(description="Local director project commands")
    parser.add_argument("command", choices=["create", "state", "apply", "undo", "redo",
                                           "draft", "drafts", "freeze", "snapshot", "review", "export", "backup",
                                           "tasks", "task-create", "task-claim", "task-finish"])
    parser.add_argument("--project", required=True)
    parser.add_argument("--actor", default="agent")
    parser.add_argument("--expected", type=int)
    parser.add_argument("--title")
    parser.add_argument("--id")
    parser.add_argument("--out")
    parser.add_argument("--episode")
    parser.add_argument("--scope", nargs='+')
    args = parser.parse_args()
    try:
        store = ProjectStore(args.project)
        if args.command.startswith('task'):
            from tasks import TaskQueue
            queue=TaskQueue(store)
            if args.command=='tasks':result=queue.list()
            elif args.command=='task-create':result={'id':queue.create(sys.stdin.read(),args.scope)}
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
