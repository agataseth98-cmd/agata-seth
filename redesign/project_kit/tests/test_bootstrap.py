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
