#!/usr/bin/env python3
"""Rotas locais por tipo de pedido (18/11/2026), lidas da ficha assinada config/rotas-ficha.json.

Regra determinística, sem modelo e sem rede além de um teste de porta:
- a ficha assinada manda: só uma rota com categoria `local` e com `tipos` pode ser escolhida, só para o tipo
  em que ganhou na prova de porta de entrada, e só se a classe do pedido estiver em `classes_permitidas`;
- o painel (decisoes.jsonl) SÓ RESTRINGE: modelo cuja última decisão é `standby` sai da escolha. `liberado` não
  acrescenta nada que a ficha não tenha. Arquivo ausente ou ilegível = comportamento da ficha, sem painel;
- Ollama fora do ar (porta fechada) = nenhuma rota local; o gateway segue pela regra de sempre.
- nuvem (19/11/2026, ordem do Humano): rota `gratuito` da ficha com `tipos`, SÓ na faixa pública do gateway (classe
  pública; nunca pessoal nem segredo), pelo mesmo sanitizador, com queda segura para a fila de sempre. O painel só
  restringe. SETH_ROTAS_NUVEM=0 desliga só a nuvem.
Nada aqui chama modelo. Quem usa é o seth_gateway (e o teste).
"""
from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FICHA_PADRAO = RAIZ / "config" / "rotas-ficha.json"
PREFIXO_GATEWAY = "ollama-local/"  # nome do modelo no OmniRoute
TIPOS = ("codigo", "conversa", "ferramenta", "json", "contexto")
# acima disto (tokens estimados do pedido do usuário, caracteres ÷ 3) o pedido é "contexto"
LIMIAR_CONTEXTO_TOKENS = 6000
_CACHE_FICHA: dict = {"mtime": None, "caminho": None, "rotas": []}
_CACHE_NUVEM: dict = {"mtime": None, "caminho": None, "rotas": []}
_CACHE_PAINEL: dict = {"mtime": None, "caminho": None, "estado": {}}
_CACHE_PORTA: dict = {"quando": 0.0, "caminho": None, "ok": False}


def ligado() -> bool:
    """SETH_ROTAS_LOCAIS=0 desliga tudo (volta ao comportamento anterior)."""
    return os.environ.get("SETH_ROTAS_LOCAIS") != "0"


def caminho_painel() -> Path:
    env = os.environ.get("AGATA_DECISOES_MODELOS")
    if env:
        return Path(env)
    return Path.home() / ".local" / "share" / "agata" / "catalogo-modelos" / "decisoes.jsonl"


def nuvem_ligada() -> bool:
    """SETH_ROTAS_NUVEM=0 desliga só as rotas de nuvem por tipo (SETH_ROTAS_LOCAIS=0 desliga as duas)."""
    return ligado() and os.environ.get("SETH_ROTAS_NUVEM") != "0"


def carregar_rotas(caminho: Path | None = None) -> list[dict]:
    """Rotas locais com tipos, da ficha. Ficha ausente ou quebrada = []."""
    caminho = Path(caminho or FICHA_PADRAO)
    try:
        mt = caminho.stat().st_mtime
        if _CACHE_FICHA["mtime"] == mt and _CACHE_FICHA["caminho"] == str(caminho):
            return _CACHE_FICHA["rotas"]
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        rotas = [r for r in dados.get("rotas", [])
                 if isinstance(r, dict) and r.get("categoria") == "local" and r.get("tipos")
                 and isinstance(r.get("modelo"), str) and r.get("provedor") == "ollama"]
    except (OSError, ValueError, AttributeError):
        return []
    _CACHE_FICHA.update(mtime=mt, caminho=str(caminho), rotas=rotas)
    return rotas


