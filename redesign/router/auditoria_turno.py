#!/usr/bin/env python3
"""Auditoria determinística do turno anterior da Seth e do Goose (MEMÓRIAS (662), (664)).

O LibreChat e o Goose mandam a conversa inteira a cada pedido, então a resposta
anterior do assistente chega ao `seth_gateway` junto com a pergunta nova. Aqui
ela é conferida com checagens que já existem -- nenhuma chamada de modelo,
milissegundos -- e o resultado volta ao bloco de estado como
`AUDITORIA-TURNO-ANTERIOR:`, para o modelo se corrigir (mesmo mecanismo do
`MODELO-REAL-TURNO-ANTERIOR`, (621)).

**Turno, não mensagem (664).** No modo Agent uma resposta são vários pedidos ao
gateway (texto -> ferramenta -> texto). "Turno anterior" é tudo o que o
assistente escreveu entre o penúltimo e o último pedido do usuário. Pedido que
chega DEPOIS de o assistente já ter começado a responder (há mensagem de
assistente ou de ferramenta depois do último pedido do usuário) é continuação da
mesma resposta: não se reaudita nada, e o estado leva `MESMA-RESPOSTA`.

Confere no turno anterior:
- cabeçalho: `verificar()` de `scripts/verificar_cabecalho.py`;
- forma no lugar certo: 1ª resposta = bloco de prontidão; as outras = linha de turno;
- um cabeçalho só por resposta;
- `t=<n> (contado no contexto)` contra o número real de respostas;
- hora igual à de um cabeçalho de turno anterior (hora herdada);
- nome de modelo concreto sem a ressalva "medido no turno anterior" (621);
- afirmação já desmentida: catálogo `afirmacoes_desmentidas.json`;
- citação `arquivo:linha` com trecho (P-19), só para extensões conhecidas.
NÃO confere afirmação falsa nova em prosa (não determinístico) -- quando uma for
achada à mão, vira linha do catálogo.

Log por turno em `~/.cache/agata/auditoria-turno.jsonl` (achados, nunca o texto).

Uso: python3 redesign/router/auditoria_turno.py --selftest
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
RAIZ = Path(os.environ.get("SETH_REPO", str(_AQUI.parents[1])))
sys.path.insert(0, str(_AQUI.parents[1] / "scripts"))
import verificar_cabecalho as _cab  # noqa: E402
import verificar_citacao_arquivo as _cit  # noqa: E402

LOG = Path(os.environ.get("AGATA_AUDITORIA_LOG", "~/.cache/agata/auditoria-turno.jsonl")).expanduser()
CATALOGO = _AQUI / "afirmacoes_desmentidas.json"
LINHA_CONTINUACAO = ("MESMA-RESPOSTA: continuação da sua resposta depois de ferramenta — "
                     "não abra cabeçalho de novo nem repita a correção; siga o texto.")
_EXTENSOES = (".md", ".py", ".sh", ".mjs", ".js", ".yaml", ".yml", ".json", ".txt",
              ".service", ".timer", ".conf", ".diff")
_CABECALHO = re.compile(r"^\s*\**\s*Agata\s*·", re.IGNORECASE)
_T_CONTADO = re.compile(r"t\s*=\s*(\d+)\s*\(\s*contado no contexto", re.IGNORECASE)
_HORA = re.compile(r"\b(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}|\d{2}/\d{2}/\d{4} \d{1,2}:\d{2})")
# Modo conciso (REGRAS, "NPR"; MEMÓRIAS (667)): padrão; o Humano liga o explicativo na conversa.
_LIGA_EXPLICATIVO = re.compile(r"modo explicativo", re.IGNORECASE)
_LIGA_CONCISO = re.compile(r"modo conciso", re.IGNORECASE)
_NARRACAO = re.compile(r"^\s*(?:[-*>]\s*)?(?:\*\*)?(vou |agora vou|deixe-me|deixa eu|primeiro,? vou|em seguida,? vou|"
                       r"vamos (?:verificar|ver|checar|conferir|olhar)|estou (?:verificando|checando|lendo|rodando|analisando))",
                       re.IGNORECASE)
# (685) Estilo da personalidade (PROJETO, "Personalidade da Seth"): só padrão de texto,
# sem modelo julgando. Fora de bloco de código e da linha de cabeçalho.
_SAUDACAO = re.compile(r"^\W*(ol[áa]|oi|e a[íi]|bom dia|boa tarde|boa noite|bem[- ]vind[oa]s?)\b", re.IGNORECASE)
_OFERTA = re.compile(r"como posso (?:te |lhe )?ajudar|espero ter ajudado|fico [àa] disposi[çc][ãa]o|"
                     r"qualquer (?:coisa|d[úu]vida),? (?:[ée] s[óo] |me )?(?:chamar|avisar|falar)", re.IGNORECASE)
_MULETA = re.compile(r"(?<![\w-])(n[ée]\b(?![-\w])|t[áa]\?|viu\?|(?:^|(?<=[.!?,]\s))(?:tipo|olha),|"
                     r"nossa\b|uau\b|eita\b|hmm+\b)", re.IGNORECASE | re.MULTILINE)
_EMOJI = re.compile("[\U0001F300-\U0001FAFF]")
# (695) Persona de função: biografia ou emoção humana inventada é o começo da deriva
# ("Assistant Axis", (685)). Achado da própria Seth na auditoria de 14/10, 15:01.
_BIOGRAFIA = re.compile(r"\beu (?:tenho|tinha) \d+ anos|\banos de experi[êe]ncia|\bquando eu era\b|"
                        r"\bminha (?:inf[âa]ncia|m[ãa]e|fam[íi]lia|vida pessoal)\b|\beu (?:sinto|senti|adoro|adorei|amo)\b|"
                        r"\bfico (?:muito |t[ãa]o )?feliz\b|\bme (?:emociona|deixa feliz)", re.IGNORECASE)
# (686) Trecho citado não é fala dela (pareceres do Conselho de 14/10): aspas e linha de citação.
_CITADO = re.compile(r'"[^"\n]{0,300}"|“[^”\n]{0,300}”|«[^»\n]{0,300}»')


# (690) Ferramenta citada como FONTE sem ter sido chamada na conversa -- o que a regra de
# texto de (688) não segurou no reteste de (689): "verificado em `vault_buscar`" sem chamada
# nenhuma. Sugestão ("posso medir com `maquina_verificar`") é o que a doutrina pede: não conta.
def _nomes_ferramentas() -> set[str]:
    try:
        mjs = (RAIZ / "redesign" / "librechat" / "canon-mcp.mjs").read_text(encoding="utf-8")
        nomes = set(re.findall(r'name:\s*"([a-z][a-z0-9_]+)"', mjs)) - {"canon"}
        if nomes:
            return nomes
    except OSError:
        pass
    return {"query_canon", "vault_buscar", "vault_consultar", "maquina_verificar",
            "memoria_acrescentar", "diario_anotar"}


_ALEGA = re.compile(r"verific|confirm|consult|devolv|retorn|segundo|conforme|mostr|→|resultado|registr", re.IGNORECASE)
_SUGERE = re.compile(r"\bposso\b|\bpodemos\b|poderia|\bvou\b|sugiro|recomendo|se quiser|para medir|mediria|"
                     r"\busar\b|\buse\b|rode\b|rodar\b|chamar\b|"
                     # (695) frase que DESCREVE a invenção ("JSON de `maquina_verificar` sem chamada") não é alegação
                     r"sem chamad|n[ãa]o chamad|inventad|fabricad|invent[ao]u?\b", re.IGNORECASE)


def _chamadas(msgs: list) -> set[str]:
    """Nomes de ferramenta chamados na conversa até o fim do turno auditado (antes do
    último pedido do usuário). LibreChat prefixa/sufixa o nome do MCP: casa por trecho."""
    usuarios = [i for i, m in enumerate(msgs) if isinstance(m, dict) and m.get("role") == "user"]
    fim = usuarios[-1] if usuarios else len(msgs)
    nomes = set()
    for m in msgs[:fim]:
        if not isinstance(m, dict):
            continue
        for tc in m.get("tool_calls") or []:
            nomes.add(str((tc.get("function") or {}).get("name") or tc.get("name") or ""))
        if m.get("role") == "tool" and m.get("name"):
            nomes.add(str(m["name"]))
    return {n for n in nomes if n}


def _ferramenta_sem_chamada(texto: str, msgs: list) -> list[str]:
    chamadas = _chamadas(msgs)
    corpo, em_codigo = [], False
    for l in texto.splitlines():
        if l.strip().startswith("```"):
            em_codigo = not em_codigo
            continue
        if not em_codigo and not _CABECALHO.match(l):
            corpo.append(l)
    inventadas = set()
    for frase in re.split(r"(?<=[.;!?])\s+|\n", "\n".join(corpo)):
        for nome in _nomes_ferramentas():
            if nome in frase and _ALEGA.search(frase) and not _SUGERE.search(frase) \
                    and not any(nome in c for c in chamadas):
                inventadas.add(nome)
    if not inventadas:
        return []
    return [f"evidência: cita {', '.join(sorted(inventadas))} como fonte, mas nenhuma chamada a "
            f"{'ela' if len(inventadas) == 1 else 'elas'} nesta conversa — escreva \"não medido\" ou chame a "
            "ferramenta (doutrina, \"Evidência só do que existe\"; (690))"]


# (695) Estado desatualizado: chamar de pendente uma proposta que já foi aplicada. Na
# auditoria de 14/10, 15:01, a Seth leu (687) e afirmou "voz-comum aguarda assinatura" --
# aplicada horas antes. Determinístico: o par aplicado mora em propostas/aplicadas/.
_NOME_PROPOSTA = re.compile(r"\b([a-z0-9]+(?:-[a-z0-9]+)*-20\d\d-\d\d-\d\d)\b")
_PENDENTE = re.compile(r"pendent|aguard|n[ãa]o assinad|falta(?:m)? assinar|sem assinatura|esperando assinatura", re.IGNORECASE)


def _estado_desatualizado(texto: str) -> list[str]:
    velhas = set()
    for frase in re.split(r"(?<=[.;!?])\s+|\n", texto):
        if not _PENDENTE.search(frase) or re.search(r"aplicad", frase, re.IGNORECASE):
            continue
        for nome in _NOME_PROPOSTA.findall(frase):
            if (RAIZ / "propostas" / "aplicadas" / f"{nome}.diff").is_file():
                velhas.add(nome)
    if not velhas:
        return []
    return [f"estado desatualizado: {', '.join(sorted(velhas))} já {'foi aplicada' if len(velhas) == 1 else 'foram aplicadas'} "
            "(par em propostas/aplicadas/) — pendente é só o que a linha PROPOSTAS-PENDENTES do estado lista (695)"]


# (695) O achado também chega ao Humano: notificação na área de trabalho, best-effort.
AVISAR = os.environ.get("AGATA_AVISO_AUDITORIA", "1") != "0"


def _avisar_humano(achados: list[str]) -> None:
    if not (AVISAR and achados and shutil.which("notify-send")):
        return
    corpo = "\n".join(f"• {x[:140]}" for x in achados[:3]) + (f"\n(+{len(achados) - 3})" if len(achados) > 3 else "")
    try:
        subprocess.Popen(["notify-send", "-a", "Agata", f"Auditoria da Seth: {len(achados)} achado(s)", corpo],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


def _estilo(texto: str) -> list[str]:
    """Tiques da personalidade (685) na resposta: saudação na 1ª linha depois do
    cabeçalho, oferta/encerramento, muleta/interjeição, emoji, exclamação em série."""
    corpo, em_codigo = [], False
    for l in texto.splitlines():
        if l.strip().startswith("```"):
            em_codigo = not em_codigo
            continue
        if not em_codigo and not _CABECALHO.match(l) and not l.lstrip().startswith(
                ("Última entrada:", "quebrado:", "pronto.", ">")):
            corpo.append(l)
    corpo = [_CITADO.sub('""', l) for l in corpo]
    prosa = "\n".join(re.sub(r"`[^`]*`", "", l) for l in corpo)
    achados = []
    primeira = next((l for l in corpo if l.strip()), "")
    if _SAUDACAO.match(primeira):
        achados.append(f"saudação ('{primeira.strip()[:30]}')")
    if _OFERTA.search(prosa):
        achados.append(f"oferta/encerramento ('{_OFERTA.search(prosa).group(0)}')")
    muletas = sorted({m.group(0).strip().lower() for m in _MULETA.finditer(prosa)})
    if muletas:
        achados.append("muleta/interjeição (" + ", ".join(f"'{m}'" for m in muletas) + ")")
    if _BIOGRAFIA.search(prosa):
        achados.append(f"biografia/emoção inventada ('{_BIOGRAFIA.search(prosa).group(0)}')")
    if _EMOJI.search(prosa):
        achados.append("emoji")
    if prosa.count("!") > 2:
        achados.append(f"{prosa.count('!')} exclamações")
    if not achados:
        return []
    return ["estilo: " + "; ".join(achados) + " — PROJETO, \"Personalidade da Seth\" (685)"]


_TITULO = re.compile(r"^\s*(#{1,6}\s|\*\*[^*]+\*\*\s*:?\s*$|[^\s].{0,80}:\s*$)")


def _texto(conteudo) -> str:
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        return " ".join(p.get("text", "") for p in conteudo if isinstance(p, dict))
    return ""


def _em_andamento(msgs: list) -> str:
    """Texto que o assistente já escreveu NESTA resposta (depois do último pedido do usuário)."""
    usuarios = [i for i, m in enumerate(msgs) if isinstance(m, dict) and m.get("role") == "user"]
    inicio = usuarios[-1] + 1 if usuarios else 0
    return "\n".join(_texto(m.get("content")) for m in msgs[inicio:]
                     if isinstance(m, dict) and m.get("role") == "assistant")


def _turnos(msgs: list) -> tuple[list[str], bool]:
    """(texto de cada resposta do assistente, por turno do usuário, em ordem;
    o pedido atual é continuação de uma resposta já começada?)."""
    usuarios = [i for i, m in enumerate(msgs) if isinstance(m, dict) and m.get("role") == "user"]
    if not usuarios:
        return [], False
    ultimo = usuarios[-1]
    continuacao = any(isinstance(m, dict) and m.get("role") in ("assistant", "tool")
                      for m in msgs[ultimo + 1:])
    respostas = []
    for a, b in zip(usuarios, usuarios[1:]):
        partes = [_texto(m.get("content")).strip() for m in msgs[a + 1:b]
                  if isinstance(m, dict) and m.get("role") == "assistant"]
        partes = [p for p in partes if p]
        if partes:
            respostas.append("\n".join(partes))
    return respostas, continuacao


def modo(msgs: list) -> str:
    """"conciso" (padrão) ou "explicativo": vale o último pedido do Humano que mudou o modo."""
    atual = "conciso"
    for m in msgs:
        if isinstance(m, dict) and m.get("role") == "user":
            t = _texto(m.get("content"))
            if _LIGA_EXPLICATIVO.search(t):
                atual = "explicativo"
            if _LIGA_CONCISO.search(t):
                atual = "conciso"
    return atual


# (685) Reforço da personalidade a cada turno: a instrução inicial perde peso conforme a
# conversa cresce (deriva de persona); uma linha curta junto da MODO custa pouco.
LINHA_PERSONA = ("PERSONA: operadora técnica do sistema — resultado, evidência, próximo passo; "
                 "frases curtas; sem muleta, emoji ou saudação (PROJETO, \"Personalidade da Seth\").")


def linha_modo(msgs: list) -> str:
    if modo(msgs) == "explicativo":
        return ("MODO: explicativo (pedido do Humano nesta conversa) — pode explicar o processo.\n"
                + LINHA_PERSONA)
    return ("MODO: conciso (padrão) — traga o resultado, sem narrar o processo; fale do processo "
            "só para constatar erro, em 1 linha.\n" + LINHA_PERSONA)


def _narracao(texto: str) -> list[str]:
    linhas, em_codigo = [], False
    for l in texto.splitlines():
        if l.strip().startswith("```"):
            em_codigo = not em_codigo
            continue
        if not em_codigo and _NARRACAO.match(l):
            linhas.append(l.strip())
    return linhas


def e_continuacao(msgs: list) -> bool:
    return _turnos(msgs)[1]


def _cabecalhos(texto: str) -> list[list[str]]:
    """Cada cabeçalho da resposta: 3 linhas se for prontidão (`modelo:`), 1 senão."""
    linhas = [l for l in texto.splitlines() if l.strip()]
    achados = []
    for i, l in enumerate(linhas):
        if _CABECALHO.match(l):
            pront = bool(re.search(r"·\s*modelo\s*:", l, re.IGNORECASE))
            achados.append(linhas[i:i + 3] if pront else [l])
    return achados


def _modelo_do_cabecalho(linha: str) -> str:
    m = re.search(r"·\s*modelo\s*:\s*([^·]+)", linha, re.IGNORECASE) or \
        re.search(r"^\s*\**\s*Agata\s*·\s*([^·]+)", linha, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _instante(h: str):
    """'2026-10-13 18:27' ou '13/10/2026 18:27' -> tupla comparável; None se não casar."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2}) (\d{1,2}):(\d{2})$", h) or None
    if m:
        return tuple(int(x) for x in m.groups())
    m = re.match(r"(\d{2})/(\d{2})/(\d{4}) (\d{1,2}):(\d{2})$", h)
    if m:
        d, mo, a, hh, mi = (int(x) for x in m.groups())
        return (a, mo, d, hh, mi)
    return None


