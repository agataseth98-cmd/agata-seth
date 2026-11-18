"""Testes do L8 (18/11/2026): memória do agente, ledger de desfechos das skills e limiar de 51%.

Os critérios AC1 a AC13 vêm da spec L8 (pasta roteador-capacidade-17-11/l8-agentes-skills, fora do repositório); este arquivo está listado em redesign/router/spec/spec.md (Código). Sem rede, sem provedor.
Todo caminho é temporário: HOME aponta para uma pasta de teste; AGATA_CACHE_CONSELHO também. Nada toca
~/.local/share/agata real, e a pasta .agents/skills do repositório é trocada por uma temporária.
Rodar: pytest -q redesign/router/test_skills_ledger.py
"""
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROUTER = Path(__file__).resolve().parent
REPO = ROUTER.parents[1]
sys.path.insert(0, str(ROUTER))

import skills_ledger as sl  # noqa: E402

CACHE = ROUTER / "cache_conselho.py"
AGENTES = REPO / ".claude" / "agents"
# Só leitura no papel: quem registra e anota é o coordenador (decisão do orquestrador, 18/11/2026).
SO_LEITURA = {"agata-revisor", "agata-inov-critico", "agata-inov-pesquisa",
              "agata-pesq-painel", "agata-pesq-processo", "agata-pesq-rea"}
# Montado em tempo de execução: o arquivo de teste não contém segredo literal.
SEGREDO = "sk-ant-api03-" + "A" * 40
# Roda main() de skills_ledger com a pasta de skills trocada; uma lista de argv por chamada.
RUNNER = ("import json, sys; sys.path.insert(0, sys.argv[1]); import skills_ledger as sl; "
          "from pathlib import Path; sl.SKILLS = Path(sys.argv[2]); "
          "sys.exit(max(sl.main(a) for a in json.loads(sys.argv[3])))")


class _HomeTemporario(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.raiz = Path(tmp.name)
        self.home = self.raiz / "home"
        self.home.mkdir()
        self.agata = self.home / ".local" / "share" / "agata"
        self.cache_dir = self.agata / "cache-conselho"
        self.memoria = self.agata / "agentes" / "agata-dev" / "memoria.jsonl"
        self.ledger = self.agata / "skills-ledger"
        patch_env = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        patch_env.start()
        self.addCleanup(patch_env.stop)

    def _env_filho(self, caminho=None) -> dict:
        env = {"HOME": str(self.home), "PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"}
        if caminho is not None:
            env["AGATA_CACHE_CONSELHO"] = str(caminho)
        return env

    def _cc(self, *args, caminho=None):
        return subprocess.run([sys.executable, str(CACHE), *args], env=self._env_filho(caminho),
                              capture_output=True, text=True, encoding="utf-8")


class TestMemoriaAgente(_HomeTemporario):
    def test_memoria_agente_fora_da_pasta_do_cache(self):
        r = self._cc("anotar", "--autor", "agata-dev", "--tipo", "nota", "lição de teste", caminho=self.memoria)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.memoria.exists())
        self.assertNotIn(self.cache_dir, self.memoria.parents)
        self.assertFalse((self.cache_dir / "cache.jsonl").exists())

    def test_memoria_agente_sobrevive_ao_reinicio_do_cache(self):
        self.assertEqual(self._cc("anotar", "--autor", "agata-dev", "lição um", caminho=self.memoria).returncode, 0)
        self.assertEqual(self._cc("anotar", "--autor", "agata-dev", "lição dois", caminho=self.memoria).returncode, 0)
        # uso normal do cache, no caminho padrão (sem variável): é a pasta que reinicia
        self.assertEqual(self._cc("anotar", "--autor", "Seth", "entrada do cache").returncode, 0)
        self.assertTrue(self.cache_dir.exists())
        antes = self.memoria.read_bytes()
        shutil.rmtree(self.cache_dir)  # reinício simulado (M4)
        self.assertFalse(self.cache_dir.exists())
        self.assertEqual(self.memoria.read_bytes(), antes)
        v = self._cc("verificar", caminho=self.memoria)
        self.assertEqual(v.returncode, 0, v.stdout)
        self.assertIn("OK", v.stdout)
        lidas = self._cc("ler", "--n", "20", "--autor", "agata-dev", caminho=self.memoria)
        self.assertIn("lição um", lidas.stdout)
        self.assertIn("lição dois", lidas.stdout)

    def test_cache_conselho_aceita_caminho_por_ambiente(self):
        custom = self.raiz / "outro" / "lugar" / "cache.jsonl"
        r = self._cc("anotar", "--autor", "agata-dev", "nota por ambiente", caminho=custom)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(custom.exists())
        self.assertIn("nota por ambiente", self._cc("ler", caminho=custom).stdout)
        v = self._cc("verificar", caminho=custom)
        self.assertEqual(v.returncode, 0)
        self.assertIn("OK", v.stdout)
        self.assertFalse(self.cache_dir.exists())

    def test_memoria_agente_recusa_segredo(self):
        r = self._cc("anotar", "--autor", "agata-dev", "--tipo", "nota", f"lição com chave {SEGREDO}",
                     caminho=self.memoria)
        self.assertEqual(r.returncode, 2)
        self.assertIn("segredo", r.stderr)
        self.assertFalse(self.memoria.exists())

    def test_definicoes_de_agente_tem_memoria_e_registro(self):
        arquivos = sorted(AGENTES.glob("agata-*.md"))
        self.assertGreaterEqual(len(arquivos), 10)
        for arq in arquivos:
            stem = arq.stem
            texto = arq.read_text(encoding="utf-8")
            with self.subTest(agente=stem):
                self.assertTrue(texto.startswith("---"))
                self.assertIn(f"name: {stem}\n", texto)
                self.assertIn(f"AGATA_CACHE_CONSELHO=$HOME/.local/share/agata/agentes/{stem}/memoria.jsonl", texto)
                self.assertIn("cache_conselho.py ler --n 20", texto)
                self.assertIn(f"cache_conselho.py anotar --autor {stem}", texto)
                self.assertIn("skills_ledger.py registrar", texto)
                if stem in SO_LEITURA:
                    self.assertIn("--por coordenador", texto)


