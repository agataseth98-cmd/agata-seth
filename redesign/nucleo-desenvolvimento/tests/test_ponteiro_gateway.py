"""C11a e C11b (condicionais à decisão D2, aceita): o ponteiro PROCESSO no gateway.

C11a: o ponteiro aparece numa conversa de faixa interna e não aparece na faixa pública.
C11b: SETH_PROCESSO_HIDRATA=0 desliga o ponteiro, e o MARCADOR não muda com a linha acrescentada.

Adaptado em 14/11/2026 ao main atual: não existe mais `_DOUTRINA_FIXA` nem `_DOUTRINA_PUBLICA`. A doutrina vive em
PROTOCOLOS.md: a seção SETH-GATEWAY (lida por `_ler_secao("seth")`) e a SETH-PUBLICA (lida por `_doutrina_publica()`).
O MARCADOR é o hash de (seção SETH-GATEWAY + AGENTS.md), em `_hash_fonte()`. Por isso o MARCADOR muda uma vez quando
AGENTS.md muda (a linha do ponteiro do AGENTS.md entra no hash); a linha PROCESSO do gateway não entra.
O valor do MARCADOR não é fixado aqui: o teste calcula a partir das fontes, para não quebrar a cada mudança de texto.

Isola o estado (`_estado`, que roda um subprocess) e o cache do Conselho (que lê o cache real).
"""
import hashlib
import importlib
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "redesign" / "router"))

PREFIXO = "PROCESSO:"
PAYLOAD = {"model": "seth-teste", "messages": [{"role": "user", "content": "oi"}]}


class PonteiroGatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.g = importlib.import_module("seth_gateway")
            cls.cc = importlib.import_module("cache_conselho")
        except Exception as e:  # noqa: BLE001
            raise AssertionError(f"seth_gateway não importa: {e!r}")
        cls.marcador = cls.g.MARCADOR

    def transformar(self, payload, env_extra=None, remover=(), *, estado="HEAD: teste (medido no teste)",
                    modo="compacto", hidratacao=None):
        """Chama _injeta com estado fixo e sem cache real."""
        g = self.g
        env = {k: v for k, v in os.environ.items() if k not in remover}
        if env_extra:
            env.update(env_extra)
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(g, "_estado", return_value=estado), \
                mock.patch.object(g, "MODO", modo), \
                mock.patch.object(g.auditoria_turno, "linha_estado", return_value=""), \
                mock.patch.object(self.cc, "resumo_hidratacao", return_value=""):
            if hidratacao is None:
                return g._injeta(json.loads(json.dumps(payload)))
            with mock.patch.object(g, "_hidratacao", return_value=hidratacao):
                return g._injeta(json.loads(json.dumps(payload)))

    def injetar(self, env_extra=None, remover=()):
        """Devolve o texto da primeira mensagem de sistema de um payload novo."""
        out = self.transformar(PAYLOAD, env_extra=env_extra, remover=remover)
        return out["messages"][0]["content"]

    def sistemas(self, payload):
        """Textos de todas as mensagens de sistema de um payload."""
        return [m.get("content", "") for m in payload["messages"]
                if isinstance(m, dict) and m.get("role") == "system"]

    def test_ponteiro_so_nas_faixas_internas(self):
        # C11a: faixa interna recebe o ponteiro (via _injeta).
        self.assertTrue(hasattr(self.g, "_LINHA_PROCESSO"),
                        "seth_gateway não tem _LINHA_PROCESSO: o ponteiro PROCESSO ainda não foi implementado")
        interna = self.injetar(remover=("SETH_PROCESSO_HIDRATA",))
        self.assertIn(PREFIXO, interna, "a faixa interna não recebeu a linha PROCESSO:")
        self.assertIn(self.g._LINHA_PROCESSO, interna)
        # faixa pública: o caminho dela é _preparar_payload_publico, que não chama _injeta
        publica = self.g._preparar_payload_publico(json.loads(json.dumps(PAYLOAD)))
        texto_publico = json.dumps(publica, ensure_ascii=False)
        self.assertNotIn(PREFIXO, texto_publico, "a faixa pública recebeu a linha PROCESSO:")
        self.assertNotIn(self.g._LINHA_PROCESSO, texto_publico)
        ok_publica, secao_publica = self.g._ler_secao("publica")
        self.assertTrue(ok_publica, "seção SETH-PUBLICA de PROTOCOLOS.md não pôde ser lida")
        self.assertNotIn(PREFIXO, secao_publica, "a doutrina pública (SETH-PUBLICA) não pode carregar o ponteiro")
        ok_seth, secao_seth = self.g._ler_secao("seth")
        self.assertTrue(ok_seth, "seção SETH-GATEWAY de PROTOCOLOS.md não pôde ser lida")
        self.assertNotIn(PREFIXO, secao_seth, "a doutrina da Seth (SETH-GATEWAY) não pode carregar o ponteiro")

    def test_ponteiro_desligavel_por_ambiente(self):
        # C11b: SETH_PROCESSO_HIDRATA=0 tira a linha; o MARCADOR não muda com a linha acrescentada.
        self.assertTrue(hasattr(self.g, "_LINHA_PROCESSO"),
                        "seth_gateway não tem _LINHA_PROCESSO: o ponteiro PROCESSO ainda não foi implementado")
        ligada = self.injetar(remover=("SETH_PROCESSO_HIDRATA",))
        self.assertIn(PREFIXO, ligada, "sem a variável, o ponteiro deveria aparecer; senão o teste de desligar não prova nada")
        desligada = self.injetar(env_extra={"SETH_PROCESSO_HIDRATA": "0"})
        self.assertNotIn(PREFIXO, desligada, "SETH_PROCESSO_HIDRATA=0 não desligou o ponteiro")
        self.assertIn("HEAD: teste", desligada, "desligar o ponteiro não pode tirar o estado")
        self.assertIn(self.marcador, ligada, "ligar o ponteiro não pode mudar o MARCADOR")
        self.assertIn(self.marcador, desligada, "desligar o ponteiro não pode mudar o MARCADOR")

    def test_marcador_vem_so_da_doutrina_e_do_agents(self):
        # O MARCADOR é o hash de (SETH-GATEWAY + AGENTS.md), como em seth_gateway._hash_fonte. A linha PROCESSO
        # do gateway não pode estar nessas fontes: se estivesse, acrescentá-la mudaria o MARCADOR.
        ok, secao = self.g._ler_secao("seth")
        self.assertTrue(ok, "seção SETH-GATEWAY de PROTOCOLOS.md não pôde ser lida")
        agents = (RAIZ / "AGENTS.md").read_text(encoding="utf-8")
        esperado = hashlib.sha256((secao + "\n--AGENTS--\n" + agents).encode("utf-8")).hexdigest()[:8]
        self.assertEqual(self.g.MARCADOR, f"<!-- SETH:HIDRATADO:{esperado} -->",
                         "o MARCADOR deixou de ser o hash de SETH-GATEWAY + AGENTS.md")
        self.assertNotIn(self.g._LINHA_PROCESSO, secao + agents,
                         "a linha PROCESSO entrou nas fontes do MARCADOR (mudaria o MARCADOR)")

    def test_ponteiro_se_atualiza_em_conversa_ja_hidratada(self):
        self.assertTrue(hasattr(self.g, "_LINHA_PROCESSO"),
                        "seth_gateway não tem _LINHA_PROCESSO: o ponteiro PROCESSO ainda não foi implementado")
        primeiro = self.transformar(PAYLOAD, remover=("SETH_PROCESSO_HIDRATA",))
        segunda_desligada = self.transformar(
            primeiro, env_extra={"SETH_PROCESSO_HIDRATA": "0"})
        sistemas_off = self.sistemas(segunda_desligada)
        self.assertEqual(sum(texto.count(PREFIXO) for texto in sistemas_off), 0,
                         "SETH_PROCESSO_HIDRATA=0 deixou o ponteiro antigo na conversa")
        self.assertTrue(any(self.marcador in texto for texto in sistemas_off),
                        "atualizar o estado apagou o MARCADOR da doutrina")

        segunda_ligada = self.transformar(
            primeiro, remover=("SETH_PROCESSO_HIDRATA",))
        sistemas_on = self.sistemas(segunda_ligada)
        self.assertEqual(sum(texto.count(PREFIXO) for texto in sistemas_on), 1,
                         "a conversa já hidratada duplicou a linha PROCESSO")
        self.assertTrue(any(self.marcador in texto for texto in sistemas_on),
                        "atualizar o estado apagou o MARCADOR da doutrina")

    def test_estado_indisponivel_preserva_ponteiro_ligado_e_remove_desligado(self):
        primeiro = self.transformar(PAYLOAD, remover=("SETH_PROCESSO_HIDRATA",))
        ligado_sem_estado = self.transformar(
            primeiro, remover=("SETH_PROCESSO_HIDRATA",), estado="")
        sistemas_ligado = self.sistemas(ligado_sem_estado)
        self.assertEqual(sum(texto.count(PREFIXO) for texto in sistemas_ligado), 1,
                         "falha de medição apagou o ponteiro ainda ligado")
        self.assertTrue(any(self.marcador in texto for texto in sistemas_ligado))

        desligado_sem_estado = self.transformar(
            primeiro, env_extra={"SETH_PROCESSO_HIDRATA": "0"}, estado="")
        sistemas_desligado = self.sistemas(desligado_sem_estado)
        self.assertEqual(sum(texto.count(PREFIXO) for texto in sistemas_desligado), 0,
                         "a chave desligada preservou o ponteiro apesar da falha de medição")
        self.assertTrue(any(self.marcador in texto for texto in sistemas_desligado))

    def test_modo_full_injeta_e_atualiza_ponteiro_so_no_caminho_interno(self):
        self.assertTrue(hasattr(self.g, "_LINHA_PROCESSO"))
        primeiro = self.transformar(PAYLOAD, remover=("SETH_PROCESSO_HIDRATA",),
                                    modo="full", hidratacao=f"{self.marcador}\nCANON\n")
        sistemas_primeiro = self.sistemas(primeiro)
        self.assertEqual(sum(texto.count(PREFIXO) for texto in sistemas_primeiro), 1,
                         "modo full não injetou o ponteiro na conversa interna")
        self.assertTrue(any(self.marcador in texto for texto in sistemas_primeiro))

        desligado = self.transformar(primeiro, env_extra={"SETH_PROCESSO_HIDRATA": "0"},
                                     modo="full", estado="HEAD: teste (medido no teste)")
        sistemas_desligado = self.sistemas(desligado)
        self.assertEqual(sum(texto.count(PREFIXO) for texto in sistemas_desligado), 0,
                         "modo full não respeitou a troca da chave para desligado")
        self.assertTrue(any(self.marcador in texto for texto in sistemas_desligado))

        with mock.patch.object(self.g, "MODO", "full"):
            publica = self.g._preparar_payload_publico(json.loads(json.dumps(PAYLOAD)))
        self.assertNotIn(PREFIXO, json.dumps(publica, ensure_ascii=False),
                         "modo full expôs o ponteiro na faixa pública")

    def test_linha_do_gateway_ate_200_caracteres(self):
        # D3 (aceita): a linha do gateway tem até 200 caracteres.
        self.assertLessEqual(len(self.g._LINHA_PROCESSO), 200,
                             f"linha PROCESSO com {len(self.g._LINHA_PROCESSO)} caracteres")


if __name__ == "__main__":
    unittest.main()
