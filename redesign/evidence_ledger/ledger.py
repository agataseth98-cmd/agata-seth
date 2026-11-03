#!/usr/bin/env python3
"""Evidence Ledger offline: append, verify and public export."""
from __future__ import annotations
import argparse, hashlib, json, fcntl, os
from pathlib import Path

KINDS = {"observation", "decision", "proposal", "approval", "execution", "verification", "drift", "correction"}
LEVELS = {"public", "project", "private", "secret"}
REQUIRED = {"id", "timestamp", "actor", "project", "kind", "status", "source", "classification"}

def normalized(event):
    return {k: event[k] for k in sorted(event) if k != "event_hash"}

def digest(event):
    return hashlib.sha256(json.dumps(normalized(event), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def validate(event):
    missing = REQUIRED - set(event)
    if missing:
        raise ValueError("campos ausentes: " + ", ".join(sorted(missing)))
    if event["kind"] not in KINDS or event["classification"] not in LEVELS:
        raise ValueError("kind/classification inválido")
    if event["classification"] == "secret":
        raise ValueError("secret não entra no ledger")

class LedgerCorruptError(ValueError):
    """The ledger contains an invalid record and must not be repaired implicitly."""


def _records(handle):
    handle.seek(0)
    records = []
    for n, line in enumerate(handle, 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            suffix = " (linha final possivelmente truncada)" if not line.endswith("\n") else ""
            raise LedgerCorruptError(f"JSON inválido na linha {n}{suffix}") from exc
    return records


def read(path):
    if not path.exists(): return []
    with path.open("r", encoding="utf-8") as handle:
        return _records(handle)

def append(path, event):
    validate(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        old = _records(handle)
        event = dict(event)
        event["prev_hash"] = old[-1]["event_hash"] if old else None
        event["event_hash"] = digest(event)
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

def verify(path):
    previous = None
    for n, event in enumerate(read(path), 1):
        validate(event)
        if event.get("prev_hash") != previous: raise ValueError(f"prev_hash inválido na linha {n}")
        if event.get("event_hash") != digest(event): raise ValueError(f"event_hash inválido na linha {n}")
        previous = event["event_hash"]
    return True

def export_public(source, target):
    events = read(source)
    public = [e for e in events if e.get("classification") == "public"]
    target.write_text("".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in public), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    v = sub.add_parser("verify"); v.add_argument("ledger", type=Path)
    e = sub.add_parser("export-public"); e.add_argument("ledger", type=Path); e.add_argument("output", type=Path)
    a = sub.add_parser("append"); a.add_argument("ledger", type=Path); a.add_argument("event_json", type=Path)
    args = ap.parse_args()
    if args.command == "verify": verify(args.ledger); print("OK")
    elif args.command == "export-public": verify(args.ledger); export_public(args.ledger, args.output); print("OK")
    else: append(args.ledger, json.loads(args.event_json.read_text(encoding="utf-8"))); print("OK")

if __name__ == "__main__": main()
