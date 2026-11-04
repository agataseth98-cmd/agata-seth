import json
import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).parents[1] / "runner.py"
LEDGER = Path(__file__).parents[2] / "evidence_ledger" / "ledger.py"


def projeto(tmp_path, teste_ok=True, comando=None):
    raiz = tmp_path / "proj"
    (raiz / "tests").mkdir(parents=True); (raiz / "spec").mkdir()
    (raiz / "app.py").write_text("def dobro(x):\n    return x * 2\n", encoding="utf-8")
    (raiz / "conftest.py").write_text("", encoding="utf-8")
    (raiz / "tests" / "test_app.py").write_text(f"from app import dobro\n\n\ndef test_dobro():\n    assert dobro(2) == {4 if teste_ok else 5}\n", encoding="utf-8")
    secoes = {"brainstorm.md": ("Brainstorm", ("Usuários", "Estado que muda", "Erros e concorrência", "Migração", "Observabilidade", "Reversão", "Sucesso")),
              "spec.md": ("Spec", ("Jornadas críticas", "Contrato", "Critérios de aceite", "Desenho e alternativas", "Implementação e testes", "Migração e reversão", "Riscos e dependências"))}
    for arq, (titulo, nomes) in secoes.items():
        corpo = "".join(f"## {n}\n\n" + ("- [ ] dobra o número\n" if n == "Critérios de aceite" else "texto\n") + "\n" for n in nomes)
        (raiz / "spec" / arq).write_text(f"# {titulo}\n\n{corpo}" + ("## Código\n\n- `app.py`\n- `conftest.py`\n- `tests/`\n" if arq == "spec.md" else ""), encoding="utf-8")
    (raiz / "spec" / "decision.md").write_text("# Decisão\n\nDECISAO: aceita\n", encoding="utf-8")
    (raiz / "spec" / "acceptance.json").write_text(json.dumps([{"criterion": "dobra o número", "command": comando or ["pytest", "-q", "tests/test_app.py::test_dobro"]}]), encoding="utf-8")
    saida = tmp_path / "saida"
    desc = tmp_path / "d.json"
    desc.write_text(json.dumps({"nome": "proj", "raiz": str(raiz), "ambiente": {"PYTHONPATH": "."}, "saida": str(saida)}), encoding="utf-8")
    return raiz, saida, desc


def rodar(tmp_path, desc):
    return subprocess.run([sys.executable, str(RUNNER), str(tmp_path / "state.json"), "project", str(desc)], capture_output=True, text=True)


def arquivos(raiz):
    return sorted(p.relative_to(raiz).as_posix() for p in raiz.rglob("*") if p.is_file())


def test_ciclo_roda_sem_escrever_no_projeto_e_registra_no_ledger(tmp_path):
    raiz, saida, desc = projeto(tmp_path)
    antes = arquivos(raiz)
    r = rodar(tmp_path, desc)
    assert r.returncode == 0, r.stdout + r.stderr
    assert arquivos(raiz) == antes
    assert json.loads((saida / "ultimo.json").read_text())["ok"] is True
    assert subprocess.run([sys.executable, str(LEDGER), "verify", str(saida / "ledger.jsonl")], capture_output=True).returncode == 0


def test_falha_de_criterio_vira_evidencia_e_codigo_de_saida_1(tmp_path):
    raiz, saida, desc = projeto(tmp_path, teste_ok=False)
    r = rodar(tmp_path, desc)
    assert r.returncode == 1
    evento = json.loads((saida / "ledger.jsonl").read_text().splitlines()[-1])
    assert evento["status"] == "fail" and evento["metadata"]["falhas"] == ["critérios"]


def test_segunda_execucao_mede_o_drift_de_arquivos(tmp_path):
    raiz, saida, desc = projeto(tmp_path)
    rodar(tmp_path, desc)
    (raiz / "app.py").write_text("def dobro(x):\n    return 2 * x\n", encoding="utf-8")
    assert rodar(tmp_path, desc).returncode == 0
    ultimo = json.loads((saida / "ultimo.json").read_text())
    drift = (Path(ultimo["relatorio"]).parent / "file-drift.md").read_text(encoding="utf-8")
    assert "Alterados: 1" in drift and "app.py" in drift


def test_comando_livre_no_manifesto_e_recusado_sem_executar(tmp_path):
    raiz, saida, desc = projeto(tmp_path, comando=["bash", "-c", "touch invadido"])
    r = rodar(tmp_path, desc)
    assert r.returncode == 1 and not (raiz / "invadido").exists()


def test_descritor_invalido_sai_com_erro_claro(tmp_path):
    desc = tmp_path / "ruim.json"; desc.write_text(json.dumps({"nome": "x", "raiz": "relativa"}), encoding="utf-8")
    r = rodar(tmp_path, desc)
    assert r.returncode != 0 and "descritor inválido" in r.stderr


def test_duas_execucoes_no_mesmo_instante_nao_dividem_pasta(tmp_path):
    raiz, saida, desc = projeto(tmp_path)
    rodar(tmp_path, desc); rodar(tmp_path, desc)
    assert len(list((saida / "execucoes").iterdir())) == 2