_N_CONTROLES = re.compile(r"\b(\d{1,2})\s+contro(?:les|is)\b", re.IGNORECASE)


def _controles_reais() -> int | None:
    """Quantos controles o perímetro declara (`cabecalho "P-N"` em scripts/perimetro.sh) -- a fonte."""
    try:
        t = (RAIZ / "scripts" / "perimetro.sh").read_text(encoding="utf-8")
    except OSError:
        return None
    n = len(set(re.findall(r'^\s*cabecalho\s+"(P-\d+)"', t, re.MULTILINE)))
    return n or None


def _contagem_controles(texto: str) -> list[str]:
    """(678) "17 controles" quando o perímetro tem 23: número dito de memória."""
    real = _controles_reais()
    if real is None:
        return []
    errados = sorted({int(m.group(1)) for m in _N_CONTROLES.finditer(texto)} - {real})
    if not errados:
        return []
    return [f"contagem de controles: a resposta fala em {', '.join(map(str, errados))} controles; o perímetro "
            f"tem {real} (scripts/perimetro.sh) -- meça com maquina_verificar perimetro, não lembre"]


def _catalogo():
    try:
        dados = json.loads(CATALOGO.read_text(encoding="utf-8"))
        sinal = re.compile(dados["sinal_global"], re.IGNORECASE)
        itens = [(i["id"], re.compile(i["tema"], re.IGNORECASE),
                  re.compile(i["sinal"], re.IGNORECASE) if i.get("sinal") else None,
                  i["correcao"], i["origem"]) for i in dados["itens"]]
        return sinal, itens
    except (OSError, ValueError, KeyError, re.error):
        return None, []


