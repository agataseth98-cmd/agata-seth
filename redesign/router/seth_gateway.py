#!/usr/bin/env python3
"""seth_gateway.py — reidrata a Seth antes do OmniRoute.

Fica entre o frontend (Open WebUI, Goose, curl) e o proxy de sanitização.
Escuta em 127.0.0.1:20126. Em cada POST /v1/chat/completions, se ainda não
houver uma mensagem de sistema hidratada, **antepõe** o conteúdo de
`.hidrata-seth.md` (REGRAS + PROJETO + janela de MEMÓRIAS, silo seth) como
mensagem `system` e repassa para :20127 (que sanitiza segredo) -> OmniRoute.

Assim qualquer frontend que apontar para :20126 fala com a Seth hidratada,
sem o Hermes. GET (/v1/models, /health) e streaming passam direto.

Só stdlib. Não instala nada. Lê UMA coisa de ~/.config/agata/token-interno desde o
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
    SETH_REFAZER         padrão LIGADO (23/11/2026): a resposta é conferida e refeita antes de sair; 0 desliga sempre;
                         1 liga sempre. SETH_ROTEADOR=capacidade:N com N válido sorteia N% dos pedidos (canário).
    SETH_REFAZER_MAX     novas tentativas por resposta (default 2)
    SETH_REFAZER_SEG     teto, em segundos, para as novas tentativas (default 180)
    SETH_REFAZER_1A_SEG  prazo para a 1ª resposta chegar inteira (default 180); passou, segue sem refazer
    SETH_REFAZER_BYTES   teto de bytes por coleta de resposta (default 4 MiB); passou, idem
    SETH_ESCOLHA_CAPACIDADE  padrão ligado (23/11/2026): o modelo concreto que o registro recomenda para o tipo, com nota
                         e amostra suficientes; 0 volta ao combo de antes
    AGATA_CAPIVARA_USO   log de uso da Capivara (padrão ~/.local/share/agata/capivara/uso.jsonl; sem texto)
"""
from __future__ import annotations

import hashlib
import http.client
import io
import json
import queue
import os
import random
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
# ('Seth no gateway', em PROTOCOLOS.md). Fora do repo (estado efêmero, mesmo padrão de
# ~/.cache/agata/ls-remote-main). Global, não por conversa -- se houver duas
# conversas simultâneas, uma pode herdar o nome da outra por 1 turno; risco
# aceito (Portão das três perguntas, MEMÓRIAS (620)/(621)): sempre visível
# (o Humano vê o nome errado na hora), nunca silencioso.
MODELO_REAL_PATH = Path(os.environ.get(
    "SETH_MODELO_REAL_PATH", str(Path.home() / ".cache" / "agata" / "seth-modelo-real-ultimo.txt")))

def _token_interno() -> str:
    """Token interno (X-Agata-Token) que este processo anexa em toda chamada ao
    sanitizador. Vem de `scripts/token_interno.py`: arquivo próprio
    (~/.config/agata/token-interno, 0600), lido uma vez por processo. NUNCA abre
    o .env -- antes abria o arquivo inteiro a cada pedido, e foi por aí que as
    chaves vazaram (MEMÓRIAS (629)-(631)). Nunca loga o valor."""
    _scripts = str(Path(__file__).resolve().parents[2] / "scripts")
    if _scripts not in sys.path:
        sys.path.insert(0, _scripts)
    import token_interno  # noqa: E402  (scripts/token_interno.py)
    return token_interno.ler()
MODO = os.environ.get("SETH_HIDRATA_MODO", "compacto").lower()
REPO = Path(os.environ.get("SETH_REPO") or Path(__file__).resolve().parents[2])   # raiz do checkout (CI e casa)
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
# Fonte única (sincronia-12-11, decisão do Humano, cache do Conselho (521)): o texto próprio da Seth NÃO é
# cópia no código. Fica em PROTOCOLOS.md, entre os marcadores SETH-GATEWAY e SETH-PUBLICA, e é lido a cada
# hidratação. O AGENTS.md entra inteiro na hidratação compacta. Quem muda a doutrina muda o canon (proposta
# P-8); o código não tem regra. Sem a seção, a Seth recebe `lacuna` (nunca silêncio) e a rota pública não responde.
_PROTOCOLOS_PATH = Path(__file__).resolve().parents[2] / "PROTOCOLOS.md"
_SECOES_CANON = {
    "seth": ("<!-- SETH-GATEWAY:INICIO -->", "<!-- SETH-GATEWAY:FIM -->"),
    "publica": ("<!-- SETH-PUBLICA:INICIO -->", "<!-- SETH-PUBLICA:FIM -->"),
}
_CACHE_SECAO: dict = {}


class DoutrinaIndisponivel(RuntimeError):
    """A seção de doutrina não pôde ser lida: a rota pública não responde sem ela (falha fechada)."""


def _ler_secao(nome: str) -> tuple[bool, str]:
    """(ok, texto): a seção de PROTOCOLOS.md sem os marcadores. ok=False se o arquivo não pôde ser lido,
    se os marcadores faltam ou estão fora de ordem. Cache por mtime."""
    ini, fim = _SECOES_CANON[nome]
    try:
        mtime = _PROTOCOLOS_PATH.stat().st_mtime
    except OSError:
        return False, ""
    cache = _CACHE_SECAO.get(nome)
    if cache and cache[0] == mtime:
        return cache[1], cache[2]
    try:
        bruto = _PROTOCOLOS_PATH.read_text(encoding="utf-8")
    except OSError:
        return False, ""
    i, f = bruto.find(ini), bruto.find(fim)
    ok = i >= 0 and f > i
    texto = bruto[i + len(ini):f].strip() if ok else ""
    _CACHE_SECAO[nome] = (mtime, ok, texto)
    return ok, texto


def _doutrina_seth() -> str:
    """Texto que o gateway injeta na hidratação. Sem a seção, diz lacuna: nunca cai em silêncio nem em cópia de reserva."""
    ok, texto = _ler_secao("seth")
    if ok:
        return texto + "\n\n"
    return ("**Protocolo da Seth:** lacuna: a seção 'Seth no gateway' de PROTOCOLOS.md não pôde ser lida "
            "(arquivo ausente ou marcadores SETH-GATEWAY quebrados). Não afirme regra de gateway que não medir.\n\n")


def _doutrina_publica() -> str:
    """Instrução da rota pública (sem ferramentas). Sem a seção, a rota não responde: falha fechada."""
    ok, texto = _ler_secao("publica")
    if not ok:
        raise DoutrinaIndisponivel("seção SETH-PUBLICA de PROTOCOLOS.md não pôde ser lida; rota pública fechada")
    return texto


def _hash_fonte() -> str:
    """Marcador amarrado ao texto que o gateway injeta (seção SETH-GATEWAY + AGENTS.md). Muda quando o canon
    muda, então uma conversa com o marcador velho volta a ser hidratada depois do redeploy."""
    _, secao = _ler_secao("seth")
    try:
        agents = (Path(__file__).resolve().parents[2] / "AGENTS.md").read_text(encoding="utf-8")
    except OSError:
        agents = ""
    return hashlib.sha256((secao + "\n--AGENTS--\n" + agents).encode("utf-8")).hexdigest()[:8]


_HASH_DOUTRINA = _hash_fonte()
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

_RE_T_CABECALHO = re.compile(
    r"^\s*\**\s*agata(?:-seth)?\s*·.*?\bt=(\d+)\b", re.I)


def _max_turno_em_mensagens(msgs: list) -> int:
    """Maior t= nos cabeçalhos injetados pela Máquina nas respostas anteriores.

    Quando o frontend trunca mensagens antigas, a contagem por pares
    usuário/assistente para de crescer. Este valor preserva a marca d'água
    alta e garante que o próximo t= é pelo menos anterior + 1."""
    maximo = 0
    for m in msgs:
        if not (isinstance(m, dict) and m.get("role") == "assistant"):
            continue
        c = m.get("content")
        if isinstance(c, str):
            match = _RE_T_CABECALHO.match(c[:400])
            if match:
                maximo = max(maximo, int(match.group(1)))
    return maximo


_ESTADO_MEMO: dict = {"t": 0.0, "texto": ""}


def _estado() -> str:
    """Saída curta de scripts/estado_para_eco.sh (HEAD, topo de MEMÓRIAS, sync).
    Best-effort — se falhar, devolve string vazia. (705) Memória de 10 s: a hidratação
    e o cabeçalho da Máquina, no mesmo pedido, usam a mesma medição."""
    if time.monotonic() - _ESTADO_MEMO["t"] < 10 and _ESTADO_MEMO["texto"]:
        return _ESTADO_MEMO["texto"]
    texto = _estado_medir()
    _ESTADO_MEMO.update(t=time.monotonic(), texto=texto)
    return texto


def _estado_medir() -> str:
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
        return "\n".join(x for x in (linhas + [_linha_propostas(), _linha_saude()]) if x)
    except Exception:
        return ""


def _linha_saude() -> str:
    """(lote 5, A1) Saúde datada da Máquina numa linha do estado da Seth. Desligada por padrão (SETH_SAUDE_NO_ESTADO=1).
    Sem fotografia, diz 'não medida'; fotografia velha (passou de revalidar_ate) diz 'velha'. Nada é estimado."""
    if os.environ.get("SETH_SAUDE_NO_ESTADO") != "1":
        return ""
    try:
        for sub in ("corpo", "nova_versao"):
            p = str(REPO / "redesign" / sub)
            if p not in sys.path:
                sys.path.insert(0, p)
        import fotografar  # noqa: E402
        import saude  # noqa: E402
        from datetime import datetime
        f = fotografar.ultima()
        if not f:
            return "SAUDE-MAQUINA: não medida (sem fotografia)"
        estado = saude.classificar(f).get("estado", "não medido")
        velha = datetime.now().astimezone().isoformat() > str(f.get("revalidar_ate") or "")
        return f"SAUDE-MAQUINA: {estado} · {'velha' if velha else 'medida ' + str(f.get('quando', ''))[:16]}"
    except Exception:  # noqa: BLE001 — nunca derruba o estado
        return ""


def _linha_propostas(pasta: Path | None = None) -> str:
    """(695) Nomes das propostas abertas (`.diff` sem `APROVADO-`) -- a Seth afirmava
    pendente o que já estava em propostas/aplicadas/, lendo uma entrada antiga.
    Proposta listada em `SUBSTITUIDAS.txt` (primeira coluna) não é pendência: vai à parte."""
    pasta = pasta or (REPO / "propostas")
    substituidas = set()
    try:
        for linha in (pasta / "SUBSTITUIDAS.txt").read_text(encoding="utf-8").splitlines():
            if linha.strip() and not linha.lstrip().startswith("#"):
                substituidas.add(linha.split("|", 1)[0].strip())
    except OSError:
        pass
    diffs = [d.stem for d in pasta.glob("*.diff") if d.stem not in substituidas]
    abertas = sorted(n for n in diffs if not (pasta / f"APROVADO-{n}").exists())
    assinadas = sorted(n for n in diffs if (pasta / f"APROVADO-{n}").exists())
    descartadas = sorted(d.stem for d in pasta.glob("*.diff") if d.stem in substituidas)
    return ("PROPOSTAS-PENDENTES: " + (", ".join(abertas) if abertas else "nenhuma")
            + (f" · assinadas, falta aplicar: {', '.join(assinadas)}" if assinadas else "")
            + (f" · substituídas, NÃO pendentes: {', '.join(descartadas)}" if descartadas else "")
            + " · o que está em propostas/aplicadas/ NÃO está pendente")


# Pacote mecânico (12/11/2026, decisão do Humano: todo modelo age segundo o mesmo sistema): as diretrizes
# vêm de AGENTS.md, lido pela Máquina a cada alteração do arquivo. É ponteiro, não cópia: o texto de
# AGENTS.md entra inteiro na hidratação compacta. O texto próprio da Seth está em PROTOCOLOS.md, seção 'Seth no gateway' (sincronia-12-11).
_AGENTS_PATH = Path(__file__).resolve().parents[2] / "AGENTS.md"
_CACHE_AGENTS: dict = {"mtime": None, "texto": ""}


def _diretrizes_agents() -> str:
    try:
        st = _AGENTS_PATH.stat()
        if _CACHE_AGENTS["mtime"] != st.st_mtime:
            _CACHE_AGENTS["texto"] = _AGENTS_PATH.read_text(encoding="utf-8")
            _CACHE_AGENTS["mtime"] = st.st_mtime
    except OSError:
        return ("**Diretrizes (AGENTS.md):** lacuna: AGENTS.md não pôde ser lido nesta Máquina; "
                "não afirme diretriz que não medir.\n")
    return "**Diretrizes de todo modelo (AGENTS.md, lido pela Máquina):**\n" + _CACHE_AGENTS["texto"] + "\n"


def doutrina_montada() -> str:
    """O texto de doutrina que a rota interna põe antes do modelo (modo compacto): a seção SETH-GATEWAY do
    PROTOCOLOS.md e o AGENTS.md inteiro, na ordem de _hidratacao. Sem estado e sem rede. Em modo full, o arquivo
    SETH_HIDRATA. É o texto que o P-23 confere (config/portas-de-entrada.txt, leitura 'doutrina'): o que o
    gateway monta, não o conteúdo de um arquivo do próprio gateway (23/11/2026, caminho-visao-23-11)."""
    if MODO == "compacto":
        return _doutrina_seth() + _diretrizes_agents()
    try:
        return HIDRATA_PATH.read_text(encoding="utf-8")
    except OSError:
        return f"(hidratação indisponível: {HIDRATA_PATH} não pôde ser lido)"


# (07/11/2026, núcleo de desenvolvimento, D2) ponteiro de uma linha para o guia universal (Ma'at), no canal de
# estado de _injeta, só nas faixas internas (a faixa pública não passa por _injeta). Fica FORA da doutrina (seção SETH-GATEWAY do
# PROTOCOLOS.md), para não mudar o marcador. SETH_PROCESSO_HIDRATA=0 desliga.
_LINHA_PROCESSO = ("PROCESSO: regras de lote e fluxo em .agents/skills/agata-fluxo/SKILL.md (Ma'at); "
                   "leia antes de propor ou aplicar mudança.")


def _linha_processo() -> str:
    if os.environ.get("SETH_PROCESSO_HIDRATA") == "0":
        return ""
    return _LINHA_PROCESSO


def _hidratacao(extra: str = "") -> str:
    """Modo compacto (default): cabeçalho + estado atual. Modo full: o arquivo inteiro.
    `extra`: linhas do turno anterior (ex.: AUDITORIA-TURNO-ANTERIOR) que vão no estado."""
    if MODO == "compacto":
        est = _estado()
        # Regra 1.1: campo medível não pode sumir em silêncio quando a
        # medição falha -- antes, `est` vazio só omitia o bloco inteiro sem
        # dizer que algo quebrou (achado 04/09/2026, Camada C).
        if est:
            corpo = est + (f"\n{extra}" if extra else "")  # (705) modelo: cabeçalho da Máquina
            bloco_estado = f"**Estado agora (fatos da Máquina):**\n{corpo}\n"
        else:
            bloco_estado = ("**Estado agora:** `lacuna: estado_para_eco.sh falhou ou não rodou "
                             "(sem shell/Máquina daqui?) — não afirme HEAD/sync sem medir.`\n"
                             + (f"{extra}\n" if extra else ""))
        return f"{MARCADOR}\n{doutrina_montada()}{bloco_estado}"
    try:
        st = HIDRATA_PATH.stat()
        if _CACHE["mtime"] != st.st_mtime:
            _CACHE["texto"] = HIDRATA_PATH.read_text(encoding="utf-8")
            _CACHE["mtime"] = st.st_mtime
    except OSError:
        return f"{MARCADOR}\n(hidratação indisponível: {HIDRATA_PATH} não pôde ser lido)"
    return f"{MARCADOR}\n" + _CACHE["texto"]


def _bloco_estado_atual(extra: str = "") -> str:
    """Bloco de estado FRESCO pra reinjetar em turno já hidratado (MEMÓRIAS (417)).
    String vazia se estado_para_eco.sh não deu saída — nesse caso não reinjeta
    nada (a Seth fica com o bloco velho do 1º turno, honesto via IDADE-HIDRATACAO)."""
    est = _estado()
    if not est:
        return ""
    corpo = est + (f"\n{extra}" if extra else "")  # (705) modelo: cabeçalho da Máquina
    return (f"{MARCADOR_ESTADO}\n**Estado agora (Máquina, medido neste turno — "
            f"vale MAIS que qualquer bloco de estado anterior nesta conversa; "
            f"o cabeçalho é escrito pela Máquina):**\n{corpo}\n")


def _retirar_ponteiro_processo_antigo(msgs: list) -> list:
    """Remove o PROCESSO anterior da mensagem hidratada antes de atualizar o estado.

    O ponteiro é estado de turno, não doutrina. Ao refrescar uma conversa já
    hidratada, ele precisa acompanhar SETH_PROCESSO_HIDRATA e não acumular.
    """
    saida = []
    for msg in msgs:
        if (isinstance(msg, dict) and msg.get("role") == "system"
                and isinstance(msg.get("content"), str) and MARCADOR in msg["content"]):
            conteudo = re.sub(r"(?m)^PROCESSO:[^\r\n]*(?:\r?\n|$)", "", msg["content"])
            if conteudo != msg["content"]:
                msg = {**msg, "content": conteudo}
        saida.append(msg)
    return saida


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
    A doutrina ('Seth no gateway', PROTOCOLOS.md) instrui a Seth a rotular isto como medição do
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
# LibreChat: detectado só pelo schema (`_schema_pede_titulo`), nunca por texto.
# `librechat.yaml` fixa `titleMethod: "structured"` no endpoint Seth; sem isso o
# `generateTitle` do @librechat/agents usa "completion" por padrão (run.cjs,
# conferido no container em 13/10/2026) e o título só seria reconhecível por
# substring -- que um usuário consegue colar. Se o título algum dia chegar sem
# schema, ele é HIDRATADO: degrada (chamada maior), nunca rouba hidratação de turno real.

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
# O texto-gatilho vem numa mensagem `system` montada pelo próprio Goose. Só
# `role == "system"` conta: conteúdo de usuário (inclusive colado) nunca dispara.
_SINAIS_TITULO_GOOSE = (
    "Generate a short title (four words or less) that describes the topic "
    "of the user's messages",
)


def _e_chamada_titulo_goose(payload: dict) -> bool:
    """Sinal 2 de `_e_chamada_utilitaria`: chamada de nomear-sessão do Goose.
    Só mensagens `system` (montadas pelo cliente) e só com `len(messages) <= 2`
    -- é sempre one-shot."""
    msgs = payload.get("messages")
    if not isinstance(msgs, list) or not msgs or len(msgs) > 2:
        return False
    for m in msgs:
        if not isinstance(m, dict) or m.get("role") != "system":
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
    um turno de chat real da Seth. Dois sinais, nenhum lê conteúdo de usuário:

    1. `_schema_pede_titulo` -- LibreChat (`titleMethod: "structured"`): sinal
       de CANAL; dado externo não forja `response_format`/`tools`.
    2. `_e_chamada_titulo_goose` -- Goose: texto-gatilho só em `role: system`.

    Fecha o residual de (419)/(431)/(433): o antigo sinal por substring na
    última mensagem de usuário saiu em 13/10/2026 -- colar a frase-gatilho
    não tira mais a hidratação de um turno real."""
    return _schema_pede_titulo(payload) or _e_chamada_titulo_goose(payload)


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
_ALIAS_PUBLICO = "seth-public"
# Modelos que rodam nesta Máquina (sem egresso): ollama-local/ e os llama-server (llama-cpp/*, llamacpp-*).
# llama-cpp/ entrou em 18/11/2026: antes caía no ramo externo e exigia classificação pública.
# Mesma lista de scripts/benchmark_roteamento.py (LOCAIS); o teste de sincronia está em
# scripts/testar_benchmark_roteamento.py.
_ROTAS_LOCAIS = ("ollama-local/", "llamacpp-", "llama-cpp/", "local/")


# Prazo da rota local (1º byte e cada leitura) = maior tempo de resposta COM SUCESSO medido para o modelo roteado
# + 30 s de folga (ordem do Humano, 18/11/2026). O modelo roteado é o qwen3-30b-a3b-64k: maior sucesso medido
# 70,5 s no benchmark 20261118-144845 (competicao-locais, 18/11/2026) -> 100,5 s. Muda com SETH_ROTA_LOCAL_MS.
_ROTA_LOCAL_MS_PADRAO = 100500
# Prazo da rota de nuvem por tipo (19/11/2026): p50 medido 1,6 a 6,5 s na prova NVIDIA; o pior caso não foi medido,
# então 30 s (SETH_ROTA_NUVEM_MS). Passou, cai na fila de sempre.
_ROTA_NUVEM_MS_PADRAO = 30000


def _rota_nuvem_seg() -> float:
    try:
        return max(1.0, float(os.environ.get("SETH_ROTA_NUVEM_MS", str(_ROTA_NUVEM_MS_PADRAO))) / 1000.0)
    except ValueError:
        return _ROTA_NUVEM_MS_PADRAO / 1000.0


def _rota_local_seg() -> float:
    """Prazo da rota local em segundos (SETH_ROTA_LOCAL_MS em milissegundos, padrão 100500). Passou, cai na fila
    de sempre: o pior caso fica 100,5 + 180 s, não 180 + 180."""
    try:
        return max(1.0, float(os.environ.get("SETH_ROTA_LOCAL_MS", str(_ROTA_LOCAL_MS_PADRAO))) / 1000.0)
    except ValueError:
        return _ROTA_LOCAL_MS_PADRAO / 1000.0


class DadosExternosSemClassificacao(ValueError):
    pass


def _politica_dados_externos(payload: dict, classification: str | None = None) -> dict:
    """Fail closed before the proxy: cloud payloads need the user's public-only lane."""
    model = str(payload.get("model") or "")
    if model == _ALIAS_PUBLICO:
        payload["model"] = _ROTA_BASE
        payload["agata_data_classification"] = "public"
    classification = payload.pop("agata_data_classification", classification)
    local = model.startswith(_ROTAS_LOCAIS)
    # (22/10/2026, P-8 sanitizador-cascata) a cascata seth-livre segue ao proxy, que bloqueia SEGREDO antes de qualquer
    # saída (sanitizar.sanitizar_payload). Dado pessoal e nomes de projeto NÃO são varridos pelo proxy desde a decisão
    # relaxa-pessoal (22/10). Outros modelos externos continuam exigindo public.
    if not local and classification != "public" and model != _ROTA_BASE:
        raise DadosExternosSemClassificacao(
            "dados sem classificação pública não podem ser enviados a modelos externos"
        )
    return payload


def _preparar_payload_publico(payload: dict) -> dict:
    """Retain only visible user/assistant history; never inject local canon.

    (19/11/2026, ferramentas-confianca) A faixa pública é de nível `gratuito`: só dado público. Ficam as ferramentas
    cujo rótulo (config/ferramentas-rotulos.json) devolve dado público, com as suas chamadas e resultados pareados no
    histórico; as demais, e todo resultado de ferramenta sem par ou acima do nível, saem antes de qualquer saída.
    Mensagens `system` e `tool` ocultas continuam removidas.
    """
    mensagens = payload.get("messages")
    maximo = ferramentas_confianca.dado_maximo(str(payload.get("model") or ""), True)
    base = [m for m in mensagens if isinstance(m, dict)
            and m.get("role") in ("user", "assistant", "tool")] if isinstance(mensagens, list) else []
    visiveis, _recusadas = ferramentas_confianca.filtrar_historico(base, maximo, so_com_par=True)
    payload["messages"] = [{"role": "system", "content": _doutrina_publica()}, *visiveis]
    for campo in ("functions", "function_call"):
        payload.pop(campo, None)
    ferramentas_confianca.filtrar_ferramentas(payload, maximo)
    return payload


def _filtrar_por_confianca(payload: dict, publica: bool) -> tuple[list, list]:
    """(19/11/2026) Fora da faixa pública: o pedido só leva as ferramentas cujo dado cabe no nível da rota, e o resultado
    de ferramenta acima do nível (ou com segredo) é trocado por uma omissão antes de voltar ao modelo.
    SETH_FERRAMENTAS_CONFIANCA=0 desliga (volta a oferecer tudo)."""
    if os.environ.get("SETH_FERRAMENTAS_CONFIANCA") == "0":
        return [], []
    maximo = ferramentas_confianca.dado_maximo(str(payload.get("model") or ""), publica)
    retiradas = ferramentas_confianca.filtrar_ferramentas(payload, maximo)
    msgs = payload.get("messages")
    recusadas: list = []
    if isinstance(msgs, list):
        payload["messages"], recusadas = ferramentas_confianca.filtrar_historico(msgs, maximo)
    if retiradas or recusadas:
        print(f"ferramentas-confianca: nível {maximo}; retiradas={retiradas} resultados_recusados={recusadas}",
              file=sys.stderr, flush=True)
    return retiradas, recusadas


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
    # (682) passo depois de ferramenta é a MESMA resposta: classifica só até o
    # último pedido do usuário. Antes, o resultado da ferramenta e as mensagens a
    # mais viravam "pesado" e a resposta trocava de fila no meio (seth-livre no
    # passo 1, seth-pesado no passo 2 -- medido no teste de 13/10, 21:59).
    if auditoria_turno.e_continuacao(msgs):
        ult = max((i for i, m in enumerate(msgs) if isinstance(m, dict) and m.get("role") == "user"),
                  default=len(msgs) - 1)
        msgs = msgs[:ult + 1]
    total, n_user, _ = _texto_e_sinais(msgs)
    # (705) "pesado" pelo PEDIDO ATUAL, não pelo histórico: a soma da conversa inteira
    # (saída de ferramenta incluída) mandava toda conversa com ferramenta para o Nemotron
    # Ultra -- 32 de 77 pedidos medidos em 14/10, e o decisor local diria "livre" em 31.
    # Contexto longo já tem fila própria (_fila_pela_janela, filas -longo).
    ult = _ultimo_texto_usuario(msgs)
    if len(ult) > _LIMIAR_PESADO_CHARS or "```" in ult:
        return "seth-pesado"
    if total < _LIMIAR_TRIVIAL_CHARS and not tem_tools and n_user <= 2:
        return "seth-rapido"
    return _ROTA_BASE


