#!/usr/bin/env python3
"""Suite unittest da privacidade do benchmark_roteamento (anexo do canon).

Modelo local (ollama-local/, llamacpp-*, llama-cpp/, local/) roda o item privado; nuvem pula.
--liberar continua abrindo o provedor pedido. --via-gateway aceita modelo local e recusa nuvem.
LOCAIS tem que ser igual a _ROTAS_LOCAIS do gateway (teste de sincronia). Sem rede: o chamador é falso.
Uso: python3 -I scripts/testar_benchmark_roteamento.py
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import benchmark_roteamento as b  # noqa: E402

PRIVADO = {"id": "longo-x", "tipo": "contexto_longo", "pergunta": "leia", "privado": True}
PUBLICO = {"id": "conv-x", "tipo": "conversa", "pergunta": "oi"}
LLAMA = "llama-cpp/nemotron-3.5-lightning"
LLAMA_AGATA = "llamacpp-agata/qwen3-30b-a3b"
LOCAL_OLLAMA = "ollama-local/qwen3.5-9b-64k:latest"
NUVEM = ["openrouter/nvidia/nemotron-3-ultra-550b-a55b:free", "gemini/gemini-2.5-flash",
         "mistral/codestral-latest", "zai/glm-4.7-flash"]
RESPOSTA = {"model": "modelo-real", "choices": [{"message": {"role": "assistant", "content": "feito"},
                                                  "finish_reason": "stop"}]}


class PrivacidadeLocal(unittest.TestCase):
    def test_llama_cpp_roda_item_privado(self):
        self.assertTrue(b.liberado(PRIVADO, LLAMA, []))

    def test_llamacpp_prefixo_roda_item_privado(self):
        for m in (LLAMA_AGATA, "llamacpp-local/qwen3-30b-a3b"):
            with self.subTest(modelo=m):
                self.assertTrue(b.liberado(PRIVADO, m, []))

    def test_ollama_local_continua_rodando(self):
        self.assertTrue(b.liberado(PRIVADO, LOCAL_OLLAMA, []))

    def test_nuvem_pula_item_privado(self):
        for m in NUVEM:
            with self.subTest(modelo=m):
                self.assertFalse(b.liberado(PRIVADO, m, []))

    def test_item_publico_roda_em_todo_modelo(self):
        for m in [LLAMA, LLAMA_AGATA, LOCAL_OLLAMA, *NUVEM]:
            with self.subTest(modelo=m):
                self.assertTrue(b.liberado(PUBLICO, m, []))

    def test_liberar_abre_so_o_prefixo_pedido(self):
        self.assertTrue(b.liberado(PRIVADO, "gemini/gemini-2.5-flash", ["gemini/"]))
        self.assertFalse(b.liberado(PRIVADO, "mistral/codestral-latest", ["gemini/"]))

    def test_remotos_sao_so_a_nuvem(self):
        self.assertEqual(b.remotos([LLAMA, "llamacpp-local/m", "ollama-local/q", "mistral/x"]), ["mistral/x"])

    def test_locais_iguais_aos_do_gateway(self):
        # Sincronia: se o gateway mudar _ROTAS_LOCAIS, este teste avisa antes da produção divergir do benchmark.
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(RAIZ / "redesign" / "router"))
        import seth_gateway as g  # noqa: E402
        self.assertEqual(tuple(b.LOCAIS), tuple(g._ROTAS_LOCAIS))


class PlanoDeExecucao(unittest.TestCase):
    def _rodar(self, modelo, itens):
        chamadas = []

        def chamar(corpo, publico=True):
            chamadas.append((corpo["model"], publico))
            return RESPOSTA, 0.1

        linhas = b._rodar_plano([(modelo, i) for i in itens], [], chamar, 0, b.SISTEMA, "")
        return linhas, chamadas

    def test_llama_cpp_nao_pula_item_privado(self):
        linhas, chamadas = self._rodar(LLAMA, [PRIVADO, PUBLICO])
        self.assertEqual([(l["item"], l["estado"]) for l in linhas], [("longo-x", "ok"), ("conv-x", "ok")])
        # privado sem liberação: sem cabeçalho `public`, como no ollama-local
        self.assertEqual(chamadas, [(LLAMA, False), (LLAMA, True)])

    def test_nuvem_pula_privado_e_nao_chama(self):
        linhas, chamadas = self._rodar("gemini/gemini-2.5-flash", [PRIVADO, PUBLICO])
        self.assertEqual([l["estado"] for l in linhas], ["pulado_privacidade", "ok"])
        self.assertEqual(chamadas, [("gemini/gemini-2.5-flash", True)])


class PlanoPeloMain(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.corpus = os.path.join(self._tmp.name, "c.jsonl")
        with open(self.corpus, "w", encoding="utf-8") as f:
            f.write(json.dumps(PRIVADO) + "\n" + json.dumps(PUBLICO) + "\n")

    def tearDown(self):
        self._tmp.cleanup()

    def _main(self, argv):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = b.main(argv + ["--corpus", self.corpus])
        return codigo, saida.getvalue()

    def test_plano_llama_cpp_roda_os_dois_itens(self):
        codigo, texto = self._main(["--modelos", LLAMA])
        self.assertEqual(codigo, 0)
        self.assertIn("2 vão rodar, 0 pulados por privacidade", texto)

    def test_plano_nuvem_pula_o_privado(self):
        codigo, texto = self._main(["--modelos", "gemini/gemini-2.5-flash"])
        self.assertEqual(codigo, 0)
        self.assertIn("1 vão rodar, 1 pulados por privacidade", texto)

    def test_via_gateway_aceita_llama_cpp(self):
        codigo, texto = self._main(["--via-gateway", "--modelos", LLAMA])
        self.assertEqual(codigo, 0)
        self.assertIn("nada chamado", texto)

    def test_via_gateway_recusa_nuvem(self):
        codigo, texto = self._main(["--via-gateway", "--modelos", "gemini/gemini-2.5-flash"])
        self.assertEqual(codigo, 2)
        self.assertIn("remotos: gemini/gemini-2.5-flash", texto)


if __name__ == "__main__":
    unittest.main(verbosity=2)
