#!/usr/bin/env python3
"""registro_pedidos.py — grava pergunta e resposta da Seth para o benchmark de roteamento.

Roteamento por capacidade, passo 2b, opção 3 (V9, seção 35; decisão do Humano em 23/10/2026:
"30 dias e grava a resposta também"). Serve para comparar, depois, o corpus sintético com o
tráfego real e rotular se a rota foi boa.

Regras:
- **Desligado por padrão.** Só grava com `SETH_REGISTRO_PEDIDOS=1` no ambiente do gateway.
- **Só o texto do Humano e a resposta em texto do modelo.** Saída de ferramenta, prompt de
  sistema e hidratação nunca entram; volta do agente sem texto (só chamada de ferramenta) não grava.
- **Redação antes de gravar:** a régua de segredo e a de dados pessoais de `sanitizar.py`
  trocam cada achado por `[REDIGIDO:<rótulo>]`. O texto original não toca o disco.
- **Fora do repositório:** `~/.local/share/agata/pedidos/AAAA-MM-DD.jsonl`, diretório 0700,
  arquivo 0600, uma linha por resposta, escrita sob `flock`.
- **Retenção de 30 dias:** arquivo de dia mais antigo que isso é apagado a cada gravação.
- **Nunca derruba a resposta:** qualquer erro aqui vira uma linha no journal e só.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import sys
import time
from pathlib import Path

DIR = Path(os.environ.get("SETH_REGISTRO_PEDIDOS_DIR", os.path.expanduser("~/.local/share/agata/pedidos")))
RETENCAO_DIAS = 30
TETO_CHARS = 20000          # por campo; o resto sai marcado
_RE_DIA = re.compile(r"^(\d{4}-\d{2}-\d{2})\.jsonl$")


def ligado() -> bool:
    return os.environ.get("SETH_REGISTRO_PEDIDOS") == "1"


def _texto(conteudo) -> str:
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        return "\n".join(p.get("text", "") for p in conteudo
                         if isinstance(p, dict) and p.get("type") == "text")
    return ""


def ultima_pergunta(msgs: list) -> str:
    """Texto da última mensagem do usuário (o Humano), nada mais."""
    for m in reversed(msgs or []):
        if isinstance(m, dict) and m.get("role") == "user":
            return _texto(m.get("content"))
    return ""


def acumular_sse(linha: bytes, estado: dict) -> None:
    """Soma o `delta.content` de uma linha `data:` do SSE em estado['resposta']. Pura."""
    if not linha.startswith(b"data:"):
        return
    corpo = linha[5:].strip()
    if not corpo or corpo == b"[DONE]":
        return
    try:
        o = json.loads(corpo)
        c = (o.get("choices") or [{}])[0].get("delta", {}).get("content")
    except (ValueError, AttributeError, IndexError, TypeError):
        return
    if isinstance(c, str) and len(estado.get("resposta", "")) < TETO_CHARS:
        estado["resposta"] = estado.get("resposta", "") + c


def resposta_json(corpo: bytes) -> str:
    try:
        return _texto(json.loads(corpo)["choices"][0]["message"].get("content"))
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        return ""


def redigir(texto: str, varrer=None, varrer_pessoal=None, nomes=None) -> tuple[str, list[str]]:
    """Troca cada achado das réguas por [REDIGIDO:<rótulo>]. Devolve (texto, rótulos)."""
    if varrer is None or varrer_pessoal is None:
        import sanitizar  # noqa: E402  (mesmo diretório)
        varrer, varrer_pessoal = sanitizar.varrer, sanitizar.varrer_pessoal
        nomes = sanitizar._nomes_projeto() if nomes is None else nomes
    rotulos = []
    for _ in range(50):  # um achado por vez: as posições mudam depois de cada troca
        achados = varrer(texto) + varrer_pessoal(texto, nomes or [])
        if not achados:
            break
        a = min(achados, key=lambda x: x["pos"])
        fim = _fim_do_achado(texto, a)
        texto = texto[:a["pos"]] + f"[REDIGIDO:{a['padrao_rotulo']}]" + texto[fim:]
        rotulos.append(a["padrao_rotulo"])
    else:
        return "[REDIGIDO: achados demais]", rotulos
    return texto, rotulos


def _fim_do_achado(texto: str, achado: dict) -> int:
    """O achado traz só a posição inicial e o tamanho redigido ('abcd…[N chars]')."""
    m = re.search(r"\[(\d+) chars", achado.get("trecho_redigido", ""))
    return achado["pos"] + (int(m.group(1)) if m else 1)


def _podar(agora: float) -> None:
    limite = time.strftime("%Y-%m-%d", time.localtime(agora - RETENCAO_DIAS * 86400))
    for f in DIR.iterdir():
        m = _RE_DIA.match(f.name)
        if m and m.group(1) < limite:
            f.unlink()


def gravar(pergunta: str, resposta: str, meta: dict, agora: float | None = None, **regua) -> bool:
    """Grava uma linha. Não grava sem resposta em texto. Nunca levanta."""
    try:
        if not resposta.strip():
            return False
        agora = time.time() if agora is None else agora
        p, rp = redigir(pergunta[:TETO_CHARS], **regua)
        r, rr = redigir(resposta[:TETO_CHARS], **regua)
        linha = dict(meta, ts=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(agora)),
                     pergunta=p, resposta=r, redigidos=sorted(set(rp + rr)))
        DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(DIR, 0o700)
        alvo = DIR / (time.strftime("%Y-%m-%d", time.localtime(agora)) + ".jsonl")
        fd = os.open(alvo, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
        _podar(agora)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"registro_pedidos: não gravou ({e.__class__.__name__})", file=sys.stderr, flush=True)
        return False


def _selftest() -> int:
    import tempfile
    global DIR
    falso_varrer = lambda t: [{"padrao_rotulo": "segredo-x", "pos": t.index("sk-ABCDEF"),  # noqa: E731
                               "trecho_redigido": "sk-A…[9 chars]"}] if "sk-ABCDEF" in t else []
    falso_pessoal = lambda t, n: [{"padrao_rotulo": "pessoal-email", "pos": t.index("a@b.co"),  # noqa: E731
                                   "trecho_redigido": "a@b.…[6 chars]"}] if "a@b.co" in t else []
    regua = {"varrer": falso_varrer, "varrer_pessoal": falso_pessoal, "nomes": []}
    estado = {}
    for l in (b'data: {"choices":[{"delta":{"content":"Ol"}}]}', b": ka",
              b'data: {"choices":[{"delta":{"content":"a."}}]}', b"data: [DONE]"):
        acumular_sse(l, estado)
    orig = DIR
    with tempfile.TemporaryDirectory() as tmp:
        DIR = Path(tmp) / "pedidos"
        agora = time.mktime(time.strptime("2026-10-23 12:00", "%Y-%m-%d %H:%M"))
        DIR.mkdir()
        (DIR / "2026-09-01.jsonl").write_text("{}\n")
        (DIR / "2026-10-20.jsonl").write_text("{}\n")
        (DIR / "notas.txt").write_text("x")
        ok = gravar("chave sk-ABCDEF e email a@b.co", "Resposta.", {"rota": "seth-livre"}, agora, **regua)
        sem = gravar("pergunta", "   ", {}, agora, **regua)
        arq = DIR / "2026-10-23.jsonl"
        linha = json.loads(arq.read_text().splitlines()[-1]) if arq.exists() else {}
        modo_arq = oct(arq.stat().st_mode & 0o777) if arq.exists() else None
        modo_dir = oct(DIR.stat().st_mode & 0o777)
        restantes = sorted(f.name for f in DIR.iterdir())
    DIR = orig
    casos = [
        ("SSE: soma os deltas e ignora keepalive e [DONE]", estado.get("resposta") == "Ola."),
        ("JSON: extrai o content", resposta_json(b'{"choices":[{"message":{"content":"x"}}]}') == "x"),
        ("pergunta = última mensagem do usuário", ultima_pergunta(
            [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"},
             {"role": "user", "content": [{"type": "text", "text": "c"}]}, {"role": "tool", "content": "t"}]) == "c"),
        ("grava quando há resposta", ok is True),
        ("sem resposta em texto não grava", sem is False),
        ("segredo e e-mail redigidos antes do disco", "sk-ABCDEF" not in json.dumps(linha)
         and "a@b.co" not in json.dumps(linha) and linha.get("redigidos") == ["pessoal-email", "segredo-x"]),
        ("o resto do texto fica", linha.get("pergunta", "").startswith("chave [REDIGIDO:segredo-x] e email")),
        ("arquivo 0600 e diretório 0700", modo_arq == "0o600" and modo_dir == "0o700"),
        ("retenção: apaga dia com mais de 30 dias, mantém o recente e o que não é dia",
         restantes == ["2026-10-20.jsonl", "2026-10-23.jsonl", "notas.txt"]),
    ]
    antes = os.environ.pop("SETH_REGISTRO_PEDIDOS", None)
    try:
        desligado = not ligado()
        os.environ["SETH_REGISTRO_PEDIDOS"] = "sim"
        so_com_1 = not ligado()
        os.environ["SETH_REGISTRO_PEDIDOS"] = "1"
        casos.append(("desligado por padrão; liga só com =1", desligado and so_com_1 and ligado()))
    finally:
        os.environ.pop("SETH_REGISTRO_PEDIDOS", None)
        if antes is not None:
            os.environ["SETH_REGISTRO_PEDIDOS"] = antes
    for nome, passou in casos:
        print(f"{'PASS' if passou else 'FALHA'}  {nome}")
    falhas = sum(not p for _, p in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(_selftest())
    print(__doc__)
    sys.exit(2)
