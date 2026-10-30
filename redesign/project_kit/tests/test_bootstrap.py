import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "bootstrap.py"


def test_bootstrap_ignores_venv_and_writes_contract(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("# Demo\n", encoding="utf-8")
    (project / ".venv").mkdir()
    (project / ".venv" / "secret.txt").write_text("do not include", encoding="utf-8")
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(SCRIPT), str(project), "--out", str(out), "--goal", "testar kit"], check=True)
    data = json.loads((out / "provenance.json").read_text(encoding="utf-8"))
    paths = {item["path"] for item in data["files"]}
    assert paths == {"README.md"}
    assert "testar kit" in (out / "concept-brief.md").read_text(encoding="utf-8")
    assert (out / "reviews" / "README.md").exists()


def test_drift_report_detects_added_removed_and_changed(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "keep.txt").write_text("one", encoding="utf-8")
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(SCRIPT), str(project), "--out", str(out), "--goal", "drift"], check=True)
    (project / "keep.txt").write_text("two", encoding="utf-8")
    (project / "added.txt").write_text("new", encoding="utf-8")
    report = tmp_path / "drift.md"
    subprocess.run([sys.executable, str(SCRIPT), str(project), "--out", str(tmp_path / "unused"), "--goal", "drift", "--drift-against", str(out / "provenance.json"), "--drift-out", str(report)], check=True)
    text = report.read_text(encoding="utf-8")
    assert "added.txt" in text
    assert "keep.txt" in text


def test_bootstrap_can_record_public_ledger_event(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("# Demo\n", encoding="utf-8")
    out = tmp_path / "out"
    ledger = tmp_path / "ledger.jsonl"
    subprocess.run([sys.executable, str(SCRIPT), str(project), "--out", str(out), "--goal", "ledger", "--ledger", str(ledger)], check=True)
    data = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
    assert data["kind"] == "observation"
    assert data["classification"] == "public"
    assert data["output_hash"]
