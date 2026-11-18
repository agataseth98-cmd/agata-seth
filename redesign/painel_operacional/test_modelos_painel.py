"""Testes do catálogo de modelos no painel (18/11/2026): leitura, decisão registrada, recusas, página e CSP.

O catálogo e o arquivo de decisões vão para um diretório temporário (variáveis AGATA_CATALOGO_MODELOS e
AGATA_DECISOES_MODELOS). Os de rota sobem o servidor numa porta livre (127.0.0.1). Nenhum teste toca rotas,
OmniRoute, ~/.config/agata ou o catálogo real.
"""
import http.client
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys_path = str(HERE)
import sys  # noqa: E402
sys.path.insert(0, sys_path)
import modelos_painel as mp  # noqa: E402

_spec = importlib.util.spec_from_file_location("painel_modelos_teste", HERE / "server.py")
panel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(panel)

HTML = (HERE / "prototipo.html").read_text(encoding="utf-8")
CSS = (HERE / "prototipo.css").read_text(encoding="utf-8")
JS = (HERE / "modelos.js").read_text(encoding="utf-8")
BLOCO_HTML = HTML[HTML.index('<div class="sub" id="sub-catalogo-modelos"'): HTML.index('<div class="sub nv-page" id="sub-nv-corpo"')]

CATALOGO = [
    {"provedor": "nvidia", "id": "nvidia/a/cand", "nome": "cand", "capacidades": ["chat", "visao"], "contexto": "x",
     "acesso_verificado": {"status": 200, "data": "2026-11-18 15:04", "latencia_s": 0.9}, "estado": "candidato_prova",
     "fonte": "teste", "veredito": {"resultado": "aprovado em 3 de 3", "data": "2026-11-18", "fonte": "prova-x"}},
    {"provedor": "nvidia", "id": "nvidia/a/sb", "nome": "sb", "capacidades": ["codigo"], "contexto": "x",
     "acesso_verificado": "não verificado", "estado": "standby", "fonte": "teste"},
    {"provedor": "outro", "id": "outro/b/proibido", "nome": "proibido", "capacidades": ["stt"], "contexto": "x",
     "acesso_verificado": "não verificado", "estado": "proibido_pela_regra", "fonte": "teste"},
    {"provedor": "outro", "id": "outro/b/fora", "nome": "fora", "capacidades": ["chat"], "contexto": "x",
     "acesso_verificado": {"status": 404, "latencia_s": 0.4, "erro": "404"}, "estado": "indisponivel", "fonte": "teste"},
]


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.cat = self.dir / "catalogo.json"
        self.dec = self.dir / "decisoes.jsonl"
        self.cat.write_text(json.dumps(CATALOGO), encoding="utf-8")
        antigo = {k: os.environ.get(k) for k in ("AGATA_CATALOGO_MODELOS", "AGATA_DECISOES_MODELOS")}
        os.environ["AGATA_CATALOGO_MODELOS"] = str(self.cat)
        os.environ["AGATA_DECISOES_MODELOS"] = str(self.dec)
        self.addCleanup(lambda: [os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v) for k, v in antigo.items()])

    def decidir(self, ident, acao, **extra):
        pedido = {"id": ident, "acao": acao, "confirmacao": ident, "quem": "Teste"}
        pedido.update(extra)
        return mp.decidir(pedido)

    def linhas(self):
        return [json.loads(x) for x in self.dec.read_text(encoding="utf-8").splitlines()] if self.dec.exists() else []


