#!/usr/bin/env python3
"""Testes da capivara: registro de capacidades, perfil derivado, semeadura, uso real e Laya.

Dados fictícios, sem rede, sem tocar no registro real: tudo roda em pastas temporárias.
Rodar: python3 scripts/testar_capivara_capacidades.py   (ou capivara_capacidades.py --selftest)
"""
from __future__ import annotations

import atexit
import json
import os
import subprocess
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))
# Estado operacional em pasta temporária: os testes nunca tocam ~/.local/share/agata/capivara.
_ESTADO_TESTE = tempfile.mkdtemp(prefix="capivara-testes-")
atexit.register(shutil.rmtree, _ESTADO_TESTE, True)
os.environ["AGATA_CAPIVARA_ESTADO"] = _ESTADO_TESTE
import capivara_capacidades as cap  # noqa: E402
import capivara_perfis as perf  # noqa: E402
import pesquisar_modelos_gratuitos as pmg  # noqa: E402

LIDO = "2026-11-23 16:50 -0300"
DATA = "2026-11-23"
LAYA = cap.LAYA
FILAS = {"seth-rapido": ["gemini/gemini-2.5-flash", "zai/glm-4.7-flash"],
         "seth-codigo": ["mistral/codestral-latest", "ollama-local/qwen3.5-9b-64k:latest"]}
NEMOTRON = "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"


def omni_fake() -> dict:
    """Formato de /v1/models do OmniRoute (campos reais), com lixo que precisa ser ignorado."""
    return {"data": [
        {"id": "gemini/gemini-2.5-flash", "owned_by": "gemini", "root": "gemini-2.5-flash",
         "context_length": 1048576, "max_output_tokens": 65536,
         "input_modalities": ["text", "image"], "output_modalities": ["text"],
         "capabilities": {"tool_calling": True, "reasoning": False}},
        {"id": "zai/glm-4.7-flash", "owned_by": "zai", "root": "glm-4.7-flash",
         "capabilities": {"tool_calling": True, "reasoning": True}},
        {"id": NEMOTRON, "owned_by": "openrouter", "root": "nvidia/nemotron-3-ultra-550b-a55b:free",
         "context_length": 1000000, "max_output_tokens": 65536, "free": True,
         "capabilities": {"tool_calling": True, "reasoning": True}},
        {"id": "auto/best-coding", "owned_by": "combo", "root": "auto/best-coding",
         "context_length": 1048576, "max_output_tokens": 384000, "capabilities": {"tool_calling": True}},
        {"id": "mistral/codestral-latest", "owned_by": "mistral", "root": "codestral-latest",
         "max_input_tokens": 256000, "capabilities": {"tool_calling": False}},
        {"id": "ollama-local/qwen3.5-9b-64k:latest", "owned_by": "ollama-local", "root": "qwen3.5",
         "capabilities": {"tool_calling": True}},
        {"id": "sem-id", "owned_by": "x"},
        "lixo", None,
    ]}


def cand_fake() -> list:
    """Itens do catalogo.json. O texto do erro de acesso é um marcador: não pode aparecer no registro."""
    return [
        {"id": "huggingface/acme/modelo-x", "provedor": "huggingface", "nome": "modelo-x",
         "capacidades": ["chat"], "contexto": "não documentado nesta coleta",
         "acesso_verificado": {"status": 404, "data": "2026-11-18 15:05", "latencia_s": 0.4,
                               "erro": "TEXTO-DE-ERRO-QUE-NAO-PODE-SAIR"},
         "estado": "indisponivel", "fonte": "https://huggingface.co/api/models (18/11/2026)"},
        {"id": "nvidia/bigcode/starcoder2-15b", "provedor": "nvidia", "nome": "starcoder2-15b",
         "capacidades": ["codigo"], "acesso_verificado": "não verificado",
         "estado": "candidato_prova", "fonte": "https://integrate.api.nvidia.com/v1/models (leitura 18/11/2026)"},
    ]


def docs_fake() -> dict:
    return {"mistral/codestral-latest": {"janela": 128000, "saida_max": None,
                                         "fonte": "https://docs.mistral.ai/x — \"Contexte 128k\" (lido em 13/10/2026)"},
            "gemini/gemini-3.5-flash-lite": {"janela": 1048576, "saida_max": 65536,
                                             "fonte": "https://ai.google.dev/y (lido em 13/10/2026)"}}


def openrouter_fake() -> dict:
    return {"data": [
        {"id": "nvidia/nemotron-3-ultra-550b-a55b:free", "context_length": 1000000,
         "top_provider": {"context_length": 1000000, "max_completion_tokens": 65536},
         "supported_parameters": ["tools", "reasoning", "temperature"]},
        {"id": "z/pago", "context_length": None, "top_provider": None, "supported_parameters": ["temperature"]},
        {"id": 7}, "lixo",
    ]}


def nvidia_fake() -> dict:
    return {"object": "list", "data": [
        {"id": "nvidia/llama-3.1-nemotron-safety-guard-8b-v3", "object": "model"},
        {"id": "bigcode/starcoder2-15b", "object": "model"},
        {"id": "x", "object": "model", "context_window": 128000, "supports_tools": True, "supports_thinking": False},
    ]}


def mapa(dados: dict) -> dict:
    return {m["id"]: m for m in dados["data"] if isinstance(m, dict) and m.get("id")}


def montar_fake(anterior=None, dados=None, docs=None, cand=None, ollama=None) -> dict:
    omni = mapa(dados if dados is not None else omni_fake())
    return cap.montar(FILAS, omni, cand if cand is not None else cand_fake(),
                      docs if docs is not None else docs_fake(), ollama or {}, anterior or {}, LIDO)


def linha(ts="2026-11-23T10:00:00-03:00", modelo="gemini/gemini-2.5-flash", tipo="conversa",
          status=200, bloqueado=False, latencia=100, **extra) -> str:
    return json.dumps({"ts": ts, "modelo": modelo, "tipo": tipo, "status": status, "bloqueado": bloqueado,
                       "latencia_ms": latencia, **extra}, ensure_ascii=False)


class _Tmp(unittest.TestCase):
    def pasta(self) -> Path:
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        return Path(d.name)


