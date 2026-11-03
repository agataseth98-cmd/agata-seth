import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "criterion_drift.py"


def test_drift_reports_each_criterion_and_blocks_missing_evidence(tmp_path):
    spec = tmp_path / "spec.md"; spec.write_text("# Spec\n\n- [ ] aceite A\n- [ ] aceite B\n", encoding="utf-8")
    evidence = tmp_path / "evidence.json"; evidence.write_text(json.dumps([{"criterion": "aceite A", "status": "pass", "classification": "intentional"}]), encoding="utf-8")
    output = tmp_path / "drift.md"
    result = subprocess.run([sys.executable, str(SCRIPT), str(spec), str(evidence), str(output)], capture_output=True, text=True)
    assert result.returncode != 0
    text = output.read_text(encoding="utf-8")
    assert "aceite A" in text and "aceite B" in text and "unmeasured" in text


def test_drift_passes_when_all_criteria_have_evidence(tmp_path):
    spec = tmp_path / "spec.md"; spec.write_text("- [x] aceite A\n", encoding="utf-8")
    evidence = tmp_path / "evidence.json"; evidence.write_text(json.dumps([{"criterion": "aceite A", "status": "pass", "classification": "intentional"}]), encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), str(spec), str(evidence), str(tmp_path / "drift.md")], capture_output=True, text=True)
    assert result.returncode == 0
