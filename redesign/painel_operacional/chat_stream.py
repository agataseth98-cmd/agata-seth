"""Streaming do chat do painel: traduz SSE do gateway (formato OpenAI) em eventos.

Transporte injetado: este módulo não abre conexão nem chama o gateway.
Não registra texto de usuário em log.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable, Iterator

# O cliente manda só user e assistant. A instrução da conversa (role "system") entra por montar_mensagens, nunca por mensagens.
PAPEIS_VALIDOS = {"user", "assistant"}
MAX_MENSAGENS = 20
MAX_CARACTERES_MENSAGEM = 4000
MAX_INSTRUCOES = 2000          # instruções da conversa (campo `instrucoes`), texto
MAX_ANEXOS = 3                 # anexos de texto por pedido (campo `anexos`)
MAX_ANEXO_NOME = 120
MAX_ANEXO_TEXTO = 20000        # por anexo
MAX_ANEXOS_TOTAL = 40000       # soma dos textos dos anexos de um pedido
SEPARADORES_DE_LINHA = frozenset("\u2028\u2029\u0085")  # proibidos no nome do anexo, além de Cc e Cf
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
                  "e dados pessoais. Consulta o canon, o vault e a Máquina; só anota no cache do Conselho."},
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


def uso_valido(valor) -> dict | None:
    """Contagem de tokens do gateway (campo `usage`, formato OpenAI): {"entrada", "saida"}.
    None se o campo não vier ou se prompt_tokens/completion_tokens não forem inteiros não negativos."""
    if not isinstance(valor, dict):
        return None
    entrada, saida = valor.get("prompt_tokens"), valor.get("completion_tokens")
    if type(entrada) is int and type(saida) is int and entrada >= 0 and saida >= 0:
        return {"entrada": entrada, "saida": saida}
    return None


def eventos_do_stream(linhas: Iterable[str]) -> Iterator[dict]:
    """Lê linhas SSE e emite eventos {"tipo": ...}.

    - {"tipo": "texto", "delta": str} para cada delta não vazio de choices[0].delta.content
    - {"tipo": "uso", "entrada": int, "saida": int} antes do fim, se algum bloco trouxe `usage` válido
      (o último visto vale); sem `usage` no gateway, o evento não existe
    - {"tipo": "fim"} ao ver [DONE], se houve ao menos um delta
    - {"tipo": "chamadas", "chamadas": [{"id", "nome", "argumentos"}]} ao ver [DONE] com tool_calls no stream
      (sem uso nem fim: quem chama executa e reenvia)
    - {"tipo": "erro", "motivo": "resposta vazia"} se [DONE] chegou sem delta
    - {"tipo": "erro", "motivo": "linha de dados inválida"} para JSON inválido (e para)
    - {"tipo": "erro", "motivo": "stream interrompido"} se o stream acabou sem [DONE]

    - {"tipo": "estado", "texto": str} para o comentário ": agata <etapa>" do gateway (progresso da conferência)

    Linhas em branco (separadores de evento) e linhas que não são "data:"
    (outros comentários, "event:") são ignoradas.
    """
    houve_delta = False
    uso = None
    chamadas: dict[int, dict] = {}
    for linha in linhas:
        linha = linha.rstrip("\r\n")
        # (23/11/2026, Regra 0) o gateway manda ": agata conferindo · ..." enquanto confere e refaz a resposta;
        # vira {"tipo": "estado"} para a tela mostrar o progresso real. Outros comentários seguem ignorados.
        if linha.startswith(": agata modelo "):  # 23/11: o modelo servido, quando o cabeçalho X-Modelo-Real não pode sair
            modelo = linha[len(": agata modelo "):].strip()[:120]
            if modelo:
                yield {"tipo": "modelo", "modelo": modelo}
            continue
        if linha.startswith(": agata "):
            texto = linha[len(": agata "):].strip()[:120]
            if texto:
                yield {"tipo": "estado", "texto": texto}
            continue
        if not linha.startswith(PREFIXO_DADOS):
            continue
        dados = linha[len(PREFIXO_DADOS):].lstrip(" ")
        if dados == SENTINELA_FIM:
            if chamadas:
                yield {"tipo": "chamadas", "chamadas": [
                    {"id": c["id"], "nome": c["nome"], "argumentos": c["argumentos"]} for _, c in sorted(chamadas.items())]}
            elif houve_delta:
                if uso is not None:
                    yield {"tipo": "uso", **uso}
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
        uso_do_bloco = uso_valido(obj.get("usage"))
        if uso_do_bloco is not None:
            uso = uso_do_bloco
        escolhas = obj.get("choices")
        if not isinstance(escolhas, list) or not escolhas or not isinstance(escolhas[0], dict):
            continue
        delta = escolhas[0].get("delta")
        conteudo = delta.get("content") if isinstance(delta, dict) else None
        for parte in (delta.get("tool_calls") if isinstance(delta, dict) else None) or []:
            if not isinstance(parte, dict):
                continue
            indice = parte.get("index") if type(parte.get("index")) is int else len(chamadas)
            atual = chamadas.setdefault(indice, {"id": None, "nome": "", "argumentos": ""})
            funcao = parte.get("function") if isinstance(parte.get("function"), dict) else {}
            if isinstance(parte.get("id"), str):
                atual["id"] = parte["id"]
            if isinstance(funcao.get("name"), str):
                atual["nome"] += funcao["name"]
            if isinstance(funcao.get("arguments"), str):
                atual["argumentos"] += funcao["arguments"]
        if isinstance(conteudo, str) and conteudo:
            houve_delta = True
            yield {"tipo": "texto", "delta": conteudo}
    yield {"tipo": "erro", "motivo": "stream interrompido"}


def codificar_sse(evento: dict) -> bytes:
    """Serializa um evento como bloco SSE: 'data: <json>' seguido de linha em branco."""
    return ("data: " + json.dumps(evento, ensure_ascii=False) + "\n\n").encode("utf-8")


def texto_instrucoes(valor) -> str | None:
    """Instruções da conversa: texto de até MAX_INSTRUCOES caracteres, sem espaço nas pontas.
    Ausente, vazio ou só espaço vira None (sem instruções). Tipo errado ou acima do limite é ValueError com motivo."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError("instruções devem ser texto")
    limpo = valor.strip()
    if len(limpo) > MAX_INSTRUCOES:
        raise ValueError(f"instruções acima de {MAX_INSTRUCOES} caracteres")
    return limpo or None


