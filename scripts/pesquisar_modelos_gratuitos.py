#!/usr/bin/env python3
"""Rotina de pesquisa/saúde do pool de modelos gratuitos (MEMÓRIAS (377)).

Roda semanal (agata-pesquisa-modelos.timer). NÃO implementa nada: só sonda e,
se algo mudou, escreve UMA proposta em propostas/ pro Humano decidir (P-8).
Mesma disciplina do flow de consolidação depois de (371).

O que faz, tudo read-only:
  1. re-testa cada modelo do pool confirmado (config/modelos-gratuitos.md) e do
     ROSTER de scripts/conselho_remoto.py -- 1 chamada mínima via :20127.
  2. testa os modelos que o OmniRoute conhece (/api/models) em provedores
     CONECTADOS mas que não estão no pool.
  3. dispara o Discovery do próprio OmniRoute (POST /api/discovery/scan) e lê os
     resultados.
  4. compara com o último run. Nada mudou -> só loga. Mudou -> escreve
     propostas/modelos-gratuitos-<data>.md com um rascunho de ROSTER e o
     lembrete das famílias que dependem de chave do Humano (Mistral, GitHub
     Models, HuggingFace).

Uso: pesquisar_modelos_gratuitos.py [--repo DIR] [--sem-discovery]
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(os.environ.get("AGATA_REPO", os.path.expanduser("~/agata")))
PROXY = os.environ.get("AGATA_PROXY", "http://127.0.0.1:20127")
OMNIROUTE = os.environ.get("AGATA_OMNIROUTE", "http://127.0.0.1:20128")
ESTADO_DIR = Path(os.path.expanduser("~/.cache/agata/pesquisa-modelos"))
ULTIMO = ESTADO_DIR / "ultimo.json"
LOG = ESTADO_DIR / "runs.log"
POOL_MD = REPO / "config" / "modelos-gratuitos.md"
CONSELHO = REPO / "scripts" / "conselho_remoto.py"

# famílias que precisam de chave do Humano -- a rotina só as LEMBRA, nunca as
# adiciona (isso é integração, decisão do Humano + .env + proposta assinada).
CANDIDATOS_COM_CHAVE = ["Mistral AI", "GitHub Models", "HuggingFace Inference",
                        "Cloudflare Workers AI", "NVIDIA NIM"]


def _http(url, metodo="GET", body=None, timeout=45):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=metodo,
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _sondar(modelo):
    """1 chamada mínima. Devolve (estado, detalhe)."""
    try:
        d = _http(f"{PROXY}/v1/chat/completions", "POST", {
            "model": modelo,
            "messages": [{"role": "user", "content": "Responda apenas: pong"}],
            "max_tokens": 24,
        })
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", errors="replace")[:200]
        if e.code in (402,) or "payment" in corpo.lower() or "billing" in corpo.lower():
            return "PAGO", f"HTTP {e.code}: {corpo}"
        return "ERRO", f"HTTP {e.code}: {corpo}"
    except Exception as e:  # noqa: BLE001
        return "ERRO", f"{type(e).__name__}: {e}"
    ch = (d.get("choices") or [{}])[0]
    txt = (ch.get("message", {}).get("content") or "").strip()
    uso = d.get("usage") or {}
    rt = int((uso.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0)
    ts = int(uso.get("completion_tokens", 0) or 0)
    if not txt:
        return "VAZIO", f"finish={ch.get('finish_reason')}, reasoning={rt}/{ts}"
    if ch.get("finish_reason") == "length" and rt and rt >= ts * 0.9:
        return "REASONING_BURN", f"{rt}/{ts} tokens em reasoning"
    return "OK", f"{txt[:40]!r} ({ts} tok)"


def _pool_confirmado():
    """ids na tabela 'Confirmado funcionando' do config/modelos-gratuitos.md."""
    if not POOL_MD.is_file():
        return []
    txt = POOL_MD.read_text(encoding="utf-8")
    m = re.search(r"## Confirmado funcionando.*?\n(.*?)\n##", txt, re.S)
    bloco = m.group(1) if m else ""
    ids = []
    for ln in bloco.splitlines():
        mm = re.match(r"\|\s*`([^`]+)`", ln)
        if mm and "/" in mm.group(1):
            ids.append(mm.group(1))
    return ids


def _roster_conselho():
    if not CONSELHO.is_file():
        return []
    txt = CONSELHO.read_text(encoding="utf-8")
    m = re.search(r"ROSTER\s*=\s*\[(.*?)\]", txt, re.S)
    return re.findall(r'"([^"]+/[^"]+)"', m.group(1)) if m else []


def _modelos_omniroute_nao_no_pool(ja_conhecidos):
    try:
        d = _http(f"{OMNIROUTE}/api/models")
    except Exception:  # noqa: BLE001
        return []
    fora = []
    for m in d.get("models", []):
        full = m.get("fullModel") or m.get("model")
        if full and full not in ja_conhecidos and m.get("available"):
            fora.append(full)
    return fora


def _discovery(fazer):
    if not fazer:
        return {"pulado": True}
    try:
        _http(f"{OMNIROUTE}/api/discovery/scan", "POST", {}, timeout=20)
        time.sleep(30)
        return _http(f"{OMNIROUTE}/api/discovery/results", timeout=20)
    except Exception as e:  # noqa: BLE001
        return {"erro": f"{type(e).__name__}: {e}"}


def _log(msg):
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now(timezone.utc).astimezone().isoformat()}] {msg}\n")


def main():
    args = sys.argv[1:]
    if "--repo" in args:
        global REPO
        REPO = Path(args[args.index("--repo") + 1])
    sem_disc = "--sem-discovery" in args

    confirmados = _pool_confirmado()
    roster = _roster_conselho()
    alvos = list(dict.fromkeys(confirmados + roster))
    resultados = {m: _sondar(m) for m in alvos}

    extras = _modelos_omniroute_nao_no_pool(set(alvos))
    novos = {}
    for m in extras[:12]:            # teto: não martelar 40 modelos
        novos[m] = _sondar(m)

    disc = _discovery(not sem_disc)

    atual = {
        "quando": date.today().isoformat(),
        "pool": {m: r[0] for m, r in resultados.items()},
        "novos_ok": sorted(m for m, r in novos.items() if r[0] == "OK"),
    }
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    anterior = {}
    if ULTIMO.is_file():
        try:
            anterior = json.loads(ULTIMO.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            anterior = {}

    mudou = (atual["pool"] != anterior.get("pool")
             or atual["novos_ok"] != anterior.get("novos_ok", []))
    ULTIMO.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")

    if not mudou:
        _log(f"sem mudança. pool={atual['pool']}")
        print("sem mudança no pool -- nenhuma proposta escrita.")
        return 0

    hoje = date.today().isoformat()
    alvo = REPO / "propostas" / f"modelos-gratuitos-{hoje}.md"
    ok_agora = sorted(m for m, r in resultados.items() if r[0] == "OK")
    linhas = [
        f"# Pesquisa de modelos gratuitos — {hoje}",
        "",
        "_Gerada por `scripts/pesquisar_modelos_gratuitos.py`. NÃO é canon, NÃO",
        "implementa nada. Se aprovada, o Humano aplica à mão: edita",
        "`config/modelos-gratuitos.md` + `ROSTER` de `conselho_remoto.py` (proposta",
        "assinada) e os combos/roteador do OmniRoute (UI). MEMÓRIAS (377)._",
        "",
        "## Pool re-testado",
        "",
        "| modelo | estado | detalhe |",
        "|---|---|---|",
    ]
    for m, (est, det) in sorted(resultados.items()):
        linhas.append(f"| `{m}` | {est} | {det} |")
    linhas += ["", "## Modelos do OmniRoute fora do pool que responderam OK", ""]
    linhas += [f"- `{m}`" for m in sorted(novos) if novos[m][0] == "OK"] or ["- (nenhum)"]
    linhas += [
        "",
        "## Rascunho de ROSTER (só os OK agora, ordem = a atual + novos no fim)",
        "",
        "```python",
        "ROSTER = [",
    ] + [f'    "{m}",' for m in ok_agora] + [
        "]",
        "```",
        "",
        f"## Discovery do OmniRoute",
        "",
        "```json",
        json.dumps(disc, ensure_ascii=False, indent=2)[:2000],
        "```",
        "",
        "## Famílias que dependem de chave do Humano (não integradas aqui)",
        "",
    ] + [f"- {c}" for c in CANDIDATOS_COM_CHAVE] + [
        "",
        "Pra integrar uma: pôr a chave em `~/.config/agata/.env`, adicionar o",
        "provedor no OmniRoute, 1 teste ao vivo, e então proposta assinada.",
    ]
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    _log(f"MUDOU -> escreveu {alvo.name}. ok_agora={ok_agora}")
    print(f"escrito: {alvo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