# --- Roteador-sombra: decisor local (PROTOCOLOS.md, "Decisor local") -----------
# O modelo de decisão escolhe a rota pelo SIGNIFICADO do pedido; as travas
# exatas abaixo continuam valendo por cima dele. Hoje só em SOMBRA: decide numa
# thread fora do caminho da resposta (winnow:e4b leva ~4 s na CPU) e registra em
# ~/.cache/agata/decisor/roteador.jsonl. A resposta segue pela heurística.
import decisor  # noqa: E402  (mesmo diretório)
import auditoria_turno  # noqa: E402  (mesmo diretório)
import limpa_emoji  # noqa: E402  (mesmo diretório; E-2, 16/10/2026)
import limpa_cabecalho  # noqa: E402  (mesmo diretório; cabeçalho único, 17/10/2026)
import limpa_laco  # noqa: E402  (mesmo diretório; trava de laço de repetição, 18/10/2026)
import registro_pedidos  # noqa: E402  (mesmo diretório; benchmark do roteamento, 23/10/2026; desligado por padrão)
import sombra_capacidade  # noqa: E402  (mesmo diretório; roteamento por capacidade em sombra, 24/10/2026; desligado por padrão)
import sombra_nova_versao  # noqa: E402  (mesmo diretório; nova versão do Experimento GPT em sombra, 04/11/2026; desligado por padrão)
import capivara_perfis  # noqa: E402  (scripts/, já no sys.path: perfis de janela por modelo, (667))
import ferramentas_confianca  # noqa: E402  (mesmo diretório; rótulos de ferramenta e confiança por provedor, 19/11/2026)
import bloqueio_turno  # noqa: E402  (mesmo diretório; bloqueio no lugar de aviso na verificação do turno, 19/11/2026)
import rotas_locais  # noqa: E402  (mesmo diretório; rotas locais por tipo, ficha assinada + painel que só restringe, 18/11/2026)

_PERFIS = {"mtime": None, "caminho": None, "quando": 0.0, "dados": {}}
_PERFIS_VALIDADE_S = 5.0  # caminho_perfil() relê o registro; o gateway chama _perfis() várias vezes por pedido


def _perfis() -> dict:
    """Perfis de janela em uso (23/11/2026, coordenação): capivara_perfis.carregar() sem argumento, que usa caminho_perfil()
    (o estado da Capivara quando está em dia com o registro; senão o retrato do repositório). Lembrado por 5 s e por mtime."""
    agora = time.monotonic()
    if _PERFIS["caminho"] is not None and agora - _PERFIS["quando"] < _PERFIS_VALIDADE_S:
        return _PERFIS["dados"]
    try:
        caminho = capivara_perfis.caminho_perfil()
        mt = Path(caminho).stat().st_mtime
    except Exception:  # noqa: BLE001 -- sem perfil legível: sem janela, vale a fila de sempre
        return {}
    if _PERFIS["mtime"] != mt or _PERFIS["caminho"] != str(caminho):
        _PERFIS["dados"], _PERFIS["mtime"], _PERFIS["caminho"] = capivara_perfis.carregar(), mt, str(caminho)
    _PERFIS["quando"] = agora
    return _PERFIS["dados"]


def _fila_pela_janela(payload: dict) -> str | None:
    """`<fila>-longo` quando o pedido (já hidratado) não cabe no menor modelo da fila
    base -- o LibreChat não sabe qual modelo da fila vai responder, o gateway sabe a fila
    (667). None = fica como está (pedido cabe, fila fora do perfil, sem fila longa)."""
    modelo = str(payload.get("model", ""))
    # A fila -longo só existe para as filas de conversa (capivara_perfis.FILAS_CONVERSA); `seth-codigo` não tem. Escalar para uma fila que
    # não existe dava HTTP 400 no OmniRoute (medido em 17/10/2026, 4 vezes no teste de produção).
    if modelo not in capivara_perfis.FILAS_CONVERSA:
        return None
    perfis = _perfis()
    limiar = capivara_perfis.limiar_tokens(perfis, modelo)
    if limiar is None or not capivara_perfis.fila_longa(perfis, modelo):
        return None
    msgs = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    estimativa = _texto_e_sinais(msgs)[0] // 3  # caracteres ÷ 3: conservador para português
    return modelo + capivara_perfis.SUFIXO_LONGO if estimativa > limiar else None

_PERGUNTA_ROTA = {"rota": {
    "type": "choice",
    "instructions": "What kind of AI model does this user request need?",
    "criteria": {
        "rapido": "a greeting, thanks, confirmation or trivial one-line question",
        "livre": "normal conversation, everyday explanation or writing help, no hard reasoning",
        "pesado": "hard reasoning, proof, deep technical analysis or complex planning",
        "codigo": "writing, fixing or explaining programming code, SQL or a script"}}}
_LIMIAR_ROTA = 0.6
# (719) o Laya decide a rota no caminho da resposta (~70 ms na CPU); passou disso, regra.
_TIMEOUT_LAYA = 1.5
_SOMBRA_LIVRE = threading.Semaphore(1)


def _rota_com_travas(escolhida: str | None, payload: dict) -> str:
    """Rota final a partir da escolha do modelo, com as travas exatas por cima.
    Sem escolha (confiança baixa, decisor fora) -> heurística de sempre."""
    if escolhida is None:
        return _classificar_rota(payload)
    msgs = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    if len(_ultimo_texto_usuario(msgs)) > _LIMIAR_PESADO_CHARS:  # (705) pedido atual, não histórico
        return "seth-pesado"
    # AC-01 (18/10/2026, decisão do Humano): a trava "ferramenta veta rapido" saiu. Medido pelo gateway,
    # 8 pedidos reais com ferramenta: seth-rapido 7 chamadas corretas, 0 malformadas, como a seth-livre.
    return f"seth-{escolhida}"


def _ultimo_texto_usuario(msgs: list) -> str:
    for m in reversed(msgs):
        if isinstance(m, dict) and m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, list):
                return " ".join(p.get("text", "") for p in c if isinstance(p, dict))
            return c if isinstance(c, str) else ""
    return ""


def _rota_laya(payload: dict) -> tuple[str, dict]:
    """(719) Rota ativa: o Laya ajustado escolhe (decisão do Humano, 15/10/2026: "prefiro
    já agora o Laya"), com as travas exatas de sempre por cima. Laya fora do ar, lento
    (> _TIMEOUT_LAYA) ou com confiança abaixo do limiar -> a regra por tamanho, como antes.
    Devolve (rota, resposta crua do Laya -- {} se não houve) para a sombra do Jev comparar."""
    if _e_chamada_utilitaria(payload):
        return _classificar_rota(payload), {}
    msgs = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    texto = _ultimo_texto_usuario(msgs)[-4000:]
    if not texto:
        return _classificar_rota(payload), {}
    total, n_user, cerca = _texto_e_sinais(msgs)
    # continuação (passo depois de ferramenta) decide de novo -- mesmo texto, mesma rota, a
    # fila não troca no meio (682) -- mas a avaliação conta só a 1ª decisão de cada resposta
    meta = {"heuristica": _classificar_rota(payload), "chars": total, "n_msgs": len(msgs),
            "n_user": n_user, "cerca_codigo": cerca, "tools": bool(payload.get("tools")),
            "continuacao": auditoria_turno.e_continuacao(msgs)}
    r = decisor.decidir("roteador-laya", texto, _PERGUNTA_ROTA, timeout=_TIMEOUT_LAYA, meta=meta,
                        url=decisor.URL_LAYA, modelo=decisor.MODELO_LAYA)
    return _rota_com_travas(decisor.escolha(r, "rota", _LIMIAR_ROTA), payload), (r or {}).get("rota") or {}


def _sombra_rota(payload: dict, rota_ativa: str, laya: dict | None = None) -> None:
    """Dispara a decisão-sombra do Jev sem esperar. Uma por vez: se o decisor ainda
    está ocupado, este pedido fica sem sombra (nunca empilha CPU). (719) Desde que o
    Laya decide a rota, o Jev é a sombra dele: onde as escolhas cruas discordam, o
    caso vai para o juiz automático (`avaliar_decisor.py`)."""
    if not _SOMBRA_LIVRE.acquire(blocking=False):
        return
    msgs = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    # Texto AGORA: logo depois o `_injeta` põe a hidratação (~4 mil chars) no
    # mesmo `payload` (13/10/2026, MEMÓRIAS (657)).
    texto = _ultimo_texto_usuario(msgs)[-4000:]
    total, n_user, cerca = _texto_e_sinais(msgs)
    meta = {"rota_ativa": rota_ativa, "chars": total, "n_msgs": len(msgs),
            "n_user": n_user, "cerca_codigo": cerca, "tools": bool(payload.get("tools"))}
    laya = laya or {}

    def _rodar():
        try:
            if not texto:
                return
            r = decisor.decidir("roteador", texto, _PERGUNTA_ROTA, meta=meta)
            jev = (r or {}).get("rota") or {}
            # escolha crua de cada um (sem limiar): é o que se compara e o que o juiz julga
            if jev.get("choice") and laya.get("choice") and jev["choice"] != laya["choice"]:
                decisor.registrar_avaliacao("roteador-laya", {
                    "jev": jev["choice"], "laya": laya["choice"],
                    "conf_jev": jev.get("confidence"), "conf_laya": laya.get("confidence"),
                    "rota_ativa": rota_ativa, "chars": total, "trecho": texto[:200]})
        finally:
            _SOMBRA_LIVRE.release()

    threading.Thread(target=_rodar, daemon=True).start()


# --- escolha por capacidade em produção e log de uso (23/11/2026) ----------------------------------------------------
# Decisão do Humano (23/11, 16:40): "todos os modelos devem ser escolhidos a partir de suas capacidades ... agata code
# segue as mesmas regras". A rota vem do Laya e o combo da fila. A capacidade troca o combo pelo modelo concreto que o
# registro (config/capivara/capacidades.json, só leitura aqui) recomenda para o tipo, com nota >= PISO e amostra >=
# AMOSTRA_MIN. Sem nota e amostra suficientes, vale o combo de sempre. Sai pelo mesmo sanitizador (UPSTREAM).
_ROTAS_CLASSE = ("rapido", "livre", "pesado", "codigo")
USO_CAPIVARA_PADRAO = Path.home() / ".local" / "share" / "agata" / "capivara" / "uso.jsonl"


def _escolha_capacidade_ligada() -> bool:
    """SETH_ESCOLHA_CAPACIDADE=0 desliga e volta ao combo de antes. Padrão ligado (decisão do Humano = produção)."""
    return os.environ.get("SETH_ESCOLHA_CAPACIDADE") != "0"


def _rota_classe(rota: str | None) -> str | None:
    """seth-livre-longo -> livre. Fora das quatro classes do Laya (ou sem rota) -> None."""
    base = (rota or "").removeprefix("seth-").removesuffix("-longo")
    return base if base in _ROTAS_CLASSE else None


def _rota_laya_por(rota: str, laya: dict | None) -> tuple[str, float | None]:
    """De onde saiu a rota: 'laya' se a escolha do Laya passou do limiar e virou a rota; 'regra' se o Laya caiu, demorou,
    veio com confiança abaixo do limiar, ou uma trava trocou a rota. A mesma regra de decisor.escolha."""
    if not isinstance(laya, dict):
        return "regra", None
    conf = laya.get("confidence")
    if isinstance(conf, bool) or not isinstance(conf, (int, float)):
        return "regra", None
    escolhida = laya.get("choice") if conf >= _LIMIAR_ROTA else None
    por = "laya" if escolhida and rota == f"seth-{escolhida}" else "regra"
    return por, float(conf)


def _janelas_perfis() -> dict:
    pf = _perfis()
    return {m: capivara_perfis.janela(pf, m) for m in (pf.get("modelos") or {})}


def _perfil_do_pedido(payload: dict, msgs_pedido: list, rota_laya: str | None) -> dict:
    """Perfil do pedido que vai ao modelo, sem texto: os requisitos da sombra sobre o pedido final (tokens com a injeção
    da Máquina e as ferramentas), a régua de dado pessoal sobre TODAS as falas recebidas (sem a injeção) e o segredo
    (falha fechada). Tipo: a rota do Laya manda (codigo -> codigo); o resto vem dos requisitos."""
    req = sombra_capacidade.requisitos(payload, varrer_pessoal=lambda _t: [])  # o privado sai do histórico, abaixo
    msgs = msgs_pedido if isinstance(msgs_pedido, list) else []
    req["privado"] = sombra_capacidade.privado_no_historico(msgs)
    req["tokens_est"] = rotas_locais.tokens_estimados(payload)
    rf = payload.get("response_format")
    req["json"] = bool(req.get("json")) or (isinstance(rf, dict) and str(rf.get("type", "")).startswith("json"))
    req["tipo"] = sombra_capacidade.tipo_da_escolha(rota_laya, req)
    req["stream"] = bool(payload.get("stream"))  # em stream, o p95 do modelo tem de caber no prazo do 1º conteúdo
    segredo = rotas_locais.tem_segredo({"messages": msgs})
    classe = "pessoal" if (req["privado"] or segredo) else "publico"  # pessoal = só modelo local na escolha
    return {"req": req, "tipo": req["tipo"], "classe": classe, "segredo": segredo}


def _escolha_capacidade(perfil: dict | None, rota: str) -> dict | None:
    """Escolha de produção (sombra_capacidade.escolher), ou None = combo de sempre. Segredo nunca escolhe; desligada por
    SETH_ESCOLHA_CAPACIDADE=0; qualquer exceção vira None (nunca derruba o pedido)."""
    if not perfil or not _escolha_capacidade_ligada() or perfil.get("segredo"):
        return None
    try:
        return sombra_capacidade.escolher(perfil["req"], rota, sombra_capacidade.carregar_registro(), _janelas_perfis(),
                                          prazo_stream_s=PRAZO_1O_CONTEUDO)
    except Exception:  # noqa: BLE001 -- escolha quebrada: fica o combo
        return None


def _caminho_uso() -> Path:
    """AGATA_CAPIVARA_USO aponta outro arquivo (os testes usam um temporário; o log real não recebe lixo de teste)."""
    return Path(os.environ.get("AGATA_CAPIVARA_USO") or USO_CAPIVARA_PADRAO)


def _linha_uso(*, modelo, tipo, classe, status, bloqueado, latencia_ms, rota, rota_por, laya_confianca,
               achados, refeito, corrigido) -> dict:
    """Uma linha do log de uso da Capivara. Só rótulos, números, códigos de achado e o nome do modelo: nenhum texto do
    pedido ou da resposta. achados = códigos (lista); refeito = nº de refações; corrigido = a entregue saiu sem achado
    (None = não verificada)."""
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "modelo": modelo, "tipo": tipo, "classe": classe,
            "status": status, "bloqueado": bool(bloqueado), "latencia_ms": latencia_ms, "rota": rota,
            "rota_por": rota_por, "laya_confianca": laya_confianca, "achados": list(achados),
            "refeito": int(refeito), "corrigido": corrigido}


def _gravar_uso(linha: dict) -> None:
    """Acrescenta a linha ao uso.jsonl (pasta criada se faltar). Nunca levanta: falha ao gravar não derruba o pedido."""
    try:
        caminho = _caminho_uso()
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        print(f"uso: não gravou ({e.__class__.__name__})", file=sys.stderr, flush=True)


def _modelo_do_corpo(corpo: bytes) -> str | None:
    """Nome do modelo que o corpo pede (a tentativa que falhou). Sem JSON legível = None."""
    try:
        m = json.loads(corpo).get("model") if corpo else None
    except (ValueError, AttributeError, TypeError):
        return None
    return m if isinstance(m, str) else None


# (705) O cabeçalho é da Máquina: o modelo real DESTE turno (medido na espiada do stream,
# antes de qualquer byte ao cliente), t pelo contador mecânico, hora do relógio e, na 1ª
# resposta, o bloco de prontidão. A Seth errava o cabeçalho em quase todo turno.
_FAMILIAS = (("gemini", "Google"), ("gemma", "Google"), ("ministral", "Mistral"), ("mistral", "Mistral"),
             ("codestral", "Mistral"), ("nemotron", "NVIDIA"), ("glm", "Zhipu"), ("qwen", "Alibaba"),
             ("llama", "Meta"), ("gpt-oss", "OpenAI"), ("deepseek", "DeepSeek"))


def _descrever_modelo(nome: str | None) -> str:
    if not nome:
        return "modelo não verificado"
    chave = next((k for k in (_perfis().get("modelos") or {}) if k == nome or k.endswith("/" + nome)), "")
    onde = "local, na Máquina" if "ollama" in (chave or nome).lower() else "nuvem"
    familia = next((f for t, f in _FAMILIAS if t in nome.lower()), None)
    return f"{nome} ({familia + ', ' if familia else ''}{onde}; medido pela Máquina neste turno)"


# O cabeçalho da Máquina abre com este nome (decisão do Humano, 17/10/2026): é o ÚNICO lugar em que o nome do sistema sai como "agata-seth".
_NOME_CABECALHO = os.environ.get("SETH_NOME_CABECALHO", "agata-seth")


def _cabecalho_maquina(msgs: list, modelo: str | None) -> str:
    n_msgs = len(auditoria_turno._turnos(msgs)[0]) + 1
    n_prev = _max_turno_em_mensagens(msgs)
    n = max(n_msgs, n_prev + 1) if n_prev > 0 else n_msgs
    hora = time.strftime("%Y-%m-%d %H:%M %z") + " (relógio da Máquina)"
    if n > 1:
        return f"{_NOME_CABECALHO} · {_descrever_modelo(modelo)} · t={n} (contador mecânico) · {hora}"
    est = {l.split(":", 1)[0]: l for l in _estado().splitlines() if ":" in l}
    sync = est.get("sync") or "sync: não verificado · lacuna: estado não medido"
    topo = est.get("TOPO-MEMÓRIAS", "").split(":", 1)[-1].strip()
    topo = (topo[:300] + "…") if len(topo) > 300 else (topo or "lacuna (estado não injetado)")
    quebrado = [est[k] for k in ("ALERTA-HISTORIA",) if k in est] + ([] if sync.startswith("sync: PASS") else [sync])
    fim = "pronto." if not quebrado else "quebrado: " + "; ".join(q[:200] for q in quebrado)
    return f"{_NOME_CABECALHO} · modelo: {_descrever_modelo(modelo)} · {sync} · {hora}\nÚltima entrada: {topo}\n{fim}"


def _injetar_sse(buf: bytes, texto: str) -> bytes | None:
    """Insere um chunk `delta.content = texto` antes do 1º chunk com TEXTO. None se não há."""
    linhas = buf.split(b"\n")
    for i, l in enumerate(linhas):
        if not l.startswith(b"data:") or l.startswith(b"data: [DONE]"):
            continue
        try:
            o = json.loads(l[5:])
        except ValueError:
            continue
        ch = (o.get("choices") or [{}])[0] if isinstance(o, dict) else {}
        if ((ch.get("delta") or {}).get("content") or "").strip():
            novo = {"id": o.get("id"), "object": o.get("object", "chat.completion.chunk"),
                    "created": o.get("created"), "model": o.get("model"),
                    "choices": [{"index": ch.get("index", 0), "delta": {"content": texto},
                                 "finish_reason": None}]}
            linhas[i:i] = [b"data: " + json.dumps(novo, ensure_ascii=False).encode("utf-8"), b""]
            return b"\n".join(linhas)
    return None


# (709) Prazo para o 1º conteúdo útil. Com a cota do Gemini estourada, o OmniRoute
# devolve 200 e só keepalive por 310 s antes de passar ao próximo modelo (medido em
# 14/10, 20:23-20:29); o LibreChat ficava girando. 40 s sem texto nem ferramenta: o
# gateway desiste e tenta a fila seguinte, antes de mandar qualquer byte ao cliente.
PRAZO_1O_CONTEUDO = float(os.environ.get("SETH_PRAZO_1O_CONTEUDO_S", "40"))


def _derrubar(up) -> None:
    """(709) Fecha o upstream SEM esperar a leitura presa na thread do _Leitor: shutdown no
    socket faz o read1 dela voltar na hora e o outro lado (sanitizador -> OmniRoute) ver a
    desistência. Só close() esperava a leitura terminar."""
    try:
        sock = getattr(getattr(getattr(up, "fp", None), "raw", None), "_sock", None)
        if sock is not None:
            sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        up.close()
    except Exception:  # noqa: BLE001
        pass


class _Leitor:
    """Lê o upstream numa thread e entrega por fila: `ler(timeout)` devolve bytes,
    b"" no fim, ou levanta queue.Empty no prazo. Prazo por socket não serve -- depois
    de um timeout o Python recusa novas leituras daquele socket."""

    def __init__(self, up):
        self._fila: queue.Queue = queue.Queue()
        self._up = up
        threading.Thread(target=self._rodar, daemon=True).start()

    def _rodar(self):
        try:
            while True:
                pedaco = self._up.read1(65536) if hasattr(self._up, "read1") else self._up.read(8192)
                self._fila.put(pedaco)
                if not pedaco:
                    return
        except Exception as e:  # noqa: BLE001 -- upstream fechado/abortado vira fim, com o motivo
            self._fila.put(e)

    def ler(self, timeout: float) -> bytes:
        item = self._fila.get(timeout=max(timeout, 0.01))
        if isinstance(item, Exception):
            raise item
        return item


def _rodadas_ferramenta(msgs: list) -> int:
    """Rodadas de ferramenta da resposta EM ANDAMENTO: mensagens do assistente com
    `tool_calls` depois da última mensagem do Humano."""
    n = 0
    for m in reversed(msgs):
        if not isinstance(m, dict):
            continue
        if m.get("role") == "user":
            break
        if m.get("role") == "assistant" and m.get("tool_calls"):
            n += 1
    return n


def _teto_ferramentas() -> int:
    """AC-37 (17/10/2026): a Seth fez 11 chamadas seguidas e parou sem texto, com a
    tela presa em "Pare de gerar". No teto, o pedido sai com `tool_choice: none`:
    o modelo tem de responder em texto com o que já mediu. SETH_TETO_FERRAMENTAS=0 desliga."""
    try:
        return max(0, int(os.environ.get("SETH_TETO_FERRAMENTAS", "6")))
    except ValueError:
        return 6


def _aplica_teto(payload: dict, msgs: list) -> str:
    """Põe `tool_choice: none` quando a resposta já usou o teto de rodadas; devolve a
    linha de estado que explica ao modelo, ou "" abaixo do teto."""
    teto = _teto_ferramentas()
    n = _rodadas_ferramenta(msgs)
    if not teto or n < teto or not payload.get("tools"):
        return ""
    payload["tool_choice"] = "none"
    return (f"TETO-FERRAMENTAS: esta resposta já fez {n} rodadas de ferramenta (teto {teto}). "
            "Não chame mais ferramenta: responda agora, em texto, com o que já foi medido; "
            "o que faltou medir, escreva \"não medido\".")


# (24/10/2026) A correção do turno anterior perto da pergunta. Medido: com a linha
# AUDITORIA-TURNO-ANTERIOR só no fim do system de ~13 mil caracteres, Codestral, Ministral e o
# MoE local corrigiram 1 vez em 9; com a mesma linha como prefixo curto da última pergunta do
# Humano, 9 em 9 (Codestral, Ministral, Gemini 3.1 Flash-Lite). Achado só de cabeçalho fica de
# fora (é com a Máquina). SETH_CORRECAO_NA_PERGUNTA=0 desliga.
_PREFIXO_AUDITORIA = "AUDITORIA-TURNO-ANTERIOR: "


# (25/10/2026) Resgate do raciocínio. O qwen3.5-9b (fundo local) com o prompt real chama a
# ferramenta e, no passo seguinte, escreve a resposta final no campo `reasoning` e deixa
# `content` vazio (4 de 5 no benchmark de prompt real): o Humano veria resposta vazia. Desligar
# o raciocínio (reasoning_effort=none) fez o modelo parar de chamar a ferramenta e inventar o
# estado; `think`/`chat_template_kwargs` não passam pelo OmniRoute. Regra: resposta que termina
# SEM texto, SEM chamada de ferramenta e COM raciocínio recebe o raciocínio como texto. Se o
# modelo escreveu texto ou chamou ferramenta, nada muda. Vem DEPOIS da nova tentativa da (695):
# primeiro tenta a fila acima; o resgate só age na resposta que vai ao cliente. Teste pelo
# gateway real com o 9b forçado (25/10, 10h31): sem o resgate, 0 caractere na 2ª volta; com
# ele, a resposta chega. SETH_RESGATE_RACIOCINIO=0 desliga.
def _resgate_ligado() -> bool:
    return os.environ.get("SETH_RESGATE_RACIOCINIO") != "0"


# (25/10/2026, noite) Só modelo LOCAL: os Gemini mandam um raciocínio separado, em inglês ("thought
# summaries"); 1 de 18 respostas do Gemini 3.5 Flash-Lite terminou só com ele, e o resgate o entregaria
# ao Humano. O ganho medido é do fundo local. O upstream devolve o nome sem o prefixo do provedor:
# a lista sai das chaves locais do registro de capacidades, relida quando o arquivo muda.
_LOCAIS_CACHE: dict = {"mtime": None, "nomes": frozenset()}


def _modelo_local(modelo: str | None) -> bool:
    if not modelo:
        return False
    arq = REPO / "config" / "capivara" / "capacidades.json"
    try:
        mt = arq.stat().st_mtime
        if mt != _LOCAIS_CACHE["mtime"]:
            reg = json.loads(arq.read_text(encoding="utf-8"))
            _LOCAIS_CACHE["nomes"] = frozenset(k.split("/", 1)[1] for k in (reg.get("modelos") or {})
                                               if k.startswith(_ROTAS_LOCAIS))
            _LOCAIS_CACHE["mtime"] = mt
    except (OSError, ValueError, AttributeError):
        return False
    return modelo in _LOCAIS_CACHE["nomes"] or modelo.split("/", 1)[-1] in _LOCAIS_CACHE["nomes"]


def _resgate_observar(linha: bytes, estado: dict) -> None:
    """Acumula, de uma linha `data:` do SSE, o raciocínio e se houve texto ou ferramenta."""
    if not linha.startswith(b"data:"):
        return
    corpo = linha[5:].strip()
    if not corpo or corpo == b"[DONE]":
        return
    try:
        o = json.loads(corpo)
        ch = (o.get("choices") or [{}])[0]
        d = ch.get("delta") or {}
    except (ValueError, AttributeError, IndexError, TypeError):
        return
    if (d.get("content") or "").strip():
        estado["texto"] = True
    if d.get("tool_calls"):
        estado["ferramenta"] = True
    r = d.get("reasoning") or d.get("reasoning_content") or ""
    if isinstance(r, str) and r:
        estado["raciocinio"] = estado.get("raciocinio", "") + r
    for k in ("id", "model", "created"):
        if o.get(k) is not None and k not in estado:
            estado[k] = o[k]


