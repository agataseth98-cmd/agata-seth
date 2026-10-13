#!/usr/bin/env python3
"""Auditoria determinística do turno anterior da Seth e do Goose (MEMÓRIAS (662)).

O LibreChat e o Goose mandam a conversa inteira a cada pedido, então a resposta
anterior do assistente chega ao `seth_gateway` junto com a pergunta nova. Aqui
ela é conferida com as checagens que já existem -- nenhuma chamada de modelo,
milissegundos -- e o resultado volta ao bloco de estado como
`AUDITORIA-TURNO-ANTERIOR:`, para o modelo se corrigir no turno seguinte (o mesmo
mecanismo do `MODELO-REAL-TURNO-ANTERIOR`, (621)).

Confere:
- cabeçalho: `verificar()` de `scripts/verificar_cabecalho.py` (formas (a) e (b),
  base do `t=`, `sync: PASS` sem medidas, entrada acima do topo de MEMÓRIAS);
- forma certa no lugar certo: a 1ª resposta da conversa abre com o bloco de
  prontidão; as seguintes, com a linha de turno;
- contagem: `t=<n> (contado no contexto)` tem de bater com o número de respostas
  do assistente na conversa (só em conversa sem ferramentas -- com tool-calls a
  contagem é ambígua e não se acusa);
- citação `arquivo:linha` com trecho: as mesmas funções do P-19, só para
  caminhos com extensão conhecida (evita "IP:porta", (657)).
NÃO confere afirmação falsa em prosa nem citação (N) real usada para a coisa
errada -- isso não é determinístico (limite declarado em (661)).

Cada auditoria vira uma linha em `~/.cache/agata/auditoria-turno.jsonl`
(achados e metadados, nunca o texto).

Uso: python3 redesign/router/auditoria_turno.py --selftest
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

RAIZ = Path(os.environ.get("SETH_REPO", str(Path(__file__).resolve().parents[2])))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import verificar_cabecalho as _cab  # noqa: E402
import verificar_citacao_arquivo as _cit  # noqa: E402

LOG = Path(os.environ.get("AGATA_AUDITORIA_LOG", "~/.cache/agata/auditoria-turno.jsonl")).expanduser()
_EXTENSOES = (".md", ".py", ".sh", ".mjs", ".js", ".yaml", ".yml", ".json", ".txt",
              ".service", ".timer", ".conf", ".diff")
_T_CONTADO = re.compile(r"t\s*=\s*(\d+)\s*\(\s*contado no contexto", re.IGNORECASE)


def _texto(conteudo) -> str:
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        return " ".join(p.get("text", "") for p in conteudo if isinstance(p, dict))
    return ""


def _cabecalho(texto: str) -> tuple[str, bool]:
    """(cabeçalho, é bloco de prontidão?). Prontidão = 1ª linha com `modelo:`."""
    linhas = [l for l in texto.strip().splitlines() if l.strip()]
    if not linhas:
        return "", False
    prontidao = bool(re.search(r"·\s*modelo\s*:", linhas[0], re.IGNORECASE))
    return ("\n".join(linhas[:3]) if prontidao else linhas[0]), prontidao


def auditar(msgs: list) -> list[str] | None:
    """Achados sobre a última resposta do assistente; [] = limpa; None = não há
    resposta anterior a auditar."""
    idx = [i for i, m in enumerate(msgs) if isinstance(m, dict) and m.get("role") == "assistant"
           and _texto(m.get("content")).strip()]
    if not idx:
        return None
    texto = _texto(msgs[idx[-1]].get("content"))
    n_resposta = len(idx)
    cab, prontidao = _cabecalho(texto)
    achados = [f"cabeçalho: {f}" for f in _cab.verificar(cab, _cab.ultima_entrada_local())]
    if n_resposta == 1 and not prontidao:
        achados.append("cabeçalho: a 1ª resposta da conversa abre com o bloco de prontidão (3 linhas), não com a linha de turno")
    if n_resposta > 1 and prontidao:
        achados.append(f"cabeçalho: bloco de prontidão na resposta nº {n_resposta}; depois da 1ª, é a linha de turno com t=")
    tem_ferramenta = any(isinstance(m, dict) and (m.get("role") == "tool" or m.get("tool_calls"))
                         for m in msgs)
    m_t = _T_CONTADO.search(cab)
    if m_t and not tem_ferramenta and int(m_t.group(1)) != n_resposta:
        achados.append(f"cabeçalho: t={m_t.group(1)}, mas foi a resposta nº {n_resposta} desta conversa")
    for arquivo, linha_n, trecho in _cit.achar_citacoes(texto):
        if not arquivo.lower().endswith(_EXTENSOES):
            continue
        ok, motivo = _cit.checar(str(RAIZ), arquivo, linha_n, trecho)
        if not ok:
            achados.append(f"citação {arquivo}:{linha_n}: {motivo}")
    return achados


def linha_estado(msgs: list, cliente: str = "") -> str:
    """`AUDITORIA-TURNO-ANTERIOR: ...` para o bloco de estado, ou "" se não há turno
    anterior. Nunca levanta exceção: auditoria quebrada não derruba a resposta."""
    try:
        achados = auditar(msgs)
    except Exception as e:  # noqa: BLE001 -- best-effort, como o modelo real (621)
        _registrar(cliente, None, f"{type(e).__name__}: {e}"[:160])
        return ""
    if achados is None:
        return ""
    _registrar(cliente, achados, None)
    if not achados:
        return "AUDITORIA-TURNO-ANTERIOR: OK"
    return "AUDITORIA-TURNO-ANTERIOR: " + " | ".join(achados)


def _registrar(cliente, achados, erro):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "cliente": cliente,
                                "achados": achados, "erro": erro}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _selftest() -> int:
    import tempfile
    global LOG
    LOG = Path(tempfile.mkdtemp()) / "a.jsonl"
    hora = "2026-10-13 12:43 -0300 (relógio da Máquina)"
    topo = _cab.ultima_entrada_local() or 1
    pront = (f"Agata · modelo: ministral-14b-latest · sync: não verificado · lacuna: teste · {hora}\n"
             f"Última entrada: ({topo}) DIÁRIO — teste\npronto.\n\nOi!")
    u = {"role": "user", "content": "x"}
    a = lambda c: {"role": "assistant", "content": c}
    casos = [
        ("sem resposta anterior -> nada", linha_estado([u]) == ""),
        ("1ª resposta com prontidão correta -> OK", linha_estado([u, a(pront), u]) == "AUDITORIA-TURNO-ANTERIOR: OK"),
        ("1ª resposta com linha de turno -> acusa", "1ª resposta" in linha_estado(
            [u, a(f"Agata · m · t=1 (contado no contexto) · {hora}\n\ntexto"), u])),
        ("cabeçalho real da Seth em (661): t=1 sem base, era a 2ª -> acusa a base",
         "qualificador" in linha_estado([u, a(pront), u, a(f"Agata · ministral-14b-latest · t=1 · {hora}\n\ntexto"), u])),
        ("t=1 (contado no contexto) na 2ª resposta -> acusa a contagem",
         "resposta nº 2" in linha_estado([u, a(pront), u, a(f"Agata · m · t=1 (contado no contexto) · {hora}\n\nx"), u])),
        ("2ª resposta correta -> OK", linha_estado(
            [u, a(pront), u, a(f"Agata · m · t=2 (contado no contexto) · {hora}\n\nx"), u]) == "AUDITORIA-TURNO-ANTERIOR: OK"),
        ("com tool-calls a contagem não é acusada", linha_estado(
            [u, a(pront), {"role": "assistant", "content": "", "tool_calls": [{}]}, {"role": "tool", "content": "r"},
             a(f"Agata · m · t=5 (contado no contexto) · {hora}\n\nx"), u]) == "AUDITORIA-TURNO-ANTERIOR: OK"),
        ("sync: PASS nu na prontidão -> acusa", "sync" in linha_estado(
            [u, a(pront.replace("sync: não verificado · lacuna: teste", "sync: PASS")), u])),
        ("citação de arquivo que não existe -> acusa", "citação" in linha_estado(
            [u, a(pront + "\nVer `PROJETO_NAO_EXISTE.md:12` \"um trecho qualquer aqui\""), u])),
        ("IP:porta não vira citação", linha_estado(
            [u, a(pront + "\nporta 127.0.0.1:11435 em uso"), u]) == "AUDITORIA-TURNO-ANTERIOR: OK"),
    ]
    linhas = LOG.read_text(encoding="utf-8").splitlines()
    casos.append(("log: 1 linha por auditoria, sem o texto", len(linhas) == 9 and all("Oi!" not in l for l in linhas)))
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(_selftest())
    print(__doc__)
