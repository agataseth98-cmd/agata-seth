#!/usr/bin/env python3
"""Contexto de início de sessão (sincronia-12-11).

Decisão do Humano (cache do Conselho, entrada (521), 12/11/2026): gancho de início que torna mecânica a
leitura do canon e do cache. Este script é o conteúdo; cada CLI chama o gancho dela:
  - Claude Code: SessionStart em .claude/settings.json (chama scripts/sessao_claude_contexto.sh, que chama este);
  - Gemini CLI: SessionStart em config/cli/gemini/settings.json.exemplo (passo do Humano);
  - Codex: [[hooks.SessionStart]] em config/cli/codex/config.toml.exemplo (passo do Humano).
  - Seth: não usa este script; a hidratação do gateway já inclui AGENTS.md, a seção do PROTOCOLOS e o resumo do cache.

Saída (--json, padrão): {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}.
O mesmo formato serve às três CLIs (doc pública: hookSpecificOutput.additionalContext). Texto curto: o Codex
limita o contexto de hook a 2500 tokens por padrão, e o limite deste script é de 3500 caracteres.

Seções: Estado da Máquina (estado_para_eco.sh); Memória comum do Conselho (últimas decisões do cache);
Lotes abertos (ONDE_ESTAMOS.md); Regras ativas (AGENTS.md, bullets Sempre); Sessão conjunta (equipe).
Só lê. O cache é lido pela ferramenta do próprio repositório (cache_conselho.py ler), nunca direto.

Uso: python3 scripts/sessao_contexto.py [--json | --texto] | --selftest
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ_PADRAO = Path(__file__).resolve().parents[1]
LIMITE_CARACTERES = 3500
CABECALHO_CACHE = re.compile(r"^\((\d+)\) (\S+) · (.*) · (\w+)$")


def _rodar(args: list[str], raiz: Path, limite_s: int) -> str | None:
    """Saída do comando, mesmo com código de saída diferente de zero (estado_para_eco.sh sai != 0 com
    sync em aviso). None só se não rodou, estourou o prazo ou não deu saída."""
    try:
        r = subprocess.run(args, cwd=raiz, capture_output=True, text=True, timeout=limite_s)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.stdout.strip() else None


def estado_maquina(raiz: Path) -> str:
    saida = _rodar(["bash", "scripts/estado_para_eco.sh"], raiz, 20)
    if not saida:
        return "lacuna: estado_para_eco.sh não rodou nesta sessão; não afirme HEAD nem sync sem medir."
    linhas = [ln for ln in saida.splitlines() if ln.strip()][:8]
    return "\n".join(linhas)


def _quando(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m %H:%M")
    except ValueError:
        return iso[:16]


def decisoes_do_cache(linhas_cache: list[str], quantas: int = 3) -> list[str]:
    """Últimas `quantas` decisões de um texto de `cache_conselho.py ler`, cada uma em uma linha: (N) data hora + início."""
    achadas: list[list[str]] = []  # [cabeçalho, texto]
    em_decisao = False
    for ln in linhas_cache:
        m = CABECALHO_CACHE.match(ln)
        if m:
            em_decisao = m.group(4) == "decisao"
            if em_decisao:
                achadas.append([f"({m.group(1)}) {_quando(m.group(2))}", ""])
            continue
        if not ln.strip():
            em_decisao = False
            continue
        if em_decisao and achadas:
            achadas[-1][1] = (achadas[-1][1] + " " + ln.strip()).strip()
    saida = []
    for cab, texto in achadas[-quantas:]:
        trecho = texto if len(texto) <= 180 else texto[:177] + "..."
        saida.append(f"{cab} {trecho}".rstrip())
    return saida


def memoria_comum(raiz: Path) -> str:
    saida = _rodar(["python3", "redesign/router/cache_conselho.py", "ler", "--n", "50"], raiz, 20)
    if saida is None:
        return "lacuna: cache_conselho.py não respondeu; leia com `python3 redesign/router/cache_conselho.py ler --n 20`."
    decisoes = decisoes_do_cache(saida.splitlines())
    if not decisoes:
        return "nenhuma decisão nas últimas 50 entradas do cache."
    return "\n".join(f"- {d}" for d in decisoes)


def lotes_abertos(onde_estamos: str) -> str:
    """Lotes com estado 'proposta' na tabela de ONDE_ESTAMOS.md (colunas: componente | proposta | estado | desde)."""
    nomes = []
    for ln in onde_estamos.splitlines():
        cols = [c.strip() for c in ln.split("|")]  # cols[0] é o vazio antes da 1ª barra
        if len(cols) >= 5 and cols[1] and cols[2] and cols[3].startswith("proposta"):
            nomes.append(cols[2])
    if not nomes:
        return "nenhum lote aberto na tabela de ONDE_ESTAMOS."
    return f"{len(nomes)} aberto(s): " + ", ".join(nomes)


def sessao_conjunta(raiz: Path) -> str:
    saida = _rodar(["python3", "scripts/equipe/equipe.py", "status"], raiz, 15)
    if not saida:
        return "lacuna: scripts/equipe/equipe.py status não respondeu."
    return "\n".join([ln for ln in saida.splitlines() if ln.strip()][:3])


def montar(raiz: Path = RAIZ_PADRAO, *, estado=None, cache=None, equipe=None) -> str:
    """Texto do contexto. As funções injetáveis deixam o selftest rodar sem rede nem subprocesso."""
    from porques import regras_curtas  # import local: scripts/ está no mesmo diretório
    onde = ""
    try:
        onde = (raiz / "ONDE_ESTAMOS.md").read_text(encoding="utf-8")
    except OSError:
        pass
    # ESTADO.md (projeto-indice) tem ~20 KB: entra como ponteiro, não inteiro (limite deste contexto, Regra 7).
    try:
        tam = (raiz / "ESTADO.md").stat().st_size
        vivo = f"ESTADO.md ({tam} B, gerado pelo pre-commit): serviços, gates e estado vivo. Leia sob demanda."
    except OSError:
        vivo = "lacuna: ESTADO.md não lido."
    partes = [
        "=== Estado da Máquina (estado_para_eco.sh) ===\n" + (estado(raiz) if estado else estado_maquina(raiz)),
        "=== Estado vivo (ESTADO.md, gerado pela Máquina; projeto-indice) ===\n" + vivo,
        "=== Memória comum do Conselho (últimas decisões) ===\n" + (cache(raiz) if cache else memoria_comum(raiz)),
        "=== Lotes abertos (ONDE_ESTAMOS) ===\n" + (lotes_abertos(onde) if onde else "lacuna: ONDE_ESTAMOS.md não lido."),
        "=== " + regras_curtas(raiz) + " ===\n"
        "Cabeçalho na abertura de cada resposta. Fato do sistema: busque no vault antes de afirmar. "
        "Antes de entregar texto com afirmação verificável: python3 redesign/router/auditoria_turno.py --verificar. "
        "Ao fechar trabalho relevante: cache_conselho.py anotar.",
        "=== Sessão conjunta (equipe.py status) ===\n" + (equipe(raiz) if equipe else sessao_conjunta(raiz)),
    ]
    texto = "\n\n".join(partes)
    if len(texto) > LIMITE_CARACTERES:
        texto = texto[: LIMITE_CARACTERES - 20] + "\n[cortado no limite]"
    return texto


def como_json(texto: str) -> str:
    return json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": texto}},
                      ensure_ascii=False)


def _selftest() -> int:
    falhas = []
    cache = (
        "(501) 2026-11-11T20:25:30-0300 · Claude Haiku 5.5 · fato\n"
        "texto de fato que não entra\n\n"
        "(504) 2026-11-11T20:30:54-0300 · Claude Opus 5.5 · decisao\n"
        "11/11 20:31, Humano: modo de voz ligado só hoje.\n\n"
        "(506) 2026-11-12T08:47:33-0300 · Claude Opus 5.5 · decisao\n"
        "12/11 08:45, Humano 'ok a todas': lote aprovado.\n\n"
        "(507) 2026-11-12T08:57:37-0300 · Codex · fato\n"
        "auditoria por leitura.\n\n"
        "(521) 2026-11-12T09:58:39-0300 · Claude Opus 5.5 · decisao\n"
        "12/11 10:00, Humano: assinou pacote-mecanico-12-11.\n\n"
    ).splitlines()
    ds = decisoes_do_cache(cache)
    falhas += [] if len(ds) == 3 and ds[-1].startswith("(521) 12/11 09:58") else [f"decisões do cache: {ds}"]
    falhas += [] if all("fato que não entra" not in d for d in ds) else ["fato entrou como decisão"]
    onde = ("| componente | proposta | estado | desde |\n|---|---|---|---|\n"
            "| A | lote-a | aplicada (PR #1) | 12/11 |\n| B | lote-b | proposta | 12/11 |\n| C | lote-c | proposta | 11/11 |\n")
    falhas += [] if lotes_abertos(onde) == "2 aberto(s): lote-b, lote-c" else [f"lotes: {lotes_abertos(onde)}"]
    raiz = RAIZ_PADRAO
    texto = montar(raiz, estado=lambda r: "HEAD: abc1234\nsync: PASS",
                   cache=lambda r: "- (521) 12/11 09:58 Humano: assinou.",
                   equipe=lambda r: "(equipe sem sessão)")
    for trecho in ["=== Estado da Máquina", "=== Estado vivo (ESTADO.md", "=== Memória comum do Conselho", "=== Lotes abertos",
                   "=== Regras ativas", "=== Sessão conjunta"]:
        falhas += [] if trecho in texto else [f"seção ausente: {trecho}"]
    falhas += [] if len(texto) <= LIMITE_CARACTERES else ["texto acima do limite"]
    j = json.loads(como_json(texto))
    falhas += [] if j["hookSpecificOutput"]["hookEventName"] == "SessionStart" and \
        j["hookSpecificOutput"]["additionalContext"] == texto else ["formato JSON do gancho"]
    if falhas:
        for f in falhas:
            print("FALHOU", f)
        return 1
    print("SELFTEST OK sessao_contexto")
    return 0


def _main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    texto = montar(RAIZ_PADRAO)
    if "--texto" in argv:
        print(texto)
    else:
        print(como_json(texto))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(_main(sys.argv[1:]))
