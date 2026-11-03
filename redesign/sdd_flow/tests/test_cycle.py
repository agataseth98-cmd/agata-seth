import json
import subprocess
import sys
from pathlib import Path


RUNNER = Path(__file__).parents[1] / "runner.py"


def test_cycle_stops_at_first_failing_gate(tmp_path):
    root = tmp_path / "spec"; root.mkdir()
    (root / "spec.md").write_text("# Spec\n", encoding="utf-8")
    manifest = tmp_path / "acceptance.json"; manifest.write_text("[]", encoding="utf-8")
    state = tmp_path / "state.json"
    result = subprocess.run([sys.executable, str(RUNNER), str(state), "cycle", str(root), str(manifest), "--scope", "redesign/sdd_flow"], capture_output=True, text=True)
    assert result.returncode != 0
    assert not (root / "evidence.json").exists()
    assert "cycle" not in {e["stage"] for e in (json.loads(state.read_text())["history"] if state.exists() else [])}
