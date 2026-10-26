#!/usr/bin/env python3
"""cache_conselho.py — cache do Conselho: memória append-only comum a todos os modelos, NÃO canônica.

Decisão do Humano, MEMÓRIAS (849) / V9 §37, fase M2: todos os modelos do Conselho escrevem e leem o
mesmo registro; dele, uma vez por semana, sai a Memória Canônica (M3); o cache reinicia a cada 15 dias
com trava (M4). Este arquivo é só o registro:

  - fora do repositório (não é canon): ~/.local/share/agata/cache-conselho/cache.jsonl (0700/0600);
  - append-only com cadeia: cada linha leva `ant` (sha256 da linha anterior) e `h` (sha256 dela
    mesma sem `h`); `verificar` recalcula tudo; trava `flock` + escrita + fsync do arquivo e da pasta;
  - na gravação: SEGREDO recusa a nota (régua do sanitizar/P-1); DADO PESSOAL (e-mail, CPF, CNPJ,
    telefone, nomes de projeto e a lista privada do P-20) vira marca — todos leem tudo;
  - D5: até 20 MB gravados por dia; acima disso recusa e avisa.

Quem escreve: a Seth, pelo diário (o escriba espelha cada /diario aqui); Claude Code, Codex e o
Conselho Remoto por este CLI. Quem lê: todos — a Seth por `maquina_verificar cache_conselho`.

  cache_conselho.py anotar --autor NOME [--tipo nota|fato|decisao|pendencia|diario] [--fonte X] TEXTO
  cache_conselho.py ler [--n 20] [--autor NOME]
  cache_conselho.py verificar
  cache_conselho.py --selftest
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI))
os.environ.setdefault("SETH_REPO", str(_AQUI.parents[1]))  # o sanitizar lê a régua do checkout, não de ~/agata
ARQ = Path(os.environ.get("AGATA_CACHE_CONSELHO",
                          os.path.expanduser("~/.local/share/agata/cache-conselho/cache.jsonl")))
TZ = ZoneInfo("America/Sao_Paulo")
TIPOS = ("nota", "fato", "decisao", "pendencia", "diario")
MAX_TEXTO = 4000
LIMITE_DIA = 20 * 1024 * 1024  # D5
LISTA_P20 = Path(os.environ.get("AGATA_P20_LISTA",
                                os.path.expanduser("~/.config/agata/identificadores-pessoais.txt")))
ZERO = "0" * 64


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _canon(reg: dict) -> bytes:
    return json.dumps(reg, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _pessoais_p20() -> list[tuple[str, re.Pattern]]:
    """Regex da lista privada do P-20 ("rotulo|regex ERE|prova"); nunca devolve a prova."""
    out = []
    try:
        for l in LISTA_P20.read_text(encoding="utf-8").splitlines():
            partes = l.split("|")
            if len(partes) >= 2 and partes[0].strip() and not l.lstrip().startswith("#"):
                try:
                    out.append((partes[0].strip(), re.compile(partes[1])))
                except re.error:
                    continue
    except OSError:
        pass
    return out


def filtrar(texto: str) -> str:
    """Recusa segredo (ValueError); troca dado pessoal por marca. Devolve o texto a gravar."""
    import sanitizar
    if sanitizar.varrer(texto):
        raise ValueError("a nota contém segredo (régua do P-1) — não foi gravada")
    regras = list(sanitizar.PADROES_PESSOAIS) + _pessoais_p20()
    regras += [("pessoal-nome-projeto", re.compile(r"(?<!\w)" + re.escape(n) + r"(?!\w)", re.IGNORECASE))
               for n in sanitizar._nomes_projeto()]
    for rotulo, rx in regras:
        texto = rx.sub(f"[{rotulo} removido]", texto)
    return texto


def _linhas() -> list[bytes]:
    try:
        return [l for l in ARQ.read_bytes().split(b"\n") if l.strip()]
    except FileNotFoundError:
        return []


def anotar(autor: str, texto: str, tipo: str = "nota", fonte: str | None = None) -> dict:
    autor, texto = (autor or "").strip(), (texto or "").strip()
    if not autor or len(autor) > 80:
        raise ValueError("autor obrigatório (até 80 caracteres)")
    if tipo not in TIPOS:
        raise ValueError(f"tipo inválido; use um de {', '.join(TIPOS)}")
    if not texto or len(texto) > MAX_TEXTO:
        raise ValueError(f"texto obrigatório (até {MAX_TEXTO} caracteres)")
    texto = filtrar(texto)
    ARQ.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(ARQ.parent, 0o700)
    with open(ARQ.with_suffix(".lock"), "a") as trava:
        fcntl.flock(trava, fcntl.LOCK_EX)
        linhas = _linhas()
        agora = datetime.now(TZ)
        hoje = agora.strftime("%Y-%m-%d")
        gravado_hoje = sum(len(l) + 1 for l in linhas if json.loads(l).get("ts", "").startswith(hoje))
        reg = {"n": (json.loads(linhas[-1])["n"] + 1) if linhas else 1,
               "ts": agora.strftime("%Y-%m-%dT%H:%M:%S%z"), "autor": autor, "tipo": tipo,
               "texto": texto, "fonte": (fonte or None), "ant": _sha(linhas[-1]) if linhas else ZERO}
        reg["h"] = _sha(_canon(reg))
        linha = _canon(reg) + b"\n"
        if gravado_hoje + len(linha) > LIMITE_DIA:
            raise ValueError("limite diário de 20 MB do cache atingido (D5) — nota não gravada")
        fd = os.open(ARQ, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, linha)
            os.fsync(fd)
        finally:
            os.close(fd)
        dfd = os.open(ARQ.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    return {"ok": True, "n": reg["n"], "h": reg["h"][:12]}


def ler(n: int = 20, autor: str | None = None) -> list[dict]:
    regs = [json.loads(l) for l in _linhas()]
    if autor:
        regs = [r for r in regs if r.get("autor", "").lower() == autor.lower()]
    return regs[-n:]


def verificar() -> tuple[bool, int, str]:
    ant = ZERO
    linhas = _linhas()
    for i, l in enumerate(linhas, 1):
        try:
            r = json.loads(l)
        except ValueError:
            return False, i, f"linha {i} não é JSON"
        h = r.pop("h", "")
        if r.get("ant") != ant:
            return False, i, f"linha {i}: cadeia quebrada (ant não bate com a linha anterior)"
        if _sha(_canon(r)) != h:
            return False, i, f"linha {i}: conteúdo alterado (h não bate)"
        ant = _sha(l)
    return True, len(linhas), "cadeia íntegra"


def resumo_hidratacao(k: int = 3, max_chars: int = 160) -> str:
    """Uma linha para a hidratação da Seth: quantas entradas e as últimas k, curtas."""
    regs = [json.loads(l) for l in _linhas()]
    if not regs:
        return ""
    ult = "; ".join(f"({r['n']}) {r['autor']}, {r['ts'][:16]}: {r['texto'][:max_chars]}" for r in regs[-k:])
    return (f"CACHE-CONSELHO (não canônico; memória comum do Conselho; {len(regs)} entradas; confira antes "
            f"de citar; leia mais com maquina_verificar cache_conselho): {ult}")


def _cli(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--selftest":
        return _selftest()
    def opt(nome, padrao=None):
        return argv[argv.index(nome) + 1] if nome in argv else padrao
    if argv[0] == "anotar":
        resto = [a for i, a in enumerate(argv[1:], 1)
                 if a not in ("--autor", "--tipo", "--fonte") and argv[i - 1] not in ("--autor", "--tipo", "--fonte")]
        try:
            print(json.dumps(anotar(opt("--autor", ""), " ".join(resto), opt("--tipo", "nota"), opt("--fonte")),
                             ensure_ascii=False))
            return 0
        except ValueError as e:
            print(f"recusado: {e}", file=sys.stderr)
            return 2
    if argv[0] == "ler":
        n = int(opt("--n", "20"))
        regs = ler(max(1, min(n, 50)), opt("--autor"))
        if not regs:
            print("cache do Conselho vazio")
        for r in regs:
            print(f"({r['n']}) {r['ts']} · {r['autor']} · {r['tipo']}" + (f" · fonte: {r['fonte']}" if r.get("fonte") else "")
                  + f"\n{r['texto']}\n")
        return 0
    if argv[0] == "verificar":
        ok, n, msg = verificar()
        print(f"{'OK' if ok else 'FALHA'}: {msg} ({n} linhas)")
        return 0 if ok else 1
    print(__doc__)
    return 2


def _selftest() -> int:
    import tempfile
    global ARQ, LISTA_P20
    salvo = (ARQ, LISTA_P20)
    casos = []
    with tempfile.TemporaryDirectory() as d:
        ARQ = Path(d) / "c" / "cache.jsonl"
        LISTA_P20 = Path(d) / "p20.txt"
        LISTA_P20.write_text("apelido|Zuleica[0-9]+|Zuleica42\n", encoding="utf-8")
        try:
            a = anotar("Seth", "o gateway reiniciou às 11h04", "fato")
            b = anotar("Claude Code", "escreva para fulano@exemplo.com e Zuleica42", "nota")
            regs = ler()
            casos += [
                ("grava e numera em sequência", a["n"] == 1 and b["n"] == 2 and len(regs) == 2),
                ("dado pessoal vira marca (padrão e lista P-20)", "fulano@" not in regs[1]["texto"]
                 and "Zuleica42" not in regs[1]["texto"] and "[pessoal-email removido]" in regs[1]["texto"]),
                ("cadeia íntegra", verificar()[0]),
                ("pasta 0700 e arquivo 0600", oct(os.stat(ARQ.parent).st_mode)[-3:] == "700"
                 and oct(os.stat(ARQ).st_mode)[-3:] == "600"),
                ("resumo para a hidratação traz as últimas", "(2) Claude Code" in resumo_hidratacao()),
            ]
            try:
                anotar("Seth", "chave sk-ant-api03-" + "A" * 40, "nota")
                casos.append(("segredo é recusado", False))
            except ValueError:
                casos.append(("segredo é recusado", len(ler()) == 2))
            for ruim in (("", "x", "nota"), ("Seth", "", "nota"), ("Seth", "x", "inventado")):
                try:
                    anotar(*ruim)
                    casos.append((f"recusa entrada inválida {ruim[2]!r}", False))
                except ValueError:
                    casos.append((f"recusa entrada inválida {ruim[2]!r}", True))
            dados = ARQ.read_bytes().replace(b"11h04", b"11h05")
            ARQ.write_bytes(dados)
            casos.append(("alteração de um byte é detectada", not verificar()[0]))
        finally:
            ARQ, LISTA_P20 = salvo
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
