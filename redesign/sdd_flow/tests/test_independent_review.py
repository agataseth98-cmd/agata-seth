import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "independent_review.py"
ROLES = ("simplificador", "operador", "implementador")


def test_consolidation_preserves_all_role_reports(tmp_path):
    root = tmp_path / "reviews"
    for role in ROLES:
        path = root / role; path.mkdir(parents=True)
        (path / "report.md").write_text(f"## Contexto do revisor\n{role}\n\n## Veredito\nrevisar\n\n## Achados\n{role}-achado\n", encoding="utf-8")
    out = tmp_path / "consolidated.md"
    subprocess.run([sys.executable, str(SCRIPT), str(root), str(out)], check=True)
    text = out.read_text(encoding="utf-8")
    assert all(role + "-achado" in text for role in ROLES)


def test_incomplete_report_blocks(tmp_path):
    root = tmp_path / "reviews"; (root / ROLES[0]).mkdir(parents=True)
    (root / ROLES[0] / "report.md").write_text("## Veredito\nrevisar\n", encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), str(root), str(tmp_path / "out")], capture_output=True, text=True)
    assert result.returncode != 0
    assert "relatório incompleto" in result.stderr
