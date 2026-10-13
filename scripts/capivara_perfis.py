#!/usr/bin/env python3
"""Capivara — perfis de capacidade dos modelos das filas da Seth (MEMÓRIAS (667)).

1ª peça do projeto Capivara (observatório dos modelos, (44)): mede o que cada modelo
das filas aguenta — janela de contexto e saída máxima — e grava em
`config/capivara/perfis-modelos.json`. Lê fatos, nunca escreve canon.

Fontes, nesta ordem: `/v1/models` do OmniRoute (o que o provedor declara); `num_ctx`
do Ollama para os locais; `config/capivara/janelas-documentadas.json` (só documentação
oficial do provedor). Sem fonte = `nao_medido`, tratado como PEQUENO — nunca como grande.

Para que serve:
- **Fila longa.** Cada fila da conversa ganha uma variante `<fila>-longo`, mesma ordem,
  só com modelos de janela >= JANELA_LONGA. O `seth_gateway` usa a variante quando o
  pedido não cabe no menor modelo da fila base (o local de 64k, um `nao_medido`).
- **Janela do LibreChat.** `janela_agente()` = min(teto de economia, menor janela das
  filas longas) − reserva da hidratação: o número que o mostrador do LibreChat exibe é a
  capacidade garantida do sistema, calculada, não chutada.

Uso:
  capivara_perfis.py                    mede e grava o perfil
  capivara_perfis.py --conferir         mede e mostra o que mudou (saída 1 se mudou)
  capivara_perfis.py --sincronizar-filas  cria/atualiza as filas -longo no OmniRoute
  capivara_perfis.py --janela-agente    imprime a janela calculada para o Agent
  capivara_perfis.py --selftest
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PERFIS = RAIZ / "config" / "capivara" / "perfis-modelos.json"
DOCUMENTADAS = RAIZ / "config" / "capivara" / "janelas-documentadas.json"
FILAS_CONVERSA = ("seth-rapido", "seth-livre", "seth-pesado")
SUFIXO_LONGO = "-longo"
JANELA_LONGA = 128000        # modelo entra na fila -longo se aguentar isto
RESERVA_SAIDA = 8000         # tokens deixados para a resposta
RESERVA_HIDRATACAO = 4000    # o gateway injeta ~3 mil tokens que o LibreChat não conta
JANELA_DESCONHECIDA = 32768  # `nao_medido` vale isto para o limiar: pequeno, de propósito
OLLAMA = "http://127.0.0.1:11434"


# --- cálculo (puro, sem rede: o gateway importa só isto) ----------------------
def janela(perfis: dict, modelo: str) -> int:
    p = (perfis.get("modelos") or {}).get(modelo) or {}
    return int(p["janela"]) if p.get("janela") else JANELA_DESCONHECIDA


def fila_longa(perfis: dict, fila: str) -> list[str]:
    return [m for m in (perfis.get("filas") or {}).get(fila, []) if janela(perfis, m) >= JANELA_LONGA]


def limiar_tokens(perfis: dict, fila: str) -> int | None:
    """Maior pedido (tokens) que cabe em TODOS os modelos da fila base; None se a fila
    não está no perfil (o gateway então não troca nada)."""
    modelos = (perfis.get("filas") or {}).get(fila)
    if not modelos:
        return None
    return min(janela(perfis, m) for m in modelos) - RESERVA_SAIDA


def janela_agente(perfis: dict, teto_economia: int) -> int:
    longas = [janela(perfis, m) for f in FILAS_CONVERSA for m in fila_longa(perfis, f)]
    piso = min(longas) if longas else min(janela(perfis, m) for f in FILAS_CONVERSA
                                          for m in (perfis.get("filas") or {}).get(f, []))
    return min(teto_economia, piso) - RESERVA_HIDRATACAO


def carregar(caminho: Path = PERFIS) -> dict:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# --- medição (rede, só leitura) ---------------------------------------------------
def _q():
    sys.path.insert(0, str(RAIZ / "scripts"))
    import queda_por_elo as q  # noqa: E402  (filas, token interno, abridor sem proxy)
    return q


def _janelas_omniroute(q) -> dict:
    req = urllib.request.Request(q.PROXY + "/v1/models", headers={"X-Agata-Token": q._token_interno()})
    with q._SEM_PROXY.open(req, timeout=30) as r:
        dados = json.load(r)
    return {m["id"]: (m.get("context_length") or m.get("max_input_tokens"), m.get("max_output_tokens"))
            for m in dados.get("data", []) if isinstance(m, dict) and m.get("id")}


def _num_ctx_ollama(q, modelo: str) -> int | None:
    req = urllib.request.Request(OLLAMA + "/api/show", json.dumps({"model": modelo.split("/", 1)[1]}).encode(),
                                 {"Content-Type": "application/json"})
    try:
        with q._SEM_PROXY.open(req, timeout=15) as r:
            params = json.load(r).get("parameters", "")
    except OSError:
        return None
    for linha in params.splitlines():
        partes = linha.split()
        if len(partes) == 2 and partes[0] == "num_ctx":
            return int(partes[1])
    return None


def medir() -> dict:
    q = _q()
    filas = q.ler_filas(quais=FILAS_CONVERSA + ("seth-codigo",))
    omni = _janelas_omniroute(q)
    doc = json.loads(DOCUMENTADAS.read_text(encoding="utf-8")).get("modelos", {})
    modelos = {}
    for m in sorted({x for ordem in filas.values() for x in ordem}):
        if m.startswith("ollama-local/"):
            n = _num_ctx_ollama(q, m)
            modelos[m] = {"janela": n, "saida_max": None, "fonte": "ollama num_ctx" if n else "nao_medido"}
        elif m in omni and omni[m][0]:
            modelos[m] = {"janela": omni[m][0], "saida_max": omni[m][1], "fonte": "omniroute /v1/models"}
        elif m in doc:
            modelos[m] = {"janela": doc[m]["janela"], "saida_max": doc[m].get("saida_max"),
                          "fonte": "documentação oficial: " + doc[m]["fonte"]}
        else:
            modelos[m] = {"janela": None, "saida_max": None, "fonte": "nao_medido"}
    return {"_como_usar": "Gerado por scripts/capivara_perfis.py — não editar à mão; rode de novo quando as filas "
                          "ou os modelos mudarem. MEMÓRIAS (667).",
            "medido_em": time.strftime("%Y-%m-%d"), "filas": filas, "modelos": modelos}


def sincronizar_filas(perfis: dict) -> list[str]:
    """Cria ou atualiza `<fila>-longo` no OmniRoute (idempotente). Escreve no banco do
    OmniRoute: faça backup do storage.sqlite antes."""
    q = _q()
    with q._SEM_PROXY.open(q.OMNIROUTE + "/api/combos", timeout=15) as r:
        bruto = json.load(r)
    lista = bruto if isinstance(bruto, list) else next(bruto[k] for k in ("combos", "data", "items")
                                                      if isinstance(bruto.get(k), list))
    por_nome = {c.get("name"): c for c in lista if isinstance(c, dict)}
    feito = []
    for fila in FILAS_CONVERSA:
        base = por_nome.get(fila)
        if base is None:
            feito.append(f"{fila}: não existe — pulada")
            continue
        quero = fila_longa(perfis, fila)
        modelos = [m for m in base["models"] if m.get("model") in quero]
        nome = fila + SUFIXO_LONGO
        atual = por_nome.get(nome)
        if atual is not None:
            if [m.get("model") for m in atual.get("models", [])] == quero:
                feito.append(f"{nome}: já em dia ({len(quero)} modelos)")
                continue
            corpo, metodo, url = dict(atual, models=modelos), "PUT", f"{q.OMNIROUTE}/api/combos/{atual['id']}"
        else:
            corpo = {k: v for k, v in base.items() if k not in ("id", "_id", "createdAt", "updatedAt")}
            corpo.update(name=nome, models=[{k: v for k, v in m.items() if k != "id"} for m in modelos])
            metodo, url = "POST", f"{q.OMNIROUTE}/api/combos"
        req = urllib.request.Request(url, json.dumps(corpo).encode(), {"Content-Type": "application/json"},
                                     method=metodo)
        with q._SEM_PROXY.open(req, timeout=15) as r:
            feito.append(f"{nome}: {metodo} {r.status} ({len(quero)} modelos: {', '.join(quero)})")
    return feito


def _selftest() -> int:
    p = {"filas": {"seth-rapido": ["a/grande", "b/nao-medido", "ollama-local/x"],
                   "seth-livre": ["a/grande", "c/medio", "ollama-local/x"],
                   "seth-pesado": ["d/enorme", "ollama-local/x"]},
         "modelos": {"a/grande": {"janela": 256000}, "b/nao-medido": {"janela": None},
                     "c/medio": {"janela": 128000}, "d/enorme": {"janela": 1048576},
                     "ollama-local/x": {"janela": 65536}}}
    casos = [
        ("nao_medido é tratado como pequeno", janela(p, "b/nao-medido") == JANELA_DESCONHECIDA),
        ("fila longa tira o local e o nao_medido", fila_longa(p, "seth-rapido") == ["a/grande"]),
        ("fila longa mantém a ordem e quem tem >= 128k", fila_longa(p, "seth-livre") == ["a/grande", "c/medio"]),
        ("limiar da fila base = menor janela − saída", limiar_tokens(p, "seth-livre") == 65536 - RESERVA_SAIDA),
        ("limiar com nao_medido usa a janela desconhecida", limiar_tokens(p, "seth-rapido") == JANELA_DESCONHECIDA - RESERVA_SAIDA),
        ("fila fora do perfil -> None (gateway não troca)", limiar_tokens(p, "seth-x") is None),
        ("janela do agente = min(teto, piso das longas) − reserva",
         janela_agente(p, 100000) == 100000 - RESERVA_HIDRATACAO and janela_agente(p, 999999) == 128000 - RESERVA_HIDRATACAO),
        ("perfil ausente -> {}", carregar(Path("/nao/existe.json")) == {}),
    ]
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    if argv == ["--janela-agente"]:
        cfg = json.loads((RAIZ / "redesign" / "librechat" / "agente-seth.json").read_text(encoding="utf-8"))
        print(janela_agente(carregar(), int(cfg["teto_economia"])))
        return 0
    if argv == ["--sincronizar-filas"]:
        for linha in sincronizar_filas(carregar()):
            print(linha)
        return 0
    novo = medir()
    if argv == ["--conferir"]:
        velho = carregar()
        mudou = [m for m in sorted(set(novo["modelos"]) | set(velho.get("modelos", {})))
                 if novo["modelos"].get(m, {}).get("janela") != velho.get("modelos", {}).get(m, {}).get("janela")]
        mudou += ["filas"] if novo["filas"] != velho.get("filas") else []
        print("OK: perfil em dia" if not mudou else "MUDOU: " + ", ".join(mudou))
        return 1 if mudou else 0
    if argv:
        print(__doc__)
        return 2
    PERFIS.parent.mkdir(parents=True, exist_ok=True)
    PERFIS.write_text(json.dumps(novo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for m, d in novo["modelos"].items():
        print(f"{m:55} {str(d['janela']):>8}  {d['fonte'][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
