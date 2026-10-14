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
    "**Personalidade** (PROJETO, \"Personalidade da Seth\"; MEMÓRIAS (685)): a "
    "operadora técnica do sistema — precisa, calma, direta; humor seco raro (no "
    "máximo uma linha; nunca em incidente, nunca às custas do Humano). Responda "
    "em três tempos: **resultado** primeiro; depois a **evidência** (comando, "
    "`arquivo:linha`, medição — ou \"não medido\"); depois o **próximo passo** ou "
    "a decisão que cabe ao Humano. Uma recomendação com o porquê, não um "
    "cardápio. Ação com efeito: leia de volta objeto, alcance e efeito, e espere "
    "confirmação explícita. Para qualquer público: sem muletas (\"né\", \"tá?\", "
    "\"viu?\", \"tipo,\", \"olha,\"), sem interjeição, sem emoji, sem exclamação "
    "em série, sem tom sedutor; não invente biografia nem experiência humana. "
    "Abrir com status (\"Sistemas operacionais.\") não é saudação; \"Bem-vindo "
    "de volta\" é.\n"
    "**Evidência só do que existe** (MEMÓRIAS (687)/(688)): o que uma ferramenta "
    "devolveu NESTA conversa, ou o bloco de estado abaixo. Sem isso, escreva "
    "\"não medido\" — nunca invente comando, saída, JSON, arquivo, linha ou serviço "
    "para preencher o espaço. Sem ferramenta à mão, o próximo passo é dizer com "
    "qual ferramenta mediria. A auditoria do turno confere: ferramenta citada "
    "como fonte sem ter sido chamada é acusada no turno seguinte (MEMÓRIAS (690)). "
    "**Pendente é só o que a linha `PROPOSTAS-PENDENTES` do estado lista** — entrada "
    "antiga de MEMÓRIAS descreve o que era pendente naquele dia (MEMÓRIAS (695)).\n\n"
    "**Regra 1 — abra TODA resposta com o cabeçalho. São DUAS formas, e você "
    "usa UMA, nunca as duas juntas** (PROTOCOLOS, \"Carregar e formatos\": "
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
    "`Agata · <modelo> · t=<n> (contado no contexto) · <hora + selo>`\n"
    "  Base entre parênteses: só `contado no contexto` (o normal), `contador "
    "mecânico` ou `prefixo compactado` — nunca o próprio número, como `t=3 (3)`.\n"
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
    "não o par pergunta-resposta). Contexto compactado/resumido: "
    "`t≥<n> (prefixo compactado)`. Não use contador de outra sessão.\n"
    "— **sync:** copie a linha `sync:` do bloco de estado **INTEIRA**, com os "
    "campos, nunca só a palavra. `sync: PASS` sozinho é ERRO: PROTOCOLOS, \"'sync' "
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
    "`perimetro` (os controles do perímetro), `estado`, `git_status`, `git_log`, "
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
    "**Buscar: o vault é a prioridade 1 (decisão do Humano, (670)).** Para ACHAR "
    "algo na memória, comece por `vault_buscar` (por sentido — acha sem a palavra "
    "exata — e por texto, no disco); navegue pela nota (`cita`, `citada_por`, "
    "`parecidas`, trechos `#^bN`) com `vault_consultar`; e só então CITE, "
    "confirmando o texto exato com `query_canon` (o vault é derivado; o canon é "
    "a fonte). A listagem de diretório do vault vem do disco desde (670) — não "
    "está mais atrasada; a leitura de ferramenta vem inteira desde (668) "
    "(`[N linha(s), completo]`). Não chame isso de limitação. **Ao avaliar ou "
    "descrever o sistema de memórias, TESTE a busca na mesma resposta** — uma "
    "chamada de `vault_buscar` sobre o tema avaliado — e relate o que ela "
    "devolveu; sem esse teste, não afirme nada sobre vault ou busca ((676)). O "
    "vault é regenerado a cada commit (não há ciclo noturno); PR juntado no "
    "GitHub já está publicado. "
    "**Sobre o próprio sistema, nunca de memória ((678)):** arquitetura, "
    "controles, regras, fluxo — consulte no MESMO turno (`query_canon`, "
    "`vault_buscar`, `maquina_verificar perimetro`); controle P-N só com a "
    "descrição lida (são 23, e o número muda). **Estado da arte / sistemas "
    "iguais:** use o navegador (`tool_search` \"navegador\") e cite a fonte de "
    "cada item; sem fonte, escreva `não verificado`. `extras/` (arquivo "
    "histórico, inteiro) se lê com `vault_consultar extras/`.\n\n"
    "**Antes de dizer que algo FALTA no sistema, procure:** entradas por data ou "
    "tema estão no `INDICE_MEMORIAS` e no `INDICE_MEMORIAS_PALAVRAS-CHAVE` "
    "(`query_canon`); o vault já é conferido contra o HEAD (P-10) e a hidratação "
    "pelo `HASH-ESTADO`; e o que foi recusado de propósito está na \"Fronteira de "
    "recusas\" (`PROJETO_REFERENCIA`). Falta que já existe ou foi recusada é "
    "afirmação errada, não sugestão (MEMÓRIAS (660)).\n\n"
    "**AUDITORIA-TURNO-ANTERIOR:** se o bloco de estado trouxer essa linha com "
    "achados, a Máquina conferiu a SUA resposta anterior e achou erro. Logo "
    "depois do cabeçalho, corrija em 1 linha (`Correção do turno anterior: …`) "
    "e siga; acerte o cabeçalho desta resposta. `OK` = nada a corrigir. "
    "\"afirmação já desmentida\" = algo que você disse e a Máquina já provou "
    "falso: não repita, nem como \"mantido\" — use a correção que vem junto. "
    "(MEMÓRIAS (662)/(664).)\n"
    "**MESMA-RESPOSTA:** se vier essa linha, você está no meio da sua resposta, "
    "depois de usar ferramenta: continue o texto, SEM cabeçalho novo e sem "
    "repetir a correção. Uma resposta tem um cabeçalho só. **Se a resposta vai "
    "usar ferramenta, chame a ferramenta ANTES de escrever qualquer texto** — o "
    "cabeçalho e o texto vêm uma vez só, depois das ferramentas ((682): o "
    "cabeçalho escrito antes da ferramenta saía repetido depois dela).\n\n"
    "**MODO (linha do estado):** `conciso` é o padrão — a resposta traz o resultado e "
    "não narra o processo (\"vou verificar…\", \"agora vou…\"); fale do processo só "
    "para constatar erro, em 1 linha. `explicativo` só quando o Humano pedir na "
    "conversa. Narração custa duas vezes: na saída e em toda mensagem seguinte, "
    "porque fica no histórico — e economia de tokens é permanente (Regra 7). "
    "(REGRAS, \"NPR\"; MEMÓRIAS (667).)\n"
    "**Plugins sob demanda:** Discord e navegador não aparecem na sua lista de "
    "ferramentas até você precisar — busque com `tool_search` (ex.: \"navegador\", "
    "\"discord\") e use. As do canon estão sempre carregadas. (MEMÓRIAS (666).)\n\n"
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
        return "\n".join(linhas + [_linha_propostas()])
    except Exception:
        return ""