def estado_painel(caminho: Path | None = None) -> dict[str, str]:
    """id -> última ação ('liberar' ou 'standby') do painel. Ausente ou ilegível = {} (sem restrição)."""
    caminho = Path(caminho or caminho_painel())
    try:
        mt = caminho.stat().st_mtime
        if _CACHE_PAINEL["mtime"] == mt and _CACHE_PAINEL["caminho"] == str(caminho):
            return _CACHE_PAINEL["estado"]
        estado: dict[str, str] = {}
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(linha)
            except ValueError:
                continue  # linha quebrada não derruba a leitura
            if isinstance(d, dict) and isinstance(d.get("id"), str) and d.get("acao") in ("liberar", "standby"):
                estado[d["id"]] = d["acao"]  # append-only: a última linha do id vale
    except (OSError, ValueError):
        return {}
    _CACHE_PAINEL.update(mtime=mt, caminho=str(caminho), estado=estado)
    return estado


def em_standby(rota: dict, estado: dict[str, str]) -> bool:
    ident = {rota.get("modelo", ""), PREFIXO_GATEWAY + rota.get("modelo", ""), "ollama/" + rota.get("modelo", ""),
             rota.get("id", "")}
    return any(estado.get(i) == "standby" for i in ident if i)


def ollama_no_ar(endereco: tuple[str, int] | None = None, validade: float = 5.0) -> bool:
    """Teste de porta (0,2 s), lembrado por `validade` segundos. Porta fechada = nada escutando (agata.target
    desligado, ou o socket não instalado) = nenhuma rota local.
    Com o Ollama sob demanda (ollama-agata.socket, 18/11/2026) a porta 11434 fica SEMPRE aberta com o sistema
    ligado, mesmo com o backend parado: o teste não distingue "frio" de "quente". A 1ª chamada a frio espera o
    backend subir e o modelo carregar dentro do prazo da rota local (seth_gateway, SETH_ROTA_LOCAL_MS, 100,5 s);
    se estourar ou o backend não subir, o gateway cai na fila de sempre (queda segura), sem erro ao usuário."""
    if endereco is None:
        env = os.environ.get("SETH_OLLAMA_ADDR", "127.0.0.1:11434")
        host, _, porta = env.rpartition(":")
        try:
            endereco = (host or "127.0.0.1", int(porta))
        except ValueError:
            return False
    agora = time.monotonic()
    chave = f"{endereco[0]}:{endereco[1]}"
    if _CACHE_PORTA["caminho"] == chave and agora - _CACHE_PORTA["quando"] < validade:
        return _CACHE_PORTA["ok"]
    try:
        with socket.create_connection(endereco, timeout=0.2):
            ok = True
    except OSError:
        ok = False
    _CACHE_PORTA.update(quando=agora, caminho=chave, ok=ok)
    return ok


def _texto(c) -> str:
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(p.get("text", "") for p in c if isinstance(p, dict) and isinstance(p.get("text"), str))
    return ""


def tipo_do_pedido(payload: dict) -> str:
    """codigo | conversa | ferramenta | json | contexto, por regra sobre o pedido atual do usuário."""
    msgs = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    ult = ""
    for m in reversed(msgs):
        if isinstance(m, dict) and m.get("role") == "user":
            ult = _texto(m.get("content"))
            break
    if payload.get("tools"):
        return "ferramenta"
    rf = payload.get("response_format")
    if isinstance(rf, dict) and str(rf.get("type", "")).startswith("json"):
        return "json"
    if len(ult) // 3 > LIMIAR_CONTEXTO_TOKENS:
        return "contexto"
    if "```" in ult:
        return "codigo"
    return "conversa"


def tokens_estimados(payload: dict) -> int:
    """Caracteres ÷ 3 do que vai ao modelo (mensagens e esquema de ferramentas): conservador para português."""
    total = 0
    for m in payload.get("messages") or []:
        if isinstance(m, dict):
            total += len(_texto(m.get("content")))
    if payload.get("tools"):
        try:
            total += len(json.dumps(payload["tools"], ensure_ascii=False))
        except (TypeError, ValueError):
            total += 20000
    return total // 3


def tem_segredo(payload: dict) -> bool:
    """Classe 'segredo': a régua de segredo da Máquina (sanitizar.varrer) acha algo no que vai ao modelo.
    Segredo nunca vai a rota nenhuma, nem local: o pedido segue como hoje. Régua indisponível = trata como segredo."""
    try:
        import sanitizar  # mesmo diretório
        partes = [_texto(m.get("content")) for m in payload.get("messages") or [] if isinstance(m, dict)]
        return bool(sanitizar.varrer("\n".join(partes)))
    except Exception:  # noqa: BLE001 -- falha fechada
        return True