class ModuloTests(Base):
    def test_lista_com_contagens_filtros_e_veredito(self):
        d = mp.listar()
        self.assertEqual(d["estado"], "ok")
        self.assertEqual(d["contagens"], {"liberado": 0, "candidato_prova": 1, "standby": 1, "indisponivel": 1, "proibido_pela_regra": 1})
        self.assertEqual(d["capacidades"], ["chat", "codigo", "stt", "visao"])
        self.assertEqual(d["provedores"], ["nvidia", "outro"])
        cand = next(m for m in d["modelos"] if m["id"] == "nvidia/a/cand")
        self.assertEqual(cand["veredito"]["resultado"], "aprovado em 3 de 3")
        self.assertIsNone(next(m for m in d["modelos"] if m["id"] == "nvidia/a/sb")["veredito"])

    def test_sem_catalogo_e_estado_proprio(self):
        self.cat.unlink()
        self.assertEqual(mp.listar()["estado"], "sem_catalogo")

    def test_catalogo_ilegivel_nao_e_inventado(self):
        self.cat.write_text("{nao e json", encoding="utf-8")
        with self.assertRaises(mp.ErroModelos) as c:
            mp.listar()
        self.assertEqual(c.exception.status, 500)

    def test_liberar_grava_linha_com_quem_e_quando_e_muda_o_estado(self):
        r = self.decidir("nvidia/a/cand", "liberar")
        linha = self.linhas()[0]
        self.assertEqual((linha["id"], linha["acao"], linha["de"], linha["para"]), ("nvidia/a/cand", "liberar", "candidato_prova", "liberado"))
        self.assertEqual(linha["quem"], "Teste (painel)")
        self.assertRegex(linha["quando"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d")
        self.assertIn("nenhuma rota foi alterada", r["aviso"])
        m = next(m for m in mp.listar()["modelos"] if m["id"] == "nvidia/a/cand")
        self.assertEqual((m["estado"], m["pode_liberar"], m["pode_standby"]), ("liberado", False, True))

    def test_voltar_ao_standby_depois_de_liberar_e_append_only(self):
        self.decidir("nvidia/a/sb", "liberar")
        primeira = self.dec.read_text(encoding="utf-8")
        self.decidir("nvidia/a/sb", "standby")
        self.assertTrue(self.dec.read_text(encoding="utf-8").startswith(primeira), "a linha antiga continua intacta")
        self.assertEqual(len(self.linhas()), 2)
        self.assertEqual(next(m for m in mp.listar()["modelos"] if m["id"] == "nvidia/a/sb")["estado"], "standby")

    def test_proibido_pela_regra_nao_pode_ser_liberado(self):
        for acao in ("liberar", "standby"):
            with self.assertRaises(mp.ErroModelos) as c:
                self.decidir("outro/b/proibido", acao)
            self.assertEqual(c.exception.status, 409)
        self.assertEqual(self.linhas(), [])

    def test_indisponivel_nao_pode_ser_liberado(self):
        with self.assertRaises(mp.ErroModelos) as c:
            self.decidir("outro/b/fora", "liberar")
        self.assertEqual(c.exception.status, 409)

    def test_decisao_antiga_nao_libera_o_que_virou_proibido(self):
        self.dec.write_text(json.dumps({"id": "outro/b/proibido", "acao": "liberar", "quando": "x", "quem": "x"}) + "\n", encoding="utf-8")
        m = next(m for m in mp.listar()["modelos"] if m["id"] == "outro/b/proibido")
        self.assertEqual(m["estado"], "proibido_pela_regra")

    def test_exige_confirmacao_explicita_e_id_do_catalogo(self):
        for pedido, status in (({"id": "nvidia/a/cand", "acao": "liberar"}, 400),
                               ({"id": "nvidia/a/cand", "acao": "liberar", "confirmacao": "outro"}, 400),
                               ({"id": "nvidia/a/cand", "acao": "apagar", "confirmacao": "nvidia/a/cand"}, 400),
                               ({"id": "nao/existe", "acao": "liberar", "confirmacao": "nao/existe"}, 404)):
            with self.assertRaises(mp.ErroModelos) as c:
                mp.decidir(pedido)
            self.assertEqual(c.exception.status, status, pedido)
        self.assertEqual(self.linhas(), [])

    def test_quem_e_sanitizado_e_decisao_nao_altera_o_catalogo(self):
        antes = self.cat.read_bytes()
        self.decidir("nvidia/a/cand", "liberar", quem='Ana <script>"\n')
        self.assertNotIn("<", self.linhas()[0]["quem"])
        self.assertEqual(self.cat.read_bytes(), antes)


class ConcorrenciaETiposTests(Base):
    def test_duas_threads_liberando_o_mesmo_modelo_gravam_uma_linha(self):
        resultados = []
        barreira = threading.Barrier(2)

        def tenta():
            barreira.wait()
            try:
                self.decidir("nvidia/a/cand", "liberar")
                resultados.append(200)
            except mp.ErroModelos as e:
                resultados.append(e.status)
        ts = [threading.Thread(target=tenta) for _ in range(2)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(sorted(resultados), [200, 409])
        self.assertEqual(len(self.linhas()), 1)

    def test_tipos_invalidos_viram_400(self):
        base = {"id": "nvidia/a/cand", "acao": "liberar", "confirmacao": "nvidia/a/cand"}
        for campo, valor in (("acao", []), ("acao", {}), ("id", []), ("id", {}), ("confirmacao", []), ("quem", []),
                             ("quem", {}), ("nota", []), ("nota", 5)):
            with self.subTest(campo=campo, valor=valor):
                pedido = dict(base)
                pedido[campo] = valor
                with self.assertRaises(mp.ErroModelos) as c:
                    mp.decidir(pedido)
                self.assertEqual(c.exception.status, 400)
        self.assertEqual(self.linhas(), [])


class RotasTests(Base):
    @classmethod
    def setUpClass(cls):
        cls.porta_antiga = panel.PORT
        cls.servidor = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.servidor.daemon_threads = True
        panel.PORT = cls.servidor.server_address[1]
        cls.thread = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.thread.join(timeout=3)
        panel.PORT = cls.porta_antiga

    def pede(self, caminho, metodo="GET", corpo=None, cab=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=10)
        try:
            h = dict(cab or {})
            if corpo is not None:
                h.setdefault("Content-Type", "application/json")
            conn.request(metodo, caminho, body=corpo, headers=h)
            r = conn.getresponse()
            return r.status, r.read()
        finally:
            conn.close()

    def post(self, pedido, cab=None):
        h = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin"}
        h.update(cab or {})
        return self.pede("/api/modelos/decisao", "POST", json.dumps(pedido).encode("utf-8"), h)

    def test_get_api_modelos(self):
        status, corpo = self.pede("/api/modelos")
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(corpo)["modelos"]), 4)

    def test_get_da_pagina_traz_o_subpainel_e_o_script_externo(self):
        status, corpo = self.pede("/prototipo")
        html = corpo.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn('id="sub-catalogo-modelos"', html)
        self.assertIn('<script src="modelos.js" defer></script>', html)
        status, js = self.pede("/modelos.js")
        self.assertEqual(status, 200)
        self.assertIn(b"carregarModelos", js)

    def test_post_libera_e_grava(self):
        status, corpo = self.post({"id": "nvidia/a/cand", "acao": "liberar", "confirmacao": "nvidia/a/cand", "quem": "Teste"})
        self.assertEqual(status, 200, corpo)
        self.assertEqual(self.linhas()[0]["para"], "liberado")

    def test_post_recusa_liberar_proibido(self):
        status, _ = self.post({"id": "outro/b/proibido", "acao": "liberar", "confirmacao": "outro/b/proibido"})
        self.assertEqual(status, 409)
        self.assertEqual(self.linhas(), [])

    def test_post_sem_confirmacao_400_e_origem_alheia_403(self):
        self.assertEqual(self.post({"id": "nvidia/a/cand", "acao": "liberar"})[0], 400)
        self.assertEqual(self.post({"id": "nvidia/a/cand", "acao": "liberar", "confirmacao": "nvidia/a/cand"},
                                   {"Origin": "http://evil.example", "Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.pede("/api/modelos/decisao", "POST", b"{}")[0], 403)
        self.assertEqual(self.linhas(), [])

    def test_post_tipos_invalidos_respondem_400_controlado(self):
        for acao in ([], {}):
            status, _ = self.post({"id": "nvidia/a/cand", "acao": acao, "confirmacao": "nvidia/a/cand"})
            self.assertEqual(status, 400)
        self.assertEqual(self.post([1])[0], 400)
        self.assertEqual(self.linhas(), [])

    def test_post_corpo_grande_e_json_invalido(self):
        h = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin"}
        self.assertEqual(self.pede("/api/modelos/decisao", "POST", b"x" * 3000, h)[0], 413)
        self.assertEqual(self.pede("/api/modelos/decisao", "POST", b"{nao", h)[0], 400)


class PaginaTests(unittest.TestCase):
    def test_sem_inline_nem_html_dinamico(self):
        self.assertNotRegex(BLOCO_HTML, r"\sstyle=|\son\w+=|<script|<style")
        self.assertNotRegex(JS, r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|\.style\b")
        self.assertNotIn("target=", BLOCO_HTML)
        self.assertNotRegex(BLOCO_HTML, r'href="https?:')

    def test_link_de_cadastro_leva_a_conexoes_e_chave_nao_e_ecoada(self):
        self.assertIn('data-open-page="sistema" data-open-sub="nv-conexoes"', BLOCO_HTML)
        self.assertNotRegex(BLOCO_HTML, r'type="(password|text)"[^>]*(chave|key)')
        self.assertNotRegex(JS, r"(?i)api[_-]?key|chave")

    def test_menu_e_loader_registram_o_subpainel(self):
        js = (HERE / "prototipo.js").read_text(encoding="utf-8")
        self.assertIn('data-sub="catalogo-modelos"', HTML)
        self.assertIn('"catalogo-modelos": () =>', js)

    def test_responsivo_e_tabela_em_moldura(self):
        self.assertIn("repeat(auto-fit,minmax(200px,1fr))", CSS)
        self.assertRegex(BLOCO_HTML, r'<div class="nv-tabela-wrap"><table class="nv-tabela" id="mod-tabela">')

    def test_filtro_roda_no_node(self):
        script = (
            "global.window={};global.document={getElementById:()=>null};"
            f"eval(require('fs').readFileSync({json.dumps(str(HERE / 'modelos.js'))},'utf8'));"
            "const f=window.AgataPainel.modelosFiltrar;"
            "const m=JSON.parse(process.argv[1]);"
            "console.log(JSON.stringify([f(m,'chat','','').length,f(m,'','outro','').length,f(m,'','','standby').length,f(m,'','','').length]));"
        )
        modelos = [{"capacidades": x["capacidades"], "provedor": x["provedor"], "estado": x["estado"]} for x in CATALOGO]
        saida = subprocess.run(["node", "-e", script, json.dumps(modelos)], capture_output=True, text=True, timeout=30)
        self.assertEqual(saida.returncode, 0, saida.stderr)
        self.assertEqual(json.loads(saida.stdout), [2, 2, 1, 4])


# Os testes de rota usam as mesmas ferramentas de linha de Base.
RotasTests.linhas = Base.linhas

if __name__ == "__main__":
    unittest.main()
