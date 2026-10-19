#!/usr/bin/env python3
"""Append-only JSON Lines event log."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


class EventLog:
    def __init__(self, path: Path):
        self.path = path

    def emit(self, event_type: str, actor: str, **fields) -> dict:
        event = {
            "type": event_type,
            "actor": actor,
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **fields,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")
        return event

    def query(self, event_type: str | None = None, actor: str | None = None):
        if not self.path.exists():
            return []
        # A context manager guarantees the file is closed even if a line is malformed.
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event_type and event.get("type") != event_type:
                    continue
                if actor and event.get("actor") != actor:
                    continue
                yield event

    def stats(self) -> dict:
        by_type, by_actor = {}, {}
        total = 0
        for event in self.query():
            total += 1
            by_type[event["type"]] = by_type.get(event["type"], 0) + 1
            by_actor[event["actor"]] = by_actor.get(event["actor"], 0) + 1
        return {"total": total,
                "by_type": dict(sorted(by_type.items())),
                "by_actor": dict(sorted(by_actor.items()))}

    def rotate(self, keep: int = 5) -> list:
        if keep < 1:
            raise ValueError("keep must be >= 1")
        if not self.path.exists():
            return []
        archived = []
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        archive = self.path.with_name(f"{self.path.name}.{stamp}")
        self.path.replace(archive)
        archived.append(archive)
        old = sorted(self.path.parent.glob(f"{self.path.name}.*"))[:-keep]
        for path in old:
            path.unlink(missing_ok=True)
            archived.append(path)
        return archived


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="VictorHub event log")
    parser.add_argument("--path", type=Path, default=Path("events.jsonl"))
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("emit")
    p.add_argument("event_type")
    p.add_argument("actor")

    p = sub.add_parser("query")
    p.add_argument("--type")
    p.add_argument("--actor")

    sub.add_parser("stats")

    p = sub.add_parser("rotate")
    p.add_argument("--keep", type=int, default=5)

    args = parser.parse_args(argv)
    log = EventLog(args.path)
    if args.command == "emit":
        print(json.dumps(log.emit(args.event_type, args.actor)))
    elif args.command == "query":
        for event in log.query(args.type, args.actor):
            print(f"{event['at']} {event['type']:<14} {event['actor']}")
    elif args.command == "stats":
        print(json.dumps(log.stats(), indent=2))
    else:
        removed = log.rotate(args.keep)
        print(f"rotated; archived {len(removed)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
