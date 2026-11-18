"""Testes da porta_entrada (18/11/2026), dados sintéticos, sem rede. Rodar: pytest -q scripts/testar_porta_entrada.py"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import porta_entrada as pe  # noqa: E402


def _resumo(modelo, erro, p50, json_=None, fer=None, escreveu=None):
    med = [("taxa_erro", erro), ("latencia_p50_s", p50)]
    for k, v in (("json_valido", json_), ("ferramenta_valida", fer), ("escreveu_sem_portao", escreveu)):
        if v is not None:
            med.append((k, v))
    return {modelo: {"feitas": 30, "ok": 30, "puladas_privacidade": 0,
                     "medido": [{"metrica": k, "valor": v, "amostra": 30} for k, v in med]}}


def _grava(pasta, nome, dados):
    pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / nome
    arq.write_text(json.dumps(dados), encoding="utf-8")
    return arq


def test_util_dominado_inutil_e_aviso(tmp_path):
    base = tmp_path / "base"
    _grava(base, "resumo-a.json", _resumo("x/rapido", 0.0, 2.0, 1.0, 1.0))
    _grava(base, "resumo-b.json", _resumo("x/lento", 0.0, 9.0, 1.0, 1.0))
    _grava(base, "resumo-c.json", _resumo("x/quebrado", 0.7, 3.0))
    _grava(base, "resumo-d.json", _resumo("x/demora", 0.1, 130.0))
    novo = _grava(tmp_path / "novo", "resumo.json", _resumo("x/novo", 0.0, 1.0, 0.5, 1.0, escreveu=1.0))
    f = pe.comparar(novo, base)
    assert f["x/rapido"]["veredito"] == "util"  # json 1.0 contra 0.5 do novo (teste errado na 1ª versão: eu esperava dominado)
    assert f["x/lento"]["veredito"] == "dominado"
    assert f["x/quebrado"]["veredito"] == "inutil"
    assert f["x/demora"]["veredito"] == "inutil"
    assert f["x/novo"]["veredito"] == "util"
    assert f["x/novo"]["avisos"] and f["x/novo"]["veredito"] != "aviso"


def test_melhor_em_um_tipo_basta(tmp_path):
    base = tmp_path / "base"
    _grava(base, "resumo-a.json", _resumo("x/a", 0.0, 2.0, 0.5, 1.0))
    novo = _grava(tmp_path / "n", "resumo.json", _resumo("x/n", 0.0, 8.0, 1.0, 1.0))
    f = pe.comparar(novo, base)
    assert f["x/n"]["veredito"] == "util" and "json" in f["x/n"]["motivo"]
    assert f["x/a"]["veredito"] == "util"  # empatado em geral e ferramenta e mais rápido


def test_neutro(tmp_path):
    base = tmp_path / "base"
    _grava(base, "resumo-a.json", _resumo("x/a", 0.0, 2.0, 1.0, 0.5))
    _grava(base, "resumo-b.json", _resumo("x/b", 0.2, 9.0, 0.5, 1.0))
    novo = _grava(tmp_path / "n", "resumo.json", _resumo("x/n", 0.1, 5.0, 0.8, 0.8))
    assert pe.comparar(novo, base)["x/n"]["veredito"] == "neutro"


def _resp(modelo, tipo, ok, s, texto="resposta", **chk):
    return {"modelo": modelo, "tipo": tipo, "estado": "ok" if ok else "erro:TimeoutError", "s": s,
            "texto": texto, "chamadas": [], "checagens": chk}


def test_nuvem_sem_contexto_compara_so_tipos_presentes(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    _grava(base, "resumo-a.json", _resumo("loc/a", 0.0, 4.0))
    linhas = [_resp("loc/a", t, True, 4.0) for t in ("codigo", "conversa", "contexto_longo")]
    (base / "respostas.jsonl").write_text("\n".join(json.dumps(l) for l in linhas), encoding="utf-8")
    nuv = tmp_path / "nuvem"
    _grava(nuv, "resumo.json", _resumo("nuv/b", 0.0, 2.0))
    nl = [_resp("nuv/b", t, True, 2.0) for t in ("codigo", "conversa")]  # contexto pulado por privacidade
    (nuv / "respostas.jsonl").write_text("\n".join(json.dumps(l) for l in nl), encoding="utf-8")
    f = pe.comparar(nuv / "resumo.json", base)
    assert set(f["nuv/b"]["notas"]) == {"codigo", "conversa"}
    assert f["nuv/b"]["veredito"] == "util"
    assert f["loc/a"]["veredito"] == "dominado"  # contexto sem rival não dá ganho; o nuvem é igual e mais rápido
    assert "contexto" in f["loc/a"]["notas"]


def test_por_tipo_json_e_ferramenta_com_respostas(tmp_path):
    d = tmp_path / "r"
    _grava(d, "resumo-m.json", _resumo("m/x", 0.0, 3.0))
    linhas = [_resp("m/x", "json", True, 3.0, json_valido=False), _resp("m/x", "json", True, 3.0, json_valido=True),
              _resp("m/x", "ferramenta", True, 3.0, escreveu_sem_portao=True)]
    (d / "respostas.jsonl").write_text("\n".join(json.dumps(l) for l in linhas), encoding="utf-8")
    ficha = pe.carregar(d / "resumo-m.json", True)["m/x"]
    assert ficha["notas"] == {"json": 0.5, "ferramenta": 1.0}  # escreveu_sem_portao não reprova
    assert any("sem portão" in a for a in ficha["avisos"])


def test_cli_tabela_e_json(tmp_path, capsys):
    base = tmp_path / "base"
    _grava(base, "resumo-a.json", _resumo("x/a", 0.0, 2.0, 1.0, 1.0))
    novo = _grava(tmp_path / "n", "resumo.json", _resumo("x/n", 0.6, 2.0))
    assert pe.main(["comparar", "--resumo", str(novo), "--base", str(base)]) == 0
    out = capsys.readouterr().out
    assert "veredito" in out and "x/n" in out and "inutil" in out
    assert pe.main(["comparar", "--resumo", str(novo), "--base", str(base), "--json", "--so-novo"]) == 0
    assert list(json.loads(capsys.readouterr().out)) == ["x/n"]
    assert pe.main(["comparar", "--resumo", str(tmp_path / "nao.json"), "--base", str(base)]) == 2


def test_base_vazia_recusa(tmp_path):
    import subprocess, sys, json as _j
    novo = tmp_path / "novo.json"
    novo.write_text(_j.dumps({"m": {"feitas": 1, "ok": 1, "medido": []}}), encoding="utf-8")
    base = tmp_path / "base"; base.mkdir()
    r = subprocess.run([sys.executable, str(Path(__file__).with_name("porta_entrada.py")), "comparar",
                        "--resumo", str(novo), "--base", str(base)], capture_output=True, text=True)
    assert r.returncode == 2 and "base sem resumo" in r.stderr


def _com_respostas(tmp_path, modelo, linhas, resumo=None):
    d = tmp_path / modelo.replace("/", "_")
    _grava(d, "resumo.json", resumo or _resumo(modelo, 0.0, 3.0))
    (d / "respostas.jsonl").write_text("\n".join(json.dumps(l) for l in linhas), encoding="utf-8")
    return pe.carregar(d / "resumo.json", True)[modelo]


def test_polaridade_das_checagens(tmp_path):
    l = [_resp("m/p", "conversa", True, 1.0, deu_porcentagem=True),   # negativa: True = falha
         _resp("m/p", "conversa", True, 1.0, deu_porcentagem=False),
         _resp("m/p", "json", True, 1.0, json_valido=False),           # positiva: False = falha
         _resp("m/p", "json", True, 1.0, json_valido=True),
         _resp("m/p", "ferramenta", True, 1.0, escreveu_sem_portao=True, chamou_ferramenta=False)]
    f = _com_respostas(tmp_path, "m/p", l)
    assert f["notas"] == {"conversa": 0.5, "json": 0.5, "ferramenta": 1.0}


def test_checagem_desconhecida_ignorada_com_aviso(tmp_path):
    f = _com_respostas(tmp_path, "m/q", [_resp("m/q", "codigo", True, 1.0, coisa_nova=False)])
    assert f["notas"] == {"codigo": 1.0}
    assert any("coisa_nova" in a for a in f["avisos"])


def test_resposta_vazia_e_think_nao_contam_mas_ferramenta_sim(tmp_path):
    vazia = _resp("m/v", "conversa", True, 1.0, texto="<think>pensando</think>  ")
    aberta = _resp("m/v", "conversa", True, 1.0, texto="<think>nunca fecha")
    boa = _resp("m/v", "conversa", True, 1.0, texto="<think>x</think>Olá")
    chamada = dict(_resp("m/v", "ferramenta", True, 1.0, texto=""), chamadas=[{"nome": "vault_buscar"}])
    f = _com_respostas(tmp_path, "m/v", [vazia, aberta, boa, chamada])
    assert f["notas"] == {"conversa": pytest.approx(1 / 3), "ferramenta": 1.0}
    assert any("vazado" in a for a in f["avisos"])  # </think> no texto de vazia e de boa


def test_python_que_nao_compila_desconta_sem_executar(tmp_path):
    ruim = _resp("m/c", "codigo", True, 1.0, texto="```python\nimport os; os.system('echo nao')\ndef f(:\n```")
    bom = _resp("m/c", "codigo", True, 1.0, texto="```python\nx = 1\n```")
    f = _com_respostas(tmp_path, "m/c", [ruim, bom])
    assert f["notas"] == {"codigo": 0.5}


def test_numeros_invalidos_recusam_com_saida_2(tmp_path, capsys):
    base = tmp_path / "base"
    _grava(base, "resumo-a.json", _resumo("x/a", 0.0, 2.0))
    casos = [_resumo("x/n", 1.5, 2.0), _resumo("x/n", float("nan"), 2.0), _resumo("x/n", 0.0, -1.0),
             _resumo("x/n", 0.0, float("inf")), _resumo("x/n", 0.0, 2.0, json_=2.0), _resumo("x/n", "0.1", 2.0)]
    for i, dados in enumerate(casos):
        novo = tmp_path / f"n{i}" / "resumo.json"
        novo.parent.mkdir()
        novo.write_text(json.dumps(dados), encoding="utf-8")  # json.dumps escreve NaN/Infinity, que o loads aceita
        assert pe.main(["comparar", "--resumo", str(novo), "--base", str(base)]) == 2, i
        assert "recusado" in capsys.readouterr().err
    # respostas com latência inválida
    d = tmp_path / "r"
    _grava(d, "resumo.json", _resumo("x/r", 0.0, 2.0))
    (d / "respostas.jsonl").write_text(json.dumps(_resp("x/r", "codigo", True, -3.0)), encoding="utf-8")
    assert pe.main(["comparar", "--resumo", str(d / "resumo.json"), "--base", str(base)]) == 2
    lixo = tmp_path / "lixo.json"
    lixo.write_text("[1,2]", encoding="utf-8")
    assert pe.main(["comparar", "--resumo", str(lixo), "--base", str(base)]) == 2


def test_util_exige_rival_e_ganho_estrito(tmp_path):
    base = tmp_path / "base"
    _grava(base, "resumo-a.json", _resumo("x/a", 0.0, 2.0, 1.0, 1.0))
    # empate exato em nota e p50: ninguém ganha
    f = pe.comparar(_grava(tmp_path / "n", "resumo.json", _resumo("x/n", 0.0, 2.0, 1.0, 1.0)), base)
    assert f["x/n"]["veredito"] == "neutro" and f["x/a"]["veredito"] == "neutro"
    # sem tipo em comum: sem rival comparável
    base2 = tmp_path / "base2"
    _grava(base2, "resumo-a.json", _resumo("x/a", 0.0, 2.0))  # só "geral"
    d = tmp_path / "so_json"
    d.mkdir()
    (d / "resumo.json").write_text(json.dumps({"x/n": {"medido": [
        {"metrica": "taxa_erro", "valor": 0.0}, {"metrica": "latencia_p50_s", "valor": 1.0}]}}), encoding="utf-8")
    (d / "respostas.jsonl").write_text(json.dumps(_resp("x/n", "codigo", True, 1.0)), encoding="utf-8")
    f = pe.comparar(d / "resumo.json", base2)
    assert f["x/n"]["veredito"] == "neutro" and "sem rival comparável" in f["x/n"]["motivo"]


def test_base_vazia_ou_so_com_o_proprio_modelo_recusa(tmp_path, capsys):
    base = tmp_path / "base"
    base.mkdir()
    novo = _grava(tmp_path / "n", "resumo.json", _resumo("x/n", 0.0, 2.0))
    assert pe.main(["comparar", "--resumo", str(novo), "--base", str(base)]) == 2
    _grava(base, "resumo-eco.json", _resumo("x/n", 0.1, 3.0))  # base só com o mesmo modelo
    assert pe.main(["comparar", "--resumo", str(novo), "--base", str(base)]) == 2
    assert "nada para comparar" in capsys.readouterr().err


def test_python_truncado_sem_cerca_de_fechamento_e_analisado(tmp_path):
    truncado = _resp("m/t", "codigo", True, 1.0, texto="```python\ndef f(:\n    return")
    bom = _resp("m/t", "codigo", True, 1.0, texto="```python\nx = 1")  # truncado, mas compila
    f = _com_respostas(tmp_path, "m/t", [truncado, bom])
    assert f["notas"] == {"codigo": 0.5}


def test_resumo_novo_ou_base_vazios_e_none_recusam(tmp_path, capsys):
    base = tmp_path / "base"
    _grava(base, "resumo-a.json", _resumo("x/a", 0.0, 2.0))
    vazio = _grava(tmp_path / "v", "resumo.json", {})
    assert pe.main(["comparar", "--resumo", str(vazio), "--base", str(base)]) == 2
    assert "sem nenhum modelo" in capsys.readouterr().err
    base2 = tmp_path / "base2"
    _grava(base2, "resumo-vazio.json", {})
    novo = _grava(tmp_path / "n", "resumo.json", _resumo("x/n", 0.0, 2.0))
    assert pe.main(["comparar", "--resumo", str(novo), "--base", str(base2)]) == 2
    nulo = _grava(tmp_path / "z", "resumo.json", {"x/z": {"medido": [{"metrica": "taxa_erro", "valor": None}]}})
    assert pe.main(["comparar", "--resumo", str(nulo), "--base", str(base)]) == 2
    assert "inválido" in capsys.readouterr().err