class AfirmacoesTest(unittest.TestCase):
    def test_omniroute_so_o_que_vem(self):
        af = cap.afirma_omniroute(omni_fake(), DATA)
        g = af["gemini/gemini-2.5-flash"]
        self.assertEqual([c["valor"] for c in g["janela"]], [1048576])
        self.assertEqual([c["valor"] for c in g["saida_max"]], [65536])
        self.assertEqual(g["ferramentas"][0]["valor"], True)
        self.assertEqual(g["raciocinio"][0]["valor"], False)  # falso explícito vale: a fonte disse não
        z = af["zai/glm-4.7-flash"]
        self.assertNotIn("janela", z)   # sem context_length: nenhum número inventado
        self.assertNotIn("saida_max", z)
        self.assertEqual(af["mistral/codestral-latest"]["janela"][0]["valor"], 256000)  # cai para max_input_tokens

    def test_omniroute_cada_afirmacao_tem_fonte_e_data(self):
        af = cap.afirma_omniroute(omni_fake(), DATA)
        for campos in af.values():
            for lista in campos.values():
                for c in lista:
                    self.assertEqual(c["origem"], "omniroute")
                    self.assertTrue(c["fonte"].startswith("omniroute GET /v1/models"))
                    self.assertEqual(c["data"], DATA)

    def test_omniroute_forma_invalida_levanta(self):
        with self.assertRaises(ValueError):
            cap.afirma_omniroute([{"id": "a"}], DATA)
        with self.assertRaises(ValueError):
            cap.afirma_omniroute({"x": 1}, DATA)

    def test_openrouter_formato_real(self):
        af = cap.afirma_openrouter(openrouter_fake(), DATA)
        n = af[NEMOTRON]
        self.assertEqual(n["janela"][0]["valor"], 1000000)
        self.assertEqual(n["saida_max"][0]["valor"], 65536)
        self.assertTrue(n["ferramentas"][0]["valor"])
        self.assertTrue(n["raciocinio"][0]["valor"])
        self.assertEqual(n["janela"][0]["fonte"], "https://openrouter.ai/api/v1/models")
        self.assertEqual(n["janela"][0]["data"], DATA)

    def test_openrouter_sem_dado_sem_afirmacao(self):
        af = cap.afirma_openrouter(openrouter_fake(), DATA)
        self.assertNotIn("openrouter/z/pago", af)  # nada a afirmar: não aparece, não vira falso
        self.assertNotIn("openrouter/7", af)

    def test_openrouter_so_afirma_positivo(self):
        dados = {"data": [{"id": "a/b", "supported_parameters": ["temperature"]}]}
        self.assertNotIn("ferramentas", cap.afirma_openrouter(dados, DATA).get("openrouter/a/b", {}))

    def test_openrouter_forma_invalida_levanta(self):
        with self.assertRaises(ValueError):
            cap.afirma_openrouter({"data": None}, DATA)
        with self.assertRaises(ValueError):
            cap.afirma_openrouter(["x"], DATA)

    def test_nvidia_prefixo_e_campos_extras(self):
        af = cap.afirma_nvidia(nvidia_fake(), DATA)
        self.assertTrue(af["nvidia/nvidia/llama-3.1-nemotron-safety-guard-8b-v3"]["listado"][0]["valor"])
        self.assertIn("nvidia/bigcode/starcoder2-15b", af)
        x = af["nvidia/x"]
        self.assertEqual(x["janela"][0]["valor"], 128000)
        self.assertTrue(x["ferramentas"][0]["valor"])
        self.assertFalse(x["raciocinio"][0]["valor"])
        self.assertNotIn("janela", af["nvidia/bigcode/starcoder2-15b"])

    def test_documentacao_data_do_texto(self):
        af = cap.afirma_documentacao(docs_fake())
        c = af["mistral/codestral-latest"]["janela"][0]
        self.assertEqual((c["origem"], c["valor"], c["data"]), ("documentacao", 128000, "2026-10-13"))
        self.assertIn("lido em", c["fonte"])

    def test_ollama_sem_num_ctx_nao_afirma(self):
        self.assertEqual(cap.afirma_ollama("ollama-local/x", None, DATA), {})
        self.assertEqual(cap.afirma_ollama("ollama-local/x", 65536, DATA)["ollama-local/x"]["janela"][0]["valor"], 65536)


class MontarTest(_Tmp):
    def test_cobertura_e_uniao_sem_repetir(self):
        reg = montar_fake()
        esperado = set(mapa(omni_fake())) | {c["id"] for c in cand_fake()} | {m for o in FILAS.values() for m in o}
        self.assertEqual(set(reg["modelos"]), esperado)
        self.assertEqual(cap.conferir(reg), [])

    def test_candidato_sem_omniroute_fica_vazio_e_com_fonte(self):
        e = montar_fake()["modelos"]["huggingface/acme/modelo-x"]
        self.assertIsNone(e["janela"])
        self.assertIsNone(e["saida_max"])
        self.assertEqual(e["fonte"], "nao_medido")
        self.assertIsNone(e["declarado"])
        self.assertEqual((e["medido"], e["observado"]), ([], []))
        self.assertIn("catalogo-modelos", e["catalogo"]["fonte"])
        self.assertEqual(e["catalogo"]["catalogo_modelos"]["estado"], "indisponivel")

    def test_texto_de_erro_nao_entra_no_registro(self):
        self.assertNotIn("TEXTO-DE-ERRO", json.dumps(montar_fake(), ensure_ascii=False))

    def test_sem_janela_mas_com_capacidade_fica_nao_medido(self):
        e = montar_fake()["modelos"]["zai/glm-4.7-flash"]
        self.assertIsNone(e["janela"])
        self.assertEqual(e["fonte"], "nao_medido")
        self.assertTrue(e["declarado"]["ferramentas"])   # a capacidade vem da fonte; a janela não

    def test_janela_com_fonte_do_omniroute(self):
        e = montar_fake()["modelos"]["gemini/gemini-2.5-flash"]
        self.assertEqual((e["janela"], e["saida_max"], e["fonte"]), (1048576, 65536, "omniroute /v1/models"))
        self.assertEqual(e["declarado"]["claims"]["janela"][0]["origem"], "omniroute")

    def test_divergencia_mantem_a_precedencia_e_marca(self):
        e = montar_fake()["modelos"]["mistral/codestral-latest"]
        self.assertEqual(e["janela"], 256000)            # omniroute vence a documentação
        self.assertEqual(e["fonte"], "omniroute /v1/models")
        self.assertIn("janela", e["declarado"]["divergente"])

    def test_numero_so_com_afirmacao(self):
        reg = montar_fake(ollama={"ollama-local/qwen3.5-9b-64k:latest": 65536})
        for m, e in reg["modelos"].items():
            if e["janela"] is not None:
                vals = [c["valor"] for c in e["declarado"]["claims"]["janela"]]
                self.assertIn(e["janela"], vals, m)
            else:
                self.assertEqual(e["fonte"], "nao_medido", m)
        self.assertEqual(reg["modelos"]["ollama-local/qwen3.5-9b-64k:latest"]["janela"], 65536)

    def test_conferir_recusa_numero_sem_fonte(self):
        reg = json.loads(json.dumps(montar_fake()))
        reg["modelos"]["gemini/gemini-2.5-flash"]["janela"] = 999
        self.assertTrue(any("não bate" in x for x in cap.conferir(reg)))

    def test_conferir_recusa_afirmacao_sem_data(self):
        reg = json.loads(json.dumps(montar_fake()))
        reg["modelos"]["gemini/gemini-2.5-flash"]["declarado"]["claims"]["janela"][0]["data"] = None
        self.assertTrue(any("falta data" in x for x in cap.conferir(reg)))

    def test_conferir_recusa_origem_nao_autorizada(self):
        reg = json.loads(json.dumps(montar_fake()))
        reg["modelos"]["gemini/gemini-2.5-flash"]["declarado"]["claims"]["listado"] = [
            {"origem": "omniroute", "fonte": "x", "data": DATA, "valor": True}]
        self.assertTrue(any("não pode afirmar" in x for x in cap.conferir(reg)))

    def test_medido_e_observado_sao_preservados(self):
        r1 = montar_fake()
        r1["modelos"]["gemini/gemini-2.5-flash"]["medido"] = [{"metrica": "taxa_erro", "valor": 0.1, "protocolo": "p",
                                                              "amostra": 5, "provedor": "gemini",
                                                              "endpoint": "gemini/gemini-2.5-flash",
                                                              "versao_resolvida": "v", "data": DATA}]
        r2 = montar_fake(anterior=r1)
        self.assertEqual(r2["modelos"]["gemini/gemini-2.5-flash"]["medido"], r1["modelos"]["gemini/gemini-2.5-flash"]["medido"])

    def test_migra_catalogo_antigo_sem_apagar_a_janela(self):
        """Registro de antes desta versão: janela só em `catalogo`, com a data da leitura. A primeira
        montagem nova transforma isso em afirmação do OmniRoute com essa data, e não apaga."""
        nm = "openrouter/cohere/north-mini-code:free"
        anterior = {"modelos": {nm: {"catalogo": {"janela": 256000, "saida_max": 64000,
                                                  "lido_em": "2026-11-17 08:41 -0300",
                                                  "fonte": "omniroute /v1/models"},
                                     "declarado": None, "medido": [], "observado": []}}}
        reg = cap.montar({"seth-codigo": [nm]}, {}, [], {}, {}, anterior, LIDO)
        e = reg["modelos"][nm]
        self.assertEqual((e["janela"], e["saida_max"], e["fonte"]), (256000, 64000, "omniroute /v1/models"))
        c = e["declarado"]["claims"]["janela"][0]
        self.assertEqual((c["origem"], c["data"]), ("omniroute", "2026-11-17"))
        self.assertEqual(cap.conferir(reg), [])

    def test_migracao_nao_duplica_quando_omniroute_ja_afirma(self):
        nm = "openrouter/cohere/north-mini-code:free"
        anterior = {"modelos": {nm: {"catalogo": {"janela": 256000, "lido_em": "2026-11-17 08:41 -0300"},
                                     "declarado": None, "medido": [], "observado": []}}}
        dados = {"data": [{"id": nm, "owned_by": "openrouter", "context_length": 300000, "capabilities": {}}]}
        reg = cap.montar({"seth-codigo": [nm]}, mapa(dados), [], {}, {}, anterior, LIDO)
        claims = reg["modelos"][nm]["declarado"]["claims"]["janela"]
        self.assertEqual([c["valor"] for c in claims if c["origem"] == "omniroute"], [300000])
        self.assertEqual(reg["modelos"][nm]["janela"], 300000)

    def test_afirmacao_de_fonte_que_sumiu_fica_com_a_data(self):
        r1 = montar_fake()
        cap.aplicar(r1["modelos"], cap.afirma_openrouter(openrouter_fake(), "2026-11-10"))
        r2 = montar_fake(anterior=r1)  # sem openrouter nesta montagem
        claims = r2["modelos"][NEMOTRON]["declarado"]["claims"]["janela"]
        self.assertIn(("openrouter", "2026-11-10"), [(c["origem"], c["data"]) for c in claims])
        self.assertEqual(r2["modelos"][NEMOTRON]["janela"], 1000000)

    def test_afirmacao_nova_substitui_a_da_mesma_origem(self):
        r1 = montar_fake()
        dados = omni_fake()
        dados["data"][0]["context_length"] = 2000000
        r2 = montar_fake(anterior=r1, dados=dados)
        claims = r2["modelos"]["gemini/gemini-2.5-flash"]["declarado"]["claims"]["janela"]
        self.assertEqual([c["valor"] for c in claims if c["origem"] == "omniroute"], [2000000])
        self.assertEqual(r2["modelos"]["gemini/gemini-2.5-flash"]["janela"], 2000000)

    def test_fora_da_cobertura_so_com_medicao(self):
        anterior = {"modelos": {"velho/w": {"medido": [{"metrica": "m"}]}, "velho/v": {}}}
        reg = montar_fake(anterior=anterior)
        self.assertTrue(reg["modelos"]["velho/w"]["fora_da_cobertura"])
        self.assertNotIn("velho/v", reg["modelos"])

    def test_declarado_antigo_sem_claims_nao_vira_numero(self):
        anterior = {"modelos": {"mistral/codestral-latest": {"declarado": {"fonte": "x", "janela": 999999}}}}
        reg = montar_fake(anterior=anterior)
        self.assertEqual(reg["modelos"]["mistral/codestral-latest"]["janela"], 256000)
        self.assertEqual(cap.conferir(reg), [])

    def test_uso_posicao_e_preservada(self):
        pos = {"inode": 1, "offset": 10, "janela_sha": "a" * 64, "tamanho": 10}
        reg = montar_fake(anterior={"uso_posicao": pos})
        self.assertEqual(reg["uso_posicao"], pos)


