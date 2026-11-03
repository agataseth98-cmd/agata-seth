import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "spec_gate.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def test_init_blocks_until_all_sections_and_decision_are_filled(tmp_path):
    root = tmp_path / "sdd"
    assert run("init", root).returncode == 0
    result = run("check", root)
    assert result.returncode != 0
    assert "brainstorm:" in result.stderr
    for name in ("brainstorm.md", "spec.md"):
        path = root / name
        text = path.read_text(encoding="utf-8").replace("[preencher]", "evidência")
        path.write_text(text, encoding="utf-8")
    (root / "decision.md").write_text("# Decisão\n\nDECISAO: aceita\n", encoding="utf-8")
    assert run("check", root).stdout.strip() == "SPEC GATES: OK"