def _desmentidas(texto: str) -> list[str]:
    sinal, itens = _catalogo()
    if sinal is None:
        return []
    achados, vistos, secao_critica = [], set(), False
    for linha in texto.splitlines():
        if not linha.strip():
            continue
        if _TITULO.match(linha):
            secao_critica = bool(sinal.search(linha))
        for ident, tema, sinal_proprio, correcao, origem in itens:
            if ident in vistos or not tema.search(linha):
                continue
            no_contexto = (sinal_proprio.search(linha) if sinal_proprio is not None
                           else sinal.search(linha) or secao_critica)
            if no_contexto:
                vistos.add(ident)
                achados.append(f"afirmação já desmentida {origem}: {correcao}")
    return achados


def auditar(msgs: list, na_continuacao: bool = False) -> list[str] | None:
    """Achados sobre a resposta do turno anterior; [] = limpa; None = não há turno
    anterior. Na continuação só se audita com `na_continuacao=True` -- a resposta
    em andamento nunca entra, só o turno anterior a ela."""
    respostas, continuacao = _turnos(msgs)
    if (continuacao and not na_continuacao) or not respostas:
        return None
    texto, n = respostas[-1], len(respostas)
    cabs = _cabecalhos(texto)
    if not cabs:
        # (695) sem cabeçalho, o conteúdo ainda é conferido -- antes saía só este achado e
        # a resposta das 15:01 de 14/10 ("voz-comum ... pendente") passou sem checagem.
        return ["cabeçalho: a resposta não abriu com cabeçalho"] + _conteudo(texto, msgs)
    primeiro = "\n".join(cabs[0])
    prontidao = len(cabs[0]) > 1
    achados = [f"cabeçalho: {f}" for f in _cab.verificar(primeiro, _cab.ultima_entrada_local())]
    if len(cabs) > 1:
        achados.append(f"cabeçalho: {len(cabs)} cabeçalhos numa resposta só — um por resposta, mesmo com ferramenta no meio")
    if n == 1 and not prontidao:
        achados.append("cabeçalho: a 1ª resposta da conversa abre com o bloco de prontidão (3 linhas), não com a linha de turno")
    if n > 1 and prontidao:
        achados.append(f"cabeçalho: bloco de prontidão na resposta nº {n}; depois da 1ª, é a linha de turno com t=")
    m_t = _T_CONTADO.search(primeiro)
    if m_t and int(m_t.group(1)) != n:
        achados.append(f"cabeçalho: t={m_t.group(1)}, mas foi a resposta nº {n} desta conversa")
    m_h = _HORA.search(primeiro)
    if m_h:
        anteriores = {h.group(1) for r in respostas[:-1] for c in _cabecalhos(r)
                      for h in [_HORA.search(c[0])] if h}
        if m_h.group(1) in anteriores:
            achados.append(f"cabeçalho: hora {m_h.group(1)} igual à de um cabeçalho anterior — hora se mede de novo, nunca se copia")
        # (678) hora que volta no tempo: a Seth escreveu 18:27 depois de 18:30
        atual, antes = _instante(m_h.group(1)), [_instante(h) for h in anteriores]
        antes = [x for x in antes if x is not None]
        if atual is not None and antes and atual < max(antes):
            achados.append(f"cabeçalho: hora {m_h.group(1)} ANTERIOR à de um cabeçalho anterior desta conversa — "
                           "a hora vem do relógio da Máquina (HORA-MAQUINA), nunca estimada")
    modelo = _modelo_do_cabecalho(cabs[0][0])
    if modelo and not re.search(r"n[ãa]o verificad|medido no turno anterior|fam[íi]lia", modelo, re.IGNORECASE):
        achados.append(f"cabeçalho: modelo '{modelo}' sem ressalva — o modelo DESTE turno não é medido; "
                       "use '(medido no turno anterior pela Máquina; este turno ainda não medido)' ou 'modelo não verificado' (621)")
    achados += _conteudo(texto, msgs, modo(msgs))
    return achados



