#!/usr/bin/env python3
"""Testes da sincronia-12-11 (fonte única, porquês, início de sessão, maxTurns).

Spec: redesign/sincronia/spec/spec.md e acceptance.json. Cada teste abaixo é um critério.
Rodar tudo:      python3 scripts/testar_sincronia.py
Rodar um:        python3 scripts/testar_sincronia.py TestPorques.test_estrito_falha_com_sem_porque
Só lê o repositório; os casos de falha usam diretórios temporários.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import conselho_mecanismos  # noqa: E402
import porques  # noqa: E402
import sessao_contexto  # noqa: E402


def _carregar_gateway():
    """Importa redesign/router/seth_gateway.py como módulo, apontando o repositório para RAIZ."""
    os.environ["SETH_REPO"] = str(RAIZ)
    os.environ.setdefault("LS_REMOTE_TIMEOUT_ECO", "1")
    sys.path.insert(0, str(RAIZ / "redesign" / "router"))
    spec = importlib.util.spec_from_file_location("seth_gateway_sincronia", RAIZ / "redesign/router/seth_gateway.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestFonteUnica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gw = _carregar_gateway()
        cls.codigo = (RAIZ / "redesign/router/seth_gateway.py").read_text(encoding="utf-8")

    def test_gateway_sem_doutrina_copiada(self):
        self.assertNotIn("_DOUTRINA_FIXA", self.codigo)
        self.assertIn("_doutrina_seth()", self.codigo)

    def test_secao_seth_lida_do_canon(self):
        ok, texto = self.gw._ler_secao("seth")
        self.assertTrue(ok)
        self.assertIn("Não escreva cabeçalho nenhum", texto)
        self.assertNotIn("<!-- SETH-GATEWAY", texto)  # os marcadores não entram na hidratação

    def test_hidratacao_traz_secao_e_agents(self):
        original = self.gw._estado
        self.gw._estado = lambda: "HEAD: teste (medição fixa do teste)"
        try:
            hidratacao = self.gw._hidratacao()
        finally:
            self.gw._estado = original
        self.assertIn("Não escreva cabeçalho nenhum", hidratacao)
        self.assertIn("Diretrizes de todo modelo (AGENTS.md", hidratacao)
        self.assertIn("**Regra 1:**", hidratacao)
        self.assertIn(self.gw.MARCADOR, hidratacao)

    def test_sem_secao_vira_lacuna_e_nao_cai_em_silencio(self):
        original_path, original_cache = self.gw._PROTOCOLOS_PATH, dict(self.gw._CACHE_SECAO)
        with tempfile.TemporaryDirectory() as tmp:
            falso = Path(tmp) / "PROTOCOLOS.md"
            falso.write_text("sem marcadores nenhum\n", encoding="utf-8")
            self.gw._PROTOCOLOS_PATH = falso
            self.gw._CACHE_SECAO.clear()
            try:
                texto = self.gw._doutrina_seth()
            finally:
                self.gw._PROTOCOLOS_PATH = original_path
                self.gw._CACHE_SECAO.clear()
                self.gw._CACHE_SECAO.update(original_cache)
        self.assertIn("lacuna", texto)

    def test_marcador_muda_quando_o_canon_muda(self):
        original_path, original_cache = self.gw._PROTOCOLOS_PATH, dict(self.gw._CACHE_SECAO)
        with tempfile.TemporaryDirectory() as tmp:
            outro = Path(tmp) / "PROTOCOLOS.md"
            outro.write_text("<!-- SETH-GATEWAY:INICIO -->\nregra nova de teste\n<!-- SETH-GATEWAY:FIM -->\n",
                             encoding="utf-8")
            try:
                self.gw._PROTOCOLOS_PATH = outro
                self.gw._CACHE_SECAO.clear()
                marcador_novo = self.gw._hash_fonte()
            finally:
                self.gw._PROTOCOLOS_PATH = original_path
                self.gw._CACHE_SECAO.clear()
                self.gw._CACHE_SECAO.update(original_cache)
        self.assertNotEqual(marcador_novo, self.gw._HASH_DOUTRINA)

    def test_protocolos_tem_secao_marcada(self):
        prot = (RAIZ / "PROTOCOLOS.md").read_text(encoding="utf-8")
        self.assertIn("## Seth no gateway (texto da hidratação)", prot)
        self.assertEqual(prot.count("<!-- SETH-GATEWAY:INICIO -->"), 1)
        self.assertEqual(prot.count("<!-- SETH-GATEWAY:FIM -->"), 1)

    def test_seth_nao_escreve_cabecalho_o_gateway_escreve(self):
        prot = (RAIZ / "PROTOCOLOS.md").read_text(encoding="utf-8")
        secao = prot[prot.index("<!-- SETH-GATEWAY:INICIO -->"):prot.index("<!-- SETH-GATEWAY:FIM -->")]
        self.assertIn("o gateway abre toda resposta sua com o cabeçalho medido", secao)
        self.assertIn("Não escreva cabeçalho nenhum", secao)

    def test_publica_sem_copia_e_com_marcadores(self):
        prot = (RAIZ / "PROTOCOLOS.md").read_text(encoding="utf-8")
        self.assertEqual(prot.count("<!-- SETH-PUBLICA:INICIO -->"), 1)
        self.assertEqual(prot.count("<!-- SETH-PUBLICA:FIM -->"), 1)
        self.assertIn("_doutrina_publica()", self.codigo)
        self.assertNotIn("_DOUTRINA_PUBLICA", self.codigo)

    def test_mecanismos_checam_fonte_unica(self):
        achados = conselho_mecanismos.verificar(RAIZ)
        linha = [a for a in achados if a.controle.startswith("fonte única")]
        self.assertEqual(len(linha), 1)
        self.assertEqual(linha[0].estado, "ok-mecanico")


class TestPorques(unittest.TestCase):
    def test_selftest_do_verificador(self):
        self.assertEqual(porques._selftest(), 0)

    def test_repositorio_tem_regras_e_skills(self):
        unidades, orfaos = porques.verificar(RAIZ)
        regras = [u for u in unidades if u.origem == "AGENTS.md"]
        skills = [u for u in unidades if u.origem == "skill"]
        self.assertEqual(len(regras), 18)
        self.assertEqual(len(skills), len(list((RAIZ / ".agents" / "skills").glob("*/SKILL.md"))))
        self.assertEqual(orfaos, [])

    def test_toda_regra_tem_origem_ou_esta_listada_como_sem_porque(self):
        unidades, _ = porques.verificar(RAIZ)
        for u in unidades:
            tem = bool(u.inline or u.registro)
            if not tem:
                self.assertNotEqual(u.origem, "AGENTS.md", f"regra do AGENTS.md sem porquê: {u.id}")

    def test_estrito_falha_com_sem_porque(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "AGENTS.md").write_text("**Sempre:**\n- **Sem origem:** nada.\n\n## Fim\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(porques._main(["--verificar", "--raiz", str(raiz)]), 0)
                self.assertEqual(porques._main(["--verificar", "--estrito", "--raiz", str(raiz)]), 1)

    def test_regras_curtas_lista_os_titulos(self):
        texto = porques.regras_curtas(RAIZ)
        self.assertTrue(texto.startswith("Regras ativas (AGENTS.md, Sempre, 18): Regra 1 · "))


class TestSessaoContexto(unittest.TestCase):
    def test_selftest_offline(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sessao_contexto._selftest(), 0)

    def test_decisoes_do_cache_so_pega_decisoes(self):
        linhas = [
            "(10) 2026-11-12T08:00:00-0300 · Codex · fato",
            "texto de fato que não entra",
            "",
            "(11) 2026-11-12T09:00:00-0300 · Claude Opus 5.5 · decisao",
            "decisão de teste",
            "",
        ]
        ds = sessao_contexto.decisoes_do_cache(linhas)
        self.assertEqual(ds, ["(11) 12/11 09:00 decisão de teste"])

    def test_lotes_abertos_le_a_coluna_estado(self):
        onde = "| componente | proposta | estado | desde |\n|---|---|---|---|\n| A | lote-a | proposta | 12/11 |\n"
        self.assertEqual(sessao_contexto.lotes_abertos(onde), "1 aberto(s): lote-a")

    def test_montar_tem_cinco_secoes_e_limite(self):
        texto = sessao_contexto.montar(RAIZ, estado=lambda r: "HEAD: x", cache=lambda r: "- (1) x",
                                       equipe=lambda r: "equipe x")
        for secao in ("Estado da Máquina", "Memória comum do Conselho", "Lotes abertos", "Regras ativas", "Sessão conjunta"):
            self.assertIn(secao, texto)
        self.assertLessEqual(len(texto), sessao_contexto.LIMITE_CARACTERES)

    def test_saida_json_no_formato_sessionstart(self):
        j = json.loads(sessao_contexto.como_json("x"))
        self.assertEqual(j["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertEqual(j["hookSpecificOutput"]["additionalContext"], "x")

    def test_involucro_claude_chama_o_conteudo_comum(self):
        sh = (RAIZ / "scripts" / "sessao_claude_contexto.sh").read_text(encoding="utf-8")
        self.assertIn("scripts/sessao_contexto.py", sh)
        self.assertNotIn("Regras desta sessão", sh)  # a cópia de regras saiu do script


class TestGatilhosDasCLIs(unittest.TestCase):
    def test_claude_settings_tem_sessionstart(self):
        settings = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
        ss = json.dumps(settings["hooks"]["SessionStart"], ensure_ascii=False)
        self.assertIn("sessao_claude_contexto.sh", ss)

    def test_gemini_exemplo_tem_sessionstart(self):
        gem = json.loads((RAIZ / "config/cli/gemini/settings.json.exemplo").read_text(encoding="utf-8"))
        self.assertIn("sessao_contexto.py", json.dumps(gem["hooks"]["SessionStart"]))
        self.assertIn("AfterAgent", gem["hooks"])  # regressão: o gancho de fim de turno continua

    def test_codex_exemplo_tem_sessionstart_e_mantem_o_resto(self):
        cdx = tomllib.loads((RAIZ / "config/cli/codex/config.toml.exemplo").read_text(encoding="utf-8"))
        self.assertIn("sessao_contexto.py", json.dumps(cdx["hooks"]["SessionStart"]))
        self.assertIn("Stop", cdx["hooks"])
        self.assertEqual(cdx["permissions"]["agata"]["filesystem"]["~/.config/agata/.env"], "deny")


class TestMaxTurns(unittest.TestCase):
    # Medição (relatórios desta sessão): 19 a 232 tool_uses por execução de agente. O tipo que chegou a
    # 232 não consta dos relatórios; por isso o teste exige só que o agente de desenvolvimento, que
    # escreve código e testes, tenha limite acima do maior uso medido (232, com margem).
    MAIOR_USO_MEDIDO = 232

    def test_todo_agente_tem_limite_numerico_entre_10_e_300(self):
        import re
        arquivos = sorted((RAIZ / ".claude" / "agents").glob("*.md"))
        self.assertTrue(arquivos)
        for arq in arquivos:
            m = re.search(r"^maxTurns: (\d+)$", arq.read_text(encoding="utf-8"), re.M)
            self.assertIsNotNone(m, arq.name)
            self.assertTrue(10 <= int(m.group(1)) <= 300, arq.name)

    def test_desenvolvedor_cabe_no_maior_uso_medido(self):
        import re
        texto = (RAIZ / ".claude" / "agents" / "agata-dev.md").read_text(encoding="utf-8")
        m = re.search(r"^maxTurns: (\d+)$", texto, re.M)
        self.assertIsNotNone(m)
        self.assertGreaterEqual(int(m.group(1)), self.MAIOR_USO_MEDIDO)


if __name__ == "__main__":
    unittest.main()