def _resgate_chunk(estado: dict, prefixo: str = "") -> bytes | None:
    """O chunk SSE com o raciocínio como texto, ou None se não há o que resgatar."""
    if (estado.get("texto") or estado.get("ferramenta") or not (estado.get("raciocinio") or "").strip()
            or not _modelo_local(estado.get("model"))):
        return None
    ev = {"id": estado.get("id", "seth-resgate"), "object": "chat.completion.chunk",
          "created": estado.get("created", 0), "model": estado.get("model", ""),
          "choices": [{"index": 0, "delta": {"content": prefixo + estado["raciocinio"].strip()}, "finish_reason": None}]}
    estado["texto"] = True
    return b"data: " + json.dumps(ev, ensure_ascii=False).encode("utf-8") + b"\n\n"


def _resgate_json(corpo: bytes) -> bytes:
    """O mesmo resgate na resposta sem stream: `content` vazio, sem ferramenta e com raciocínio ->
    o raciocínio vira `content`. Independe do cabeçalho (25/10: na volta depois da ferramenta de
    um turno já começado não há cabeçalho, e o resgate ficava de fora)."""
    try:
        o = json.loads(corpo)
        m = o["choices"][0]["message"]
    except (ValueError, KeyError, IndexError, TypeError):
        return corpo
    r = m.get("reasoning") or m.get("reasoning_content") or ""
    if ((m.get("content") or "").strip() or m.get("tool_calls") or not isinstance(r, str) or not r.strip()
            or not _modelo_local(o.get("model"))):
        return corpo
    m["content"] = r.strip()
    return json.dumps(o, ensure_ascii=False).encode("utf-8")


# (26/10/2026, V9 §37 M6a, decisão do Humano: "bloqueia para o humano é mais compreensível") Verificação
# de fatos ANTES de a resposta aparecer: nas rotas seth-*, as linhas de dados do stream ficam retidas (os
# comentários SSE de keepalive passam, para a conexão não cair); no fim, a Máquina roda as checagens
# mecânicas de fato (auditoria_turno.verificar_resposta_atual) sobre o texto -- sem o cabeçalho e a
# correção que ela mesma injetou -- e entrega tudo de uma vez, com a "Verificação da Máquina" no fim se houver
# achado. Fora do stream, o mesmo no `content`. SETH_VERIFICACAO_BLOQUEIA=0 desliga.
def _verificacao_ligada() -> bool:
    return os.environ.get("SETH_VERIFICACAO_BLOQUEIA") != "0"


def _texto_do_sse(chunks: list) -> str:
    """O texto (`delta.content`) de uma lista de chunks SSE retidos."""
    partes = []
    for ch in chunks:
        for linha in ch.split(b"\n"):
            if not linha.startswith(b"data:") or linha.strip() == b"data: [DONE]":
                continue
            try:
                for c in json.loads(linha[5:]).get("choices") or []:
                    partes.append((c.get("delta") or {}).get("content") or "")
            except (ValueError, AttributeError, TypeError):
                continue
    return "".join(partes)


def _bloco_verificacao(achados: list) -> str:
    itens = "\n".join(f"- {a.strip()[:300]}" for a in achados[:8])
    return f"\n\n---\n**Verificação da Máquina** (antes de você ler; mecânica, sem modelo):\n{itens}"


def _guarda_bloqueia(texto: str, msgs: list) -> bool:
    """(lote 5, A3) Eco de segredo ou frase mandada por uma ferramenta suspeita/privada no histórico.
    Só age com SETH_GUARDA_BLOQUEIA=1; sem ferramenta no histórico, nunca bloqueia."""
    if os.environ.get("SETH_GUARDA_BLOQUEIA") != "1" or not (texto or "").strip():
        return False
    try:
        p = str(REPO / "redesign" / "metacognicao")
        if p not in sys.path:
            sys.path.insert(0, p)
        import guarda  # noqa: E402
        fontes = [{"id": f"t{i}", "texto": str(m.get("content") or ""), "classification": "public"}
                  for i, m in enumerate(msgs or []) if isinstance(m, dict) and m.get("role") == "tool"]
        return bool(fontes) and guarda.checar(texto, fontes)["estado"] == "bloqueado"
    except Exception:  # noqa: BLE001 — guarda quebrada nunca segura a resposta
        return False


def _recusa_no_stream(retidos: list, modelo: str) -> list:
    """Troca os chunks de conteúdo por uma recusa, mantendo o finish e o [DONE] (não quebra o cliente)."""
    import guarda  # noqa: E402
    saida, inserida = [], False
    for ch in retidos:
        if b"data: [DONE]" in ch:
            if not inserida:
                saida.append(_chunk_texto(guarda.RECUSA, modelo)); inserida = True
            saida.append(ch)
        elif _texto_do_sse([ch]).strip():
            if not inserida:
                saida.append(_chunk_texto(guarda.RECUSA, modelo)); inserida = True
        else:
            saida.append(ch)
    return saida


def _chunk_texto(texto: str, modelo: str = "") -> bytes:
    ev = {"id": "seth-verificacao", "object": "chat.completion.chunk", "created": 0, "model": modelo,
          "choices": [{"index": 0, "delta": {"content": texto}, "finish_reason": None}]}
    return b"data: " + json.dumps(ev, ensure_ascii=False).encode("utf-8") + b"\n\n"


def _so_comentario(saida: bytes) -> bool:
    """Chunk com comentário SSE (keepalive) e nada além de comentários e linhas vazias: pode passar mesmo
    com a resposta retida. Linha vazia SOZINHA não passa: ela é o separador que fecha o evento `data:`
    anterior. (26/10/2026) Soltá-la na hora e reter o `data:` mandava todos os separadores na frente
    e os dados colados no fim, sem linha vazia entre eles: para o cliente SSE, um evento só, nunca
    fechado -> nenhum chunk -> "'tool_calls' in undefined" no Agent do LibreChat (a mesma classe de
    (635))."""
    linhas = saida.split(b"\n")
    return any(l.startswith(b":") for l in linhas) and all((not l.strip()) or l.startswith(b":") for l in linhas)


def _correcao_da_maquina(linha: str) -> str:
    """(25/10/2026) A Máquina escreve ela mesma a correção, logo abaixo do cabeçalho que já injeta.
    Medido pelo gateway: pedir ao modelo para corrigir (prefixo na pergunta) fez o Codestral parar de
    chamar ferramenta (0 de 6) e inventar saída (4 de 6); sem prompt novo ele chama (5 de 6). Esta linha
    não muda o prompt, então não mexe em ferramenta, e aparece sempre. SETH_CORRECAO_MAQUINA=0 desliga."""
    if os.environ.get("SETH_CORRECAO_MAQUINA") == "0":
        return ""
    # (19/11/2026, decisão do Humano) a correção do turno anterior vai SÓ ao contexto do modelo (a nota perto da pergunta,
    # abaixo), nunca ao Humano. SETH_CORRECAO_VISIVEL=1 restaura a linha visível de 25/10.
    if os.environ.get("SETH_CORRECAO_VISIVEL") != "1":
        return ""
    marca_cont = "AINDA FALTA corrigir o turno anterior: "   # passo final do modo Agent (auditoria_turno)
    if linha.startswith(_PREFIXO_AUDITORIA):
        resto = linha[len(_PREFIXO_AUDITORIA):]
    elif linha.startswith("MESMA-RESPOSTA") and marca_cont in linha:
        resto = linha.split(marca_cont, 1)[1]
    else:
        return ""
    achados = [a.strip() for a in resto.split(" | ")
               if a.strip() and a.strip() != "OK" and not a.strip().startswith("cabeçalho")]
    if not achados:
        return ""
    # o texto contém "correção do turno anterior": a auditoria do passo seguinte vê a correção feita
    return "Correção do turno anterior (pela Máquina): " + "; ".join(achados) + "\n\n"


def _correcao_perto_da_pergunta(msgs: list, linha: str) -> list:
    if os.environ.get("SETH_CORRECAO_NA_PERGUNTA") == "0" or not linha.startswith(_PREFIXO_AUDITORIA):
        return msgs
    achados = [a.strip() for a in linha[len(_PREFIXO_AUDITORIA):].split(" | ")
               if a.strip() and a.strip() != "OK" and not a.strip().startswith("cabeçalho")]
    if not achados or not msgs or not isinstance(msgs[-1], dict) or msgs[-1].get("role") != "user":
        return msgs
    aviso = ("[Máquina, só para você; não cite esta nota ao Humano: a sua resposta anterior foi conferida e tem erro. "
             "Corrija sem repetir o erro e sem anunciar a correção. " + " | ".join(achados) + "]\n\n")
    ultima = dict(msgs[-1])
    c = ultima.get("content")
    if isinstance(c, str):
        ultima["content"] = aviso + c
    elif isinstance(c, list):
        ultima["content"] = [{"type": "text", "text": aviso}] + c
    else:
        return msgs
    return msgs[:-1] + [ultima]


def _injeta(payload: dict) -> dict:
    msgs = payload.get("messages")
    if not isinstance(msgs, list):
        return payload
    # chamada de título/utilidade do frontend: repassa crua, sem hidratar.
    if _e_chamada_utilitaria(payload):
        return payload
    # resposta anterior do assistente conferida aqui, antes de mexer em `msgs` (662)
    auditoria = auditoria_turno.linha_estado(msgs, str(payload.get("model", "")))
    msgs = _correcao_perto_da_pergunta(msgs, auditoria)
    payload["_agata_aud"] = auditoria  # o handler tira antes de enviar e usa na correção da Máquina
    auditoria = auditoria_turno.linha_modo(msgs) + (f"\n{auditoria}" if auditoria else "")
    literais = auditoria_turno.entradas_literais(msgs)  # rédea (17/10/2026): o texto exato das entradas que o Humano citou
    if literais:
        auditoria = (auditoria + "\n" if auditoria else "") + literais
    unidades = auditoria_turno.unidades_medidas(msgs)  # 17/10/2026: estado da unidade medido pela Máquina, não de cabeça
    if unidades:
        auditoria = (auditoria + "\n" if auditoria else "") + unidades
    teto = _aplica_teto(payload, msgs)
    if teto:
        auditoria = (auditoria + "\n" if auditoria else "") + teto
    # (26/10/2026, V9 §37 M2) a memória comum do Conselho, não canônica: quantas entradas e as últimas 3,
    # curtas; o resto se lê com `maquina_verificar cache_conselho`. Falha aqui nunca atrapalha a hidratação.
    try:
        import cache_conselho
        _cc = cache_conselho.resumo_hidratacao()
    except Exception:  # noqa: BLE001
        _cc = ""
    if _cc and os.environ.get("SETH_CACHE_CONSELHO_HIDRATA") != "0":
        auditoria = (auditoria + "\n" if auditoria else "") + _cc
    # (07/11/2026, núcleo de desenvolvimento, D2) ponteiro PROCESSO: para o guia universal; não entra na doutrina.
    _proc = _linha_processo()
    if _proc:
        auditoria = (auditoria + "\n" if auditoria else "") + _proc
    # (05/11/2026, nova versão lote 4 item 3) evidência da Alexandria para a pergunta da vez, com as notas da
    # curadoria; DESLIGADA por padrão (SETH_ALEXANDRIA_HIDRATA=1 liga). Só no 1º passo da resposta (não em
    # continuação de ferramenta); sem índice ou com erro, segue sem o bloco.
    if os.environ.get("SETH_ALEXANDRIA_HIDRATA") == "1" and not auditoria_turno.e_continuacao(msgs):
        try:
            import hidratacao  # redesign/alexandria (caminho posto por sombra_nova_versao)
            _ev, _ = hidratacao.bloco(registro_pedidos.ultima_pergunta(msgs))
        except Exception:  # noqa: BLE001
            _ev = None
        if _ev:
            auditoria = (auditoria + "\n" if auditoria else "") + _ev
    # (lote 5, A2) skills sugeridas: só nomes e descrição, nada é carregado. Desligado (SETH_SKILLS_SUGERE=1).
    if os.environ.get("SETH_SKILLS_SUGERE") == "1" and not auditoria_turno.e_continuacao(msgs):
        try:
            import skills as _sk  # noqa: E402  (redesign/alexandria já está no sys.path via sombra_nova_versao)
            _bs = _sk.bloco_skills(registro_pedidos.ultima_pergunta(msgs))
        except Exception:  # noqa: BLE001
            _bs = None
        if _bs:
            auditoria = (auditoria + "\n" if auditoria else "") + _bs
    ja_hidratado = any(
        isinstance(m, dict) and m.get("role") == "system"
        and isinstance(m.get("content"), str) and MARCADOR in m["content"]
        for m in msgs)
    if ja_hidratado:
        # não repete a doutrina, mas REFRESCA o estado (MEMÓRIAS (417)): tira o
        # ESTADO-ATUAL do turno anterior e põe um com a hora/sync de agora. O
        # ponteiro PROCESSO também é estado de turno: remove a cópia anterior
        # para respeitar SETH_PROCESSO_HIDRATA e evitar duplicação. Se a medição
        # falhar, conserva o ponteiro anterior quando ainda estiver ligado.
        msgs = [m for m in msgs if not (
            isinstance(m, dict) and m.get("role") == "system"
            and isinstance(m.get("content"), str) and MARCADOR_ESTADO in m["content"])]
        bloco = _bloco_estado_atual(auditoria)
        if not _proc or bloco:
            msgs = _retirar_ponteiro_processo_antigo(msgs)
        payload["messages"] = ([{"role": "system", "content": bloco}] + msgs
                               if bloco else msgs)
        return payload
    hidratacao = _hidratacao(auditoria)
    # No modo full, _hidratacao usa o arquivo completo e não consome `extra`.
    # Mantém o ponteiro como estado variável após o conteúdo hidratado, fora da
    # doutrina fixa e só neste caminho interno.
    if _proc and MODO != "compacto":
        hidratacao = f"{hidratacao.rstrip()}\n{_proc}\n"
    sys_msg = {"role": "system", "content": hidratacao}
    # se o frontend já mandou um system próprio, o nosso entra ANTES dele
    payload["messages"] = [sys_msg] + msgs
    return payload


# --- base do roteador (17/11/2026, proposta seth-base-17-11) ---------------------------------------------
# Itens que valem em qualquer modo: served_by no log, cabeçalho sem duplicata na Seth, ferramenta escrita
# como texto virar tool_calls. SETH_ROTEADOR (legado padrão | sombra | capacidade[:N]) só entra no 429
# (a marca de log em _passar); nenhuma ação muda por modo, porque o 429 nasce no OmniRoute.


def _modo_roteador() -> str:
    """SETH_ROTEADOR, lido a cada chamada. Padrão 'legado'; vazio conta como legado."""
    return (os.environ.get("SETH_ROTEADOR") or "legado").strip().lower() or "legado"


# --- verificar e refazer (18/11/2026) -------------------------------------------------------------------------
# Decisão do Humano (17/11): "os mecanismos de checagem de fatos e correções devem agir antes de a resposta do
# modelo ser apresentada, o que pode ser refeito embaixo do capô quantas vezes forem necessárias até a resposta
# ser confiável". Sem isto, a Máquina confere a resposta e só anexa a "Verificação da Máquina". Com isto, a
# resposta inteira é lida, conferida, e enquanto houver achado o upstream é chamado de novo com o mesmo pedido,
# mais a resposta ruim e uma nota com os achados. Para no 1º texto sem achado, em SETH_REFAZER_MAX novas
# tentativas ou em SETH_REFAZER_SEG segundos. Entrega a de menos achados; se ainda sobrar algum, o gate de
# entrega põe a "Verificação da Máquina" como antes. Só nas rotas seth-* com verificação ligada.
_REFAZER_ORDEM = ("seth-rapido", "seth-livre", "seth-pesado")


def _refazer_ligado_neste_pedido() -> bool:
    """Decidido por pedido. Padrão LIGADO (23/11/2026, Humano: "as respostas só saem depois da correção do sistema"): a
    resposta é conferida e refeita antes de sair. SETH_REFAZER=0 desliga sempre; =1 liga sempre. Com o canário
    SETH_ROTEADOR=capacidade:N, liga N% dos pedidos (sorteio por pedido)."""
    chave = (os.environ.get("SETH_REFAZER") or "").strip()
    if chave == "0":
        return False
    if chave == "1":
        return True
    modo = _modo_roteador()
    if modo.startswith("capacidade:"):
        try:
            pct = float(modo.partition(":")[2])
            return random.random() * 100 < pct
        except ValueError:
            pass  # N inválido: sem canário, vale o padrão ligado
    return True


_PEDIDO_TETO_S_PADRAO = 600.0  # (23/11, Humano) teto total do pedido: coleta + refazer + correção do bloqueio


def _pedido_teto_seg() -> float:
    try:
        return max(0.001, float(os.environ.get("SETH_PEDIDO_TETO_SEG", str(_PEDIDO_TETO_S_PADRAO))))
    except ValueError:
        return _PEDIDO_TETO_S_PADRAO


def _refazer_max() -> int:
    try:
        return max(0, int(os.environ.get("SETH_REFAZER_MAX", "2")))
    except ValueError:
        return 2


def _refazer_seg() -> float:
    """Teto, em segundos, das NOVAS tentativas (a partir do fim da 1ª resposta). Não conta a 1ª resposta."""
    try:
        return max(0.0, float(os.environ.get("SETH_REFAZER_SEG", "180")))
    except ValueError:
        return 180.0


def _refazer_1a_seg() -> float:
    """Prazo absoluto para a 1ª resposta chegar inteira (180 s é o mesmo teto por pedaço do stream normal)."""
    try:
        return max(0.0, float(os.environ.get("SETH_REFAZER_1A_SEG", "180")))
    except ValueError:
        return 180.0


_REFAZER_BYTES_PADRAO = 4 * 1024 * 1024
_PROGRESSO_S = 10.0  # (23/11/2026, Regra 0) comentário de progresso no SSE enquanto o gateway confere e refaz


def _refazer_bytes() -> int:
    """Teto de bytes por coleta de resposta (1ª e novas tentativas). Passou disso, a coleta para."""
    try:
        return max(0, int(os.environ.get("SETH_REFAZER_BYTES", str(_REFAZER_BYTES_PADRAO))))
    except ValueError:
        return _REFAZER_BYTES_PADRAO


def _proxima_fila_refazer(rota: str) -> str:
    """Escalada da nova tentativa: sobe uma fila pelo mapa _SUBIR_FILA (rapido -> livre -> pesado). Esse mapa, do
    resgate de resposta vazia, dá a volta (pesado -> livre); para refazer isso seria rebaixar, então o topo fica."""
    alvo = _Handler._SUBIR_FILA.get(rota)
    if rota in _REFAZER_ORDEM and alvo in _REFAZER_ORDEM and _REFAZER_ORDEM.index(alvo) > _REFAZER_ORDEM.index(rota):
        return alvo
    return rota


_RE_AUTORIZACAO = re.compile(r"(?i)\bauthorization\s*:[^\n|]*")
_RE_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")


def _sem_segredo(texto: str) -> str:
    """O achado sem segredo, para a nota: as réguas de segredo do sanitizador (a mesma lista de
    scripts/varredura_segredo.sh) e os cabeçalhos Authorization e Bearer, que a régua não cobre. Falha fechada: sem a
    régua, o detalhe do achado sai da nota."""
    try:
        import sanitizar  # noqa: E402  (redesign/router, mesmo diretório)
        regras = sanitizar._regras()
    except Exception:  # noqa: BLE001 -- sem a régua, nada do achado vai à nota
        return "[detalhe omitido: régua de segredo indisponível]"
    for _rotulo, _bruto, rx in regras:
        texto = rx.sub("[segredo removido]", texto)
    texto = _RE_AUTORIZACAO.sub("Authorization: [segredo removido]", texto)
    return _RE_BEARER.sub("Bearer [segredo removido]", texto)


def _nota_refazer(achados: list[str]) -> str:
    """A nota à nova tentativa: texto fixo e os achados da Máquina (curtos, sem segredo). Não leva a resposta
    nem o cabeçalho."""
    itens = " | ".join(_sem_segredo(a.strip())[:300] for a in achados[:8] if a.strip())
    return ("[Máquina, antes de entregar ao Humano: a sua resposta anterior foi conferida mecanicamente e tem estes "
            f"achados: {itens}. Refaça a resposta inteira corrigindo cada achado. Não cite esta nota e não peça "
            "desculpas. Se um achado não puder ser corrigido com o que está no contexto, diga isso em uma frase e "
            "escreva \"não medido\" onde faltar medição.]")


def _pedido_refazer(corpo: bytes, texto_ruim: str, achados: list[str], rota: str) -> bytes:
    """O mesmo pedido, com a resposta ruim e a nota no fim, na fila `rota`."""
    pl = json.loads(corpo)
    pl["messages"] = list(pl.get("messages") or []) + [
        {"role": "assistant", "content": texto_ruim},
        {"role": "user", "content": _nota_refazer(achados)}]
    pl["model"] = rota
    return json.dumps(pl, ensure_ascii=False).encode("utf-8")


def _texto_auditavel(bruto: bytes, sse: bool, nomes) -> str:
    """O texto que a verificação confere, como a entrega o mostraria: ferramenta escrita como texto vira chamada
    (então não sobra texto) e raciocínio sem resposta vira texto. Os mesmos passos do gateway, na mesma ordem."""
    if not sse:
        b = _resgate_json(bruto) if _resgate_ligado() else bruto
        if nomes:
            b = _tool_calls_do_json(b, nomes)
        try:
            return str(json.loads(b)["choices"][0]["message"].get("content") or "")
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            return ""
    if nomes and (conv := _sse_tool_calls(bruto, nomes)) is not None:
        bruto = conv
    texto = _texto_do_sse([bruto])
    if not texto.strip() and _resgate_ligado():
        estado: dict = {}
        for linha in bruto.split(b"\n"):
            _resgate_observar(linha, estado)
        resgate = _resgate_chunk(estado)
        if resgate:
            texto = _texto_do_sse([resgate])
    return texto


def _achados_do_texto(texto: str, msgs: list) -> list[str]:
    """Achados mecânicos de um texto (sem texto, sem achado). Verificação quebrada nunca segura a resposta."""
    if not texto.strip():
        return []
    try:
        return list(auditoria_turno.verificar_resposta_atual(texto, msgs) or [])
    except Exception:  # noqa: BLE001 -- como na entrega: falha da verificação não segura a resposta
        return []


# (23/11/2026, Humano: o uso guarda CÓDIGOS, nunca o texto) prefixo da frase de cada checagem -> código do achado. A frase
# pode trazer trecho da resposta; por isso só o código sai daqui.
_CODIGOS_ACHADO = (
    ("evidência: cita", "citacao_inventada"),
    ("estado desatualizado:", "estado_desatualizado"),
    ("estilo:", "estilo"),
    ("contagem de controles:", "controles"),
    ("cita controle inexistente:", "controles"),
    ("cabeçalho:", "cabecalho"),
    ("negou '", "negacao_contradita"),
    ("origem (F0):", "origem_f0"),
    ("ação afirmada sem chamada", "acao_sem_chamada"),
    ("opinião atribuída", "opiniao_sem_consulta"),
    ("cita caminho que não existe", "caminho_inexistente"),
)


# (23/11) letras do bloqueio_turno -> o mesmo vocabulário de nomes fixos
_CODIGOS_BLOQUEIO = {"a": "escrita_sem_ferramenta", "b": "saida_simulada", "c": "cabecalho_divergente"}


def _codigos_achados(achados) -> list[str]:
    """Códigos (rótulos fixos) dos achados da verificação: frase do auditoria (por prefixo), tupla (letra, descrição)
    do bloqueio (pela letra). Desconhecido = 'outro'. Só o código sai daqui, nunca a descrição."""
    out = []
    for a in achados or []:
        if isinstance(a, tuple):
            out.append(_CODIGOS_BLOQUEIO.get(a[0], "outro") if a and isinstance(a[0], str) else "outro")
            continue
        texto = a if isinstance(a, str) else ""
        out.append(next((c for prefixo, c in _CODIGOS_ACHADO if texto.startswith(prefixo)), "outro"))
    return out


def _bloqueio_ligado() -> bool:
    """SETH_BLOQUEIO_TURNO=0 desliga o bloqueio da verificação do turno (19/11/2026)."""
    return os.environ.get("SETH_BLOQUEIO_TURNO") != "0"


def _tem_tool_calls(bruto: bytes, sse: bool) -> bool:
    """A resposta chama ferramenta (estrutura OpenAI)? Então o texto que a acompanha é passo do meio, não resposta."""
    if not sse:
        try:
            return bool(json.loads(bruto)["choices"][0]["message"].get("tool_calls"))
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            return False
    for linha in bruto.split(b"\n"):
        if not linha.startswith(b"data:") or linha.strip() == b"data: [DONE]":
            continue
        try:
            for c in json.loads(linha[5:]).get("choices") or []:
                if (c.get("delta") or {}).get("tool_calls"):
                    return True
        except (ValueError, AttributeError, TypeError):
            continue
    return False