def _linha_propostas() -> str:
    """(695) Nomes das propostas abertas (`.diff` sem `APROVADO-`) -- a Seth afirmava
    pendente o que já estava em propostas/aplicadas/, lendo uma entrada antiga."""
    pasta = REPO / "propostas"
    abertas = sorted(d.stem for d in pasta.glob("*.diff") if not (pasta / f"APROVADO-{d.stem}").exists())
    assinadas = sorted(d.stem for d in pasta.glob("*.diff") if (pasta / f"APROVADO-{d.stem}").exists())
    return ("PROPOSTAS-PENDENTES: " + (", ".join(abertas) if abertas else "nenhuma")
            + (f" · assinadas, falta aplicar: {', '.join(assinadas)}" if assinadas else "")
            + " · o que está em propostas/aplicadas/ NÃO está pendente")


def _hidratacao(extra: str = "") -> str:
    """Modo compacto (default): cabeçalho + estado atual. Modo full: o arquivo inteiro.
    `extra`: linhas do turno anterior (ex.: AUDITORIA-TURNO-ANTERIOR) que vão no estado."""
    if MODO == "compacto":
        est = _estado()
        # Regra 1.1: campo medível não pode sumir em silêncio quando a
        # medição falha -- antes, `est` vazio só omitia o bloco inteiro sem
        # dizer que algo quebrou (achado 04/09/2026, Camada C).
        if est:
            linha_modelo = _linha_modelo_real_anterior()
            corpo = est + (f"\n{linha_modelo}" if linha_modelo else "") + (f"\n{extra}" if extra else "")
            bloco_estado = f"**Estado agora (fatos da Máquina):**\n{corpo}\n"
        else:
            bloco_estado = ("**Estado agora:** `lacuna: estado_para_eco.sh falhou ou não rodou "
                             "(sem shell/Máquina daqui?) — não afirme HEAD/sync sem medir.`\n"
                             + (f"{extra}\n" if extra else ""))
        return f"{MARCADOR}\n{_DOUTRINA_FIXA}{bloco_estado}"
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
    linha_modelo = _linha_modelo_real_anterior()
    corpo = est + (f"\n{linha_modelo}" if linha_modelo else "") + (f"\n{extra}" if extra else "")
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
    # (682) passo depois de ferramenta é a MESMA resposta: classifica só até o
    # último pedido do usuário. Antes, o resultado da ferramenta e as mensagens a
    # mais viravam "pesado" e a resposta trocava de fila no meio (seth-livre no
    # passo 1, seth-pesado no passo 2 -- medido no teste de 13/10, 21:59).
    if auditoria_turno.e_continuacao(msgs):
        ult = max((i for i, m in enumerate(msgs) if isinstance(m, dict) and m.get("role") == "user"),
                  default=len(msgs) - 1)
        msgs = msgs[:ult + 1]
    total, n_user, codigo = _texto_e_sinais(msgs)
    if total > _LIMIAR_PESADO_CHARS or codigo or len(msgs) > _LIMIAR_PESADO_MSGS:
        return "seth-pesado"
    if total < _LIMIAR_TRIVIAL_CHARS and not tem_tools and n_user <= 2:
        return "seth-rapido"
    return _ROTA_BASE