class PerfisTest(unittest.TestCase):
    def test_perfil_derivado_tem_o_formato_do_gateway(self):
        p = perf.derivar(montar_fake())
        self.assertEqual(set(p["modelos"]), {m for o in FILAS.values() for m in o})
        for d in p["modelos"].values():
            self.assertEqual(set(d), {"janela", "saida_max", "fonte"})
        self.assertEqual(p["medido_em"], DATA)
        self.assertEqual(p["filas"], FILAS)
        self.assertEqual(p["modelos"]["gemini/gemini-2.5-flash"]["fonte"], "omniroute /v1/models")

    def test_zai_sem_janela_continua_32768(self):
        p = perf.derivar(montar_fake())
        self.assertIsNone(p["modelos"]["zai/glm-4.7-flash"]["janela"])  # sem número no perfil: o 32768 é regra do cálculo
        self.assertEqual(perf.janela(p, "zai/glm-4.7-flash"), perf.JANELA_DESCONHECIDA)
        self.assertEqual(perf.JANELA_DESCONHECIDA, 32768)
        self.assertEqual(p["modelos"]["zai/glm-4.7-flash"]["fonte"], "nao_medido")
        self.assertEqual(perf.limiar_tokens(p, "seth-rapido"), 32768 - perf.RESERVA_SAIDA)

    def test_fila_longa_usa_o_registro(self):
        p = perf.derivar(montar_fake())
        self.assertEqual(perf.fila_longa(p, "seth-rapido"), ["gemini/gemini-2.5-flash"])


