import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI.parents[1] / "nova_versao"))
import adaptadores  # noqa: E402
import orcamento  # noqa: E402
import segredos  # noqa: E402
import testar_rotas  # noqa: E402

CHAVE = "sk-ant-" + "x" * 40
TARIFA = {"entrada_usd_mtok": 1.0, "saida_usd_mtok": 5.0, "cambio_brl": 5.5, "fonte": "https://exemplo/precos", "data": "2026-11-04"}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        os.environ["AGATA_NV_DIR"] = str(t / "dados")
        os.environ["AGATA_NV_CACHE"] = str(t / "cache")
        os.environ["AGATA_CONEXOES_DIR"] = str(t / "cofre")
        for v in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            os.environ.pop(v, None)
        self.privado = mock.patch.object(adaptadores, "_privado", lambda t: "@" in t)
        self.privado.start()

    def tearDown(self):
        self.privado.stop()
        self.tmp.cleanup()

    def ledger(self) -> str:
        p = Path(os.environ["AGATA_NV_DIR"]) / "eventos" / "ledger.jsonl"
        return p.read_text(encoding="utf-8") if p.exists() else ""


class CofreTests(Base):
    def test_chave_vai_para_o_cofre_0600_e_nunca_volta(self):
        e = segredos.gravar("claude", CHAVE, "sk-ant-")
        p = Path(os.environ["AGATA_CONEXOES_DIR"]) / "claude.chave"
        self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(p.parent.stat().st_mode), 0o700)
        self.assertTrue(e["no_cofre"])
        bruto = json.dumps([e, adaptadores.estado()], ensure_ascii=False) + self.ledger()
        self.assertNotIn(CHAVE, bruto)
        self.assertNotIn("x" * 40, bruto)
        with self.assertRaises(ValueError):
            segredos.gravar("claude", "sk-errado-" + "y" * 30, "sk-ant-")
        with self.assertRaises(ValueError):
            segredos.gravar("../fora", CHAVE)
        self.assertTrue(segredos.remover("claude")["removida"])
        self.assertFalse(p.exists())


class ChamadaTests(Base):
    def test_portas_orcamento_privacidade_e_custo_antes_de_sair(self):
        r = adaptadores.chamar("claude", "api", "oi")
        self.assertEqual(r["falha_etapa"], "orcamento")              # pago desligado por padrão
        o = orcamento.ler(); o["provedores"]["pago"] = True; o["teto_reais"] = 1.0; orcamento.salvar(o)
        segredos.gravar("claude", CHAVE, "sk-ant-")
        self.assertEqual(adaptadores.chamar("claude", "api", "oi")["falha_etapa"], "custo")   # sem tarifa datada
        adaptadores.ajustar("claude", tarifa=TARIFA)
        self.assertEqual(adaptadores.chamar("claude", "api", "meu e-mail a@b.c")["falha_etapa"], "privacidade")
        visto = {}

        def post(url, cab, corpo, timeout):
            visto.update(url=url, cab=cab, corpo=corpo)
            return {"model": "claude-haiku-5-5", "content": [{"type": "text", "text": "pronto"}],
                    "usage": {"input_tokens": 10, "output_tokens": 2}}
        r = adaptadores.chamar("claude", "api", "oi", post=post)
        self.assertTrue(r["ok"]); self.assertEqual(r["texto"], "pronto")
        self.assertEqual(visto["cab"]["x-api-key"], CHAVE)
        self.assertGreater(r["reais_estimado"], 0)
        self.assertEqual(adaptadores.chamar("claude", "navegador", "oi")["falha_etapa"], "autorizacao")
        o["teto_reais"] = 0.0000001; orcamento.salvar(o)
        self.assertEqual(adaptadores.chamar("claude", "api", "oi", post=post)["falha_etapa"], "custo")

    def test_cli_roda_em_pasta_vazia_sem_ferramentas(self):
        o = orcamento.ler(); o["provedores"]["assinatura"] = True; orcamento.salvar(o)
        visto = {}

        class R:
            returncode = 0
            stdout = json.dumps({"result": "pronto", "usage": {"input_tokens": 5, "output_tokens": 1}})
            stderr = ""

        def rodar(argv, cwd, **k):
            visto.update(argv=argv, cwd=cwd, vazio=not os.listdir(cwd))
            return R()
        r = adaptadores.chamar("claude", "cli", "oi", rodar=rodar)
        self.assertTrue(r["ok"])
        self.assertEqual(visto["argv"][visto["argv"].index("--tools") + 1], "")
        self.assertIn("--no-session-persistence", visto["argv"])
        self.assertEqual(visto["argv"][-1], "oi")
        self.assertTrue(visto["vazio"])

    def test_provedor_novo_so_api_https(self):
        with self.assertRaises(ValueError):
            adaptadores.adicionar_local("x1", "X", "openai", "http://inseguro/v1", None, "m")
        with self.assertRaises(ValueError):
            adaptadores.adicionar_local("claude", "dup", "openai", "https://a.b/v1", None, "m")
        p = adaptadores.adicionar_local("mistral", "Mistral", "openai", "https://api.mistral.ai/v1/chat/completions",
                                        "MISTRAL_API_KEY", "mistral-small-latest")
        self.assertEqual(p["origem"], "local")
        self.assertNotIn("cli", p)
        self.assertIn("mistral", [x["id"] for x in adaptadores.estado()])


class RedundanciaTests(Base):
    def test_testa_por_capacidade_sem_guardar_resposta_e_com_independencia(self):
        def get(url):
            if url.endswith("/api/tags"):
                return {"models": [{"name": "qwen3:4b"}, {"name": "nomic-embed-text"}]}
            return {"models": []}

        def post(url, corpo, timeout):
            pedido = corpo["messages"][0]["content"]
            texto = "pronto" if pedido.startswith("Responda apenas") else '{"ok": true}' if pedido.startswith("Responda somente") else "x"
            return {"message": {"content": texto}, "prompt_eval_count": 3, "eval_count": 1}
        run = testar_rotas.testar({"local"}, get=get, post=post)
        self.assertEqual(run["rotas_que_passaram"]["conversa"], ["ollama-local/qwen3:4b"])
        self.assertEqual(run["rotas_que_passaram"]["codigo"], [])
        self.assertTrue(all("texto" not in r for r in run["resultados"]))
        self.assertEqual(run["resultados"][0]["independencia"]["rede"], "nenhuma")
        self.assertEqual(len(run["resultados"]), 3)   # embedding fica fora


if __name__ == "__main__":
    unittest.main()