# --- Roteador-sombra: decisor local (PROJETO.md, "Decisor local") -----------
# O modelo de decisão escolhe a rota pelo SIGNIFICADO do pedido; as travas
# exatas abaixo continuam valendo por cima dele. Hoje só em SOMBRA: decide numa
# thread fora do caminho da resposta (winnow:e4b leva ~4 s na CPU) e registra em
# ~/.cache/agata/decisor/roteador.jsonl. A resposta segue pela heurística.
import decisor  # noqa: E402  (mesmo diretório)
import auditoria_turno  # noqa: E402  (mesmo diretório)
import capivara_perfis  # noqa: E402  (scripts/, já no sys.path: perfis de janela por modelo, (667))

_PERFIS = {"mtime": None, "dados": {}}


def _perfis() -> dict:
    caminho = REPO / "config" / "capivara" / "perfis-modelos.json"
    try:
        mt = caminho.stat().st_mtime
    except OSError:
        return {}
    if _PERFIS["mtime"] != mt:
        _PERFIS["dados"], _PERFIS["mtime"] = capivara_perfis.carregar(caminho), mt
    return _PERFIS["dados"]


def _fila_pela_janela(payload: dict) -> str | None:
    """`<fila>-longo` quando o pedido (já hidratado) não cabe no menor modelo da fila
    base -- o LibreChat não sabe qual modelo da fila vai responder, o gateway sabe a fila
    (667). None = fica como está (pedido cabe, fila fora do perfil, sem fila longa)."""
    modelo = str(payload.get("model", ""))
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
_SOMBRA_LIVRE = threading.Semaphore(1)


def _rota_com_travas(escolhida: str | None, payload: dict) -> str:
    """Rota final a partir da escolha do modelo, com as travas exatas por cima.
    Sem escolha (confiança baixa, decisor fora) -> heurística de sempre."""
    if escolhida is None:
        return _classificar_rota(payload)
    msgs = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    total, _, _ = _texto_e_sinais(msgs)
    if total > _LIMIAR_PESADO_CHARS or len(msgs) > _LIMIAR_PESADO_MSGS:
        return "seth-pesado"
    if escolhida == "rapido" and payload.get("tools"):
        return "seth-livre"
    return f"seth-{escolhida}"


