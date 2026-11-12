#!/usr/bin/env python3
"""Testes dos Importantes do painel (11/11/2026): armazém (importantes.py) e rotas (server.py).

Cobre: criar, marcar feito/descartado/aberto, editar; nada some (descartado fica); ordem da lista; arquivo ilegível
não é sobrescrito; escrita atômica; registro só com hora, rota, id e status; trazer do cache do Conselho marca só
entradas IMPORTANTE, não duplica (nem o descartado), recusa segredo, filtra dado pessoal e não escreve no cache;
rotas recusam origem alheia (403) e corpo acima de 4096 bytes (413).

Nada toca em ~/.cache/agata: o arquivo e o registro vão para um diretório temporário, e o cache do Conselho
é trocado por um arquivo temporário. Os de rota sobem o servidor numa porta livre (127.0.0.1).
"""
import http.client
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import importantes

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("painel_importantes", HERE / "server.py")
panel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(panel)


def id_de(n):
    return f"{n:012x}"


class Base(unittest.TestCase):
    """Arquivo e registro num diretório temporário."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name) / "agata"
        patch = mock.patch.object(importantes, "ARQUIVO", self.dir / "painel-importantes.json")
        patch.start()
        self.addCleanup(patch.stop)
        self.registro = importantes._registro_caminho()

    def criar(self, texto="ideia"):
        return importantes.criar({"texto": texto})

    def linhas_registro(self):
        if not self.registro.exists():
            return []
        return [json.loads(linha) for linha in self.registro.read_text(encoding="utf-8").splitlines()]


class ArmazemTests(Base):
    def test_arquivo_padrao_fica_no_cache_do_usuario(self):
        fonte = (HERE / "importantes.py").read_text(encoding="utf-8")
        self.assertIn('ARQUIVO = Path.home() / ".cache/agata/painel-importantes.json"', fonte)
        self.assertEqual(importantes._registro_caminho().name, "painel-importantes.registro.jsonl")

    def test_criar_grava_item_aberto_de_origem_humano(self):
        item = self.criar("  Pensar no painel de custos  ")
        self.assertRegex(item["id"], r"^[0-9a-f]{12}$")
        self.assertEqual((item["texto"], item["origem"], item["estado"], item["feito_em"], item["nota"], item["cache_n"]),
                         ("Pensar no painel de custos", "humano", "aberto", None, "", None))
        self.assertRegex(item["criado_em"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-03:00$")
        self.assertEqual(importantes.listar()["itens"], [item])

    def test_criar_recusa_texto_vazio_longo_ou_com_nulo(self):
        for ruim in ({}, {"texto": "   "}, {"texto": 7}, {"texto": "x" * 4001}, {"texto": "a\x00b"}):
            with self.subTest(ruim=ruim):
                with self.assertRaises(importantes.ErroImportantes) as caso:
                    importantes.criar(ruim)
                self.assertEqual(caso.exception.status, 400)
        self.assertEqual(importantes.listar()["itens"], [], "nenhum recusado foi gravado")

    def test_criar_recusa_campo_que_nao_existe_no_contrato(self):
        with self.assertRaises(importantes.ErroImportantes) as caso:
            importantes.criar({"texto": "ok", "origem": "modelo"})
        self.assertEqual(caso.exception.status, 400)
        self.assertFalse((self.dir / "painel-importantes.json").exists(), "o pedido recusado não grava nada")

    def test_marcar_feito_grava_a_hora_e_reabrir_limpa(self):
        item = self.criar()
        feito = importantes.mudar_estado({"id": item["id"], "estado": "feito"})
        self.assertEqual(feito["estado"], "feito")
        self.assertRegex(feito["feito_em"], r"^\d{4}-\d{2}-\d{2}T")
        reaberto = importantes.mudar_estado({"id": item["id"], "estado": "aberto"})
        self.assertEqual((reaberto["estado"], reaberto["feito_em"]), ("aberto", None))

    def test_marcar_feito_de_novo_nao_troca_a_hora(self):
        item = self.criar()
        primeiro = importantes.mudar_estado({"id": item["id"], "estado": "feito"})["feito_em"]
        with mock.patch.object(importantes, "_agora", return_value="2099-01-01T00:00:00-03:00"):
            segundo = importantes.mudar_estado({"id": item["id"], "estado": "feito"})["feito_em"]
        self.assertEqual(primeiro, segundo)

    def test_descartado_nao_some_da_lista_e_volta_com_reabrir(self):
        item = self.criar("guardar isto")
        importantes.mudar_estado({"id": item["id"], "estado": "descartado"})
        dados = importantes.listar()
        self.assertEqual([(i["texto"], i["estado"]) for i in dados["itens"]], [("guardar isto", "descartado")])
        self.assertEqual(dados["contagem"], {"aberto": 0, "feito": 0, "descartado": 1})
        importantes.mudar_estado({"id": item["id"], "estado": "aberto"})
        self.assertEqual(importantes.listar()["contagem"]["aberto"], 1)

    def test_estado_invalido_id_invalido_e_item_inexistente_recusam(self):
        item = self.criar()
        casos = [({"id": item["id"], "estado": "apagado"}, 400), ({"id": "xyz", "estado": "feito"}, 400),
                 ({"id": id_de(999), "estado": "feito"}, 404), ({"estado": "feito"}, 400),
                 ({"id": item["id"], "estado": "feito", "extra": 1}, 400), (["lista"], 400)]
        for pedido, status in casos:
            with self.subTest(pedido=pedido):
                with self.assertRaises(importantes.ErroImportantes) as caso:
                    importantes.mudar_estado(pedido)
                self.assertEqual(caso.exception.status, status)
        self.assertEqual(importantes.listar()["itens"][0]["estado"], "aberto", "nenhuma recusa mudou o item")

    def test_editar_muda_texto_e_nota_e_nota_vazia_limpa(self):
        item = self.criar("primeiro texto")
        editado = importantes.editar({"id": item["id"], "texto": "texto novo", "nota": "  ver depois  "})
        self.assertEqual((editado["texto"], editado["nota"]), ("texto novo", "ver depois"))
        limpo = importantes.editar({"id": item["id"], "nota": ""})
        self.assertEqual((limpo["texto"], limpo["nota"]), ("texto novo", ""))

    def test_editar_recusa_campo_desconhecido_nota_longa_e_pedido_vazio(self):
        item = self.criar()
        for pedido in ({"id": item["id"], "estado": "feito"}, {"id": item["id"], "nota": "x" * 501},
                       {"id": item["id"]}, {"id": item["id"], "texto": "   "}):
            with self.subTest(pedido=pedido):
                with self.assertRaises(importantes.ErroImportantes) as caso:
                    importantes.editar(pedido)
                self.assertEqual(caso.exception.status, 400)

    def test_lista_mostra_abertos_primeiro_e_o_mais_recente_antes(self):
        instantes = iter(["2026-11-11T10:00:00-03:00", "2026-11-11T11:00:00-03:00", "2026-11-11T12:00:00-03:00"])
        with mock.patch.object(importantes, "_agora", side_effect=lambda: next(instantes)):
            antigo = self.criar("antigo aberto")
            novo = self.criar("novo aberto")
            feito = self.criar("feito")
        importantes.mudar_estado({"id": feito["id"], "estado": "feito"})
        importantes.mudar_estado({"id": antigo["id"], "estado": "descartado"})
        ordem = [i["texto"] for i in importantes.listar()["itens"]]
        self.assertEqual(ordem, ["novo aberto", "feito", "antigo aberto"])

    def test_arquivo_ilegivel_nao_e_sobrescrito(self):
        self.dir.mkdir(parents=True)
        arquivo = self.dir / "painel-importantes.json"
        arquivo.write_text("{isto não é json", encoding="utf-8")
        dados = importantes.listar()
        self.assertEqual((dados["estado"], dados["itens"]), ("ilegivel", []))
        with self.assertRaises(importantes.ErroImportantes) as caso:
            self.criar()
        self.assertEqual(caso.exception.status, 409)
        self.assertEqual(arquivo.read_text(encoding="utf-8"), "{isto não é json", "o conteúdo ilegível fica como está")

    def test_item_fora_do_formato_torna_o_arquivo_ilegivel(self):
        self.dir.mkdir(parents=True)
        dados = {"schema_version": 1, "itens": [{"id": id_de(1), "texto": "ok", "origem": "humano", "criado_em": "x",
                                                  "estado": "inventado", "feito_em": None, "nota": "", "cache_n": None}]}
        (self.dir / "painel-importantes.json").write_text(json.dumps(dados), encoding="utf-8")
        self.assertEqual(importantes.listar()["estado"], "ilegivel")
        with self.assertRaises(importantes.ErroImportantes):
            importantes.mudar_estado({"id": id_de(1), "estado": "feito"})

    def test_escrita_nao_deixa_temporario_e_o_arquivo_tem_so_o_formato(self):
        self.criar("um")
        self.criar("dois")
        nomes = sorted(p.name for p in self.dir.iterdir())
        self.assertEqual(nomes, ["painel-importantes.json"], "nenhum temporário sobrou")
        bruto = json.loads((self.dir / "painel-importantes.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(bruto), ["itens", "schema_version"])
        self.assertEqual(bruto["schema_version"], 1)

    def test_lista_cheia_recusa_sem_gravar(self):
        with mock.patch.object(importantes, "ITENS_LIMITE", 2):
            self.criar("a")
            self.criar("b")
            with self.assertRaises(importantes.ErroImportantes) as caso:
                self.criar("c")
        self.assertEqual(caso.exception.status, 409)
        self.assertEqual(len(importantes.listar()["itens"]), 2)


class FonteFalsa:
    """Substituto do cache_conselho: ler devolve as entradas; filtrar recusa o que contém SEGREDO."""

    def __init__(self, entradas, falha_leitura=None):
        self.entradas = entradas
        self.falha_leitura = falha_leitura

    def ler(self, n=20, autor=None):
        if self.falha_leitura:
            raise self.falha_leitura
        return list(self.entradas)[-n:]

    def filtrar(self, texto):
        if "SEGREDO" in texto:
            raise ValueError("a nota contém segredo")
        return texto.replace("fulano@exemplo.com", "[pessoal-email removido]")


def entrada(n, texto, autor="Claude Code"):
    return {"n": n, "ts": "2026-11-11T10:00:00-0300", "autor": autor, "tipo": "pendencia", "texto": texto, "fonte": None}


class TrazerTests(Base):
    def test_traz_so_as_marcadas_com_origem_cache_e_numero(self):
        cache = FonteFalsa([entrada(1, "comum"), entrada(2, "IMPORTANTE (Humano, 11/11): ver o acervo"),
                            entrada(3, "IMPORTANTES em ordem"), entrada(4, "no meio IMPORTANTE não conta")])
        resultado = importantes.trazer_do_conselho(cache)
        self.assertEqual(resultado, {"trazidas": 1, "ja_estavam": 0, "recusadas": 0, "lidas": 4})
        item = importantes.listar()["itens"][0]
        self.assertEqual((item["origem"], item["cache_n"]), ("cache", 2))
        self.assertEqual(item["texto"], "IMPORTANTE (Humano, 11/11): ver o acervo")

    def test_nao_duplica_e_nao_traz_de_novo_o_descartado(self):
        cache = FonteFalsa([entrada(2, "IMPORTANTE: uma coisa")])
        importantes.trazer_do_conselho(cache)
        item = importantes.listar()["itens"][0]
        importantes.mudar_estado({"id": item["id"], "estado": "descartado"})
        segunda = importantes.trazer_do_conselho(cache)
        self.assertEqual((segunda["trazidas"], segunda["ja_estavam"]), (0, 1))
        self.assertEqual(len(importantes.listar()["itens"]), 1, "nenhum item novo para a mesma entrada")

    def test_segredo_nao_e_trazido_e_e_contado(self):
        cache = FonteFalsa([entrada(5, "IMPORTANTE: SEGREDO aqui"), entrada(6, "IMPORTANTE: ok")])
        resultado = importantes.trazer_do_conselho(cache)
        self.assertEqual((resultado["trazidas"], resultado["recusadas"]), (1, 1))
        self.assertNotIn("SEGREDO", json.dumps(importantes.listar(), ensure_ascii=False))

    def test_cache_ilegivel_da_500_e_nada_muda(self):
        self.criar("ja existia")
        with self.assertRaises(importantes.ErroImportantes) as caso:
            importantes.trazer_do_conselho(FonteFalsa([], falha_leitura=ValueError("linha quebrada")))
        self.assertEqual(caso.exception.status, 500)
        self.assertEqual([i["texto"] for i in importantes.listar()["itens"]], ["ja existia"])

    def test_com_o_filtro_real_do_cache_dado_pessoal_vira_marca_e_o_cache_nao_muda(self):
        cache = panel._memoria_conselho_modulo()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        arq = Path(tmp.name) / "cache.jsonl"
        linhas = [entrada(9, "IMPORTANTE: escrever para fulano@exemplo.com depois")]
        arq.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in linhas), encoding="utf-8")
        antes = arq.read_bytes()
        with mock.patch.object(cache, "ARQ", arq), mock.patch.object(cache, "LISTA_P20", Path(tmp.name) / "p20.txt"):
            resultado = importantes.trazer_do_conselho(cache)
        self.assertEqual(resultado["trazidas"], 1)
        texto = importantes.listar()["itens"][0]["texto"]
        self.assertNotIn("fulano@exemplo.com", texto)
        self.assertIn("[pessoal-email removido]", texto)
        self.assertEqual(arq.read_bytes(), antes, "o cache do Conselho não é escrito por esta função")


class RotasBase(Base):
    """Rotas de verdade num servidor numa porta livre (127.0.0.1)."""

    @classmethod
    def setUpClass(cls):
        cls.porta_antiga, cls.origem_antiga = panel.PORT, panel.ALLOWED_ORIGIN
        cls.servidor = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.servidor.daemon_threads = True
        panel.PORT = cls.servidor.server_address[1]
        panel.ALLOWED_ORIGIN = f"http://127.0.0.1:{panel.PORT}"
        cls.thread = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.thread.join(timeout=3)
        panel.PORT, panel.ALLOWED_ORIGIN = cls.porta_antiga, cls.origem_antiga

    def pede(self, metodo, caminho, corpo=None, cabecalhos=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=5)
        try:
            conn.request(metodo, caminho, body=corpo, headers=cabecalhos or {})
            resposta = conn.getresponse()
            return resposta.status, resposta.read(), {k.lower(): v for k, v in resposta.getheaders()}
        finally:
            conn.close()

    def mesma_origem(self):
        return {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json"}

    def post(self, rota, corpo, cabecalhos=None):
        bruto = corpo if isinstance(corpo, bytes) else json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        return self.pede("POST", rota, bruto, cabecalhos or self.mesma_origem())


class RotasTests(RotasBase):
    def test_get_lista_vazia_e_com_itens(self):
        status, corpo, _ = self.pede("GET", "/api/importantes", cabecalhos={"Sec-Fetch-Site": "same-origin"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(corpo)["estado"], "vazio")
        self.post("/api/importantes", {"texto": "guardar"})
        status, corpo, _ = self.pede("GET", "/api/importantes", cabecalhos={"Sec-Fetch-Site": "same-origin"})
        dados = json.loads(corpo)
        self.assertEqual((dados["estado"], dados["contagem"]["aberto"]), ("ok", 1))

    def test_get_de_outra_origem_e_recusado(self):
        status, _, _ = self.pede("GET", "/api/importantes", cabecalhos={"Sec-Fetch-Site": "cross-site"})
        self.assertEqual(status, 403)

    def test_escrita_sem_cabecalhos_responde_403_nao_grava_e_registra(self):
        status, corpo, _ = self.post("/api/importantes", {"texto": "sem origem"}, {"Content-Type": "application/json"})
        self.assertEqual((status, corpo), (403, b"cross-origin request denied"))
        self.assertFalse((self.dir / "painel-importantes.json").exists())
        self.assertEqual([(l["rota"], l["status"], l["id"]) for l in self.linhas_registro()], [("/api/importantes", 403, None)])

    def test_origem_de_outro_site_recusa_mesmo_com_a_do_painel_no_outro_cabecalho(self):
        cabecalhos = {"Origin": "http://evil.example", "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json"}
        self.assertEqual(self.post("/api/importantes", {"texto": "x"}, cabecalhos)[0], 403)
        cabecalhos = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "cross-site", "Content-Type": "application/json"}
        self.assertEqual(self.post("/api/importantes", {"texto": "x"}, cabecalhos)[0], 403)

    def test_criar_marcar_editar_pela_rota_e_registro_sem_texto(self):
        status, corpo, _ = self.post("/api/importantes", {"texto": "segredo-de-texto-xyz"})
        self.assertEqual(status, 200)
        item = json.loads(corpo)
        status, corpo, _ = self.post("/api/importantes/estado", {"id": item["id"], "estado": "feito"})
        self.assertEqual((status, json.loads(corpo)["estado"]), (200, "feito"))
        status, corpo, _ = self.post("/api/importantes/editar", {"id": item["id"], "nota": "nota-segredo-abc"})
        self.assertEqual(status, 200)
        linhas = self.linhas_registro()
        self.assertEqual([(l["rota"], l["status"], l["id"]) for l in linhas],
                         [("/api/importantes", 200, item["id"]), ("/api/importantes/estado", 200, item["id"]),
                          ("/api/importantes/editar", 200, item["id"])])
        self.assertEqual({tuple(sorted(l)) for l in linhas}, {("hora", "id", "rota", "status")})
        bruto = self.registro.read_text(encoding="utf-8")
        self.assertNotIn("segredo-de-texto-xyz", bruto)
        self.assertNotIn("nota-segredo-abc", bruto)

    def test_registro_so_acrescenta(self):
        self.post("/api/importantes", {"texto": "um"})
        antes = self.registro.read_bytes()
        self.post("/api/importantes", {"texto": "dois"})
        depois = self.registro.read_bytes()
        self.assertTrue(depois.startswith(antes) and len(depois) > len(antes))

    def test_erros_de_pedido_respondem_400_404_413_e_nao_gravam(self):
        self.assertEqual(self.post("/api/importantes", b"{nao e json")[0], 400)
        self.assertEqual(self.post("/api/importantes", {"texto": "x", "outro": 1})[0], 400)
        self.assertEqual(self.post("/api/importantes", {"texto": ""})[0], 400)
        self.assertEqual(self.post("/api/importantes/estado", {"id": id_de(42), "estado": "feito"})[0], 404)
        grande = json.dumps({"texto": "a" * 4200}).encode("utf-8")
        status, _, _ = self.pede("POST", "/api/importantes", grande, self.mesma_origem())
        self.assertEqual(status, 413)
        self.assertFalse((self.dir / "painel-importantes.json").exists(), "nenhum pedido recusado gravou")
        self.assertEqual([l["status"] for l in self.linhas_registro()], [400, 400, 400, 404, 413])

    def test_arquivo_ilegivel_responde_409_e_nao_e_sobrescrito(self):
        self.dir.mkdir(parents=True)
        arquivo = self.dir / "painel-importantes.json"
        arquivo.write_text("quebrado", encoding="utf-8")
        status, corpo, _ = self.post("/api/importantes", {"texto": "novo"})
        self.assertEqual(status, 409)
        self.assertEqual(arquivo.read_text(encoding="utf-8"), "quebrado")

    def test_trazer_pela_rota_usa_o_cache_do_conselho_sem_escrever_nele(self):
        cache = FonteFalsa([entrada(7, "IMPORTANTE: pela rota")])
        with mock.patch.object(panel, "_memoria_conselho_modulo", return_value=cache):
            status, corpo, _ = self.post("/api/importantes/trazer", {})
            segunda, corpo2, _ = self.post("/api/importantes/trazer", {})
        self.assertEqual(status, 200)
        self.assertEqual((json.loads(corpo)["trazidas"], json.loads(corpo2)["ja_estavam"]), (1, 1))
        self.assertIsNone(self.linhas_registro()[0]["id"], "trazer não tem um item só para registrar")

    def test_trazer_com_cache_indisponivel_responde_500_e_registra(self):
        cache = FonteFalsa([], falha_leitura=OSError("sem arquivo"))
        with mock.patch.object(panel, "_memoria_conselho_modulo", return_value=cache):
            status, _, _ = self.post("/api/importantes/trazer", {})
        self.assertEqual(status, 500)
        self.assertEqual(self.linhas_registro()[-1]["status"], 500)

    def test_tela_tem_a_lista_e_so_chama_as_rotas_que_existem(self):
        html = (HERE / "prototipo.html").read_text(encoding="utf-8")
        js = (HERE / "prototipo.js").read_text(encoding="utf-8")
        self.assertIn('id="importantes-lista"', html)
        for rota in ("/api/importantes", "/api/importantes/estado", "/api/importantes/editar", "/api/importantes/trazer"):
            with self.subTest(rota=rota):
                self.assertIn(rota, js)
                self.assertIn(rota, panel.IMPORTANTES_ROTAS)


if __name__ == "__main__":
    unittest.main()
