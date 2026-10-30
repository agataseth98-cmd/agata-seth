import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parents[1]; SCRIPT = ROOT / "mesh.py"

def test_prepare_isolates_roles_and_consolidates_missing(tmp_path):
    spec = tmp_path / "spec.md"; spec.write_text("# Spec\n\nContrato", encoding="utf-8")
    out = tmp_path / "reviews"
    subprocess.run([sys.executable, str(SCRIPT), "prepare", str(spec), str(out)], check=True)
    assert (out / "simplificador" / "packet.md").exists()
    assert (out / "operador" / "packet.md").exists()
    report = tmp_path / "consolidated.md"
    subprocess.run([sys.executable, str(SCRIPT), "consolidate", str(out), str(report)], check=True)
    text = report.read_text(encoding="utf-8")
    assert "Relatório ausente" in text
    assert "implementador" in text
