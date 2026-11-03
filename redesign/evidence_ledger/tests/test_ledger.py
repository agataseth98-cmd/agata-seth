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

def test_concurrent_appends_preserve_chain(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    worker = """import json, subprocess, sys\nfrom pathlib import Path\nscript, ledger, directory, prefix = map(Path, sys.argv[1:])\nfor i in range(40):\n    event = {'id': f'{prefix}-{i}', 'timestamp': '2026-10-30T19:00:00Z', 'actor': 'test', 'project': 'demo', 'kind': 'observation', 'status': 'ok', 'source': 'test', 'classification': 'public'}\n    source = directory / f'{prefix}-{i}.json'; source.write_text(json.dumps(event), encoding='utf-8')\n    subprocess.run([sys.executable, str(script), 'append', str(ledger), str(source)], check=True)\n"""
    a = subprocess.Popen([sys.executable, "-c", worker, str(SCRIPT), str(ledger), str(tmp_path), "a"])
    b = subprocess.Popen([sys.executable, "-c", worker, str(SCRIPT), str(ledger), str(tmp_path), "b"])
    assert a.wait() == b.wait() == 0
    run("verify", ledger)
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 80

def test_truncated_final_line_is_explicit_and_preserved(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    item = tmp_path / "e.json"; item.write_text(json.dumps(event()), encoding="utf-8")
    run("append", ledger, item)
    ledger.open("ab").write(b'{"id":"truncated"')
    before = ledger.read_bytes()
    result = subprocess.run([sys.executable, str(SCRIPT), "append", str(ledger), str(item)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "truncada" in result.stderr
    assert ledger.read_bytes() == before