class UsoTest(_Tmp):
    """Incorporação do uso.jsonl por POSIÇÃO no arquivo (não por ts): idempotente, sem perder linha do mesmo
    segundo, e com a falha (status nulo ou != 200) contando como taxa 0."""

    def setUp(self):
        self.arq = self.pasta() / "uso.jsonl"
        self.reg = montar_fake()

    def anexar(self, *linhas_txt):
        with self.arq.open("a", encoding="utf-8") as f:
            for txt in linhas_txt:
                f.write(txt + "\n")

    def incorporar(self):
        return cap.incorporar_arquivo(self.reg, self.arq)

    def _registros(self, modelo, tipo=None):
        return [x for x in self.reg["modelos"][modelo]["observado"] if tipo is None or x.get("tipo") == tipo]

    def test_agrega_por_modelo_e_tipo(self):
        self.anexar(linha(ts="2026-11-23T10:00:00-03:00", latencia=100),
                    linha(ts="2026-11-23T10:01:00-03:00", latencia=200),
                    linha(ts="2026-11-23T10:02:00-03:00", status=500, latencia=300),
                    linha(ts="2026-11-23T10:03:00-03:00", bloqueado=True, latencia=400),
                    linha(ts="2026-11-23T10:04:00-03:00", tipo="codigo", latencia=50))
        st = self.incorporar()
        self.assertEqual((st["novas"], st["malformadas"]), (5, 0))
        conv = self._registros("gemini/gemini-2.5-flash", "conversa")
        self.assertEqual(len(conv), 1)
        r = conv[0]
        self.assertEqual((r["metrica"], r["amostra"], r["valor"], r["falhas"]), ("taxa_ok", 4, 0.5, 2))
        self.assertEqual(r["latencia_media_ms"], 250)
        self.assertEqual((r["desde"], r["ate"]), ("2026-11-23T10:00:00-03:00", "2026-11-23T10:03:00-03:00"))
        self.assertEqual((r["provedor"], r["endpoint"], r["data"]), ("gemini", "gemini/gemini-2.5-flash", DATA))
        self.assertEqual(len(self._registros("gemini/gemini-2.5-flash", "codigo")), 1)
        self.assertEqual(cap.conferir(self.reg), [])

    def test_idempotente_rodar_de_novo_nao_duplica(self):
        self.anexar(linha(), linha(ts="2026-11-23T10:05:00-03:00", status=500))
        self.incorporar()
        antes = json.dumps(self.reg, sort_keys=True)
        st2 = self.incorporar()
        self.assertEqual((st2["novas"], st2["registros"]), (0, 0))
        self.assertEqual(json.dumps(self.reg, sort_keys=True), antes)

    def test_linha_do_mesmo_segundo_do_corte_nao_se_perde(self):
        """Regressão: com a marca antiga (uso_ate, resolução de segundo), uma linha de ts igual ao corte, gravada
        depois da leitura, era descartada. Aqui as duas linhas têm o mesmo timestamp de segundo inteiro."""
        self.anexar(linha(ts="2026-11-23T10:00:00-03:00"))
        self.incorporar()
        self.anexar(linha(ts="2026-11-23T10:00:00-03:00", status=500))
        st = self.incorporar()
        self.assertEqual(st["novas"], 1)
        conv = self._registros("gemini/gemini-2.5-flash", "conversa")
        self.assertEqual(sum(r["amostra"] for r in conv), 2)

    def test_linha_parcial_so_entra_quando_completa(self):
        l1 = linha(ts="2026-11-23T10:00:00-03:00")
        l2 = linha(ts="2026-11-23T10:01:00-03:00", status=500)
        with self.arq.open("w", encoding="utf-8") as f:
            f.write(l1 + "\n" + l2[:25])  # gravação em andamento: sem \n no fim
        st = self.incorporar()
        self.assertEqual((st["novas"], st["malformadas"]), (1, 0))
        with self.arq.open("a", encoding="utf-8") as f:
            f.write(l2[25:] + "\n")
        st = self.incorporar()
        self.assertEqual((st["novas"], st["malformadas"]), (1, 0))
        conv = self._registros("gemini/gemini-2.5-flash", "conversa")
        self.assertEqual(sum(r["amostra"] for r in conv), 2)

    def test_arquivo_encolheu_recomeca_do_zero(self):
        self.anexar(linha(), linha(ts="2026-11-23T10:01:00-03:00"), linha(ts="2026-11-23T10:02:00-03:00"))
        self.incorporar()
        self.arq.write_text(linha(ts="2026-11-23T11:00:00-03:00") + "\n", encoding="utf-8")  # mesmo inode, menor
        st = self.incorporar()
        self.assertEqual(st["novas"], 1)
        conv = self._registros("gemini/gemini-2.5-flash", "conversa")
        self.assertEqual(sum(r["amostra"] for r in conv), 3 + 1)

    def test_arquivo_trocado_recomeca_do_zero(self):
        self.anexar(linha(), linha(ts="2026-11-23T10:01:00-03:00"))
        self.incorporar()
        novo = self.arq.parent / "novo.jsonl"
        novo.write_text("".join(linha(ts=f"2026-11-23T12:0{i}:00-03:00") + "\n" for i in range(3)), encoding="utf-8")
        os.replace(novo, self.arq)  # outro inode
        st = self.incorporar()
        self.assertEqual(st["novas"], 3)

    def test_trecho_ja_lido_reescrito_recomeca(self):
        self.anexar(linha(latencia=100), linha(ts="2026-11-23T10:01:00-03:00", latencia=200))
        self.incorporar()
        dados = self.arq.read_bytes()
        self.assertEqual(dados.count(b'"latencia_ms": 200'), 1)
        self.arq.write_bytes(dados.replace(b'"latencia_ms": 200', b'"latencia_ms": 900'))  # mesmo tamanho e inode
        st = self.incorporar()
        self.assertEqual(st["novas"], 2)  # o que já foi lido mudou: relê tudo

    def test_malformada_conta_uma_vez(self):
        self.anexar("{ruim", linha())
        st = self.incorporar()
        self.assertEqual((st["novas"], st["malformadas"]), (1, 1))
        st2 = self.incorporar()
        self.assertEqual((st2["novas"], st2["malformadas"]), (0, 0))

    def test_linha_malformada_e_ignorada(self):
        arq = self.pasta() / "uso.jsonl"
        arq.write_text("\n".join([
            linha(),
            "{ruim",
            json.dumps({"ts": "2026-11-23T10:00:00-03:00", "modelo": "g/x", "tipo": "conversa",
                        "status": 200, "latencia_ms": 5}),
            linha(tipo="invento"),
            linha(ts="2026-11-23T10:00:00"),
            linha(bloqueado="sim"),
            linha(latencia=-5),
            linha(status="200"),
            "[1, 2]",
            "",
        ]) + "\n", encoding="utf-8")
        linhas, mal = cap.ler_uso(arq)
        self.assertEqual((len(linhas), mal), (1, 8))

    def test_status_nulo_e_falha_sem_resposta_contam_como_falha(self):
        self.anexar(linha(status=None, latencia=None),
                    linha(ts="2026-11-23T10:01:00-03:00", status=500, latencia=300),
                    linha(ts="2026-11-23T10:02:00-03:00", status=200, latencia=100))
        st = self.incorporar()
        self.assertEqual((st["novas"], st["malformadas"]), (3, 0))
        (r,) = self._registros("gemini/gemini-2.5-flash", "conversa")
        self.assertEqual((r["amostra"], r["valor"], r["falhas"]), (3, 0.3333, 2))
        self.assertEqual(r["latencia_media_ms"], 200)  # mediana de 300 e 100; a linha sem latência fica fora

    def test_latencia_nula_fica_fora_da_mediana_mas_conta_na_taxa(self):
        self.anexar(linha(latencia=None), linha(ts="2026-11-23T10:01:00-03:00", latencia=300))
        self.incorporar()
        (r,) = self._registros("gemini/gemini-2.5-flash", "conversa")
        self.assertEqual((r["amostra"], r["valor"], r["latencia_media_ms"]), (2, 1.0, 300))

    def test_nunca_le_campo_de_texto(self):
        self.anexar(linha(texto="PALAVRA-SECRETA-9X", prompt="PROMPT-SECRETO-7Z",
                          resposta="RESPOSTA-SECRETA-3W", classe="interno"))
        self.incorporar()
        blob = json.dumps(self.reg, ensure_ascii=False)
        for segredo in ("PALAVRA-SECRETA-9X", "PROMPT-SECRETO-7Z", "RESPOSTA-SECRETA-3W"):
            self.assertNotIn(segredo, blob)
        linhas, _ = cap.ler_uso(self.arq)
        self.assertEqual(set(linhas[0]), {"ts", "modelo", "tipo", "status", "bloqueado", "latencia_ms",
                                          "rota", "rota_por", "laya_confianca", "achados", "refeito", "corrigido"})

    def test_arquivo_ausente_nao_faz_nada(self):
        self.assertEqual(cap.ler_uso(Path("/nao/existe/uso.jsonl")), ([], 0))
        antes = json.dumps(self.reg, sort_keys=True)
        st = cap.incorporar_arquivo(self.reg, self.pasta() / "nao-existe.jsonl")
        self.assertEqual(st["novas"], 0)
        self.assertEqual(json.dumps(self.reg, sort_keys=True), antes)

    def test_modelo_fora_do_inventario_entra_marcado(self):
        self.anexar(linha(modelo="groq/novo"))
        self.incorporar()
        e = self.reg["modelos"]["groq/novo"]
        self.assertTrue(e["fora_da_cobertura"])
        self.assertEqual((e["fonte"], e["janela"], len(e["observado"])), ("nao_medido", None, 1))

    def test_posicao_gravada_e_valida(self):
        self.anexar(linha())
        self.incorporar()
        self.assertEqual(self.reg["uso_posicao"]["offset"], self.arq.stat().st_size)
        self.assertEqual(cap.conferir(self.reg), [])
        self.reg["uso_posicao"] = {"inode": "x"}
        self.assertTrue(any("uso_posicao inválida" in e for e in cap.conferir(self.reg)))


