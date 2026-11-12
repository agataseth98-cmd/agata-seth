#!/usr/bin/env python3
"""Testes do contador mecânico de turno (scripts/turno.py) e da divergência da auditoria.

Rodar:  python3 scripts/testar_turno.py
        uv run --offline --with pytest python3 -m pytest -q scripts/testar_turno.py
Sem modelo, sem rede. O estado fica sempre num diretório temporário (AGATA_TURNOS_DIR).
Os testes que a spec (redesign/router/spec/acceptance.json) cita existem aqui com esses nomes.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import turno  # noqa: E402
import verificar_cabecalho  # noqa: E402

TURNO_PY = RAIZ / "scripts" / "turno.py"
AUDITORIA = RAIZ / "redesign" / "router" / "auditoria_turno.py"
HORA_RE = r"\d{2}/\d{2}/\d{4} \d{2}:\d{2} -03 \(relógio da Máquina\)"


def _env(tmp: str, **extra) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_SESSION_ID"}
    env["AGATA_TURNOS_DIR"] = tmp
    env.update(extra)
    return env


def _cli(tmp: str, *args: str, entrada: str | None = None, **extra) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(TURNO_PY), *args], input=entrada,
                          capture_output=True, text=True, env=_env(tmp, **extra), timeout=60)


def _t(linha: str) -> int:
    return int(re.search(r"t=(\d+)", linha).group(1))


class _Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="turno-teste-")
        self._antes = os.environ.get("AGATA_TURNOS_DIR")
        os.environ["AGATA_TURNOS_DIR"] = self.tmp
        self.addCleanup(self._restaurar)

    def _restaurar(self):
        if self._antes is None:
            os.environ.pop("AGATA_TURNOS_DIR", None)
        else:
            os.environ["AGATA_TURNOS_DIR"] = self._antes
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _corromper(self, sessao: str, conteudo: str) -> None:
        Path(self.tmp, f"{sessao}.json").write_text(conteudo, encoding="utf-8")


class TestContador(_Base):
    def test_comeca_em_1_e_soma(self):
        a = turno.proximo("sess-1", "claude-haiku-5-5")
        b = turno.proximo("sess-1", "claude-haiku-5-5")
        self.assertTrue(a.startswith("agata · claude-haiku-5-5 · t=1 (contador mecânico) · "), a)
        self.assertIn("t=2 (contador mecânico)", b)

    def test_sub_nao_incrementa(self):
        turno.proximo("sess-2")
        s = turno.subagente("sess-2", "claude-haiku-5-5")
        self.assertIn("t=1.sub (contador mecânico, subagente)", s)
        self.assertIn("t=1 (contador mecânico)", turno.atual("sess-2"))
        self.assertIn("t=2 (contador mecânico)", turno.proximo("sess-2"))

    def test_sub_e_atual_recusam_sessao_sem_turno(self):
        with self.assertRaises(turno.SemContador):
            turno.subagente("nova")
        with self.assertRaises(turno.SemContador):
            turno.atual("nova")
        self.assertFalse(Path(self.tmp, "nova.json").exists())

    def test_sessoes_independentes(self):
        turno.proximo("sess-a")
        turno.proximo("sess-a")
        self.assertIn("t=1 (contador", turno.proximo("sess-b"))

    def test_id_invalido_nao_escreve_fora_do_diretorio(self):
        for ruim in ("../fora", "a/b", "", ".oculto", "x" * 129, "com espaço"):
            with self.subTest(ruim=ruim), self.assertRaises(turno.ErroSessao):
                turno.proximo(ruim)
        self.assertEqual(list(Path(self.tmp).iterdir()), [])
        self.assertFalse(Path(self.tmp).parent.joinpath("fora.json").exists())

    def test_hora_regional_com_fuso_e_selo(self):
        self.assertRegex(turno.proximo("sess-h"), HORA_RE)

    def test_modelo_nao_quebra_o_cabecalho(self):
        linha = turno.proximo("sess-m", "claude · x\nquebra")
        self.assertNotIn("\n", linha)
        self.assertEqual(linha.count("·"), 3, linha)

    def test_modelo_ausente_vira_nao_verificado(self):
        self.assertIn("modelo não verificado", turno.proximo("sess-n"))

    def test_selftest_do_modulo_passa(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(turno._selftest(), 0)

    def test_cli_codigos_de_saida(self):
        r = _cli(self.tmp, "proximo", "--sessao", "cli-1", "--modelo", "m1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("t=1 (contador mecânico)", r.stdout)
        self.assertEqual(_cli(self.tmp, "atual", "--sessao", "nao-existe").returncode, 1)
        self.assertEqual(_cli(self.tmp, "proximo", "--sessao", "../x").returncode, 2)
        r = _cli(self.tmp, "sub", "--sessao", "cli-1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("t=1.sub", r.stdout)


class TestCorrupcao(_Base):
    def test_json_invalido_reinicia_com_marca(self):
        self._corromper("c1", "{quebrado")
        self.assertIn("t=1 (contador mecânico; contador reiniciado)", turno.proximo("c1"))

    def test_tipos_invalidos_reiniciam(self):
        for conteudo in ('{"t": -4}', '{"t": "7"}', '{"t": true}', "[1, 2]", "{}", ""):
            with self.subTest(conteudo=conteudo):
                self._corromper("c2", conteudo)
                self.assertIn("contador reiniciado", turno.proximo("c2"))

    def test_depois_do_reinicio_segue_normal(self):
        self._corromper("c3", "lixo")
        turno.proximo("c3")
        self.assertIn("t=2 (contador mecânico)", turno.proximo("c3"))

    def test_atual_e_sub_recusam_corrompido(self):
        self._corromper("c4", "lixo")
        with self.assertRaises(turno.SemContador):
            turno.atual("c4")
        with self.assertRaises(turno.SemContador):
            turno.subagente("c4")
        self.assertIsNone(turno.atual_da_sessao("c4"))

    def test_cli_corrompido_sai_1_e_gancho_segue(self):
        self._corromper("c5", "lixo")
        self.assertEqual(_cli(self.tmp, "atual", "--sessao", "c5").returncode, 1)
        r = _cli(self.tmp, "hook", entrada=json.dumps({"session_id": "c5"}))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Contador reiniciado", json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_arquivo_ilegivel_nao_quebra_o_gancho(self):
        Path(self.tmp, "d1.json").mkdir()  # o caminho existe, mas não é arquivo
        r = _cli(self.tmp, "hook", entrada=json.dumps({"session_id": "d1"}))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")


class TestConcorrencia(_Base):
    def test_threads_nao_repetem_nem_pulam(self):
        resultados: list[int] = []
        trava = threading.Lock()

        def trabalhar():
            for _ in range(25):
                n = _t(turno.proximo("par-t"))
                with trava:
                    resultados.append(n)

        ths = [threading.Thread(target=trabalhar) for _ in range(8)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        self.assertEqual(sorted(resultados), list(range(1, 201)))
        self.assertIn("t=200 (contador mecânico)", turno.atual("par-t"))

    def test_processos_nao_repetem_nem_pulam(self):
        procs = [subprocess.Popen([sys.executable, "-I", str(TURNO_PY), "proximo", "--sessao", "par-p"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                  env=_env(self.tmp)) for _ in range(30)]
        numeros = []
        for p in procs:
            out, err = p.communicate(timeout=60)
            self.assertEqual(p.returncode, 0, err)
            numeros.append(_t(out))
        self.assertEqual(sorted(numeros), list(range(1, 31)))


class TestHook(_Base):
    def _gancho(self, payload, **extra) -> subprocess.CompletedProcess:
        entrada = payload if isinstance(payload, str) else json.dumps(payload)
        return _cli(self.tmp, "hook", entrada=entrada, **extra)

    def _contexto(self, r) -> str:
        self.assertEqual(r.returncode, 0, r.stderr)
        dados = json.loads(r.stdout)
        self.assertEqual(dados["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        return dados["hookSpecificOutput"]["additionalContext"]

    def test_primeiro_turno_pede_prontidao_sem_linha_t(self):
        ctx = self._contexto(self._gancho({"session_id": "h1", "transcript_path": "/nao/existe"}))
        self.assertIn("1ª resposta desta sessão", ctx)
        self.assertIn("bloco de prontidão", ctx)
        self.assertNotIn("t=1 (", ctx)

    def test_segundo_turno_injeta_cabecalho_pronto(self):
        self._gancho({"session_id": "h2"})
        ctx = self._contexto(self._gancho({"session_id": "h2"}))
        self.assertIn("Cabeçalho deste turno: agata · modelo não verificado · t=2 (contador mecânico) · ", ctx)
        self.assertRegex(ctx, HORA_RE)
        self.assertIn("--sessao h2", ctx)

    def test_usa_session_id_do_stdin_antes_do_ambiente(self):
        self._contexto(self._gancho({"session_id": "do-stdin"}, CLAUDE_SESSION_ID="do-env"))
        self.assertTrue(Path(self.tmp, "do-stdin.json").exists())
        self.assertFalse(Path(self.tmp, "do-env.json").exists())

    def test_cai_no_ambiente_sem_session_id(self):
        self._contexto(self._gancho({}, CLAUDE_SESSION_ID="do-env2"))
        self.assertTrue(Path(self.tmp, "do-env2.json").exists())

    def test_sem_sessao_nao_escreve_e_sai_0(self):
        r = self._gancho({})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")
        self.assertEqual(list(Path(self.tmp).iterdir()), [])

    def test_entrada_invalida_nao_quebra(self):
        for entrada in ("{quebrado", "[]", "", "null", '{"session_id": 7}', '{"session_id": "../x"}'):
            with self.subTest(entrada=entrada):
                r = self._gancho(entrada)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout, "")

    def _transcrito(self, nome: str, modelos: list[str]) -> str:
        caminho = Path(self.tmp, nome)
        linhas = [json.dumps({"type": "user", "message": {"role": "user", "content": "oi"}})]
        linhas += [json.dumps({"type": "assistant", "message": {"model": m, "role": "assistant"}}) for m in modelos]
        caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        return str(caminho)

    def test_modelo_medido_no_transcrito(self):
        tr = self._transcrito("tr.jsonl", ["claude-haiku-5-5"])
        self._gancho({"session_id": "tr1", "transcript_path": tr})
        ctx = self._contexto(self._gancho({"session_id": "tr1", "transcript_path": tr}))
        self.assertIn("agata · claude-haiku-5-5 · t=2 (contador mecânico)", ctx)

    def test_modelo_sintetico_e_ignorado(self):
        tr = self._transcrito("sint.jsonl", ["<synthetic>"])
        self._gancho({"session_id": "sn1", "transcript_path": tr})
        ctx = self._contexto(self._gancho({"session_id": "sn1", "transcript_path": tr}))
        self.assertIn("modelo não verificado", ctx)

    def test_modelo_do_payload_tem_prioridade(self):
        tr = self._transcrito("pri.jsonl", ["claude-haiku-5-5"])
        self._gancho({"session_id": "pm1", "model": "claude-opus-x", "transcript_path": tr})
        ctx = self._contexto(self._gancho({"session_id": "pm1", "model": "claude-opus-x", "transcript_path": tr}))
        self.assertIn("agata · claude-opus-x · t=2", ctx)

    def test_linha_do_gancho_passa_no_verificador_de_cabecalho(self):
        self._gancho({"session_id": "vc1"})
        ctx = self._contexto(self._gancho({"session_id": "vc1"}))
        linha = ctx.split("Cabeçalho deste turno: ", 1)[1].split("\n", 1)[0]
        self.assertEqual(verificar_cabecalho.verificar(linha), [], linha)
        self.assertEqual(verificar_cabecalho.verificar(turno.subagente("vc1", "claude-haiku-5-5")), [])


class TestAuditoria(_Base):
    def setUp(self):
        super().setUp()
        # a auditoria importa detector_estado_sem_prova.py do próprio diretório; rodada como script, o Python já o põe no path
        sys.path.insert(0, str(AUDITORIA.parent))
        spec = importlib.util.spec_from_file_location("auditoria_turno_teste", AUDITORIA)
        self.aud = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.aud)

    @staticmethod
    def _cab(n, sufixo: str = "") -> str:
        return (f"agata · claude-haiku-5-5 · t={n}{sufixo} (contador mecânico) · "
                "12/11/2026 09:20 -03 (relógio da Máquina)\n\nResultado.")

    def _contar(self, sessao: str, vezes: int) -> None:
        for _ in range(vezes):
            turno.proximo(sessao)

    def test_divergencia_acusa_como_aviso(self):
        self._contar("au-1", 3)
        avisos = self.aud.divergencia_turno(self._cab(2), "au-1")
        self.assertEqual(len(avisos), 1)
        self.assertIn("não bloqueia", avisos[0])

    def test_igual_ao_contador_nao_acusa(self):
        self._contar("au-1", 3)
        self.assertEqual(self.aud.divergencia_turno(self._cab(3), "au-1"), [])

    def test_subagente_compara_pelo_numero(self):
        self._contar("au-1", 3)
        self.assertEqual(self.aud.divergencia_turno(self._cab(3, ".sub"), "au-1"), [])
        self.assertEqual(len(self.aud.divergencia_turno(self._cab(2, ".sub"), "au-1")), 1)

    def test_sem_sessao_sem_contador_ou_sem_t_nao_acusa(self):
        self._contar("au-1", 3)
        self.assertEqual(self.aud.divergencia_turno(self._cab(2), None), [])
        self.assertEqual(self.aud.divergencia_turno(self._cab(2), "sessao-sem-contador"), [])
        prontidao = ("agata · modelo: x · sync: não verificado · lacuna: y · 12/11/2026 09:20 -03 (relógio da Máquina)\n"
                     "Última entrada: (1) x\npronto.")
        self.assertEqual(self.aud.divergencia_turno(prontidao, "au-1"), [])

    def _verificar(self, texto: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(AUDITORIA), "--verificar", *args], input=texto,
                              capture_output=True, text=True, env=_env(self.tmp), timeout=60)

    def test_cli_divergencia_nao_bloqueia(self):
        self._contar("au-2", 3)
        r = self._verificar(self._cab(2), "--sessao", "au-2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("aviso (não bloqueia)", r.stdout)
        self.assertIn("nada a bloquear", r.stdout)

    def test_cli_sem_divergencia_nada_a_apontar(self):
        self._contar("au-3", 3)
        r = self._verificar(self._cab(3), "--sessao", "au-3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("aviso", r.stdout)
        self.assertIn("nada a apontar", r.stdout)

    def test_cli_sem_sessao_fica_como_antes(self):
        r = self._verificar(self._cab(2))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("aviso", r.stdout)

    def test_cli_argumento_desconhecido_sai_2(self):
        self.assertEqual(self._verificar("x", "--foo").returncode, 2)


class TestCanonEGateway(unittest.TestCase):
    def test_gateway_usa_o_mesmo_rotulo(self):
        texto = (RAIZ / "redesign" / "router" / "seth_gateway.py").read_text(encoding="utf-8")
        self.assertIn("(contador mecânico)", texto)
        self.assertIn("len(auditoria_turno._turnos(msgs)[0]) + 1", texto)

    def test_canon_aponta_o_contador(self):
        for arq in ("REGRAS.md", "PROTOCOLOS.md", "AGENTS.md"):
            with self.subTest(arq=arq):
                self.assertIn("scripts/turno.py", (RAIZ / arq).read_text(encoding="utf-8"))
        for arq in ("REGRAS.md", "PROTOCOLOS.md"):
            with self.subTest(arq=arq):
                self.assertIn("t=<n>.sub", (RAIZ / arq).read_text(encoding="utf-8"))

    def test_gancho_registrado_e_sessao_preservada(self):
        cfg = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
        comandos = [h["command"] for g in cfg["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        self.assertTrue(any(c.endswith('scripts/turno.py" hook') for c in comandos), comandos)
        self.assertIn("SessionStart", cfg["hooks"])

    def test_criterios_da_spec_batem_com_o_acceptance(self):
        spec = (RAIZ / "redesign" / "router" / "spec" / "spec.md").read_text(encoding="utf-8")
        criterios_md = {l[6:].strip() for l in spec.splitlines() if l.startswith("- [ ] ") or l.startswith("- [x] ")}
        acc = json.loads((RAIZ / "redesign" / "router" / "spec" / "acceptance.json").read_text(encoding="utf-8"))
        self.assertEqual(criterios_md, {item["criterion"] for item in acc})

    def test_comandos_da_spec_apontam_para_testes_existentes(self):
        acc = json.loads((RAIZ / "redesign" / "router" / "spec" / "acceptance.json").read_text(encoding="utf-8"))
        for item in acc:
            cmd = item["command"]
            if cmd[1] == "scripts/testar_turno.py" and len(cmd) == 3:
                classe, metodo = cmd[2].split(".")
                with self.subTest(teste=cmd[2]):
                    self.assertTrue(hasattr(globals()[classe], metodo))


if __name__ == "__main__":
    unittest.main()
