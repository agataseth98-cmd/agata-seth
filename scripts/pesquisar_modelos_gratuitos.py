#!/usr/bin/env python3
"""Rotina de pesquisa/saúde do pool de modelos gratuitos (MEMÓRIAS (377)).

Roda semanal (agata-pesquisa-modelos.timer). NÃO implementa nada: só lê e,
se algo mudou, escreve UMA proposta em propostas/ pro Humano decidir (P-8).
Mesma disciplina do flow de consolidação depois de (371).

Dois modos, nunca misturados (roteamento por capacidade, passo 2; V9, seção 35):

DESCOBERTA (padrão; o timer roda este) -- nenhuma chamada a modelo, nenhuma
escrita no OmniRoute, zero cota:
  1. lê os modelos que o OmniRoute conhece (GET /api/models) em provedores
     CONECTADOS que não estão no pool nem no ROSTER;
  2. lê os últimos resultados do Discovery (GET /api/discovery/results), sem
     disparar varredura nova;
  3. compara com a última descoberta. Mudou -> propostas/modelos-gratuitos-<data>.md
     com a lista de candidatos ("disponível no catálogo", nunca "funciona").

ENSAIO (`--ensaio`, só à mão, com autorização: gasta cota grátis) -- teste de vida:
  1. re-testa cada modelo do pool confirmado (config/modelos-gratuitos.md) e do
     ROSTER de scripts/conselho_remoto.py -- 1 chamada mínima via :20127;
  2. testa até 12 candidatos fora do pool;
  3. com `--scan`, dispara antes o Discovery do OmniRoute (POST /api/discovery/scan);
  4. compara com o último ensaio e, se mudou, escreve a proposta com o rascunho de
     ROSTER. Um `pong` prova conectividade numa amostra, não qualidade (desenho do
     roteamento, seção 8). Benchmark de qualidade é outra peça, com corpus próprio.

Uso: pesquisar_modelos_gratuitos.py [--repo DIR] [--ensaio [--scan]] | --selftest
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
ULTIMO = ESTADO_DIR / "ultimo.json"                     # último ENSAIO
ULTIMA_DESCOBERTA = ESTADO_DIR / "ultima-descoberta.json"
LOG = ESTADO_DIR / "runs.log"
POOL_MD = REPO / "config" / "modelos-gratuitos.md"
CONSELHO = REPO / "scripts" / "conselho_remoto.py"
CAPACIDADES = REPO / "config" / "capivara" / "capacidades.json"

# Reaproveita os MESMOS parâmetros da chamada real (achado 22/09/2026: com
# max_tokens fixo baixo, a sonda reportava Gemini como VAZIO -- na verdade só
# precisa de max_tokens alto pra não queimar tudo em reasoning, confirmado
# testando direto com os parâmetros de baixo. Sem isto, todo modelo que
# precisa de max_tokens>padrão (hoje: gemini/, llama-cpp/nemotron-3.5-lightning)
# aparece falso-VAZIO aqui mesmo funcionando limpo em produção).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import conselho_remoto as _cr  # noqa: E402

# famílias que precisam de chave do Humano -- a rotina só as LEMBRA, nunca as
# adiciona (isso é integração, decisão do Humano + .env + proposta assinada).
CANDIDATOS_COM_CHAVE = ["Mistral AI", "GitHub Models", "HuggingFace Inference",
                        "Cloudflare Workers AI", "NVIDIA NIM"]


def _token_interno():
    """Token interno (X-Agata-Token), de `scripts/token_interno.py` -- arquivo
    próprio, nunca o .env (MEMÓRIAS (629)-(631)). Nunca loga o valor. Sem ele,
    o proxy sanitizador (:20127) recusa a chamada com 403 (MEMÓRIAS (437)).
    Enviado também nas chamadas diretas ao OmniRoute (:20128) por
    simplicidade -- ele não conhece o header e o ignora."""
    _scripts = str(Path(__file__).resolve().parents[1] / "scripts")
    if _scripts not in sys.path:
        sys.path.insert(0, _scripts)
    import token_interno  # noqa: E402  (scripts/token_interno.py)
    return token_interno.ler()


def _http(url, metodo="GET", body=None, timeout=45, classification=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"content-type": "application/json", "X-Agata-Token": _token_interno()}
    if classification is not None:
        headers["X-Agata-Data-Classification"] = classification
    req = urllib.request.Request(url, data=data, method=metodo,
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _sondar(modelo):
    """1 chamada mínima, com os mesmos max_tokens/thinking da chamada real de
    conselho_remoto.py (MAX_TOKENS_POR_MODELO / THINKING_DISABLED_PREFIXOS) --
    não um teto fixo curto. Devolve (estado, detalhe)."""
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": "Responda apenas: pong"}],
        "max_tokens": _cr.MAX_TOKENS_POR_MODELO.get(modelo, _cr.TETO_TOKENS_SAIDA),
    }
    if _cr.DESABILITAR_THINKING and modelo.startswith(_cr.THINKING_DISABLED_PREFIXOS):
        payload["thinking"] = {"type": "disabled"}
    try:
        d = _http(f"{PROXY}/v1/chat/completions", "POST", payload,
                  classification="public")
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


def _modelos_das_filas():
    """(26/10/2026) Os modelos que já estão nas filas da Seth (registro de capacidades). Sem eles,
    o relatório de 25/10 listou como 'candidatos' o Gemini 3.1 Flash-Lite e o 3 Flash, já nas filas."""
    try:
        reg = json.loads(CAPACIDADES.read_text(encoding="utf-8"))
        return sorted({m for fila in (reg.get("filas") or {}).values() for m in fila})
    except (OSError, ValueError, AttributeError):
        return []


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


def _discovery(varrer):
    """Lê os resultados do Discovery. `varrer=True` (só no ensaio com --scan) dispara
    antes uma varredura nova -- escreve no OmniRoute; a descoberta nunca varre."""
    try:
        if varrer:
            _http(f"{OMNIROUTE}/api/discovery/scan", "POST", {}, timeout=20,
                  classification="public")
            time.sleep(30)
        return _http(f"{OMNIROUTE}/api/discovery/results", timeout=20)
    except Exception as e:  # noqa: BLE001
        return {"erro": f"{type(e).__name__}: {e}"}


def _ler_json(caminho):
    if caminho.is_file():
        try:
            return json.loads(caminho.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def descobrir():
    """Modo DESCOBERTA: só GET, nenhuma chamada a modelo. Devolve o estado comparável."""
    conhecidos = set(_pool_confirmado()) | set(_roster_conselho()) | set(_modelos_das_filas())
    candidatos = sorted(_modelos_omniroute_nao_no_pool(conhecidos))
    disc = _discovery(False)
    return {"quando": date.today().isoformat(), "candidatos": candidatos}, disc


def _escrever_descoberta(atual, disc):
    hoje = date.today().isoformat()
    alvo = REPO / "propostas" / f"modelos-gratuitos-{hoje}.md"
    linhas = [
        f"# Descoberta de modelos gratuitos — {hoje}",
        "",
        "_Gerada por `scripts/pesquisar_modelos_gratuitos.py` em modo DESCOBERTA: nenhuma",
        "chamada a modelo, zero cota. NÃO é canon, NÃO implementa nada. Candidato aqui",
        "quer dizer disponível no catálogo do OmniRoute, nunca 'funciona': para testar,",
        "rode à mão `--ensaio` (gasta cota). MEMÓRIAS (377)._",
        "",
        "## Candidatos fora do pool, do ROSTER e das filas (catálogo do OmniRoute)",
        "",
    ] + ([f"- `{m}`" for m in atual["candidatos"]] or ["- (nenhum)"]) + [
        "",
        "## Últimos resultados do Discovery (leitura, sem varredura nova)",
        "",
        "```json",
        json.dumps(disc, ensure_ascii=False, indent=2)[:2000],
        "```",
    ]
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return alvo


def _selftest():
    global _http, _pool_confirmado, _roster_conselho, _modelos_das_filas
    chamadas = []

    def falso_http(url, metodo="GET", body=None, timeout=45, classification=None):
        chamadas.append((metodo, url))
        if url.endswith("/api/models"):
            return {"models": [{"fullModel": "a/novo", "available": True},
                               {"fullModel": "b/pool", "available": True},
                               {"fullModel": "c/fora", "available": False},
                               {"fullModel": "d/fila", "available": True}]}
        return {"ok": True}

    orig = (_http, _pool_confirmado, _roster_conselho, _modelos_das_filas)
    _http, _pool_confirmado, _roster_conselho = falso_http, lambda: ["b/pool"], lambda: []
    _modelos_das_filas = lambda: ["d/fila"]  # noqa: E731
    try:
        atual, _ = descobrir()
        casos = [
            ("descoberta não chama modelo", not any("/chat/completions" in u for _, u in chamadas)),
            ("descoberta não escreve no OmniRoute (só GET)", all(m == "GET" for m, _ in chamadas)),
            ("candidato = disponível e fora do pool, do ROSTER e das filas", atual["candidatos"] == ["a/novo"]),
            ("descoberta lê os resultados do Discovery", any(u.endswith("/api/discovery/results")
                                                            for _, u in chamadas)),
        ]
        chamadas.clear()
        _discovery(True)
        casos.append(("só o --scan dispara varredura (POST)", ("POST", f"{OMNIROUTE}/api/discovery/scan")
                      in chamadas))
    finally:
        _http, _pool_confirmado, _roster_conselho, _modelos_das_filas = orig
    casos.append(("filas lidas do registro real", "ollama-local/qwen3.5-9b-64k:latest" in _modelos_das_filas()))
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


def _log(msg):
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now(timezone.utc).astimezone().isoformat()}] {msg}\n")


def main():
    args = sys.argv[1:]
    if args == ["--selftest"]:
        return _selftest()
    if "--repo" in args:
        global REPO
        REPO = Path(args[args.index("--repo") + 1])

    if "--ensaio" not in args:
        if "--scan" in args:
            print("--scan só vale com --ensaio (a descoberta nunca varre).")
            return 2
        atual, disc = descobrir()
        anterior = _ler_json(ULTIMA_DESCOBERTA)
        ESTADO_DIR.mkdir(parents=True, exist_ok=True)
        ULTIMA_DESCOBERTA.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")
        if atual["candidatos"] == anterior.get("candidatos"):
            _log(f"descoberta: sem mudança. candidatos={atual['candidatos']}")
            print("descoberta: sem mudança -- nenhuma proposta escrita.")
            return 0
        alvo = _escrever_descoberta(atual, disc)
        _log(f"descoberta: MUDOU -> escreveu {alvo.name}. candidatos={atual['candidatos']}")
        print(f"escrito: {alvo}")
        return 0

    confirmados = _pool_confirmado()
    roster = _roster_conselho()
    alvos = list(dict.fromkeys(confirmados + roster))
    resultados = {m: _sondar(m) for m in alvos}

    extras = _modelos_omniroute_nao_no_pool(set(alvos))
    novos = {}
    for m in extras[:12]:            # teto: não martelar 40 modelos
        novos[m] = _sondar(m)

    disc = _discovery("--scan" in args)

    atual = {
        "quando": date.today().isoformat(),
        "pool": {m: r[0] for m, r in resultados.items()},
        "novos_ok": sorted(m for m, r in novos.items() if r[0] == "OK"),
    }
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    anterior = _ler_json(ULTIMO)

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