class LayaTest(_Tmp):
    """Perfil do roteador Laya: por rota, taxa_ok quando a rota veio do Laya e quando veio da regra,
    e a média de laya_confianca. Dados fictícios."""

    def setUp(self):
        self.reg = montar_fake()
        arq = self.pasta() / "uso.jsonl"
        m = "gemini/gemini-2.5-flash"
        linhas = [
            linha(ts="2026-11-23T10:00:00-03:00", modelo=m, rota="rapido", rota_por="laya", laya_confianca=0.8),
            linha(ts="2026-11-23T10:01:00-03:00", modelo=m, rota="rapido", rota_por="laya", laya_confianca=0.4),
            linha(ts="2026-11-23T10:02:00-03:00", modelo=m, status=500, rota="rapido", rota_por="laya", laya_confianca=0.6),
            linha(ts="2026-11-23T10:03:00-03:00", modelo=m, rota="rapido", rota_por="laya", laya_confianca=1.7),
            linha(ts="2026-11-23T10:04:00-03:00", modelo=m, rota="rapido", rota_por="regra"),
            linha(ts="2026-11-23T10:05:00-03:00", modelo=m, rota="livre", rota_por="laya", laya_confianca=0.5),
            linha(ts="2026-11-23T10:06:00-03:00", modelo=m, rota="rapido", rota_por="bot"),      # por inválido
            linha(ts="2026-11-23T10:07:00-03:00", modelo=m, rota="pesado"),                      # sem quem decidiu
            linha(ts="2026-11-23T10:08:00-03:00", modelo=m),                                     # sem rota
        ]
        arq.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        self.st = cap.incorporar_arquivo(self.reg, arq)
        self.mal = self.st["malformadas"]
        self.laya = self.reg["modelos"][LAYA]["observado"]

    def _achar(self, **kw):
        return [x for x in self.laya if all(x.get(k) == v for k, v in kw.items())]

    def test_taxa_quando_veio_do_laya_e_quando_veio_da_regra(self):
        (laya_r,) = self._achar(metrica="taxa_ok", rota="rapido", rota_por="laya")
        self.assertEqual((laya_r["amostra"], laya_r["valor"]), (4, 0.75))
        (regra_r,) = self._achar(metrica="taxa_ok", rota="rapido", rota_por="regra")
        self.assertEqual((regra_r["amostra"], regra_r["valor"]), (1, 1.0))

    def test_media_de_confianca_por_rota_ignora_valor_invalido(self):
        (conf,) = self._achar(metrica="laya_confianca_media", rota="rapido")
        self.assertEqual((conf["amostra"], conf["valor"]), (3, 0.6))
        (conf_l,) = self._achar(metrica="laya_confianca_media", rota="livre")
        self.assertEqual((conf_l["amostra"], conf_l["valor"]), (1, 0.5))

    def test_linha_sem_quem_decidiu_ou_com_valor_invalido_fica_de_fora(self):
        self.assertEqual(self._achar(rota="pesado"), [])
        total_laya = sum(x["amostra"] for x in self.laya if x["metrica"] == "taxa_ok")
        self.assertEqual(total_laya, 4 + 1 + 1)  # rapido/laya, rapido/regra, livre/laya; não entram bot nem sem-quem

    def test_modelo_continua_contado_no_uso_geral(self):
        geral = [x for x in self.reg["modelos"]["gemini/gemini-2.5-flash"]["observado"] if x.get("tipo") == "conversa"]
        self.assertEqual(sum(x["amostra"] for x in geral), 9)  # as 9 linhas de conversa, válidas ou não para o Laya

    def test_entrada_do_laya_e_roteador_sem_janela(self):
        e = self.reg["modelos"][LAYA]
        self.assertTrue(e["fora_da_cobertura"])
        self.assertIsNone(e["janela"])
        self.assertEqual(e["fonte"], "nao_medido")
        self.assertEqual(cap.conferir(self.reg), [])

    def test_registros_do_laya_tem_proveniencia(self):
        for x in self.laya:
            for p in cap.PROVENIENCIA:
                self.assertIn(p, x)
            self.assertEqual(x["provedor"], "laya")
            self.assertEqual(x["endpoint"], LAYA)

    def test_sem_linha_de_rota_nao_cria_a_entrada(self):
        reg = montar_fake()
        arq = self.pasta() / "u.jsonl"
        arq.write_text(linha() + "\n", encoding="utf-8")
        cap.incorporar_arquivo(reg, arq)
        self.assertNotIn(LAYA, reg["modelos"])


class MedidoTest(unittest.TestCase):
    def test_incorporar_medido_qualidade_por_tipo_sem_duplicar(self):
        reg = montar_fake()
        med = {"metrica": "taxa_erro", "valor": 0.0, "protocolo": "p1", "amostra": 30, "provedor": "gemini",
               "endpoint": "gemini/gemini-2.5-flash", "versao_resolvida": "x-2026", "data": "2026-10-23"}
        res = {"gemini/gemini-2.5-flash": {"medido": [med]}}
        rots = [{"rodada": "R1", "modelo": "gemini/gemini-2.5-flash", "item": "cod-01", "rotulo": "boa"},
                {"rodada": "R1", "modelo": "gemini/gemini-2.5-flash", "item": "cod-02", "rotulo": "parcial"},
                {"rodada": "R1", "modelo": "gemini/gemini-2.5-flash", "item": "fer-01", "rotulo": "ruim_grave"},
                {"rodada": "R2", "modelo": "gemini/gemini-2.5-flash", "item": "cod-03", "rotulo": "ruim"}]
        n1 = cap.incorporar(reg, "R1", res, rots)
        n2 = cap.incorporar(reg, "R1", res, rots)
        med2 = {x["metrica"]: x for x in reg["modelos"]["gemini/gemini-2.5-flash"]["medido"]}
        self.assertEqual(med2["qualidade_codigo"]["valor"], 0.75)
        self.assertEqual(med2["qualidade_codigo"]["amostra"], 2)
        self.assertEqual(med2["qualidade_ferramenta"]["valor"], 0.0)
        self.assertTrue(n1 > 0 and n2 == 0)
        self.assertEqual(cap.conferir(reg), [])


class CliTest(_Tmp):
    """Roda o subcomando de verdade, numa cópia pequena do repositório (o registro real não é tocado)."""

    def _raiz(self):
        raiz = self.pasta()
        (raiz / "scripts").mkdir()
        (raiz / "config" / "capivara").mkdir(parents=True)
        shutil.copy(AQUI / "capivara_capacidades.py", raiz / "scripts" / "capivara_capacidades.py")
        cap.gravar(montar_fake(), raiz / "config" / "capivara" / "capacidades.json")
        return raiz

    def _rodar(self, raiz, *args):
        env = {**os.environ, "AGATA_CAPIVARA_ESTADO": str(raiz / "estado")}
        return subprocess.run([sys.executable, "-I", str(raiz / "scripts" / "capivara_capacidades.py"), *args],
                              capture_output=True, text=True, timeout=60, env=env)

    def test_incorporar_uso_grava_no_estado_e_e_idempotente(self):
        raiz = self._raiz()
        retrato = raiz / "config" / "capivara" / "capacidades.json"
        antes_retrato = retrato.read_text(encoding="utf-8")
        uso = raiz / "uso.jsonl"
        uso.write_text(linha() + "\n" + linha(ts="2026-11-23T10:05:00-03:00", rota="rapido", rota_por="laya") + "\n",
                       encoding="utf-8")
        r1 = self._rodar(raiz, "--incorporar-uso", str(uso))
        self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
        estado = raiz / "estado" / "capacidades.json"
        self.assertIn(LAYA, cap.carregar(estado)["modelos"])
        self.assertEqual(retrato.read_text(encoding="utf-8"), antes_retrato, "uso é operacional: não mexe no retrato")
        tamanho = estado.read_text(encoding="utf-8")
        r2 = self._rodar(raiz, "--incorporar-uso", str(uso))
        self.assertEqual(r2.returncode, 0)
        self.assertIn("novas 0", r2.stdout)
        self.assertEqual(estado.read_text(encoding="utf-8"), tamanho)

    def test_incorporar_uso_sem_arquivo_sai_zero(self):
        raiz = self._raiz()
        r = self._rodar(raiz, "--incorporar-uso", str(raiz / "nao-existe.jsonl"))
        self.assertEqual(r.returncode, 0)
        self.assertIn("sem arquivo de uso", r.stdout)


