#!/usr/bin/env python3
"""seth_gateway.py — reidrata a Seth antes do OmniRoute.

Fica entre o frontend (Open WebUI, Goose, curl) e o proxy de sanitização.
Escuta em 127.0.0.1:20126. Em cada POST /v1/chat/completions, se ainda não
houver uma mensagem de sistema hidratada, **antepõe** o conteúdo de
`.hidrata-seth.md` (REGRAS + PROJETO + janela de MEMÓRIAS, silo seth) como
mensagem `system` e repassa para :20127 (que sanitiza segredo) -> OmniRoute.

Assim qualquer frontend que apontar para :20126 fala com a Seth hidratada,
sem o Hermes. GET (/v1/models, /health) e streaming passam direto.

Só stdlib. Não instala nada. Lê UMA coisa de ~/.config/agata/.env desde o
item 3 do plano de mitigação da auditoria do Marcos (MEMÓRIAS (437)):
AGATA_INTERNAL_TOKEN, que este processo anexa em toda chamada ao proxy
sanitizador -- a fronteira localhost sozinha não provava quem estava do
outro lado da chamada.

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
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

UPSTREAM = os.environ.get("SETH_UPSTREAM", "http://127.0.0.1:20127").rstrip("/")
_bind = os.environ.get("SETH_BIND", "127.0.0.1:20126")
BIND_HOST, BIND_PORT = _bind.split(":")[0], int(_bind.split(":")[1])
HIDRATA_PATH = Path(os.environ.get(
    "SETH_HIDRATA", str(Path.home() / "agata" / ".hidrata-seth.md")))
# Pedido de (615): a Seth se identificar pelo modelo real na própria fala, não
# só por header HTTP invisível (X-Modelo-Real, (613)/(614)). Só se sabe o
# modelo DEPOIS da resposta terminar -- por isso este arquivo guarda o nome
# do turno ANTERIOR pro PRÓXIMO turno citar, sempre rotulado com o atraso
# (_DOUTRINA_FIXA abaixo). Fora do repo (estado efêmero, mesmo padrão de
# ~/.cache/agata/ls-remote-main). Global, não por conversa -- se houver duas
# conversas simultâneas, uma pode herdar o nome da outra por 1 turno; risco
# aceito (Portão das três perguntas, MEMÓRIAS (620)/(621)): sempre visível
# (o Humano vê o nome errado na hora), nunca silencioso.
MODELO_REAL_PATH = Path(os.environ.get(
    "SETH_MODELO_REAL_PATH", str(Path.home() / ".cache" / "agata" / "seth-modelo-real-ultimo.txt")))

_ENV_PATH = os.path.expanduser("~/.config/agata/.env")


def _token_interno() -> str:
    """Lê AGATA_INTERNAL_TOKEN de ~/.config/agata/.env. Nunca loga o valor.
    Mesma função de redesign/router/proxy.py -- duplicação deliberada,
    igual à de _e_comportamento em redesign/grafo/tools.py: são só 8
    linhas, e as duas cópias lêem o MESMO arquivo pela MESMA chave, risco
    de deriva baixo. Unificação real fica pro item 11/Fase E do plano."""
    try:
        with open(_ENV_PATH, encoding="utf-8") as f:
            for linha in f:
                if linha.startswith("AGATA_INTERNAL_TOKEN="):
                    return linha.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""
MODO = os.environ.get("SETH_HIDRATA_MODO", "compacto").lower()
REPO = Path(os.environ.get("SETH_REPO", str(Path.home() / "agata")))
sys.path.insert(0, str(REPO / "scripts"))
from http_seguro import ler_corpo_limitado, ServidorConcorrenciaLimitada  # noqa: E402

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
    "  **`modelo:` quer o MODELO, não a persona.** \"Seth\" é como o sistema "
    "te chama; por baixo roda uma cascata que troca de modelo por requisição. "
    "A Regra 1 existe para rastrear QUEM disse o quê, e \"Seth\" não responde "
    "isso. Se você sabe o modelo, diga-o; se não sabe — que é o caso normal na "
    "cascata — `modelo não verificado` é a resposta certa e honesta, não um "
    "rebaixamento. `família <X>, versão não verificada` quando souber a família. "
    "Nunca escreva `modelo: Seth`. (MEMÓRIAS (424).)\n"
    "  **Se o bloco de estado trouxer `MODELO-REAL-TURNO-ANTERIOR:`, use esse "
    "nome — é fato da Máquina (medido de verdade no `X-Modelo-Real`), não seu "
    "palpite. Mas é do TURNO ANTERIOR, nunca deste: só se sabe o modelo DEPOIS "
    "da resposta terminar. Escreva `<nome> (medido no turno anterior pela "
    "Máquina; este turno ainda não medido)` — nunca apresente como medição de "
    "agora. Sem essa linha, siga a regra de cima: `modelo não verificado`. "
    "Vale pro mesmo campo nas DUAS formas do cabeçalho — `modelo:` em (a), "
    "`<modelo>` em (b). (MEMÓRIAS (621).)\n"
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
    "— **TOPO-PROPOSTA-JA-APLICADA:** se essa linha vier no bloco de estado, o "
    "texto da entrada do topo (ex.: \"aguardando assinatura\") já está "
    "desatualizado — a proposta citada foi assinada e aplicada DEPOIS de a "
    "entrada ter sido escrita, e a entrada não ganha correção própria (Regra "
    "4: correção é entrada nova, nunca edição do texto existente). Copie a "
    "entrada normalmente, mas não afirme o status dela como atual — diga que "
    "está aplicada, apontando pra esta linha. Achado auditando você mesma, "
    "MEMÓRIAS (464)/(465): sem isto, você repetiria \"aguardando assinatura\" "
    "pra sempre, mesmo commits depois de já resolvido.\n"
    "— **ALERTA-HISTORIA:** se essa linha vier no bloco de estado, a cópia "
    "local de MEMÓRIAS.md perdeu história sem commit (Regra 4, linha vermelha). "
    "Ponha isso PRIMEIRO em `quebrado:`, copiado da linha, e não chame "
    "`memoria_acrescentar`/`diario_anotar` até o Humano resolver — escrever em "
    "cima da cópia mutilada só esconde o dano. Achado real, MEMÓRIAS (516)/(517).\n"
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
    "— **sync:** copie a linha `sync:` do bloco de estado **INTEIRA**, com os "
    "campos, nunca só a palavra. `sync: PASS` sozinho é ERRO: REGRAS, \"'sync' "
    "tem preço\", exige `PASS · REGRAS=<hash8> · MEMÓRIAS=<hash8> · "
    "HEAD=<commit7>` — sem as três medidas, PASS é afirmação, não verificação, "
    "e quem lê seu cabeçalho não tem como conferir nada. Truncou? então é "
    "`sync: não verificado`, não PASS. (Medido em 10/09/2026, MEMÓRIAS (424): "
    "a Máquina entregou a linha completa e o cabeçalho saiu com `PASS` nu.) "
    "Hoje você também pode medir sozinha: `maquina_verificar{comando:\"estado\"}`. "
    "Carregue a linha em TODO cabeçalho; "
    "se ela não veio, `sync: não verificado`. Se o bloco de estado traz "
    "`IDADE-HIDRATACAO` acima de ~15 min, anexe: `sync: PASS (hidratação ~Xmin, "
    "não re-medido)` — um PASS antigo que você não pode re-medir não é um PASS ao "
    "vivo.\n"
    "— **quebrado:** só no bloco de prontidão (a). Não repita ali a linha "
    "`sync:` — isso é reformulação, não item aberto. Procure em PROJETO, "
    "\"Estado dos bugs e dos testes\", e na janela de MEMÓRIAS: item aberto "
    "ali entra em `quebrado:`; nada aberto, `pronto.`.\n\n"
    "**Você PODE medir a Máquina — use antes de afirmar.** A tool "
    "`maquina_verificar` roda uma verificação real no host e devolve a saída: "
    "`perimetro` (os 17 controles), `estado`, `git_status`, `git_log`, "
    "`git_diff_stat`, `git_sync` (SHA do remoto), `selos`, `suite_controles`, "
    "`servicos`. Regra 2 manda medir, não lembrar: se for AFIRMAR algo sobre o "
    "estado do sistema, rode e cite a saída, não o que você acha. É "
    "read-only e lista fechada — não escreve, não commita, não aceita comando "
    "livre; comando fora da lista volta 400 com a lista junto. Fora do ar → "
    "`lacuna`, nunca suposição. Nasceu do seu pedido por interpretador de "
    "código, MEMÓRIAS (423): você ganhou o poder de verificar, não o de mudar — "
    "seu único caminho de escrita continua sendo o `memoria_acrescentar`/"
    "`diario_anotar` (append-only).\n\n"
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
                                    "HASH-ESTADO:", "TOPO-PROPOSTA-JA-APLICADA:",
                                    "ALERTA-HISTORIA:", "SYNC-REMOTO-IDADE:"))]
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
        if est:
            linha_modelo = _linha_modelo_real_anterior()
            corpo = est + (f"\n{linha_modelo}" if linha_modelo else "")
            bloco_estado = f"**Estado agora (fatos da Máquina):**\n{corpo}\n"
        else:
            bloco_estado = ("**Estado agora:** `lacuna: estado_para_eco.sh falhou ou não rodou "
                             "(sem shell/Máquina daqui?) — não afirme HEAD/sync sem medir.`\n")
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
    linha_modelo = _linha_modelo_real_anterior()
    corpo = est + (f"\n{linha_modelo}" if linha_modelo else "")
    return (f"{MARCADOR_ESTADO}\n**Estado agora (Máquina, medido neste turno — "
            f"vale MAIS que qualquer bloco de estado anterior nesta conversa; "
            f"use ESTA hora e ESTE `sync:`):**\n{corpo}\n")


def _lembrar_modelo_real(nome: str) -> None:
    """Grava o modelo real medido NESTA resposta (`X-Modelo-Real`), pro PRÓXIMO
    turno poder citá-lo -- só se sabe o modelo depois da resposta terminar, daí
    o atraso de 1 turno (mesma limitação já aceita em (613)). Best-effort:
    falha de disco (permissão, cheio) nunca derruba a resposta que está sendo
    servida -- o pior caso é a linha nova não aparecer no próximo turno."""
    try:
        MODELO_REAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = MODELO_REAL_PATH.with_suffix(".tmp")
        tmp.write_text(nome, encoding="utf-8")
        tmp.replace(MODELO_REAL_PATH)
    except OSError:
        pass


def _modelo_real_anterior() -> str | None:
    """Último modelo real medido (turno anterior -- de QUALQUER conversa, o
    arquivo é global, ver nota em MODELO_REAL_PATH). None se nunca mediu ou
    o arquivo sumiu."""
    try:
        nome = MODELO_REAL_PATH.read_text(encoding="utf-8").strip()
        return nome or None
    except OSError:
        return None


def _linha_modelo_real_anterior() -> str:
    """'MODELO-REAL-TURNO-ANTERIOR: <nome>' se houver um medido, ou "" se não.
    A doutrina (_DOUTRINA_FIXA) instrui a Seth a rotular isto como medição do
    TURNO ANTERIOR, nunca deste -- é fato da Máquina (X-Modelo-Real), não
    palpite do modelo (REGRAS, Os 3 papéis; evita a classe FALHAS IDF-1)."""
    nome = _modelo_real_anterior()
    return f"MODELO-REAL-TURNO-ANTERIOR: {nome}" if nome else ""


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

# Sinal separado pro Goose (achado 21/09/2026, MEMÓRIAS (495)): ele também faz
# uma chamada de "nomear a sessão" pro MESMO endpoint (:20126), sistema PRÓPRIO
# do cliente Goose, nunca visto antes porque o LibreChat era o único frontend
# auditado até aqui. Capturado com um proxy de log real entre o Goose e este
# gateway (não suposto) -- corpo de verdade:
#   {"model":"seth-codigo","messages":[
#     {"role":"system","content":"Generate a short title (four words or less)
#       that describes the topic of the user's messages. \nReply with only
#       the title, nothing else..."},
#     {"role":"user","content":"---BEGIN USER MESSAGES---\n...\n---END USER
#       MESSAGES---\n\nGenerate a short title for the above messages."}],
#    "stream":true,"stream_options":{"include_usage":true}}
# Diferença estrutural do padrão LibreChat: o texto-gatilho está na PRIMEIRA
# mensagem (system), não na última -- por isso checado à parte de
# `_SINAIS_TITULO` (que só olha `msgs[-1]`), em QUALQUER posição/papel.
# Mesma classe de risco residual já declarada acima para `_SINAIS_TITULO`:
# string literal do PRÓPRIO cliente, não conteúdo de usuário -- colar esse
# texto exato como mensagem própria no pior caso perde só a hidratação
# daquele turno.
_SINAIS_TITULO_GOOSE = (
    "Generate a short title (four words or less) that describes the topic "
    "of the user's messages",
)


def _e_chamada_titulo_goose(payload: dict) -> bool:
    """Sinal 3 de `_e_chamada_utilitaria`: chamada de nomear-sessão do Goose,
    que carrega o texto-gatilho na PRIMEIRA mensagem (system), não na
    última. Varre todas as mensagens (posição não importa aqui), mas só
    quando `len(messages) <= 2` -- mesmo limite dos outros sinais, é sempre
    one-shot."""
    msgs = payload.get("messages")
    if not isinstance(msgs, list) or not msgs or len(msgs) > 2:
        return False
    for m in msgs:
        if not isinstance(m, dict):
            continue
        conteudo = m.get("content")
        if isinstance(conteudo, list):
            texto = " ".join(p.get("text", "") for p in conteudo if isinstance(p, dict))
        elif isinstance(conteudo, str):
            texto = conteudo
        else:
            continue
        if any(s in texto for s in _SINAIS_TITULO_GOOSE):
            return True
    return False


def _schema_pede_titulo(payload: dict) -> bool:
    """Sinal FORTE, não forjável por dado externo: o @librechat/agents monta
    a chamada de título com `model.withStructuredOutput(titleSchema)`
    (node_modules/@librechat/agents/dist/cjs/utils/title.cjs, conferido no
    container real em 17/09/2026) -- um schema fixo do PRÓPRIO LibreChat,
    exigindo a propriedade "title" (`titleSchema`/`combinedSchema`, ambos
    com `required: ["title", ...]`). Mensagem de usuário ou resultado de
    ferramenta não tem como escrever em `response_format`/`tools` -- esses
    campos são montados pelo backend do frontend, nunca por conteúdo.
    Verificação tolerante de propósito (não presumo a forma exata do JSON
    Schema -- OpenAI json_schema aninha em `schema`, tool-calling aninha em
    `function.parameters`): procura "title" como CHAVE de propriedade em
    qualquer nível dentro de `response_format` ou `tools`, sem exigir
    caminho fixo. Onde esse formato divergir do suposto, este sinal
    simplesmente não dispara -- cai pro sinal 2, não perde proteção."""
    def _tem_prop_title(no) -> bool:
        if isinstance(no, dict):
            props = no.get("properties")
            if isinstance(props, dict) and "title" in props:
                return True
            return any(_tem_prop_title(v) for v in no.values())
        if isinstance(no, list):
            return any(_tem_prop_title(v) for v in no)
        return False
    return _tem_prop_title(payload.get("response_format")) or _tem_prop_title(payload.get("tools"))


def _e_chamada_utilitaria(payload: dict) -> bool:
    """True se o corpo é uma chamada de título/utilidade do frontend, nunca
    um turno de chat real da Seth. Três sinais, checados nesta ordem
    (achado 21/09/2026, MEMÓRIAS (495): 3º sinal cobre o Goose, não só o
    LibreChat):

    1. `_schema_pede_titulo` -- sinal de CANAL, não de conteúdo. Se bater,
       basta: nenhuma posição de mensagem importa, porque dado externo não
       consegue forjar `response_format`/`tools`.
    2. Sem (1): o `@librechat/agents` também tem um caminho SEM structured
       output (`createCompletionTitleRunnable`, mesmo arquivo, usado quando
       o provedor não suporta) -- prompt de completion puro, sem
       `response_format`. Aí vale a correção de (419)/MEMÓRIAS (431): a
       string-gatilho só conta se estiver na ÚLTIMA mensagem, com
       `role` user/system, E `len(messages) <= 2` -- a chamada de título é
       sempre one-shot (um H, no máximo um turno de usuário antes).
       `content` normalizado antes do teste de substring: lista de partes
       vira texto concatenado, `None`/outro tipo vira string vazia -- nunca
       `TypeError`, nunca falso negativo silencioso por testar `in` numa
       lista (achado de auditoria, 16/09/2026).
    3. `_e_chamada_titulo_goose` -- mesma ideia do (2), mas pro Goose: o
       texto-gatilho vem na PRIMEIRA mensagem (system), não na última, então
       tem checagem própria (varre todas as mensagens do payload).

    Residual CONHECIDO, não fechado por este desenho: colar um texto com a
    string-gatilho como a PRIMEIRA mensagem de uma conversa nova ainda bate
    a condição 2 (role user, len<=2) sem ser uma chamada de título de
    verdade -- mesma classe de risco que qualquer detector por conteúdo,
    registrado em vez de escondido (Doutrina de defesa proporcional,
    PROJETO.md: risco residual declarado é mais seguro que estado seguro
    não declarado)."""
    if _schema_pede_titulo(payload):
        return True
    if _e_chamada_titulo_goose(payload):
        return True

    msgs = payload.get("messages")
    if not isinstance(msgs, list) or not msgs or len(msgs) > 2:
        return False
    ultima = msgs[-1]
    if not isinstance(ultima, dict) or ultima.get("role") not in ("user", "system"):
        return False
    conteudo = ultima.get("content")
    if isinstance(conteudo, list):
        texto = " ".join(p.get("text", "") for p in conteudo if isinstance(p, dict))
    elif isinstance(conteudo, str):
        texto = conteudo
    else:
        texto = ""
    return any(s in texto for s in _SINAIS_TITULO)


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


# --- Rota pela cota por minuto do tier 0 (02/10/2026) ---------------------------
# Medido na Máquina (MEMÓRIAS (627)-(631)): os 3 combos da Seth começam no mesmo
# `groq/openai/gpt-oss-120b`, cujo plano grátis aceita 8.000 tokens POR MINUTO
# (TPM). Toda chamada do Agent já leva ~3,1 mil tokens de injeção deste gateway
# + ~3,1 mil do esquema das ferramentas MCP; a 2ª chamada de um turno com
# ferramenta estoura a cota quase sempre -> 429 -> cascata dentro do OmniRoute.
# O OmniRoute não deixa "pular" a posição 0 de um combo por pedido; então cada
# combo da Seth ganha um gêmeo `<rota>-sg` ("sem Groq": mesma ordem, sem o Groq),
# criado pela API do OmniRoute (config/combos-seth.json), e este gateway escolhe
# o gêmeo quando o pedido NÃO CABE na cota que sobra no minuto. Contabilidade:
# janela deslizante de 60 s com os tokens ESTIMADOS dos pedidos que o Groq de
# fato atendeu (X-Modelo-Real). Só regras, sem rede, sem inferência. Desligado
# por padrão (SETH_ROTA_COTA=1 liga): sem os combos -sg criados, ligar quebraria
# a Seth (404 do OmniRoute) -- por isso o liga é uma decisão de implantação.
_ROTA_COTA_LIGADA = os.environ.get("SETH_ROTA_COTA", "0") == "1"
_COTA_TPM = int(os.environ.get("SETH_COTA_TPM", "8000"))
_COTA_MARGEM = float(os.environ.get("SETH_COTA_MARGEM", "0.85"))   # folga do estimador
_CHARS_POR_TOKEN = float(os.environ.get("SETH_CHARS_POR_TOKEN", "3.0"))  # conservador p/ pt-BR
_SUFIXO_SEM_COTA = "-sg"
_ROTAS_COM_TIER0_COTADO = frozenset({"seth-rapido", "seth-livre", "seth-pesado"})
_MODELO_COTADO = "gpt-oss-120b"   # como aparece no "model" que o OmniRoute devolve
_JANELA_S = 60.0
_janela_cota: list[tuple[float, int]] = []
_janela_lock = threading.Lock()


def _estimar_tokens(payload: dict) -> int:
    """Estimativa conservadora (para mais) dos tokens de ENTRADA + o teto de saída
    pedido: chars de messages+tools / _CHARS_POR_TOKEN + max_tokens. Sem
    tokenizador de propósito -- é para decidir rota, não para cobrar."""
    try:
        base = len(json.dumps(payload.get("messages") or [], ensure_ascii=False))
        base += len(json.dumps(payload.get("tools") or [], ensure_ascii=False))
    except (TypeError, ValueError):
        return 10**9   # não deu para medir -> trata como "não cabe" (falha fechada)
    saida = payload.get("max_tokens") or payload.get("max_completion_tokens") or 0
    try:
        saida = int(saida)
    except (TypeError, ValueError):
        saida = 0
    return int(base / _CHARS_POR_TOKEN) + max(0, saida)


def _cota_usada(agora: float) -> int:
    with _janela_lock:
        _janela_cota[:] = [(t, n) for t, n in _janela_cota if agora - t < _JANELA_S]
        return sum(n for _, n in _janela_cota)


def _registrar_uso_cota(modelo_real: str | None, est: int, agora: float) -> None:
    """Conta na janela só o que o modelo cotado ATENDEU de fato (X-Modelo-Real)."""
    if modelo_real and _MODELO_COTADO in modelo_real and 0 < est < 10**9:
        with _janela_lock:
            _janela_cota.append((agora, est))


def _rota_pela_cota(rota: str, est: int, agora: float) -> str:
    """rota -> rota | rota-sg. Cabe no que sobra da cota do minuto -> mantém o
    tier 0 rápido; não cabe -> gêmeo sem ele. Desligado ou rota fora da lista
    -> intacto."""
    if not _ROTA_COTA_LIGADA or rota not in _ROTAS_COM_TIER0_COTADO:
        return rota
    if est + _cota_usada(agora) <= int(_COTA_TPM * _COTA_MARGEM):
        return rota
    return rota + _SUFIXO_SEM_COTA


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
    _est = 0     # tokens estimados do pedido hidratado (rota pela cota)

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        self._passar(b"", "GET")

    def do_HEAD(self):
        self._passar(b"", "HEAD")

    def do_POST(self):
        # estado por REQUISIÇÃO: com keep-alive o mesmo handler atende vários
        # pedidos, e uma rota/estimativa velha vazaria pro header do seguinte
        self._rota, self._est = "", 0
        corpo = ler_corpo_limitado(self)
        if corpo is None:
            return
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
                payload = _injeta(payload)
                if self._rota:
                    # cota por minuto do tier 0: decidida sobre o pedido JÁ hidratado,
                    # que é o que de fato chega ao provedor
                    self._est = _estimar_tokens(payload)
                    self._rota = _rota_pela_cota(self._rota, self._est, time.monotonic())
                    payload["model"] = self._rota
                corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._passar(corpo, "POST")

    # Nome real do modelo que respondeu, pela Máquina (campo "model" que o
    # OmniRoute devolve -- "openai/gpt-oss-120b", nunca o alias de roteamento
    # "seth-livre"/"seth-rapido"). Vira header HTTP novo, nunca reescreve o
    # corpo -- proxy.py (sanitizador) é passthrough byte a byte de propósito,
    # e SSE reescrito no meio do conteúdo arrisca corromper o stream que o
    # LibreChat acumula (mesma classe de risco de MEMÓRIAS (415)). Header é
    # aditivo: nada no stack lê "X-Modelo-Real" hoje, então nada quebra
    # (conferido: grep em redesign/router|mcp|librechat não achou consumidor
    # do campo "model" da resposta). Fato da Máquina, não autorrelato do
    # modelo (REGRAS, Os 3 papéis) -- pedido da Seth, MEMÓRIAS (612)/turno
    # seguinte, risco assumido pelo Humano por escrito, sem teste prévio em
    # worktree (Portão das três perguntas respondido direto nesta sessão).
    _RE_MODELO = re.compile(rb'"model"\s*:\s*"([^"]+)"')
    _PEEK_MAX_PEDACOS = 8  # ~64 KiB -- cobre a janela de keepalive do OmniRoute antes do provedor responder

    @classmethod
    def _modelo_de_bytes(cls, dado: bytes) -> str | None:
        """Primeiro campo "model" em `dado`, ou None se ausente ou só
        "keepalive" (sentinela do OmniRoute, nunca o modelo real)."""
        for m in cls._RE_MODELO.finditer(dado):
            nome = m.group(1).decode("utf-8", "replace")
            if nome != "keepalive":
                return nome
        return None

    def _passar(self, corpo: bytes, metodo: str):
        url = UPSTREAM + self.path
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in _HOP_BY_HOP}
        headers["X-Agata-Token"] = _token_interno()
        req = urllib.request.Request(url, data=corpo or None, method=metodo, headers=headers)
        try:
            up = urllib.request.urlopen(req, timeout=180)
        except urllib.error.HTTPError as e:
            up = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            return self._erro(502, f"upstream ({UPSTREAM}) inacessível: {e}. "
                                   "Suba o sanitizador: systemctl --user start omniroute-sanitizer omniroute")
        sse = "text/event-stream" in (up.headers.get("Content-Type") or "").lower()
        modelo_real = None
        buf_pre = b""
        try:
            if sse:
                # Espia os primeiros pedaços (sem enviar nada ao cliente ainda --
                # headers não foram mandados) até achar o "model" real ou esgotar
                # o limite; o que foi lido entra no stream normal depois, intacto.
                for _ in range(self._PEEK_MAX_PEDACOS):
                    pedaco = up.read(8192)
                    if not pedaco:
                        break
                    buf_pre += pedaco
                    modelo_real = self._modelo_de_bytes(buf_pre)
                    if modelo_real:
                        break
            else:
                buf_pre = up.read()
                modelo_real = self._modelo_de_bytes(buf_pre)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
            up.close()
            return
        self.send_response(up.status)
        for k, v in up.headers.items():
            if k.lower() not in _HOP_BY_HOP:
                self.send_header(k, v)
        if self._rota:
            self.send_header("X-Seth-Rota", self._rota)
        if self._est:
            self.send_header("X-Seth-Est-Tokens", str(self._est))
        if modelo_real:
            self.send_header("X-Modelo-Real", modelo_real)
            _lembrar_modelo_real(modelo_real)
            if 200 <= up.status < 300:
                _registrar_uso_cota(modelo_real, self._est, time.monotonic())
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        try:
            if sse:
                self._stream_sse_filtrado(up, buf_pre)
            else:
                for i in range(0, len(buf_pre), 8192):
                    pedaco = buf_pre[i:i + 8192]
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

    def _stream_sse_filtrado(self, up, buf: bytes = b""):
        """Repassa o SSE do upstream, trocando os chunks-sentinela de keepalive
        do OmniRoute por comentários SSE. Line-buffered: um read do upstream pode
        cair no meio de uma linha. `buf` = bytes já lidos de `up` antes desta
        chamada (espreitada do X-Modelo-Real em _passar) -- processados primeiro,
        como se tivessem acabado de chegar; nada se perde, nada se duplica."""
        # As linhas completas JÁ presentes em `buf` (vindas da espiada) saem
        # ANTES de ler mais. Regressão de 9dfd7da (614): sem isto, quando a
        # espiada lia a resposta inteira até o EOF (resposta pequena -- o caso de
        # quase toda chamada de ferramenta), o primeiro read() voltava vazio e o
        # buffer INTEIRO caía no tratamento de "última linha parcial": começando
        # pelo keepalive do OmniRoute, virava um único ": ka" e o conteúdo real
        # sumia -> stream sem nenhum chunk -> crash "'tool_calls' in undefined"
        # no LibreChat. Reproduzido no lab: 5 bytes de saída para 471 de entrada.
        buf = self._escrever_linhas_completas(buf)
        while True:
            pedaco = up.read(8192)
            if not pedaco:
                break
            buf = self._escrever_linhas_completas(buf + pedaco)
        if buf:
            saida = self._filtrar_linha_sse(buf)
            self.wfile.write(f"{len(saida):X}\r\n".encode())
            self.wfile.write(saida)
            self.wfile.write(b"\r\n")

    def _escrever_linhas_completas(self, buf: bytes) -> bytes:
        """Escreve (filtradas, em chunk HTTP) todas as linhas COMPLETAS de `buf`;
        devolve o resto -- no máximo uma linha parcial, sem '\\n'."""
        while b"\n" in buf:
            linha, buf = buf.split(b"\n", 1)
            saida = self._filtrar_linha_sse(linha + b"\n")
            self.wfile.write(f"{len(saida):X}\r\n".encode())
            self.wfile.write(saida)
            self.wfile.write(b"\r\n")
        return buf

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
    srv = ServidorConcorrenciaLimitada((host, port), _Handler)
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
    modelo_resposta = None  # teste 10/11 liga isto pra simular "model" na resposta real

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        type(self).ultimo_corpo = self.rfile.read(n)
        resp = {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
        if type(self).modelo_resposta:
            resp["model"] = type(self).modelo_resposta
        corpo = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def _selftest() -> int:
    global UPSTREAM, MODELO_REAL_PATH
    up_port, gw_port = _porta_livre(), _porta_livre()
    UPSTREAM = f"http://127.0.0.1:{up_port}"
    import tempfile
    MODELO_REAL_PATH = Path(tempfile.mkdtemp()) / "modelo-real.txt"  # isolado do arquivo real
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

    # 3b. chamada de TÍTULO do Goose (payload real capturado com proxy, MEMÓRIAS (495)) ->
    # repassada crua, SEM system hidratado. Gatilho na PRIMEIRA mensagem (system), não na
    # última -- é exatamente o caso que o sinal 2 (só olha msgs[-1]) não cobre.
    body3b = json.dumps({"model": "seth-codigo", "messages": [
        {"role": "system", "content": "Generate a short title (four words or less) that "
         "describes the topic of the user's messages. \nReply with only the title, "
         "nothing else. Do not show your reasoning."},
        {"role": "user", "content": "---BEGIN USER MESSAGES---\noi\n---END USER "
         "MESSAGES---\n\nGenerate a short title for the above messages."}],
        "stream": True, "stream_options": {"include_usage": True}}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body3b, headers={"Content-Type": "application/json"}), timeout=10).read()
    m3b = json.loads(_Dummy.ultimo_corpo)["messages"]
    ok3b = len(m3b) == 2 and m3b[0]["role"] == "system" and MARCADOR not in m3b[0]["content"]
    print(f"{'PASS' if ok3b else 'FALHA'}  chamada de título do Goose -> repassada sem "
          f"hidratar (messages={len(m3b)})")
    falhas += 0 if ok3b else 1

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

    # 10. identificação de modelo na fala (MEMÓRIAS (621)): resposta com "model"
    # real -> grava no sidecar (isolado em tmp, nunca o arquivo de produção);
    # o PRÓXIMO turno já hidratado reinjeta MODELO-REAL-TURNO-ANTERIOR.
    ok10a = _modelo_real_anterior() is None
    print(f"{'PASS' if ok10a else 'FALHA'}  modelo real: sem medição prévia -> None")
    falhas += 0 if ok10a else 1

    _Dummy.modelo_resposta = "teste/modelo-selftest"
    body10 = json.dumps({"model": "seth", "messages": [
        {"role": "system", "content": f"{MARCADOR}\nx"},
        {"role": "user", "content": "oi"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body10, headers={"Content-Type": "application/json"}), timeout=10).read()
    ok10b = _modelo_real_anterior() == "teste/modelo-selftest"
    print(f"{'PASS' if ok10b else 'FALHA'}  modelo real: resposta com \"model\" -> sidecar gravado "
          f"(lido: {_modelo_real_anterior()!r})")
    falhas += 0 if ok10b else 1

    urllib.request.urlopen(urllib.request.Request(
        base, data=body10, headers={"Content-Type": "application/json"}), timeout=10).read()
    m10 = json.loads(_Dummy.ultimo_corpo)["messages"]
    est10 = next((x["content"] for x in m10 if isinstance(x.get("content"), str)
                  and MARCADOR_ESTADO in x["content"]), "")
    ok10c = "MODELO-REAL-TURNO-ANTERIOR: teste/modelo-selftest" in est10
    print(f"{'PASS' if ok10c else 'FALHA'}  modelo real: turno seguinte cita o nome, rotulado "
          f"como turno anterior ({'achou' if ok10c else 'não achou'} a linha)")
    falhas += 0 if ok10c else 1
    _Dummy.modelo_resposta = None

    # 12. regressão de 9dfd7da (614): a espiada do X-Modelo-Real leu a resposta
    # inteira (pequena, começando pelo keepalive) antes do laço de stream ->
    # o conteúdo real NÃO pode sumir; tem de sair linha a linha, keepalive -> ": ka".
    import io
    ka12 = (b'data: {"id":"chatcmpl-keepalive","model":"keepalive","choices":[{"index":0,'
            b'"delta":{},"finish_reason":null}]}\n\n')
    real12 = (b'data: {"id":"chatcmpl-msg_1","model":"m","choices":[{"index":0,"delta":'
              b'{"tool_calls":[{"index":0,"id":"c1","function":{"name":"f","arguments":"{}"}}]},'
              b'"finish_reason":"tool_calls"}]}\n\ndata: [DONE]\n\n')

    class _UpVazio:  # a espiada já leu tudo: o próximo read() é EOF
        def read(self, n=-1):
            return b""

    h12 = _Handler.__new__(_Handler)
    h12.wfile = io.BytesIO()
    h12._stream_sse_filtrado(_UpVazio(), ka12 + real12)
    saida12 = h12.wfile.getvalue()
    ok12 = (b"tool_calls" in saida12 and b"[DONE]" in saida12 and b": ka" in saida12
            and b"chatcmpl-keepalive" not in saida12)
    print(f"{'PASS' if ok12 else 'FALHA'}  SSE espiado inteiro: conteúdo real preservado, "
          f"keepalive virou comentário ({len(saida12)} bytes de saída)")
    falhas += 0 if ok12 else 1
    # 11. rota pela cota por minuto do tier 0 (funções puras, relógio injetado)
    global _ROTA_COTA_LIGADA
    ligada_antes = _ROTA_COTA_LIGADA
    teto = int(_COTA_TPM * _COTA_MARGEM)
    _janela_cota.clear()
    _ROTA_COTA_LIGADA = False
    c11a = _rota_pela_cota("seth-livre", 10**6, 0.0) == "seth-livre"
    _ROTA_COTA_LIGADA = True
    c11b = _rota_pela_cota("seth-livre", teto // 2, 0.0) == "seth-livre"
    c11c = _rota_pela_cota("seth-pesado", teto + 1, 0.0) == "seth-pesado-sg"
    _registrar_uso_cota("openai/gpt-oss-120b", teto // 2 + 10, 1.0)
    c11d = _rota_pela_cota("seth-livre", teto // 2, 2.0) == "seth-livre-sg"   # soma passa do teto
    _registrar_uso_cota("glm-4.7-flash", 10**4, 3.0)                          # outro modelo não conta
    c11e = _cota_usada(3.0) == teto // 2 + 10
    c11f = _rota_pela_cota("seth-livre", teto // 2, 1.0 + _JANELA_S + 0.1) == "seth-livre"  # janela expirou
    c11g = _rota_pela_cota("seth-codigo", 10**6, 0.0) == "seth-codigo"      # fora da lista: intacto
    est = _estimar_tokens({"messages": [{"role": "user", "content": "x" * 3000}], "max_tokens": 500})
    c11h = est >= int(3000 / _CHARS_POR_TOKEN) + 500                         # conservador: nunca abaixo
    c11i = _estimar_tokens({"messages": [{"x": object()}]}) == 10**9          # não mede -> não cabe
    # 11j. ponta a ponta pelo gateway real: pedido grande do Agent sai como -sg,
    # com a estimativa no header (o liga ainda ligado aqui)
    corpo11 = json.dumps({"model": _ROTA_BASE, "messages": [
        {"role": "user", "content": "y" * (teto * 4)}]}).encode()
    r11 = urllib.request.urlopen(urllib.request.Request(
        base, data=corpo11, headers={"Content-Type": "application/json"}), timeout=10)
    r11.read()
    modelo_enviado = json.loads(_Dummy.ultimo_corpo).get("model")
    c11j = (modelo_enviado == "seth-pesado-sg" and
            int(r11.headers.get("X-Seth-Est-Tokens") or 0) > teto)
    _ROTA_COTA_LIGADA = ligada_antes
    _janela_cota.clear()
    for n, ok, desc in [("11a", c11a, "desligada -> rota intacta mesmo com pedido enorme"),
                        ("11b", c11b, "ligada, cabe na cota -> mantém o tier 0"),
                        ("11c", c11c, "ligada, pedido sozinho passa do teto -> seth-pesado-sg"),
                        ("11d", c11d, "uso do minuto + pedido passa do teto -> seth-livre-sg"),
                        ("11e", c11e, "só o modelo cotado entra na janela"),
                        ("11f", c11f, "janela de 60 s expira -> volta ao tier 0"),
                        ("11g", c11g, "rota fora da lista (seth-codigo) -> intacta"),
                        ("11h", c11h, f"estimador conservador ({est} tokens p/ 3000 chars + 500)"),
                        ("11i", c11i, "payload que não serializa -> trata como não cabe"),
                        ("11j", c11j, f"ponta a ponta: pedido grande sai como {modelo_enviado!r} + X-Seth-Est-Tokens")]:
        print(f"{'PASS' if ok else 'FALHA'}  cota {n}: {desc}")
        falhas += 0 if ok else 1

    up.shutdown()
    gw.shutdown()
    print(f"\n{'SELFTEST OK' if not falhas else f'SELFTEST FALHOU ({falhas})'}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        raise SystemExit(_selftest())
    servir()
