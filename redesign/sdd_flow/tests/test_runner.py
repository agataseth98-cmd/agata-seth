import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "sdd_flow" / "runner.py"


def invoke(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], check=True, capture_output=True, text=True)


def test_runner_records_mechanical_stages_without_deciding(tmp_path):
    project = tmp_path / "project"; project.mkdir()
    (project / "README.md").write_text("# Demo\n", encoding="utf-8")
    out = tmp_path / "kit"; state = tmp_path / "state.json"
    invoke(state, "bootstrap", project, out, "--goal", "goal")
    invoke(state, "review", out)
    (out / "review-package" / "operador" / "report.md").write_text("achado", encoding="utf-8")
    invoke(state, "consolidate", out)
    data = json.loads(state.read_text(encoding="utf-8"))
    assert data["stage"] == "decision"
    assert [entry["stage"] for entry in data["history"]] == ["bootstrap", "review", "decision"]
    assert "Aguardando decisão humana" in (out / "decision.md").read_text(encoding="utf-8")


def test_status_on_missing_state_is_non_mutating(tmp_path):
    state = tmp_path / "state.json"
    result = invoke(state, "status")
    assert json.loads(result.stdout)["stage"] == "new"
    assert not state.exists()


def test_complete_requires_gates_and_records_completion(tmp_path):
    state = tmp_path / "state.json"
    invoke(state, "decision", "--accepted")
    invoke(state, "implementation", tmp_path)
    invoke(state, "verify", "redesign/evidence_ledger/tests/test_ledger.py::test_append_verify_and_public_export")
    previous = tmp_path / "provenance.json"; previous.write_text('{"files": []}\n', encoding="utf-8")
    project = tmp_path / "project"; project.mkdir()
    output = tmp_path / "drift.md"
    invoke(state, "drift", project, previous, output)
    data = json.loads(state.read_text())
    artifacts = {}
    for key in ("spec", "consolidated_review", "evidence", "criterion_drift"):
        path = tmp_path / key; path.write_text("ok", encoding="utf-8"); artifacts[key] = str(path)
    data["artifacts"] = artifacts; state.write_text(json.dumps(data), encoding="utf-8")
    invoke(state, "complete")
    assert json.loads(state.read_text(encoding="utf-8"))["stage"] == "complete"
