import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "ledger.py"

def event(kind="observation", classification="public"):
    return {"id": "1", "timestamp": "2026-10-30T19:00:00Z", "actor": "test", "project": "demo", "kind": kind, "status": "ok", "source": "test", "classification": classification}

def run(*args): return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], check=True, capture_output=True, text=True)

def test_append_verify_and_public_export(tmp_path):
    ledger = tmp_path / "ledger.jsonl"; e1 = tmp_path / "e1.json"; e2 = tmp_path / "e2.json"
    e1.write_text(json.dumps(event()), encoding="utf-8"); e2.write_text(json.dumps(event("decision", "project")), encoding="utf-8")
    run("append", ledger, e1); run("append", ledger, e2); run("verify", ledger)
    public = tmp_path / "public.jsonl"; run("export-public", ledger, public)
    assert len(public.read_text().splitlines()) == 1

def test_tamper_is_detected(tmp_path):
    ledger = tmp_path / "ledger.jsonl"; e = tmp_path / "e.json"; e.write_text(json.dumps(event()), encoding="utf-8")
    run("append", ledger, e); data = json.loads(ledger.read_text()); data["status"] = "tampered"; ledger.write_text(json.dumps(data) + "\n")
    assert subprocess.run([sys.executable, str(SCRIPT), "verify", str(ledger)]).returncode != 0
