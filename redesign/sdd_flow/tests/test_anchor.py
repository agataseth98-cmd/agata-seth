import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "anchor.py"
SPEC = "# Spec\n\n## Contrato\n\nx\n\n## Critérios de aceite\n\n- [ ] a\n\n## Código\n\n- `a.py`\n"


def anchor(repo, *scopes):
    return subprocess.run([sys.executable, str(SCRIPT), str(repo), *scopes], capture_output=True, text=True)


def component(tmp_path, spec=SPEC):
    comp = tmp_path / "comp"; comp.mkdir()
    (comp / "SPEC.md").write_text(spec, encoding="utf-8")
    (comp / "a.py").write_text("x = 1\n", encoding="utf-8")
    return comp


def test_anchored_component_passes(tmp_path):
    component(tmp_path)
    assert anchor(tmp_path, "comp").returncode == 0


def test_orphan_code_blocks(tmp_path):
    comp = component(tmp_path)
    (comp / "novo.py").write_text("y = 2\n", encoding="utf-8")
    result = anchor(tmp_path, "comp")
    assert result.returncode != 0 and "novo.py" in result.stderr


def test_ghost_entry_and_missing_spec_block(tmp_path):
    comp = component(tmp_path, SPEC + "- `fantasma.py`\n")
    assert "fantasma.py" in anchor(tmp_path, "comp").stderr
    (comp / "SPEC.md").unlink()
    assert "sem SPEC.md" in anchor(tmp_path, "comp").stderr


def test_missing_section_blocks(tmp_path):
    component(tmp_path, "# Spec\n\n## Contrato\n\nx\n\n## Código\n\n- `a.py`\n")
    assert "Critérios de aceite" in anchor(tmp_path, "comp").stderr