def _ultimo_texto_usuario(msgs: list) -> str:
    for m in reversed(msgs):
        if isinstance(m, dict) and m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, list):
                return " ".join(p.get("text", "") for p in c if isinstance(p, dict))
            return c if isinstance(c, str) else ""
    return ""


def _sombra_rota(payload: dict, rota_heuristica: str) -> None:
    """Dispara a decisão-sombra sem esperar. Uma por vez: se o decisor ainda
    está ocupado, este pedido fica sem sombra (nunca empilha CPU)."""
    if not _SOMBRA_LIVRE.acquire(blocking=False):
        return
    msgs = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    # Cópia AGORA: logo depois o `_injeta` põe a hidratação (~4 mil chars) no
    # mesmo `payload`, e a trava de tamanho leria tudo como "pesado" (13/10/2026,
    # MEMÓRIAS (657)).
    pedido = {"messages": list(msgs), "tools": payload.get("tools")}
    texto = _ultimo_texto_usuario(msgs)[-4000:]
    total, n_user, cerca = _texto_e_sinais(msgs)
    meta = {"heuristica": rota_heuristica, "chars": total, "n_msgs": len(msgs),
            "n_user": n_user, "cerca_codigo": cerca, "tools": bool(payload.get("tools"))}

    def _rodar():
        try:
            if not texto:
                return
            r = decisor.decidir("roteador", texto, _PERGUNTA_ROTA, meta=meta)
            escolhida = decisor.escolha(r, "rota", _LIMIAR_ROTA)
            final = _rota_com_travas(escolhida, pedido)
            if escolhida is not None and final != rota_heuristica:
                # avaliação em produção: o Humano julga as divergências
                decisor.registrar_avaliacao("roteador", {
                    "heuristica": rota_heuristica, "modelo": final,
                    "confianca": r["rota"]["confidence"], "chars": total,
                    "trecho": texto[:200]})
        finally:
            _SOMBRA_LIVRE.release()

    threading.Thread(target=_rodar, daemon=True).start()