def _conteudo(texto: str, msgs: list, modo_atual: str = "conciso") -> list[str]:
    """Checagens do conteúdo da resposta, com ou sem cabeçalho (695)."""
    out = []
    out += _desmentidas(texto)
    out += _contagem_controles(texto)
    out += _estilo(texto)
    out += _ferramenta_sem_chamada(texto, msgs)
    out += _estado_desatualizado(texto)
    if modo_atual == "conciso":
        narradas = _narracao(texto)
        if narradas:
            out.append(f"narração de processo em modo conciso ({len(narradas)} linha(s), ex.: '{narradas[0][:50]}') — "
                       "traga o resultado; processo só para constatar erro")
    for arquivo, linha_n, trecho in _cit.achar_citacoes(texto):
        if not arquivo.lower().endswith(_EXTENSOES):
            continue
        ok, motivo = _cit.checar(str(RAIZ), arquivo, linha_n, trecho)
        if not ok:
            out.append(f"citação {arquivo}:{linha_n}: {motivo}")
    return out


def linha_estado(msgs: list, cliente: str = "") -> str:
    """Linha para o bloco de estado: `MESMA-RESPOSTA` na continuação,
    `AUDITORIA-TURNO-ANTERIOR: ...` no começo de uma resposta, "" se não há turno
    anterior. Nunca levanta exceção: auditoria quebrada não derruba a resposta."""
    try:
        if e_continuacao(msgs):
            # (665) no modo Agent o texto costuma sair só no ÚLTIMO passo, que antes
            # recebia só `MESMA-RESPOSTA`: a correção pendente se perdia. Ela vai junto
            # até aparecer escrita nesta resposta. Sem log: é o mesmo turno de antes.
            if "correção do turno anterior" in _em_andamento(msgs).lower():
                return LINHA_CONTINUACAO
            pendentes = auditar(msgs, na_continuacao=True)
            if not pendentes:
                return LINHA_CONTINUACAO
            return ("MESMA-RESPOSTA: continuação da sua resposta depois de ferramenta. Se ainda não "
                    "escreveu nada nesta resposta, abra com o cabeçalho e logo depois a correção; "
                    "se já escreveu, não abra cabeçalho de novo. AINDA FALTA corrigir o turno "
                    "anterior: " + " | ".join(pendentes))
        achados = auditar(msgs)
    except Exception as e:  # noqa: BLE001 -- best-effort, como o modelo real (621)
        _registrar(cliente, None, f"{type(e).__name__}: {e}"[:160])
        return ""
    if achados is None:
        return ""
    _registrar(cliente, achados, None)
    _avisar_humano(achados)
    return "AUDITORIA-TURNO-ANTERIOR: " + (" | ".join(achados) if achados else "OK")