def classe_do_pedido(publico: bool) -> str:
    """Pedido explicitamente público = 'publico'. Qualquer outro = 'pessoal' (o mais restrito que a ficha admite
    em rota local), então só rota que a ficha liberou para dado pessoal pode atendê-lo."""
    return "publico" if publico else "pessoal"


def escolher(payload: dict, tipo: str, publico: bool, ficha: Path | None = None, painel: Path | None = None,
             checar_ollama: bool = True) -> dict | None:
    """Rota local da ficha para este tipo, ou None (= regra de sempre). A ficha decide; o painel só tira."""
    if not ligado() or tipo not in TIPOS:
        return None
    if tem_segredo(payload):
        return None
    estado = estado_painel(painel)
    classe = classe_do_pedido(publico)
    est = tokens_estimados(payload)
    candidatas = []
    for r in carregar_rotas(ficha):
        if tipo not in r["tipos"] or classe not in r.get("classes_permitidas", []):
            continue
        if em_standby(r, estado):
            continue
        limite = r.get("max_tokens_entrada")
        if isinstance(limite, int) and est > limite:
            continue
        candidatas.append(r)
    if not candidatas:
        return None
    if checar_ollama and not ollama_no_ar():
        return None
    return sorted(candidatas, key=lambda r: (r.get("prioridade", 100), r["id"]))[0]


def modelo_no_gateway(rota: dict) -> str:
    return PREFIXO_GATEWAY + rota["modelo"]


def nome_nuvem(rota: dict) -> str:
    """Nome da rota de nuvem no OmniRoute (provedor/modelo, ex.: nvidia/poolside/laguna-xs-2.1) e no painel."""
    return f"{rota['provedor']}/{rota['modelo']}"


def carregar_rotas_nuvem(caminho: Path | None = None) -> list[dict]:
    """Rotas gratuitas com tipos, da ficha, só com classe pública/sintética. Ficha ausente ou quebrada = [].
    Lembrada por mtime (como as rotas locais)."""
    caminho = Path(caminho or FICHA_PADRAO)
    try:
        mt = caminho.stat().st_mtime
        if _CACHE_NUVEM["mtime"] == mt and _CACHE_NUVEM["caminho"] == str(caminho):
            return _CACHE_NUVEM["rotas"]
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        rotas = [r for r in dados.get("rotas", [])
                if isinstance(r, dict) and r.get("categoria") == "gratuito" and r.get("tipos")
                and isinstance(r.get("modelo"), str) and isinstance(r.get("provedor"), str)
                and r.get("classes_permitidas") and set(r["classes_permitidas"]) <= {"publico", "sintetico"}]
    except (OSError, ValueError, AttributeError, TypeError):
        return []
    _CACHE_NUVEM.update(mtime=mt, caminho=str(caminho), rotas=rotas)
    return rotas


def escolher_nuvem(payload: dict, tipo: str, ficha: Path | None = None, painel: Path | None = None) -> dict | None:
    """Rota de nuvem da ficha para este tipo, ou None (= fila de sempre). Só chamar na faixa pública: a classe do
    pedido é 'publico'. A ficha decide; o painel só tira (standby)."""
    if not nuvem_ligada() or tipo not in TIPOS or tem_segredo(payload):
        return None
    estado = estado_painel(painel)
    est = tokens_estimados(payload)
    candidatas = []
    for r in carregar_rotas_nuvem(ficha):
        if tipo not in r["tipos"] or "publico" not in r["classes_permitidas"]:
            continue
        if any(estado.get(i) == "standby" for i in (nome_nuvem(r), r["modelo"], r.get("id", "")) if i):
            continue
        limite = r.get("max_tokens_entrada")
        if not isinstance(limite, int) or est > limite:
            continue
        candidatas.append(r)
    return sorted(candidatas, key=lambda r: (r.get("prioridade", 100), r.get("id", "")))[0] if candidatas else None
