import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "acceptance_runner.py"


def test_acceptance_runner_emits_evidence_without_shell_interpretation(tmp_path):
    manifest = tmp_path / "manifest.json"; output = tmp_path / "evidence.json"
    manifest.write_text(json.dumps([{"criterion": "works", "command": [sys.executable, "-c", "print('ok')"]}]), encoding="utf-8")
    assert subprocess.run([sys.executable, str(SCRIPT), str(manifest), str(output)]).returncode == 0
    row = json.loads(output.read_text(encoding="utf-8"))[0]
    assert row["status"] == "pass" and row["classification"] == "verified"


def test_failed_acceptance_is_recorded_as_defect(tmp_path):
    manifest = tmp_path / "manifest.json"; output = tmp_path / "evidence.json"
    manifest.write_text(json.dumps([{"criterion": "fails", "command": [sys.executable, "-c", "raise SystemExit(2)"]}]), encoding="utf-8")
    assert subprocess.run([sys.executable, str(SCRIPT), str(manifest), str(output)]).returncode != 0
    assert json.loads(output.read_text(encoding="utf-8"))[0]["classification"] == "defect"
