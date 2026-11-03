import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[2]; RUNNER = ROOT / "sdd_flow" / "runner.py"


def call(state, *args):
    return subprocess.run([sys.executable, str(RUNNER), str(state), *map(str, args)], capture_output=True, text=True)


def test_complete_requires_integrated_artifacts(tmp_path):
    state = tmp_path / "state.json"
    for stage, detail in (("decision", "ok"), ("implementation", str(tmp_path)), ("verification", "ok"), ("drift", "ok")):
        call(state, "decision", "--accepted") if stage == "decision" else None
        if stage != "decision":
            data = json.loads(state.read_text()) if state.exists() else {"history": []}
            data.setdefault("history", []).append({"stage": stage, "detail": detail})
            state.write_text(json.dumps(data))
    result = call(state, "complete")
    assert result.returncode != 0
    assert "artefato" in result.stderr or "spec" in result.stderr
