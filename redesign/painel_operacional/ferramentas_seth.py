"""Ferramentas da Seth no painel (decisão do Humano, 20/11/2026): só LEITURA, só no modelo seth-livre, mais uma
escrita: anotar no cache do Conselho (autor fixo "Seth (painel)").

- As quatro de leitura vêm do MCP do canon (redesign/librechat/canon-mcp.mjs, stdio JSON-RPC): um processo node por
  chamada, com timeout. Nada é reimplementado aqui. `memoria_acrescentar` nunca é oferecida nem executada.
- `cache_anotar` chama cache_conselho.anotar (recusa segredo, marca dado pessoal).
- Web (buscar_web, ler_pagina): NÃO implementada. O navegador-mcp (127.0.0.1:20136/mcp) é FastMCP HTTP com sessão e
  estado de página (navegar, depois ler_pagina); não há chamada simples de uma ferramenta só.
- O laço (`laco`) reenvia ao gateway com os resultados, no máximo MAX_RODADAS rodadas. Transporte injetado.
- `agata_code` (lote 2, 20/11/2026): a Seth chama o Agata Code (agente do OpenCode, `.opencode/agent/agata-code.md`) numa
  worktree NOVA e descartável a partir de origin/main, fora do ~/agata vivo. Um sentido só: ele não chama a Seth.
  Devolve resposta, `git diff --stat` e caminhos; sem mudança, a worktree é removida. O laço emite estado a cada 10 s.
Não registra texto de usuário em log.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from chat_stream import eventos_do_stream

MODELO_COM_FERRAMENTAS = "seth-livre"
NOMES_MCP = ("maquina_verificar", "vault_buscar", "query_canon", "vault_consultar")  # lista fixa; sem memoria_acrescentar
NOME_ANOTAR = "cache_anotar"
NOME_AGATA_CODE = "agata_code"
NOMES_PERMITIDOS = frozenset(NOMES_MCP) | {NOME_ANOTAR, NOME_AGATA_CODE}
AUTOR_CACHE = "Seth (painel)"
TIPOS_CACHE = ("fato", "decisao", "pendencia", "nota")
MAX_TEXTO_CACHE = 4000
MAX_RODADAS = 5
MAX_RESULTADO = 12000
TIMEOUT_FERRAMENTA_S = 60
MCP_CANON = Path(__file__).resolve().parents[1] / "librechat" / "canon-mcp.mjs"
# Agata Code (lote 2). Tudo que o teste precisa trocar é variável de módulo, lida na hora da chamada.
MAX_TAREFA_CODE = 4000
TIMEOUT_AGATA_CODE_S = 600
PULSO_S = 10                     # intervalo do evento de estado enquanto o Agata Code trabalha (Regra 0)
MAX_RESPOSTA_CODE = 6000
AGENTE_CODE = "agata-code"
AGENTE_CODE_ARQUIVO = Path(".opencode") / "agent" / "agata-code.md"
OPENCODE_BIN = Path.home() / ".opencode" / "bin" / "opencode"
ARQUIVO_CODE = Path.home() / "agata-arquivo" / "agata-code"      # uma pasta por execução: worktree + transcricao.jsonl
REPO_RAIZ = Path(__file__).resolve().parents[2]                    # checkout de onde sai a worktree (só leitura de refs)
ENV_CODE_PERMITIDAS = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TERM", "SHELL")  # nada de segredo herdado
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
    lista.append(ESQUEMA_AGATA_CODE)
    if len(lista) > 2:  # só guarda lista completa; falha do MCP tenta de novo no próximo pedido
        _cache_esquemas.update(quando=t, lista=lista)
    return list(lista)


ESQUEMA_AGATA_CODE = {
    "type": "function",
    "function": {
        "name": NOME_AGATA_CODE,
        "description": ("Chama o Agata Code, o agente de código do Agata (OpenCode), numa cópia descartável do repositório. "
                        "Ele edita arquivos e roda testes, mas nunca commita, publica, aplica nem assina. Devolve a resposta, "
                        "o resumo das mudanças (git diff --stat) e o caminho da cópia. Leva minutos; use para tarefa de código."),
        "parameters": {"type": "object", "additionalProperties": False, "required": ["tarefa"],
                       "properties": {"tarefa": {"type": "string", "maxLength": MAX_TAREFA_CODE}}},
    },
}


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


def _env_code() -> dict:
    return {k: os.environ[k] for k in ENV_CODE_PERMITIDAS if k in os.environ}


def _git(pasta, *args, timeout: float = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(pasta), *args], capture_output=True, text=True, timeout=timeout)


def _texto_final(transcricao: Path) -> str:
    """Texto do agente: junta os eventos {"type":"text"} da transcrição (formato `opencode run --format json`)."""
    partes = []
    try:
        for linha in transcricao.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(linha)
            except ValueError:
                continue
            if isinstance(ev, dict) and ev.get("type") == "text":
                texto = (ev.get("part") or {}).get("text")
                if isinstance(texto, str) and texto.strip():
                    partes.append(texto.strip())
    except OSError:
        pass
    return "\n\n".join(partes)


def _rodar_opencode(cmd: list, pasta: Path, transcricao: Path, timeout_s: float, cancelar) -> str | None:
    """Roda o agente com a saída (eventos json) direto no arquivo. Devolve None se terminou, ou o motivo (tempo/cancelado)."""
    with open(transcricao, "wb") as saida:
        proc = subprocess.Popen(cmd, cwd=str(pasta), env=_env_code(), stdin=subprocess.DEVNULL, stdout=saida,
                                stderr=subprocess.DEVNULL, start_new_session=True)
        fim = time.monotonic() + timeout_s
        motivo = None
        while proc.poll() is None:
            if cancelar is not None and cancelar.is_set():
                motivo = "cancelado (a conversa foi fechada)"
            elif time.monotonic() >= fim:
                motivo = f"tempo esgotado ({int(timeout_s)} s)"
            if motivo:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    proc.kill()
                proc.wait()
                return motivo
            time.sleep(0.2)
    return None


def executar_agata_code(args, timeout_s: float | None = None, cancelar=None) -> dict:
    """Roda o Agata Code numa worktree nova de origin/main, em ARQUIVO_CODE/<data-hora>/. Devolve um dict:
    {ok, resposta, diff_stat, worktree (None se removida), transcricao, erro, tempo_s}. Nunca levanta."""
    t0 = time.monotonic()
    res = {"ok": False, "resposta": "", "diff_stat": "", "worktree": None, "transcricao": None, "erro": None, "tempo_s": 0.0}
    tarefa = args.get("tarefa") if isinstance(args, dict) else None
    if not isinstance(tarefa, str) or not tarefa.strip():
        res["erro"] = f"tarefa obrigatória, texto de até {MAX_TAREFA_CODE} caracteres"
        return res
    if len(tarefa) > MAX_TAREFA_CODE:
        res["erro"] = f"tarefa acima de {MAX_TAREFA_CODE} caracteres"
        return res
    timeout_s = TIMEOUT_AGATA_CODE_S if timeout_s is None else timeout_s
    pasta = Path(ARQUIVO_CODE) / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + os.urandom(3).hex())
    worktree, transcricao = pasta / "worktree", pasta / "transcricao.jsonl"
    try:
        pasta.mkdir(parents=True, exist_ok=False)
        criou = _git(REPO_RAIZ, "worktree", "add", "--detach", str(worktree), "origin/main")
        if criou.returncode != 0:
            res["erro"] = "não consegui criar a worktree de origin/main"
            return res
        origem = Path(REPO_RAIZ) / AGENTE_CODE_ARQUIVO  # a definição do agente é a do checkout servido, mesmo antes do merge
        if origem.is_file():
            (worktree / AGENTE_CODE_ARQUIVO).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origem, worktree / AGENTE_CODE_ARQUIVO)
        res["transcricao"] = str(transcricao)
        cmd = [str(OPENCODE_BIN), "run", "--agent", AGENTE_CODE, "--format", "json", "--dir", str(worktree), "--", tarefa]
        try:
            motivo = _rodar_opencode(cmd, worktree, transcricao, timeout_s, cancelar)
        except OSError:
            motivo = "não consegui iniciar o opencode"
        res["resposta"] = truncar(_texto_final(transcricao), MAX_RESPOSTA_CODE)
        excluir = f":(exclude){AGENTE_CODE_ARQUIVO.as_posix()}"
        _git(worktree, "add", "-A", "-N", "--", ".", excluir)
        stat = _git(worktree, "diff", "--stat", "--", ".", excluir).stdout.strip()
        res["diff_stat"] = truncar(stat, 3000)
        if stat:
            res["worktree"] = str(worktree)
        else:
            _git(REPO_RAIZ, "worktree", "remove", "--force", str(worktree))  # sem mudança, nada a guardar
        if motivo:
            res["erro"] = motivo
        elif not res["resposta"]:
            res["erro"] = "o agente não devolveu texto (veja a transcrição)"
        else:
            res["ok"] = True
    except Exception as erro:  # a ferramenta nunca derruba a conversa
        res["erro"] = f"falha ao rodar o Agata Code ({type(erro).__name__})"
    finally:
        res["tempo_s"] = round(time.monotonic() - t0, 1)
    return res


def texto_agata_code(res: dict) -> str:
    """O que volta para a Seth (e para o gateway): resposta, diff --stat e caminhos."""
    linhas = []
    if res.get("erro"):
        linhas.append("erro: " + str(res["erro"]))
    if res.get("resposta"):
        linhas.append("Resposta do Agata Code:\n" + res["resposta"])
    linhas.append("git diff --stat:\n" + (res.get("diff_stat") or "(sem mudanças; worktree removida)"))
    if res.get("worktree"):
        linhas.append("Worktree: " + res["worktree"])
    if res.get("transcricao"):
        linhas.append("Transcrição: " + res["transcricao"])
    return truncar("\n\n".join(linhas))


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
        if nome == NOME_AGATA_CODE:
            return texto_agata_code(executar_agata_code(args))
        resp = _rpc_mcp([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": nome, "arguments": args}}])
        return truncar(_texto_mcp(resp.get(1) or {"error": {"message": "sem resposta do MCP"}}))
    except ErroMCP as erro:
        return f"erro: {erro}"
    except Exception as erro:  # a ferramenta nunca derruba a conversa
        return f"erro: {type(erro).__name__}"


def _id_chamada(c: dict, i: int) -> str:
    return str(c.get("id") or f"call_{i}")


def _args_json(argumentos) -> dict:
    try:
        args = json.loads(argumentos) if isinstance(argumentos, str) and argumentos.strip() else (argumentos or {})
    except ValueError:
        return {}
    return args if isinstance(args, dict) else {}


def _com_pulso(funcao, cancelar: threading.Event, intervalo: float | None = None):
    """Roda `funcao` numa thread e emite {"tipo":"estado"} a cada `intervalo` s até ela terminar (Regra 0: o stream não
    fica mudo). Se o gerador for fechado (o navegador saiu), sinaliza `cancelar` e o agente é morto. Devolve o resultado."""
    intervalo = PULSO_S if intervalo is None else intervalo
    saida = {}

    def alvo():
        try:
            saida["r"] = funcao()
        except Exception as erro:
            saida["e"] = erro

    thread = threading.Thread(target=alvo, daemon=True)
    thread.start()
    inicio = time.monotonic()
    try:
        while True:
            thread.join(intervalo)
            if not thread.is_alive():
                break
            yield {"tipo": "estado", "texto": f"Agata Code trabalhando… ({int(time.monotonic() - inicio)} s)"}
    finally:
        if thread.is_alive():
            cancelar.set()
    if "e" in saida:
        raise saida["e"]
    return saida["r"]


def laco(abrir_proxima, primeira_linhas, pedido: dict, executor=None, max_rodadas: int = MAX_RODADAS,
         executor_code=None, intervalo_pulso: float | None = None):
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
            if nome == NOME_AGATA_CODE:
                cancelar = threading.Event()
                args = _args_json(c["argumentos"])
                fn = executor_code or executar_agata_code
                yield {"tipo": "estado", "texto": "Agata Code trabalhando…"}
                res = yield from _com_pulso(lambda: fn(args, cancelar=cancelar), cancelar, intervalo_pulso)
                yield {"tipo": "agata_code", "resposta": res.get("resposta") or "", "diff_stat": res.get("diff_stat") or "",
                       "transcricao": res.get("transcricao") or "", "worktree": res.get("worktree") or "",
                       "erro": res.get("erro") or "", "tempo_s": res.get("tempo_s") or 0}
                conteudo = texto_agata_code(res)
            else:
                conteudo = executor(nome, c["argumentos"])
            pedido["messages"].append({"role": "tool", "tool_call_id": _id_chamada(c, i), "content": truncar(conteudo)})
        try:
            linhas = abrir_proxima(pedido)
        except OSError:
            yield {"tipo": "erro", "motivo": "gateway indisponível"}
            return