def anexo_nome_valido(valor) -> str | None:
    """Nome de anexo: de 1 a MAX_ANEXO_NOME caracteres, sem barra, sem '..'. Recusa, em qualquer posição, caractere
    de controle ou de formato (Unicode Cc e Cf) e os separadores de linha U+2028, U+2029 e U+0085.
    Devolve o nome sem espaço nas pontas; qualquer outra coisa vira None."""
    if not isinstance(valor, str):
        return None
    if any(c in SEPARADORES_DE_LINHA or unicodedata.category(c) in ("Cc", "Cf") for c in valor):
        return None
    nome = valor.strip()
    if not 0 < len(nome) <= MAX_ANEXO_NOME or "/" in nome or "\\" in nome or ".." in nome:
        return None
    return nome


def validar_anexos(valor) -> list[dict]:
    """Anexos do pedido: lista de até MAX_ANEXOS itens {nome, texto}. Ausente vale lista vazia.
    Recusa com ValueError e motivo em português; a mensagem não ecoa o nome nem o texto do anexo."""
    if valor is None:
        return []
    if not isinstance(valor, list):
        raise ValueError("anexos devem ser uma lista")
    if len(valor) > MAX_ANEXOS:
        raise ValueError(f"até {MAX_ANEXOS} anexos por mensagem")
    limpos, total = [], 0
    for indice, item in enumerate(valor, 1):
        if not isinstance(item, dict):
            raise ValueError(f"anexo {indice} fora do formato")
        nome = anexo_nome_valido(item.get("nome"))
        if nome is None:
            raise ValueError(f"anexo {indice} com nome inválido (de 1 a {MAX_ANEXO_NOME} caracteres, sem barra nem '..')")
        texto = item.get("texto")
        if not isinstance(texto, str) or not texto:
            raise ValueError(f"anexo {indice} sem texto")
        if len(texto) > MAX_ANEXO_TEXTO:
            raise ValueError(f"anexo {indice} acima de {MAX_ANEXO_TEXTO} caracteres")
        total += len(texto)
        limpos.append({"nome": nome, "texto": texto})
    if total > MAX_ANEXOS_TOTAL:
        raise ValueError(f"anexos somam mais de {MAX_ANEXOS_TOTAL} caracteres")
    return limpos


