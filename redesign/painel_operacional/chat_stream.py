"""Streaming do chat do painel: traduz SSE do gateway (formato OpenAI) em eventos.

Transporte injetado: este módulo não abre conexão nem chama o gateway.
Não registra texto de usuário em log.
"""

import json
from typing import Iterable, Iterator

PAPEIS_VALIDOS = {"system", "user", "assistant"}
MAX_MENSAGENS = 20
MAX_CARACTERES_MENSAGEM = 4000
PREFIXO_DADOS = "data:"
SENTINELA_FIM = "[DONE]"


def eventos_do_stream(linhas: Iterable[str]) -> Iterator[dict]:
    """Lê linhas SSE e emite eventos {"tipo": ...}.

    - {"tipo": "texto", "delta": str} para cada delta não vazio de choices[0].delta.content
    - {"tipo": "fim"} ao ver [DONE], se houve ao menos um delta
    - {"tipo": "erro", "motivo": "resposta vazia"} se [DONE] chegou sem delta
    - {"tipo": "erro", "motivo": "linha de dados inválida"} para JSON inválido (e para)
    - {"tipo": "erro", "motivo": "stream interrompido"} se o stream acabou sem [DONE]

    Linhas em branco (separadores de evento) e linhas que não são "data:"
    (comentários, "event:") são ignoradas.
    """
    houve_delta = False
    for linha in linhas:
        linha = linha.rstrip("\r\n")
        if not linha.startswith(PREFIXO_DADOS):
            continue
        dados = linha[len(PREFIXO_DADOS):].lstrip(" ")
        if dados == SENTINELA_FIM:
            if houve_delta:
                yield {"tipo": "fim"}
            else:
                yield {"tipo": "erro", "motivo": "resposta vazia"}
            return
        try:
            obj = json.loads(dados)
        except json.JSONDecodeError:
            yield {"tipo": "erro", "motivo": "linha de dados inválida"}
            return
        if not isinstance(obj, dict):
            yield {"tipo": "erro", "motivo": "linha de dados inválida"}
            return
        escolhas = obj.get("choices")
        if not isinstance(escolhas, list) or not escolhas or not isinstance(escolhas[0], dict):
            continue
        delta = escolhas[0].get("delta")
        conteudo = delta.get("content") if isinstance(delta, dict) else None
        if isinstance(conteudo, str) and conteudo:
            houve_delta = True
            yield {"tipo": "texto", "delta": conteudo}
    yield {"tipo": "erro", "motivo": "stream interrompido"}


def codificar_sse(evento: dict) -> bytes:
    """Serializa um evento como bloco SSE: 'data: <json>' seguido de linha em branco."""
    return ("data: " + json.dumps(evento, ensure_ascii=False) + "\n\n").encode("utf-8")


def montar_pedido(mensagens: list[dict], modelo: str = "seth-livre") -> dict:
    """Monta o corpo do pedido de chat em streaming. Recusa entrada inválida com ValueError.

    As mensagens da exceção não ecoam o conteúdo do usuário.
    """
    if not isinstance(mensagens, list) or not mensagens:
        raise ValueError("lista de mensagens vazia ou inválida")
    if len(mensagens) > MAX_MENSAGENS:
        raise ValueError(f"mais de {MAX_MENSAGENS} mensagens")
    limpas = []
    for indice, msg in enumerate(mensagens):
        if not isinstance(msg, dict):
            raise ValueError(f"mensagem {indice} não é objeto")
        papel = msg.get("role")
        if papel not in PAPEIS_VALIDOS:
            raise ValueError(f"mensagem {indice} com papel inválido")
        conteudo = msg.get("content")
        if not isinstance(conteudo, str):
            raise ValueError(f"mensagem {indice} sem conteúdo texto")
        if len(conteudo) > MAX_CARACTERES_MENSAGEM:
            raise ValueError(f"mensagem {indice} acima de {MAX_CARACTERES_MENSAGEM} caracteres")
        limpas.append({"role": papel, "content": conteudo})
    return {"model": modelo, "messages": limpas, "stream": True}
