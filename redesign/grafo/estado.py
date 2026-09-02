#!/usr/bin/env python3
"""
Estado tipado do loop de governanca da Fase 4 (P4-01).

Os campos `eventos` e `decisao_log` usam o reducer `operator.add` -- append-only, cada no
soma sem sobrescrever (o event-stream e o log de decisao do DURABILIDADE.md).
"""
from operator import add
from typing import Annotated, Any, TypedDict


class Estado(TypedDict, total=False):
    # --- entrada
    thread_id: str            # id do pedido; chave do checkpoint (SqliteSaver) e do WAL
    entrada: str              # o pedido em si
    tipo: str                 # "conselho" | "trabalho" | "verificacao"  (guia o rotear)
    com_envelope: bool        # se True, trabalhar usa GBNF-envelope (P4-03)
    repo: str                 # caminho do repo alvo (~/agata em producao; um clone no teste)

    # --- hidratar
    hidratacao: dict[str, Any]   # {hash_estado, head, topo_memorias, sync, ...} do estado_para_eco.sh

    # --- rotear
    rota: str                    # combo do OmniRoute: "cheap" | "auto" | "conselho"

    # --- trabalhar
    trabalho: str                # resposta CRUA do modelo (ou "(sem modelo)" se desligado)
    trabalho_erro: str           # vazio, ou o erro se a chamada falhou

    # --- verificar  (espinha deterministica -- roda com o modelo desligado)
    verificacao: dict[str, Any]  # {perimetro_exit, cabecalho_ok, cabecalho_falhas, citacoes_suspeitas}

    # --- portao  (interrupt)
    diff_proposto: str           # o que registrar_e_commitar escreveria/commitaria
    portao: dict[str, Any]       # {reversivel, alcance, silencio, aprovado}

    # --- registrar_e_commitar
    commit_sha: str              # sha do commit feito no repo alvo (vazio se nao aprovado)
    ultimo_efeito_confirmado: str

    # --- transversal (append-only)
    eventos: Annotated[list, add]
    decisao_log: Annotated[list, add]


def estado_inicial(entrada: str, thread_id: str, repo: str, tipo: str = "trabalho",
                   com_envelope: bool = False) -> Estado:
    return {
        "thread_id": thread_id, "entrada": entrada, "tipo": tipo, "repo": repo,
        "com_envelope": com_envelope,
        "hidratacao": {}, "rota": "", "trabalho": "", "trabalho_erro": "",
        "verificacao": {}, "diff_proposto": "", "portao": {},
        "commit_sha": "", "ultimo_efeito_confirmado": "",
        "eventos": [], "decisao_log": [],
    }
