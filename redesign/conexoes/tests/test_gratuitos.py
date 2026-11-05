"""Gratuitos por passagem (config/gratuitos_omniroute.json) e cota esgotada como estado próprio (lote 7)."""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
import testar_rotas  # noqa: E402


def test_lista_versionada_tem_so_ativos_e_crouton_fora():
    ids = testar_rotas.gratuitos_configurados()
    assert "zai/glm-4.7-flash" in ids
    assert "openrouter/stealth/crouton-alpha" in ids  # origem anônima: liberado só com dados redigidos e plano de contingência
    assert all(i.startswith(("openrouter/", "zai/")) for i in ids)


def test_cota_esgotada_vira_estado_proprio(monkeypatch):
    import orcamento
    monkeypatch.setattr(orcamento, "permite", lambda *a, **k: (True, ""))

    def post_429(url, body, timeout):
        raise RuntimeError("HTTP Error 429: Too Many Requests")

    def post_rede(url, body, timeout):
        raise RuntimeError("connection reset by peer")

    r = {"tipo": "omniroute", "categoria": "gratuito", "modelo": "x", "rota": "x"}
    assert testar_rotas.chamar_rota(r, "oi", 5, post=post_429)["falha_etapa"] == "cota_esgotada"
    assert testar_rotas.chamar_rota(r, "oi", 5, post=post_rede)["falha_etapa"] == "transporte"


def test_rotas_gratuitas_entram_quando_categoria_ligada(monkeypatch):
    import orcamento
    monkeypatch.setattr(orcamento, "ler", lambda: {"provedores": {"local": False, "gratuito": True,
                                                                  "assinatura": False, "pago": False}})

    def get(url):
        return {"models": [{"fullModel": "groq/llama-x", "available": True}]}

    rs = testar_rotas.rotas({"gratuito"}, get=get)
    nomes = {r["rota"] for r in rs}
    assert "groq/llama-x" in nomes and "zai/glm-4.7-flash" in nomes
