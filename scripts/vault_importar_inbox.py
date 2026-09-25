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

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(os.environ.get("AGATA_REPO", os.path.expanduser("~/agata")))
# IRMÃ de memoria/obsidian/, nunca dentro -- ver docstring do módulo.
INBOX = REPO / "memoria" / "obsidian-inbox"
ESCRIBA_URL = os.environ.get("SETH_ESCRIBA_URL", "http://127.0.0.1:20140")


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


def _importar_um(caminho: Path) -> tuple[bool, str]:
    parsed = _parse_nota(caminho.read_text(encoding="utf-8"))
    if parsed is None:
        return False, "nota sem título+corpo reconhecíveis -- não apagada, corrija e rode de novo"
    titulo, corpo = parsed
    payload = json.dumps({"titulo": titulo, "corpo": corpo}).encode("utf-8")
    req = urllib.request.Request(
        f"{ESCRIBA_URL}/memoria", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return False, f"seth_escriba recusou (HTTP {e.code}): {e.read().decode(errors='replace')[:200]}"
    except urllib.error.URLError as e:
        return False, f"seth_escriba inacessível em {ESCRIBA_URL}: {e}"
    if not resp.get("ok"):
        return False, f"resposta inesperada de seth_escriba: {resp}"
    return True, f"entrada ({resp['entrada']}) criada -- {resp['header']}"


def main() -> int:
    if not INBOX.is_dir():
        print(f"inbox ainda não existe: {INBOX} (nada a importar)")
        return 0
    notas = sorted(INBOX.glob("*.md"))
    if not notas:
        print("inbox vazio -- nada a importar")
        return 0
    falhas = 0
    for nota in notas:
        ok, msg = _importar_um(nota)
        if ok:
            print(f"OK     {nota.name}: {msg}")
            nota.unlink()
        else:
            falhas += 1
            print(f"PULADA {nota.name}: {msg}")
    print(f"\n{len(notas) - falhas} importada(s), {falhas} pulada(s), {len(notas)} no total")
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
    # 7. _importar_um contra seth_escriba inacessível (porta que não existe) -- erro limpo, não crash
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "nota.md"
        p.write_text("teste\ncorpo de teste\n", encoding="utf-8")
        global ESCRIBA_URL
        _url_original = ESCRIBA_URL
        ESCRIBA_URL = "http://127.0.0.1:1"  # porta reservada, nunca escuta
        ok_imp, msg = _importar_um(p)
        casos.append(("seth_escriba inacessível -> falha limpa, nao crash", ok_imp is False and "inacessível" in msg))
        casos.append(("nota nao apagada quando falha", p.exists()))
        ESCRIBA_URL = _url_original
    for nome, passou in casos:
        print(("PASS  " if passou else "FALHA ") + nome)
        ok += 1 if passou else 0
    print(f"\nSELFTEST {'OK' if ok == len(casos) else 'FALHOU'} -- {ok}/{len(casos)}")
    return 0 if ok == len(casos) else 1


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else main())
