#!/usr/bin/env python3
"""Testes do progresso do CI local (Regra 0, decisão do Humano 18/11/2026).

Cada linha OK/FALHA de scripts/ci_sdd_local.sh traz "[n/total · tempo]". O total é contado
no próprio script (passada sem executar comandos), nunca escrito à mão. Estes testes conferem:
o formato do marcador, o formato da linha OK/FALHA (prefixo preservado), e que o total contado
bate com as chamadas `passo` que o código realmente tem (inclusive as do laço `for`).
Não roda o CI inteiro: só a passada de contagem (CI_SO_CONTAR=1), que não executa passo nenhum.
"""
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CI = RAIZ / "scripts" / "ci_sdd_local.sh"


def _ambiente(extra=None):
    # GIT_* herdado de um hook apontaria o script para outro repositório.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(extra or {})
    return env


def _chamadas_no_codigo():
    """Conta as chamadas `passo "..."` do código: as de fora de laço valem 1; as de dentro de
    `for ... in <palavras>; do ... done` valem <palavras> vezes. Não usa o número do script."""
    total = 0
    bloco = None  # [palavras do laço, chamadas dentro do laço]
    for linha in CI.read_text(encoding="utf-8").splitlines():
        s = linha.strip()
        m = re.match(r"^for \w+ in (.+); do$", s)
        if m:
            bloco = [len(m.group(1).split()), 0]
            continue
        if s == "done" and bloco is not None:
            total += bloco[0] * bloco[1]
            bloco = None
            continue
        if re.match(r'^passo "', s):
            if bloco is None:
                total += 1
            else:
                bloco[1] += 1
    if bloco is not None:
        raise AssertionError("laço for sem done em ci_sdd_local.sh")
    return total


class MarcadorTests(unittest.TestCase):
    def _marca(self, n, total, seg):
        r = subprocess.run(
            ["bash", "-c", 'source "$1"; _ci_marca "$2" "$3" "$4"', "bash", str(CI), str(n), str(total), str(seg)],
            capture_output=True, text=True, env=_ambiente(), check=True,
        )
        return r.stdout.strip()

    def test_minutos_e_segundos_com_dois_digitos(self):
        self.assertEqual(self._marca(12, 92, 64), "[12/92 · 1m04s]")

    def test_zero_segundos(self):
        self.assertEqual(self._marca(1, 3, 0), "[1/3 · 0m00s]")

    def test_mais_de_uma_hora_mantem_minutos(self):
        self.assertEqual(self._marca(90, 92, 3725), "[90/92 · 62m05s]")


class LinhaDePassoTests(unittest.TestCase):
    def test_tempo_e_o_do_fim_do_passo(self):
        # a linha sai quando o passo termina: um passo de 2 s, começando agora, tem de mostrar ~2 s (e não 0 s)
        script = (
            'source "$1"\n'
            'TMP="$(mktemp -d)"; FALHAS=0; CI_TOTAL=1; CI_INICIO="$(date +%s)"\n'
            'passo "lento" sleep 2\n'
            'rm -rf "$TMP"\n'
        )
        r = subprocess.run(["bash", "-c", script, "bash", str(CI)], capture_output=True, text=True,
                           env=_ambiente(), check=True)
        self.assertEqual(r.stdout.splitlines()[0], "  ... [1/1] lento")  # anúncio do início (Regra 0)
        self.assertRegex(r.stdout.splitlines()[1], r"^OK    \[1/1 · 0m0[23]s\] lento$")

    def test_ok_e_falha_trazem_progresso_e_prefixo_preservado(self):
        script = (
            'source "$1"\n'
            'TMP="$(mktemp -d)"; FALHAS=0; CI_TOTAL=3; CI_INICIO=$(( $(date +%s) - 64 ))\n'
            'passo "um passo" true\n'
            'passo "outro passo" false\n'
            'passo "terceiro" true\n'
            'echo "FALHAS=$FALHAS"\n'
            'echo "PASSOS=${CI_PASSOS[*]}"\n'
            'rm -rf "$TMP"\n'
        )
        r = subprocess.run(["bash", "-c", script, "bash", str(CI)], capture_output=True, text=True,
                           env=_ambiente(), check=True)
        # o anúncio de início ("  ... [n/total] nome") sai antes de cada passo; aqui só as linhas de resultado
        linhas = [l for l in r.stdout.splitlines() if not l.startswith("  ... ")]
        # o tempo pode virar 1m05s se a fronteira do segundo cair no meio da execução
        self.assertRegex(linhas[0], r"^OK    \[1/3 · 1m0[45]s\] um passo$")
        self.assertRegex(linhas[1], r"^FALHA \[2/3 · 1m0[45]s\] outro passo$")
        self.assertRegex(linhas[-3], r"^OK    \[3/3 · 1m0[45]s\] terceiro$")
        self.assertIn("FALHAS=1", linhas)
        self.assertIn("PASSOS=um passo|1 outro passo|0 terceiro|1", linhas)


class ContagemTests(unittest.TestCase):
    def test_total_bate_com_as_chamadas_do_codigo(self):
        esperado = _chamadas_no_codigo()
        self.assertGreater(esperado, 50, "a conta do código não pode dar um número trivial")
        with tempfile.TemporaryDirectory() as d:
            env = _ambiente({
                "CI_SO_CONTAR": "1",
                "AGATA_CI_DIR": d,
                # a contagem não executa o pytest; só precisa de um valor não vazio
                "PYTEST": os.environ.get("PYTEST") or sys.executable,
            })
            r = subprocess.run(["bash", str(CI)], capture_output=True, text=True, env=env,
                               cwd=str(RAIZ), timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(int(r.stdout.strip()), esperado)
            self.assertFalse((pathlib.Path(d) / "ultimo.json").exists(),
                             "a passada de contagem não grava o resumo do CI")

    def test_laco_conta_cada_iteracao(self):
        # o laço "for c in ..." do script tem duas chamadas por item: a conta tem de multiplicar
        texto = CI.read_text(encoding="utf-8")
        m = re.search(r"^for \w+ in (.+); do$", texto, re.M)
        self.assertIsNotNone(m, "o script deve ter um laço for com lista de componentes")
        palavras = len(m.group(1).split())
        self.assertGreaterEqual(palavras, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
