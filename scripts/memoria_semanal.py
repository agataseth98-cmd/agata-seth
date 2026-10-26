#!/usr/bin/env python3
"""memoria_semanal.py — Memória Canônica semanal a partir do cache do Conselho (V9 §37, M3).

Decisão do Humano em MEMÓRIAS (849): do cache do Conselho (não canônico) sai, uma vez por semana, uma
Memória Canônica; "um modelo propõe, a Máquina confere cada fato contra o cache, o Humano assina".

  1. lê as entradas do cache da janela (padrão: os 7 dias até hoje);
  2. um modelo LOCAL (padrão ollama-local/qwen3.5-9b-64k: nada sai da Máquina) escreve até 15 tópicos,
     cada um terminado pelas entradas de onde saiu: [c12] ou [c12, c15];
  3. a Máquina confere cada tópico, mecanicamente: precisa citar entrada da janela, e todo número,
     entrada "(NNN)", controle P-n e trecho `entre crases` do tópico tem de aparecer nas entradas
     citadas; o que não passa é CORTADO e listado com o motivo. Se o modelo falhar ou nada passar, a
     memória sai por extração direta (um tópico por entrada, encurtado);
  4. escreve em propostas/ o par para assinatura: `memoria-semanal-<fim>.diff` (cria
     extras/memoria-semanal/semana-<fim>.md -- fora de memoria/, que o P-3 reserva a escritor automático
     não rastreado; a v3 gravava em memoria/semanal/ e o pre-commit barrou a 1ª aplicação, 26/10) e
     `memoria-semanal-<fim>.registro.txt` (a entrada de MEMÓRIAS,
     para `aplicar.py --registro`). Nunca escreve no canon, nunca faz commit.

Quando: na janela de manutenção (12h15-13h15), tarefa `memoria-semanal` com cadência weekly em
config/janela-tarefas.txt -- pedido do Humano, 26/10/2026 ("tem que ser no horário de manutenção").

  memoria_semanal.py gerar [--ate AAAA-MM-DD] [--dias 7] [--modelo M | --sem-modelo] [--repo R]
  memoria_semanal.py --selftest
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "redesign" / "router"))
os.environ.setdefault("SETH_REPO", str(RAIZ))
MODELO = os.environ.get("AGATA_MEMORIA_SEMANAL_MODELO", "ollama-local/qwen3.5-9b-64k:latest")
PROXY = os.environ.get("AGATA_PROXY", "http://127.0.0.1:20127")
MAX_TOPICOS = 15
# Citação no fim do tópico: "[c12]" ou "[c12, c15]". Lida em duas etapas sem quantificador aninhado (o CodeQL
# apontou retrocesso exponencial na regex única da v2, PR 567): o colchete final, limitado, e depois cada parte.
# pontuação depois da citação é aceita: o 9b escreve "[c1]." e, sem isso, todo tópico dele era cortado (26/10)
_CIT_BLOCO = re.compile(r"\[([^\[\]\n]{1,80})\][\s.;:!,]*$")
_CIT_PARTE = re.compile(r"c?\s?(\d{1,6})", re.IGNORECASE)


def _citacao(t: str):
    """(início do bloco, [números]) ou None se o tópico não termina com citação válida."""
    m = _CIT_BLOCO.search(t)
    if not m:
        return None
    nums = []
    for parte in m.group(1).split(","):
        p = _CIT_PARTE.fullmatch(parte.strip())
        if not p:
            return None
        nums.append(int(p.group(1)))
    return m.start(), nums
_VERIFICAVEIS = re.compile(r"`([^`\n]+)`|\(\d{2,4}\)|\bP-\d+\b|\b\d{2,}(?:[.,:/h]\d+)*\b")


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", t)).strip().lower()


def entradas_da_janela(ate: date, dias: int) -> list[dict]:
    import cache_conselho
    ini = (ate - timedelta(days=dias - 1)).isoformat()
    fim = ate.isoformat()
    return [r for r in cache_conselho.ler(10 ** 6) if ini <= r.get("ts", "")[:10] <= fim]


def _prompt(entradas: list[dict]) -> str:
    linhas = "\n".join(f"[c{r['n']}] {r['ts'][:10]} · {r['autor']} · {r['tipo']}: {r['texto']}" for r in entradas)
    return ("Você escreve a Memória Canônica da semana do sistema Agata, em português do Brasil, a partir SÓ "
            "das entradas abaixo (o cache do Conselho). Regras: no máximo 15 tópicos, um por linha, começando "
            "com '- '; cada tópico termina com as entradas de onde saiu, assim: [c12] ou [c12, c15]; junte o "
            "que se repete; escreva na 3ª pessoa e diga de quem é a anotação quando for diário ou nota (ex.: 'A Seth "
            "anotou que...'; a Seth é tratada no feminino); não invente nada que não esteja nas entradas; não acrescente opinião; copie números, "
            "nomes de arquivo e números de entrada exatamente como estão. Responda só com os tópicos.\n\n"
            f"ENTRADAS:\n{linhas}")


def propor(entradas: list[dict], modelo: str = MODELO, timeout: float = 300) -> str:
    sys.path.insert(0, str(RAIZ / "scripts"))
    import queda_por_elo as q
    # sem ferramenta nesta tarefa: o raciocínio do 9b só custava tempo (92 s e 504 na 1ª medição, 26/10)
    corpo = {"model": modelo, "stream": False, "max_tokens": 3000, "temperature": 0, "reasoning_effort": "none",
             "messages": [{"role": "user", "content": _prompt(entradas)}]}
    h = {"Content-Type": "application/json", "X-Agata-Token": q._token_interno()}
    if not modelo.startswith(("ollama-local/", "llamacpp-local/", "local/")):
        h["X-Agata-Data-Classification"] = "public"
    req = urllib.request.Request(PROXY + "/v1/chat/completions", method="POST",
                                 data=json.dumps(corpo).encode("utf-8"), headers=h)
    d = json.load(q._SEM_PROXY.open(req, timeout=timeout))
    m = d["choices"][0]["message"]
    return (m.get("content") or "").strip() or (m.get("reasoning") or "").strip()


def conferir(texto: str, entradas: list[dict]) -> tuple[list[str], list[tuple[str, str]]]:
    """(tópicos aceitos, [(tópico cortado, motivo)]). Mecânico, sem modelo."""
    por_n = {r["n"]: r for r in entradas}
    aceitos, cortados = [], []
    for linha in texto.splitlines():
        t = linha.strip()
        if not t.startswith(("-", "*", "•")):
            continue
        t = t.lstrip("-*• ").strip()
        if not t:
            continue
        cit = _citacao(t)
        if not cit:
            cortados.append((t, "sem citação de entrada do cache"))
            continue
        inicio_cit, nums = cit
        faltam = [n for n in nums if n not in por_n]
        if faltam:
            cortados.append((t, f"cita entrada fora da semana: {', '.join(f'c{n}' for n in faltam)}"))
            continue
        fonte = _norm(" ".join(por_n[n]["texto"] for n in nums))
        corpo = t[:inicio_cit]
        soltos = [v for v in (x.group(1) or x.group(0) for x in _VERIFICAVEIS.finditer(corpo)) if _norm(v) not in fonte]
        if soltos:
            cortados.append((t, f"não está nas entradas citadas: {', '.join(soltos[:3])}"))
            continue
        if len(t) > 500:
            cortados.append((t[:120] + "…", "tópico longo demais"))
            continue
        aceitos.append(t)
    return aceitos[:MAX_TOPICOS], cortados


def extrair(entradas: list[dict]) -> list[str]:
    """Plano B, sem modelo: um tópico por entrada, encurtado, com a própria citação."""
    out = []
    for r in entradas[-MAX_TOPICOS:]:
        t = re.sub(r"\s+", " ", r["texto"]).strip()
        out.append(f"{r['autor']} ({r['tipo']}): {t[:280] + ('…' if len(t) > 280 else '')} [c{r['n']}]")
    return out


def documento(aceitos: list[str], cortados: list[tuple[str, str]], entradas: list[dict],
              ini: date, fim: date, origem: str) -> str:
    cab = (f"# Memória Canônica da semana {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}\n\n"
           f"Gerada de {len(entradas)} entrada(s) do cache do Conselho (não canônico; `[cN]` = entrada N do cache). "
           f"Origem: {origem}. Conferida pela Máquina tópico a tópico; entra no canon só com a assinatura do "
           "Humano (MEMÓRIAS (849), V9 §37 M3).\n\n## Tópicos\n\n")
    corpo = "".join(f"- {t}\n" for t in aceitos) or "- (nenhum tópico na semana)\n"
    conf = (f"\n## Conferência da Máquina\n\n- Aceitos: {len(aceitos)}. Cortados: {len(cortados)}.\n"
            + "".join(f"- Cortado ({m}): {t[:200]}\n" for t, m in cortados[:20]))
    return cab + corpo + conf


def _diff_arquivo_novo(caminho: str, conteudo: str) -> str:
    linhas = conteudo.splitlines()
    return (f"diff --git a/{caminho} b/{caminho}\nnew file mode 100644\n--- /dev/null\n+++ b/{caminho}\n"
            f"@@ -0,0 +1,{len(linhas)} @@\n" + "".join(f"+{l}\n" for l in linhas))


def gerar(ate: date, dias: int = 7, modelo: str | None = MODELO, repo: Path = RAIZ, proponente=None) -> dict:
    entradas = entradas_da_janela(ate, dias)
    ini = ate - timedelta(days=dias - 1)
    if not entradas:  # semana vazia: nada para assinar, nada escrito
        return {"nome": None, "entradas": 0, "aceitos": 0, "cortados": 0, "origem": "semana sem entradas", "diff": None}
    aceitos, cortados, origem, propos = [], [], "extração direta, sem modelo", None
    if entradas and modelo:
        try:
            texto = (proponente or propor)(entradas, modelo)
            aceitos, cortados = conferir(texto, entradas)
            origem, propos = f"proposta do modelo {modelo}, conferida pela Máquina", modelo
        except Exception as e:  # noqa: BLE001 -- sem modelo, cai na extração
            codigo = getattr(e, "code", "")
            cortados = [(f"(o modelo {modelo} falhou: {type(e).__name__}{' ' + str(codigo) if codigo else ''})",
                         "sem proposta do modelo")]
    if entradas and not aceitos:
        aceitos, propos = extrair(entradas), None
        origem = ("extração direta: " + ("nenhum tópico do modelo passou na conferência" if cortados and
                  not cortados[0][0].startswith("(o modelo") else "o modelo não respondeu")) if modelo else origem
    nome = f"memoria-semanal-{ate.isoformat()}"
    doc = documento(aceitos, cortados, entradas, ini, ate, origem)
    caminho = f"extras/memoria-semanal/semana-{ate.isoformat()}.md"
    reg = (f"({{N}}) DIÁRIO — {ate.strftime('%d/%m/%Y')} · **Memória Canônica da semana {ini.strftime('%d/%m')} a "
           f"{ate.strftime('%d/%m/%Y')}: {len(aceitos)} tópico(s) de {len(entradas)} entrada(s) do cache do "
           f"Conselho.** Texto em `{caminho}`, assinado pelo Humano (V9 §37, M3; (849)). Origem: {origem}. "
           f"A Máquina cortou {len(cortados)} tópico(s) sem sustentação nas entradas citadas.\n"
           f"Modelo: {propos + ' propôs' if propos else 'nenhum (extração direta)'}; a Máquina conferiu "
           "(`scripts/memoria_semanal.py`) · "
           "vetor: cache do Conselho, cadeia íntegra · Autorização: Humano (assinatura do par)\n")
    prop = repo / "propostas"
    (prop / f"{nome}.diff").write_text(_diff_arquivo_novo(caminho, doc), encoding="utf-8")
    (prop / f"{nome}.registro.txt").write_text(reg, encoding="utf-8")
    return {"nome": nome, "entradas": len(entradas), "aceitos": len(aceitos), "cortados": len(cortados),
            "origem": origem, "diff": str(prop / f"{nome}.diff")}


def _selftest() -> int:
    import subprocess
    import tempfile
    import cache_conselho
    casos = []
    ents = [{"n": 3, "ts": "2026-10-26T10:00:00-0300", "autor": "Seth", "tipo": "fato",
             "texto": "O gateway reiniciou às 11h04 e a entrada (852) registrou a M6a."},
            {"n": 4, "ts": "2026-10-26T11:00:00-0300", "autor": "Codex", "tipo": "pendencia",
             "texto": "Medir o checador com 30 respostas boas; ver `scripts/benchmark_roteamento.py`."}]
    prop = ("- A M6a foi registrada na (852) depois do reinício das 11h04 [c3]\n"
            "- Falta medir o checador com 30 respostas boas em `scripts/benchmark_roteamento.py` [c4]\n"
            "- O checador ficou pronto e acerta 95% [c4]\n"
            "- O Jev aprovou tudo\n"
            "- A entrada (999) mudou o P-40 [c3]\n"
            "- Algo da outra semana [c9]\n")
    ok, cortes = conferir(prop, ents)
    motivos = " | ".join(m for _, m in cortes)
    casos += [
        ("tópicos sustentados passam", len(ok) == 2 and ok[0].startswith("A M6a")),
        ("número que não está na fonte é cortado (95%)", any("95" in t for t, _ in cortes)),
        ("tópico sem citação é cortado", "sem citação" in motivos),
        ("entrada (999) e P-40 inexistentes na fonte são cortados", any("(999)" in t for t, _ in cortes)),
        ("citação fora da semana é cortada", "fora da semana" in motivos),
        ("extração direta cita a própria entrada", extrair(ents)[0].endswith("[c3]")),
        ("ponto depois da citação é aceito: [c3]. e [c3, c4];", _citacao("x [c3].") == (2, [3])
         and _citacao("x [c3, c4];")[1] == [3, 4] and conferir("- A M6a foi registrada na (852) [c3].", ents)[0]),
        ("citação lida sem regex aninhada: [c3, c4], [ C3 ], malformada e longa", _citacao("x [c3, c4]") == (2, [3, 4])
         and _citacao("x [ C3 ]")[1] == [3] and _citacao("x [c3,, c4]") is None
         and _citacao("x [c0," + " 0," * 5000 + "]") is None),
    ]
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        (repo / "propostas").mkdir()
        salvo = cache_conselho.ARQ
        cache_conselho.ARQ = repo / "cache.jsonl"
        try:
            cache_conselho.anotar("Seth", "O gateway reiniciou às 11h04 e a entrada (852) registrou a M6a.", "fato")
            hoje = datetime.now(cache_conselho.TZ).date()
            r1 = gerar(hoje, 7, MODELO, repo, proponente=lambda e, m: "- A M6a foi registrada na (852) [c1]\n- Inventado 77 [c1]")
            r2 = gerar(hoje, 7, MODELO, repo, proponente=lambda e, m: (_ for _ in ()).throw(TimeoutError()))
            r0 = gerar(hoje - timedelta(days=30), 7, MODELO, repo, proponente=lambda e, m: "x")
            doc = (repo / "propostas" / f"{r1['nome']}.diff").read_text(encoding="utf-8")
            casos += [
                ("gera o par .diff + registro", r1["aceitos"] == 1 and r1["cortados"] == 1
                 and (repo / "propostas" / f"{r1['nome']}.registro.txt").exists()),
                ("modelo falhou -> extração direta", r2["aceitos"] == 1 and "extração" in r2["origem"]),
                ("semana vazia não escreve proposta", r0["diff"] is None),
            ]
            subprocess.run(["git", "init", "-q", str(repo / "g")], check=True)
            (repo / "g" / "x.diff").write_text(doc, encoding="utf-8")
            ap = subprocess.run(["git", "apply", "--check", "x.diff"], cwd=repo / "g", capture_output=True)
            casos.append(("o .diff aplica num repositório limpo", ap.returncode == 0))
            reg = (repo / "propostas" / f"{r1['nome']}.registro.txt").read_text(encoding="utf-8")
            casos.append(("registro no formato DIÁRIO com {N}", reg.startswith("({N}) DIÁRIO — ")))
        finally:
            cache_conselho.ARQ = salvo
    for nome, okc in casos:
        print(f"{'PASS' if okc else 'FALHA'}  {nome}")
    falhas = sum(not c for _, c in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if argv[:1] != ["gerar"]:
        print(__doc__)
        return 2
    def opt(n, p=None):
        return argv[argv.index(n) + 1] if n in argv else p
    ate = date.fromisoformat(opt("--ate")) if opt("--ate") else date.today()
    modelo = None if "--sem-modelo" in argv else opt("--modelo", MODELO)
    r = gerar(ate, int(opt("--dias", "7")), modelo, Path(opt("--repo", str(RAIZ))))
    print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
