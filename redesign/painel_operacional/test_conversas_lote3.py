#!/usr/bin/env python3
"""Testes do lote 3 das conversas (09/11/2026): organização, busca, exportação e importação.

Cada teste usa um diretório temporário no lugar de armazem.CONVERSAS_DIR; nada toca em
~/.cache/agata/painel-conversas. Os de rota sobem o servidor numa porta livre (127.0.0.1).
"""
import http.client
import importlib.util
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import armazem

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("painel_lote3", HERE / "server.py")
panel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(panel)


def id_de(n):
    return f"{n:012x}"


def conversas_em(pasta):
    """Arquivos de conversa da pasta (sem organizacao.json)."""
    return [a for a in pasta.glob("*.json") if a.name != armazem.ORGANIZACAO_ARQUIVO]


class ConversasBase(unittest.TestCase):
    """Diretório temporário no lugar de CONVERSAS_DIR, com datas de modificação crescentes (n)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        patch = mock.patch.object(armazem, "CONVERSAS_DIR", self.dir)
        patch.start()
        self.addCleanup(patch.stop)

    def conversa(self, n, titulo, textos=("oi",), **extra):
        mensagens = [{"role": "user" if i % 2 == 0 else "assistant", "content": t} for i, t in enumerate(textos)]
        salvo = armazem._conversa_gravar({"id": id_de(n), "titulo": titulo, "mensagens": mensagens, **extra})
        self.assertIsNotNone(salvo, "a conversa de teste devia ser válida")
        os.utime(self.dir / (id_de(n) + ".json"), (1_700_000_000 + n, 1_700_000_000 + n))
        return salvo


class OrganizacaoTests(ConversasBase):
    def test_conversa_antiga_sem_organizacao_lista_e_abre_com_padrao(self):
        # Arquivo de antes do lote 3: sem modelo, sem organização, sem origem.
        (self.dir / (id_de(1) + ".json")).write_text(json.dumps({"titulo": "Antiga", "mensagens": [
            {"role": "user", "content": "oi"}, {"role": "assistant", "content": "olá"}]}), encoding="utf-8")
        item = armazem._conversas_listar()["items"][0]
        self.assertEqual((item["fixada"], item["arquivada"], item["marcadores"], item["pasta"]), (False, False, [], None))
        self.assertEqual(armazem._conversa_ler(id_de(1))["modelo"], "seth-livre")
        self.assertEqual(armazem._conversas_buscar("olá")["resultados"][0]["id"], id_de(1))
        corpo, nome, _ = armazem._conversa_exportar(id_de(1), "json")
        self.assertEqual(json.loads(corpo)["origem_id"], id_de(1))

    def test_fixar_arquivar_marcar_e_pasta_nao_mexem_no_conteudo(self):
        self.conversa(1, "Primeira", ("texto original",))
        arq = self.dir / (id_de(1) + ".json")
        antes = arq.read_bytes()
        armazem._conversa_organizar(id_de(1), {"fixada": True, "arquivada": False, "marcadores": ["Auditoria", "  ideia  "]})
        self.assertEqual(arq.read_bytes(), antes, "organizar não pode reescrever a conversa")
        item = armazem._conversas_listar()["items"][0]
        self.assertTrue(item["fixada"])
        self.assertEqual(item["marcadores"], ["auditoria", "ideia"])

    def test_fixada_vai_para_o_topo_mesmo_mais_antiga(self):
        self.conversa(1, "Antiga fixada")
        self.conversa(2, "Nova")
        armazem._conversa_organizar(id_de(1), {"fixada": True})
        self.assertEqual([c["titulo"] for c in armazem._conversas_listar()["items"]], ["Antiga fixada", "Nova"])

    def test_organizar_recusa_fora_do_contrato_com_motivo(self):
        self.conversa(1, "Uma")
        casos = [
            ({"marcadores": ["x" * 25]}, 400, "marcador passa de 24 caracteres"),
            ({"marcadores": [f"m{i}" for i in range(11)]}, 400, "a conversa aceita até 10 marcadores"),
            ({"marcadores": ["#tag"]}, 400, "marcador só pode ter letras, números, espaço e hífen"),
            ({"marcadores": ["   "]}, 400, "marcador vazio"),
            ({"marcadores": "auditoria"}, 400, "marcadores precisa ser uma lista"),
            ({"fixada": "sim"}, 400, "fixada precisa ser sim ou não"),
            ({"pasta": "naoexiste0000"}, 400, "a pasta não existe"),
            ({"apagar": True}, 400, "campo desconhecido: apagar"),
        ]
        for campos, status, motivo in casos:
            with self.subTest(campos=campos), self.assertRaises(armazem.ErroConversa) as erro:
                armazem._conversa_organizar(id_de(1), campos)
            self.assertEqual((erro.exception.status, erro.exception.motivo), (status, motivo))
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._conversa_organizar(id_de(99), {"fixada": True})
        self.assertEqual(erro.exception.status, 404)
        with self.assertRaises(armazem.ErroConversa):
            armazem._conversa_organizar(id_de(1), {})
        self.assertFalse((self.dir / armazem.ORGANIZACAO_ARQUIVO).exists(), "recusa não grava nada")

    def test_salvar_a_conversa_depois_nao_apaga_a_organizacao(self):
        self.conversa(1, "Guardada")
        armazem._conversa_organizar(id_de(1), {"fixada": True, "marcadores": ["ideia"]})
        armazem._conversa_gravar({"id": id_de(1), "titulo": "Guardada", "mensagens": [{"role": "user", "content": "nova"}]})
        item = armazem._conversas_listar()["items"][0]
        self.assertEqual((item["fixada"], item["marcadores"]), (True, ["ideia"]))

    def test_apagar_conversa_tira_a_entrada_da_organizacao(self):
        self.conversa(1, "Apagar")
        armazem._conversa_organizar(id_de(1), {"fixada": True})
        self.assertTrue(armazem._conversa_apagar(id_de(1)))
        org = json.loads((self.dir / armazem.ORGANIZACAO_ARQUIVO).read_text(encoding="utf-8"))
        self.assertNotIn(id_de(1), org["conversas"])

    def test_organizacao_malformada_e_lida_com_tolerancia(self):
        self.conversa(1, "Uma")
        (self.dir / armazem.ORGANIZACAO_ARQUIVO).write_text(json.dumps({"pastas": [
            {"id": "a00000000001", "nome": "  Projeto  X "}, {"id": "ruim", "nome": "x"}, "lixo"],
            "conversas": {id_de(1): {"fixada": "sim", "marcadores": [["lista"], "ok", "ok"], "pasta": ["x"]},
                          "nao-hex": {"fixada": True}}}), encoding="utf-8")
        org, legivel = armazem._organizacao_ler()
        self.assertTrue(legivel)
        self.assertEqual(org["pastas"], [{"id": "a00000000001", "nome": "Projeto X"}])
        self.assertEqual(org["conversas"], {id_de(1): {"fixada": False, "arquivada": False, "marcadores": ["ok"],
                                                        "pasta": None, "origem_id": None}})

    def test_organizacao_ilegivel_recusa_escrita_e_avisa_na_lista(self):
        self.conversa(1, "Uma")
        arq = self.dir / armazem.ORGANIZACAO_ARQUIVO
        arq.write_text("{não é json", encoding="utf-8")
        listado = armazem._conversas_listar()
        self.assertEqual(listado["organizacao"], "ilegivel")
        self.assertEqual(len(listado["items"]), 1, "a lista continua funcionando")
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._conversa_organizar(id_de(1), {"fixada": True})
        self.assertEqual(erro.exception.status, 409)
        self.assertEqual(arq.read_text(encoding="utf-8"), "{não é json", "o arquivo ilegível não pode ser sobrescrito")


class PastasTests(ConversasBase):
    def test_criar_mover_renomear_e_apagar_pasta_sem_apagar_conversa(self):
        self.conversa(1, "Da pasta")
        criada = armazem._pasta_mudar("criar", nome="  Projeto   X ")
        self.assertEqual(criada["nome"], "Projeto X")
        armazem._conversa_organizar(id_de(1), {"pasta": criada["id"]})
        lista = armazem._conversas_listar()
        self.assertEqual(lista["pastas"], [{"id": criada["id"], "nome": "Projeto X", "conversas": 1}])
        self.assertEqual(lista["items"][0]["pasta"], criada["id"])
        renomeada = armazem._pasta_mudar("renomear", criada["id"], "Projeto Y")
        self.assertEqual(renomeada["nome"], "Projeto Y")
        apagada = armazem._pasta_mudar("apagar", criada["id"])
        self.assertEqual(apagada, {"apagada": True, "conversas_soltas": 1})
        lista = armazem._conversas_listar()
        self.assertEqual(lista["pastas"], [])
        self.assertEqual([c["id"] for c in lista["items"]], [id_de(1)], "apagar pasta não apaga conversa")
        self.assertIsNone(lista["items"][0]["pasta"])

    def test_pasta_recusa_nome_repetido_longo_e_acao_fora_da_lista(self):
        armazem._pasta_mudar("criar", nome="Ideias")
        casos = [
            (("criar", None, "ideias"), 400, "já existe pasta com esse nome"),
            (("criar", None, "x" * 61), 400, "nome da pasta passa de 60 caracteres"),
            (("criar", None, "   "), 400, "nome da pasta vazio"),
            (("mover", None, "x"), 400, "ação de pasta desconhecida"),
            (("apagar", "../etc", None), 400, "pasta inválida"),
            (("renomear", id_de(77), "Outro"), 404, "pasta não encontrada"),
        ]
        for argumentos, status, motivo in casos:
            with self.subTest(argumentos=argumentos), self.assertRaises(armazem.ErroConversa) as erro:
                armazem._pasta_mudar(*argumentos)
            self.assertEqual((erro.exception.status, erro.exception.motivo), (status, motivo))

    def test_limite_de_50_pastas(self):
        for i in range(50):
            armazem._pasta_mudar("criar", nome=f"Pasta {i}")
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._pasta_mudar("criar", nome="Pasta 51")
        self.assertEqual(erro.exception.motivo, "limite de 50 pastas; apague alguma antes")


class BuscaTests(ConversasBase):
    def setUp(self):
        super().setUp()
        self.conversa(1, "Revisão da ação", ("nada aqui", "Vamos revisar a AÇÃO do decisor"))
        self.conversa(2, "Proposta de cadeia", ("texto sem termo",))
        self.conversa(3, "Outra conversa", ("Ação",))

    def test_busca_acha_mensagem_sem_acento_nem_caixa_e_aponta_a_posicao(self):
        resultado = armazem._conversas_buscar("ACAO")
        self.assertEqual(resultado["termo"], "ACAO")
        por_id = {r["id"]: r for r in resultado["resultados"]}
        self.assertEqual(por_id[id_de(1)]["campo"], "mensagem")
        self.assertEqual(por_id[id_de(1)]["mensagem"], 1)
        self.assertEqual(por_id[id_de(1)]["ocorrencias"], 2, "título e mensagem contam")
        self.assertIn("AÇÃO", por_id[id_de(1)]["trecho"])
        self.assertEqual(por_id[id_de(3)]["mensagem"], 0)
        self.assertNotIn(id_de(2), por_id)

    def test_busca_no_titulo_nao_tem_mensagem_para_abrir(self):
        resultado = armazem._conversas_buscar("proposta")
        self.assertEqual(resultado["total"], 1)
        self.assertEqual(resultado["resultados"][0]["campo"], "titulo")
        self.assertIsNone(resultado["resultados"][0]["mensagem"])

    def test_termo_sem_resultado_nao_e_erro(self):
        resultado = armazem._conversas_buscar("inexistente")
        self.assertEqual((resultado["total"], resultado["resultados"]), (0, []))

    def test_busca_recusa_termo_vazio_e_longo(self):
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._conversas_buscar("   ")
        self.assertEqual(erro.exception.motivo, "digite o que procurar")
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._conversas_buscar("x" * 121)
        self.assertEqual(erro.exception.motivo, "a busca aceita até 120 caracteres")

    def test_busca_marca_arquivada_e_limita_a_50_resultados(self):
        armazem._conversa_organizar(id_de(3), {"arquivada": True})
        for n in range(10, 61):
            self.conversa(n, f"Alvo {n}", ("alvo",))
        resultado = armazem._conversas_buscar("alvo")
        self.assertEqual(resultado["total"], 51)
        self.assertEqual(len(resultado["resultados"]), 50)
        self.assertEqual(armazem._conversas_buscar("outra")["resultados"][0]["arquivada"], True)

    def test_trecho_tem_contexto_e_reticencias(self):
        self.conversa(20, "Longa", ("a" * 300 + "ALVO" + "b" * 300,))
        trecho = armazem._conversas_buscar("alvo")["resultados"][0]["trecho"]
        self.assertTrue(trecho.startswith("…") and trecho.endswith("…"))
        self.assertIn("ALVO", trecho)
        self.assertLessEqual(len(trecho), 130)

    def test_dobrar_mantem_o_tamanho_para_a_posicao_valer(self):
        for texto in ("Ação", "AÇÃO revisada", "İstanbul ß", "combinação"):
            self.assertEqual(len(armazem._dobrar(texto)), len(texto))
        self.assertEqual(armazem._dobrar("AÇÃO"), "acao")


class ExportacaoImportacaoTests(ConversasBase):
    def setUp(self):
        super().setUp()
        self.conversa(1, "Para levar", ("pergunta", "resposta"), modelo="seth-public")
        mensagens = [{"role": "user", "content": "oi"},
                     {"role": "assistant", "content": "olá", "modelo": "seth-public", "modelo_real": "openai/gpt-oss-120b"}]
        armazem._conversa_gravar({"id": id_de(2), "titulo": "Com modelo", "modelo": "seth-public", "mensagens": mensagens})

    def test_exporta_json_e_markdown_com_nome_so_com_o_id(self):
        corpo, nome, tipo = armazem._conversa_exportar(id_de(2), "json")
        dados = json.loads(corpo)
        self.assertEqual((dados["formato"], dados["versao"], dados["id"], dados["origem_id"]),
                         ("agata-conversa", 1, id_de(2), id_de(2)))
        self.assertEqual(nome, f"agata-conversa-{id_de(2)}.json")
        self.assertEqual(tipo, "application/json; charset=utf-8")
        corpo_md, nome_md, tipo_md = armazem._conversa_exportar(id_de(2), "md")
        texto = corpo_md.decode("utf-8")
        self.assertTrue(texto.startswith("# Com modelo\n"))
        self.assertIn("## Você", texto)
        self.assertIn("## Seth (modelo: openai/gpt-oss-120b)", texto)
        self.assertEqual((nome_md, tipo_md), (f"agata-conversa-{id_de(2)}.md", "text/markdown; charset=utf-8"))

    def test_exportacao_recusa_formato_e_id(self):
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._conversa_exportar(id_de(2), "pdf")
        self.assertEqual(erro.exception.status, 400)
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._conversa_exportar(id_de(42), "json")
        self.assertEqual(erro.exception.status, 404)

    def test_importa_em_outra_instalacao_e_nao_duplica_por_id_ou_origem(self):
        corpo, _, _ = armazem._conversa_exportar(id_de(2), "json")
        tmp_outra = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_outra.cleanup)
        outra = Path(tmp_outra.name)
        with mock.patch.object(armazem, "CONVERSAS_DIR", outra):
            primeira = armazem._conversa_importar(json.loads(corpo))
            self.assertEqual(primeira["estado"], "importada")
            self.assertNotEqual(primeira["id"], id_de(2))
            self.assertEqual(len(conversas_em(outra)), 1)
            self.assertEqual(armazem._organizacao_ler()[0]["conversas"][primeira["id"]]["origem_id"], id_de(2))
            segunda = armazem._conversa_importar(json.loads(corpo))
            self.assertEqual((segunda["estado"], segunda["id"]), ("ja_existe", primeira["id"]))
            self.assertEqual(len(conversas_em(outra)), 1, "reconhecida não grava de novo")
            por_origem = dict(json.loads(corpo), id=id_de(9), origem_id=id_de(2))
            self.assertEqual(armazem._conversa_importar(por_origem)["estado"], "ja_existe")
        terceira = armazem._conversa_importar(json.loads(corpo))
        self.assertEqual((terceira["estado"], terceira["id"]), ("ja_existe", id_de(2)), "na mesma instalação, pelo id")

    def test_importa_recusa_arquivo_que_nao_e_do_painel(self):
        corpo = json.loads(armazem._conversa_exportar(id_de(2), "json")[0])
        casos = [
            (dict(corpo, formato="outro"), "o arquivo não é uma conversa exportada pelo painel (formato ou versão)"),
            (dict(corpo, versao=2), "o arquivo não é uma conversa exportada pelo painel (formato ou versão)"),
            (dict(corpo, versao=True), "o arquivo não é uma conversa exportada pelo painel (formato ou versão)"),
            ({k: v for k, v in corpo.items() if k not in ("id", "origem_id")}, "arquivo sem identificador da conversa"),
            (dict(corpo, id="../../etc"), "identificador da conversa inválido"),
            (dict(corpo, modelo="seth-zai"), "modelo fora da lista"),
        ]
        for dados, motivo in casos:
            with self.subTest(motivo=motivo), self.assertRaises(armazem.ErroConversa) as erro:
                armazem._conversa_importar(dados)
            self.assertEqual((erro.exception.status, erro.exception.motivo), (400, motivo))
        self.assertEqual(len(conversas_em(self.dir)), 2, "recusa não grava nada")


class RotasConversasTests(ConversasBase):
    """Rotas novas pelo servidor de verdade, numa porta livre."""

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

    def mesma_origem(self, tipo="application/json"):
        return {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": tipo}

    def test_busca_pela_rota_devolve_trecho_e_posicao(self):
        self.conversa(1, "Rota", ("primeiro", "fala sobre a ação"))
        status, corpo, cab = self.pede("GET", "/api/seth/conversas/busca?q=acao")
        self.assertEqual(status, 200)
        dados = json.loads(corpo)
        self.assertEqual((dados["schema_version"], dados["resultados"][0]["mensagem"]), (1, 1))
        self.assertEqual(cab["cache-control"], "no-store")

    def test_busca_recusa_termo_vazio_longo_e_origem_cruzada(self):
        self.assertEqual(self.pede("GET", "/api/seth/conversas/busca?q=")[0], 400)
        self.assertEqual(self.pede("GET", "/api/seth/conversas/busca?q=" + "x" * 121)[0], 400)
        cruzada = {"Origin": "https://exemplo.invalid"}
        self.assertEqual(self.pede("GET", "/api/seth/conversas/busca?q=oi", cabecalhos=cruzada)[0], 403)

    def test_exportar_pela_rota_baixa_com_nome_so_com_o_id(self):
        self.conversa(1, "Baixar")
        status, corpo, cab = self.pede("GET", f"/api/seth/conversa/exportar?id={id_de(1)}&formato=md")
        self.assertEqual(status, 200)
        self.assertEqual(cab["content-disposition"], f'attachment; filename="agata-conversa-{id_de(1)}.md"')
        self.assertTrue(corpo.decode("utf-8").startswith("# Baixar"))
        self.assertEqual(self.pede("GET", f"/api/seth/conversa/exportar?id={id_de(1)}&formato=exe")[0], 400)
        self.assertEqual(self.pede("GET", f"/api/seth/conversa/exportar?id={id_de(9)}&formato=json")[0], 404)
        self.assertEqual(self.pede("GET", f"/api/seth/conversa/exportar?id={id_de(1)}&formato=json",
                                   cabecalhos={"Origin": "https://exemplo.invalid"})[0], 403)

    def test_organizar_pela_rota_grava_e_recusa_origem_cruzada_e_pedido_grande(self):
        self.conversa(1, "Rota")
        corpo = json.dumps({"id": id_de(1), "fixada": True, "marcadores": ["ideia"]}).encode("utf-8")
        status, dados, _ = self.pede("POST", "/api/seth/conversa/organizar", corpo, self.mesma_origem())
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(dados)["marcadores"], ["ideia"])
        cruzado = dict(self.mesma_origem(), **{"Sec-Fetch-Site": "cross-site"})
        self.assertEqual(self.pede("POST", "/api/seth/conversa/organizar", corpo, cruzado)[0], 403)
        grande = b"{" + b" " * 4200 + b"}"
        self.assertEqual(self.pede("POST", "/api/seth/conversa/organizar", grande, self.mesma_origem())[0], 413)
        ruim = json.dumps({"id": id_de(1), "fixada": "sim"}).encode("utf-8")
        status, texto, _ = self.pede("POST", "/api/seth/conversa/organizar", ruim, self.mesma_origem())
        self.assertEqual((status, texto), (400, b"fixada precisa ser sim ou n\xc3\xa3o"))

    def test_pastas_pela_rota_e_lista_com_contagem(self):
        self.conversa(1, "Na pasta")
        status, corpo, _ = self.pede("POST", "/api/seth/pastas", json.dumps({"acao": "criar", "nome": "Projeto"}).encode(),
                                     self.mesma_origem())
        self.assertEqual(status, 200)
        pasta = json.loads(corpo)
        self.pede("POST", "/api/seth/conversa/organizar", json.dumps({"id": id_de(1), "pasta": pasta["id"]}).encode(),
                  self.mesma_origem())
        listado = json.loads(self.pede("GET", "/api/seth/conversas")[1])
        self.assertEqual(listado["pastas"], [{"id": pasta["id"], "nome": "Projeto", "conversas": 1}])
        self.assertEqual(listado["organizacao"], "ok")
        self.assertEqual(self.pede("POST", "/api/seth/pastas", json.dumps({"acao": "mover"}).encode(), self.mesma_origem())[0], 400)
        self.assertEqual(self.pede("POST", "/api/seth/pastas", b"[1]", self.mesma_origem())[0], 400)
        cruzado = dict(self.mesma_origem(), **{"Sec-Fetch-Site": "cross-site"})
        self.assertEqual(self.pede("POST", "/api/seth/pastas", json.dumps({"acao": "criar", "nome": "X"}).encode(), cruzado)[0], 403)

    def test_importar_pela_rota_recusa_acima_do_limite_sem_ler_e_nao_duplica(self):
        self.conversa(1, "Para importar")
        corpo = armazem._conversa_exportar(id_de(1), "json")[0]
        cabecalhos = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json",
                      "Content-Length": str(armazem.IMPORTACAO_LIMITE_BYTES + 1)}
        status, texto, _ = self.pede("POST", "/api/seth/conversa/importar", None, cabecalhos)
        self.assertEqual(status, 413)
        self.assertIn(f"arquivo acima de {armazem.IMPORTACAO_LIMITE_BYTES} bytes".encode(), texto)
        status, dados, _ = self.pede("POST", "/api/seth/conversa/importar", corpo, self.mesma_origem())
        self.assertEqual(json.loads(dados)["estado"], "ja_existe")
        self.assertEqual(self.pede("POST", "/api/seth/conversa/importar", b"{nao json", self.mesma_origem())[0], 400)
        cruzado = dict(self.mesma_origem(), **{"Sec-Fetch-Site": "cross-site"})
        self.assertEqual(self.pede("POST", "/api/seth/conversa/importar", corpo, cruzado)[0], 403)


if __name__ == "__main__":
    unittest.main()
