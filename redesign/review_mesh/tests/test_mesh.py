import subprocess, sys, pytest
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

def test_prepare_refuses_overwrite_and_packet_contract(tmp_path):
    spec = tmp_path / "spec.md"; spec.write_text("# Spec", encoding="utf-8")
    out = tmp_path / "reviews"
    subprocess.run([sys.executable, str(SCRIPT), "prepare", str(spec), str(out)], check=True)
    report = out / "operador" / "report.md"; report.write_text("preservar", encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), "prepare", str(spec), str(out)], capture_output=True, text=True)
    assert result.returncode != 0
    assert report.read_text(encoding="utf-8") == "preservar"
    assert "report.md" in (out / "operador" / "packet.md").read_text(encoding="utf-8")
