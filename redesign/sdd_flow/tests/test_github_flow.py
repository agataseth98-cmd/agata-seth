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


def test_handoff_requires_recorded_cycle(tmp_path):
    for state in (None, tmp_path / "ausente.json"):
        try:
            flow.require_cycle(state)
        except SystemExit as exc:
            assert "--state" in str(exc)
        else:
            raise AssertionError("handoff must require a state")
    sem_ciclo = tmp_path / "s.json"; sem_ciclo.write_text('{"history": [{"stage": "decision"}]}', encoding="utf-8")
    try:
        flow.require_cycle(sem_ciclo)
    except SystemExit as exc:
        assert "ciclo SDD" in str(exc)
    else:
        raise AssertionError("handoff must require the cycle stage")
    com_ciclo = tmp_path / "c.json"; com_ciclo.write_text('{"history": [{"stage": "cycle"}]}', encoding="utf-8")
    flow.require_cycle(com_ciclo)
