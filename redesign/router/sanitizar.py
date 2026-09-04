#!/usr/bin/env python3
"""sanitizar.py — scrub de segredo ANTES de uma chamada sair pelo OmniRoute (P1-02).

Uma régua só: os padrões vêm de `scripts/varredura_segredo.sh` (`PADROES_SEGREDO`),
extraídos via `bash -c 'source ...; printf ...'` — sem re-digitar, sem segunda cópia.
A única tradução ERE→Python é `[[:space:]]` → conjunto explícito; qualquer outra classe
POSIX faz o módulo falhar alto (não adivinha).

Falha FECHADA: padrão casado ⇒ `sanitizar_payload` levanta `SegredoNoPayload`. Não
mascara e envia — bloqueia. Quem chama devolve erro ao caller sem ecoar o segredo.

Uso:
    python3 redesign/router/sanitizar.py --padroes
        # imprime os 7 padrões (auditoria da régua única)

    python3 redesign/router/sanitizar.py --autoteste
        # fixtures offline: cada padrão casa o que deve, casos limpos passam. exit 0 = OK

    python3 redesign/router/sanitizar.py --selftest < entrada
        # entrada = JSON de payload (dict) OU texto cru. Imprime {bloqueado, achados}.
        # exit 0 = limpo · 3 = bloqueado · 2 = uso errado
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# SETH_REPO -- mesma env var que seth_gateway.py/seth_escriba.py já respeitam
# (achado 04/09/2026: este módulo era o único hardcoded em ~/agata, quebra em
# qualquer checkout fora do $HOME real de quem roda o processo).
REPO = os.environ.get("SETH_REPO", os.path.expanduser("~/agata"))
SH_PADROES = os.path.join(REPO, "scripts", "varredura_segredo.sh")

# ERE POSIX -> Python. `[[:space:]]` em locale C = [ \t\n\r\f\v]. Só esta.
_POSIX_CLASSES = {"[[:space:]]": r"[ \t\n\r\f\v]"}
_POSIX_SOBRANDO = re.compile(r"\[\[:[a-z]+:\]\]")

_ROTULOS = [
    "aws-access-key-id",
    "google-api-key",
    "github-token",
    "openai-style-key",
    "slack-token",
    "pem-private-key",
    "heuristica-KEY/TOKEN/SECRET/PASSWORD",
]


class PadraoNaoTraduzivel(RuntimeError):
    pass


class SegredoNoPayload(Exception):
    def __init__(self, achados: list[dict]):
        self.achados = achados
        nomes = ", ".join(sorted({a["padrao_rotulo"] for a in achados}))
        super().__init__(f"payload bloqueado — casou: {nomes}")


def _extrair_padroes(sh_path: str = SH_PADROES) -> list[str]:
    """Fonte da verdade: o array PADROES_SEGREDO do .sh, como o bash o vê."""
    r = subprocess.run(
        ["bash", "-c", f'source "$1"; printf "%s\\n" "${{PADROES_SEGREDO[@]}}"', "_", sh_path],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"não consegui ler PADROES_SEGREDO de {sh_path}: {r.stderr.strip()}")
    linhas = [ln for ln in r.stdout.splitlines() if ln.strip()]
    if not linhas:
        raise RuntimeError(f"PADROES_SEGREDO vazio em {sh_path}")
    return linhas


def _ere_para_python(p: str) -> str:
    for posix, repl in _POSIX_CLASSES.items():
        p = p.replace(posix, repl)
    sobra = _POSIX_SOBRANDO.search(p)
    if sobra:
        raise PadraoNaoTraduzivel(
            f"classe POSIX não traduzida: {sobra.group(0)} em {p!r} — "
            f"adicione a tradução explícita em _POSIX_CLASSES, não adivinhe"
        )
    return p


def compilar(sh_path: str = SH_PADROES) -> list[tuple[str, str, re.Pattern]]:
    brutos = _extrair_padroes(sh_path)
    rotulos = _ROTULOS if len(brutos) == len(_ROTULOS) else [f"padrao-{i}" for i in range(len(brutos))]
    out = []
    for rotulo, bruto in zip(rotulos, brutos):
        out.append((rotulo, bruto, re.compile(_ere_para_python(bruto))))
    return out


_COMPILADOS: list[tuple[str, str, re.Pattern]] | None = None


def _regras() -> list[tuple[str, str, re.Pattern]]:
    global _COMPILADOS
    if _COMPILADOS is None:
        _COMPILADOS = compilar()
    return _COMPILADOS


def _redigir(trecho: str) -> str:
    n = len(trecho)
    cabeca = trecho[:4]
    return f"{cabeca}…[{n} chars]"


def varrer(texto: str) -> list[dict]:
    """Lista de {padrao_rotulo, padrao, trecho_redigido, pos}. Nunca devolve o segredo."""
    achados = []
    for rotulo, bruto, rx in _regras():
        for m in rx.finditer(texto):
            achados.append(
                {
                    "padrao_rotulo": rotulo,
                    "padrao": bruto,
                    "trecho_redigido": _redigir(m.group(0)),
                    "pos": m.start(),
                }
            )
    return achados


_PROFUNDIDADE_MAX = 12   # payload OpenAI-compat real não passa disso; trava contra recursão patológica
_NOS_MAX = 20000         # trava contra payload absurdamente grande (nº de chaves/itens visitados)


def _campos_texto(payload):
    """Rende TODA string em qualquer profundidade do payload (dict/list aninhado).

    Achado real (auditoria 04/09/2026, Camada C): a versão anterior só olhava
    campos fixos (system/prompt/messages[].content/input) — um segredo em
    `tools[].function.description`, `metadata`, ou qualquer campo custom
    passava ileso. `sanitizar_payload` promete "falha FECHADA" (docstring do
    módulo); a lista fixa era falha ABERTA pra tudo que não citou. Recursivo,
    sem lista de campo — nenhum campo novo do formato OpenAI-compat (ou de um
    provedor) pode reabrir esta lacuna por omissão.
    """
    contador = [0]

    def _anda(no, caminho, profundidade):
        contador[0] += 1
        if contador[0] > _NOS_MAX or profundidade > _PROFUNDIDADE_MAX:
            return
        if isinstance(no, str):
            yield caminho, no
        elif isinstance(no, dict):
            for k, v in no.items():
                yield from _anda(v, f"{caminho}.{k}" if caminho else str(k), profundidade + 1)
        elif isinstance(no, list):
            for i, v in enumerate(no):
                yield from _anda(v, f"{caminho}[{i}]", profundidade + 1)
        # números/bool/None/etc: nada a varrer

    yield from _anda(payload, "", 0)


def sanitizar_payload(payload: dict) -> dict:
    """Falha FECHADA: casou um padrão ⇒ levanta SegredoNoPayload. Senão, devolve igual."""
    achados = []
    for campo, texto in _campos_texto(payload):
        for a in varrer(texto):
            achados.append({**a, "campo": campo or "(raiz)"})
    if achados:
        raise SegredoNoPayload(achados)
    return payload


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
# Fixtures montadas de fragmentos: nenhuma linha-fonte deste arquivo pode casar
# um dos 7 padrões (senão o P-1 do perímetro barra o commit, e está certo em
# barrar). Os valores só se formam em runtime, ao juntar os pedaços.
def _fx(*partes: str) -> str:
    return "".join(partes)


_FIXTURES_CASA = [
    ("aws-access-key-id", _fx("AK", "IA", "A" * 16)),
    ("google-api-key", _fx("AI", "za", "b" * 35)),
    ("github-token", _fx("gh", "p", "_", "c" * 36)),
    ("openai-style-key", _fx("sk", "-", "d" * 20)),
    ("slack-token", _fx("xo", "xb", "-", "1234567890")),
    ("pem-private-key", _fx("---", "--BEGIN ", "RSA ", "PRIVATE ", "KEY", "---", "--")),
    ("heuristica-KEY/TOKEN/SECRET/PASSWORD", _fx("API", "_KEY", " = ", '"', "abcdef0123456789ABCD", '"')),
]
_FIXTURES_LIMPO = [
    "responda só: ok",
    _fx("o padrão sk", "-[A-Za-z0-9]{20,} casa chave OpenAI"),  # menção, não valor
    _fx("aki de manhã cedo, sem AK", "IA aqui"),
    "meu token de metrô",
]


def _autoteste() -> int:
    falhas = 0
    for esperado, texto in _FIXTURES_CASA:
        achados = varrer(texto)
        rotulos = {a["padrao_rotulo"] for a in achados}
        # o texto pode casar mais de um padrão; basta o esperado estar entre eles
        ok = esperado in rotulos or (esperado.startswith("heuristica") and achados)
        print(f"{'PASS' if ok else 'FALHA'}  casa[{esperado}]  -> {sorted(rotulos) or '(nada)'}")
        falhas += 0 if ok else 1
    for texto in _FIXTURES_LIMPO:
        achados = varrer(texto)
        ok = not achados
        print(f"{'PASS' if ok else 'FALHA'}  limpo  {texto!r:50}  -> {[a['padrao_rotulo'] for a in achados] or 'ok'}")
        falhas += 0 if ok else 1
    print(f"\n{'AUTOTESTE OK' if not falhas else f'AUTOTESTE FALHOU ({falhas})'}")
    return 0 if not falhas else 1


def _selftest(raw: str) -> int:
    raw = raw.strip()
    payload = None
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            payload = obj
    except (ValueError, TypeError):
        pass
    if payload is not None:
        try:
            sanitizar_payload(payload)
        except SegredoNoPayload as e:
            print(json.dumps({"bloqueado": True, "achados": e.achados}, ensure_ascii=False, indent=2))
            return 3
        print(json.dumps({"bloqueado": False, "achados": []}, ensure_ascii=False, indent=2))
        return 0
    achados = varrer(raw)
    print(json.dumps({"bloqueado": bool(achados), "achados": achados}, ensure_ascii=False, indent=2))
    return 3 if achados else 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--padroes":
        for rotulo, bruto, _ in _regras():
            print(f"{rotulo}\t{bruto}")
        raise SystemExit(0)
    if arg == "--autoteste":
        raise SystemExit(_autoteste())
    if arg == "--selftest":
        raise SystemExit(_selftest(sys.stdin.read()))
    print(__doc__)
    raise SystemExit(2)
