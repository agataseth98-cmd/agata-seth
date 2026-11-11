#!/usr/bin/env python3
"""Testes da proteção das conversas (09/11/2026, chat-protege-conversas-09-11).

Cobre: apagar move para a lixeira (com a organização); restaurar; purga só manual; escritas recusam origem
alheia (403 sem cabeçalhos); registro de escritas em .registro.jsonl sem conteúdo; salvar conversa importada
preserva a origem; arquivo ilegível é contado e não é apagado.

Cada teste usa um diretório temporário no lugar de armazem.CONVERSAS_DIR; nada toca em
~/.cache/agata/painel-conversas. Os de rota sobem o servidor numa porta livre (127.0.0.1).
"""
import http.client
import importlib.util
import json
import re
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import armazem

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("painel_protege", HERE / "server.py")
panel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(panel)

LIXEIRA = armazem.LIXEIRA_PASTA
ORGANIZACAO = armazem.ORGANIZACAO_ARQUIVO
REGISTRO = armazem.REGISTRO_ARQUIVO
ID_IMPORTADO = "a1b2c3d4e5f6"
ORIGEM_IMPORTADA = {"origem": "librechat", "origem_id": "5a1e0c2e-7b1d-4c3a-9f10-0000000000a1",
                    "titulo_original": "Importada", "importado_em": "2026-11-07T13:00:00-03:00",
                    "data_original": {"criada": "2026-11-01T09:00:00-03:00", "atualizada": "2026-11-01T09:05:00-03:00"}}


def gravar_importado(pasta):
    """Arquivo como o importador do LibreChat grava (migrar.py): nome = id, id dentro, origem e mensagens com origem."""
    dados = {"id": ID_IMPORTADO, "titulo": "[LibreChat] Importada", **ORIGEM_IMPORTADA,
             "mensagens": [{"role": "user", "content": "pergunta", "criada": "2026-11-01T09:00:00-03:00", "origem_id": "m1"},
                           {"role": "assistant", "content": "resposta", "criada": "2026-11-01T09:01:00-03:00", "origem_id": "m2"}]}
    (pasta / (ID_IMPORTADO + ".json")).write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return json.loads((pasta / (ID_IMPORTADO + ".json")).read_text(encoding="utf-8"))


def id_de(n):
    return f"{n:012x}"


