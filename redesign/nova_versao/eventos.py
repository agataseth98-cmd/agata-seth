#!/usr/bin/env python3
"""Eventos da nova versão: camada fina sobre o `redesign/evidence_ledger`.

Não cria um terceiro log. Todo evento da nova versão (Alexandria, metacognição,
corpo, orçamento) vai para UM ledger encadeado por hash, com `flock` (escritor
único), em `<dados>/eventos/ledger.jsonl`. Este módulo só acrescenta:

- chave idempotente: o mesmo `chave` não grava duas vezes;
- transição das sete palavras (Apresentação ... Aprimoramento), com Remoção
  opcional: `estado_anterior`, `estado_seguinte`, `evidencia`, `autorizacao`,
  `retorno`. Registro, não máquina autônoma: nenhuma transição executa efeito.

Pastas: `AGATA_NV_DIR` (padrão ~/.local/share/agata/nova-versao), fora do repo.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "evidence_ledger"))
import ledger  # noqa: E402

SETE = ("apresentacao", "compreensao", "assimilacao", "simbiose", "transicao", "remocao", "aprimoramento")
# destino normal e retornos (tabela da spec Alexandria §11); Remoção é opcional
TRANSICOES = {
    "apresentacao": {"compreensao"},
    "compreensao": {"assimilacao", "apresentacao"},
    "assimilacao": {"simbiose", "compreensao"},
    "simbiose": {"transicao", "assimilacao"},
    "transicao": {"aprimoramento", "remocao", "simbiose"},
    "remocao": {"aprimoramento", "transicao"},
    "aprimoramento": {"apresentacao", "compreensao", "assimilacao", "simbiose", "transicao"},
}


def dados() -> Path:
    return Path(os.environ.get("AGATA_NV_DIR", Path.home() / ".local" / "share" / "agata" / "nova-versao"))


def caminho_ledger() -> Path:
    return dados() / "eventos" / "ledger.jsonl"


def _agora() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def registrar(kind: str, status: str, source: str, *, actor: str = "maquina", componente: str = "nova-versao",
              classification: str = "project", chave: str | None = None, **campos) -> dict:
    """Acrescenta um evento. Com `chave`, é idempotente: devolve o existente."""
    caminho = caminho_ledger()
    if chave is not None:
        for e in ledger.read(caminho):
            if e.get("chave") == chave:
                return {**e, "repetido": True}
    ev = {"id": "nv:" + hashlib.sha256(f"{time.time_ns()}{os.getpid()}{kind}{source}".encode()).hexdigest()[:16],
          "timestamp": _agora(), "actor": actor, "project": "nova-versao", "kind": kind, "status": status,
          "source": source, "classification": classification, "componente": componente, **campos}
    if chave is not None:
        ev["chave"] = chave
    ledger.append(caminho, ev)
    return ev


def transicao(objeto: str, anterior: str | None, seguinte: str, evidencia: str, *, autorizacao: str | None = None,
              retorno: str | None = None, actor: str = "maquina", componente: str = "nova-versao",
              chave: str | None = None) -> dict:
    """Registra a passagem de um objeto pelas sete palavras. Recusa salto fora da tabela."""
    if seguinte not in SETE or (anterior is not None and anterior not in SETE):
        raise ValueError("estado fora das sete palavras")
    if anterior is not None and seguinte not in TRANSICOES[anterior]:
        raise ValueError(f"transição não prevista: {anterior} -> {seguinte}")
    if seguinte == "remocao" and not autorizacao:
        raise ValueError("Remoção exige autorização explícita")
    return registrar("observation", "registrada", objeto, actor=actor, componente=componente, chave=chave,
                     estado_anterior=anterior, estado_seguinte=seguinte, evidencia=evidencia,
                     autorizacao=autorizacao, retorno=retorno)


def caminho_ate(atual: str | None, alvo: str) -> list[str]:
    """Passos previstos na tabela de TRANSICOES para ir de `atual` até `alvo` (BFS). Nunca pula uma palavra."""
    if atual == alvo:
        return []
    from collections import deque
    fila, visto = deque([(atual or "apresentacao", [])]), {atual or "apresentacao"}
    while fila:
        no, passos = fila.popleft()
        for viz in sorted(TRANSICOES.get(no, ())):
            if viz in visto:
                continue
            if viz == alvo:
                return passos + [viz]
            visto.add(viz)
            fila.append((viz, passos + [viz]))
    raise ValueError(f"sem caminho de {atual} para {alvo}")


def ultimo_estado(objeto: str) -> str | None:
    """Último `estado_seguinte` registrado para o objeto, lido do ledger (a fonte de verdade)."""
    ult = None
    caminho = caminho_ledger()
    if not caminho.exists():
        return None
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(linha)
        except ValueError:
            continue
        if ev.get("source") == objeto and ev.get("estado_seguinte"):
            ult = ev["estado_seguinte"]
    return ult


def ultimos(n: int = 20) -> list[dict]:
    return ledger.read(caminho_ledger())[-n:]


def verificar() -> bool:
    caminho = caminho_ledger()
    return True if not caminho.exists() else ledger.verify(caminho)


if __name__ == "__main__":
    if sys.argv[1:] == ["ultimos"]:
        print(json.dumps(ultimos(), ensure_ascii=False, indent=1))
    elif sys.argv[1:] == ["verificar"]:
        print("OK" if verificar() else "FALHA")
    else:
        print(__doc__)
        sys.exit(2)
