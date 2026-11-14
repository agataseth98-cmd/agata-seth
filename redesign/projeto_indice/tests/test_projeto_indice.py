"""Testes do componente projeto-indice (spec: redesign/projeto_indice/spec/spec.md).

Um teste por critério de redesign/projeto_indice/spec/acceptance.json. Os que leem o índice e o ESTADO
só passam no estado aplicado (depois do par assinado). Os do gerador usam uma raiz temporária.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
COMPONENTE = RAIZ / "redesign" / "projeto_indice"
sys.path.insert(0, str(COMPONENTE))
import teto  # noqa: E402
import verificar_destinos  # noqa: E402


def _carregar(nome: str, caminho: Path):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


gerar_estado = _carregar("gerar_estado", RAIZ / "scripts" / "gerar_estado.py")
CFG = json.loads((COMPONENTE / "destinos.json").read_text(encoding="utf-8"))


def _secao(texto: str, titulo: str) -> str:
    partes = re.split(rf"^## {re.escape(titulo)}\s*$", texto, maxsplit=1, flags=re.M)
    return partes[1].split("\n## ", 1)[0] if len(partes) == 2 else ""


def _sem_acento(t: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


class TetoTests(unittest.TestCase):
    def test_projeto_cabe_no_teto(self):
        dados = (RAIZ / "PROJETO.md").read_bytes()
        self.assertLessEqual(len(dados), 6000)
        ok, _ = teto.checar(dados)
        self.assertTrue(ok)

    def test_acima_do_teto_recusa_e_diz_para_onde_vai(self):
        ok, texto = teto.checar(b"x" * (teto.TETO_BYTES + 1))
        self.assertFalse(ok)
        for destino in ("ESTADO.md", "PROTOCOLOS.md", "extras/arquivo/", "extras/projeto-detalhe/"):
            self.assertIn(destino, texto)
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "PROJETO.md"
            caminho.write_bytes(b"x" * (teto.TETO_BYTES + 1))
            r = subprocess.run([sys.executable, str(COMPONENTE / "teto.py"), str(caminho)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)

    def test_pre_commit_bloqueia_pelo_teto(self):
        hook = (RAIZ / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        bloco = hook.split("# Teto do PROJETO.md", 1)[1].split("\nfi\n", 1)[0]
        self.assertIn("teto.py", bloco)
        self.assertIn("exit 1", bloco)
        self.assertIn("git show :PROJETO.md", bloco)


class OndeTests(unittest.TestCase):
    def test_todo_caminho_do_onde_encontrar_existe(self):
        texto = (RAIZ / "PROJETO.md").read_text(encoding="utf-8")
        onde = _secao(texto, "Onde encontrar")
        caminhos = []
        for linha in onde.splitlines():
            if not linha.startswith("|") or linha.startswith("|---") or "Onde está" in linha:
                continue
            celulas = linha.split("|")
            if len(celulas) < 4:
                continue
            for token in re.findall(r"`([^`\s]+)`", celulas[2]):
                if re.fullmatch(r"[\w./-]+\.(?:md|py|json|txt|sh)", token):
                    caminhos.append(token)
        self.assertGreaterEqual(len(caminhos), 10)
        faltando = [c for c in caminhos if not (RAIZ / c).exists()]
        self.assertEqual(faltando, [])


class DestinosTests(unittest.TestCase):
    def test_todo_paragrafo_que_saiu_existe_no_destino(self):
        achados = [a for a in verificar_destinos.verificar(RAIZ) if a.startswith(("(c)", "(d)"))]
        self.assertEqual(achados, [])

    def test_arquivo_de_historico_tem_o_sha_registrado(self):
        arquivo = RAIZ / CFG["historico"]["arquivo"]
        self.assertEqual(hashlib.sha256(arquivo.read_bytes()).hexdigest(), CFG["historico"]["sha256"])
        achados = [a for a in verificar_destinos.verificar(RAIZ) if a.startswith("(a)")]
        self.assertEqual(achados, [])

    def test_toda_secao_tem_destino_e_nenhuma_sobra(self):
        achados = [a for a in verificar_destinos.verificar(RAIZ) if a.startswith("(b)")]
        self.assertEqual(achados, [])

    def test_titulo_movido_continua_existindo_no_destino(self):
        """Ponteiro `PROTOCOLOS.md, "<título>"` só resolve se o título existir como seção no destino."""
        for nome, regra in CFG["secoes"].items():
            if regra.get("indice") is not None or nome.startswith("__"):
                continue
            destino = RAIZ / regra["padrao"]
            if destino.name == "PROJETO_REFERENCIA.md":
                continue
            titulos = re.findall(r"^## (.+?)\s*$", destino.read_text(encoding="utf-8"), flags=re.M)
            self.assertIn(_sem_acento(nome), [_sem_acento(t) for t in titulos], f"{nome!r} sem seção em {regra['padrao']}")


class EstadoTests(unittest.TestCase):
    def test_gerador_e_deterministico(self):
        self.assertEqual(gerar_estado.renderizar(RAIZ), gerar_estado.renderizar(RAIZ))
        r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "gerar_estado.py"), "--verificar"],
                           capture_output=True, text=True, cwd=RAIZ)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_estado_sem_data_nem_sha(self):
        texto = (RAIZ / "ESTADO.md").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"\b[0-9a-f]{40}\b", texto))
        self.assertIsNone(re.search(r"(?i)(gerado|escrito|atualizado) em", texto.split("-->", 1)[1]))
        self.assertIsNone(re.search(r"(?i)\bcommit\s+[0-9a-f]{7,}", texto))

    def test_portas_e_modelos_vivos(self):
        texto = (RAIZ / "ESTADO.md").read_text(encoding="utf-8")
        for linha in (RAIZ / "config" / "portas-agata.txt").read_text(encoding="utf-8").splitlines():
            if linha and not linha.startswith("#") and linha.count("|") == 2:
                porta = linha.split("|")[0].strip()
                self.assertIn(f"`{porta}`", texto)
        modelos = gerar_estado.modelos_confirmados(RAIZ)
        self.assertGreaterEqual(len(modelos), 3)
        for mid, _nota in modelos:
            self.assertIn(f"`{mid}`", texto)
        self.assertIn("A nota é a da própria tabela", texto)

    def test_servicos_com_porta_na_secao(self):
        texto = (RAIZ / "ESTADO.md").read_text(encoding="utf-8")
        secao = _secao(texto, "Serviços (boot)")
        self.assertTrue(secao)
        for s in gerar_estado.servicos(RAIZ):
            self.assertIn(s["unidade"], secao)
            if s["porta"] != "-":
                self.assertIn(f"(porta :{s['porta']})", secao)

    def test_unidade_fora_do_manifesto_e_acusada(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "config").mkdir()
            (raiz / "redesign" / "systemd").mkdir(parents=True)
            (raiz / "config" / "servicos-agata.txt").write_text("a.service|usuario|-|sim|fora do repo\n", encoding="utf-8")
            (raiz / "redesign" / "systemd" / "a.service").write_text("[Install]\nWantedBy=agata.target\n", encoding="utf-8")
            (raiz / "redesign" / "systemd" / "b.service").write_text("[Install]\nWantedBy=agata.target\n", encoding="utf-8")
            texto = gerar_estado.renderizar(raiz)
            self.assertIn("`b.service` — AVISO", texto)
            self.assertNotIn("`a.service` — AVISO", texto)

    def test_gerador_le_bugs_ou_aponta_a_prosa(self):
        texto = (RAIZ / "ESTADO.md").read_text(encoding="utf-8")
        self.assertIn("## Bugs e testes abertos", texto)
        self.assertIn("estado-de-fundo-12-11.md", texto)


class IntegracaoTests(unittest.TestCase):
    def test_p9_carrega_o_manifesto(self):
        esperado = [s["unidade"] for s in gerar_estado.servicos(RAIZ)
                    if s["escopo"] == "usuario" and s["p9"] == "sim"]
        r = subprocess.run(
            ["bash", "-c", "source scripts/perimetro/p09_servicos_declarados.sh; p9_carregar_fonte; "
                           "printf '%s\\n' \"${P9_UNIDADES_USUARIO[@]}\""],
            capture_output=True, text=True, cwd=RAIZ)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.split(), esperado)
        perimetro = (RAIZ / "scripts" / "perimetro.sh").read_text(encoding="utf-8")
        self.assertIn("p9_carregar_fonte", perimetro)
        self.assertNotIn('P9_UNIDADES_USUARIO=("seth-gateway.service"', perimetro)

    def test_painel_le_servicos_do_estado(self):
        fonte = (RAIZ / "redesign" / "painel_operacional" / "server.py").read_text(encoding="utf-8")
        trecho = fonte.split("def _lacunas_snapshot", 1)[1].split("\ndef ", 1)[0]
        self.assertIn('ROOT / "ESTADO.md"', trecho)
        self.assertNotIn('ROOT / "PROJETO.md"', trecho)
        self.assertIn("oneshot", trecho)

    def test_prompt_de_nuvem_manda_indice_e_estado(self):
        texto = (RAIZ / "PROMPT_CARREGAMENTO.md").read_text(encoding="utf-8")
        leia = next(l for l in texto.splitlines() if l.startswith("LEIA, NESTA ORDEM"))
        self.assertIn("ESTADO.md", leia)
        self.assertIn("índice", leia)
        self.assertNotIn("PROJETO.md inteiro.", leia)

    def test_regras_sem_ponteiro_para_criterio_inexistente(self):
        texto = (RAIZ / "REGRAS.md").read_text(encoding="utf-8")
        self.assertNotIn("critério de reabilitação (PROJETO)", texto)
        self.assertIn("Lacuna declarada em 12/11/2026", texto)

    def test_hidratacao_inclui_o_estado(self):
        script = (RAIZ / ".githooks" / "gerar-hidratacao.sh").read_text(encoding="utf-8")
        # O .hidrata.md é regenerado pelo pre-commit a cada commit (fora do diff); aqui confere-se o gerador.
        self.assertIn("ESTADO.md (gerado por scripts/gerar_estado.py)", script)
        self.assertNotIn("PROJETO_TETO_BYTES", script)

    def test_hidratacao_traz_mapa_de_protocolos_nao_o_texto(self):
        script = (RAIZ / ".githooks" / "gerar-hidratacao.sh").read_text(encoding="utf-8")
        self.assertIn("for _camada in FALHAS.md; do", script)
        self.assertNotIn("for _camada in PROTOCOLOS.md", script)
        estado = (RAIZ / "ESTADO.md").read_text(encoding="utf-8")
        self.assertIn("## Mapa de PROTOCOLOS (PROTOCOLOS.md, gerado)", estado)
        self.assertIn("Carregar e formatos", _secao(estado, "Mapa de PROTOCOLOS (PROTOCOLOS.md, gerado)"))

    def test_mapa_do_projeto_mantem_a_fonte_no_rotulo(self):
        mapa = _carregar("gerar_mapa_projeto", RAIZ / "scripts" / "gerar_mapa_projeto.py")
        saida = mapa.gerar((RAIZ / "PROJETO.md").read_text(encoding="utf-8"))
        self.assertIn("— PROJETO.md:", saida)
        saida_p = mapa.gerar((RAIZ / "PROTOCOLOS.md").read_text(encoding="utf-8"), nome="PROTOCOLOS.md")
        self.assertIn("— PROTOCOLOS.md:", saida_p)
        self.assertNotIn("a fonte completa é PROJETO.md", saida_p)

    def test_sessao_mostra_o_estado(self):
        r = subprocess.run(["bash", str(RAIZ / "scripts" / "sessao_claude_contexto.sh")],
                           capture_output=True, text=True, cwd=RAIZ, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Estado vivo (ESTADO.md", r.stdout)

    def test_auditoria_reconhece_numeros_do_historico_movido(self):
        fonte = (RAIZ / "redesign" / "router" / "auditoria_turno.py").read_text(encoding="utf-8")
        self.assertIn('"extras" / "arquivo" / "projeto-ate-2026-11-12.md"', fonte)
        self.assertIn('"extras" / "projeto-detalhe" / "estado-de-fundo-12-11.md"', fonte)

    def test_nenhum_ponteiro_vivo_para_secao_que_saiu(self):
        """Ponteiro `PROJETO.md, "<seção>"` em arquivo vivo só pode citar seção que ainda está no índice.

        Pula histórico (MEMÓRIAS, morno, LOG, extras/, propostas/, memoria/), o texto movido (verbatim, marcado
        em PROTOCOLOS.md e no estado de fundo) e as linhas do bloco ANCORA-SHA (texto gerado por máquina)."""
        pular_exato = {"MEMÓRIAS.md", "MEMORIAS-MORNO.md", "SETH-DIARIO.md", "redesign/LOG.md",
                       "PROCEDIMENTO_LOGIN.md", "PROJETO.md", "PROTOCOLOS.md",
                       "scripts/perimetro-sombra-referencia.sh", "scripts/atualizar_ancora_prompt.py",
                       "scripts/p8_integral.py", "redesign/projeto_indice/tests/test_projeto_indice.py"}
        pular_prefixo = ("propostas/", "memoria/", "extras/", "redesign/propostas/", "ferramentas/", ".hidrata",
                         "INDICE_MEMORIAS", "MEMORIAS-", ".git/", "__pycache__", ".claude/worktrees/")
        titulos_indice = {_sem_acento(t) for t in re.findall(r"^## (.+?)\s*$",
                                                           (RAIZ / "PROJETO.md").read_text(encoding="utf-8"), re.M)}
        padrao = re.compile(r'PROJETO(?:\.md)?(?:,| ·| )\s?\\?"([^"\\\n]{3,90})\\?"')
        padrao_verso = re.compile(r'\\?"([^"\\\n]{3,90})\\?"\s+(?:do|no)\s+PROJETO\.md')
        achados = []
        for raiz, pastas, arquivos in os.walk(RAIZ):
            pastas[:] = [p for p in pastas if p not in {".git", "__pycache__", "worktrees", ".pytest_cache"}]
            for nome in arquivos:
                caminho = Path(raiz) / nome
                rel = caminho.relative_to(RAIZ).as_posix()
                if rel in pular_exato or rel.startswith(pular_prefixo) or caminho.suffix in {".json", ".jsonl", ".png", ".pdf"}:
                    continue
                try:
                    linhas = caminho.read_text(encoding="utf-8").splitlines()
                except (UnicodeDecodeError, OSError):
                    continue
                for n, linha in enumerate(linhas, 1):
                    if "SHA do commit ANTERIOR" in linha or "ANCORA-SHA" in linha:
                        continue
                    for m in list(padrao.finditer(linha)) + list(padrao_verso.finditer(linha)):
                        titulo = _sem_acento(m.group(1))
                        if any(titulo == t or titulo.startswith(t + " ") or titulo.startswith(t + "(")
                               for t in titulos_indice):
                            continue
                        if titulo.startswith(("ancora", "memoria e hidratacao", "personalidade", "sudo", "quarentena",
                                              "decisor", "conselho", "interface", "cerebro", "maquinas", "servicos",
                                              "estado dos bugs", "plano vigente", "seguranca", "atualizacao",
                                              "memoria em duas", "ambiente", "fonte canonica",
                                              "estado de publicacao", "ferramenta embutida")):
                            achados.append(f"{rel}:{n}: {m.group(1)!r}")
        self.assertEqual(achados, [], "ponteiros para seções que saíram do índice (reapontar para o destino)")


if __name__ == "__main__":
    unittest.main()