class PesquisarEtapaTest(_Tmp):
    """Semeadura semanal (pesquisar_modelos_gratuitos.py), com as fontes injetadas e sem rede."""

    def setUp(self):
        p1 = mock.patch.object(pmg, "ESTADO_DIR", self.pasta())
        p2 = mock.patch.object(pmg, "LOG", self.pasta() / "runs.log")
        p1.start(); p2.start()
        self.addCleanup(p1.stop); self.addCleanup(p2.stop)
        self.retrato = self.pasta() / "config" / "capivara" / "capacidades.json"
        cap.gravar(montar_fake(), self.retrato)
        self.estado = self.pasta() / "estado" / "capacidades.json"
        self.perfil = self.pasta() / "estado" / "perfis-modelos.json"

    def _pub(self, openrouter=None, nvidia=None):
        def f(url, timeout=30):
            if "openrouter" in url:
                if openrouter is None:
                    raise OSError("fora do ar")
                return openrouter
            return nvidia if nvidia is not None else nvidia_fake()
        return f

    def _etapa(self, pub, uso=None, hoje=DATA):
        return pmg._etapa_capivara(origem=self.retrato, estado=self.estado, perfil=self.perfil,
                                   fetch_omni=omni_fake, fetch_publico=pub,
                                   uso=uso or (self.pasta() / "sem.jsonl"), hoje=hoje)

    def test_etapa_nao_escreve_no_retrato_do_repositorio(self):
        antes = self.retrato.read_text(encoding="utf-8")
        self._etapa(self._pub(openrouter_fake(), nvidia_fake()))
        self._etapa(self._pub(openrouter_fake(), nvidia_fake()), hoje="2026-11-30")
        self.assertEqual(self.retrato.read_text(encoding="utf-8"), antes)
        self.assertTrue(self.estado.is_file())

    def test_primeira_rodada_le_o_retrato_e_a_segunda_le_o_estado(self):
        self.assertEqual(self._etapa(self._pub(openrouter_fake(), nvidia_fake()))["base"], "retrato")
        self.assertEqual(self._etapa(self._pub(openrouter_fake(), nvidia_fake()))["base"], "estado")

    def test_etapa_regenera_o_perfil_derivado_no_estado(self):
        self._etapa(self._pub(openrouter_fake(), nvidia_fake()))
        perfil = json.loads(self.perfil.read_text(encoding="utf-8"))
        self.assertEqual(perf.conferir_perfil(perfil, cap.carregar(self.estado)), [])

    def test_semeadura_atualiza_declarado_e_grava(self):
        r = self._etapa(self._pub(openrouter_fake(), nvidia_fake()))
        self.assertTrue(r["gravado"])
        reg = cap.carregar(self.estado)
        c = reg["modelos"][NEMOTRON]["declarado"]["claims"]["janela"]
        self.assertIn(("openrouter", DATA), [(x["origem"], x["data"]) for x in c])
        self.assertEqual(cap.conferir(reg), [])

    def test_falha_de_uma_fonte_nao_apaga_o_que_ja_havia(self):
        self._etapa(self._pub(openrouter_fake(), nvidia_fake()), hoje="2026-11-16")
        r = self._etapa(self._pub(None, nvidia_fake()), hoje=DATA)
        self.assertTrue(r["openrouter"].startswith("erro"))
        reg = cap.carregar(self.estado)
        c = [x for x in reg["modelos"][NEMOTRON]["declarado"]["claims"]["janela"] if x["origem"] == "openrouter"]
        self.assertTrue(c, "a afirmação da fonte que falhou sumiu do registro")
        self.assertEqual(c[0]["data"], "2026-11-16")

    def test_segunda_rodada_igual_nao_regrava(self):
        self._etapa(self._pub(openrouter_fake(), nvidia_fake()))
        r = self._etapa(self._pub(openrouter_fake(), nvidia_fake()))
        self.assertFalse(r["gravado"])

    def test_id_so_da_lista_publica_nao_entra_no_registro(self):
        r = self._etapa(self._pub(openrouter_fake(), nvidia_fake()))
        reg = cap.carregar(self.estado)
        self.assertNotIn("openrouter/z/pago", reg["modelos"])
        self.assertGreaterEqual(r["fora_do_inventario"], 1)

    def test_uso_entra_pela_mesma_etapa(self):
        uso = self.pasta() / "uso.jsonl"
        uso.write_text(linha() + "\n", encoding="utf-8")
        r = self._etapa(self._pub(openrouter_fake(), nvidia_fake()), uso=uso)
        self.assertEqual(r["uso_novas"], 1)
        self.assertTrue(cap.carregar(self.estado)["modelos"]["gemini/gemini-2.5-flash"]["observado"])