def _injeta(payload: dict) -> dict:
    msgs = payload.get("messages")
    if not isinstance(msgs, list):
        return payload
    # chamada de título/utilidade do frontend: repassa crua, sem hidratar.
    if _e_chamada_utilitaria(payload):
        return payload
    # resposta anterior do assistente conferida aqui, antes de mexer em `msgs` (662)
    auditoria = auditoria_turno.linha_estado(msgs, str(payload.get("model", "")))
    auditoria = auditoria_turno.linha_modo(msgs) + (f"\n{auditoria}" if auditoria else "")
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
        bloco = _bloco_estado_atual(auditoria)
        payload["messages"] = ([{"role": "system", "content": bloco}] + msgs
                               if bloco else msgs)
        return payload
    sys_msg = {"role": "system", "content": _hidratacao(auditoria)}
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
        # estado por REQUISIÇÃO: com keep-alive o mesmo handler atende vários
        # pedidos, e uma rota velha vazaria pro header X-Seth-Rota do seguinte
        self._rota = ""
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
                    # 1 decisão por resposta: no modo Agent os passos depois de
                    # ferramenta são a mesma resposta (664)
                    if not _e_chamada_utilitaria(payload) and not auditoria_turno.e_continuacao(
                            payload.get("messages") or []):
                        _sombra_rota(payload, self._rota)
                    payload["model"] = self._rota
                # (697) sem tool_choice "required": o Nemotron (seth-pesado) passou a escrever a
                # chamada de ferramenta como TEXTO e a conversa travou (14/10, 15:26-15:28).
                payload = _injeta(payload)
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

    def _log(self, msg: str, t0: float):
        """(682) Erro e desconexão vão para o journal (antes nada era registrado:
        uma resposta que morreu no meio não deixava rastro aqui)."""
        print(f"gateway: {msg} · rota={self._rota or '-'} · {time.monotonic() - t0:.1f}s · {self.path}",
              file=sys.stderr, flush=True)

    # (695) 200 sem texto nem ferramenta (Gemini, 14/10 15:00:12: "succeeded" em 2,4 s e o
    # LibreChat gravou resposta vazia). Nada foi enviado ao cliente ainda: tenta 1 vez a
    # fila seguinte. Só nas filas da Seth; o resto passa como veio.
    _SUBIR_FILA = {"seth-rapido": "seth-livre", "seth-livre": "seth-pesado", "seth-pesado": "seth-livre"}

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

    def _passar(self, corpo: bytes, metodo: str, tentativa: int = 0):
        t0 = time.monotonic()
        url = UPSTREAM + self.path
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in _HOP_BY_HOP}
        headers["X-Agata-Token"] = _token_interno()
        req = urllib.request.Request(url, data=corpo or None, method=metodo, headers=headers)
        try:
            up = urllib.request.urlopen(req, timeout=180)
        except urllib.error.HTTPError as e:
            up = e
            self._log(f"upstream HTTP {e.code}", t0)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            self._log(f"upstream inacessível ({e})", t0)
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
                # (695) espia até o 1º conteúdo útil, não só até o "model": sem isso
                # não dá para saber, antes de responder, se a resposta veio vazia.
                fim = False
                for _ in range(self._PEEK_MAX_PEDACOS):
                    pedaco = up.read(8192)
                    if not pedaco:
                        fim = True
                        break
                    buf_pre += pedaco
                    modelo_real = modelo_real or self._modelo_de_bytes(buf_pre)
                    if modelo_real and self._tem_conteudo(buf_pre, True):
                        break
                vazio = fim and up.status == 200 and not self._tem_conteudo(buf_pre, True)
            else:
                buf_pre = up.read()
                modelo_real = self._modelo_de_bytes(buf_pre)
                vazio = up.status == 200 and not self._tem_conteudo(buf_pre, False)
            if vazio and tentativa == 0 and self._rota in self._SUBIR_FILA:
                try:
                    pl = json.loads(corpo)
                    pl["model"] = self._rota = self._SUBIR_FILA[self._rota]
                except ValueError:
                    pl = None
                if pl is not None:
                    self._log(f"resposta vazia (modelo {modelo_real or '?'}) -> nova tentativa", t0)
                    up.close()
                    return self._passar(json.dumps(pl, ensure_ascii=False).encode("utf-8"), metodo, 1)
        except (BrokenPipeError, ConnectionResetError):
            self._log("cliente desconectou antes da 1ª resposta do modelo", t0)
            self.close_connection = True
            up.close()
            return
        except (TimeoutError, OSError) as e:
            self._log(f"upstream parou de responder ({e})", t0)
            up.close()
            return self._erro(504, f"upstream parou de responder: {e}")
        self.send_response(up.status)
        for k, v in up.headers.items():
            if k.lower() not in _HOP_BY_HOP:
                self.send_header(k, v)
        if self._rota:
            self.send_header("X-Seth-Rota", self._rota)
        if modelo_real:
            self.send_header("X-Modelo-Real", modelo_real)
            _lembrar_modelo_real(modelo_real)
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
            self._log(f"cliente desconectou no meio do stream (modelo {modelo_real or '?'})", t0)
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
    vazias = 0          # (695) quantas respostas vazias dar antes da normal
    modelos_pedidos = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        type(self).ultimo_corpo = self.rfile.read(n)
        try:
            type(self).modelos_pedidos.append(json.loads(type(self).ultimo_corpo).get("model"))
        except ValueError:
            pass
        texto = "ok"
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

    # 1b. (683) campo `user` do LibreChat não chega ao OmniRoute (Mistral: 422)
    body_u = json.dumps({"model": "seth", "user": "6a99c85", "messages": [
        {"role": "user", "content": "oi"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body_u, headers={"Content-Type": "application/json"}), timeout=10).read()
    ok1b = "user" not in json.loads(_Dummy.ultimo_corpo)
    print(f"{'PASS' if ok1b else 'FALHA'}  campo `user` retirado antes do OmniRoute")
    falhas += 0 if ok1b else 1

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

    # 3. chamada de TÍTULO do LibreChat (titleMethod structured: schema com "title")
    #    -> repassada crua, SEM system hidratado
    body3 = json.dumps({"model": "seth", "messages": [
        {"role": "user", "content": "User: oi\nAssistant: ok"}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "title", "schema": {
            "type": "object", "properties": {"title": {"type": "string"}},
            "required": ["title"]}}}}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body3, headers={"Content-Type": "application/json"}), timeout=10).read()
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
        base, data=body3c, headers={"Content-Type": "application/json"}), timeout=10).read()
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
        base, data=body3d, headers={"Content-Type": "application/json"}), timeout=10).read()
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
        ("rapido com tools -> seth-livre", _rota_com_travas(
            "rapido", {"tools": [{"x": 1}], **curto}), "seth-livre"),
    ]
    for desc, deu, quer in travas:
        ok = deu == quer
        print(f"{'PASS' if ok else 'FALHA'}  trava: {desc} (deu {deu})")
        falhas += 0 if ok else 1

    # 9c. sombra com decisor fora do ar: o pedido passa pela heurística, sem esperar
    import time as _t
    _url_antes, decisor.URL = decisor.URL, "http://127.0.0.1:9"
    _log_antes, decisor.LOG_DIR = decisor.LOG_DIR, Path(tempfile.mkdtemp())
    t0 = _t.monotonic()
    urllib.request.urlopen(urllib.request.Request(base, data=json.dumps(
        {"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}]}).encode(),
        headers={"Content-Type": "application/json"}), timeout=10).read()
    dt = _t.monotonic() - t0
    rota_sombra = json.loads(_Dummy.ultimo_corpo)["model"]
    decisor.URL, decisor.LOG_DIR = _url_antes, _log_antes
    ok9c = rota_sombra == "seth-rapido" and dt < 2
    print(f"{'PASS' if ok9c else 'FALHA'}  sombra com decisor fora -> heurística, "
          f"sem bloquear (rota {rota_sombra}, {dt * 1000:.0f} ms)")
    falhas += 0 if ok9c else 1

    # 9d. caminho completo (pedido real, hidratação injetada, thread): a trava de
    # tamanho tem de ver o pedido do usuário, não o pedido já hidratado (657).
    _decidir_antes, _log_antes = decisor.decidir, decisor.LOG_DIR
    _hid_antes = globals()["_hidratacao"]
    globals()["_hidratacao"] = lambda extra="": MARCADOR + "\n" + "h" * 9000  # a real tem ~8,8 mil
    decisor.LOG_DIR = Path(tempfile.mkdtemp())
    divs = decisor.LOG_DIR / "roteador-avaliacao.jsonl"

    def _sombra_com(escolha_falsa):
        def _falso(*a, **k):
            _t.sleep(0.3)  # o real leva ~4 s: o `_injeta` já mexeu no pedido quando ele volta
            return {"rota": {"type": "choice", "choice": escolha_falsa, "confidence": 0.95}}
        decisor.decidir = _falso
        urllib.request.urlopen(urllib.request.Request(base, data=json.dumps(
            {"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}]}).encode(),
            headers={"Content-Type": "application/json"}), timeout=10).read()
        for _ in range(50):  # espera a thread de sombra soltar o semáforo
            if _SOMBRA_LIVRE.acquire(blocking=False):
                _SOMBRA_LIVRE.release()
                break
            _t.sleep(0.05)
        return divs.read_text().splitlines() if divs.exists() else []

    ok9d = _sombra_com("rapido") == []
    linhas = _sombra_com("pesado")
    ok9e = len(linhas) == 1 and json.loads(linhas[0])["modelo"] == "seth-pesado"
    decisor.decidir, decisor.LOG_DIR = _decidir_antes, _log_antes
    globals()["_hidratacao"] = _hid_antes
    print(f"{'PASS' if ok9d else 'FALHA'}  sombra pelo caminho completo: 'oi' = rapido "
          f"não vira divergência (hidratação não conta na trava)")
    print(f"{'PASS' if ok9e else 'FALHA'}  sombra pelo caminho completo: modelo diz pesado "
          f"-> 1 divergência registrada")
    falhas += (0 if ok9d else 1) + (0 if ok9e else 1)

    # 9f. auditoria do turno anterior pelo caminho completo (662): resposta anterior
    # com cabeçalho errado -> o pedido seguinte leva AUDITORIA-TURNO-ANTERIOR.
    _aud_log = auditoria_turno.LOG
    auditoria_turno.LOG = Path(tempfile.mkdtemp()) / "aud.jsonl"
    urllib.request.urlopen(urllib.request.Request(base, data=json.dumps({"model": "seth", "messages": [
        {"role": "user", "content": "oi"},
        {"role": "assistant", "content": "Agata · m · t=1 · 2026-10-13 12:43 -0300 (relógio da Máquina)\n\nok"},
        {"role": "user", "content": "e agora?"}]}).encode(),
        headers={"Content-Type": "application/json"}), timeout=10).read()
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
        headers={"Content-Type": "application/json"}), timeout=10).read()
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
    globals()["_perfis"] = lambda: {"filas": {"seth-pesado": ["a/grande", "ollama-local/x"]},
                                    "modelos": {"a/grande": {"janela": 1000000}, "ollama-local/x": {"janela": 65536}}}
    curto = {"model": "seth-pesado", "messages": [{"role": "user", "content": "oi"}]}
    grande = {"model": "seth-pesado", "messages": [{"role": "user", "content": "z" * 200000}]}
    fora = {"model": "seth-codigo", "messages": [{"role": "user", "content": "z" * 200000}]}
    ok9h = (_fila_pela_janela(curto) is None and _fila_pela_janela(grande) == "seth-pesado-longo"
            and _fila_pela_janela(fora) is None)
    globals()["_perfis"] = _perfis_antes
    print(f"{'PASS' if ok9h else 'FALHA'}  fila pela janela: curto fica, grande vai pro -longo, fora do perfil não muda")
    falhas += 0 if ok9h else 1

    # 9i. modo conciso padrão e explicativo pedido pelo Humano chegam ao estado (667)
    def _sys_de(msgs):
        urllib.request.urlopen(urllib.request.Request(base, data=json.dumps({"model": "seth", "messages": msgs}).encode(),
                                                      headers={"Content-Type": "application/json"}), timeout=10).read()
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

    # 13. keep-alive: a rota de um pedido não vaza pro X-Seth-Rota do seguinte.
    # Mesma conexão HTTP/1.1, mesmo handler: 1º pedido seth-livre (classificado),
    # 2º pedido seth-codigo (não classificado) -- este não pode sair com rota.
    import http.client
    c13 = http.client.HTTPConnection("127.0.0.1", gw_port, timeout=10)
    rotas13 = []
    for modelo13 in (_ROTA_BASE, "seth-codigo"):
        c13.request("POST", "/v1/chat/completions", body=json.dumps({
            "model": modelo13, "messages": [{"role": "user", "content": "oi"}]}),
            headers={"Content-Type": "application/json"})
        r13 = c13.getresponse()
        r13.read()
        rotas13.append(r13.getheader("X-Seth-Rota"))
    c13.close()
    ok13 = bool(rotas13[0]) and rotas13[1] is None
    print(f"{'PASS' if ok13 else 'FALHA'}  keep-alive: rota não vaza pro pedido seguinte {rotas13}")
    falhas += 0 if ok13 else 1

    # 14. (695) resposta vazia -> 1 nova tentativa, fila acima; o cliente recebe a 2ª
    _Dummy.vazias, _Dummy.modelos_pedidos = 1, []
    body = json.dumps({"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}]}).encode()
    r14 = json.loads(urllib.request.urlopen(urllib.request.Request(
        base, data=body, headers={"Content-Type": "application/json"}), timeout=10).read())
    ok14 = (r14["choices"][0]["message"]["content"] == "ok"
            and _Dummy.modelos_pedidos == ["seth-rapido", "seth-livre"])
    print(f"{'PASS' if ok14 else 'FALHA'}  resposta vazia -> nova tentativa na fila acima "
          f"({_Dummy.modelos_pedidos})")
    falhas += 0 if ok14 else 1
    # 16. (695) linha de propostas no estado
    ok16 = _linha_propostas().startswith("PROPOSTAS-PENDENTES: ") and "propostas/aplicadas/" in _linha_propostas()
    print(f"{'PASS' if ok16 else 'FALHA'}  PROPOSTAS-PENDENTES no estado: {_linha_propostas()[:80]}")
    falhas += 0 if ok16 else 1
    up.shutdown()
    gw.shutdown()
    print(f"\n{'SELFTEST OK' if not falhas else f'SELFTEST FALHOU ({falhas})'}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        raise SystemExit(_selftest())
    servir()
