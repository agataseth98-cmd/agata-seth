"""AC-01 e AC-02: schema das fontes (canônico e overlay)."""
from __future__ import annotations

import pytest
import yaml
from ferr_helpers import REPO, entrada_teste, escrever_overlay, montar_ctx  # noqa: F401

import schema as S


def test_schema_canon_valido():
    canon, indice = S.carregar_canonico(REPO)
    assert set(canon["mcp"]) == {"github-pat", "agata-navegador"}
    assert "agata-arranque" in canon["skills"]
    assert len(canon["agentes"]) == 10
    assert indice == ".agents/skills/INDICE.md"
    for tipo in ("mcp", "skills", "agentes"):
        for nome, e in canon[tipo].items():
            assert e["clis"], nome
            assert set(e["clis"]) <= set(S.CLIS), nome
            if not e["gerenciado"]:
                assert e["motivo"].strip(), nome
    # nenhum valor de segredo na fonte: env, se houver, são só nomes de variável
    for e in canon["mcp"].values():
        assert all(S.RE_VARIAVEL.fullmatch(v) for v in e["env"])


def test_schema_overlay_rejeita_campo_extra(tmp_path):
    overlay = tmp_path / "ferramentas.yml"
    overlay.write_text(yaml.safe_dump({"mcp": [entrada_teste(campo_inventado="x")]}), encoding="utf-8")
    with pytest.raises(S.ErroSchema) as erro:
        S.carregar_overlay(overlay)
    assert "campo_inventado" in str(erro.value)

    # chave de topo fora do schema também é recusada
    overlay.write_text(yaml.safe_dump({"hooks": []}), encoding="utf-8")
    with pytest.raises(S.ErroSchema):
        S.carregar_overlay(overlay)

    # valor de segredo no lugar de nome de variável: recusado, e o valor não aparece na mensagem
    segredo = "segredo-de-teste-000111"
    overlay.write_text(yaml.safe_dump({"mcp": [entrada_teste(env=[f"CHAVE={segredo}"])]}), encoding="utf-8")
    with pytest.raises(S.ErroSchema) as erro:
        S.carregar_overlay(overlay)
    assert segredo not in str(erro.value)


def test_schema_overlay_aceita_entrada_valida(tmp_path):
    ctx = montar_ctx(tmp_path, "ov")
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    ov = S.carregar_overlay(ctx.overlay)
    assert list(ov["mcp"]) == ["agata-teste"]
    assert ov["mcp"]["agata-teste"]["env"] == ["AGATA_TESTE_VAR"]
