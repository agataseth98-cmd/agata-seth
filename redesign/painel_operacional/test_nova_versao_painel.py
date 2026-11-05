import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class NovaVersaoPainelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = self.tmp.name + "/dados"
        os.environ["AGATA_NV_CACHE"] = self.tmp.name + "/cache"
        os.environ["AGATA_CONEXOES_DIR"] = self.tmp.name + "/cofre"
        import nova_versao_painel
        self.m = nova_versao_painel

    def tearDown(self):
        self.tmp.cleanup()

    def test_recusa_acao_e_consulta_fora_do_contrato(self):
        with self.assertRaises(ValueError):
            self.m.executar("rm -rf", {})
        with self.assertRaises(ValueError):
            self.m.executar("consultar", {"consulta": "x" * 301})
        with self.assertRaises(ValueError):
            self.m.executar("skills", {"consulta": "   "})

    def test_orcamento_recusa_fora_do_limite_e_registra_mudanca(self):
        with self.assertRaises(ValueError):
            self.m.executar("salvar_orcamento", {"orcamento": {"max_chamadas": -1}})
        with self.assertRaises(ValueError):
            self.m.executar("salvar_orcamento", {"orcamento": {"provedores": {"outro": True}}})
        r = self.m.executar("salvar_orcamento", {"orcamento": {"provedores": {"local": True, "gratuito": True},
                                                               "max_chamadas": 50}})
        self.assertTrue(r["resultado"]["mudou"])
        ledger = Path(os.environ["AGATA_NV_DIR"]) / "eventos" / "ledger.jsonl"
        ev = [json.loads(x) for x in ledger.read_text().splitlines()]
        self.assertEqual(ev[-1]["source"], "orcamento")
        self.assertEqual(ev[-1]["antes"]["provedores"]["gratuito"], False)
        self.assertEqual(ev[-1]["depois"]["provedores"]["gratuito"], True)

    def test_estado_sem_dados_diz_nao_medido(self):
        e = self.m.estado()
        self.assertEqual(e["corpo"]["saude"]["estado"], "não medido")
        self.assertIsNone(e["alexandria"]["indice"])
        self.assertEqual(e["orcamento"]["provedores"], {"local": True, "gratuito": False, "assinatura": False, "pago": False})

    def test_chave_gravada_nao_volta_na_resposta_nem_no_estado(self):
        chave = "sk-ant-" + "q" * 48
        r = self.m.executar("gravar_chave", {"provedor": "claude", "chave": chave})
        bruto = json.dumps([r, self.m.estado()], ensure_ascii=False)
        self.assertNotIn("q" * 48, bruto)
        self.assertIn('"no_cofre": true', bruto)
        with self.assertRaises(ValueError):
            self.m.executar("gravar_chave", {"provedor": "claude", "chave": "curta"})
        with self.assertRaises(ValueError):
            self.m.executar("testar_rotas", {"categorias": ["tudo"]})
        html = (HERE / "prototipo.html").read_text(encoding="utf-8")
        self.assertIn('id="nv-api-chave" type="password" autocomplete="new-password"', html)

    def test_js_externo_e_sem_innerhtml(self):
        html = (HERE / "prototipo.html").read_text(encoding="utf-8")
        self.assertIn('<script src="nova_versao.js"></script>', html)
        js = (HERE / "nova_versao.js").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", js)

    def test_paginas_sem_estilo_inline_porque_a_csp_bloqueia(self):
        # style-src 'self': atributo style é ignorado pelo navegador; foi a causa da tela crua dos lotes 1 e 2
        import re
        html = (HERE / "prototipo.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="stylesheet" href="nova_versao.css">', html)
        for sec in re.findall(r'<section class="page nv-page".*?</section>', html, re.S):
            self.assertNotIn("style=", sec)
        self.assertEqual(len(re.findall(r'<section class="page nv-page"', html)), 8)
        js = (HERE / "nova_versao.js").read_text(encoding="utf-8")
        self.assertNotIn(".style.", js)
        self.assertNotIn('"style"', js)
        import server
        self.assertIn("/nova_versao.css", server._ASSETS)
        self.assertIn("style-src 'self'", (HERE / "server.py").read_text(encoding="utf-8"))

    def test_avaliacao_pelo_painel_respeita_os_portoes(self):
        import json as _j
        with self.assertRaises(ValueError):
            self.m.executar("salvar_politica", {"margem_minima": 5, "teto_latencia_ms": 1000, "teto_reais": 0})
        with self.assertRaises(ValueError):
            self.m.executar("ver_execucao", {"run_id": "../../etc/passwd"})
        with self.assertRaises(ValueError):
            self.m.executar("avaliar", {"split": "dev", "rotas": "tudo"})
        # reservado sem conjunto/revisão: recusa volta na hora, sem abrir rodada
        base = Path(os.environ["AGATA_NV_DIR"]) / "avaliacao" / "teste-reservado"
        base.mkdir(parents=True)
        t = {"task_id": "ope-teste", "grupo": "operacao", "split": "teste", "pedido": "p", "autor": "teste", "criterios": [{"tipo": "abstem"}]}
        (base / "conjunto.jsonl").write_text(_j.dumps(t) + "\n", encoding="utf-8")
        r = self.m.executar("avaliar", {"split": "teste", "rotas": ["x"], "condicoes": ["alexandria"], "repeticoes": 1})
        self.assertIn("revisão", r["resultado"]["recusado"])
        e = self.m.estado()["avaliacao"]
        self.assertEqual(e["reservado"]["tarefas"], 1)
        self.assertIsNone(e["reservado"]["revisado_por"])
        self.assertNotIn("criterios", _j.dumps(e))   # o estado nunca traz o gabarito
        self.m.executar("revisar_reservado", {})
        self.assertTrue(self.m.estado()["avaliacao"]["reservado"]["revisado_por"])


if __name__ == "__main__":
    unittest.main()