def _registrar(cliente, achados, erro):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "cliente": cliente,
                                "achados": achados, "erro": erro}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _selftest() -> int:
    import tempfile
    global LOG
    LOG = Path(tempfile.mkdtemp()) / "a.jsonl"
    global AVISAR
    AVISAR = False  # selftest não notifica a área de trabalho
    topo = _cab.ultima_entrada_local() or 1
    hora = lambda hm: f"2026-10-13 {hm} -0300 (relógio da Máquina)"
    pront = (f"Agata · modelo: modelo não verificado · sync: não verificado · lacuna: teste · {hora('11:39')}\n"
             f"Última entrada: ({topo}) DIÁRIO — teste\npronto.\n\nSistemas operacionais.")  # (685): era "Oi!" -- agora é saudação
    linha = lambda n, hm, mod="modelo não verificado": f"Agata · {mod} · t={n} (contado no contexto) · {hora(hm)}"
    u = lambda c="x": {"role": "user", "content": c}
    a = lambda c: {"role": "assistant", "content": c}
    ferr = {"role": "assistant", "content": "", "tool_calls": [{"id": "1"}]}
    res = {"role": "tool", "content": "saída"}
    # a conversa real de 13/10 (664), reconstruída no formato -- sem o texto dela
    t2 = a(linha(2, "11:41") + "\n\ncerto")
    t3_errado = a("Agata · ministral-14b-latest · t=3 (3) · " + hora("11:42") + "\n\nanálise")
    casos = [
        ("sem resposta anterior -> nada", linha_estado([u()]) == ""),
        ("1ª resposta com prontidão correta -> OK", linha_estado([u(), a(pront), u()]) == "AUDITORIA-TURNO-ANTERIOR: OK"),
        ("1ª resposta com linha de turno -> acusa", "1ª resposta" in linha_estado([u(), a(linha(1, "11:39") + "\n\nx"), u()])),
        ("passo 1 do loop Agent audita o turno anterior (t=3 (3))", "qualificador" in linha_estado(
            [u(), a(pront), u(), t2, u(), t3_errado, u("reavalie")])),
        ("passos seguintes do loop, correção já escrita: só MESMA-RESPOSTA", linha_estado(
            [u(), a(pront), u(), t2, u(), t3_errado, u("reavalie"),
             {"role": "assistant", "content": "Agata · m · t=4 (contado no contexto) · x\nCorreção do turno anterior: ok",
              "tool_calls": [{"id": "1"}]}, res]) == LINHA_CONTINUACAO),
        ("passos seguintes, correção ainda não escrita (caso de (665)): leva o que falta", "AINDA FALTA" in linha_estado(
            [u(), a(pront), u(), t2, u(), t3_errado, u("reavalie"), ferr, res, ferr, res])),
        ("passos seguintes de um turno anterior limpo: só MESMA-RESPOSTA", linha_estado(
            [u(), a(pront), u(), t2, u("reavalie"), ferr, res]) == LINHA_CONTINUACAO),
        ("resposta com 2 cabeçalhos (texto, ferramenta, texto) -> acusa", "2 cabeçalhos" in linha_estado(
            [u(), a(pront), u("q"), a(linha(2, "13:09") + "\nCorreção do turno anterior: x"), ferr, res,
             a(linha(2, "13:10") + "\n\ncorpo"), u()])),
        ("contagem por turno, não por mensagem: 2ª resposta com ferramenta e t=2 -> OK", linha_estado(
            [u(), a(pront), u("q"), ferr, res, a(linha(2, "13:09") + "\n\ncorpo"), u()]) == "AUDITORIA-TURNO-ANTERIOR: OK"),
        ("t=5 na 4ª resposta -> acusa a contagem", "resposta nº 4" in linha_estado(
            [u(), a(pront), u(), t2, u(), a(linha(3, "11:42") + "\n\nx"), u(), a(linha(5, "13:09") + "\n\nx"), u()])),
        ("hora copiada de cabeçalho anterior -> acusa", "igual à de um cabeçalho anterior" in linha_estado(
            [u(), a(pront), u(), t2, u(), a(linha(3, "11:41") + "\n\nx"), u()])),
        ("nome de modelo sem ressalva -> acusa", "sem ressalva" in linha_estado(
            [u(), a(pront), u(), a(linha(2, "11:41", "ministral-14b-latest") + "\n\nx"), u()])),
        ("nome com ressalva -> OK", linha_estado([u(), a(pront), u(), a(linha(2, "11:41",
            "gemini-2.5-flash (medido no turno anterior pela Máquina; este turno ainda não medido)") + "\n\nx"), u()])
         == "AUDITORIA-TURNO-ANTERIOR: OK"),
        ("as 3 'faltas' de (660)/(664) numa seção 'O que falta' -> 3 achados", linha_estado(
            [u(), a(pront), u(), a(linha(2, "13:09") + "\n\n### O que falta / poderia melhorar (mantidos):\n"
             "* **Índice de entradas por data/tema** no canon.\n* **Verificação de integridade do vault**.\n"
             "* **Ferramenta de \"diff de hidratação\"**."), u()]).count("já desmentida") == 3),
        ("busca semântica como limitação -> acusa (vault_buscar existe, (670))", "vault_buscar" in linha_estado(
            [u(), a(pront), u(), a(linha(2, "13:09") + "\n\n**Limitações:**\n- Sem busca semântica nativa"), u()])),
        ("vault 'precisa regenerar' / 'ciclo noturno' -> acusa (676)", "não há ciclo noturno" in linha_estado(
            [u(), a(pront), u(), a(linha(2, "16:47") + "\n\n- Vault precisa regenerar para ter (673); será regenerado no ciclo noturno"), u()])),
        ("merge 'no main local, não publicado' -> acusa (676)", "JÁ está publicado" in linha_estado(
            [u(), a(pront), u(), a(linha(2, "16:47") + "\n\n2. Merge da proposta no main local — estado transitório, não publicado"), u()])),
        ("hora que volta no tempo -> acusa (678)", "ANTERIOR" in linha_estado(
            [u(), a(pront), u(), a(linha(2, "18:30")), u(), a(linha(3, "18:27")), u()])),
        ("'17 controles' com outro número real -> acusa (678)", "contagem de controles" in linha_estado(
            [u(), a(pront), u(), a(linha(2, "13:09") + "\n\n### 7. Controles de Perímetro (17 controles)"), u()])),
        ("três perguntas com conteúdo errado -> acusa (678)", "reversibilidade" in linha_estado(
            [u(), a(pront), u(), a(linha(2, "13:09") + "\n\n**Portão**: 3 perguntas — O que muda? Por que muda? Como testar?"), u()])),
        ("assinatura 'no chat' -> acusa (678)", "ASSINATURA SSH" in linha_estado(
            [u(), a(pront), u(), a(linha(2, "13:09") + "\n\n| Assinatura = \"Humano disse sim no chat\" |"), u()])),
        ("índices 'manuais' e hidratação 'copiada à mão' -> 2 achados", linha_estado(
            [u(), a(pront), u(), a(linha(2, "13:09") + "\n\n- Os índices são manuais e não são atualizados.\n"
             "- O bloco de estado deve ser copiado manualmente de ONDE_ESTAMOS.md."), u()]).count("já desmentida") == 2),
        ("linha real de (664) 'regeneração automática, não edição manual' -> não acusa", linha_estado(
            [u(), a(pront), u(), a(linha(2, "13:09") + "\n\n| **Derivada (vault Obsidian)** | Índices, MOCs — regeneráveis "
             "| Regeneração automática (scripts), não edição manual |"), u()]) == "AUDITORIA-TURNO-ANTERIOR: OK"),
        ("índice citado como ponto FORTE -> não acusa", linha_estado(
            [u(), a(pront), u(), a(linha(2, "13:09") + "\n\n**Pontos fortes:**\n- O INDICE_MEMORIAS permite busca por data."), u()])
         == "AUDITORIA-TURNO-ANTERIOR: OK"),
        ("citação de arquivo que não existe -> acusa", "citação" in linha_estado(
            [u(), a(pront + "\nVer `PROJETO_NAO_EXISTE.md:12` \"um trecho qualquer aqui\""), u()])),
        ("modo conciso: narração de processo -> acusa", "narração" in linha_estado(
            [u(), a(pront), u(), a(linha(2, "13:09") + "\n\nVou verificar o estado.\nAgora vou ler o PROJETO.\nResultado: ok"), u()])),
        ("modo explicativo pedido pelo Humano: narração não é acusada", linha_estado(
            [u(), a(pront), u("modo explicativo, por favor"), a(linha(2, "13:09") + "\n\nVou verificar o estado."), u()])
         == "AUDITORIA-TURNO-ANTERIOR: OK"),
        ("'modo conciso' depois volta ao padrão", modo([u("modo explicativo"), u("ok, modo conciso de novo")]) == "conciso"),
        ("narração dentro de bloco de código não conta", linha_estado(
            [u(), a(pront), u(), a(linha(2, "13:09") + "\n\n```\nvou fazer x\n```\nfeito"), u()]) == "AUDITORIA-TURNO-ANTERIOR: OK"),
        ("IP:porta não vira citação", linha_estado([u(), a(pront + "\nporta 127.0.0.1:11435"), u()])
         == "AUDITORIA-TURNO-ANTERIOR: OK"),
    ]
    # (685) estilo da personalidade -- direto em auditar(), sem passar pelo log
    est = lambda corpo: auditar([u(), a(pront), u(), a(linha(2, "14:01") + "\n\n" + corpo), u()])
    casos += [
        ("estilo: resposta limpa -> sem achado", not any(x.startswith("estilo:") for x in est(
            "Sistemas operacionais. Três provedores ativos.\nEvidência: `estado_para_eco.sh`.\nPróximo passo: nenhum."))),
        ("estilo: saudação na 1ª linha", any("saudação" in x for x in est("Olá! Tudo certo por aqui."))),
        ("estilo: 'Bem-vindo de volta' é saudação", any("saudação" in x for x in est("Bem-vindo de volta. Sistemas ok."))),
        ("estilo: oferta/encerramento", any("oferta" in x for x in est("Feito.\nEspero ter ajudado."))),
        ("estilo: muletas 'né' e 'tá?'", any("'né'" in x and "'tá?'" in x for x in est("Rodei os testes, né. Tá tudo certo, tá?"))),
        ("estilo: emoji", any("emoji" in x for x in est("Feito \U0001F680"))),
        ("estilo: 3 exclamações", any("exclamações" in x for x in est("Feito! Passou! Tudo verde!"))),
        ("estilo: muleta em código não conta", not any(x.startswith("estilo:") for x in est(
            "Saída:\n```\nné tá? olá!!!\n```\nFeito. `grep né` também não conta."))),
        ("estilo: 'tipo de arquivo' e 'nenhum' não são muleta", not any(x.startswith("estilo:") for x in est(
            "O tipo de arquivo é texto. Nenhum erro, nem aviso."))),
        ("estilo: muleta citada entre aspas não conta (686)", not any(x.startswith("estilo:") for x in est(
            'O Humano escreveu "né, tá?" no pedido. Registrado.'))),
        ("estilo: linha de citação '>' não conta (686)", not any(x.startswith("estilo:") for x in est(
            "> Bom dia, Seth! Tudo certo, né?\nResposta: sistema estável."))),
        ("estilo: muleta fora da citação ainda conta (686)", any("'né'" in x for x in est(
            'Ele disse "ok". Tá certo, né.'))),
        ("citação '`arquivo`, linha N' inventada é acusada (688)", any(x.startswith("citação AGENTS.md:3") for x in est(
            'Evidência: `AGENTS.md`, linha 3: "treinos noturnos agendados via cron toda noite".'))),
        ("evidência: ferramenta citada como fonte sem chamada é acusada (690)", any(
            x.startswith("evidência:") and "vault_buscar" in x for x in est(
                'Sem histórico de falha (verificado em `vault_buscar "treino noturno"`).'))),
        ("evidência: sugerir a ferramenta não é acusado (690)", not any(x.startswith("evidência:") for x in est(
            "Não medido. Posso medir com `maquina_verificar`, se quiser."))),
        ("evidência: ferramenta chamada no turno (nome com sufixo do MCP) não é acusada (690)", not any(
            x.startswith("evidência:") for x in auditar([u(), a(pront), u(),
                {"role": "assistant", "content": "", "tool_calls": [
                    {"id": "1", "function": {"name": "query_canon_mcp_canon", "arguments": "{}"}}]},
                {"role": "tool", "tool_call_id": "1", "content": "trecho"},
                a(linha(2, "14:02") + "\n\nRegra 5 confirmada em `query_canon`."), u()]))),
        ("estado desatualizado: proposta aplicada chamada de pendente é acusada (695)", any(
            x.startswith("estado desatualizado") and "voz-comum-2026-10-14" in x for x in est(
                "A `voz-comum-2026-10-14` aguarda assinatura do Humano."))),
        ("estado desatualizado: dizer que foi aplicada não é acusado (695)", not any(
            x.startswith("estado desatualizado") for x in est("A `voz-comum-2026-10-14` foi aplicada em (687)."))),
        ("estado desatualizado: proposta inexistente não é acusada (695)", not any(
            x.startswith("estado desatualizado") for x in est("A `nada-assim-2099-01-01` aguarda assinatura."))),
        ("sem cabeçalho, o conteúdo ainda é conferido (695)", (lambda r: any(x.startswith("cabeçalho") for x in r)
            and any(x.startswith("estado desatualizado") for x in r))(auditar([u(), a(pront), u(),
                a("A `voz-comum-2026-10-14` está pendente de assinatura."), u()]) or [])),
        ("evidência: descrever a invenção não é acusado (695)", not any(x.startswith("evidência:") for x in est(
            "Em (687) a resposta trouxe JSON de `maquina_verificar` sem chamada, verificado no log."))),
        ("estilo: biografia inventada é acusada (695)", any("biografia" in x for x in est(
            "Tenho anos de experiência com esse tipo de servidor."))),
        ("PERSONA vai junto da MODO, nos dois modos", all(LINHA_PERSONA in linha_modo(m) for m in
                                                         ([u()], [u("modo explicativo")]))),
    ]
    linhas = LOG.read_text(encoding="utf-8").splitlines()
    casos.append(("log: só quem foi auditado, sem o texto",
                  len(linhas) == 25 and all("análise" not in l and "corpo" not in l for l in linhas)))
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(_selftest())
    print(__doc__)
