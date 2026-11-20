"""Ferramentas da Seth no painel (decisão do Humano, 20/11/2026): só LEITURA, só no modelo seth-livre, mais uma
escrita: anotar no cache do Conselho (autor fixo "Seth (painel)").

- As quatro de leitura vêm do MCP do canon (redesign/librechat/canon-mcp.mjs, stdio JSON-RPC): um processo node por
  chamada, com timeout. Nada é reimplementado aqui. `memoria_acrescentar` nunca é oferecida nem executada.
- `cache_anotar` chama cache_conselho.anotar (recusa segredo, marca dado pessoal).
- Web (buscar_web, ler_pagina): NÃO implementada. O navegador-mcp (127.0.0.1:20136/mcp) é FastMCP HTTP com sessão e
  estado de página (navegar, depois ler_pagina); não há chamada simples de uma ferramenta só.
- O laço (`laco`) reenvia ao gateway com os resultados, no máximo MAX_RODADAS rodadas. Transporte injetado.
Não registra texto de usuário em log.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

from chat_stream import eventos_do_stream

MODELO_COM_FERRAMENTAS = "seth-livre"
NOMES_MCP = ("maquina_verificar", "vault_buscar", "query_canon", "vault_consultar")  # lista fixa; sem memoria_acrescentar
NOME_ANOTAR = "cache_anotar"
NOMES_PERMITIDOS = frozenset(NOMES_MCP) | {NOME_ANOTAR}
AUTOR_CACHE = "Seth (painel)"
TIPOS_CACHE = ("fato", "decisao", "pendencia", "nota")
MAX_TEXTO_CACHE = 4000
MAX_RODADAS = 5
MAX_RESULTADO = 12000
TIMEOUT_FERRAMENTA_S = 60
MCP_CANON = Path(__file__).resolve().parents[1] / "librechat" / "canon-mcp.mjs"
AVISO_LIMITE = "\n\n[Limite de {n} rodadas de ferramentas atingido; sigo sem mais consultas.]"

ESQUEMA_ANOTAR = {
    "type": "function",
    "function": {
        "name": NOME_ANOTAR,
        "description": ("Anota no cache do Conselho (memória comum, não canônica, só acrescenta). Use para registrar um "
                        "fato, decisão, pendência ou nota que outros modelos devam ler. Segredo é recusado."),
        "parameters": {"type": "object", "additionalProperties": False, "required": ["tipo", "texto"],
                       "properties": {"tipo": {"type": "string", "enum": list(TIPOS_CACHE)},
                                      "texto": {"type": "string", "maxLength": MAX_TEXTO_CACHE}}},
    },
}


class ErroMCP(Exception):
    pass


def truncar(texto, limite: int = MAX_RESULTADO) -> str:
    texto = texto if isinstance(texto, str) else json.dumps(texto, ensure_ascii=False)
    if len(texto) <= limite:
        return texto
    return texto[:limite] + f"\n[... truncado: {len(texto) - limite} caracteres a mais]"


def _rpc_mcp(chamadas: list[dict], timeout: float = TIMEOUT_FERRAMENTA_S) -> dict:
    """Roda o MCP do canon (node) com initialize + as chamadas; devolve {id: resposta}. Timeout ou falha viram ErroMCP."""
    linhas = [{"jsonrpc": "2.0", "id": 0, "method": "initialize",
               "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "painel", "version": "1"}}},
              {"jsonrpc": "2.0", "method": "notifications/initialized"}] + chamadas
    entrada = "".join(json.dumps(l, ensure_ascii=False) + "\n" for l in linhas)
    try:
        proc = subprocess.run(["node", str(MCP_CANON)], input=entrada, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ErroMCP("tempo esgotado") from None
    except OSError as erro:
        raise ErroMCP(f"MCP do canon indisponível ({type(erro).__name__})") from None
    respostas = {}
    for linha in proc.stdout.splitlines():
        try:
            obj = json.loads(linha)
        except ValueError:
            continue
        if isinstance(obj, dict) and "id" in obj:
            respostas[obj["id"]] = obj
    return respostas


_cache_esquemas = {"quando": 0.0, "lista": None}


def esquemas(agora=None, ttl: float = 300.0) -> list[dict]:
    """Ferramentas no formato OpenAI: as quatro de leitura do MCP (filtradas pela lista fixa) e cache_anotar.
    Se o MCP não responde, oferece só cache_anotar (nada quebra)."""
    t = time.monotonic() if agora is None else agora
    if _cache_esquemas["lista"] is not None and t - _cache_esquemas["quando"] < ttl:
        return list(_cache_esquemas["lista"])
    lista = []
    try:
        resp = _rpc_mcp([{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}], timeout=20)
        for ferr in ((resp.get(1) or {}).get("result") or {}).get("tools") or []:
            if isinstance(ferr, dict) and ferr.get("name") in NOMES_MCP:
                lista.append({"type": "function", "function": {
                    "name": ferr["name"], "description": ferr.get("description") or "",
                    "parameters": ferr.get("inputSchema") or {"type": "object", "properties": {}}}})
    except ErroMCP:
        lista = []
    lista.sort(key=lambda f: NOMES_MCP.index(f["function"]["name"]))
    lista.append(ESQUEMA_ANOTAR)
    if len(lista) > 1:  # só guarda lista completa; falha do MCP tenta de novo no próximo pedido
        _cache_esquemas.update(quando=t, lista=lista)
    return list(lista)


def _cache_modulo():
    router = str(Path(__file__).resolve().parents[1] / "router")
    if router not in sys.path:
        sys.path.insert(0, router)
    import cache_conselho
    return cache_conselho


def cache_anotar(args: dict) -> str:
    """Grava no cache do Conselho com autor fixo. Devolve o recibo (JSON) ou o motivo da recusa, como texto."""
    if not isinstance(args, dict):
        return "erro: argumentos devem ser um objeto"
    tipo, texto = args.get("tipo"), args.get("texto")
    if tipo not in TIPOS_CACHE:
        return f"erro: tipo deve ser um de {', '.join(TIPOS_CACHE)}"
    if not isinstance(texto, str) or not texto.strip() or len(texto) > MAX_TEXTO_CACHE:
        return f"erro: texto obrigatório, até {MAX_TEXTO_CACHE} caracteres"
    try:
        recibo = _cache_modulo().anotar(AUTOR_CACHE, texto, tipo)
    except (ValueError, OSError) as erro:
        return f"erro: cache recusou ({erro})"
    return json.dumps(recibo, ensure_ascii=False)


def _texto_mcp(resp: dict) -> str:
    if "error" in resp:
        return "erro: " + str((resp["error"] or {}).get("message", "falha do MCP"))
    partes = [c.get("text", "") for c in (resp.get("result") or {}).get("content") or [] if isinstance(c, dict)]
    return "\n".join(partes) if partes else "(sem conteúdo)"


def executar(nome, argumentos) -> str:
    """Executa UMA chamada. Nome fora da lista não executa. Erro vira texto para o modelo; o resultado é truncado."""
    if nome not in NOMES_PERMITIDOS:
        return f"erro: ferramenta {nome!r} não permitida"
    try:
        args = json.loads(argumentos) if isinstance(argumentos, str) and argumentos.strip() else (argumentos or {})
    except ValueError:
        return "erro: argumentos não são JSON válido"
    if not isinstance(args, dict):
        return "erro: argumentos devem ser um objeto"
    try:
        if nome == NOME_ANOTAR:
            return truncar(cache_anotar(args))
        resp = _rpc_mcp([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": nome, "arguments": args}}])
        return truncar(_texto_mcp(resp.get(1) or {"error": {"message": "sem resposta do MCP"}}))
    except ErroMCP as erro:
        return f"erro: {erro}"
    except Exception as erro:  # a ferramenta nunca derruba a conversa
        return f"erro: {type(erro).__name__}"


def _id_chamada(c: dict, i: int) -> str:
    return str(c.get("id") or f"call_{i}")


def laco(abrir_proxima, primeira_linhas, pedido: dict, executor=None, max_rodadas: int = MAX_RODADAS):
    """Gera eventos SSE do painel. `primeira_linhas` são as linhas da 1ª resposta (já aberta). `abrir_proxima(pedido)`
    devolve as linhas da resposta seguinte (ou levanta OSError). Eventos de texto passam na hora; chamadas de
    ferramenta emitem {"tipo":"estado"} e voltam ao gateway com a resposta; uso e fim saem só da resposta final."""
    executor = executor or executar
    pedido = dict(pedido, messages=list(pedido["messages"]))
    linhas, rodada = primeira_linhas, 0
    while True:
        chamadas = None
        for ev in eventos_do_stream(linhas):
            if ev["tipo"] == "chamadas":
                chamadas = ev["chamadas"]
            else:
                yield ev
        if chamadas is None:
            return
        if rodada >= max_rodadas:
            yield {"tipo": "texto", "delta": AVISO_LIMITE.format(n=max_rodadas)}
            yield {"tipo": "fim"}
            return
        rodada += 1
        pedido["messages"].append({"role": "assistant", "content": "", "tool_calls": [
            {"id": _id_chamada(c, i), "type": "function",
             "function": {"name": c["nome"], "arguments": c["argumentos"]}} for i, c in enumerate(chamadas)]})
        for i, c in enumerate(chamadas):
            nome = c["nome"]
            yield {"tipo": "estado", "texto": f"consultando {nome}…" if nome in NOMES_PERMITIDOS else "ferramenta não permitida"}
            pedido["messages"].append({"role": "tool", "tool_call_id": _id_chamada(c, i),
                                       "content": truncar(executor(nome, c["argumentos"]))})
        try:
            linhas = abrir_proxima(pedido)
        except OSError:
            yield {"tipo": "erro", "motivo": "gateway indisponível"}
            return
