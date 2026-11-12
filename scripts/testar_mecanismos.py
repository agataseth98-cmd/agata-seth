#!/usr/bin/env python3
"""Testes do pacote mecânico de 12/11/2026: ponto de entrada por modelo, gancho Stop (só aviso),
negação de leitura do .env, subagentes com pacote mínimo e o verificador conselho_mecanismos.py.

Rodar:  python3 scripts/testar_mecanismos.py
        uv run --offline --with pytest python3 -m pytest -q scripts/testar_mecanismos.py
Sem modelo, sem rede. Estado do turno em diretório temporário (AGATA_TURNOS_DIR); nada fora do repo.
Os nomes dos testes são os citados em redesign/router/spec/acceptance.json.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import conselho_mecanismos as cm  # noqa: E402

PY = sys.executable
AGENTES = sorted((RAIZ / ".claude" / "agents").glob("*.md"))
SO_LEITURA = {"agata-inov-critico", "agata-inov-pesquisa", "agata-pesq-painel",
              "agata-pesq-processo", "agata-pesq-rea"}
PARAGRAFO_PACOTE = "Quem delega a você passa só: objetivo, arquivos, critérios de pronto"

# Arquivos que o verificador lê. Os testes copiam só isto para um diretório temporário.
NECESSARIOS = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", "PROMPT_CARREGAMENTO.md",
               "redesign/router/cache_conselho.py", "redesign/router/seth_gateway.py",
               ".claude/settings.json", ".agents/skills/agata-fluxo-equipe/SKILL.md",
               "config/cli/codex/config.toml.exemplo", "config/cli/gemini/settings.json.exemplo",
               "config/cli/opencode/opencode.json.exemplo"]


def _copia_minima(destino: Path) -> Path:
    for rel in NECESSARIOS:
        alvo = destino / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(RAIZ / rel, alvo)
    (destino / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
    for arq in AGENTES:
        shutil.copy(arq, destino / ".claude" / "agents" / arq.name)
    return destino


def _falhas(achados) -> list:
    return [a for a in achados if a.estado == "FALHA"]


def _stop(payload, ambiente: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update(ambiente or {})
    entrada = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return subprocess.run([PY, str(RAIZ / "scripts" / "auditoria_stop.py")], input=entrada,
                          capture_output=True, text=True, timeout=60, env=env)


class TestPontosDeEntrada(unittest.TestCase):
    def test_claude_aponta_agents(self):
        achado = next(a for a in cm.verificar(RAIZ) if a.modelo == "Claude Code" and a.controle.startswith("entrada"))
        self.assertEqual(achado.estado, "ok-mecanico", achado.evidencia)

    def test_gemini_aponta_agents(self):
        achado = next(a for a in cm.verificar(RAIZ) if a.modelo == "Gemini CLI" and a.controle.startswith("entrada"))
        self.assertEqual(achado.estado, "ok-mecanico", achado.evidencia)

    def test_ponteiro_quebrado_falha(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = _copia_minima(Path(tmp))
            (raiz / "CLAUDE.md").write_text("# Agata\n\nRegra própria, sem o import do AGENTS.md.\n", encoding="utf-8")
            falhas = _falhas(cm.verificar(raiz))
            self.assertTrue(any(a.modelo == "Claude Code" and a.controle.startswith("entrada") for a in falhas))

    def test_ponteiro_virou_copia_falha(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = _copia_minima(Path(tmp))
            (raiz / "GEMINI.md").write_text("@AGENTS.md\n" + "regra copiada\n" * 80, encoding="utf-8")
            falhas = _falhas(cm.verificar(raiz))
            self.assertTrue(any(a.modelo == "Gemini CLI" and a.controle.startswith("entrada") for a in falhas))

    def test_codex_limite_de_32_kib(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = _copia_minima(Path(tmp))
            (raiz / "AGENTS.md").write_text("x" * (33 * 1024), encoding="utf-8")
            falhas = _falhas(cm.verificar(raiz))
            self.assertTrue(any(a.modelo == "Codex" and a.controle.startswith("entrada") for a in falhas))

    def test_codex_override_na_raiz_falha(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = _copia_minima(Path(tmp))
            (raiz / "AGENTS.override.md").write_text("outro", encoding="utf-8")
            falhas = _falhas(cm.verificar(raiz))
            self.assertTrue(any(a.modelo == "Codex" and a.controle.startswith("entrada") for a in falhas))

    def test_verificador_sai_1_com_falha(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = _copia_minima(Path(tmp))
            (raiz / "CLAUDE.md").write_text("sem import\n", encoding="utf-8")
            r = subprocess.run([PY, str(RAIZ / "scripts" / "conselho_mecanismos.py"), "--verificar", "--raiz", str(raiz)],
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 1, r.stdout)

    def test_repositorio_sem_falha(self):
        r = subprocess.run([PY, str(RAIZ / "scripts" / "conselho_mecanismos.py"), "--verificar"],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("FALHA 0", r.stdout)


class TestSemLeituraDeSegredo(unittest.TestCase):
    def test_settings_nega_leitura_do_env(self):
        cfg = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertIn("Read(~/.config/agata/.env)", cfg["permissions"]["deny"])

    def test_exemplo_codex_nega_o_env(self):
        import tomllib
        cfg = tomllib.loads((RAIZ / "config/cli/codex/config.toml.exemplo").read_text(encoding="utf-8"))
        self.assertEqual(cfg["permissions"]["agata"]["filesystem"]["~/.config/agata/.env"], "deny")
        self.assertEqual(cfg["default_permissions"], "agata")

    def test_exemplo_opencode_nega_env(self):
        cfg = json.loads((RAIZ / "config/cli/opencode/opencode.json.exemplo").read_text(encoding="utf-8"))
        self.assertIn({"action": "read", "resource": "*.env", "effect": "deny"}, cfg["permissions"])

    def test_gancho_gemini_bloqueia_leitura_do_env(self):
        script = str(RAIZ / "config" / "cli" / "gemini" / "bloquear_env.py")
        negado = subprocess.run([PY, script], input=json.dumps({"tool_name": "read_file", "tool_input": {
            "file_path": "/home/x/.config/agata/.env"}}), capture_output=True, text=True, timeout=30)
        self.assertEqual(negado.returncode, 2)
        liberado = subprocess.run([PY, script], input=json.dumps({"tool_name": "read_file", "tool_input": {
            "file_path": "README.md"}}), capture_output=True, text=True, timeout=30)
        self.assertEqual(liberado.returncode, 0)
        invalido = subprocess.run([PY, script], input="{ruim", capture_output=True, text=True, timeout=30)
        self.assertEqual(invalido.returncode, 0)


class TestGancho(unittest.TestCase):
    def setUp(self):
        self.turnos = tempfile.mkdtemp()
        self.env = {"AGATA_TURNOS_DIR": self.turnos}

    def tearDown(self):
        shutil.rmtree(self.turnos, ignore_errors=True)

    def test_stop_settings_registrado(self):
        cfg = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
        cmd = json.dumps(cfg["hooks"]["Stop"], ensure_ascii=False)
        self.assertIn("scripts/auditoria_stop.py", cmd)

    def test_stop_avisa_sem_bloquear(self):
        texto = "Resultado. Veja o P-999 antes de citar."
        r = _stop({"session_id": "sessao-a", "last_assistant_message": texto}, self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        dados = json.loads(r.stdout.strip())
        self.assertIn("systemMessage", dados)
        self.assertNotIn("decision", dados)
        self.assertNotIn("continue", dados)

    def test_stop_sem_achado_sai_calado(self):
        texto = "Resultado curto, sem citação nem controle."
        r = _stop({"session_id": "sessao-a", "last_assistant_message": texto}, self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_stop_sem_texto_ou_entrada_ruim_sai_0(self):
        for entrada in ("", "{ruim", json.dumps({"session_id": "x"})):
            r = _stop(entrada, self.env)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")

    def test_stop_le_prompt_response_do_gemini(self):
        r = _stop({"prompt_response": "Veja o P-999."}, self.env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("systemMessage", json.loads(r.stdout.strip()))

    def test_stop_confere_t_com_o_contador(self):
        # O contador da sessão está em 1; o cabeçalho diz t=3: a auditoria aponta a divergência.
        subprocess.run([PY, str(RAIZ / "scripts" / "turno.py"), "proximo", "--sessao", "sessao-t"],
                       env={**os.environ, **self.env}, capture_output=True, text=True, timeout=60, check=True)
        texto = "agata · claude-haiku-5-5 · t=3 (contador mecânico) · 12/11/2026 10:00 -03 (relógio da Máquina)\n\nOi."
        r = _stop({"session_id": "sessao-t", "last_assistant_message": texto}, self.env)
        self.assertIn("t=1", json.loads(r.stdout.strip())["systemMessage"])


class TestSubagentes(unittest.TestCase):
    def test_agentes_haiku_e_max_turns(self):
        self.assertTrue(AGENTES)
        for arq in AGENTES:
            t = arq.read_text(encoding="utf-8")
            self.assertIn("model: haiku", t, arq.name)
            self.assertIn("maxTurns:", t, arq.name)

    def test_agentes_so_leitura_sem_bash(self):
        for arq in AGENTES:
            if arq.stem not in SO_LEITURA:
                continue
            linha = next(l for l in arq.read_text(encoding="utf-8").splitlines() if l.startswith("tools:"))
            self.assertNotIn("Bash", linha, arq.name)

    def test_agentes_sem_omitclaudemd(self):
        for arq in AGENTES:
            self.assertNotIn("omitClaudeMd: true", arq.read_text(encoding="utf-8"), arq.name)

    def test_pacote_minimo_igual_em_todos(self):
        paragrafos = set()
        for arq in AGENTES:
            t = arq.read_text(encoding="utf-8")
            self.assertIn("## Pacote mínimo", t, arq.name)
            trecho = next(l for l in t.splitlines() if l.startswith(PARAGRAFO_PACOTE))
            paragrafos.add(trecho)
        self.assertEqual(len(paragrafos), 1)

    def test_skill_de_equipe_tem_a_regra(self):
        skill = (RAIZ / ".agents/skills/agata-fluxo-equipe/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## 9. Pacote mínimo para subagente", skill)
        self.assertIn("(`t=<n>.sub`)", skill)

    def test_prompt_carregamento_tem_o_contador(self):
        prompt = (RAIZ / "PROMPT_CARREGAMENTO.md").read_text(encoding="utf-8")
        self.assertIn("scripts/turno.py proximo --sessao", prompt)


class TestSeth(unittest.TestCase):
    def test_gateway_inclui_agents_na_hidratacao(self):
        # O gateway lê AGENTS.md por caminho relativo ao próprio arquivo: testa o texto injetado.
        sys.path.insert(0, str(RAIZ / "redesign" / "router"))
        spec = importlib.util.spec_from_file_location("seth_gateway_teste", RAIZ / "redesign/router/seth_gateway.py")
        gw = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gw)
        texto = gw._diretrizes_agents()
        self.assertIn("Diretrizes de todo modelo (AGENTS.md", texto)
        primeira = next(l for l in (RAIZ / "AGENTS.md").read_text(encoding="utf-8").splitlines() if l.strip())
        self.assertIn(primeira, texto)

    def test_gateway_nao_quebra_sem_agents(self):
        sys.path.insert(0, str(RAIZ / "redesign" / "router"))
        spec = importlib.util.spec_from_file_location("seth_gateway_teste2", RAIZ / "redesign/router/seth_gateway.py")
        gw = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gw)
        gw._AGENTS_PATH = Path(tempfile.mkdtemp()) / "nao_existe.md"
        gw._CACHE_AGENTS.update(mtime=None, texto="")
        self.assertIn("lacuna", gw._diretrizes_agents())


class TestConfigEExemplos(unittest.TestCase):
    def test_exemplos_existem(self):
        for rel in NECESSARIOS[-3:]:
            self.assertTrue((RAIZ / rel).exists(), rel)

    def test_gemini_exemplo_tem_os_dois_ganchos(self):
        cfg = json.loads((RAIZ / "config/cli/gemini/settings.json.exemplo").read_text(encoding="utf-8"))
        self.assertIn("AfterAgent", cfg["hooks"])
        self.assertIn("BeforeTool", cfg["hooks"])


if __name__ == "__main__":
    unittest.main()