class VerificacaoTest(_Tmp):
    """Verificação na 1ª resposta (achados, correção e refações) do uso.jsonl: medidas por modelo×tipo e o bloco
    global `verificacao` (contagem por rótulo, e quantas vezes a refação resolveu)."""

    def setUp(self):
        self.arq = self.pasta() / "uso.jsonl"
        self.reg = montar_fake()

    def anexar(self, *linhas_txt):
        with self.arq.open("a", encoding="utf-8") as f:
            for txt in linhas_txt:
                f.write(txt + "\n")

    def incorporar(self):
        return cap.incorporar_arquivo(self.reg, self.arq)

    def _metrica(self, metrica):
        return [x for x in self.reg["modelos"]["gemini/gemini-2.5-flash"]["observado"] if x["metrica"] == metrica]

    def _cenario(self):
        self.anexar(
            linha(ts="2026-11-23T10:00:00-03:00", achados=[], refeito=0),
            linha(ts="2026-11-23T10:01:00-03:00", achados=["fato_sem_fonte"], corrigido=True, refeito=1),
            linha(ts="2026-11-23T10:02:00-03:00", achados=["fato_sem_fonte", "citacao"], corrigido=False, refeito=2),
            linha(ts="2026-11-23T10:03:00-03:00"),                 # sem o campo: não verificada
            linha(ts="2026-11-23T10:04:00-03:00", achados=None),    # null: verificada, sem achado
        )

    def test_taxas_por_modelo_e_tipo(self):
        self._cenario()
        self.incorporar()
        self.assertEqual([(x["valor"], x["amostra"]) for x in self._metrica("taxa_achado")], [(0.5, 4)])
        self.assertEqual([(x["valor"], x["amostra"]) for x in self._metrica("taxa_corrigido")], [(0.5, 2)])
        self.assertEqual([(x["valor"], x["amostra"]) for x in self._metrica("refeito_medio")], [(1.0, 3)])
        self.assertEqual(self._metrica("taxa_achado")[0]["tipo"], "conversa")
        self.assertEqual(self._metrica("taxa_ok")[0]["amostra"], 5)  # a taxa de sucesso segue sobre todas
        self.assertEqual(cap.conferir(self.reg), [])

    def test_bloco_global_conta_rotulos_e_resolvidos_pela_refacao(self):
        self._cenario()
        self.incorporar()
        v = self.reg["verificacao"]
        self.assertEqual(v["linhas"], 4)
        self.assertEqual(v["achados"]["fato_sem_fonte"], {"ocorrencias": 2, "resolvidos_pela_refacao": 1})
        self.assertEqual(v["achados"]["citacao"], {"ocorrencias": 1, "resolvidos_pela_refacao": 0})
        self.assertEqual(cap.conferir(self.reg), [])

    def test_acumula_entre_lotes_e_nao_duplica(self):
        self._cenario()
        self.incorporar()
        antes = json.dumps(self.reg["verificacao"], sort_keys=True)
        self.incorporar()
        self.assertEqual(json.dumps(self.reg["verificacao"], sort_keys=True), antes)
        self.anexar(linha(ts="2026-11-23T11:00:00-03:00", achados=["citacao"], corrigido=True, refeito=1))
        self.incorporar()
        self.assertEqual(self.reg["verificacao"]["linhas"], 5)
        self.assertEqual(self.reg["verificacao"]["achados"]["citacao"], {"ocorrencias": 2, "resolvidos_pela_refacao": 1})

    def test_corrigido_sem_refacao_nao_conta_como_resolvido(self):
        """Resolvido = tinha o rótulo, veio corrigido e foi refeito pelo menos uma vez. Corrigido sem refação não conta."""
        self.anexar(linha(achados=["citacao"], corrigido=True, refeito=0))
        self.incorporar()
        self.assertEqual(self.reg["verificacao"]["achados"]["citacao"], {"ocorrencias": 1, "resolvidos_pela_refacao": 0})

    def test_rotulo_que_nao_e_slug_nao_entra(self):
        self.anexar(linha(achados=["texto livre com frase"], corrigido=True, refeito=1),
                    linha(ts="2026-11-23T10:01:00-03:00", achados=["fato_sem_fonte"]))
        st = self.incorporar()
        self.assertEqual((st["novas"], st["malformadas"]), (2, 0))
        self.assertEqual(set(self.reg["verificacao"]["achados"]), {"fato_sem_fonte"})
        self.assertEqual(self.reg["verificacao"]["linhas"], 1)
        self.assertEqual(self._metrica("taxa_achado")[0]["amostra"], 1)

    def test_sem_campo_achados_nao_gera_verificacao(self):
        self.anexar(linha(), linha(ts="2026-11-23T10:01:00-03:00", status=500))
        self.incorporar()
        self.assertNotIn("verificacao", self.reg)
        self.assertEqual(self._metrica("taxa_achado"), [])
        self.assertEqual(self._metrica("refeito_medio"), [])

    def test_refeito_e_corrigido_de_tipo_errado_sao_ignorados(self):
        self.anexar(linha(achados=["citacao"], refeito="2", corrigido="sim"))
        st = self.incorporar()
        self.assertEqual((st["novas"], st["malformadas"]), (1, 0))
        self.assertEqual(self._metrica("refeito_medio"), [])
        self.assertEqual(self._metrica("taxa_corrigido"), [])
        self.assertEqual(self._metrica("taxa_achado")[0]["valor"], 1.0)
        self.assertEqual(self.reg["verificacao"]["achados"]["citacao"], {"ocorrencias": 1, "resolvidos_pela_refacao": 0})

    def test_bloco_invalido_e_recusado(self):
        self._cenario()
        self.incorporar()
        self.reg["verificacao"]["achados"]["citacao"]["resolvidos_pela_refacao"] = 9
        self.assertTrue(any("verificacao inválida" in e for e in cap.conferir(self.reg)))

    def test_montagem_preserva_o_bloco_global(self):
        bloco = {"linhas": 3, "achados": {"citacao": {"ocorrencias": 2, "resolvidos_pela_refacao": 1}}}
        self.assertEqual(montar_fake(anterior={"verificacao": bloco})["verificacao"], bloco)


class AcumuladoTest(_Tmp):
    """Registro acumulado por chave: duas rodadas somam, a rotação do arquivo não reconta nem zera, e as taxas
    são recalculadas a partir das somas (não é a média das taxas de cada rodada)."""

    def setUp(self):
        self.arq = self.pasta() / "uso.jsonl"
        self.reg = montar_fake()

    def anexar(self, *linhas_txt):
        with self.arq.open("a", encoding="utf-8") as f:
            for txt in linhas_txt:
                f.write(txt + "\n")

    def incorporar(self):
        return cap.incorporar_arquivo(self.reg, self.arq)

    def _registros(self, metrica, **chave):
        return [x for x in self.reg["modelos"]["gemini/gemini-2.5-flash"]["observado"]
                if x["metrica"] == metrica and all(x.get(k) == v for k, v in chave.items())]

    def _taxa(self):
        (r,) = self._registros("taxa_ok", tipo="conversa")
        return r

    def test_duas_rodadas_somam_e_taxa_sai_da_soma(self):
        self.anexar(linha(ts="2026-11-23T10:00:00-03:00", latencia=100),
                    linha(ts="2026-11-23T10:01:00-03:00", status=500, latencia=300))
        self.incorporar()
        self.anexar(linha(ts="2026-11-23T10:02:00-03:00", latencia=200),
                    linha(ts="2026-11-23T10:03:00-03:00", latencia=200),
                    linha(ts="2026-11-23T10:04:00-03:00", status=None, latencia=None))
        self.incorporar()
        r = self._taxa()
        self.assertEqual((r["amostra"], r["ok"], r["falhas"], r["valor"]), (5, 3, 2, 0.6))
        self.assertEqual(r["latencia_media_ms"], 200.0)  # (100 + 300 + 200 + 200) / 4; a sem latência fica fora
        self.assertEqual((r["desde"], r["ate"]), ("2026-11-23T10:00:00-03:00", "2026-11-23T10:04:00-03:00"))
        self.assertEqual(cap.conferir(self.reg), [])

    def test_rotacao_nao_reconta_nem_zera(self):
        self.anexar(linha(latencia=100), linha(ts="2026-11-23T10:01:00-03:00", status=500, latencia=300),
                    linha(ts="2026-11-23T10:02:00-03:00", latencia=200))
        self.incorporar()
        novo = self.arq.parent / "rotacionado.jsonl"
        novo.write_text(linha(ts="2026-11-23T12:00:00-03:00", latencia=400) + "\n"
                        + linha(ts="2026-11-23T12:01:00-03:00", status=None, latencia=None) + "\n", encoding="utf-8")
        os.replace(novo, self.arq)  # o arquivo foi trocado: outro inode, só linhas novas
        st = self.incorporar()
        self.assertEqual(st["novas"], 2)
        r = self._taxa()
        self.assertEqual((r["amostra"], r["ok"], r["falhas"]), (5, 3, 2))  # 3 antigas + 2 novas
        self.assertEqual(r["valor"], 0.6)
        self.assertEqual(r["latencia_media_ms"], 250.0)  # (100 + 300 + 200 + 400) / 4

    def test_taxas_de_verificacao_recalculadas_pelas_somas(self):
        self.anexar(linha(ts="2026-11-23T10:00:00-03:00", achados=["citacao"], corrigido=True, refeito=1),
                    linha(ts="2026-11-23T10:01:00-03:00", achados=[], refeito=0))
        self.incorporar()
        self.anexar(linha(ts="2026-11-23T11:00:00-03:00", achados=["x"], corrigido=False, refeito=2),
                    linha(ts="2026-11-23T11:01:00-03:00", achados=["x"], corrigido=False, refeito=0))
        self.incorporar()
        (ta,) = self._registros("taxa_achado", tipo="conversa")
        (tc,) = self._registros("taxa_corrigido", tipo="conversa")
        (rm,) = self._registros("refeito_medio", tipo="conversa")
        self.assertEqual((ta["amostra"], ta["valor"]), (4, 0.75))       # 3 com achado de 4 verificadas
        self.assertEqual((tc["amostra"], tc["valor"]), (3, 0.3333))     # 1 corrigido de 3 com achado
        self.assertEqual((rm["amostra"], rm["valor"]), (4, 0.75))       # (1 + 0 + 2 + 0) / 4 refações
        self.assertEqual(cap.conferir(self.reg), [])

    def test_um_registro_por_chave_mesmo_depois_de_varias_rodadas(self):
        for i in range(4):
            self.anexar(linha(ts=f"2026-11-23T1{i}:00:00-03:00"))
            self.incorporar()
        self.assertEqual(len(self.reg["modelos"]["gemini/gemini-2.5-flash"]["observado"]), 1)
        self.assertEqual(self._taxa()["amostra"], 4)

    def test_laya_acumula_por_rota_e_media_de_confianca(self):
        m = "gemini/gemini-2.5-flash"
        self.anexar(linha(ts="2026-11-23T10:00:00-03:00", modelo=m, rota="rapido", rota_por="laya", laya_confianca=0.8),
                    linha(ts="2026-11-23T10:01:00-03:00", modelo=m, rota="rapido", rota_por="laya", laya_confianca=0.4))
        self.incorporar()
        self.anexar(linha(ts="2026-11-23T11:00:00-03:00", modelo=m, rota="rapido", rota_por="laya", laya_confianca=0.9))
        self.incorporar()
        laya = self.reg["modelos"][LAYA]["observado"]
        (taxa,) = [x for x in laya if x["metrica"] == "taxa_ok" and x["rota"] == "rapido" and x["rota_por"] == "laya"]
        (conf,) = [x for x in laya if x["metrica"] == "laya_confianca_media" and x["rota"] == "rapido"]
        self.assertEqual((taxa["amostra"], taxa["valor"]), (3, 1.0))
        self.assertEqual((conf["amostra"], conf["valor"]), (3, 0.7))  # (0.8 + 0.4 + 0.9) / 3
        self.assertEqual(len(laya), 2)  # um de taxa, um de confiança: nada a mais por rodada