class TestLedger(_HomeTemporario):
    def setUp(self):
        super().setUp()
        self.skills = self.raiz / "skills"
        for nome in ("agata-fluxo", "agata-painel"):
            (self.skills / nome).mkdir(parents=True)
            (self.skills / nome / "SKILL.md").write_text("# teste\n", encoding="utf-8")
        patch_skills = mock.patch.object(sl, "SKILLS", self.skills)
        patch_skills.start()
        self.addCleanup(patch_skills.stop)
        self.arq = self.ledger / "agata-fluxo.jsonl"

    def _registrar(self, skill, erro, solucao, acertos, falhas, prefixo):
        ids = []
        for i in range(acertos + falhas):
            ids.append(sl.registrar(skill=skill, erro=erro, solucao=solucao,
                                    resultado="acerto" if i < acertos else "falha",
                                    agente="agata-dev", tarefa=f"{prefixo}-{i:03d}"))
        return ids

    def _conferir(self, ids):
        for id_ in ids:
            sl.conferir(ref=id_, por="coordenador")

    def _linhas(self, arq=None):
        return (arq or self.arq).read_text(encoding="utf-8").splitlines()

    def test_registrar_grava_desfecho_pendente(self):
        id_ = sl.registrar(skill="agata-fluxo", erro="erro-x", solucao="sol-y", resultado="acerto",
                           agente="agata-dev", tarefa="t-1")
        self.assertRegex(id_, r"^[0-9a-f]{16}$")
        linhas = self._linhas()
        self.assertEqual(len(linhas), 1)
        reg = json.loads(linhas[0])
        self.assertEqual((reg["tipo"], reg["id"], reg["resultado"]), ("desfecho", id_, "acerto"))
        self.assertEqual(stat.S_IMODE(os.stat(self.arq).st_mode), 0o600)
        rows, pendentes = sl.recalcular()
        self.assertEqual(pendentes, 1)
        self.assertEqual(rows[0]["usos"], 0)
        self.assertEqual(rows[0]["status"], "não comprovada")

    def test_registrar_recusa_skill_inexistente_slug_e_duplicata(self):
        base = dict(erro="erro-x", solucao="sol-y", resultado="acerto", agente="agata-dev", tarefa="t-1")
        with self.assertRaises(sl.LedgerRecusado):
            sl.registrar(skill="skill-fantasma", **base)
        for ruim in ("Agata Fluxo", "../agata-fluxo", "a/b", "-x", ""):
            with self.subTest(skill=ruim), self.assertRaises(sl.LedgerRecusado):
                sl.registrar(**{**base, "skill": ruim})
        for campo, ruim in (("erro", "Erro Ruim"), ("solucao", "sol/x"), ("agente", ""), ("tarefa", "t 1")):
            with self.subTest(campo=campo), self.assertRaises(sl.LedgerRecusado):
                sl.registrar(**{**base, "skill": "agata-fluxo", campo: ruim})
        sl.registrar(skill="agata-fluxo", **base)
        with self.assertRaises(sl.LedgerRecusado):
            sl.registrar(skill="agata-fluxo", **base)
        with self.assertRaises(sl.LedgerRecusado):
            sl.registrar(**{**base, "skill": "agata-fluxo", "resultado": "falha"})  # mesma chave, outro desfecho
        self.assertEqual(len(self._linhas()), 1)

    def test_conferir_so_acrescenta_e_exige_registro(self):
        id_ = sl.registrar(skill="agata-fluxo", erro="erro-x", solucao="sol-y", resultado="acerto",
                           agente="agata-dev", tarefa="t-1")
        antes = self.arq.read_bytes()
        with self.assertRaises(sl.LedgerRecusado):
            sl.conferir(ref="0" * 16, por="coordenador")
        self.assertEqual(self.arq.read_bytes(), antes)
        sl.conferir(ref=id_, por="coordenador")
        depois = self.arq.read_bytes()
        self.assertTrue(depois.startswith(antes))
        novas = depois[len(antes):].splitlines()
        self.assertEqual(len(novas), 1)
        reg = json.loads(novas[0])
        self.assertEqual((reg["tipo"], reg["ref"], reg["por"]), ("conferencia", id_, "coordenador"))
        with self.assertRaises(sl.LedgerRecusado):
            sl.conferir(ref=id_, por="coordenador")  # já conferido: não acrescenta de novo
        self.assertEqual(self.arq.read_bytes(), depois)

    def test_recalculo_limiar_51_e_n_10(self):
        casos = [("e-51", "s-51", 51, 49, "não comprovada"),
                 ("e-52", "s-52", 52, 48, "comprovada"),
                 ("e-9", "s-9", 9, 0, "não comprovada"),
                 ("e-6", "s-6", 6, 4, "comprovada")]
        for erro, sol, acertos, falhas, _ in casos:
            self._conferir(self._registrar("agata-fluxo", erro, sol, acertos, falhas, f"t-{erro}"))
        rows, _ = sl.recalcular()
        por = {(r["erro"], r["solucao"]): r for r in rows}
        for erro, sol, acertos, falhas, esperado in casos:
            with self.subTest(caso=f"{acertos} de {acertos + falhas}"):
                r = por[(erro, sol)]
                self.assertEqual((r["usos"], r["acertos"]), (acertos + falhas, acertos))
                self.assertEqual(r["status"], esperado)

    def test_recalculo_ignora_nao_conferido(self):
        ids = self._registrar("agata-fluxo", "e-10", "s-10", 10, 0, "t-e10")
        self._conferir(ids[:9])
        rows, pendentes = sl.recalcular()
        self.assertEqual((rows[0]["usos"], rows[0]["acertos"], pendentes), (9, 9, 1))
        self.assertEqual(rows[0]["status"], "não comprovada")
        self._conferir(ids[9:])
        rows, pendentes = sl.recalcular()
        self.assertEqual((rows[0]["usos"], pendentes, rows[0]["status"]), (10, 0, "comprovada"))

    def test_recalculo_mantem_nao_comprovada_na_saida(self):
        self._conferir(self._registrar("agata-fluxo", "e-30", "s-30", 3, 7, "t-e30"))
        rows, _ = sl.recalcular()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "não comprovada")
        self.assertAlmostEqual(rows[0]["taxa"], 30.0)
        saida = io.StringIO()
        with redirect_stdout(saida):
            self.assertEqual(sl.main(["recalcular"]), 0)
        self.assertIn("agata-fluxo | e-30 | s-30 | 10 | 3 | 30.0% | não comprovada", saida.getvalue())

    def test_recalculo_falha_com_linha_invalida(self):
        sl.registrar(skill="agata-fluxo", erro="erro-x", solucao="sol-y", resultado="acerto",
                     agente="agata-dev", tarefa="t-1")
        with self.arq.open("ab") as f:
            f.write(b"{isto nao e json\n")
        with self.assertRaises(sl.LedgerInvalido):
            sl.recalcular()
        with self.assertRaises(sl.LedgerInvalido):
            sl.registrar(skill="agata-fluxo", erro="erro-x", solucao="sol-y", resultado="falha",
                         agente="agata-dev", tarefa="t-2")
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            rc = sl.main(["recalcular"])
        self.assertEqual(rc, 2)
        self.assertEqual(saida.getvalue(), "")  # sem tabela parcial
        self.assertIn("linha 2", erro.getvalue())
        self.assertEqual(len(self._linhas()), 2)  # nada foi gravado sobre o ledger ruim

    def test_registrar_concorrente_nao_perde_linha(self):
        env = self._env_filho()
        procs = []
        for p in range(8):
            argvs = [["registrar", "--skill", "agata-fluxo", "--erro", "e-conc", "--solucao", "s-conc",
                      "--resultado", "acerto", "--agente", f"agente-{p}", "--tarefa", f"t-p{p}-{i}"]
                     for i in range(5)]
            procs.append(subprocess.Popen([sys.executable, "-c", RUNNER, str(ROUTER), str(self.skills),
                                           json.dumps(argvs)], env=env, stdout=subprocess.DEVNULL,
                                          stderr=subprocess.PIPE, text=True))
        for pr in procs:
            _, err = pr.communicate(timeout=120)
            self.assertEqual(pr.returncode, 0, err)
        linhas = self._linhas()
        self.assertEqual(len(linhas), 40)
        self.assertEqual(len({json.loads(l)["id"] for l in linhas}), 40)
        rows, pendentes = sl.recalcular()
        self.assertEqual(pendentes, 40)


if __name__ == "__main__":
    unittest.main()