def _resposta_com_texto(bruto: bytes, sse: bool, texto: str, modelo: str | None) -> bytes:
    """A mesma resposta com o texto trocado (a resposta mínima honesta). No SSE: um chunk de texto, o fim e o [DONE]."""
    if sse:
        fim = {"id": "seth-verificacao", "object": "chat.completion.chunk", "created": 0, "model": modelo or "",
               "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
        return (_chunk_texto(texto, modelo or "") + b"data: " + json.dumps(fim).encode("utf-8") + b"\n\n"
                + b"data: [DONE]\n\n")
    try:
        o = json.loads(bruto)
        m = o["choices"][0]["message"]
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        o = {"model": modelo or "", "choices": [{"index": 0, "message": {"role": "assistant"}}]}
        m = o["choices"][0]["message"]
    m["content"] = texto
    for campo in ("tool_calls", "reasoning", "reasoning_content"):
        m.pop(campo, None)
    o["choices"][0]["finish_reason"] = "stop"
    return json.dumps(o, ensure_ascii=False).encode("utf-8")


def _pedido_correcao(corpo: bytes, texto_ruim: str, ach: list) -> bytes:
    """O mesmo pedido com a resposta retida e a nota da Máquina (só contexto do modelo, nunca ao Humano)."""
    pl = json.loads(corpo)
    pl["messages"] = list(pl.get("messages") or []) + [
        {"role": "assistant", "content": texto_ruim},
        {"role": "user", "content": _sem_segredo(bloqueio_turno.nota_correcao(ach))}]
    return json.dumps(pl, ensure_ascii=False).encode("utf-8")


def _consumir(leitor, prazo: float | None = None, limite: int | None = None) -> tuple[bytes, str]:
    """Lê o upstream até o fim. Devolve (o lido, motivo): "fim" (pedaço vazio); "prazo" (o prazo absoluto, em
    time.monotonic, chegou: para antes de ler de novo, mesmo com dados prontos, ou um pedaço não veio a tempo);
    "limite" (passou de `limite` bytes); "erro" (upstream caído). Sem prazo, cada pedaço espera até 180 s."""
    partes: list[bytes] = []
    total = 0
    while True:
        if prazo is None:
            espera = 180.0
        else:
            espera = prazo - time.monotonic()
            if espera <= 0:
                return b"".join(partes), "prazo"
        if limite is not None and total > limite:
            return b"".join(partes), "limite"
        try:
            pedaco = leitor.ler(min(espera, 180.0))
        except queue.Empty:
            return b"".join(partes), "prazo"
        except Exception:  # noqa: BLE001 -- upstream caído: a resposta não está completa
            return b"".join(partes), "erro"
        if not pedaco:
            return b"".join(partes), "fim"
        partes.append(pedaco)
        total += len(pedaco)


def _resposta_valida(bruto: bytes, sse: bool) -> bool:
    """Estrutura mínima para a resposta entrar na escolha: nunca uma candidata truncada ou malformada vence.
    JSON: parseia e tem choices[0].message com conteúdo, ferramenta ou raciocínio. SSE: termina de forma normal,
    com [DONE] ou com finish_reason de algum pedaço."""
    if not sse:
        try:
            m = json.loads(bruto)["choices"][0]["message"]
        except (ValueError, KeyError, IndexError, TypeError):
            return False
        if not isinstance(m, dict):
            return False
        c = m.get("content")
        r = m.get("reasoning") or m.get("reasoning_content")
        return ((isinstance(c, str) and c.strip() != "") or bool(m.get("tool_calls"))
                or (isinstance(r, str) and r.strip() != ""))
    for linha in bruto.split(b"\n"):
        if linha.strip() == b"data: [DONE]":
            return True
        if not linha.startswith(b"data:"):
            continue
        try:
            escolhas = json.loads(linha[5:]).get("choices") or []
        except (ValueError, AttributeError):
            continue
        if any(isinstance(ch, dict) and ch.get("finish_reason") for ch in escolhas):
            return True
    return False


_RE_CAB_LINHA = re.compile(r"^(?:\*\*)?agata(?:-seth)? · ", re.I)
_RE_CAB_RODAPE = re.compile(r"^\s*(?:\*\*)?\s*(?:última entrada\s*:|pronto\.|quebrado\s*:)", re.I)


def _cabecalho_unico_texto(texto: str, cab: str) -> str:
    """Item 2 (não-stream). Se o texto não começa com linha de cabeçalho, prefixa `cab` (o que a Máquina já calculou
    para o turno). Com SETH_CABECALHO_UNICO ligado (padrão), apaga cópia de cabeçalho SÓ no bloco inicial da resposta
    (cabeçalhos, rodapés e linhas em branco antes do 1º conteúdo), e só quando a cópia vem com o rodapé dela logo depois.
    Depois do 1º conteúdo (parágrafo, cerca de código, exemplo) nada é tocado. A 1ª linha de cabeçalho fica.
    Em SSE a remoção não roda (limite)."""
    if not texto.strip():
        return texto
    if not _RE_CAB_LINHA.match(texto.lstrip()):
        texto = cab + texto
    if not _cabecalho_unico_ligado():
        return texto
    linhas = texto.split("\n")
    saida, viu, i = [], False, 0
    while i < len(linhas):
        linha = linhas[i]
        if _RE_CAB_LINHA.match(linha.lstrip()):
            if not viu:
                viu = True
                saida.append(linha)
                i += 1
                continue
            if i + 1 < len(linhas) and _RE_CAB_RODAPE.match(linhas[i + 1]):
                i += 1
                while i < len(linhas) and _RE_CAB_RODAPE.match(linhas[i]):
                    i += 1
                continue
            break  # cabeçalho sem rodapé depois da 1ª linha: conteúdo do modelo, não cópia
        if _RE_CAB_RODAPE.match(linha) or not linha.strip():
            saida.append(linha)
            i += 1
            continue
        break  # 1º conteúdo: daqui para a frente o texto é do modelo
    saida.extend(linhas[i:])
    return "\n".join(saida)


def _cabecalho_unico_json(corpo: bytes, cab: str) -> bytes:
    """Item 2, resposta não-stream: aplica `_cabecalho_unico_texto` ao `content` da 1ª escolha, se houver texto."""
    try:
        o = json.loads(corpo)
        m = o["choices"][0]["message"]
        c = m.get("content")
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        return corpo
    if not isinstance(c, str) or not c.strip():
        return corpo
    novo = _cabecalho_unico_texto(c, cab)
    if novo == c:
        return corpo
    m["content"] = novo
    return json.dumps(o, ensure_ascii=False).encode("utf-8")


def _cabecalho_sse_tardio(linha: bytes, pendente: str) -> bytes | None:
    """Item 2, SSE. O cabeçalho que ficou pendente (a espiada não viu texto) sai antes do 1º chunk de TEXTO
    que chegar depois. None se a linha não é um chunk com texto, ou se não há pendente."""
    if not pendente or not linha.startswith(b"data:"):
        return None
    try:
        o = json.loads(linha[5:])
        ch = (o.get("choices") or [{}])[0]
        texto = (ch.get("delta") or {}).get("content")
    except (ValueError, AttributeError, IndexError, TypeError):
        return None
    if not isinstance(texto, str) or not texto.strip():
        return None
    ev = {"id": o.get("id"), "object": "chat.completion.chunk", "created": o.get("created"), "model": o.get("model"),
          "choices": [{"index": ch.get("index", 0), "delta": {"content": pendente}, "finish_reason": None}]}
    return b"data: " + json.dumps(ev, ensure_ascii=False).encode("utf-8") + b"\n\n"


_RE_TOOL_BLOCO = re.compile(r"\s*<tool_call>(.*?)</tool_call>", re.S)
_RE_TOOL_FUNCAO = re.compile(r"<function=([^>\s]+)\s*>(.*?)</function>", re.S)
_RE_TOOL_PARAM = re.compile(r"<parameter=([^>\s]+)\s*>(.*?)</parameter>", re.S)


def _nomes_de_tools(tools) -> frozenset:
    """Nomes das ferramentas do pedido, nos dois formatos: `{"type":"function","function":{"name":..}}` ou plano."""
    nomes = set()
    for t in tools if isinstance(tools, list) else []:
        if isinstance(t, dict):
            f = t.get("function") if isinstance(t.get("function"), dict) else t
            if isinstance(f.get("name"), str) and f["name"]:
                nomes.add(f["name"])
    return frozenset(nomes)


def _toolcall_texto_ligado() -> bool:
    """SETH_TOOLCALL_TEXTO=0 desliga só o item 3 (ferramenta escrita como texto). O cabeçalho não depende dela."""
    return os.environ.get("SETH_TOOLCALL_TEXTO", "1") != "0"


def _ferramentas_convertiveis(payload: dict, publica: bool) -> frozenset:
    """Nomes que podem virar tool_calls neste pedido. Vazio com SETH_TOOLCALL_TEXTO=0 e com tool_choice none (o teto de
    rodadas não pode virar laço). Na faixa pública (19/11/2026) só as ferramentas de dado público; antes, nenhuma."""
    if not _toolcall_texto_ligado() or payload.get("tool_choice") == "none":
        return frozenset()
    nomes = _nomes_de_tools(payload.get("tools"))
    if publica:
        maximo = ferramentas_confianca.dado_maximo(str(payload.get("model") or ""), True)
        nomes = frozenset(n for n in nomes if ferramentas_confianca.ferramenta_cabe(n, maximo))
    return nomes


def _valor_parametro(bruto: str):
    """Valor de <parameter=...>: o JSON, quando for JSON (número, bool, lista, objeto); senão o texto, sem as bordas."""
    s = bruto.strip()
    try:
        return json.loads(s)
    except ValueError:
        return s


def _chamadas_do_bloco(corpo: str) -> list | None:
    """(nome, argumentos) de cada chamada num bloco <tool_call>, só se o bloco inteiro é chamada bem formada: JSON
    {"name","arguments"}, ou o XML do Qwen (<function=NOME> com <parameter=CHAVE>VALOR</parameter>), sem nada solto
    fora dos elementos. None se sobra qualquer coisa."""
    s = corpo.strip()
    if s.startswith(("{", "[")):
        try:
            o = json.loads(s)
        except ValueError:
            return None
        pares = []
        for it in (o if isinstance(o, list) else [o]):
            if not isinstance(it, dict) or not isinstance(it.get("name"), str):
                return None
            args = it.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except ValueError:
                    return None
            if not isinstance(args, dict):
                return None
            pares.append((it["name"], args))
        return pares or None
    funcoes = list(_RE_TOOL_FUNCAO.finditer(s))
    if not funcoes or _RE_TOOL_FUNCAO.sub("", s).strip():
        return None
    pares = []
    for f in funcoes:
        if _RE_TOOL_PARAM.sub("", f.group(2)).strip():
            return None
        args = {p.strip(): _valor_parametro(v) for p, v in _RE_TOOL_PARAM.findall(f.group(2))}
        pares.append((f.group(1).strip(), args))
    return pares


_TAG_TOOL = "<tool_call>"
_RODAPES = ("última entrada:", "pronto.", "quebrado:")


def _pode_ser_cabecalho(parcial: str) -> bool:
    """Linha de cabeçalho ainda sem o fim da linha: começa como "agata" (** opcional). Até 300 caracteres."""
    s = parcial.lstrip().lstrip("*").lower()
    return len(s) <= 300 and ("agata".startswith(s) or s.startswith("agata"))


def _pode_ser_rodape(parcial: str) -> bool:
    """Linha do rodapé do cabeçalho ainda sem o fim da linha (prefixo de "Última entrada:", "pronto.", "quebrado:")."""
    s = parcial.strip().lstrip("*").strip().lower()
    return bool(s) and any(k.startswith(s) or s.startswith(k) for k in _RODAPES)


def _sem_cabecalho_inicial(texto: str) -> str:
    """Tira o cabeçalho que abre a resposta (o da Máquina ou a cópia que o modelo escreve), com o rodapé logo depois."""
    linhas = texto.lstrip().split("\n")
    i = 0
    if linhas and _RE_CAB_LINHA.match(linhas[0].lstrip()):
        i = 1
        while i < len(linhas) and _RE_CAB_RODAPE.match(linhas[i]):
            i += 1
    return "\n".join(linhas[i:])


_RE_CERCA_JSON = re.compile(r"\A```[ \t]*(?:json)?[ \t]*\n(.*?)\n?```\Z", re.S | re.I)
_RE_CERCA_JSON_INICIO = re.compile(r"```[ \t]*(?:json[ \t]*\n\s*|\n\s*)[\{\[]", re.I)
_RE_CERCA_JSON_PREFIXO = re.compile(r"```[ \t]*(?:j(?:s(?:o(?:n)?)?)?)?[ \t]*\n?\s*", re.I)
_CHAVES_CHAMADA = (frozenset({"name", "arguments"}), frozenset({"nome", "argumentos"}))


def _chamadas_do_json_cru(t: str, nomes) -> list | None:
    """(20/11) Chamada escrita como texto: o `t` inteiro é um objeto JSON (ou lista de objetos) cru, ou o mesmo JSON
    dentro de UMA cerca ```json (ou ```), nada fora dela. Cada objeto tem exatamente as chaves {name, arguments} ou
    {nome, argumentos} (argumentos: objeto ou string JSON de objeto), nome em `nomes`. Senão None."""
    m = _RE_CERCA_JSON.match(t)
    if m:
        t = m.group(1).strip()
        if "```" in t:
            return None
    if not t.startswith(("{", "[")):
        return None
    try:
        o = json.loads(t)
    except ValueError:
        return None
    pares = []
    for it in (o if isinstance(o, list) else [o]):
        if not isinstance(it, dict) or frozenset(it) not in _CHAVES_CHAMADA:
            return None
        nome = it.get("name", it.get("nome"))
        args = it.get("arguments", it.get("argumentos"))
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except ValueError:
                return None
        if not isinstance(nome, str) or nome not in nomes or not isinstance(args, dict):
            return None
        pares.append((nome, args))
    return pares or None


def _extrair_tool_calls(texto: str, nomes) -> list | None:
    """Regra estrita (revisão do Codex, 17/11): converte SÓ se o texto, sem o cabeçalho inicial (da Máquina ou do
    modelo) e sem espaços nas bordas, é feito EXCLUSIVAMENTE de um ou mais blocos <tool_call>...</tool_call> completos
    e bem formados, separados só por espaço em branco, com nomes em `nomes`. Qualquer outro caractere (texto, cerca,
    "Exemplo:", bloco sem fechar) => None: nada é convertido. Devolve as tool_calls no padrão OpenAI."""
    if not nomes or not isinstance(texto, str):
        return None
    t = _sem_cabecalho_inicial(texto).strip()
    chamadas, pos = [], 0
    if not t.startswith(_TAG_TOOL):
        pares = _chamadas_do_json_cru(t, nomes)
        if not pares:
            return None
        return [{"id": "call_" + os.urandom(4).hex(), "type": "function",
                 "function": {"name": n, "arguments": json.dumps(a, ensure_ascii=False)}} for n, a in pares]
    while True:
        m = _RE_TOOL_BLOCO.match(t, pos)
        if m is None:
            break
        pares = _chamadas_do_bloco(m.group(1))
        if not pares or _TAG_TOOL in m.group(1) or any(nome not in nomes for nome, _ in pares):
            return None
        for nome, args in pares:
            chamadas.append({"id": "call_" + os.urandom(4).hex(), "type": "function",
                             "function": {"name": nome, "arguments": json.dumps(args, ensure_ascii=False)}})
        pos = m.end()
    if not chamadas or t[pos:].strip():
        return None
    return chamadas


def _tool_calls_do_json(corpo: bytes, nomes) -> bytes:
    """Item 3, resposta não-stream: a 1ª escolha cujo content é SÓ blocos <tool_call> bem formados vira tool_calls
    (content vazio, finish_reason tool_calls). Qualquer outra coisa no content: devolve o corpo igual."""
    try:
        o = json.loads(corpo)
        if len(o["choices"]) != 1:
            return corpo  # (revisão r3) mais de uma escolha: não se converte
        ch = o["choices"][0]
        m = ch["message"]
        if ch.get("index", 0) != 0 or m.get("tool_calls") or not isinstance(m.get("content"), str):
            return corpo
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        return corpo
    chamadas = _extrair_tool_calls(m["content"], nomes)
    if chamadas is None:
        return corpo
    m["tool_calls"], m["content"] = chamadas, ""
    ch["finish_reason"] = "tool_calls"
    return json.dumps(o, ensure_ascii=False).encode("utf-8")


def _decisao_tool_call(buf: bytes) -> str:
    """Item 3, SSE, sobre o texto lido até agora. "sim": começa com <tool_call> (depois de um cabeçalho, se houver):
    lê-se até o fim do stream. "mais": ainda pode ser cabeçalho (a linha "agata" sem o fim, ou o rodapé dele), ou
    prefixo de <tool_call>, ou tem menos de 11 caracteres sem espaços: continua lendo. "nao": não pode ser ferramenta,
    segue o stream normal. Sem texto ainda (só keepalive): "nao", para o keepalive não ficar retido."""
    t = _texto_do_sse([buf]).lstrip()
    if not t:
        return "nao"
    if "\n" not in t and _pode_ser_cabecalho(t):
        return "mais"
    linhas = t.split("\n")
    i = 0
    if _RE_CAB_LINHA.match(linhas[0].lstrip()):
        i = 1
        while i < len(linhas) - 1 and (_RE_CAB_RODAPE.match(linhas[i]) or not linhas[i].strip()):
            i += 1
    if i >= 1 and i == len(linhas) - 1 and _pode_ser_rodape(linhas[i]):
        return "mais"
    resto = "\n".join(linhas[i:]).lstrip()
    if not resto:
        return "mais"
    if resto.startswith(_TAG_TOOL) or resto.startswith(("{", "[")):
        return "sim"  # (20/11) JSON cru: lê até o fim; o extrator decide, e se não converte o texto sai intacto
    if resto.startswith("```"):
        # (20/11) cerca: só retém se abre com JSON (```json ou ``` seguido de { ou [); cerca de código segue em stream
        if _RE_CERCA_JSON_INICIO.match(resto):
            return "sim"
        return "mais" if _RE_CERCA_JSON_PREFIXO.fullmatch(resto) else "nao"
    sem = "".join(resto.split())
    if _TAG_TOOL.startswith(sem) or len(sem) < len(_TAG_TOOL):
        return "mais"
    return "nao"


def _texto_inicia_tool_call(buf: bytes) -> bool:
    return _decisao_tool_call(buf) == "sim"


def _sse_tool_calls(buf: bytes, nomes) -> bytes | None:
    """Item 3, SSE com o stream inteiro no buffer. Converte só se: (a) o stream terminou como deve (viu [DONE] e um
    finish_reason do upstream); (b) o content inteiro é só blocos <tool_call> bem formados (_extrair_tool_calls); (c) o
    stream não traz tool_calls de verdade. Senão devolve None, e o stream passa como chegou."""
    partes, meta, viu_done, viu_finish = [], {}, False, False
    for linha in buf.split(b"\n"):
        if linha.strip() == b"data: [DONE]":
            viu_done = True
            continue
        if not linha.startswith(b"data:"):
            continue
        if any(m in linha for m in _Handler._SSE_KEEPALIVE):  # keepalive do OmniRoute: nem resposta nem metadado
            continue
        try:
            o = json.loads(linha[5:])
        except ValueError:
            continue
        if not isinstance(o, dict):
            continue
        escolhas = o.get("choices") or []
        if not isinstance(escolhas, list) or len(escolhas) > 1:
            return None  # (revisão r4) evento com mais de uma escolha: nem se acumula nem se converte (o index sozinho não basta)
        if any(isinstance(ch, dict) and ch.get("delta") for ch in escolhas):
            for k in ("id", "created", "model"):  # metadado só de chunk com delta real
                if o.get(k) is not None:
                    meta.setdefault(k, o[k])
        for ch in escolhas:
            if not isinstance(ch, dict) or ch.get("index", 0) != 0:
                return None  # (revisão r3) escolha diferente da 0: não se mistura o conteúdo, não se converte
            if ch.get("finish_reason"):
                viu_finish = True
            d = ch.get("delta") if isinstance(ch.get("delta"), dict) else {}
            if d.get("tool_calls"):
                return None
            if isinstance(d.get("content"), str):
                partes.append(d["content"])
    if not (viu_done and viu_finish):
        return None  # stream sem fim normal: não se fabrica o término
    chamadas = _extrair_tool_calls("".join(partes), nomes)
    if chamadas is None:
        return None

    def ev(delta, finish=None) -> bytes:
        o = {"id": meta.get("id", "seth-ferramenta"), "object": "chat.completion.chunk",
             "created": meta.get("created", 0), "model": meta.get("model", ""),
             "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
        return b"data: " + json.dumps(o, ensure_ascii=False).encode("utf-8") + b"\n\n"

    saida = [ev({"role": "assistant"})]
    saida += [ev({"tool_calls": [dict(c, index=i)]}) for i, c in enumerate(chamadas)]
    saida += [ev({}, "tool_calls"), b"data: [DONE]\n\n"]
    return b"".join(saida)


def _converter_sse_stream(buf: bytes, leitor, nomes):
    """Item 3, SSE: decide com o texto já lido e, se for ferramenta em texto, lê até o fim e converte. Devolve
    (bytes a enviar, leitor a usar depois). Converte só com o stream terminado (fim normal do upstream): prazo,
    erro, ou fim sem [DONE]/finish_reason, passam como chegaram."""
    completo, estado, fim, erro = buf, _decisao_tool_call(buf), False, False
    try:
        while not fim and estado == "mais":
            pedaco = leitor.ler(180)
            if not pedaco:
                fim = True
            else:
                completo += pedaco
                estado = _decisao_tool_call(completo)
        while not fim and estado == "sim":
            pedaco = leitor.ler(180)
            if not pedaco:
                fim = True
            else:
                completo += pedaco
    except Exception:  # noqa: BLE001 -- prazo (queue.Empty) ou upstream caído: nada de converter
        fim = erro = True
    saida = (_sse_tool_calls(completo, nomes) or completo) if (estado == "sim" and fim and not erro) else completo
    return saida, (_LeitorVazio() if fim else leitor)


class _LeitorVazio:
    """Substituto do _Leitor quando o stream já foi lido por inteiro (item 3, SSE): não espera nada."""
    _up = None

    def ler(self, timeout: float) -> bytes:
        return b""


def _pede_nao_registrar(h) -> bool:
    """(19/11/2026) `X-Agata-Nao-Registrar: 1` só vale vindo de loopback (canal de voz); qualquer outro valor ou origem
    = comportamento de sempre. Decidido por pedido, no do_POST."""
    try:
        origem = h.client_address[0]
    except (AttributeError, IndexError, TypeError):
        return False
    return (h.headers.get("X-Agata-Nao-Registrar") == "1"
            and origem in ("127.0.0.1", "::1", "::ffff:127.0.0.1"))


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    _rota = ""   # rota escolhida pelo classificador nesta requisição (observabilidade)
    _refazer = False   # verificar-e-refazer: só do_POST liga; GET e demais leem o padrão (fix 18/11)
    _verificar = False
    _cab_ctx = None  # (705) mensagens do pedido, se esta resposta leva o cabeçalho da Máquina
    _cab_injetado = None  # texto do cabeçalho que a Máquina injetou nesta resposta (cabeçalho único)
    _cab_estados = None
    _served_by = None  # (17/11, item 1) campo "model" do upstream nesta resposta; "?" no log se não houve
    _nomes_tools = frozenset()  # (17/11, item 3) ferramentas do pedido que podem virar tool_calls
    _public_only_lane = False  # (19/11) default de classe: GET e HEAD frios não têm o atributo de instância
    _fallback_corpo = None  # (18/11) corpo com a fila de sempre, se este pedido foi para uma rota local por tipo
    _nao_registrar = False  # (19/11) por pedido: X-Agata-Nao-Registrar: 1 vindo de loopback; o GET lê só este padrão
    _prazo_nuvem = False  # (19/11) o pedido foi para uma rota de nuvem por tipo: prazo próprio, não o da rota local
    _laya_rodou = False  # (23/11) o Laya decidiu a rota deste pedido (Agent e alias público)
    _rota_por = None  # (23/11) "laya" ou "regra": de onde saiu a rota (log de uso)
    _laya_conf = None  # (23/11) confiança do Laya, número ou None (log de uso)
    _perfil = None  # (23/11) perfil do pedido que vai ao modelo: req, tipo, classe, segredo
    _escolha = None  # (23/11) escolha por capacidade aplicada neste pedido, se houve
    _bloqueado = False  # (23/11) a verificação da Máquina barrou e a resposta mínima saiu (log de uso)
    _cap_sombra = False  # (23/11) o pedido entra na sombra de capacidade (não é utilitário nem continuação)
    _t_inicio = 0.0  # (23/11) início do pedido, para a latência do log de uso
    _achados_uso = None  # (23/11) códigos dos achados da 1ª resposta; None = não verificada (log de uso)
    _refeito = 0  # (23/11) refações feitas pela verificação neste pedido (log de uso)
    _corrigido = None  # (23/11) a entregue saiu sem achado; None = não verificada (log de uso)
    _progresso = None  # (23/11) etapa atual da conferência, para o comentário de progresso (SSE)
    _cabecalhos_ja_enviados = False  # (23/11) SSE com conferência: os cabeçalhos saíram antes da conferência
    _prazo_pedido = float("inf")  # (23/11) instante em que o teto total do pedido estoura
    _fn_parar = None  # (23/11) função que para o comentário de progresso, se ele estiver rodando
    _rota_no_cabecalho = None  # (23/11) rota que foi no cabeçalho X-Seth-Rota (para avisar a troca)

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        self._fallback_corpo = None  # keep-alive: um POST anterior nunca deixa corpo guardado para este pedido
        self._nao_registrar = False  # idem: o GET nunca herda o "não registrar" do POST anterior
        self._prazo_nuvem = False  # idem: nem o prazo de nuvem
        self._passar(b"", "GET")

    def do_HEAD(self):
        self._fallback_corpo = None
        self._nao_registrar = False
        self._prazo_nuvem = False
        self._passar(b"", "HEAD")

    def do_POST(self):
        # estado por REQUISIÇÃO: com keep-alive o mesmo handler atende vários
        # pedidos, e uma rota velha vazaria pro header X-Seth-Rota do seguinte
        self._rota = ""
        self._cab_ctx = None
        self._verificar = False
        self._refazer = False
        self._msgs_pedido = []
        self._texto_maquina = ""
        self._cab_injetado = None
        self._nomes_tools = frozenset()
        self._fallback_corpo = None
        self._prazo_nuvem = False
        self._data_classification = None
        self._public_only_lane = False
        self._laya_rodou = False
        self._rota_por = None
        self._laya_conf = None
        self._perfil = None
        self._escolha = None
        self._bloqueado = False
        self._cap_sombra = False
        self._t_inicio = time.monotonic()
        self._prazo_pedido = time.monotonic() + _pedido_teto_seg()  # (23/11) teto total do pedido
        self._fn_parar = None
        self._achados_uso = None
        self._refeito = 0
        self._corrigido = None
        self._progresso = None
        self._cabecalhos_ja_enviados = False
        self._reg = None
        self._aud = ""
        self._nao_registrar = _pede_nao_registrar(self)
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
                try:
                    agent_padrao = payload.get("model") == _ROTA_BASE  # só o alvo padrão do Agent pode ir a rota local
                    alias_publico = payload.get("model") == _ALIAS_PUBLICO
                    classificacao = self.headers.get("X-Agata-Data-Classification")
                    if classificacao is None:
                        classificacao = payload.get("agata_data_classification")
                    payload = _politica_dados_externos(
                        payload, classificacao
                    )
                    rota_local = str(payload.get("model", "")).startswith(_ROTAS_LOCAIS)
                    self._public_only_lane = not rota_local and (
                        alias_publico or classificacao == "public"
                    ) and not getattr(self.server, "_selftest_allow_context", False)
                    if classificacao == "public":
                        self._data_classification = "public"
                    elif payload.get("model") == _ROTA_BASE:
                        self._data_classification = "sanitizado-cascata"
                except DadosExternosSemClassificacao as e:
                    return self._erro(403, str(e))
                # roteador por complexidade: só o alvo "seth-livre" do Agent
                if payload.get("model") == _ROTA_BASE:
                    self._rota, laya = _rota_laya(payload)
                    self._laya_rodou = True
                    self._rota_por, self._laya_conf = _rota_laya_por(self._rota, laya)
                    self._cap_sombra = (not _e_chamada_utilitaria(payload)
                                        and not auditoria_turno.e_continuacao(payload.get("messages") or []))
                    # 1 decisão por resposta: no modo Agent os passos depois de
                    # ferramenta são a mesma resposta (664)
                    if self._cap_sombra:
                        _sombra_rota(payload, self._rota, laya)
                        # nova versão (Alexandria + metacognição): só registra o que faria (sombra)
                        if sombra_nova_versao.ligado():
                            sombra_nova_versao.registrar(payload, self._rota)
                    payload["model"] = self._rota
                # (697) sem tool_choice "required": o Nemotron (seth-pesado) passou a escrever a
                # chamada de ferramenta como TEXTO e a conversa travou (14/10, 15:26-15:28).
                msgs0 = payload.get("messages") if isinstance(payload.get("messages"), list) else []
                self._msgs_pedido = list(msgs0)
                self._verificar = (not self._public_only_lane and str(payload.get("model", "")).startswith("seth-")
                                   and not _e_chamada_utilitaria(payload))
                # (18/11/2026) decidido uma vez por pedido: o sorteio do canário não muda no meio da resposta
                self._refazer = bool(self._verificar and _refazer_ligado_neste_pedido())
                if (not self._public_only_lane and str(payload.get("model", "")).startswith("seth-")
                        and not _e_chamada_utilitaria(payload)
                        and not auditoria_turno._em_andamento(msgs0).strip()):
                    self._cab_ctx = list(msgs0)
                # Benchmark do roteamento (23/10/2026): pergunta do Humano + resposta em texto,
                # redigidas, fora do repositório, 30 dias. Só com SETH_REGISTRO_PEDIDOS=1.
                if (registro_pedidos.ligado() and not self._nao_registrar and not self._public_only_lane
                        and str(payload.get("model", "")).startswith("seth-")
                        and not _e_chamada_utilitaria(payload)):
                    self._reg = {"pergunta": registro_pedidos.ultima_pergunta(msgs0),
                                 "meta": {"continuacao": auditoria_turno.e_continuacao(msgs0)}}
                if self._public_only_lane:
                    try:
                        payload = _preparar_payload_publico(payload)
                    except DoutrinaIndisponivel as e:  # falha fechada: sem doutrina, a rota pública não responde
                        return self._erro(503, str(e))
                else:
                    payload = _injeta(payload)
                    _filtrar_por_confianca(payload, False)  # (19/11) só ferramenta cujo dado cabe no nível da rota
                self._aud = payload.pop("_agata_aud", "")
                # (17/11, item 3) ferramentas que podem virar tool_calls: nada na faixa pública, nada com tool_choice none
                # (o teto de rodadas põe none aqui dentro, em _injeta, por isso a leitura é depois)
                self._nomes_tools = _ferramentas_convertiveis(payload, self._public_only_lane)
                # (683) o LibreChat manda `user` (id do usuário); a API da Mistral
                # recusa campo a mais com 422 "Extra inputs are not permitted" --
                # Ministral e Codestral caíam sempre e a fila pulava para o próximo.
                # Campo opcional do OpenAI, nada no caminho o usa: sai aqui.
                payload.pop("user", None)
                longa = _fila_pela_janela(payload)
                if longa:
                    print(f"fila pela janela: {payload.get('model')} -> {longa}", file=sys.stderr, flush=True)
                    payload["model"] = longa
                    self._rota = longa
                # (23/11/2026) perfil do pedido que vai ao modelo: requisitos, tipo (a rota do Laya manda), classe pela
                # régua de dado pessoal sobre as falas recebidas e segredo. Alimenta a escolha por capacidade e o log de uso.
                try:
                    self._perfil = _perfil_do_pedido(payload, self._msgs_pedido,
                                                     _rota_classe(self._rota) if self._laya_rodou else None)
                except Exception:  # noqa: BLE001 -- perfil quebrado nunca derruba o pedido: sem escolha, sem log de uso
                    self._perfil = None
                corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                # Decisão do coordenador (18/11): a queda segura de pedido pessoal volta para a fila de sempre, que é a
                # regra de hoje. O proxy (sanitizar.sanitizar_payload) bloqueia SEGREDO; dado pessoal e nomes de projeto
                # não são varridos desde a decisão relaxa-pessoal (22/10). Segredo nem chega a rota local
                # (rotas_locais.tem_segredo).
                # (18/11/2026) rota local por tipo: a ficha assinada manda, o painel só restringe, Ollama fora = regra
                # de sempre. Guarda o corpo com a fila original para a queda segura em _passar.
                if agent_padrao and not self._public_only_lane and not _e_chamada_utilitaria(payload):
                    try:
                        local = rotas_locais.escolher(payload, rotas_locais.tipo_do_pedido(payload),
                                                      self._data_classification == "public")
                    except Exception:  # noqa: BLE001 -- escolha quebrada nunca derruba o pedido: regra de sempre
                        local = None
                    if local:
                        self._fallback_corpo = corpo
                        corpo = json.dumps(dict(payload, model=rotas_locais.modelo_no_gateway(local)),
                                           ensure_ascii=False).encode("utf-8")
                        print(f"rota local por tipo: {self._rota} -> {rotas_locais.modelo_no_gateway(local)}",
                              file=sys.stderr, flush=True)
                # (19/11/2026) rota de nuvem por tipo, SÓ na faixa pública (texto, sem ferramentas, sem segredo, pelo mesmo
                # sanitizador). A ficha assinada manda, o painel só restringe; falha de qualquer tipo = fila de sempre.
                # (19/11, ferramentas-confianca) a faixa pública mantém as ferramentas de dado público: com elas o tipo é
                # "ferramenta" e só uma rota de nuvem da ficha com esse tipo é escolhida; o payload segue com as ferramentas.
                if (self._public_only_lane and (agent_padrao or alias_publico) and rotas_locais.nuvem_ligada()
                        and not _e_chamada_utilitaria(payload) and self._fallback_corpo is None):
                    try:  # o tipo é do payload já público (só com ferramentas de dado público, se houver)
                        nuvem = rotas_locais.escolher_nuvem(payload, rotas_locais.tipo_do_pedido(payload))
                    except Exception:  # noqa: BLE001 -- escolha quebrada nunca derruba o pedido
                        nuvem = None
                    if nuvem:
                        self._fallback_corpo, self._prazo_nuvem = corpo, True
                        corpo = json.dumps(dict(payload, model=rotas_locais.nome_nuvem(nuvem)),
                                           ensure_ascii=False).encode("utf-8")
                        print(f"rota de nuvem por tipo: {self._rota} -> {rotas_locais.nome_nuvem(nuvem)}",
                              file=sys.stderr, flush=True)
                # (23/11/2026) escolha por capacidade (decisão do Humano, 16:40): o modelo concreto que o registro recomenda
                # para o tipo, só com nota >= PISO e amostra >= AMOSTRA_MIN. Sai pelo mesmo sanitizador (UPSTREAM). Rota local
                # e de nuvem da ficha já escolhidas mandam; falha ou prazo do concreto volta ao combo (_fallback_corpo).
                if (self._fallback_corpo is None and self._laya_rodou and self._perfil is not None
                        and not _e_chamada_utilitaria(payload)):
                    escolha = _escolha_capacidade(self._perfil, self._rota)
                    if escolha:
                        self._escolha = escolha
                        self._fallback_corpo = corpo
                        self._prazo_nuvem = not escolha["modelo"].startswith(_ROTAS_LOCAIS)
                        corpo = json.dumps(dict(payload, model=escolha["modelo"]), ensure_ascii=False).encode("utf-8")
                        print(f"escolha por capacidade: {self._rota} -> {escolha['modelo']} ({escolha['motivo']})",
                              file=sys.stderr, flush=True)
                # passos 3-4 do roteamento por capacidade: só registra a recomendação (sombra), com a escolha aplicada ou não
                if self._cap_sombra and self._perfil is not None and sombra_capacidade.ligado():
                    sombra_capacidade.registrar(payload, self._rota, _janelas_perfis(), req=self._perfil["req"],
                                                escolhida=(self._escolha or {}).get("modelo"))
        self._passar(corpo, "POST")

    def _enviar_cabecalhos(self, up, modelo_real) -> None:
        """Cabeçalhos da resposta ao cliente, uma vez por resposta. Com modelo_real, leva X-Modelo-Real."""
        self.send_response(up.status)
        for k, v in up.headers.items():
            if k.lower() not in _HOP_BY_HOP:
                self.send_header(k, v)
        if self._rota:
            self.send_header("X-Seth-Rota", self._rota)
        if self._nao_registrar:
            self.send_header("X-Agata-Registro", "nao")  # confirmação: este pedido não foi nem será registrado
        if modelo_real:
            self.send_header("X-Modelo-Real", modelo_real)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        self._cabecalhos_ja_enviados = True
        self._rota_no_cabecalho = self._rota

    def _escrever_comentario_sse(self, linha: str) -> None:
        """Um comentário SSE (linha que começa com ':') em bloco HTTP próprio. Só depois dos cabeçalhos."""
        dado = (linha + "\n\n").encode("utf-8")
        self.wfile.write(f"{len(dado):X}\r\n".encode() + dado + b"\r\n")

    def _encerrar_com_erro(self, msg: str) -> None:
        """(23/11) Fim de um stream que já abriu (200 com cabeçalhos): para o progresso, um evento SSE de erro curto, [DONE]
        e o terminador chunked. Nunca deixa a resposta truncada."""
        if self._fn_parar is not None:
            self._fn_parar()
        dado = ("data: " + json.dumps({"error": {"message": msg}}, ensure_ascii=False)
                + "\n\ndata: [DONE]\n\n").encode("utf-8")
        try:
            self.wfile.write(f"{len(dado):X}\r\n".encode() + dado + b"\r\n0\r\n\r\n")
        except OSError:
            pass
        self.close_connection = True

    def _etapa_progresso(self, etapa: str, tentativa: int, total: int) -> None:
        """Etapa real da conferência, para o comentário de progresso (coleta, conferindo, refazendo)."""
        self._progresso = {"etapa": etapa, "tentativa": tentativa, "total": total}

    def _linha_progresso(self, t0: float) -> str:
        p = self._progresso or {}
        return (f": agata {p.get('etapa', 'coletando')} · tentativa {p.get('tentativa', 1)}/{p.get('total', 1)} · "
                f"{int(time.monotonic() - t0)}s")

    def _iniciar_progresso(self, t0: float):
        """(23/11/2026, Regra 0) Comentários SSE a cada _PROGRESSO_S enquanto a conferência roda. Só depois dos cabeçalhos.
        São linhas de comentário: o cliente as ignora e o conteúdo entregue não muda. Devolve a função que para e espera
        o último comentário sair (a partir daí nada mais é escrito por este caminho)."""
        trava = threading.Lock()
        parar = threading.Event()

        def _emitir(linha: str) -> None:
            dado = (linha + "\n\n").encode("utf-8")
            with trava:
                if parar.is_set():
                    return
                self.wfile.write(f"{len(dado):X}\r\n".encode() + dado + b"\r\n")
                self.wfile.flush()

        def _bater() -> None:
            while not parar.wait(_PROGRESSO_S):
                try:
                    _emitir(self._linha_progresso(t0))
                except OSError:
                    return  # o cliente saiu: o fim do pedido trata

        th = threading.Thread(target=_bater, daemon=True)
        th.start()

        def _parar() -> None:
            with trava:
                parar.set()
            th.join(timeout=1.0)
        return _parar

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

    @classmethod
    def _modelo_de_bytes(cls, dado: bytes) -> str | None:
        """Primeiro campo "model" em `dado`, ou None se ausente ou só
        "keepalive" (sentinela do OmniRoute, nunca o modelo real)."""
        for m in cls._RE_MODELO.finditer(dado):
            nome = m.group(1).decode("utf-8", "replace")
            if nome != "keepalive":
                return nome
        return None

    def _log(self, msg: str, t0: float):
        """(682) Erro e desconexão vão para o journal (antes nada era registrado:
        uma resposta que morreu no meio não deixava rastro aqui)."""
        # (17/11, item 1) served_by = campo "model" que o upstream devolveu nesta resposta; "?" se não veio
        print(f"gateway: {msg} · rota={self._rota or '-'} · {time.monotonic() - t0:.1f}s · {self.path} · "
              f"served_by={self._served_by or '?'}", file=sys.stderr, flush=True)

    def _uso_do_pedido(self, status: int, modelo: str | None = None, entregue: bool = True) -> None:
        """(23/11/2026) Uma linha por pedido de chat que chegou ao cliente: modelo servido, tipo, classe, status, bloqueio,
        latência e a rota do Laya (classe, de onde saiu e confiança). Sem texto do pedido nem da resposta. Com `modelo`,
        é a linha de uma tentativa que falhou (o modelo pedido)."""
        perfil = self._perfil or {}
        if entregue:
            achados, refeito, corrigido = list(self._achados_uso or []), self._refeito, self._corrigido
        else:  # tentativa que não entregou nada: sem achado, sem refação, não verificada
            achados, refeito, corrigido = [], 0, None
        _gravar_uso(_linha_uso(
            modelo=self._served_by if modelo is None else modelo, tipo=perfil.get("tipo"), classe=perfil.get("classe"),
            status=int(status), achados=achados, refeito=refeito, corrigido=corrigido,
            bloqueado=self._bloqueado, latencia_ms=int((time.monotonic() - self._t_inicio) * 1000),
            rota=_rota_classe(self._rota), rota_por=self._rota_por if self._laya_rodou else None,
            laya_confianca=self._laya_conf if self._laya_rodou else None))

    def _uso_de_falha(self, status: int, corpo: bytes, metodo: str) -> None:
        """(23/11/2026) Tentativa que não entregou resposta útil (HTTP de erro, queda, timeout ou resposta vazia; com ou
        sem fallback) e erro final do gateway (502/504): uma linha do modelo PEDIDO, com o status (0 = sem resposta útil).
        Assim o uso registra a falha do concreto, da rota local e da nuvem, além do que foi servido."""
        if metodo != "POST" or self._perfil is None or "/chat/completions" not in self.path:
            return
        self._uso_do_pedido(status, modelo=_modelo_do_corpo(corpo), entregue=False)

    # (695) 200 sem texto nem ferramenta (Gemini, 14/10 15:00:12: "succeeded" em 2,4 s e o
    # LibreChat gravou resposta vazia). Nada foi enviado ao cliente ainda: tenta 1 vez a
    # fila seguinte. Só nas filas da Seth; o resto passa como veio.
    _SUBIR_FILA = {"seth-rapido": "seth-livre", "seth-livre": "seth-pesado", "seth-pesado": "seth-livre"}
    # (709) Sem conteúdo no prazo = provedor pendurado (cota, fila): o destino é a fila MAIS
    # RÁPIDA, não a mais forte -- no teste 1, subir para seth-pesado custou mais 97 s.
    _FILA_RAPIDA = {"seth-livre": "seth-rapido", "seth-pesado": "seth-rapido", "seth-rapido": "seth-livre"}

    @staticmethod
    def _tem_conteudo(dado: bytes, sse: bool) -> bool:
        def util(o) -> bool:
            for c in (o.get("choices") or []) if isinstance(o, dict) else []:
                m = c.get("delta") or c.get("message") or {}
                if (m.get("content") or "").strip() or m.get("tool_calls"):
                    return True
            return False
        if not sse:
            try:
                return util(json.loads(dado))
            except ValueError:
                return True  # não é JSON de chat: não é "vazio", passa
        for linha in dado.split(b"\n"):
            if linha.startswith(b"data:") and not linha.startswith(b"data: [DONE]"):
                try:
                    if util(json.loads(linha[5:])):
                        return True
                except ValueError:
                    continue
        return False

    def _cabecalhos_upstream(self) -> dict:
        """Cabeçalhos da chamada ao sanitizador, como em _passar. Sem Content-Length: o corpo pode ter mudado."""
        headers = {k: v for k, v in self.headers.items() if k.lower() not in _HOP_BY_HOP}
        headers["X-Agata-Token"] = _token_interno()
        if getattr(self, "_data_classification", None) in ("public", "sanitizado-cascata"):
            headers["X-Agata-Data-Classification"] = self._data_classification
        return headers

    def _refazer_chamada(self, corpo: bytes, sse: bool, prazo: float):
        """Uma nova tentativa ao upstream, pelo mesmo caminho. Devolve (bytes, modelo) da resposta completa e com
        conteúdo, ou None: erro, HTTP diferente de 200, tipo de resposta diferente, vazia ou prazo estourado."""
        restante = prazo - time.monotonic()
        if restante <= 0:
            return None
        try:
            req = urllib.request.Request(UPSTREAM + self.path, data=corpo, method="POST",
                                         headers=self._cabecalhos_upstream())
            up = urllib.request.urlopen(req, timeout=min(180.0, restante))  # nem a conexão passa do teto
        except Exception:  # noqa: BLE001 -- falha da nova tentativa: fica a melhor resposta até aqui
            return None
        try:
            e_sse = "text/event-stream" in (up.headers.get("Content-Type") or "").lower()
            if up.status != 200 or e_sse != sse:
                return None
            bruto, motivo = _consumir(_Leitor(up), prazo, _refazer_bytes())
            # candidata só entra se chegou ao fim, tem conteúdo e estrutura válida (truncada ou malformada não vence)
            if motivo != "fim" or not self._tem_conteudo(bruto, sse) or not _resposta_valida(bruto, sse):
                return None
            return bruto, self._modelo_de_bytes(bruto)
        except Exception:  # noqa: BLE001 -- uma tentativa ruim nunca derruba a resposta
            return None
        finally:
            _derrubar(up)

    def _refazer_antes_de_entregar(self, corpo: bytes, buf: bytes, leitor, sse: bool, modelo, t0: float):
        """Verificar e refazer ANTES de a resposta sair (18/11/2026). Lê a 1ª resposta até o fim e confere o texto
        que a entrega conferiria. Enquanto houver achado, chama o upstream de novo (até SETH_REFAZER_MAX tentativas
        ou SETH_REFAZER_SEG segundos, contados daqui) com o mesmo pedido mais a resposta ruim e a nota dos achados,
        numa fila acima quando houver (_proxima_fila_refazer). Devolve (bytes, leitor, modelo) da resposta a
        entregar: a de menos achados. O gate de entrega confere de novo e põe a Verificação da Máquina se sobrar."""
        # o teto de bytes vale para a resposta inteira: a pré-leitura (espreita do stream, ou o corpo do JSON) conta,
        # e a coleta seguinte só recebe o que sobra (r2, achado 1). Passou: não audita nem refaz.
        limite = _refazer_bytes()
        if len(buf) > limite:
            self._log("verificar e refazer: 1ª resposta passou do limite (limite), seguiu sem refazer", t0)
            return buf, leitor, modelo
        self._etapa_progresso("coletando", 1, _refazer_max() + 1)  # (23/11) progresso: a 1ª resposta sendo coletada
        if sse:
            # a 1ª coleta tem prazo absoluto próprio (não o da refazer): quem manda keepalive sem parar não prende o
            # pedido nem enche a memória
            resto, motivo = _consumir(leitor, min(time.monotonic() + _refazer_1a_seg(), self._prazo_pedido),
                                      limite - len(buf))
            buf = buf + resto
            if motivo == "erro":
                self._log("verificar e refazer: 1ª resposta com erro no upstream, entregue como veio", t0)
                return buf, _LeitorVazio(), modelo
            if motivo != "fim":
                # prazo ou bytes estourados: a coleta para aqui e o resto segue pelo caminho legado, sem refazer
                self._log(f"verificar e refazer: 1ª resposta passou do limite ({motivo}), seguiu sem refazer", t0)
                return buf, leitor, modelo
            leitor = _LeitorVazio()
        if not _resposta_valida(buf, sse):
            self._log("verificar e refazer: 1ª resposta sem estrutura válida, entregue como veio", t0)
            return buf, leitor, modelo
        try:
            rota0 = str(json.loads(corpo).get("model") or "")
        except (ValueError, AttributeError):
            return buf, leitor, modelo
        nomes, msgs = self._nomes_tools, self._msgs_pedido
        texto = _texto_auditavel(buf, sse, nomes)
        cands = [(buf, rota0, modelo, texto, _achados_do_texto(texto, msgs))]
        inicio, teto, maximo, n = time.monotonic(), _refazer_seg(), _refazer_max(), 0
        atual = cands[0]
        self._etapa_progresso("conferindo", 1, maximo + 1)  # (23/11) progresso: conferindo a 1ª resposta
        while atual[4] and n < maximo and time.monotonic() - inicio < teto and time.monotonic() < self._prazo_pedido:
            n += 1
            rota = _proxima_fila_refazer(atual[1])
            self._etapa_progresso("refazendo", n + 1, maximo + 1)  # (23/11) progresso: uma nova tentativa
            nova = self._refazer_chamada(_pedido_refazer(corpo, atual[3], atual[4], rota), sse,
                                         min(inicio + teto, self._prazo_pedido))
            if nova is None:
                break
            bruto, modelo_n = nova
            texto_n = _texto_auditavel(bruto, sse, nomes)
            atual = (bruto, rota, modelo_n, texto_n, _achados_do_texto(texto_n, msgs))
            cands.append(atual)
        melhor = min(cands, key=lambda c: len(c[4]))  # empate: a mais antiga, a 1ª resposta
        if melhor[1] != rota0:
            self._rota = melhor[1]
        self._achados_uso = _codigos_achados(cands[0][4])  # (23/11) códigos da 1ª resposta, sem texto
        self._refeito = n
        self._corrigido = not melhor[4]
        self._served_by = melhor[2]
        self._log(f"refazer_tentativas={n} achados_inicio={len(cands[0][4])} achados_fim={len(melhor[4])}", t0)
        return melhor[0], leitor, melhor[2]

    def _bloquear_antes_de_entregar(self, corpo: bytes, buf: bytes, leitor, sse: bool, modelo, t0: float):
        """Bloqueio no lugar de aviso (19/11/2026). Lê a resposta inteira e aplica bloqueio_turno: escrita afirmada sem
        ferramenta de escrita bem-sucedida, saída de ferramenta simulada, cabeçalho duplicado ou de outro modelo. Com
        achado, devolve ao modelo UMA vez (nota só no contexto dele); se persistir, entrega a resposta mínima honesta.
        Resposta que chama ferramenta passa. Devolve (bytes, leitor, modelo)."""
        limite = _refazer_bytes()

        def nao_conferida(motivo_):
            # falha fechada (19/11, revisão do Codex): o que não deu para conferir inteiro NÃO sai. Resposta que chama
            # ferramenta é passo do meio e passa; texto vira a resposta mínima honesta.
            if _tem_tool_calls(buf, sse):
                return buf, leitor, modelo
            self._log(f"bloqueio_turno: resposta não conferida ({motivo_}) -> resposta mínima", t0)
            self._bloqueado = True  # (23/11) log de uso: a resposta mínima saiu no lugar da do modelo
            self._corrigido = False
            return (_resposta_com_texto(buf, sse, bloqueio_turno.resposta_longa_demais(), modelo),
                    _LeitorVazio(), modelo)

        if len(buf) > limite:
            return nao_conferida("limite")
        if sse:
            resto, motivo = _consumir(leitor, min(time.monotonic() + _refazer_1a_seg(), self._prazo_pedido),
                                      limite - len(buf))
            buf = buf + resto
            if motivo != "fim":
                return nao_conferida(motivo)  # prazo, teto de bytes ou upstream caído no meio
            leitor = _LeitorVazio()
        if not _resposta_valida(buf, sse):
            return buf, leitor, modelo
        nomes, msgs = self._nomes_tools, self._msgs_pedido

        def avaliar(bruto, mod):
            if _tem_tool_calls(bruto, sse):
                return "", []
            texto = _texto_auditavel(bruto, sse, nomes)
            return texto, bloqueio_turno.achados(texto, msgs, mod)

        self._etapa_progresso("conferindo", 1, 2)  # (23/11) progresso: conferindo o texto que sairia
        texto, ach = avaliar(buf, modelo)
        if not ach:
            if self._achados_uso is None:
                self._achados_uso = []  # (23/11) verificada e sem achado
            if self._corrigido is None:  # (23/11) sem o refazer, esta verificação diz se saiu sem achado; com ele, vale o dele
                self._corrigido = True
            return buf, leitor, modelo
        cods = "".join(c for c, _ in ach)
        # (23/11) códigos do bloqueio somados aos do refazer (sem repetir): cada verificador pode achar o que o outro não viu
        self._achados_uso = list(dict.fromkeys((self._achados_uso or []) + _codigos_achados(ach)))
        self._corrigido = False  # (23/11) o texto que sairia tem achado
        if time.monotonic() >= self._prazo_pedido:  # (23/11) teto do pedido estourado: sai a 1ª resposta, com o aviso
            self._log("bloqueio_turno: teto do pedido estourado -> 1ª resposta com aviso da Máquina", t0)
            return buf, leitor, modelo
        nova = None
        self._etapa_progresso("refazendo", 2, 2)  # (23/11) progresso: uma correção pedida ao modelo
        try:
            self._refeito += 1  # (23/11) uma correção pedida ao modelo
            nova = self._refazer_chamada(_pedido_correcao(corpo, texto, ach), sse,
                                         min(time.monotonic() + _refazer_seg(), self._prazo_pedido))
        except Exception:  # noqa: BLE001 -- a nova tentativa nunca derruba a resposta
            nova = None
        if nova is not None:
            bruto_n, modelo_n = nova
            texto_n, ach_n = avaliar(bruto_n, modelo_n)
            if not ach_n:
                self._served_by = modelo_n
                self._corrigido = True
                self._log(f"bloqueio_turno: achados={cods} corrigido_na_2a", t0)
                return bruto_n, leitor, modelo_n
            ach, modelo = ach_n, modelo_n
        self._bloqueado = True  # (23/11) log de uso: a resposta mínima saiu no lugar da do modelo
        self._corrigido = False
        self._log(f"bloqueio_turno: achados={cods} persistiu -> resposta mínima", t0)
        return _resposta_com_texto(buf, sse, bloqueio_turno.resposta_minima(ach), modelo), leitor, modelo

    def _passar(self, corpo: bytes, metodo: str, tentativa: int = 0):
        t0 = time.monotonic()
        if metodo != "POST":
            self._fallback_corpo = None
        self._served_by = None  # (17/11, item 1) por tentativa: a nova tentativa põe o modelo da sua resposta
        self._cabecalhos_ja_enviados = False  # (23/11) por tentativa
        url = UPSTREAM + self.path
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in _HOP_BY_HOP}
        headers["X-Agata-Token"] = _token_interno()
        if getattr(self, "_data_classification", None) in ("public", "sanitizado-cascata"):
            headers["X-Agata-Data-Classification"] = self._data_classification
        req = urllib.request.Request(url, data=corpo or None, method=metodo, headers=headers)
        try:
            # (19/11/2026) rota de nuvem: prazo ABSOLUTO contado daqui (headers, 1º conteúdo e corpo JSON dentro dele)
            if self._prazo_nuvem and self._fallback_corpo is not None:
                limite_nuvem = t0 + _rota_nuvem_seg()
                tmo = max(0.05, limite_nuvem - time.monotonic())
            else:
                limite_nuvem = None
                tmo = _rota_local_seg() if self._fallback_corpo is not None else 180
            up = urllib.request.urlopen(req, timeout=tmo)
        except urllib.error.HTTPError as e:
            up = e
            # (17/11, item 4) o 429 nasce no OmniRoute (cota e circuit breaker de cada provedor), não numa escolha do
            # gateway: aqui só se mede, com a fila que o gateway pediu e o modo. Nenhuma pausa é aplicada.
            marca = (f" · 429_pausaria={self._rota} · roteador={_modo_roteador()}"
                     if e.code == 429 and self._rota in self._SUBIR_FILA else "")
            self._log(f"upstream HTTP {e.code}{marca}", t0)
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as e:
            self._log(f"upstream inacessível ({e})", t0)
            if self._fallback_corpo is not None and metodo == "POST":  # (18/11) rota local sem conexão/timeout: fila de sempre
                self._uso_de_falha(0, corpo, metodo)  # (23/11) a tentativa que caiu entra no uso, com status 0
                fb, self._fallback_corpo = self._fallback_corpo, None
                return self._passar(fb, metodo, tentativa)
            self._uso_de_falha(502, corpo, metodo)  # (23/11) erro final do gateway entra no uso
            return self._erro(502, f"upstream ({UPSTREAM}) inacessível: {e}. "
                                   "Suba o sanitizador: systemctl --user start omniroute-sanitizer omniroute")
        if up.status >= 400 and self._fallback_corpo is not None and metodo == "POST":
            # (18/11/2026) queda segura: a rota local falhou (modelo ausente, Ollama parou no meio): fila de sempre
            fb, self._fallback_corpo = self._fallback_corpo, None
            self._log(f"rota local falhou (HTTP {up.status}) -> fila de sempre", t0)
            self._uso_de_falha(up.status, corpo, metodo)  # (23/11) a tentativa com erro entra no uso
            _derrubar(up)
            return self._passar(fb, metodo, tentativa)
        sse = "text/event-stream" in (up.headers.get("Content-Type") or "").lower()
        modelo_real = None
        buf_pre = b""
        leitor = None
        try:
            if sse:
                # Espia os primeiros pedaços (sem enviar nada ao cliente ainda --
                # headers não foram mandados) até achar o "model" real ou esgotar
                # o limite; o que foi lido entra no stream normal depois, intacto.
                # (695) espia até o 1º conteúdo útil, não só até o "model": sem isso
                # não dá para saber, antes de responder, se a resposta veio vazia.
                fim = sem_conteudo = False
                leitor = _Leitor(up)
                # (19/11/2026) rota de nuvem por tipo: prazo ABSOLUTO até o 1º conteúdo útil (keep-alives não o renovam);
                # estourou = sem conteúdo = queda segura para a fila de sempre.
                nuvem_ativa = limite_nuvem is not None
                prazo = limite_nuvem if nuvem_ativa else time.monotonic() + PRAZO_1O_CONTEUDO
                while True:
                    try:
                        pedaco = leitor.ler(prazo - time.monotonic())
                    except queue.Empty:
                        sem_conteudo = up.status == 200  # (709) só keepalive até o prazo
                        break
                    if not pedaco:
                        fim = True
                        break
                    buf_pre += pedaco
                    modelo_real = modelo_real or self._modelo_de_bytes(buf_pre)
                    if modelo_real and self._tem_conteudo(buf_pre, True):
                        break
                    if (self._refazer or nuvem_ativa) and time.monotonic() >= prazo:
                        # (18/11/2026) keepalive sem parar: com dados sempre prontos o Empty nunca vem e o prazo
                        # acima não sai. Só no caminho de refazer; o legado segue como estava.
                        sem_conteudo = up.status == 200
                        break
                vazio = (fim and up.status == 200 and not self._tem_conteudo(buf_pre, True)) or sem_conteudo
            else:
                if limite_nuvem is not None:  # JSON devagar: leitura com prazo absoluto; estourou = queda segura
                    lei, buf_pre = _Leitor(up), b""
                    while True:
                        try:
                            ped = lei.ler(limite_nuvem - time.monotonic())
                        except queue.Empty:
                            _derrubar(up)  # a thread do _Leitor volta na hora; close() esperaria a leitura presa
                            raise TimeoutError("rota de nuvem estourou o prazo no corpo") from None
                        if not ped:
                            break
                        buf_pre += ped
                else:
                    buf_pre = up.read()
                modelo_real = self._modelo_de_bytes(buf_pre)
                vazio = up.status == 200 and not self._tem_conteudo(buf_pre, False)
            self._served_by = modelo_real  # (17/11, item 1)
            if vazio and self._fallback_corpo is not None and metodo == "POST":
                fb, self._fallback_corpo = self._fallback_corpo, None
                self._log(f"rota local sem conteúdo (modelo {modelo_real or '?'}) -> fila de sempre", t0)
                self._uso_de_falha(0, corpo, metodo)  # (23/11) resposta vazia: sem resposta útil, status 0
                _derrubar(up)
                return self._passar(fb, metodo, tentativa)
            if vazio and tentativa == 0 and self._rota in self._SUBIR_FILA:
                try:
                    pl = json.loads(corpo)
                    destino = self._FILA_RAPIDA if (sse and sem_conteudo) else self._SUBIR_FILA
                    pl["model"] = self._rota = destino[self._rota]
                except ValueError:
                    pl = None
                if pl is not None:
                    motivo = (f"sem conteúdo em {PRAZO_1O_CONTEUDO:.0f} s" if sse and sem_conteudo
                              else "resposta vazia")
                    self._log(f"{motivo} (modelo {modelo_real or '?'}) -> nova tentativa", t0)
                    _derrubar(up)
                    return self._passar(json.dumps(pl, ensure_ascii=False).encode("utf-8"), metodo, 1)
        except (BrokenPipeError, ConnectionResetError):
            self._log("cliente desconectou antes da 1ª resposta do modelo", t0)
            self.close_connection = True
            up.close()
            return
        except (TimeoutError, OSError, http.client.HTTPException) as e:  # HTTPException: IncompleteRead (corpo cortado)
            self._log(f"upstream parou de responder ({e})", t0)
            if limite_nuvem is not None:
                _derrubar(up)  # nuvem: nunca esperar a leitura presa
            else:
                up.close()
            if self._fallback_corpo is not None and metodo == "POST":  # (18/11) rota local pendurada: fila de sempre
                self._uso_de_falha(0, corpo, metodo)  # (23/11) a tentativa que travou entra no uso, com status 0
                fb, self._fallback_corpo = self._fallback_corpo, None
                return self._passar(fb, metodo, tentativa)
            self._uso_de_falha(504, corpo, metodo)  # (23/11) erro final do gateway entra no uso
            return self._erro(504, f"upstream parou de responder: {e}")
        # (18/11/2026, verificar e refazer) antes de qualquer byte ao cliente: lê a resposta inteira, confere e, com
        # achado, refaz (SETH_REFAZER). Desligado, segue o caminho de sempre, abaixo.
        # (23/11/2026, Regra 0) SSE com conferência: os cabeçalhos saem ANTES da coleta e da conferência, e um comentário
        # de progresso (": agata ...") sai a cada _PROGRESSO_S até a resposta estar conferida. O conteúdo não muda: sai depois.
        conferindo = (sse and metodo == "POST" and up.status == 200 and "/chat/completions" in self.path and (
            (self._refazer and self._verificar and _verificacao_ligada())
            or ((self._verificar or self._public_only_lane) and _bloqueio_ligado())))
        parar_progresso = None
        if conferindo:
            try:
                self._enviar_cabecalhos(up, None)  # sem X-Modelo-Real: o modelo final só se sabe depois da conferência
            except (BrokenPipeError, ConnectionResetError):
                self.close_connection = True
                up.close()
                return
            parar_progresso = self._iniciar_progresso(t0)
            self._fn_parar = parar_progresso
        try:
            if self._refazer and self._verificar and metodo == "POST" and up.status == 200 and _verificacao_ligada():
                # (r4) se a espreita já leu o EOF (fim), o leitor não tem mais nada e não manda outro: a coleta não pode
                # esperar nele (180 s por padrão) nem registrar um limite de prazo falso. Vale um leitor vazio.
                buf_pre, leitor, modelo_real = self._refazer_antes_de_entregar(
                    corpo, buf_pre, _LeitorVazio() if (sse and fim) else leitor, sse, modelo_real, t0)
            # (19/11/2026) bloqueio no lugar de aviso: vale com ou sem SETH_REFAZER, em toda rota seth-* verificada e na faixa
            # pública (onde há ferramenta de dado público e nenhuma de escrita). SETH_BLOQUEIO_TURNO=0 desliga.
            # (a ordem importa: GET e HEAD não passam por do_POST, que é quem põe _verificar e _public_only_lane)
            if (metodo == "POST" and up.status == 200 and (self._verificar or self._public_only_lane)
                    and _bloqueio_ligado() and "/chat/completions" in self.path):
                buf_pre, leitor, modelo_real = self._bloquear_antes_de_entregar(
                    corpo, buf_pre, _LeitorVazio() if (sse and fim) else leitor, sse, modelo_real, t0)
        except Exception as e:  # noqa: BLE001 -- (23/11) falha da conferência: fecha o stream, não o deixa truncado
            if not self._cabecalhos_ja_enviados:
                raise
            print(f"gateway: conferência falhou depois dos cabeçalhos ({e.__class__.__name__}) -> fim do stream com erro",
                  file=sys.stderr, flush=True)
            self._uso_de_falha(500, corpo, metodo)
            self._encerrar_com_erro("a conferência da resposta falhou; tente de novo")
            return
        finally:
            if parar_progresso is not None:
                parar_progresso()
        if sse and up.status == 200 and self._nomes_tools and leitor is not None:
            # (17/11, item 3, SSE) decide, lê até o fim se for ferramenta em texto, e só converte com o stream
            # terminado: senão o stream passa como chegou
            buf_pre, leitor = _converter_sse_stream(buf_pre, leitor, self._nomes_tools)
        if up.status == 200 and not sse and _resgate_ligado():
            buf_pre = _resgate_json(buf_pre)
        if up.status == 200 and not sse and self._nomes_tools:
            buf_pre = _tool_calls_do_json(buf_pre, self._nomes_tools)  # (17/11, item 3)
        if self._cab_ctx is not None and up.status == 200:
            cab = _cabecalho_maquina(self._cab_ctx, modelo_real) + "\n\n"
            texto_maquina = cab + _correcao_da_maquina(getattr(self, "_aud", "") or "")
            # (revisão 17/11, achado 4) o filtro do cabeçalho do modelo compara com o texto INTEIRO que a Máquina injetou
            self._cab_injetado = texto_maquina
            self._texto_maquina = texto_maquina
            self._cab_pendente = ""
            if sse:
                novo = _injetar_sse(buf_pre, texto_maquina)
                if novo is not None:
                    buf_pre = novo
                else:
                    self._cab_pendente = texto_maquina  # vai junto se o resgate do raciocínio acontecer
            else:
                try:
                    o = json.loads(buf_pre)
                    m = o["choices"][0]["message"]
                    if (m.get("content") or "").strip() and _verificacao_ligada() and self._verificar:
                        try:
                            _ach = auditoria_turno.verificar_resposta_atual(m["content"], self._msgs_pedido)
                        except Exception:  # noqa: BLE001
                            _ach = []
                        if not m.get("tool_calls") and _guarda_bloqueia(m["content"], self._msgs_pedido):
                            import guarda as _g  # noqa: E402  (lote 5, A3: recusa no lugar da resposta)
                            m["content"] = _g.RECUSA
                            self._bloqueado = True  # (23/11) log de uso: a recusa da Máquina saiu no lugar da resposta
                            _ach = []
                        if _ach:
                            m["content"] = m["content"] + _bloco_verificacao(_ach)
                    if (m.get("content") or "").strip():
                        m["content"] = texto_maquina + m["content"]
                        buf_pre = json.dumps(o, ensure_ascii=False).encode("utf-8")
                except (ValueError, KeyError, IndexError, TypeError):
                    pass
        self._emoji_estados = {}
        self._modelo_para_log = modelo_real
        if up.status == 200 and not sse and _emoji_ligado():
            buf_pre, _rem = limpa_emoji.limpar_json(buf_pre)
            _registrar_emoji(self._rota, modelo_real, _rem)
        if up.status == 200 and not sse and self._cab_injetado and _cabecalho_unico_ligado():
            buf_pre, _nc = limpa_cabecalho.limpar_json(buf_pre, self._cab_injetado)
            _registrar_cabecalho(self._rota, modelo_real, _nc)
        if up.status == 200 and not sse and self._cab_injetado:
            buf_pre = _cabecalho_unico_json(buf_pre, self._cab_injetado)  # (17/11, item 2): prefixo e duplicata
        if not self._cabecalhos_ja_enviados:
            self._enviar_cabecalhos(up, modelo_real)
        if modelo_real:
            _lembrar_modelo_real(modelo_real)
        try:
            if sse and modelo_real:
                # (23/11/2026) o modelo servido vai num comentário SSE antes do conteúdo: o painel converte; os clientes
                # ignoram. Substitui o X-Modelo-Real nas respostas com conferência (cabeçalhos saem antes da conferência).
                self._escrever_comentario_sse(f": agata modelo {modelo_real}")
            if sse and self._rota and self._rota != self._rota_no_cabecalho:
                # (23/11) a rota mudou depois do cabeçalho X-Seth-Rota (refazer ou troca de fila): avisa no stream
                self._escrever_comentario_sse(f": agata rota {self._rota}")
            if sse:
                self._stream_sse_filtrado(leitor, buf_pre)
            else:
                for i in range(0, len(buf_pre), 8192):
                    pedaco = buf_pre[i:i + 8192]
                    self.wfile.write(f"{len(pedaco):X}\r\n".encode())
                    self.wfile.write(pedaco)
                    self.wfile.write(b"\r\n")
            # (23/11) o uso é gravado ANTES do terminador: o cliente só dá a resposta por completa quando lê o terminador,
            # então a linha já está no arquivo quando ele vê o fim (sem corrida). Latência = até o fim do corpo.
            if metodo == "POST" and "/chat/completions" in self.path and self._perfil is not None:
                self._uso_do_pedido(up.status)  # sem texto do pedido nem da resposta
            self.wfile.write(b"0\r\n\r\n")
            if up.status == 200 and "/chat/completions" in self.path:
                self._log("ok", t0)  # (17/11, item 1) uma linha por pedido concluído, com served_by
        except (BrokenPipeError, ConnectionResetError):
            # O cliente (LibreChat) desconectou no meio do stream -- reload da
            # página, timeout do navegador. Abandona ESTA requisição em silêncio;
            # sem isto a exceção subia e o servidor inteiro emperrava (a Seth
            # "travou" no teste 3, MEMÓRIAS (393)). close_connection pra o
            # keep-alive não reusar o socket morto.
            self._log(f"cliente desconectou no meio do stream (modelo {modelo_real or '?'})", t0)
            self.close_connection = True
        finally:
            up.close()
        self._fallback_corpo = None  # resposta entregue: nada guardado para o próximo pedido da conexão
        reg = getattr(self, "_reg", None)
        if reg is not None and up.status == 200:
            resposta = reg.get("resposta", "") if sse else registro_pedidos.resposta_json(buf_pre)
            registro_pedidos.gravar(reg["pergunta"], resposta,
                                    dict(reg["meta"], rota=self._rota, modelo=modelo_real))

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

    def _stream_sse_filtrado(self, leitor, buf: bytes = b""):
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
        self._emoji_estados = {}
        self._cab_estados = {}
        self._laco_estados = {}
        self._laco_cortou = False
        self._resgate = {}
        self._retidos = []
        self._reter = bool(_verificacao_ligada() and getattr(self, "_verificar", False))
        buf = self._escrever_linhas_completas(buf)
        while not self._laco_cortou:
            try:
                pedaco = leitor.ler(180)  # (709) mesmo teto de antes (urlopen timeout=180)
            except queue.Empty:
                break
            if not pedaco:
                break
            buf = self._escrever_linhas_completas(buf + pedaco)
        if self._laco_cortou:
            # Trava de laço (18/10/2026): o SSE já foi fechado (nota + finish_reason + [DONE]);
            # solta o upstream na hora para o provedor parar de gerar.
            _derrubar(getattr(leitor, "_up", None))
        elif buf:
            saida = self._filtrar_linha_sse(buf)
            if _emoji_ligado():
                saida = limpa_emoji.limpar_sse_linha(saida, self._emoji_estados)
            if self._cab_injetado and _cabecalho_unico_ligado():
                saida = limpa_cabecalho.limpar_sse_linha(saida, self._cab_estados, self._cab_injetado)
            if _trava_laco_ligada():
                saida, self._laco_cortou = limpa_laco.limpar_sse(saida, self._laco_estados, _trava_laco_repeticoes())
            if saida:
                self._enviar(saida)
        self._liberar_retidos()
        if _emoji_ligado():
            _registrar_emoji(self._rota, getattr(self, "_modelo_para_log", ""),
                             [c for est in self._emoji_estados.values() for c in est.removidos])
        if self._cab_injetado and _cabecalho_unico_ligado():
            _registrar_cabecalho(self._rota, getattr(self, "_modelo_para_log", ""),
                                 sum(est.removidas for est in self._cab_estados.values()))
        if _trava_laco_ligada():
            _registrar_laco(self._rota, getattr(self, "_modelo_para_log", ""), self._laco_estados)

    def _enviar(self, saida: bytes) -> None:
        """Escreve um chunk HTTP -- ou o retém, se a verificação bloqueante está ativa nesta resposta."""
        if getattr(self, "_reter", False) and not _so_comentario(saida):
            self._retidos.append(saida)
            return
        self.wfile.write(f"{len(saida):X}\r\n".encode())
        self.wfile.write(saida)
        self.wfile.write(b"\r\n")

    def _liberar_retidos(self) -> None:
        """Fim da resposta retida: verifica o texto e entrega tudo, com o bloco antes do [DONE]."""
        if not getattr(self, "_reter", False):
            return
        self._reter = False
        retidos, self._retidos = self._retidos, []
        texto = _texto_do_sse(retidos)
        for prefixo in (getattr(self, "_texto_maquina", "") or "",):
            if prefixo and texto.startswith(prefixo):
                texto = texto[len(prefixo):]
        achados = []
        if texto.strip():
            try:
                achados = auditoria_turno.verificar_resposta_atual(texto, getattr(self, "_msgs_pedido", []) or [])
            except Exception as e:  # noqa: BLE001 -- verificação quebrada nunca segura a resposta
                print(f"gateway: verificação falhou ({e})", file=sys.stderr, flush=True)
        tool_calls = any(b'"tool_calls"' in ch for ch in retidos)
        if not tool_calls and _guarda_bloqueia(texto, getattr(self, "_msgs_pedido", []) or []):
            retidos = _recusa_no_stream(retidos, getattr(self, "_modelo_para_log", "") or "")
            achados = []
        if achados:
            bloco = _chunk_texto(_bloco_verificacao(achados), getattr(self, "_modelo_para_log", "") or "")
            i = next((k for k, ch in enumerate(retidos) if b"data: [DONE]" in ch), len(retidos))  # como o resgate
            retidos.insert(i, bloco)
            self._log_verificacao = achados
        for ch in retidos:
            self._enviar(ch)

    def _escrever_linhas_completas(self, buf: bytes) -> bytes:
        """Escreve (filtradas, em chunk HTTP) todas as linhas COMPLETAS de `buf`;
        devolve o resto -- no máximo uma linha parcial, sem '\\n'. Depois de um corte
        da trava de laço, não escreve mais nada e devolve b""."""
        while b"\n" in buf:
            if getattr(self, "_laco_cortou", False):
                return b""
            linha, buf = buf.split(b"\n", 1)
            tardio = _cabecalho_sse_tardio(linha, getattr(self, "_cab_pendente", "") or "")
            if tardio:
                # (item 2; revisão achado 4) o cabeçalho pendente sai antes do 1º texto que chegar depois. Ele volta para a fila
                # e passa pelo mesmo filtro (limpa_cabecalho) que a linha seguinte: se o modelo escreveu o próprio
                # cabeçalho logo depois, ele é apagado, e não sai duplo.
                self._cab_pendente = ""
                buf = tardio + linha + b"\n" + buf
                continue
            if getattr(self, "_served_by", None) is None:  # (17/11, item 1) o modelo pode vir só depois da espiada
                self._served_by = self._modelo_de_bytes(linha)
            if _resgate_ligado():
                if linha.strip() == b"data: [DONE]":
                    resg = _resgate_chunk(self._resgate, getattr(self, "_cab_pendente", "") or "")
                    if resg:
                        self._enviar(resg)
                        if getattr(self, "_reg", None) is not None:
                            registro_pedidos.acumular_sse(resg.split(b"\n")[0], self._reg)
                else:
                    _resgate_observar(linha, self._resgate)
            saida = self._filtrar_linha_sse(linha + b"\n")
            if _emoji_ligado():
                saida = limpa_emoji.limpar_sse_linha(saida, self._emoji_estados)
            if self._cab_injetado and _cabecalho_unico_ligado():
                saida = limpa_cabecalho.limpar_sse_linha(saida, self._cab_estados, self._cab_injetado)
            if _trava_laco_ligada():
                saida, self._laco_cortou = limpa_laco.limpar_sse(saida, self._laco_estados, _trava_laco_repeticoes())
            if getattr(self, "_reg", None) is not None:
                registro_pedidos.acumular_sse(saida, self._reg)
            if not saida:
                continue  # chunk HTTP de tamanho 0 encerraria a resposta
            self._enviar(saida)
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
def _emoji_ligado() -> bool:
    """E-2 (decisão do Humano, 16/10/2026): remove emoji da prosa. Chave para desligar sem mexer em código:
    SETH_EMOJI_REMOVER=0 (lida a cada resposta). Padrão: ligado."""
    return os.environ.get("SETH_EMOJI_REMOVER", "1") != "0"


def _registrar_emoji(rota, modelo, removidos) -> None:
    """Log do que o MODELO produziu (só códigos Unicode e contagem, nunca o texto): o cliente guarda a resposta já limpa,
    então a auditoria do turno seguinte não vê mais o emoji; esta é a medida. Fail-soft."""
    if not removidos:
        return
    try:
        arq = Path(os.environ.get("AGATA_EMOJI_LOG") or Path.home() / ".cache" / "agata" / "emoji-removido.jsonl")
        arq.parent.mkdir(parents=True, exist_ok=True)
        with open(arq, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rota": rota or "", "modelo": modelo or "",
                                "n": len(removidos), "codigos": sorted(set(removidos))}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _cabecalho_unico_ligado() -> bool:
    """Cabeçalho único (17/10/2026): apaga o cabeçalho que o MODELO escreve no começo, depois do da Máquina.
    Chave para desligar: SETH_CABECALHO_UNICO=0 (lida a cada resposta). Padrão: ligado."""
    return os.environ.get("SETH_CABECALHO_UNICO", "1") != "0"


def _registrar_cabecalho(rota, modelo, n) -> None:
    """Log de quantas linhas de cabeçalho o modelo escreveu e foram removidas (só contagem, nunca o texto). Fail-soft."""
    if not n:
        return
    try:
        arq = Path(os.environ.get("AGATA_CABECALHO_LOG") or Path.home() / ".cache" / "agata" / "cabecalho-removido.jsonl")
        arq.parent.mkdir(parents=True, exist_ok=True)
        with open(arq, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rota": rota or "", "modelo": modelo or "",
                                "n": int(n)}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _trava_laco_ligada() -> bool:
    """Trava de laço de repetição (18/10/2026, sonda 18 da rodada de 17/10): corta a resposta que degenera repetindo o mesmo
    trecho. Chave para desligar: SETH_TRAVA_LACO=0 (lida a cada resposta). Padrão: ligada."""
    return os.environ.get("SETH_TRAVA_LACO", "1") != "0"


def _trava_laco_repeticoes() -> int:
    """Mínimo de voltas seguidas do mesmo trecho para cortar (SETH_LACO_REPETICOES; padrão do limpa_laco)."""
    try:
        return int(os.environ.get("SETH_LACO_REPETICOES", limpa_laco.REPETICOES))
    except ValueError:
        return limpa_laco.REPETICOES


def _registrar_laco(rota, modelo, estados) -> None:
    """Log da trava de laço: só quando cortou ou quando o modelo ecoou o bloco de estado. Só contagens e o período, nunca o
    texto. Fail-soft."""
    ests = list((estados or {}).values())
    cortou = any(e.cortado for e in ests)
    eco = any(e.eco for e in ests)
    if not (cortou or eco):
        return
    try:
        arq = Path(os.environ.get("AGATA_LACO_LOG") or Path.home() / ".cache" / "agata" / "laco-cortado.jsonl")
        arq.parent.mkdir(parents=True, exist_ok=True)
        with open(arq, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rota": rota or "", "modelo": modelo or "",
                                "cortou": cortou, "eco_estado": eco,
                                "periodo": max((e.periodo for e in ests), default=0),
                                "voltas": max((e.voltas for e in ests), default=0),
                                "chars": sum(len(e.texto) for e in ests)}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _porta_livre() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class _Dummy(BaseHTTPRequestHandler):
    ultimo_corpo = b""
    modelo_resposta = None  # teste 10/11 liga isto pra simular "model" na resposta real
    vazias = 0          # (695) quantas respostas vazias dar antes da normal
    penduradas = 0      # (709) quantas respostas só-keepalive (SSE, sem conteúdo) antes da normal
    modelos_pedidos = []
    texto_fixo = None   # E-2: resposta não streaming com este texto (ex.: com emoji)
    sse_emoji = False   # E-2: próxima resposta é SSE com emoji partido em fragmentos
    sse_laco = False    # trava de laço: próxima resposta é SSE que repete a mesma frase sem parar
    laco_escritos = 0   # quantos fragmentos do laço o upstream conseguiu escrever antes de ser solto

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        type(self).ultimo_corpo = self.rfile.read(n)
        if type(self).sse_laco:  # o caso medido da sonda 18 (17/10/2026), em ~2 MB se ninguém cortar
            type(self).sse_laco = False
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            frags = ["ativa\n\nAUDITORIA-TURNO-ANTERIOR: OK\nMESMA-RESPOSTA: continuação da sua resposta.\n\n"]
            frags += ["Não cite o arquivo histórico ", "sem `vault_consultar extras/`. "] * 20000
            try:
                for i, frag in enumerate(frags):
                    ch = {"id": "c-laco", "model": "m-real", "choices": [{"index": 0, "delta": {"content": frag}}]}
                    self.wfile.write(b"data: " + json.dumps(ch, ensure_ascii=False).encode() + b"\n\n")
                    type(self).laco_escritos = i + 1
                    if i % 50 == 0:
                        self.wfile.flush()
                        time.sleep(0.005)
                self.wfile.write(b"data: [DONE]\n\n")
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        if type(self).sse_emoji:
            type(self).sse_emoji = False
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for frag in ("Feito ", "\u2705", " ok `\u2705` \"\u274c\" ", "fim \U0001F600\n"):
                ch = {"model": "m-real", "choices": [{"index": 0, "delta": {"content": frag}}]}
                self.wfile.write(b"data: " + json.dumps(ch).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            return
        try:
            type(self).modelos_pedidos.append(json.loads(type(self).ultimo_corpo).get("model"))
        except ValueError:
            pass
        if type(self).penduradas > 0:
            type(self).penduradas -= 1
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            ka = (b'data: {"id":"chatcmpl-keepalive","model":"keepalive","choices":[{"index":0,'
                  b'"delta":{},"finish_reason":null}]}\n\n')
            try:
                for _ in range(20):  # 4 s de keepalive, sem conteúdo
                    self.wfile.write(ka); self.wfile.flush(); time.sleep(0.2)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        texto = type(self).texto_fixo or "ok"
        if type(self).vazias > 0:
            type(self).vazias -= 1
            texto = ""
        resp = {"choices": [{"message": {"role": "assistant", "content": texto}}]}
        if type(self).modelo_resposta:
            resp["model"] = type(self).modelo_resposta
        corpo = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def _selftest() -> int:
    # offline por desenho: o ls-remote do estado nao pode estourar o timeout dos casos (flaky na CI)
    os.environ.setdefault("LS_REMOTE_TIMEOUT_ECO", "1")
    global UPSTREAM, MODELO_REAL_PATH
    up_port, gw_port = _porta_livre(), _porta_livre()
    UPSTREAM = f"http://127.0.0.1:{up_port}"
    import tempfile
    MODELO_REAL_PATH = Path(tempfile.mkdtemp()) / "modelo-real.txt"  # isolado do arquivo real
    os.environ["AGATA_CAPIVARA_USO"] = str(Path(tempfile.mkdtemp()) / "uso.jsonl")  # (23/11) o selftest não grava no log real
    # (23/11) o selftest confere a rota do Laya e o combo; a escolha por capacidade (que lê o registro real) tem testes
    # próprios, com registro temporário, em redesign/router/test_rotas_locais.py
    os.environ["SETH_ESCOLHA_CAPACIDADE"] = "0"
    # (719) o selftest nunca fala com o Laya nem com o Jev de verdade: rota e sombra
    # determinísticas mesmo com os serviços no ar (os casos que precisam deles os simulam)
    decisor.URL = decisor.URL_LAYA = "http://127.0.0.1:9"
    decisor.LOG_DIR = Path(tempfile.mkdtemp())
    up = ThreadingHTTPServer(("127.0.0.1", up_port), _Dummy)
    gw = ThreadingHTTPServer(("127.0.0.1", gw_port), _Handler)
    # Os casos legados abaixo verificam hidratação com respostas sintéticas;
    # a política da rota pública tem testes próprios e não é desativada em runtime.
    gw._selftest_allow_context = True
    threading.Thread(target=up.serve_forever, daemon=True).start()
    threading.Thread(target=gw.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{gw_port}/v1/chat/completions"
    falhas = 0

    # 1. pedido sem system -> o corpo repassado ao upstream ganha 1 system hidratado
    body = json.dumps({"model": "seth", "messages": [{"role": "user", "content": "oi"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    repassado = json.loads(_Dummy.ultimo_corpo)
    m = repassado["messages"]
    ok = (m[0]["role"] == "system" and MARCADOR in m[0]["content"]
          and m[1]["role"] == "user" and len(m) == 2)
    print(f"{'PASS' if ok else 'FALHA'}  sem system -> injetou 1 system hidratado antes do user "
          f"({len(m[0]['content'])} chars)")
    falhas += 0 if ok else 1

    # 1b. (683) campo `user` do LibreChat não chega ao OmniRoute (Mistral: 422)
    body_u = json.dumps({"model": "seth", "user": "6a99c85", "messages": [
        {"role": "user", "content": "oi"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body_u, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    ok1b = "user" not in json.loads(_Dummy.ultimo_corpo)
    print(f"{'PASS' if ok1b else 'FALHA'}  campo `user` retirado antes do OmniRoute")
    falhas += 0 if ok1b else 1

    # 2. pedido JÁ hidratado -> NÃO repete a doutrina, MAS reinjeta ESTADO-ATUAL
    body2 = json.dumps({"model": "seth", "messages": [
        {"role": "system", "content": f"{MARCADOR}\nx"},
        {"role": "user", "content": "oi"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body2, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
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
        base, data=body2b, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    m2b = json.loads(_Dummy.ultimo_corpo)["messages"]
    est_b = [x for x in m2b if isinstance(x.get("content"), str) and MARCADOR_ESTADO in x["content"]]
    ok2b = len(est_b) == 1 and "VELHO" not in est_b[0]["content"]
    print(f"{'PASS' if ok2b else 'FALHA'}  ESTADO-ATUAL velho -> substituído, não acumulou "
          f"(est={len(est_b)})")
    falhas += 0 if ok2b else 1

    # 3. chamada de TÍTULO do LibreChat (titleMethod structured: schema com "title")
    #    -> repassada crua, SEM system hidratado
    body3 = json.dumps({"model": "seth", "messages": [
        {"role": "user", "content": "User: oi\nAssistant: ok"}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "title", "schema": {
            "type": "object", "properties": {"title": {"type": "string"}},
            "required": ["title"]}}}}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body3, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    m3 = json.loads(_Dummy.ultimo_corpo)["messages"]
    ok3 = len(m3) == 1 and m3[0]["role"] == "user" and MARCADOR not in m3[0]["content"]
    print(f"{'PASS' if ok3 else 'FALHA'}  chamada de título -> repassada sem hidratar "
          f"(messages={len(m3)}, role0={m3[0]['role']})")
    falhas += 0 if ok3 else 1

    # 3c. usuário COLA a frase-gatilho antiga do título (sem schema) -> hidrata
    #     (residual de (419)/(431)/(433) fechado)
    body3c = json.dumps({"model": "seth", "messages": [
        {"role": "user", "content": "Analyze this conversation and provide:\n1. The "
         "detected language\n2. A concise title in the detected language"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body3c, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    m3c = json.loads(_Dummy.ultimo_corpo)["messages"]
    ok3c = len(m3c) == 2 and m3c[0]["role"] == "system" and MARCADOR in m3c[0]["content"]
    print(f"{'PASS' if ok3c else 'FALHA'}  frase de título colada pelo usuário -> hidratou "
          f"(messages={len(m3c)})")
    falhas += 0 if ok3c else 1

    # 3d. gatilho do Goose vindo em mensagem de USUÁRIO -> hidrata
    body3d = json.dumps({"model": "seth", "messages": [
        {"role": "user", "content": "Generate a short title (four words or less) that "
         "describes the topic of the user's messages"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body3d, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    m3d = json.loads(_Dummy.ultimo_corpo)["messages"]
    ok3d = len(m3d) == 2 and m3d[0]["role"] == "system" and MARCADOR in m3d[0]["content"]
    print(f"{'PASS' if ok3d else 'FALHA'}  gatilho do Goose como mensagem de usuário -> "
          f"hidratou (messages={len(m3d)})")
    falhas += 0 if ok3d else 1

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
        base, data=body3b, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    m3b = json.loads(_Dummy.ultimo_corpo)["messages"]
    ok3b = len(m3b) == 2 and m3b[0]["role"] == "system" and MARCADOR not in m3b[0]["content"]
    print(f"{'PASS' if ok3b else 'FALHA'}  chamada de título do Goose -> repassada sem "
          f"hidratar (messages={len(m3b)})")
    falhas += 0 if ok3b else 1

    # 4. chat normal com a palavra "título" no meio -> AINDA hidrata (sem falso positivo)
    body4 = json.dumps({"model": "seth", "messages": [
        {"role": "user", "content": "que título você daria pra essa conversa?"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body4, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
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

    # 9j. (682) passo depois de ferramenta fica na fila do passo 1 (mesma resposta)
    hist = [{"role": "user", "content": "x" * 1200}]
    passo1 = _classificar_rota({"model": "seth-livre", "tools": [{"x": 1}], "messages": hist})
    passo2 = _classificar_rota({"model": "seth-livre", "tools": [{"x": 1}], "messages": hist + [
        {"role": "assistant", "content": "", "tool_calls": [{"id": "t1", "type": "function",
                                                              "function": {"name": "vault_buscar", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "z" * 9000}]})
    ok9j = passo1 == passo2 == "seth-livre"
    print(f"{'PASS' if ok9j else 'FALHA'}  rota estável depois de ferramenta ({passo1} -> {passo2})")
    falhas += 0 if ok9j else 1

    # 9b. travas exatas sobre a escolha do decisor (pura, sem rede)
    curto = {"messages": [{"role": "user", "content": "prove que há infinitos primos"}]}
    travas = [
        ("sem escolha -> heurística", _rota_com_travas(None, curto), "seth-rapido"),
        ("codigo -> seth-codigo", _rota_com_travas("codigo", curto), "seth-codigo"),
        ("pesado curto -> seth-pesado", _rota_com_travas("pesado", curto), "seth-pesado"),
        (">6000 chars vence o modelo", _rota_com_travas(
            "rapido", {"messages": [{"role": "user", "content": "z" * 7000}]}), "seth-pesado"),
        ("rapido com tools fica seth-rapido (AC-01)", _rota_com_travas(
            "rapido", {"tools": [{"x": 1}], **curto}), "seth-rapido"),
    ]
    for desc, deu, quer in travas:
        ok = deu == quer
        print(f"{'PASS' if ok else 'FALHA'}  trava: {desc} (deu {deu})")
        falhas += 0 if ok else 1

    # 9c. (719) Laya e Jev fora do ar: o pedido passa pela regra por tamanho, sem esperar
    import time as _t
    _urls_antes = (decisor.URL, decisor.URL_LAYA)
    decisor.URL = decisor.URL_LAYA = "http://127.0.0.1:9"
    _log_antes, decisor.LOG_DIR = decisor.LOG_DIR, Path(tempfile.mkdtemp())
    t0 = _t.monotonic()
    urllib.request.urlopen(urllib.request.Request(base, data=json.dumps(
        {"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}]}).encode(),
        headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    dt = _t.monotonic() - t0
    rota_sombra = json.loads(_Dummy.ultimo_corpo)["model"]
    decisor.URL, decisor.URL_LAYA = _urls_antes
    decisor.LOG_DIR = _log_antes
    ok9c = rota_sombra == "seth-rapido" and dt < 2
    print(f"{'PASS' if ok9c else 'FALHA'}  (719) Laya e Jev fora -> regra, sem bloquear "
          f"(rota {rota_sombra}, {dt * 1000:.0f} ms)")
    falhas += 0 if ok9c else 1

    # 9d. (719) caminho completo (pedido real, hidratação injetada, thread do Jev): o Laya
    # escolhe a rota com as travas; o Jev é a sombra; discordância vira caso para o juiz.
    _decidir_antes, _log_antes = decisor.decidir, decisor.LOG_DIR
    _hid_antes = globals()["_hidratacao"]
    globals()["_hidratacao"] = lambda extra="": MARCADOR + "\n" + "h" * 9000  # a real tem ~8,8 mil
    decisor.LOG_DIR = Path(tempfile.mkdtemp())
    divs = decisor.LOG_DIR / "roteador-laya-avaliacao.jsonl"

    def _rota_com(laya_diz, jev_diz, conf_laya=0.95, texto="oi"):
        def _falso(uso, *a, **k):
            if k.get("modelo") == decisor.MODELO_LAYA:
                return {"rota": {"type": "choice", "choice": laya_diz, "confidence": conf_laya}}
            _t.sleep(0.3)  # o Jev real leva ~4 s, numa thread: o `_injeta` já mexeu no pedido
            return {"rota": {"type": "choice", "choice": jev_diz, "confidence": 0.9}}
        decisor.decidir = _falso
        urllib.request.urlopen(urllib.request.Request(base, data=json.dumps(
            {"model": "seth-livre", "messages": [{"role": "user", "content": texto}]}).encode(),
            headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
        for _ in range(50):  # espera a thread de sombra soltar o semáforo
            if _SOMBRA_LIVRE.acquire(blocking=False):
                _SOMBRA_LIVRE.release()
                break
            _t.sleep(0.05)
        return (json.loads(_Dummy.ultimo_corpo)["model"],
                divs.read_text().splitlines() if divs.exists() else [])

    r1, d1 = _rota_com("rapido", "rapido")
    r2, d2 = _rota_com("codigo", "livre", texto="me explica latência")
    r3, _ = _rota_com("pesado", "pesado", conf_laya=0.3)
    decisor.decidir, decisor.LOG_DIR = _decidir_antes, _log_antes
    globals()["_hidratacao"] = _hid_antes
    casos9 = [
        ("(719) Laya diz rapido -> seth-rapido; concordando com o Jev, nenhum caso "
         "(hidratação não conta na trava)", r1 == "seth-rapido" and d1 == []),
        ("(719) Laya decide a rota (codigo) e a discordância do Jev (livre) vira 1 caso com os dois",
         r2 == "seth-codigo" and len(d2) == 1 and json.loads(d2[0])["jev"] == "livre"
         and json.loads(d2[0])["laya"] == "codigo" and json.loads(d2[0])["rota_ativa"] == "seth-codigo"),
        ("(719) Laya com confiança abaixo do limiar -> regra por tamanho", r3 == "seth-rapido"),
    ]
    for desc, ok in casos9:
        print(f"{'PASS' if ok else 'FALHA'}  {desc}")
        falhas += 0 if ok else 1


    # 9f. auditoria do turno anterior pelo caminho completo (662): resposta anterior
    # com cabeçalho errado -> o pedido seguinte leva AUDITORIA-TURNO-ANTERIOR.
    _aud_log = auditoria_turno.LOG
    auditoria_turno.LOG = Path(tempfile.mkdtemp()) / "aud.jsonl"
    urllib.request.urlopen(urllib.request.Request(base, data=json.dumps({"model": "seth", "messages": [
        {"role": "user", "content": "oi"},
        {"role": "assistant", "content": "Agata · m · t=1 · 2026-10-13 12:43 -0300 (relógio da Máquina)\n\nok"},
        {"role": "user", "content": "e agora?"}]}).encode(),
        headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    m9f = json.loads(_Dummy.ultimo_corpo)["messages"]
    sys9f = " ".join(x["content"] for x in m9f if x.get("role") == "system" and isinstance(x.get("content"), str))
    ok9f = "AUDITORIA-TURNO-ANTERIOR:" in sys9f and "qualificador" in sys9f
    auditoria_turno.LOG = _aud_log
    print(f"{'PASS' if ok9f else 'FALHA'}  auditoria do turno anterior chega ao bloco de estado")
    falhas += 0 if ok9f else 1

    # 9g. passo de continuação do modo Agent (664): depois de ferramenta, o pedido
    # leva MESMA-RESPOSTA e não reaudita a resposta em andamento.
    auditoria_turno.LOG = Path(tempfile.mkdtemp()) / "aud.jsonl"
    urllib.request.urlopen(urllib.request.Request(base, data=json.dumps({"model": "seth", "messages": [
        {"role": "user", "content": "reavalie"},
        {"role": "assistant", "content": "Agata · m · t=1 · x", "tool_calls": [{"id": "1", "type": "function",
         "function": {"name": "f", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "1", "content": "saída"}]}).encode(),
        headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    m9g = json.loads(_Dummy.ultimo_corpo)["messages"]
    sys9g = " ".join(x["content"] for x in m9g if x.get("role") == "system" and isinstance(x.get("content"), str))
    # a doutrina também cita os dois rótulos: confere a LINHA de estado, no começo de linha
    ok9g = (auditoria_turno.LINHA_CONTINUACAO in sys9g
            and not re.search(r"(?m)^AUDITORIA-TURNO-ANTERIOR: ", sys9g))
    auditoria_turno.LOG = _aud_log
    print(f"{'PASS' if ok9g else 'FALHA'}  passo de continuação: MESMA-RESPOSTA, sem reauditar")
    falhas += 0 if ok9g else 1

    # 9h. fila pela janela (667): perfil de teste -- pedido curto fica, pedido grande
    # vai pro -longo; fila fora do perfil não muda.
    _perfis_antes = globals()["_perfis"]
    globals()["_perfis"] = lambda: {"filas": {"seth-pesado": ["a/grande", "ollama-local/x"], "seth-codigo": ["a/grande", "ollama-local/x"]},
                                    "modelos": {"a/grande": {"janela": 1000000}, "ollama-local/x": {"janela": 65536}}}
    curto = {"model": "seth-pesado", "messages": [{"role": "user", "content": "oi"}]}
    grande = {"model": "seth-pesado", "messages": [{"role": "user", "content": "z" * 200000}]}
    fora = {"model": "seth-codigo", "messages": [{"role": "user", "content": "z" * 200000}]}  # no perfil, mas sem fila -longo no OmniRoute
    ok9h = (_fila_pela_janela(curto) is None and _fila_pela_janela(grande) == "seth-pesado-longo"
            and _fila_pela_janela(fora) is None)
    globals()["_perfis"] = _perfis_antes
    print(f"{'PASS' if ok9h else 'FALHA'}  fila pela janela: curto fica, grande vai pro -longo, fora do perfil não muda")
    falhas += 0 if ok9h else 1

    # 9i. modo conciso padrão e explicativo pedido pelo Humano chegam ao estado (667)
    def _sys_de(msgs):
        urllib.request.urlopen(urllib.request.Request(base, data=json.dumps({"model": "seth", "messages": msgs}).encode(),
                                                      headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
        return " ".join(x["content"] for x in json.loads(_Dummy.ultimo_corpo)["messages"]
                        if x.get("role") == "system" and isinstance(x.get("content"), str))
    ok9i = (re.search(r"(?m)^MODO: conciso", _sys_de([{"role": "user", "content": "oi"}])) is not None
            and re.search(r"(?m)^MODO: explicativo", _sys_de([{"role": "user", "content": "modo explicativo"}])) is not None)
    print(f"{'PASS' if ok9i else 'FALHA'}  modo conciso padrão / explicativo a pedido chegam ao estado")
    falhas += 0 if ok9i else 1

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
        base, data=body10, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    ok10b = _modelo_real_anterior() == "teste/modelo-selftest"
    print(f"{'PASS' if ok10b else 'FALHA'}  modelo real: resposta com \"model\" -> sidecar gravado "
          f"(lido: {_modelo_real_anterior()!r})")
    falhas += 0 if ok10b else 1

    urllib.request.urlopen(urllib.request.Request(
        base, data=body10, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read()
    m10 = json.loads(_Dummy.ultimo_corpo)["messages"]
    est10 = next((x["content"] for x in m10 if isinstance(x.get("content"), str)
                  and MARCADOR_ESTADO in x["content"]), "")
    ok10c = "MODELO-REAL-TURNO-ANTERIOR" not in est10 and MARCADOR_ESTADO in est10
    print(f"{'PASS' if ok10c else 'FALHA'}  (705) estado sem MODELO-REAL-TURNO-ANTERIOR: "
          f"o modelo vai no cabeçalho da Máquina")
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

        def ler(self, timeout):  # (709) o stream agora lê de um _Leitor
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

    # 13. keep-alive: a rota de um pedido não vaza pro X-Seth-Rota do seguinte.
    # Mesma conexão HTTP/1.1, mesmo handler: 1º pedido seth-livre (classificado),
    # 2º pedido seth-codigo (não classificado) -- este não pode sair com rota.
    import http.client
    c13 = http.client.HTTPConnection("127.0.0.1", gw_port, timeout=10)
    rotas13 = []
    for modelo13 in (_ROTA_BASE, "seth-codigo"):
        c13.request("POST", "/v1/chat/completions", body=json.dumps({
            "model": modelo13, "messages": [{"role": "user", "content": "oi"}]}),
            headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"})
        r13 = c13.getresponse()
        r13.read()
        rotas13.append(r13.getheader("X-Seth-Rota"))
    c13.close()
    ok13 = bool(rotas13[0]) and rotas13[1] is None
    print(f"{'PASS' if ok13 else 'FALHA'}  keep-alive: rota não vaza pro pedido seguinte {rotas13}")
    falhas += 0 if ok13 else 1

    # 19. (709) só keepalive além do prazo -> nova tentativa na fila acima, sem esperar o upstream
    global PRAZO_1O_CONTEUDO
    prazo_orig, PRAZO_1O_CONTEUDO = PRAZO_1O_CONTEUDO, 1.0
    _Dummy.penduradas, _Dummy.modelos_pedidos = 1, []
    t19 = time.monotonic()
    r19 = json.loads(urllib.request.urlopen(urllib.request.Request(base, data=json.dumps(
        {"model": "seth-livre", "stream": True, "messages": [{"role": "user", "content": "oi"}]}).encode(),
        headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=20).read())["choices"][0]["message"]["content"]
    dt19 = time.monotonic() - t19
    PRAZO_1O_CONTEUDO = prazo_orig
    ok19 = r19.endswith("ok") and _Dummy.modelos_pedidos == ["seth-rapido", "seth-livre"] and dt19 < 3.5
    print(f"{'PASS' if ok19 else 'FALHA'}  só keepalive além do prazo -> fila acima em {dt19:.1f} s "
          f"({_Dummy.modelos_pedidos})")
    falhas += 0 if ok19 else 1

    # 17. (705) cabeçalho da Máquina: 1ª resposta = prontidão; 2ª = linha de turno; só ferramenta = nada
    _Dummy.modelo_resposta = "gemini-2.5-flash"
    r17a = json.loads(urllib.request.urlopen(urllib.request.Request(base, data=json.dumps(
        {"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}]}).encode(),
        headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read())["choices"][0]["message"]["content"]
    r17b = json.loads(urllib.request.urlopen(urllib.request.Request(base, data=json.dumps(
        {"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}, {"role": "assistant", "content": "x"},
                                             {"role": "user", "content": "e agora?"}]}).encode(),
        headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read())["choices"][0]["message"]["content"]
    l17 = r17a.splitlines()
    ok17a = (l17[0].startswith("agata-seth · modelo: gemini-2.5-flash (Google, nuvem; medido pela Máquina neste turno)")
             and l17[1].startswith("Última entrada:") and (l17[2] == "pronto." or l17[2].startswith("quebrado:")))
    ok17b = r17b.startswith("agata-seth · gemini-2.5-flash (Google, nuvem; medido pela Máquina neste turno) · t=2 (contador mecânico) · ")
    ok17c = r17a.endswith("ok") and r17b.endswith("ok")
    print(f"{'PASS' if ok17a else 'FALHA'}  cabeçalho da Máquina, 1ª resposta: prontidão de 3 linhas")
    print(f"{'PASS' if ok17b else 'FALHA'}  cabeçalho da Máquina, 2ª resposta: t=2 (contador mecânico)")
    print(f"{'PASS' if ok17c else 'FALHA'}  cabeçalho não come o conteúdo do modelo")
    falhas += sum(0 if x else 1 for x in (ok17a, ok17b, ok17c))
    sse = (b'data: {"id":"c1","model":"m","choices":[{"delta":{"role":"assistant"}}]}\n\n'
           b'data: {"id":"c1","model":"m","choices":[{"delta":{"content":"oi"}}]}\n\n')
    inj = _injetar_sse(sse, "CAB\n\n") or b""
    ok17d = inj.index(b'"CAB') < inj.index(b'"oi"') and inj.count(b"data:") == 3
    so_ferr = b'data: {"id":"c1","choices":[{"delta":{"tool_calls":[{"index":0}]}}]}\n\n'
    ok17e = _injetar_sse(so_ferr, "CAB") is None
    print(f"{'PASS' if ok17d else 'FALHA'}  SSE: cabeçalho entra antes do 1º texto")
    print(f"{'PASS' if ok17e else 'FALHA'}  SSE: resposta só de ferramenta não recebe cabeçalho")
    falhas += (0 if ok17d else 1) + (0 if ok17e else 1)
    ok17f = "local, na Máquina" in _descrever_modelo("qwen3.5-9b-64k:latest") or "Alibaba" in _descrever_modelo("qwen3.5-9b-64k:latest")
    ok17g = _descrever_modelo(None) == "modelo não verificado"
    print(f"{'PASS' if ok17f and ok17g else 'FALHA'}  descrição do modelo: {_descrever_modelo('qwen3.5-9b-64k:latest')}")
    falhas += 0 if ok17f and ok17g else 1
    # 17h. Cabeçalho único (17/10/2026): o cabeçalho que o MODELO escreve depois do da Máquina é apagado
    _Dummy.texto_fixo = ("Agata · modelo: x · sync: PASS · HEAD=4975b44 · 2026-10-17 11:56 -0300\n"
                         "Última entrada: (741) DIÁRIO — x\npronto.\n\nSistemas operacionais.")
    log_cab = Path(__import__("tempfile").mkdtemp()) / "cab.jsonl"
    os.environ["AGATA_CABECALHO_LOG"] = str(log_cab)
    r17h = json.loads(urllib.request.urlopen(urllib.request.Request(base, data=json.dumps(
        {"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}, {"role": "assistant", "content": "x"},
                                             {"role": "user", "content": "e agora?"}]}).encode(),
        headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read())["choices"][0]["message"]["content"]
    ok17h = r17h.count("agata-seth ·") == 1 and r17h.count("Agata ·") == 0 and r17h.endswith("Sistemas operacionais.") and "sync: PASS" not in r17h
    ok17i = log_cab.exists() and json.loads(log_cab.read_text(encoding="utf-8").splitlines()[0])["n"] >= 1
    os.environ["SETH_CABECALHO_UNICO"] = "0"
    r17j = json.loads(urllib.request.urlopen(urllib.request.Request(base, data=json.dumps(
        {"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}, {"role": "assistant", "content": "x"},
                                             {"role": "user", "content": "e agora?"}]}).encode(),
        headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read())["choices"][0]["message"]["content"]
    del os.environ["SETH_CABECALHO_UNICO"]
    ok17j = r17j.count("agata-seth ·") + r17j.count("Agata ·") == 2
    _Dummy.texto_fixo = None
    print(f"{'PASS' if ok17h else 'FALHA'}  cabeçalho único: o duplicado do modelo é apagado, fica o da Máquina")
    print(f"{'PASS' if ok17i else 'FALHA'}  cabeçalho único: remoção registrada em log (só contagem)")
    print(f"{'PASS' if ok17j else 'FALHA'}  cabeçalho único: SETH_CABECALHO_UNICO=0 desliga")
    falhas += sum(0 if x else 1 for x in (ok17h, ok17i, ok17j))
    # 17m. Rédea (17/10/2026): o pedido cita (N) -> o texto exato da entrada vai no estado do turno
    _pr = _injeta({"model": "seth-livre", "messages": [{"role": "user", "content": "explique a (743) pra mim"}]})
    _sys = " ".join(m["content"] for m in _pr["messages"] if isinstance(m, dict) and m.get("role") == "system")
    ok17m = "ENTRADAS-LITERAIS" in _sys and "(743) " in _sys
    _pr2 = _injeta({"model": "seth-livre", "messages": [{"role": "user", "content": "oi, tudo bem?"}]})
    _sys2 = " ".join(m["content"] for m in _pr2["messages"] if isinstance(m, dict) and m.get("role") == "system")
    ok17n = "ENTRADAS-LITERAIS" not in _sys2
    print(f"{'PASS' if ok17m else 'FALHA'}  rédea: pedido com (743) leva a entrada exata no estado")
    print(f"{'PASS' if ok17n else 'FALHA'}  rédea: pedido sem (N) não leva bloco")
    falhas += sum(0 if x else 1 for x in (ok17m, ok17n))
    # 18. (705) rota pelo pedido atual: histórico longo com saída de ferramenta + pergunta simples = livre
    hist18 = [{"role": "user", "content": "x" * 300}, {"role": "assistant", "content": "", "tool_calls": [{"id": "t"}]},
              {"role": "tool", "content": "z" * 20000}, {"role": "assistant", "content": "y" * 3000}] * 4 + [
             {"role": "user", "content": "e o que você acha disso?"}]
    r18 = _classificar_rota({"model": "seth-livre", "tools": [{"x": 1}], "messages": hist18})
    print(f"{'PASS' if r18 == 'seth-livre' else 'FALHA'}  rota pelo pedido atual, não pelo histórico (deu {r18})")
    falhas += 0 if r18 == "seth-livre" else 1
    _Dummy.modelo_resposta = None

    # 14. (695) resposta vazia -> 1 nova tentativa, fila acima; o cliente recebe a 2ª
    _Dummy.vazias, _Dummy.modelos_pedidos = 1, []
    body = json.dumps({"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}]}).encode()
    r14 = json.loads(urllib.request.urlopen(urllib.request.Request(
        base, data=body, headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}), timeout=10).read())
    ok14 = (r14["choices"][0]["message"]["content"].endswith("ok")  # (705) agora com o cabeçalho da Máquina na frente
            and _Dummy.modelos_pedidos == ["seth-rapido", "seth-livre"])
    print(f"{'PASS' if ok14 else 'FALHA'}  resposta vazia -> nova tentativa na fila acima "
          f"({_Dummy.modelos_pedidos})")
    falhas += 0 if ok14 else 1
    # 16. (695) linha de propostas no estado
    ok16 = _linha_propostas().startswith("PROPOSTAS-PENDENTES: ") and "propostas/aplicadas/" in _linha_propostas()
    print(f"{'PASS' if ok16 else 'FALHA'}  PROPOSTAS-PENDENTES no estado: {_linha_propostas()[:80]}")
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _t:
        _p = Path(_t)
        for _n in ("a-aberta", "b-assinada", "c-substituida"):
            (_p / f"{_n}.diff").write_text("x", encoding="utf-8")
        (_p / "APROVADO-b-assinada").write_text("s", encoding="utf-8")
        (_p / "APROVADO-c-substituida").write_text("s", encoding="utf-8")
        (_p / "SUBSTITUIDAS.txt").write_text("# nome | por | motivo\nc-substituida | d-nova | teste\n", encoding="utf-8")
        _l = _linha_propostas(_p)
        ok16b = ("PENDENTES: a-aberta" in _l and "falta aplicar: b-assinada" in _l
                 and "falta aplicar: b-assinada, c" not in _l and "substituídas, NÃO pendentes: c-substituida" in _l)
    print(f"{'PASS' if ok16b else 'FALHA'}  proposta em SUBSTITUIDAS.txt sai das pendentes e das assinadas: {_l[:110]}")
    falhas += 0 if ok16b else 1
    falhas += 0 if ok16 else 1
    # 17. (E-2, 16/10/2026) remoção de emoji da prosa: não streaming e SSE, log só com códigos, chave para desligar
    import tempfile as _tf
    log_emoji = Path(_tf.mkdtemp()) / "emoji.jsonl"
    os.environ["AGATA_EMOJI_LOG"] = str(log_emoji)
    corpo_e = json.dumps({"model": "seth", "messages": [{"role": "user", "content": "oi"}]}).encode()
    hdr = {"Content-Type": "application/json", "X-Agata-Data-Classification": "public"}
    _Dummy.texto_fixo = "Pronto \u2705 e `\u2705` fim \U0001F600"
    r17 = json.loads(urllib.request.urlopen(urllib.request.Request(base, data=corpo_e, headers=hdr), timeout=10).read())
    t17 = r17["choices"][0]["message"]["content"]
    ok17a = "\U0001F600" not in t17 and t17.count("\u2705") == 1 and "`\u2705`" in t17
    print(f"{'PASS' if ok17a else 'FALHA'}  E-2 não streaming: emoji da prosa sai, o do código fica ({t17!r})")
    falhas += 0 if ok17a else 1
    _Dummy.texto_fixo = None
    _Dummy.sse_emoji = True
    sse17 = urllib.request.urlopen(urllib.request.Request(base, data=json.dumps({"model": "seth", "stream": True,
        "messages": [{"role": "user", "content": "oi"}]}).encode(), headers=hdr), timeout=15).read().decode("utf-8")
    txt17 = "".join(json.loads(l[6:])["choices"][0]["delta"].get("content") or ""
                    for l in sse17.splitlines() if l.startswith("data: {") and "choices" in l and "keepalive" not in l)
    ok17b = ("\u2705" not in txt17.replace("`\u2705`", "")) and "`\u2705`" in txt17 and '"\u274c"' in txt17 and "\U0001F600" not in txt17 and "[DONE]" in sse17
    print(f"{'PASS' if ok17b else 'FALHA'}  E-2 SSE: fragmentos limpos, código e aspas preservados, [DONE] intacto ({txt17!r})")
    falhas += 0 if ok17b else 1
    log17 = [json.loads(l) for l in log_emoji.read_text(encoding="utf-8").splitlines()] if log_emoji.exists() else []
    ok17c = len(log17) == 2 and all("texto" not in e and "codigos" in e for e in log17) and log17[0]["n"] >= 1
    print(f"{'PASS' if ok17c else 'FALHA'}  E-2 log: {len(log17)} registros, só códigos Unicode e contagem")
    falhas += 0 if ok17c else 1
    # 19. Trava de laço (18/10/2026): o caso medido da sonda 18, pelo mesmo caminho da produção (SSE pelo gateway)
    log_laco = Path(_tf.mkdtemp()) / "laco.jsonl"
    os.environ["AGATA_LACO_LOG"] = str(log_laco)
    _Dummy.sse_laco = True
    t19 = time.monotonic()
    sse19 = urllib.request.urlopen(urllib.request.Request(base, data=json.dumps({"model": "seth", "stream": True,
        "messages": [{"role": "user", "content": "oi"}]}).encode(), headers=hdr), timeout=30).read().decode("utf-8")
    dt19 = time.monotonic() - t19
    txt19 = "".join(json.loads(l[6:])["choices"][0]["delta"].get("content") or ""
                    for l in sse19.splitlines() if l.startswith("data: {") and "choices" in l and "keepalive" not in l)
    ok19a = (len(txt19) < 3000 and txt19.endswith(limpa_laco.NOTA) and sse19.count("[DONE]") == 1
             and sse19.count('"finish_reason": "stop"') == 1)
    print(f"{'PASS' if ok19a else 'FALHA'}  trava de laço: {len(txt19)} caracteres chegam (sem a trava, ~1,2 milhão), "
          f"nota + finish_reason + [DONE] uma vez")
    falhas += 0 if ok19a else 1
    for _ in range(50):  # o upstream é solto: o Dummy para de escrever bem antes do fim
        if _Dummy.laco_escritos and not _Dummy.sse_laco:
            time.sleep(0.1)
            break
    ok19b = 0 < _Dummy.laco_escritos < 40000 and dt19 < 15
    print(f"{'PASS' if ok19b else 'FALHA'}  trava de laço: upstream solto ({_Dummy.laco_escritos} de 40001 fragmentos, "
          f"{dt19:.1f} s)")
    falhas += 0 if ok19b else 1
    log19 = [json.loads(l) for l in log_laco.read_text(encoding="utf-8").splitlines()] if log_laco.exists() else []
    ok19c = (len(log19) == 1 and log19[0]["cortou"] and log19[0]["eco_estado"] and log19[0]["periodo"] == len("Não cite o arquivo histórico sem `vault_consultar extras/`. ")
             and "texto" not in log19[0])
    print(f"{'PASS' if ok19c else 'FALHA'}  trava de laço: log com corte, eco do estado e período, sem texto ({log19})")
    falhas += 0 if ok19c else 1
    os.environ["SETH_TRAVA_LACO"] = "0"
    _Dummy.sse_emoji = True  # SSE comum, sem laço
    sse19d = urllib.request.urlopen(urllib.request.Request(base, data=json.dumps({"model": "seth", "stream": True,
        "messages": [{"role": "user", "content": "oi"}]}).encode(), headers=hdr), timeout=15).read().decode("utf-8")
    del os.environ["SETH_TRAVA_LACO"]
    ok19d = sse19d.count("[DONE]") == 1 and "Corte da Máquina" not in sse19d and "fim" in sse19d
    print(f"{'PASS' if ok19d else 'FALHA'}  trava de laço: SETH_TRAVA_LACO=0 desliga (resposta comum intacta)")
    falhas += 0 if ok19d else 1
    # 20. Teto de ferramentas (AC-37, 18/10/2026)
    def _hist20(n):
        h = [{"role": "user", "content": "e o laya-roteador?"}]
        for i in range(n):
            h += [{"role": "assistant", "content": "", "tool_calls": [{"id": f"t{i}", "type": "function",
                   "function": {"name": "maquina_verificar_mcp_canon", "arguments": "{}"}}]},
                  {"role": "tool", "tool_call_id": f"t{i}", "content": "ok"}]
        return h
    _ant20 = [{"role": "user", "content": "antes"}, {"role": "assistant", "content": "", "tool_calls": [{"id": "x"}]},
              {"role": "tool", "tool_call_id": "x", "content": "ok"}, {"role": "assistant", "content": "feito"}]
    _p20a = _injeta({"model": "seth-livre", "tools": [{"x": 1}], "messages": _hist20(5)})
    _p20b = _injeta({"model": "seth-livre", "tools": [{"x": 1}], "messages": _hist20(6)})
    _sys20b = " ".join(m["content"] for m in _p20b["messages"] if isinstance(m, dict) and m.get("role") == "system")
    ok20a = "tool_choice" not in _p20a and _p20b.get("tool_choice") == "none" and "TETO-FERRAMENTAS: esta resposta já fez 6" in _sys20b
    ok20b = _rodadas_ferramenta(_ant20 * 4 + _hist20(2)) == 2  # rodadas de respostas anteriores não contam
    os.environ["SETH_TETO_FERRAMENTAS"] = "0"
    _p20c = _injeta({"model": "seth-livre", "tools": [{"x": 1}], "messages": _hist20(9)})
    del os.environ["SETH_TETO_FERRAMENTAS"]
    ok20c = "tool_choice" not in _p20c and "TETO-FERRAMENTAS" not in json.dumps(_p20c, ensure_ascii=False)
    print(f"{'PASS' if ok20a else 'FALHA'}  teto de ferramentas: 5 rodadas passam, na 6ª sai tool_choice none com aviso")
    print(f"{'PASS' if ok20b else 'FALHA'}  teto de ferramentas: só conta a resposta em andamento")
    print(f"{'PASS' if ok20c else 'FALHA'}  teto de ferramentas: SETH_TETO_FERRAMENTAS=0 desliga")
    falhas += sum(0 if x else 1 for x in (ok20a, ok20b, ok20c))
    # 21. Padrão PRIV-01: cloud falha fechada sem classe pública; o alias
    # escolhido pelo Humano declara público e o marcador nunca sai ao provedor.
    _pub21 = _politica_dados_externos({"model": _ALIAS_PUBLICO, "messages": []})
    _local21 = _politica_dados_externos({"model": "ollama-local/qwen", "messages": []})
    _deny21 = False
    try:
        _politica_dados_externos({"model": "seth-rapido", "messages": []})
    except DadosExternosSemClassificacao:
        _deny21 = True
    _bad21 = False
    try:
        _politica_dados_externos({"model": "seth-rapido"}, "internal")
    except DadosExternosSemClassificacao:
        _bad21 = True
    # (22/10/2026) cascata seth-livre passa sem classificação: o proxy sanitiza
    _casc21 = _politica_dados_externos({"model": _ROTA_BASE, "messages": []})
    _casc21_ok = _casc21["model"] == _ROTA_BASE
    ok21 = (_pub21["model"] == _ROTA_BASE and "agata_data_classification" not in _pub21
            and _local21["model"] == "ollama-local/qwen" and _deny21 and _bad21 and _casc21_ok)
    print(f"{'PASS' if ok21 else 'FALHA'}  política de dados: nuvem sem classe/fora de public bloqueia; alias público e local seguem")
    # 21e (18/11/2026) llama-cpp/ e llamacpp- são locais: sem classificação passam; nuvem continua bloqueada.
    _lcpp21 = [_politica_dados_externos({"model": m, "messages": []})["model"]
               for m in ("llama-cpp/nemotron-3.5-lightning", "llamacpp-agata/qwen3-30b-a3b")]
    _nuvem21 = []
    for m in ("gemini/gemini-2.5-flash", "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"):
        try:
            _politica_dados_externos({"model": m, "messages": []})
            _nuvem21.append(False)
        except DadosExternosSemClassificacao:
            _nuvem21.append(True)
    ok21e = _lcpp21 == ["llama-cpp/nemotron-3.5-lightning", "llamacpp-agata/qwen3-30b-a3b"] and all(_nuvem21)
    print(f"{'PASS' if ok21e else 'FALHA'}  llama-cpp/ e llamacpp- entram no ramo local; nuvem sem classe continua bloqueada")
    falhas += 0 if ok21e else 1
    falhas += 0 if ok21 else 1
    _upstream_antes = _Dummy.ultimo_corpo
    _http_21 = 0
    try:
        urllib.request.urlopen(urllib.request.Request(
            base, data=json.dumps({"model": "seth-rapido", "messages": []}).encode(),
            headers={"Content-Type": "application/json"}), timeout=5).read()
    except urllib.error.HTTPError as e:
        _http_21 = e.code
        e.close()
    ok21b = _http_21 == 403 and _Dummy.ultimo_corpo == _upstream_antes
    print(f"{'PASS' if ok21b else 'FALHA'}  política de dados: HTTP 403 antes do upstream ({_http_21})")
    falhas += 0 if ok21b else 1
    _public_req = urllib.request.Request(
        base, data=json.dumps({"model": _ALIAS_PUBLICO, "messages": [{"role": "user", "content": "oi"}]}).encode(),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(_public_req, timeout=10).read()
    _public_upstream = json.loads(_Dummy.ultimo_corpo)
    ok21c = (_public_upstream.get("model") == "seth-rapido"
             and "agata_data_classification" not in _public_upstream)
    print(f"{'PASS' if ok21c else 'FALHA'}  política de dados: alias público mapeia à fila e o marcador não sai")
    falhas += 0 if ok21c else 1
    os.environ["SETH_EMOJI_REMOVER"] = "0"
    _Dummy.texto_fixo = "Pronto \u2705"
    t17d = json.loads(urllib.request.urlopen(urllib.request.Request(base, data=corpo_e, headers=hdr), timeout=10).read())["choices"][0]["message"]["content"]
    del os.environ["SETH_EMOJI_REMOVER"]
    _Dummy.texto_fixo = None
    ok17d = "\u2705" in t17d
    print(f"{'PASS' if ok17d else 'FALHA'}  E-2 chave SETH_EMOJI_REMOVER=0 devolve o texto original")
    falhas += 0 if ok17d else 1
    up.shutdown()
    gw.shutdown()
    _u = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}, {"role": "user", "content": "c"}]
    _l = "AUDITORIA-TURNO-ANTERIOR: cabeçalho: x | evidência: cita 1 entrada(s) inexistente | ação afirmada sem chamada"
    _r = _correcao_perto_da_pergunta(_u, _l)
    casos_corr = [
        ("correção vira prefixo da última pergunta", _r[-1]["content"].startswith("[Máquina") and _r[-1]["content"].endswith("c")),
        ("achado de cabeçalho fica de fora do prefixo", "cabeçalho: x" not in _r[-1]["content"]),
        ("a mensagem original não é alterada", _u[-1]["content"] == "c"),
        ("só cabeçalho -> nada", _correcao_perto_da_pergunta(_u, "AUDITORIA-TURNO-ANTERIOR: cabeçalho: x")[-1]["content"] == "c"),
        ("OK -> nada", _correcao_perto_da_pergunta(_u, "AUDITORIA-TURNO-ANTERIOR: OK")[-1]["content"] == "c"),
        ("MESMA-RESPOSTA -> nada", _correcao_perto_da_pergunta(_u, "MESMA-RESPOSTA: x")[-1]["content"] == "c"),
        ("conteúdo em lista recebe parte de texto na frente", _correcao_perto_da_pergunta(
            [{"role": "user", "content": [{"type": "text", "text": "c"}]}], _l)[-1]["content"][0]["text"].startswith("[Máquina")),
        ("última mensagem não é do usuário -> nada", _correcao_perto_da_pergunta(
            _u + [{"role": "tool", "content": "t"}], _l)[-1]["content"] == "t"),
    ]
    os.environ["SETH_CORRECAO_NA_PERGUNTA"] = "0"
    casos_corr.append(("SETH_CORRECAO_NA_PERGUNTA=0 desliga", _correcao_perto_da_pergunta(_u, _l)[-1]["content"] == "c"))
    del os.environ["SETH_CORRECAO_NA_PERGUNTA"]
    _e = {}
    for _ln in (b'data: {"id":"a","model":"qwen3.5-9b-64k:latest","choices":[{"delta":{"reasoning":"Resultado: "}}]}',
                b'data: {"id":"a","choices":[{"delta":{"reasoning":"ativo."}}]}', b'data: {"choices":[{"delta":{"content":""}}]}'):
        _resgate_observar(_ln, _e)
    _ch = _resgate_chunk(dict(_e), "CAB\n\n")
    _e2 = {}
    _resgate_observar(b'data: {"choices":[{"delta":{"reasoning":"pensando"}}]}', _e2)
    _resgate_observar(b'data: {"choices":[{"delta":{"content":"Resposta"}}]}', _e2)
    _e3 = {}
    _resgate_observar(b'data: {"choices":[{"delta":{"reasoning":"vou chamar"}}]}', _e3)
    _resgate_observar(b'data: {"choices":[{"delta":{"tool_calls":[{"index":0}]}}]}', _e3)
    # M6a pelo caminho real (_enviar + _liberar_retidos), na ordem em que o stream chega linha a linha.
    _h = _Handler.__new__(_Handler)
    _h.wfile, _h._reter, _h._retidos, _h._texto_maquina, _h._msgs_pedido = io.BytesIO(), True, [], "", []
    for _l in (b'data: {"choices":[{"delta":{"content":"ok"}}]}\n', b"\n", b": ka\n", b"\n", b"data: [DONE]\n", b"\n"):
        _h._enviar(_l)
    _h._liberar_retidos()
    _sse, _resto = b"", _h.wfile.getvalue()
    while _resto:
        _tam, _resto = _resto.split(b"\r\n", 1)
        _sse, _resto = _sse + _resto[:int(_tam, 16)], _resto[int(_tam, 16) + 2:]
    casos_corr += [
        ("M6a: dado retido sai com o separador colado (evento fechado antes do [DONE])",
         b'"ok"}}]}\n\n' in _sse and _sse.endswith(b"data: [DONE]\n\n") and _sse.startswith(b": ka\n")),
        ("M6a: linha vazia sozinha fica retida; keepalive passa", not _so_comentario(b"\n") and _so_comentario(b": ka\n")),
        ("resgate: só raciocínio vira texto (com o cabeçalho pendente)", _ch is not None and
         json.loads(_ch[6:].decode())["choices"][0]["delta"]["content"] == "CAB\n\nResultado: ativo."),
        ("resgate: com texto do modelo -> nada", _resgate_chunk(_e2) is None),
        ("resgate: com chamada de ferramenta -> nada", _resgate_chunk(_e3) is None),
        ("resgate: sem raciocínio -> nada", _resgate_chunk({}) is None),
        ("M6a: texto juntado do SSE retido, sem o [DONE]", _texto_do_sse([
            b'data: {"choices":[{"delta":{"content":"Ol"}}]}\n\n', b': ka\n',
            b'data: {"choices":[{"delta":{"content":"\xc3\xa1"}}]}\n\ndata: [DONE]\n\n']) == "Olá"),
        ("M6a: keepalive passa, dado fica retido", _so_comentario(b": ka\n\n") and not _so_comentario(b"data: {}\n\n")),
        ("M6a: bloco com os achados e chunk válido", "Verificação da Máquina" in _bloco_verificacao(["x"])
         and json.loads(_chunk_texto("t")[6:].decode())["choices"][0]["delta"]["content"] == "t"),
        ("resgate sem stream: só raciocínio vira content", json.loads(_resgate_json(
            b'{"model":"qwen3.5-9b-64k:latest","choices":[{"message":{"content":"","reasoning":" ativo. "}}]}'))["choices"][0]["message"]["content"] == "ativo."),
        ("resgate: modelo remoto (Gemini, raciocínio em inglês) -> nada, no stream e fora dele",
         _resgate_chunk({"model": "gemini-3.5-flash-lite", "raciocinio": "Checking Service Status"}) is None
         and _resgate_json(b'{"model":"gemini-3.5-flash-lite","choices":[{"message":{"content":"","reasoning":"r"}}]}')
         == b'{"model":"gemini-3.5-flash-lite","choices":[{"message":{"content":"","reasoning":"r"}}]}'),
        ("resgate: lista local sai do registro (com e sem prefixo)", _modelo_local("qwen3.5-9b-64k:latest")
         and _modelo_local("ollama-local/qwen3.5-9b-64k:latest") and not _modelo_local("codestral-latest")
         and not _modelo_local(None)),
        ("resgate sem stream: com texto, com ferramenta ou corpo inválido -> intacto",
         _resgate_json(b'{"choices":[{"message":{"content":"x","reasoning":"r"}}]}') == b'{"choices":[{"message":{"content":"x","reasoning":"r"}}]}'
         and _resgate_json(b'{"choices":[{"message":{"content":"","tool_calls":[{}],"reasoning":"r"}}]}')
         == b'{"choices":[{"message":{"content":"","tool_calls":[{}],"reasoning":"r"}}]}' and _resgate_json(b"nao") == b"nao"),
    ]
    _l2 = "AUDITORIA-TURNO-ANTERIOR: cabeçalho: x | evidência: cita 1 entrada(s) inexistente"
    casos_corr.append(("correção da Máquina: por padrão nada vai ao Humano (só ao contexto do modelo)",
                       _correcao_da_maquina(_l2) == ""))
    os.environ["SETH_CORRECAO_VISIVEL"] = "1"
    casos_corr += [
        ("correção da Máquina: linha com o achado, sem o de cabeçalho",
         _correcao_da_maquina(_l2) == "Correção do turno anterior (pela Máquina): evidência: cita 1 entrada(s) inexistente\n\n"),
        ("correção da Máquina: passo final do Agent com correção pendente",
         _correcao_da_maquina("MESMA-RESPOSTA: x. AINDA FALTA corrigir o turno anterior: ação afirmada sem chamada")
         == "Correção do turno anterior (pela Máquina): ação afirmada sem chamada\n\n"),
        ("correção da Máquina: só cabeçalho / OK / MESMA-RESPOSTA -> nada",
         _correcao_da_maquina("AUDITORIA-TURNO-ANTERIOR: cabeçalho: x") == "" and _correcao_da_maquina(
             "AUDITORIA-TURNO-ANTERIOR: OK") == "" and _correcao_da_maquina("MESMA-RESPOSTA: x") == ""),
    ]
    os.environ["SETH_CORRECAO_MAQUINA"] = "0"
    casos_corr.append(("correção da Máquina: SETH_CORRECAO_MAQUINA=0 desliga", _correcao_da_maquina(_l2) == ""))
    del os.environ["SETH_CORRECAO_MAQUINA"]
    del os.environ["SETH_CORRECAO_VISIVEL"]
    for _n, _ok in casos_corr:
        print(f"{'PASS' if _ok else 'FALHA'}  correção perto da pergunta: {_n}")
        falhas += 0 if _ok else 1
    print(f"\n{'SELFTEST OK' if not falhas else f'SELFTEST FALHOU ({falhas})'}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        raise SystemExit(_selftest())
    servir()