class Base(unittest.TestCase):
    """Diretório temporário no lugar de CONVERSAS_DIR."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        patch = mock.patch.object(armazem, "CONVERSAS_DIR", self.dir)
        patch.start()
        self.addCleanup(patch.stop)

    def conversa(self, n, titulo="Conversa", textos=("oi", "olá"), **extra):
        mensagens = [{"role": "user" if i % 2 == 0 else "assistant", "content": t} for i, t in enumerate(textos)]
        salvo = armazem._conversa_gravar({"id": id_de(n), "titulo": titulo, "mensagens": mensagens, **extra})
        self.assertIsNotNone(salvo, "a conversa de teste devia ser válida")
        return salvo

    def arquivos_de_conversa(self):
        return sorted(p.name for p in self.dir.glob("*.json") if p.name != ORGANIZACAO)

    def organizacao(self):
        return json.loads((self.dir / ORGANIZACAO).read_text(encoding="utf-8"))


class LixeiraTests(Base):
    def test_apagar_move_o_arquivo_para_a_lixeira_com_os_mesmos_bytes(self):
        self.conversa(1, "Para apagar")
        original = (self.dir / (id_de(1) + ".json")).read_bytes()
        nome = armazem._conversa_apagar(id_de(1))
        self.assertRegex(nome, rf"^{id_de(1)}-[0-9]{{8}}-[0-9]{{6}}$")
        self.assertFalse((self.dir / (id_de(1) + ".json")).exists(), "a conversa sai da pasta principal")
        self.assertEqual((self.dir / LIXEIRA / (nome + ".json")).read_bytes(), original, "mover não muda o conteúdo")

    def test_entrada_de_organizacao_vai_junto_e_volta_ao_restaurar(self):
        self.conversa(1, "Organizada")
        armazem._conversa_organizar(id_de(1), {"fixada": True, "marcadores": ["ideia"]})
        original = (self.dir / (id_de(1) + ".json")).read_bytes()
        nome = armazem._conversa_apagar(id_de(1))
        org = self.organizacao()
        self.assertNotIn(id_de(1), org["conversas"], "a entrada sai da organização principal")
        self.assertEqual((org["lixeira"][nome]["fixada"], org["lixeira"][nome]["marcadores"]), (True, ["ideia"]))
        restaurada = armazem._lixeira_restaurar(nome)
        self.assertEqual(restaurada, {"id": id_de(1), "titulo": "Organizada", "restaurada": True})
        self.assertEqual((self.dir / (id_de(1) + ".json")).read_bytes(), original)
        item = armazem._conversas_listar()["items"][0]
        self.assertEqual((item["fixada"], item["marcadores"]), (True, ["ideia"]))
        self.assertEqual(self.organizacao()["lixeira"], {}, "restaurar tira a entrada da lixeira")

    def test_apagar_conversa_sem_organizacao_nao_cria_entrada(self):
        self.conversa(1, "Simples")
        armazem._conversa_apagar(id_de(1))
        self.assertFalse((self.dir / ORGANIZACAO).exists(), "sem organização, nada é gravado")
        self.assertEqual(armazem._lixeira_listar()["total"], 1)

    def test_lixeira_lista_titulo_data_e_contagem_sem_o_texto(self):
        self.conversa(1, "Lista", ("pergunta sem destino", "resposta"))
        nome = armazem._conversa_apagar(id_de(1))
        listado = armazem._lixeira_listar()
        item = listado["items"][0]
        self.assertEqual((item["nome"], item["id"], item["titulo"], item["mensagens"]), (nome, id_de(1), "Lista", 2))
        self.assertRegex(item["apagada_em"], r"^[0-9]{2}/[0-9]{2}/[0-9]{4} [0-9]{2}:[0-9]{2}$")
        self.assertNotIn("pergunta sem destino", json.dumps(listado, ensure_ascii=False))
        self.assertEqual(armazem._conversas_listar()["items"], [], "a apagada sai da lista principal")

    def test_nada_e_purgado_sozinho(self):
        self.conversa(1, "Fica")
        nome = armazem._conversa_apagar(id_de(1))
        armazem._conversas_listar()
        armazem._lixeira_listar()
        armazem._conversas_buscar("fica")
        self.assertEqual(armazem._lixeira_listar()["total"], 1, "listar e buscar não apagam nada")
        self.assertTrue((self.dir / LIXEIRA / (nome + ".json")).exists())

    def test_purga_so_quando_pedida_e_tira_a_entrada(self):
        self.conversa(1, "Vai embora")
        armazem._conversa_organizar(id_de(1), {"fixada": True})
        nome = armazem._conversa_apagar(id_de(1))
        self.assertEqual(armazem._lixeira_purgar(nome), {"purgada": True})
        self.assertFalse((self.dir / LIXEIRA / (nome + ".json")).exists())
        self.assertNotIn(nome, self.organizacao()["lixeira"])
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._lixeira_purgar(nome)
        self.assertEqual(erro.exception.status, 404)

    def test_restaurar_recusa_conflito_e_mantem_o_item_na_lixeira(self):
        self.conversa(1, "Repetida")
        nome = armazem._conversa_apagar(id_de(1))
        self.conversa(1, "Outra com o mesmo id")
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._lixeira_restaurar(nome)
        self.assertEqual((erro.exception.status, erro.exception.motivo),
                         (409, "já existe conversa com este identificador; nada foi restaurado"))
        self.assertTrue((self.dir / LIXEIRA / (nome + ".json")).exists(), "conflito não mexe na lixeira")

    def test_restaurar_recusa_nome_invalido_e_item_inexistente(self):
        for ruim in ("../../etc/passwd", id_de(1), None, 42, f"{id_de(1)}-20261109-16180x", f"{id_de(1)}-20261109-161800/../x"):
            with self.subTest(nome=ruim), self.assertRaises(armazem.ErroConversa) as erro:
                armazem._lixeira_restaurar(ruim)
            self.assertEqual(erro.exception.status, 400)
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._lixeira_restaurar(f"{id_de(9)}-20260101-000000")
        self.assertEqual(erro.exception.status, 404)

    def test_mesma_conversa_apagada_duas_vezes_nao_colide(self):
        self.conversa(1, "Primeira vez")
        primeiro = armazem._conversa_apagar(id_de(1))
        self.conversa(1, "Segunda vez")
        segundo = armazem._conversa_apagar(id_de(1))
        self.assertNotEqual(primeiro, segundo)
        self.assertEqual(len(list((self.dir / LIXEIRA).glob("*.json"))), 2, "as duas versões ficam na lixeira")

    def test_pasta_apagada_enquanto_na_lixeira_vira_sem_pasta_ao_restaurar(self):
        self.conversa(1, "Com pasta")
        pasta = armazem._pasta_mudar("criar", nome="Projeto")
        armazem._conversa_organizar(id_de(1), {"pasta": pasta["id"]})
        nome = armazem._conversa_apagar(id_de(1))
        armazem._pasta_mudar("apagar", pasta["id"])
        armazem._lixeira_restaurar(nome)
        self.assertIsNone(armazem._conversas_listar()["items"][0]["pasta"])

    def test_apagar_com_organizacao_ilegivel_recusa_e_nao_mexe_no_arquivo(self):
        self.conversa(1, "Intacta")
        (self.dir / ORGANIZACAO).write_text("{não é json", encoding="utf-8")
        with self.assertRaises(armazem.ErroConversa) as erro:
            armazem._conversa_apagar(id_de(1))
        self.assertEqual(erro.exception.status, 409)
        self.assertTrue((self.dir / (id_de(1) + ".json")).exists())
        self.assertFalse((self.dir / LIXEIRA).exists(), "recusa não cria a lixeira")

    def test_apagar_conversa_inexistente_devolve_none(self):
        self.assertIsNone(armazem._conversa_apagar(id_de(5)))

    def test_importar_conversa_que_esta_na_lixeira_nao_duplica(self):
        self.conversa(1, "Vinda")
        corpo = json.loads(armazem._conversa_exportar(id_de(1), "json")[0])
        armazem._conversa_apagar(id_de(1))
        resultado = armazem._conversa_importar(corpo)
        self.assertEqual((resultado["estado"], resultado["id"], resultado.get("lixeira")), ("ja_existe", id_de(1), True))
        self.assertEqual(self.arquivos_de_conversa(), [], "a reimportação não grava nada fora da lixeira")


class RotasBase(Base):
    """Rotas de verdade, num servidor numa porta livre (127.0.0.1)."""

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

    def post_json(self, rota, corpo, cabecalhos=None):
        return self.pede("POST", rota, json.dumps(corpo, ensure_ascii=False).encode("utf-8"), cabecalhos or self.mesma_origem())


class EscritaOrigemTests(RotasBase):
    def test_escritas_sem_cabecalhos_respondem_403_e_nao_gravam(self):
        self.conversa(1, "Protegida")
        self.conversa(2, "Na lixeira")
        nome_lixeira = armazem._conversa_apagar(id_de(2))
        arquivos_antes = self.arquivos_de_conversa()
        lixeira_antes = sorted(p.name for p in (self.dir / LIXEIRA).glob("*.json"))
        exportado = json.loads(armazem._conversa_exportar(id_de(1), "json")[0])
        cenarios = [
            ("/api/seth/conversa", {"titulo": "Nova", "mensagens": [{"role": "user", "content": "oi"}]}),
            ("/api/seth/conversa/apagar", {"id": id_de(1)}),
            ("/api/seth/conversa/organizar", {"id": id_de(1), "fixada": True}),
            ("/api/seth/pastas", {"acao": "criar", "nome": "Sem cabeçalho"}),
            ("/api/seth/conversa/importar", dict(exportado, id=id_de(8), origem_id=id_de(8))),
            ("/api/seth/lixeira/restaurar", {"nome": nome_lixeira}),
            ("/api/seth/lixeira/purgar", {"nome": nome_lixeira}),
        ]
        for rota, corpo in cenarios:
            with self.subTest(rota=rota):
                status, texto, _ = self.post_json(rota, corpo, {"Content-Type": "application/json"})
                self.assertEqual((status, texto), (403, b"cross-origin request denied"))
        self.assertEqual(self.arquivos_de_conversa(), arquivos_antes, "nenhuma conversa foi criada ou apagada")
        self.assertEqual(sorted(p.name for p in (self.dir / LIXEIRA).glob("*.json")), lixeira_antes, "a purga sem cabeçalho não aconteceu")
        self.assertEqual(armazem._organizacao_ler()[0]["pastas"], [], "a pasta sem cabeçalho não foi criada")

    def test_origem_do_painel_ou_same_origin_passam(self):
        self.conversa(1, "Ok")
        corpo = {"id": id_de(1), "fixada": True}
        status, _, _ = self.post_json("/api/seth/conversa/organizar", corpo, {"Origin": panel.ALLOWED_ORIGIN, "Content-Type": "application/json"})
        self.assertEqual(status, 200, "Origin igual ao do painel")
        status, _, _ = self.post_json("/api/seth/conversa/organizar", corpo, {"Sec-Fetch-Site": "same-origin", "Content-Type": "application/json"})
        self.assertEqual(status, 200, "Sec-Fetch-Site same-origin")

    def test_cabecalho_de_outro_site_recusa_mesmo_com_origem_do_painel(self):
        self.conversa(1, "Ok")
        casos = {
            "cross-site com a origem do painel": {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "cross-site"},
            "origem de outro site": {"Origin": "https://exemplo.invalid", "Sec-Fetch-Site": "same-origin"},
            "origem nula": {"Origin": "null"},
            "navegação sem origem": {"Sec-Fetch-Site": "none"},
        }
        for nome, cab in casos.items():
            with self.subTest(caso=nome):
                status, _, _ = self.post_json("/api/seth/conversa/organizar", {"id": id_de(1), "fixada": True},
                                              {**cab, "Content-Type": "application/json"})
                self.assertEqual(status, 403)
        self.assertFalse(armazem._conversas_listar()["items"][0]["fixada"], "nenhum pedido recusado gravou")

    def test_leitura_da_lixeira_segue_o_padrao_das_leituras(self):
        self.assertEqual(self.pede("GET", "/api/seth/lixeira")[0], 200)
        self.assertEqual(self.pede("GET", "/api/seth/lixeira", None, {"Origin": "https://exemplo.invalid"})[0], 403)

    def test_salvar_do_cliente_pela_api_preserva_a_origem_e_nao_cria_segundo_arquivo(self):
        # caminho real do painel: GET da conversa importada, POST com id, titulo e mensagens (role, content)
        gravar_importado(self.dir)
        status, corpo, _ = self.pede("GET", f"/api/seth/conversa?id={ID_IMPORTADO}")
        self.assertEqual(status, 200)
        aberta = json.loads(corpo)
        envio = {"id": ID_IMPORTADO, "titulo": "Renomeada",
                 "mensagens": [{"role": m["role"], "content": m["content"]} for m in aberta["mensagens"]]}
        self.assertEqual(self.post_json("/api/seth/conversa", envio)[0], 200)
        gravado = json.loads((self.dir / (ID_IMPORTADO + ".json")).read_text(encoding="utf-8"))
        self.assertEqual((gravado["origem"], gravado["origem_id"], gravado["titulo"]),
                         (ORIGEM_IMPORTADA["origem"], ORIGEM_IMPORTADA["origem_id"], "Renomeada"))
        self.assertEqual(self.arquivos_de_conversa(), [ID_IMPORTADO + ".json"])

    def test_post_sem_id_com_origem_pela_api_nao_cria_segundo_arquivo(self):
        gravar_importado(self.dir)
        corpo = {"titulo": "[LibreChat] Importada", **ORIGEM_IMPORTADA, "mensagens": [{"role": "user", "content": "pergunta"}]}
        status, dados, _ = self.post_json("/api/seth/conversa", corpo)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(dados)["id"], ID_IMPORTADO)
        self.assertEqual(self.arquivos_de_conversa(), [ID_IMPORTADO + ".json"])

class OrigemNaGravacaoTests(Base):
    """Origem preservada ao salvar (origem-preservada-07-11, incorporada neste lote), sem HTTP."""

    def test_salvar_do_cliente_preserva_a_origem_da_importacao(self):
        # prototipo.js salva só id, titulo e mensagens (role, content); a origem já gravada tem que sobreviver
        original = gravar_importado(self.dir)
        salvo = armazem._conversa_gravar({"id": ID_IMPORTADO, "titulo": "Renomeada",
                                          "mensagens": [{"role": "user", "content": "pergunta"},
                                                        {"role": "assistant", "content": "resposta"}]})
        self.assertEqual(salvo["id"], ID_IMPORTADO)
        gravado = json.loads((self.dir / (ID_IMPORTADO + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(gravado.get("id"), ID_IMPORTADO)
        for campo in ("origem", "origem_id", "titulo_original", "importado_em", "data_original"):
            self.assertEqual(gravado.get(campo), original[campo], campo)
        self.assertEqual(gravado["titulo"], "Renomeada")
        self.assertEqual([m.get("origem_id") for m in gravado["mensagens"]], ["m1", "m2"])
        self.assertEqual([m.get("criada") for m in gravado["mensagens"]], ["2026-11-01T09:00:00-03:00", "2026-11-01T09:01:00-03:00"])

    def test_salvar_com_origem_ja_presente_reusa_o_arquivo_sem_criar_outro(self):
        # a mesma conversa importada, vinda sem id, não pode virar um segundo arquivo
        gravar_importado(self.dir)
        salvo = armazem._conversa_gravar({"titulo": "[LibreChat] Importada", **ORIGEM_IMPORTADA,
                                          "mensagens": [{"role": "user", "content": "pergunta"}]})
        self.assertEqual(salvo["id"], ID_IMPORTADO)
        self.assertEqual(self.arquivos_de_conversa(), [ID_IMPORTADO + ".json"])

    def test_origem_do_arquivo_nao_e_reescrita_por_salvar(self):
        original = gravar_importado(self.dir)
        armazem._conversa_gravar({"id": ID_IMPORTADO, "titulo": "X", "origem": "outra", "origem_id": "outro-id",
                                  "mensagens": [{"role": "user", "content": "pergunta"}]})
        gravado = json.loads((self.dir / (ID_IMPORTADO + ".json")).read_text(encoding="utf-8"))
        self.assertEqual((gravado["origem"], gravado["origem_id"]), (original["origem"], original["origem_id"]))
        self.assertEqual(self.arquivos_de_conversa(), [ID_IMPORTADO + ".json"])

    def test_campos_de_origem_invalidos_saem_e_o_salvar_continua(self):
        sem_origem = armazem._conversa_gravar({"titulo": "T", "origem": 7, "origem_id": "x",
                                               "mensagens": [{"role": "user", "content": "oi"}]})
        self.assertIsNotNone(sem_origem)
        self.assertNotIn("origem", json.loads((self.dir / (sem_origem["id"] + ".json")).read_text(encoding="utf-8")))
        com_origem = armazem._conversa_gravar({"titulo": "T", "origem": "librechat", "origem_id": "x", "titulo_original": "y" * 600,
                                               "mensagens": [{"role": "user", "content": "oi"}]})
        gravado = json.loads((self.dir / (com_origem["id"] + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(gravado["origem"], "librechat")
        self.assertNotIn("titulo_original", gravado)

    def test_mensagem_alterada_perde_criada_e_as_que_continuam_mantem(self):
        gravar_importado(self.dir)
        armazem._conversa_gravar({"id": ID_IMPORTADO, "titulo": "X", "mensagens": [
            {"role": "user", "content": "pergunta"}, {"role": "assistant", "content": "outra resposta"}]})
        gravado = json.loads((self.dir / (ID_IMPORTADO + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(gravado["mensagens"][0].get("origem_id"), "m1")
        self.assertNotIn("origem_id", gravado["mensagens"][1], "texto mudou: a marca da mensagem não vale mais")


class RegistroTests(RotasBase):
    def test_registro_tem_so_hora_rota_id_e_status(self):
        corpo = {"id": id_de(1), "titulo": "segredo-titulo", "mensagens": [{"role": "user", "content": "segredo-texto"}]}
        self.assertEqual(self.post_json("/api/seth/conversa", corpo)[0], 200)
        organizar = {"id": id_de(1), "marcadores": ["segredo-marcador"]}
        self.assertEqual(self.post_json("/api/seth/conversa/organizar", organizar)[0], 200)
        self.assertEqual(self.post_json("/api/seth/conversa/apagar", {"id": id_de(1)})[0], 200)
        self.assertEqual(self.post_json("/api/seth/conversa/organizar", organizar, {"Content-Type": "application/json"})[0], 403)
        linhas = [json.loads(linha) for linha in (self.dir / REGISTRO).read_text(encoding="utf-8").splitlines()]
        self.assertEqual({tuple(sorted(linha)) for linha in linhas}, {("hora", "id", "rota", "status")})
        self.assertEqual([(l["rota"], l["status"]) for l in linhas], [
            ("/api/seth/conversa", 200), ("/api/seth/conversa/organizar", 200),
            ("/api/seth/conversa/apagar", 200), ("/api/seth/conversa/organizar", 403)])
        self.assertEqual([l["id"] for l in linhas], [id_de(1), id_de(1), id_de(1), None])
        bruto = (self.dir / REGISTRO).read_text(encoding="utf-8")
        for segredo in ("segredo-titulo", "segredo-texto", "segredo-marcador"):
            self.assertNotIn(segredo, bruto)
        self.assertTrue(all(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-03:00", l["hora"]) for l in linhas))

    def test_registro_so_acrescenta(self):
        corpo = {"titulo": "Um", "mensagens": [{"role": "user", "content": "oi"}]}
        self.post_json("/api/seth/conversa", corpo)
        antes = (self.dir / REGISTRO).read_bytes()
        self.post_json("/api/seth/conversa", corpo)
        depois = (self.dir / REGISTRO).read_bytes()
        self.assertTrue(depois.startswith(antes) and len(depois) > len(antes), "as linhas antigas ficam como estão")

    def test_registro_que_nao_pode_ser_escrito_nao_recusa_a_acao(self):
        (self.dir / REGISTRO).mkdir()  # o caminho do registro está ocupado por uma pasta: a linha não cabe
        corpo = {"titulo": "Salva mesmo assim", "mensagens": [{"role": "user", "content": "oi"}]}
        self.assertEqual(self.post_json("/api/seth/conversa", corpo)[0], 200)
        self.assertEqual(len(self.arquivos_de_conversa()), 1)


class LixeiraRotasTests(RotasBase):
    def test_apagar_listar_restaurar_e_purgar_pela_rota(self):
        self.conversa(1, "Pela rota")
        status, dados, _ = self.post_json("/api/seth/conversa/apagar", {"id": id_de(1)})
        self.assertEqual(status, 200)
        nome = json.loads(dados)["lixeira"]
        listado = json.loads(self.pede("GET", "/api/seth/lixeira")[1])
        self.assertEqual((listado["schema_version"], listado["items"][0]["nome"], listado["total"], listado["ilegiveis"]), (1, nome, 1, 0))
        status, dados, _ = self.post_json("/api/seth/lixeira/restaurar", {"nome": nome})
        self.assertEqual((status, json.loads(dados)["id"]), (200, id_de(1)))
        self.assertEqual(json.loads(self.pede("GET", "/api/seth/conversas")[1])["items"][0]["id"], id_de(1))
        status, dados, _ = self.post_json("/api/seth/conversa/apagar", {"id": id_de(1)})
        nome_novo = json.loads(dados)["lixeira"]
        status, dados, _ = self.post_json("/api/seth/lixeira/purgar", {"nome": nome_novo})
        self.assertEqual((status, json.loads(dados)), (200, {"purgada": True}))
        self.assertEqual(self.post_json("/api/seth/lixeira/purgar", {"nome": nome_novo})[0], 404)

    def test_rota_da_lixeira_recusa_nome_invalido_e_pedido_grande(self):
        status, texto, _ = self.post_json("/api/seth/lixeira/restaurar", {})
        self.assertEqual((status, texto), (400, b"item da lixeira inv\xc3\xa1lido"))
        self.assertEqual(self.post_json("/api/seth/lixeira/purgar", {"nome": "../x"})[0], 400)
        grande = b"{" + b" " * 4200 + b"}"
        self.assertEqual(self.pede("POST", "/api/seth/lixeira/purgar", grande, self.mesma_origem())[0], 413)

    def test_apagar_conversa_que_nao_existe_responde_404(self):
        status, dados, _ = self.post_json("/api/seth/conversa/apagar", {"id": id_de(9)})
        self.assertEqual((status, json.loads(dados)), (404, {"apagada": False}))


class IlegiveisTests(Base):
    def test_listagem_conta_arquivos_ilegiveis_sem_apagar(self):
        self.conversa(1, "Legível")
        quebrado = self.dir / (id_de(2) + ".json")
        quebrado.write_text("{quebrado", encoding="utf-8")
        nao_objeto = self.dir / (id_de(3) + ".json")
        nao_objeto.write_text("[1, 2]", encoding="utf-8")
        listado = armazem._conversas_listar()
        self.assertEqual((listado["total"], listado["ilegiveis"], [i["id"] for i in listado["items"]]), (1, 2, [id_de(1)]))
        self.assertTrue(quebrado.exists() and nao_objeto.exists(), "a listagem não apaga nem mexe no arquivo ilegível")

    def test_lixeira_conta_ilegiveis_sem_apagar(self):
        self.conversa(1)
        armazem._conversa_apagar(id_de(1))
        ruim = self.dir / LIXEIRA / f"{id_de(7)}-20260101-101010.json"
        ruim.write_text("x{", encoding="utf-8")
        listado = armazem._lixeira_listar()
        self.assertEqual((listado["total"], listado["ilegiveis"]), (1, 1))
        self.assertTrue(ruim.exists())

    def test_sem_arquivo_ilegivel_a_contagem_e_zero(self):
        self.conversa(1)
        self.assertEqual(armazem._conversas_listar()["ilegiveis"], 0)
        self.assertEqual(armazem._lixeira_listar()["ilegiveis"], 0)


if __name__ == "__main__":
    unittest.main()
