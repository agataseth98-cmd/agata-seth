import importlib.util
from pathlib import Path


HERE = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("github_flow", HERE / "github_flow.py")
flow = importlib.util.module_from_spec(spec); spec.loader.exec_module(flow)


def test_missing_approval_is_blocking(tmp_path):
    try:
        flow.approval(tmp_path, "demo")
    except SystemExit as exc:
        assert "assinatura ausente" in str(exc)
    else:
        raise AssertionError("approval gate must block")


def test_approval_path_is_exact(tmp_path):
    path = tmp_path / "propostas" / "APROVADO-demo"
    path.parent.mkdir(); path.write_text("signed", encoding="utf-8")
    assert flow.approval(tmp_path, "demo") == path