def _filtro_padrao(texto: str) -> str:
    """Filtro de saída do que este módulo põe no pedido: as instruções da conversa e os anexos (nome e texto).
    É o mesmo da gravação do Conselho (cache_conselho.filtrar). Segredo recusa com ValueError; dado pessoal vira marca.
    As mensagens digitadas não passam por aqui (montar_mensagens não as filtra); a proteção de saída delas é o proxy
    sanitizador, que o pedido atravessa antes do OmniRoute."""
    router = str(Path(__file__).resolve().parents[1] / "router")
    if router not in sys.path:
        sys.path.insert(0, router)
    import cache_conselho
    return cache_conselho.filtrar(texto)


def _cerca(texto: str) -> str:
    """Cerca de bloco de código: mais crases que qualquer sequência dentro do texto, e nunca menos de três."""
    maior = max((len(trecho) for trecho in re.findall(r"`+", texto)), default=0)
    return "`" * max(3, maior + 1)


def bloco_anexos(anexos: list[dict], filtro=None) -> str:
    """Um bloco por anexo: 'Arquivo anexado: <nome>' e o texto em bloco de código. Nome e texto passam pelo filtro.
    Segredo em qualquer um vira ValueError sem o conteúdo."""
    filtrar = filtro or _filtro_padrao
    blocos = []
    for indice, anexo in enumerate(anexos, 1):
        try:
            nome = filtrar(anexo["nome"])
            texto = filtrar(anexo["texto"])
        except ValueError:
            raise ValueError(f"anexo {indice} com segredo (régua do P-1): não foi enviado") from None
        cerca = _cerca(texto)
        blocos.append(f"Arquivo anexado: {nome}\n{cerca}\n{texto}\n{cerca}")
    return "\n\n".join(blocos)


def montar_mensagens(limpas: list[dict], instrucoes=None, anexos=None, filtro=None) -> list[dict]:
    """Mensagens que vão ao gateway. `limpas` já passou pela checagem de papel e de tamanho (user/assistant, até
    MAX_CARACTERES_MENSAGEM no texto digitado). Instruções da conversa viram UMA mensagem role "system" na frente,
    filtradas. Anexos entram no fim da ÚLTIMA mensagem do usuário, depois do texto digitado (o limite de 4000 não os conta).
    `filtro` é a função texto -> texto de saída; ausente, vale _filtro_padrao."""
    texto_instr = texto_instrucoes(instrucoes)
    lista_anexos = validar_anexos(anexos)
    saida = list(limpas)
    if lista_anexos:
        indice = max((i for i, m in enumerate(saida) if m["role"] == "user"), default=None)
        if indice is None:
            raise ValueError("anexo sem mensagem do usuário para receber o texto")
        bloco = bloco_anexos(lista_anexos, filtro)
        saida[indice] = {**saida[indice], "content": saida[indice]["content"] + "\n\n" + bloco}
    if texto_instr is not None:
        try:
            texto_instr = (filtro or _filtro_padrao)(texto_instr)
        except ValueError:
            raise ValueError("instruções com segredo (régua do P-1): não foram enviadas") from None
        saida.insert(0, {"role": "system", "content": texto_instr})
    return saida


def montar_pedido(mensagens: list[dict], modelo: str | None = None, instrucoes=None, anexos=None,
                  filtro=None, ferramentas=None) -> dict:
    """Monta o corpo do pedido de chat em streaming. Recusa entrada inválida com ValueError.

    `modelo` ausente vale MODELO_PADRAO; fora de MODELOS_PERMITIDOS é recusado.
    `instrucoes` e `anexos` seguem montar_mensagens (filtro de saída aplicado a ambos).
    `ferramentas` (lista de esquemas OpenAI) só entra no pedido do seth-livre; na Seth pública é ignorada (20/11/2026).
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
    # C11 (16/11/2026): o gateway informa o uso (entrada e saída) no fim do stream, para a linha de contexto.
    pedido = {"model": modelo, "messages": montar_mensagens(limpas, instrucoes, anexos, filtro), "stream": True,
              "stream_options": {"include_usage": True}}
    if ferramentas and modelo == "seth-livre":
        pedido["tools"] = list(ferramentas)
    return pedido
