#!/usr/bin/env python3
"""Importa notas do vault Obsidian pra MEMÓRIAS.md -- Fase 4 do plano de
replicabilidade (propostas/plano-replicabilidade-2026-09-25.md), decisão do
Humano 25/09/2026: "Obsidian como camada de leitura/escrita do cliente,
MEMÓRIAS.md como o registro mecânico por baixo".

NÃO escreve em MEMÓRIAS.md diretamente -- chama o MESMO caminho hardened que
a Seth já usa, `POST /memoria` do `seth_escriba` (append-only, lock, escrita
atômica, verificação pós-escrita, número e data do relógio da Máquina, nunca
do chamador). Zero lógica de escrita nova: este script é só um CLIENTE HTTP
a mais desse serviço, como o `canon-mcp.mjs` já é. "Menor solução que cobre
o caso" -- REGRAS, Princípios (Elegância e eficiência).

Cada arquivo em `memoria/obsidian-inbox/*.md` é uma nota que o cliente (ou a
Seth, em nome dele) escreveu direto no vault. Sucesso -> a nota é apagada do
inbox: o conteúdo dela já mora em MEMÓRIAS.md, e a próxima geração do vault
derivado (`gerar_obsidian.py`, já roda no post-commit) recria a entrada em
`entradas/`, no lugar certo -- não há necessidade de manter as duas cópias.
Falha (seth_escriba fora do ar, nota sem conteúdo aproveitável) -> a nota
fica no inbox, nada se perde, e o motivo é impresso.

**Por que `memoria/obsidian-inbox/`, IRMÃ de `memoria/obsidian/`, nunca
dentro dela:** `gerar_obsidian.py` faz `shutil.rmtree(SAIDA)` e reconstrói
o vault inteiro do zero a cada regeneração (post-commit, todo commit).
Um inbox vivendo DENTRO de `memoria/obsidian/` seria apagado antes mesmo de
ser lido -- nota do cliente ainda não importada, perdida no primeiro commit
seguinte. Achado testando de verdade esta mudança, antes de virar hábito.

Formato de uma nota:
  - Frontmatter YAML simples, com `titulo:` -- tudo depois do frontmatter é o corpo; ou
  - Sem frontmatter: a 1ª linha não-vazia vira o título (um `#` de heading
    Markdown na frente é ignorado), o resto -- a partir dela -- vira o corpo.
Nota sem título OU sem corpo é pulada (nunca gera entrada vazia).

Tipo de entrada: sempre DIÁRIO -- é o único que `seth_escriba` sabe escrever
(mesma trava que já vale pra Seth: fato coletivo, nunca CORREÇÃO/CONSELHO/MOD
por este caminho, que exigem julgamento que este script não tem).

Uso: python3 scripts/vault_importar_inbox.py [--selftest]
Env: AGATA_REPO (default ~/agata), SETH_ESCRIBA_URL (default http://127.0.0.1:20140)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(os.environ.get("AGATA_REPO", os.path.expanduser("~/agata")))
# IRMÃ de memoria/obsidian/, nunca dentro -- ver docstring do módulo.
INBOX = REPO / "memoria" / "obsidian-inbox"
# (22/10/2026, P-8 fila-inbox) Notas aprovadas pelo Humano entram em MEMÓRIAS por PR, nunca por este script.
FILA = REPO / "memoria" / "obsidian-fila-revisao"

# Nota pronta = "decide e confere" (PROJETO.md, "Decisor local"). O Obsidian
# salva sozinho a cada poucos segundos enquanto se digita, e MEMÓRIAS é
# append-only: importar no meio da digitação gravaria entrada parcial para
# sempre. Trava exata: a nota está parada há QUIETO_MIN minutos. Por cima, o
# decisor local só pode BARRAR (parece rascunho pela metade); fora do ar ->
# vale só a trava. Nota parada há LIBERA_MIN não consulta o decisor: um dia
# intocada = pronta, e nada fica preso no inbox para sempre por um falso
# "rascunho" (13/10/2026: nota completa deu 0,82, rascunho cortado 0,60).
QUIETO_MIN = int(os.environ.get("AGATA_INBOX_QUIETO_MIN", "10"))
LIBERA_MIN = 24 * 60
LIMIAR_CONCLUIDA = 0.7
_PERGUNTA_CONCLUIDA = {"concluida": {
    "type": "noul",
    "instructions": "This note is a finished thought, not a half-written draft "
                    "that stops mid-sentence or mid-idea."}}
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "redesign" / "router"))
import decisor  # noqa: E402  (redesign/router/decisor.py)


def _parse_nota(texto: str) -> tuple[str, str] | None:
    """(titulo, corpo), ou None se a nota nao tem os dois."""
    texto = texto.strip("\n")
    if not texto.strip():
        return None
    if texto.startswith("---\n"):
        fim = texto.find("\n---", 4)
        if fim != -1:
            frente = texto[4:fim]
            corpo = texto[fim + 4:].lstrip("\n").strip()
            titulo = None
            for linha in frente.splitlines():
                m = re.match(r"^titulo:\s*(.+)$", linha.strip(), re.I)
                if m:
                    titulo = m.group(1).strip().strip("'\"")
            if titulo and corpo:
                return titulo, corpo
            # frontmatter presente mas sem titulo+corpo válidos -- cai no
            # fallback abaixo, tratando o arquivo INTEIRO (frontmatter
            # incluído) como texto simples, mesma disciplina de "nunca
            # inventa dado que não está lá".
    linhas = texto.split("\n")
    titulo = linhas[0].strip()
    if titulo.startswith("#"):
        titulo = titulo.lstrip("#").strip()
    corpo = "\n".join(linhas[1:]).strip()
    if not titulo or not corpo:
        return None
    return titulo, corpo


def _id_nota(caminho: Path) -> str:
    """Identifica a nota nos logs sem gravar o nome (pode ser pessoal)."""
    return hashlib.sha256(caminho.name.encode()).hexdigest()[:12]


def _pronta(caminho: Path, agora: float) -> tuple[bool, str, str]:
    """(pode importar?, motivo, via). Trava exata primeiro; o decisor só barra.
    `via` diz por qual caminho a nota passou -- é o que a avaliação mede."""
    parada_min = (agora - caminho.stat().st_mtime) / 60
    if parada_min < QUIETO_MIN:
        return False, f"salva há {parada_min:.0f} min (< {QUIETO_MIN}) -- pode estar em edição", ""
    parsed = _parse_nota(caminho.read_text(encoding="utf-8"))
    if parsed is None:
        return True, "", "sem-titulo-corpo"  # _importar_um dá o motivo exato
    if parada_min >= LIBERA_MIN:
        return True, "", "24h"
    titulo, corpo = parsed
    r = decisor.decidir("inbox", f"{titulo}\n\n{corpo}"[:4000], _PERGUNTA_CONCLUIDA,
                        meta={"nota": _id_nota(caminho), "chars": len(corpo),
                              "parada_min": round(parada_min)})
    p = decisor.probabilidade(r, "concluida")
    if p is None:
        return True, "", "sem-decisor"
    if p < LIMIAR_CONCLUIDA:
        return False, f"decisor: parece rascunho pela metade (p={p:.2f}) -- complete e espere", ""
    return True, "", "decisor"


def _enfileirar(caminho: Path, fila: Path | None = None) -> tuple[bool, str]:
    """(22/10/2026, P-8 fila-inbox) Copia a nota para a FILA de revisão, sem gravar em MEMÓRIAS.
    O original só sai do inbox depois de a cópia estar no lugar (gravação atômica)."""
    fila = fila or FILA
    texto = caminho.read_text(encoding="utf-8")
    if _parse_nota(texto) is None:
        return False, "nota sem título+corpo reconhecíveis -- não enfileirada, corrija e rode de novo"
    fila.mkdir(parents=True, exist_ok=True)
    destino = fila / caminho.name
    tmp = fila / f".{caminho.name}.tmp"
    tmp.write_text(texto, encoding="utf-8")
    os.replace(tmp, destino)
    return True, f"enfileirada para revisão do Humano em {destino} (nada gravado em MEMÓRIAS)"


def main() -> int:
    if not INBOX.is_dir():
        print(f"inbox ainda não existe: {INBOX} (nada a importar)")
        return 0
    notas = sorted(INBOX.glob("*.md"))
    if not notas:
        print("inbox vazio -- nada a importar")
        return 0
    falhas = aguardando = 0
    agora = time.time()
    for nota in notas:
        pronta, motivo, via = _pronta(nota, agora)
        if not pronta:
            aguardando += 1
            print(f"AGUARDA {nota.name}: {motivo}")
            continue
        parsed = _parse_nota(nota.read_text(encoding="utf-8"))
        chars = len(parsed[1]) if parsed else 0
        ok, msg = _enfileirar(nota)
        if ok:
            print(f"OK     {nota.name}: {msg}")
            decisor.registrar_avaliacao("inbox", {"evento": "enfileirada", "nota": _id_nota(nota),
                                                  "chars": chars, "via": via})
            nota.unlink()
        else:
            falhas += 1
            print(f"PULADA {nota.name}: {msg}")
    importadas = len(notas) - falhas - aguardando
    print(f"\n{importadas} enfileirada(s), {aguardando} aguardando, {falhas} pulada(s), "
          f"{len(notas)} no total")
    return 1 if falhas else 0


def _selftest() -> int:
    casos, ok = [], 0
    # 1. frontmatter com titulo -- corpo eh o resto
    r = _parse_nota("---\ntitulo: assunto do dia\n---\nprimeira linha do corpo\nsegunda linha\n")
    casos.append(("frontmatter titulo+corpo", r == ("assunto do dia", "primeira linha do corpo\nsegunda linha")))
    # 2. sem frontmatter -- 1a linha vira titulo, resto vira corpo
    r = _parse_nota("Assunto do dia\n\nCorpo da nota, mais de uma linha.\nSegunda linha.\n")
    casos.append(("1a linha -> titulo", r == ("Assunto do dia", "Corpo da nota, mais de uma linha.\nSegunda linha.")))
    # 3. heading markdown na 1a linha -- # eh removido do titulo
    r = _parse_nota("# Assunto do dia\ncorpo aqui\n")
    casos.append(("heading # removido do titulo", r == ("Assunto do dia", "corpo aqui")))
    # 4. nota vazia -> None
    casos.append(("nota vazia -> None", _parse_nota("   \n\n") is None))
    casos.append(("nota so espaco -> None", _parse_nota("") is None))
    # 5. so titulo, sem corpo -> None (nao gera entrada vazia)
    casos.append(("titulo sem corpo -> None", _parse_nota("só uma linha, nada mais\n") is None))
    # 6. frontmatter mal formado (sem titulo:) -- cai no fallback, tratando
    # o arquivo inteiro como texto simples (a 1a linha "---" vira titulo)
    r = _parse_nota("---\nalgo: valor\n---\ncorpo\n")
    casos.append(("frontmatter sem titulo -> fallback nao quebra", r is not None and r[0] == "---"))
    # 7. _enfileirar: a nota vai para a fila, o conteúdo é idêntico e nada toca MEMÓRIAS
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "nota.md"
        p.write_text("teste\ncorpo de teste\n", encoding="utf-8")
        fila_teste = Path(td) / "fila"
        ok_enf, msg = _enfileirar(p, fila_teste)
        casos.append(("nota enfileirada -> ok", ok_enf is True and "nada gravado em MEMÓRIAS" in msg))
        casos.append(("fila recebeu cópia idêntica", (fila_teste / p.name).read_text(encoding="utf-8") == p.read_text(encoding="utf-8")))
        ruim = Path(td) / "ruim.md"; ruim.write_text("só uma linha\n", encoding="utf-8")
        ok_ruim, _ = _enfileirar(ruim, fila_teste)
        casos.append(("nota sem corpo -> não enfileirada", ok_ruim is False and not (fila_teste / "ruim.md").exists()))
        # 8-10. nota pronta: trava exata (tempo parado) + decisor que só barra
        agora = time.time()
        os.utime(p, (agora, agora))
        casos.append(("nota recém-salva -> aguarda (trava exata)", _pronta(p, agora)[0] is False))
        velha = agora - (QUIETO_MIN + 1) * 60
        os.utime(p, (velha, velha))
        _decidir_original = decisor.decidir
        decisor.decidir = lambda *a, **k: None
        casos.append(("nota parada + decisor fora do ar -> importa (só a trava)",
                      _pronta(p, agora)[0] is True))
        decisor.decidir = lambda *a, **k: {"concluida": {"type": "noul", "noul": 0.3}}
        barrada, motivo, _ = _pronta(p, agora)
        casos.append(("nota parada + decisor diz rascunho -> barrada", barrada is False and "rascunho" in motivo))
        decisor.decidir = lambda *a, **k: {"concluida": {"type": "noul", "noul": 0.95}}
        casos.append(("nota parada + decisor diz concluída -> importa", _pronta(p, agora)[0] is True))
        dia = agora - (LIBERA_MIN + 1) * 60
        os.utime(p, (dia, dia))
        decisor.decidir = lambda *a, **k: {"concluida": {"type": "noul", "noul": 0.1}}
        casos.append(("nota parada há 1 dia -> importa sem perguntar ao decisor",
                      _pronta(p, agora)[0] is True))
        decisor.decidir = _decidir_original
    for nome, passou in casos:
        print(("PASS  " if passou else "FALHA ") + nome)
        ok += 1 if passou else 0
    print(f"\nSELFTEST {'OK' if ok == len(casos) else 'FALHOU'} -- {ok}/{len(casos)}")
    return 0 if ok == len(casos) else 1


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else main())
