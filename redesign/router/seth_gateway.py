#!/usr/bin/env python3
"""seth_gateway.py — reidrata a Seth antes do OmniRoute.

Fica entre o frontend (Open WebUI, Goose, curl) e o proxy de sanitização.
Escuta em 127.0.0.1:20126. Em cada POST /v1/chat/completions, se ainda não
houver uma mensagem de sistema hidratada, **antepõe** o conteúdo de
`.hidrata-seth.md` (REGRAS + PROJETO + janela de MEMÓRIAS, silo seth) como
mensagem `system` e repassa para :20127 (que sanitiza segredo) -> OmniRoute.

Assim qualquer frontend que apontar para :20126 fala com a Seth hidratada,
sem o Hermes. GET (/v1/models, /health) e streaming passam direto.

Só stdlib. Não instala nada, não lê chave nenhuma.

Uso:
    python3 redesign/router/seth_gateway.py
        # frontend aponta para http://127.0.0.1:20126

    python3 redesign/router/seth_gateway.py --selftest
        # sobe upstream dummy + gateway; manda 1 pedido sem system e confere
        # que o corpo repassado ganhou a mensagem system hidratada. exit 0 = OK.

Env:
    SETH_UPSTREAM        default http://127.0.0.1:20127   (o proxy sanitizador)
    SETH_BIND            default 127.0.0.1:20126
    SETH_HIDRATA         default ~/agata/.hidrata-seth.md
    SETH_HIDRATA_MODO    compacto (default) | full
        compacto -> cabeçalho curto + estado atual (estado_para_eco.sh) + ponteiro
                    p/ query_canon. Rápido, sem estourar o deadline do OmniRoute.
        full     -> injeta o .hidrata-seth.md inteiro (~45k tokens). Só com um
                    modelo de janela grande E o deadline do OmniRoute folgado.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

UPSTREAM = os.environ.get("SETH_UPSTREAM", "http://127.0.0.1:20127").rstrip("/")
_bind = os.environ.get("SETH_BIND", "127.0.0.1:20126")
BIND_HOST, BIND_PORT = _bind.split(":")[0], int(_bind.split(":")[1])
HIDRATA_PATH = Path(os.environ.get(
    "SETH_HIDRATA", str(Path.home() / "agata" / ".hidrata-seth.md")))
MODO = os.environ.get("SETH_HIDRATA_MODO", "compacto").lower()
REPO = Path(os.environ.get("SETH_REPO", str(Path.home() / "agata")))

# --- marcador amarrado a hash (achado 04/09/2026, Camada C) ----------------
# A versão anterior usava uma string fixa: qualquer system message que o
# CLIENTE mandasse contendo essa string era aceito como "já hidratado", sem
# nada ligando o marcador à injeção real deste gateway. Um cliente direto em
# :20126 (fora do LibreChat, ex.: um Goose mal configurado ou um teste solto)
# podia mandar só a linha do marcador e pular a hidratação inteira, olhando
# hidratado pro resto do pipeline sem estar. Agora o marcador carrega um hash
# do texto-fonte deste módulo (a doutrina fixa, não o bloco "Estado agora"
# que varia a cada chamada -- hashear isso forçaria reinjeção every turn,
# acumulando system messages). Não é defesa contra quem lê este arquivo (não
# há segredo aqui, é loopback) -- é o mesmo tipo de trava que P-8 documenta
# pra si mesmo: fecha o descuido/bug, não o contorno deliberado por quem já
# tem acesso ao código-fonte. Efeito colateral bom: também pega REDEPLOY —
# se este módulo mudar a doutrina, o hash muda, e uma conversa em andamento
# com o marcador velho volta a ser reidratada em vez de ficar presa à versão
# antiga pro resto da sessão.
_DOUTRINA_FIXA = (
    "Você é a **Seth**, o modelo do sistema **Agata** — governança pessoal "
    "canônica em git (REGRAS, PROJETO, MEMÓRIAS, append-only). Papéis: o "
    "**Humano decide**, você **propõe**, a Máquina arbitra fatos (rodando o "
    "comando, não afirmando de memória). Nada muda o canon sem passar pelo "
    "**portão** (as 3 perguntas). Não bajule, não simule emoção, não afirme "
    "sem fonte, não diga ter feito o que não fez.\n"
    "**Sem saudação, sem oferta de ajuda, sem encerramento performático** "
    "(REGRAS, Regra 5: \"Sem saudação, bajulação ou encerramento "
    "performático\"). Nada de \"Olá\", \"Como posso ajudar?\", \"Espero ter "
    "ajudado\". Depois do cabeçalho, vá direto ao assunto. Acrescentado em "
    "(422): a doutrina proibia bajular e não proibia saudar, e a saudação "
    "apareceu — a falta era da instrução, não sua.\n\n"
    "**Regra 1 — abra TODA resposta com o cabeçalho. São DUAS formas, e você "
    "usa UMA, nunca as duas juntas** (REGRAS, \"Carregar e formatos\": "
    "\"Cabeçalho: uma forma só, nunca as duas\"; misturar `modelo:` com `t=` "
    "é erro de formato).\n"
    "— **(a) Só na PRIMEIRA resposta da conversa** (o `carregar`), bloco de "
    "prontidão, 3 linhas, SEM `t=`:\n"
    "`Agata · modelo: <nome> · sync: <repita do bloco de estado> · <hora + selo>`\n"
    "`Última entrada: (<n>) <título> — <1 linha>`\n"
    "`<quebrado: liste em 1 linha>` ou `pronto.`\n"
    "  Sem nome confiável, a Regra 1 permite trocar `modelo: <nome>` por "
    "`modelo não verificado` ou `família <X>, versão não verificada` — nessa "
    "ordem de preferência, e último recurso, não o primeiro.\n"
    "— **(b) Em TODA resposta seguinte**, uma linha só, COM `t=` e SEM "
    "`Última entrada:`/`quebrado:`:\n"
    "`Agata · <modelo> · t=<n> (<base da contagem>) · <hora + selo>`\n"
    "  Corrigido em 10/09/2026, MEMÓRIAS (422): esta doutrina mandava fundir as "
    "duas — `t=` junto com `Última entrada:` e `quebrado:` em todo cabeçalho. "
    "Você obedecia certo uma instrução errada; o defeito era daqui.\n"
    "— **Última entrada:** `<n>` e `<título>` saem da linha `TOPO-MEMÓRIAS:` do "
    "bloco de estado abaixo, copiada, não inventada. Sem essa linha → "
    "`Última entrada: lacuna (estado não injetado)`. Nunca ponha `(0)` nem um "
    "número de memória.\n"
    "— **hora:** você não tem relógio de dentro. Copie a linha `HORA-MAQUINA:` "
    "do bloco de estado abaixo, exatamente como veio (valor + selo entre "
    "parênteses, ex.: `(relógio da Máquina)`) — é a Máquina medindo, você só "
    "repassa. O que vai entre parênteses é o SELO; **nunca** o `HASH-ESTADO`, "
    "que é outra linha e não entra no cabeçalho. Sem a linha `HORA-MAQUINA:` → "
    "`lacuna: sem relógio` (Regra 1.1). Nunca invente hora, nunca calcule, "
    "nunca repita a do cabeçalho anterior.\n"
    "— **t=<n>:** conte as SUAS respostas neste contexto (a resposta do modelo, "
    "não o par pergunta-resposta). Contexto compactado/resumido: se o resumo "
    "preserva a contagem de turnos, `t=<n> (contagem do resumo)`; se a contagem "
    "se perdeu, `t≥<n> (prefixo compactado)`. Não use contador de outra sessão.\n"
    "— **sync:** carregue a linha `sync:` do bloco de estado em TODO cabeçalho; "
    "se ela não veio, `sync: não verificado`. Se o bloco de estado traz "
    "`IDADE-HIDRATACAO` acima de ~15 min, anexe: `sync: PASS (hidratação ~Xmin, "
    "não re-medido)` — um PASS antigo que você não pode re-medir não é um PASS ao "
    "vivo.\n"
    "— **quebrado:** só no bloco de prontidão (a). Não repita ali a linha "
    "`sync:` — isso é reformulação, não item aberto. Procure em PROJETO, "
    "\"Estado dos bugs e dos testes\", e na janela de MEMÓRIAS: item aberto "
    "ali entra em `quebrado:`; nada aberto, `pronto.`.\n\n"
    "**Leitura parcial (Regra 2):** resultado de tool que diga 'cortado', "
    "'truncado', 'resumido', ou uma listagem SEM total explícito: NUNCA afirme o "
    "fim da lista, o intervalo, nem 'vai até X'. É `lacuna: leitura parcial` — "
    "peça a continuação, um sub-caminho, ou o total. O mesmo vale pro que sobra "
    "de um tool-result depois de uma compactação.\n\n"
    "**Listagem de diretório do vault pode estar VELHA, não truncada:** o índice "
    "do Obsidian headless fica atrás do disco — uma listagem de `entradas/` pode "
    "terminar antes da entrada mais recente e ainda trazer um total coerente "
    "(MEMÓRIAS (391)/(400)). Pra saber se uma entrada recente existe, LEIA o "
    "arquivo dela (`query_canon`), não conclua da listagem. Não estar na listagem "
    "≠ não existir no disco.\n\n"
    "O canon inteiro está no repositório; **não assuma o conteúdo** — peça o "
    "trecho com a tool `query_canon` (ou peça ao Humano). Este cabeçalho é a "
    "hidratação mínima; o resto é sob demanda.\n"
    "— **entrada (N) ≠ linha N.** Pra achar a entrada `(N)` de MEMÓRIAS, busque "
    "o marcador `(N)` com `query_canon` (grep), não peça o intervalo de linhas "
    "`N`: o argumento `linhas:` é número de linha física do arquivo, não de "
    "entrada.\n\n"
)
_HASH_DOUTRINA = hashlib.sha256(_DOUTRINA_FIXA.encode("utf-8")).hexdigest()[:8]
MARCADOR = f"<!-- SETH:HIDRATADO:{_HASH_DOUTRINA} -->"
# Bloco de estado FRESCO, reinjetado a cada turno (MEMÓRIAS (417)). O bloco de
# estado que entra junto da doutrina no 1º turno fica congelado -- hora e sync
# envelhecem, e do turno 2 em diante a Seth escrevia `lacuna: sem relógio` /
# `sync: não verificado` (viola Regra 1.1). Agora `_injeta`, quando a conversa
# já está hidratada, tira o ESTADO-ATUAL anterior e põe um novo com a hora/sync
# do momento. Curto (só a saída de estado_para_eco.sh), sem repetir a doutrina.
MARCADOR_ESTADO = "<!-- SETH:ESTADO-ATUAL -->"

_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}

_CACHE: dict = {"mtime": None, "texto": ""}


def _estado() -> str:
    """Saída curta de scripts/estado_para_eco.sh (HEAD, topo de MEMÓRIAS, sync).
    Best-effort — se falhar, devolve string vazia."""
    import subprocess
    try:
        # 25s (era 15): estado_para_eco.sh faz `git ls-remote` -- local e' instantâneo,
        # mas o remoto pode dar um pico de rede que estourava 15s e a Seth abria sem
        # bloco de estado (MEMÓRIAS (394): `Última entrada: (0)`).
        r = subprocess.run(["bash", "scripts/estado_para_eco.sh"], cwd=REPO,
                           capture_output=True, text=True, timeout=25)
        linhas = [l for l in r.stdout.splitlines()
                  if l.startswith(("HEAD:", "TOPO-MEMÓRIAS:", "sync:",
                                    "IDADE-HIDRATACAO:", "HORA-MAQUINA:",
                                    "HASH-ESTADO:"))]
        return "\n".join(linhas)
    except Exception:
        return ""


def _hidratacao() -> str:
    """Modo compacto (default): cabeçalho + estado atual. Modo full: o arquivo inteiro."""
    if MODO == "compacto":
        est = _estado()
        # Regra 1.1: campo medível não pode sumir em silêncio quando a
        # medição falha -- antes, `est` vazio só omitia o bloco inteiro sem
        # dizer que algo quebrou (achado 04/09/2026, Camada C).
        bloco_estado = (
            f"**Estado agora (fatos da Máquina):**\n{est}\n" if est
            else "**Estado agora:** `lacuna: estado_para_eco.sh falhou ou não rodou "
                 "(sem shell/Máquina daqui?) — não afirme HEAD/sync sem medir.`\n"
        )
        return f"{MARCADOR}\n{_DOUTRINA_FIXA}{bloco_estado}"
    try:
        st = HIDRATA_PATH.stat()
        if _CACHE["mtime"] != st.st_mtime:
            _CACHE["texto"] = HIDRATA_PATH.read_text(encoding="utf-8")
            _CACHE["mtime"] = st.st_mtime
    except OSError:
        return f"{MARCADOR}\n(hidratação indisponível: {HIDRATA_PATH} não pôde ser lido)"
    return f"{MARCADOR}\n" + _CACHE["texto"]


def _bloco_estado_atual() -> str:
    """Bloco de estado FRESCO pra reinjetar em turno já hidratado (MEMÓRIAS (417)).
    String vazia se estado_para_eco.sh não deu saída — nesse caso não reinjeta
    nada (a Seth fica com o bloco velho do 1º turno, honesto via IDADE-HIDRATACAO)."""
    est = _estado()
    if not est:
        return ""
    return (f"{MARCADOR_ESTADO}\n**Estado agora (Máquina, medido neste turno — "
            f"vale MAIS que qualquer bloco de estado anterior nesta conversa; "
            f"use ESTA hora e ESTE `sync:`):**\n{est}\n")


# --- chamadas utilitárias do frontend que NÃO devem ser hidratadas ---------
# O LibreChat (e outros frontends) fazem, além do turno de chat, chamadas
# auxiliares ao mesmo endpoint: geração de TÍTULO da conversa, sumarização,
# etc. Injetar a hidratação inteira nelas é: (a) desperdício -- a doutrina + o
# estado não têm nada a ver com "escreva um título"; (b) perigoso -- no
# LibreChat a geração de título roda uma 2ª run CONCORRENTE no mesmo
# AgentClient (modo `immediate`), e uma chamada de título grande/lenta estoura
# o timeout de 45s do `title.js`, cujo `AbortController` compartilhado fazia a
# resposta PRINCIPAL ser gravada vazia (MEMÓRIAS (411)).
#
# Detector: strings LITERAIS que o `@librechat/agents` põe no prompt de título
# ou no schema de saída estruturada (`dist/*/utils/title.*`). São texto GERADO
# pelo frontend, nunca conteúdo de usuário -- casar por elas não tem falso
# positivo prático. Se um usuário colar exatamente uma dessas frases, o pior
# caso é aquele turno sair sem hidratação (`Última entrada: lacuna`),
# recuperável. Fonte conferida no container em 09/09/2026.
_SINAIS_TITULO = (
    "A concise title in the detected language",
    "A concise title for the conversation in 5 words or less",
    "Provide a concise, 5-word-or-less title for the conversation",
    "Analyze this conversation and provide",
)


def _e_chamada_utilitaria(payload: dict) -> bool:
    """True se o corpo parece uma chamada de título/utilidade do frontend
    (não um turno de chat real). Varre o JSON inteiro -- a frase pode estar
    numa message, em tools[].function.description ou em response_format."""
    try:
        blob = json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError):
        return False
    return any(s in blob for s in _SINAIS_TITULO)


# --- Roteador por complexidade (MEMÓRIAS (416); reabre a (383) com premissa nova) --
# A Seth roda na cascata cloud `seth-livre` (OmniRoute, strategy=priority): toda
# requisição começa no tier 0 e só cai por falha. Quando o tier de topo está
# lento, "oi" paga o mesmo que uma análise longa. Este classificador -- SÓ REGRAS,
# nenhuma inferência extra, ~microssegundos -- reescreve o alvo quando o modelo
# pedido é exatamente "seth-livre" (o default do Agent). Specs manuais
# (seth-zai/seth-gemini/etc.) chegam com o model já concreto -> NÃO são tocadas.
# Os 3 combos (seth-rapido / seth-livre / seth-pesado) são priority e TODOS
# terminam nos mesmos modelos confiáveis -- misroteamento degrada latência/força,
# nunca quebra. Rodar ANTES de _injeta: a hidratação (~3,8k chars) empurraria
# tudo pra "não trivial".
_ROTA_BASE = "seth-livre"
_LIMIAR_TRIVIAL_CHARS = 400
_LIMIAR_PESADO_CHARS = 6000
_LIMIAR_PESADO_MSGS = 10


def _texto_e_sinais(msgs: list) -> tuple[int, int, bool]:
    """(total de chars de conteúdo, nº de mensagens 'user', tem cerca de código)."""
    total, n_user, codigo = 0, 0, False
    for m in msgs:
        if not isinstance(m, dict):
            continue
        if m.get("role") == "user":
            n_user += 1
        c = m.get("content")
        pedacos = [c] if isinstance(c, str) else (
            [p.get("text") for p in c if isinstance(p, dict)] if isinstance(c, list) else [])
        for t in pedacos:
            if isinstance(t, str):
                total += len(t)
                if "```" in t:
                    codigo = True
    return total, n_user, codigo


def _classificar_rota(payload: dict) -> str:
    """seth-livre -> seth-rapido | seth-livre | seth-pesado. Heurística pura."""
    msgs = payload.get("messages")
    if not isinstance(msgs, list):
        return _ROTA_BASE
    tem_tools = bool(payload.get("tools"))
    total, n_user, codigo = _texto_e_sinais(msgs)
    if total > _LIMIAR_PESADO_CHARS or codigo or len(msgs) > _LIMIAR_PESADO_MSGS:
        return "seth-pesado"
    if total < _LIMIAR_TRIVIAL_CHARS and not tem_tools and n_user <= 2:
        return "seth-rapido"
    return _ROTA_BASE


def _injeta(payload: dict) -> dict:
    msgs = payload.get("messages")
    if not isinstance(msgs, list):
        return payload
    # chamada de título/utilidade do frontend: repassa crua, sem hidratar.
    if _e_chamada_utilitaria(payload):
        return payload
    ja_hidratado = any(
        isinstance(m, dict) and m.get("role") == "system"
        and isinstance(m.get("content"), str) and MARCADOR in m["content"]
        for m in msgs)
    if ja_hidratado:
        # não repete a doutrina, mas REFRESCA o estado (MEMÓRIAS (417)): tira o
        # ESTADO-ATUAL do turno anterior e põe um com a hora/sync de agora.
        msgs = [m for m in msgs if not (
            isinstance(m, dict) and m.get("role") == "system"
            and isinstance(m.get("content"), str) and MARCADOR_ESTADO in m["content"])]
        bloco = _bloco_estado_atual()
        payload["messages"] = ([{"role": "system", "content": bloco}] + msgs
                               if bloco else msgs)
        return payload
    sys_msg = {"role": "system", "content": _hidratacao()}
    # se o frontend já mandou um system próprio, o nosso entra ANTES dele
    payload["messages"] = [sys_msg] + msgs
    return payload


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    _rota = ""   # rota escolhida pelo classificador nesta requisição (observabilidade)

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        self._passar(b"", "GET")

    def do_HEAD(self):
        self._passar(b"", "HEAD")

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(n) if n else b""
        ctype = (self.headers.get("Content-Type") or "").lower()
        if "application/json" in ctype and corpo and "/chat/completions" in self.path:
            try:
                payload = json.loads(corpo)
            except ValueError:
                return self._erro(400, "corpo marcado como JSON mas não parseia")
            if isinstance(payload, dict):
                # roteador por complexidade: só o alvo "seth-livre" do Agent
                if payload.get("model") == _ROTA_BASE:
                    self._rota = _classificar_rota(payload)
                    payload["model"] = self._rota
                corpo = json.dumps(_injeta(payload), ensure_ascii=False).encode("utf-8")
        self._passar(corpo, "POST")

    def _passar(self, corpo: bytes, metodo: str):
        url = UPSTREAM + self.path
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in _HOP_BY_HOP}
        req = urllib.request.Request(url, data=corpo or None, method=metodo, headers=headers)
        try:
            up = urllib.request.urlopen(req, timeout=180)
        except urllib.error.HTTPError as e:
            up = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            return self._erro(502, f"upstream ({UPSTREAM}) inacessível: {e}. "
                                   "Suba o sanitizador: systemctl --user start omniroute-sanitizer omniroute")
        self.send_response(up.status)
        for k, v in up.headers.items():
            if k.lower() not in _HOP_BY_HOP:
                self.send_header(k, v)
        if self._rota:
            self.send_header("X-Seth-Rota", self._rota)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        sse = "text/event-stream" in (up.headers.get("Content-Type") or "").lower()
        try:
            if sse:
                self._stream_sse_filtrado(up)
            else:
                while True:
                    pedaco = up.read(8192)
                    if not pedaco:
                        break
                    self.wfile.write(f"{len(pedaco):X}\r\n".encode())
                    self.wfile.write(pedaco)
                    self.wfile.write(b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
        except (BrokenPipeError, ConnectionResetError):
            # O cliente (LibreChat) desconectou no meio do stream -- reload da
            # página, timeout do navegador. Abandona ESTA requisição em silêncio;
            # sem isto a exceção subia e o servidor inteiro emperrava (a Seth
            # "travou" no teste 3, MEMÓRIAS (393)). close_connection pra o
            # keep-alive não reusar o socket morto.
            self.close_connection = True
        finally:
            up.close()

    # Chunks-sentinela de keep-alive que o OmniRoute emite ANTES de escolher/
    # conectar o provedor: `data: {"id":"chatcmpl-keepalive","model":"keepalive",
    # "choices":[{"delta":{},"finish_reason":null}]}`. Servem só pra segurar a
    # conexão HTTP durante a latência de seleção -- não carregam conteúdo.
    # O acumulador de tool-call em streaming do LibreChat (@librechat/agents)
    # tropeça neles: o `id` muda de `chatcmpl-keepalive` pro `chatcmpl-msg_...`
    # real, e os deltas de `function.arguments` (que só trazem `index`, sem `id`
    # nem `name`) acabam órfãos -> a tool é chamada com `arguments: ""` e falha
    # ("Cancelado" na UI). Achado 09/09/2026 comparando o SSE cru do :20126 (que
    # traz os args certinhos, formato OpenAI padrão) com o que o LibreChat grava.
    # Aqui a gente troca cada linha `data:` de keepalive por um COMENTÁRIO SSE
    # (`: ka`) -- mantém a conexão quente, e todo parser de SSE ignora linha que
    # começa com `:`. O resto do stream passa byte a byte.
    _SSE_KEEPALIVE = (b'"chatcmpl-keepalive"', b'"model":"keepalive"',
                      b'"model": "keepalive"')

    @classmethod
    def _filtrar_linha_sse(cls, linha: bytes) -> bytes:
        """Uma linha `data:` de keepalive vira comentário SSE (`: ka`); o resto
        passa intacto. Pura -- testada no --selftest."""
        if linha.startswith(b"data:") and any(m in linha for m in cls._SSE_KEEPALIVE):
            return b": ka\n" if linha.endswith(b"\n") else b": ka"
        return linha

    def _stream_sse_filtrado(self, up):
        """Repassa o SSE do upstream, trocando os chunks-sentinela de keepalive
        do OmniRoute por comentários SSE. Line-buffered: um read do upstream pode
        cair no meio de uma linha."""
        buf = b""
        while True:
            pedaco = up.read(8192)
            if not pedaco:
                break
            buf += pedaco
            while b"\n" in buf:
                linha, buf = buf.split(b"\n", 1)
                saida = self._filtrar_linha_sse(linha + b"\n")
                self.wfile.write(f"{len(saida):X}\r\n".encode())
                self.wfile.write(saida)
                self.wfile.write(b"\r\n")
        if buf:
            saida = self._filtrar_linha_sse(buf)
            self.wfile.write(f"{len(saida):X}\r\n".encode())
            self.wfile.write(saida)
            self.wfile.write(b"\r\n")

    def _erro(self, code: int, msg: str):
        corpo = json.dumps({"error": {"type": "seth_gateway_error", "message": msg}},
                           ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        try:
            self.wfile.write(corpo)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True  # cliente já foi; ver _passar


def servir(host: str = BIND_HOST, port: int = BIND_PORT):
    srv = ThreadingHTTPServer((host, port), _Handler)
    print(f"seth_gateway em http://{host}:{port}  ->  {UPSTREAM}  "
          f"(hidratação: {MODO}, {HIDRATA_PATH.name})")
    srv.serve_forever()


# --------------------------------------------------------------------------- #
def _porta_livre() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class _Dummy(BaseHTTPRequestHandler):
    ultimo_corpo = b""

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        type(self).ultimo_corpo = self.rfile.read(n)
        corpo = json.dumps({"choices": [{"message": {"role": "assistant", "content": "ok"}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def _selftest() -> int:
    global UPSTREAM
    up_port, gw_port = _porta_livre(), _porta_livre()
    UPSTREAM = f"http://127.0.0.1:{up_port}"
    up = ThreadingHTTPServer(("127.0.0.1", up_port), _Dummy)
    gw = ThreadingHTTPServer(("127.0.0.1", gw_port), _Handler)
    threading.Thread(target=up.serve_forever, daemon=True).start()
    threading.Thread(target=gw.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{gw_port}/v1/chat/completions"
    falhas = 0

    # 1. pedido sem system -> o corpo repassado ao upstream ganha 1 system hidratado
    body = json.dumps({"model": "seth", "messages": [{"role": "user", "content": "oi"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body, headers={"Content-Type": "application/json"}), timeout=10).read()
    repassado = json.loads(_Dummy.ultimo_corpo)
    m = repassado["messages"]
    ok = (m[0]["role"] == "system" and MARCADOR in m[0]["content"]
          and m[1]["role"] == "user" and len(m) == 2)
    print(f"{'PASS' if ok else 'FALHA'}  sem system -> injetou 1 system hidratado antes do user "
          f"({len(m[0]['content'])} chars)")
    falhas += 0 if ok else 1

    # 2. pedido JÁ hidratado -> NÃO repete a doutrina, MAS reinjeta ESTADO-ATUAL
    body2 = json.dumps({"model": "seth", "messages": [
        {"role": "system", "content": f"{MARCADOR}\nx"},
        {"role": "user", "content": "oi"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body2, headers={"Content-Type": "application/json"}), timeout=10).read()
    m2 = json.loads(_Dummy.ultimo_corpo)["messages"]
    hidr = [x for x in m2 if isinstance(x.get("content"), str) and MARCADOR in x["content"]]
    est = [x for x in m2 if isinstance(x.get("content"), str) and MARCADOR_ESTADO in x["content"]]
    ok2 = (len(hidr) == 1 and hidr[0]["content"] == f"{MARCADOR}\nx"  # doutrina não repetida
           and len(est) == 1 and m2[0]["content"].startswith(MARCADOR_ESTADO))  # 1 estado fresco no topo
    print(f"{'PASS' if ok2 else 'FALHA'}  já hidratado -> doutrina intacta + 1 ESTADO-ATUAL "
          f"(msgs={len(m2)}, hidr={len(hidr)}, est={len(est)})")
    falhas += 0 if ok2 else 1

    # 2b. ESTADO-ATUAL velho no input -> substituído (nunca acumula)
    body2b = json.dumps({"model": "seth", "messages": [
        {"role": "system", "content": f"{MARCADOR_ESTADO}\nVELHO"},
        {"role": "system", "content": f"{MARCADOR}\nx"},
        {"role": "user", "content": "oi"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body2b, headers={"Content-Type": "application/json"}), timeout=10).read()
    m2b = json.loads(_Dummy.ultimo_corpo)["messages"]
    est_b = [x for x in m2b if isinstance(x.get("content"), str) and MARCADOR_ESTADO in x["content"]]
    ok2b = len(est_b) == 1 and "VELHO" not in est_b[0]["content"]
    print(f"{'PASS' if ok2b else 'FALHA'}  ESTADO-ATUAL velho -> substituído, não acumulou "
          f"(est={len(est_b)})")
    falhas += 0 if ok2b else 1

    # 3. chamada de TÍTULO do LibreChat -> repassada crua, SEM system hidratado
    body3 = json.dumps({"model": "seth", "messages": [
        {"role": "user", "content": "Analyze this conversation and provide:\n1. The "
         "detected language\n2. A concise title in the detected language (5 words "
         "or less, no punctuation or quotation)\n\nUser: oi\nAssistant: ok"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body3, headers={"Content-Type": "application/json"}), timeout=10).read()
    m3 = json.loads(_Dummy.ultimo_corpo)["messages"]
    ok3 = len(m3) == 1 and m3[0]["role"] == "user" and MARCADOR not in m3[0]["content"]
    print(f"{'PASS' if ok3 else 'FALHA'}  chamada de título -> repassada sem hidratar "
          f"(messages={len(m3)}, role0={m3[0]['role']})")
    falhas += 0 if ok3 else 1

    # 4. chat normal com a palavra "título" no meio -> AINDA hidrata (sem falso positivo)
    body4 = json.dumps({"model": "seth", "messages": [
        {"role": "user", "content": "que título você daria pra essa conversa?"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body4, headers={"Content-Type": "application/json"}), timeout=10).read()
    m4 = json.loads(_Dummy.ultimo_corpo)["messages"]
    ok4 = len(m4) == 2 and m4[0]["role"] == "system" and MARCADOR in m4[0]["content"]
    print(f"{'PASS' if ok4 else 'FALHA'}  chat que fala de título -> hidratou normal "
          f"(messages={len(m4)})")
    falhas += 0 if ok4 else 1

    # 5. filtro de keepalive SSE: linha de keepalive -> comentário; resto intacto
    ka = (b'data: {"id":"chatcmpl-keepalive","object":"chat.completion.chunk",'
          b'"created":0,"model":"keepalive","choices":[{"index":0,"delta":{},'
          b'"finish_reason":null}]}\n')
    real = (b'data: {"id":"chatcmpl-msg_x","choices":[{"index":0,"delta":'
            b'{"tool_calls":[{"index":0,"function":{"arguments":"250"}}]}}]}\n')
    r_ka = _Handler._filtrar_linha_sse(ka)
    r_real = _Handler._filtrar_linha_sse(real)
    r_blank = _Handler._filtrar_linha_sse(b"\n")
    r_done = _Handler._filtrar_linha_sse(b"data: [DONE]\n")
    ok5 = (r_ka == b": ka\n" and r_real == real and r_blank == b"\n"
           and r_done == b"data: [DONE]\n")
    print(f"{'PASS' if ok5 else 'FALHA'}  SSE: keepalive->': ka', tool_call/blank/[DONE] intactos "
          f"(ka={r_ka!r})")
    falhas += 0 if ok5 else 1

    # 6-9. classificador de rota (pura, sem rede)
    r_triv = _classificar_rota({"model": "seth-livre",
                                "messages": [{"role": "user", "content": "oi"}]})
    r_norm = _classificar_rota({"model": "seth-livre", "messages": [
        {"role": "user", "content": "x" * 1200}]})
    r_pesado_txt = _classificar_rota({"model": "seth-livre", "messages": [
        {"role": "user", "content": "y" * 7000}]})
    r_pesado_cod = _classificar_rota({"model": "seth-livre", "messages": [
        {"role": "user", "content": "veja isso ```def f(): pass```"}]})
    r_triv_tools = _classificar_rota({"model": "seth-livre", "tools": [{"x": 1}],
                                      "messages": [{"role": "user", "content": "oi"}]})
    ok6 = r_triv == "seth-rapido"
    ok7 = r_norm == "seth-livre"
    ok8 = r_pesado_txt == "seth-pesado" and r_pesado_cod == "seth-pesado"
    ok9 = r_triv_tools == "seth-livre"   # curto MAS com tools -> não é trivial
    for n, ok, desc in [(6, ok6, f"'oi' -> seth-rapido (deu {r_triv})"),
                        (7, ok7, f"1200 chars -> seth-livre (deu {r_norm})"),
                        (8, ok8, f"7000 chars / código -> seth-pesado ({r_pesado_txt}/{r_pesado_cod})"),
                        (9, ok9, f"curto+tools -> seth-livre (deu {r_triv_tools})")]:
        print(f"{'PASS' if ok else 'FALHA'}  rota {n}: {desc}")
        falhas += 0 if ok else 1

    up.shutdown()
    gw.shutdown()
    print(f"\n{'SELFTEST OK' if not falhas else f'SELFTEST FALHOU ({falhas})'}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        raise SystemExit(_selftest())
    servir()
