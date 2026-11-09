"""Streaming do chat do painel: traduz SSE do gateway (formato OpenAI) em eventos.

Transporte injetado: este módulo não abre conexão nem chama o gateway.
Não registra texto de usuário em log.
"""

import json
import re
from typing import Iterable, Iterator

PAPEIS_VALIDOS = {"system", "user", "assistant"}
MAX_MENSAGENS = 20
MAX_CARACTERES_MENSAGEM = 4000
PREFIXO_DADOS = "data:"
SENTINELA_FIM = "[DONE]"

# Modelos do chat (seletor da tela de conversa). Lista FIXA: o servidor só aceita estes nomes.
# Conferidos em redesign/router/seth_gateway.py, _politica_dados_externos (09/11/2026): o gateway aceita
# seth-livre (cascata com sanitização) e seth-public (alias da via pública, sem ferramentas e sem contexto
# do Agata). Ficam fora seth-zai, seth-gemini, seth-hf, seth-mistral e seth-auto: a política recusa com 403
# quem não é seth-livre, seth-public ou modelo local, quando não há classificação pública.
MODELO_PADRAO = "seth-livre"
MODELOS_CHAT = (
    {"id": "seth-livre", "rotulo": "Seth (padrão)",
     "descricao": "Usa o contexto do Agata. Antes de sair, a mensagem passa por filtro de segredos "
                  "e dados pessoais. Nesta tela não há ferramentas."},
    {"id": "seth-public", "rotulo": "Seth pública",
     "descricao": "Só o texto da conversa vai para modelos externos. Sem contexto do Agata e sem ferramentas."},
)
MODELOS_PERMITIDOS = frozenset(m["id"] for m in MODELOS_CHAT)


def modelo_permitido(valor) -> bool:
    """True só para um nome exato da lista fixa. Qualquer outro tipo (número, lista, None) é recusado."""
    return isinstance(valor, str) and valor in MODELOS_PERMITIDOS


# Modelo que de fato respondeu: vem do cabeçalho X-Modelo-Real do gateway (fato da Máquina, nome como "openai/gpt-oss-120b").
# Não é a lista fixa acima (é o nome real, que muda); só passa texto curto, sem espaço nem controle.
_MODELO_REAL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/+-]{0,119}")


def modelo_real_valido(valor) -> str | None:
    """Nome do modelo real se for texto curto e limpo; qualquer outra coisa (None, vazio, com espaço) vira None."""
    if isinstance(valor, str) and _MODELO_REAL_RE.fullmatch(valor):
        return valor
    return None


def modelo_valido(valor) -> str:
    """Modelo do pedido: ausente (None) vale o padrão; fora da lista é ValueError."""
    if valor is None:
        return MODELO_PADRAO
    if not modelo_permitido(valor):
        raise ValueError("modelo fora da lista")
    return valor


def lista_modelos() -> dict:
    """Corpo de GET /api/seth/modelos: a lista fixa, com o padrão marcado."""
    return {"schema_version": 1, "padrao": MODELO_PADRAO, "modelos": [dict(m) for m in MODELOS_CHAT]}


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


def montar_pedido(mensagens: list[dict], modelo: str | None = None) -> dict:
    """Monta o corpo do pedido de chat em streaming. Recusa entrada inválida com ValueError.

    `modelo` ausente vale MODELO_PADRAO; fora de MODELOS_PERMITIDOS é recusado.
    As mensagens da exceção não ecoam o conteúdo do usuário.
    """
    modelo = modelo_valido(modelo)
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