class CaminhosTest(_Tmp):
    """Qual arquivo está em uso: o do estado quando ele é válido (conferir OK); senão o retrato do repositório."""

    def _registro(self):
        t = self.pasta()
        retrato, estado = t / "retrato" / "capacidades.json", t / "estado" / "capacidades.json"
        cap.gravar(montar_fake(), retrato)
        return retrato, estado

    def test_registro_sem_estado_usa_o_retrato(self):
        retrato, estado = self._registro()
        self.assertEqual(cap.caminho_registro(retrato, estado), retrato)

    def test_registro_de_estado_valido_tem_precedencia(self):
        retrato, estado = self._registro()
        cap.gravar(montar_fake(), estado)
        self.assertEqual(cap.caminho_registro(retrato, estado), estado)

    def test_registro_de_estado_corrompido_cai_no_retrato(self):
        retrato, estado = self._registro()
        estado.parent.mkdir(parents=True)
        estado.write_text("{ruim", encoding="utf-8")
        self.assertEqual(cap.caminho_registro(retrato, estado), retrato)

    def test_registro_de_estado_que_nao_passa_na_conferencia_cai_no_retrato(self):
        retrato, estado = self._registro()
        ruim = montar_fake()
        ruim["modelos"]["gemini/gemini-2.5-flash"]["janela"] = 999  # número sem afirmação
        cap.gravar(ruim, estado)
        self.assertEqual(cap.caminho_registro(retrato, estado), retrato)

    def test_carregar_sem_argumento_segue_o_registro_em_uso(self):
        retrato, estado = self._registro()
        cap.gravar(montar_fake(), estado)
        with mock.patch.object(cap, "REGISTRO", retrato), mock.patch.object(cap, "ESTADO_REGISTRO", estado):
            self.assertEqual(cap.carregar(), cap.carregar(estado))

    def _perfis(self):
        t = self.pasta()
        retrato_reg, estado_reg = t / "retrato" / "capacidades.json", t / "estado" / "capacidades.json"
        retrato_perf, estado_perf = t / "retrato" / "perfis-modelos.json", t / "estado" / "perfis-modelos.json"
        cap.gravar(montar_fake(), retrato_reg)
        cap.gravar(perf.derivar(montar_fake()), retrato_perf)
        return retrato_reg, estado_reg, retrato_perf, estado_perf

    def test_perfil_de_estado_em_dia_tem_precedencia(self):
        r_reg, e_reg, r_perf, e_perf = self._perfis()
        cap.gravar(perf.derivar(montar_fake()), e_perf)
        with mock.patch.object(cap, "REGISTRO", r_reg), mock.patch.object(cap, "ESTADO_REGISTRO", e_reg):
            self.assertEqual(perf.caminho_perfil(r_perf, e_perf), e_perf)

    def test_perfil_de_estado_defasado_cai_no_retrato(self):
        r_reg, e_reg, r_perf, e_perf = self._perfis()
        velho = perf.derivar(montar_fake())
        velho["modelos"]["gemini/gemini-2.5-flash"]["janela"] = 5
        cap.gravar(velho, e_perf)
        with mock.patch.object(cap, "REGISTRO", r_reg), mock.patch.object(cap, "ESTADO_REGISTRO", e_reg):
            self.assertEqual(perf.caminho_perfil(r_perf, e_perf), r_perf)

    def test_perfil_de_estado_corrompido_cai_no_retrato(self):
        r_reg, e_reg, r_perf, e_perf = self._perfis()
        e_perf.parent.mkdir(parents=True)
        e_perf.write_text("{ruim", encoding="utf-8")
        with mock.patch.object(cap, "REGISTRO", r_reg), mock.patch.object(cap, "ESTADO_REGISTRO", e_reg):
            self.assertEqual(perf.caminho_perfil(r_perf, e_perf), r_perf)

    def test_carregar_perfil_sem_argumento_usa_o_caminho_em_uso(self):
        r_reg, e_reg, r_perf, e_perf = self._perfis()
        em_dia = perf.derivar(montar_fake())
        em_dia["medido_em"] = "2026-11-20"  # difere do retrato só na data: continua em dia com o registro
        cap.gravar(em_dia, e_perf)
        with mock.patch.object(cap, "REGISTRO", r_reg), mock.patch.object(cap, "ESTADO_REGISTRO", e_reg), \
                mock.patch.object(cap, "ESTADO_PERFIL", e_perf):
            self.assertEqual(perf.carregar()["medido_em"], "2026-11-20")

    def test_conferir_perfil_aponta_o_modelo_defasado(self):
        reg = montar_fake()
        perfil = perf.derivar(reg)
        self.assertEqual(perf.conferir_perfil(perf.derivar(reg), reg), [])
        perfil["modelos"]["gemini/gemini-2.5-flash"]["janela"] = 5
        self.assertEqual(perf.conferir_perfil(perfil, reg), ["gemini/gemini-2.5-flash"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
