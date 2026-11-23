#!/usr/bin/env python3
"""Capivara — perfis de capacidade dos modelos das filas da Seth (MEMÓRIAS (667)).

`config/capivara/perfis-modelos.json` é DERIVADO de `config/capivara/capacidades.json` (fonte única,
capivara_capacidades.py). O gateway da Seth lê este arquivo (`seth_gateway._perfis()`), então ele
continua existindo, no mesmo formato. Este script não mede nada: quem mede é
capivara_capacidades.py. Lê fatos, nunca escreve canon.

Fonte da janela e da saída máxima: a mesma precedência do registro (ollama num_ctx; /v1/models do
OmniRoute; documentação oficial; lista pública do provedor). Sem fonte = `nao_medido`, tratado como
PEQUENO — nunca como grande.

Para que serve:
- **Fila longa.** Cada fila da conversa ganha uma variante `<fila>-longo`, mesma ordem,
  só com modelos de janela >= JANELA_LONGA. O `seth_gateway` usa a variante quando o
  pedido não cabe no menor modelo da fila base (o local de 64k, um `nao_medido`).
- **Janela do LibreChat.** `janela_agente()` = min(teto de economia, menor janela das
  filas longas) − reserva da hidratação: o número que o mostrador do LibreChat exibe é a
  capacidade garantida do sistema, calculada, não chutada.

Uso:
  capivara_perfis.py                      deriva o perfil de capacidades.json e grava
  capivara_perfis.py --conferir           diz se o perfil gravado está em dia com o registro (saída 1 se não)
  capivara_perfis.py --sincronizar-filas  cria/atualiza as filas -longo no OmniRoute
  capivara_perfis.py --janela-agente      imprime a janela calculada para o Agent
  capivara_perfis.py --selftest
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PERFIS = RAIZ / "config" / "capivara" / "perfis-modelos.json"
FILAS_CONVERSA = ("seth-rapido", "seth-livre", "seth-pesado")
SUFIXO_LONGO = "-longo"
JANELA_LONGA = 128000        # modelo entra na fila -longo se aguentar isto
RESERVA_SAIDA = 8000         # tokens deixados para a resposta
RESERVA_HIDRATACAO = 4000    # o gateway injeta ~3 mil tokens que o LibreChat não conta
JANELA_DESCONHECIDA = 32768  # `nao_medido` vale isto para o limiar: pequeno, de propósito
COMO_USAR = ("Gerado por scripts/capivara_perfis.py a partir de config/capivara/capacidades.json "
             "(fonte única) — não editar à mão; rode capivara_capacidades.py e depois capivara_perfis.py. "
             "MEMÓRIAS (667).")


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


def conferir_perfil(perfil: dict, reg: dict) -> list[str]:
    """Diferenças entre o perfil dado e o que o registro deriva. Lista vazia = em dia."""
    esperado = derivar(reg)
    mods = perfil.get("modelos") or {}
    erros = ["filas"] if perfil.get("filas") != esperado["filas"] else []
    erros += [m for m in sorted(set(esperado["modelos"]) | set(mods)) if mods.get(m) != esperado["modelos"].get(m)]
    return erros


def caminho_perfil(retrato: Path | None = None, estado: Path | None = None) -> Path:
    """Perfil em uso: o do estado se existir e estiver em dia com o registro em uso (conferir_perfil); senão o
    retrato do repositório. O gateway passa o caminho do retrato de forma explícita: não muda com isto."""
    aqui = str(Path(__file__).resolve().parent)
    if aqui not in sys.path:
        sys.path.insert(0, aqui)
    import capivara_capacidades as cap  # noqa: E402  (fonte única; import tardio: o gateway só usa as funções puras)
    retrato = PERFIS if retrato is None else retrato
    estado = cap.ESTADO_PERFIL if estado is None else estado
    try:
        perfil = json.loads(estado.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return retrato
    reg = cap.carregar()
    if isinstance(perfil, dict) and reg.get("modelos") and not conferir_perfil(perfil, reg):
        return estado
    return retrato


def carregar(caminho: Path | None = None) -> dict:
    try:
        return json.loads((caminho or caminho_perfil()).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# --- derivação (puro): registro de capacidades -> perfil que o gateway lê ----------------
def derivar(reg: dict) -> dict:
    """Projeção do registro: só as filas, com janela, saída máxima e a fonte da janela.
    Modelo de fila sem dado vira `nao_medido` (janela None), nunca um número."""
    filas = reg.get("filas") or {}
    registro = reg.get("modelos") or {}
    modelos = {}
    for m in sorted({x for ordem in filas.values() for x in ordem}):
        v = registro.get(m) if isinstance(registro.get(m), dict) else {}
        modelos[m] = {"janela": v.get("janela"), "saida_max": v.get("saida_max"),
                      "fonte": v.get("fonte") or "nao_medido"}
    return {"_como_usar": COMO_USAR, "medido_em": str(reg.get("gerado_em") or "")[:10],
            "filas": filas, "modelos": modelos}


# --- sincronização das filas -longo no OmniRoute (rede, escreve no OmniRoute) ----------
def _q():
    sys.path.insert(0, str(RAIZ / "scripts"))
    import queda_por_elo as q  # noqa: E402  (filas, token interno, abridor sem proxy)
    return q


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
    if argv and argv != ["--conferir"]:
        print(__doc__)
        return 2
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import capivara_capacidades as cap  # noqa: E402  (fonte única)
    reg = cap.carregar()
    if not reg.get("modelos"):
        print("registro de capacidades ausente: rode capivara_capacidades.py antes")
        return 1
    novo = derivar(reg)
    if argv == ["--conferir"]:
        diferencas = conferir_perfil(carregar(), reg)
        print("OK: perfil em dia com o registro em uso" if not diferencas
              else "DESATUALIZADO: " + ", ".join(diferencas))
        return 1 if diferencas else 0
    cap.gravar(novo, PERFIS)              # retrato versionado
    cap.gravar(novo, cap.ESTADO_PERFIL)   # estado operacional, o mesmo conteúdo
    for m, d in novo["modelos"].items():
        print(f"{m:55} {str(d['janela']):>8}  {str(d['fonte'])[:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
