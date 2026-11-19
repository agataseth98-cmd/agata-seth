#!/usr/bin/env python3
"""Bloqueio no lugar de aviso, na verificação do turno (19/11/2026, decisão do Humano).

A auditoria de 18/11 mediu 27 respostas da Seth sem nenhuma chamada de ferramenta real e várias afirmações de
escrita ("criei", "REGISTRADO"), saídas de ferramenta inventadas e cabeçalhos duplicados. Aviso no fim da resposta
não impede nada. Aqui, três checagens mecânicas decidem se a resposta pode sair:

  (a) afirma escrita ou aplicação sem tool_call de ESCRITA bem-sucedida neste turno;
  (b) simula saída de ferramenta ou JSON de estado sem tool_call;
  (c) traz um segundo cabeçalho `agata-seth ·` no corpo, ou um cabeçalho com modelo diferente do roteado.

O gateway devolve ao modelo uma vez, com uma nota que só ele vê ("Correção do turno anterior", nunca ao Humano). Se
persistir, entrega a resposta mínima honesta (`resposta_minima`). Funções puras, sem rede e sem modelo. Quem usa é o
seth_gateway (e o teste). SETH_BLOQUEIO_TURNO=0 desliga no gateway.
"""
from __future__ import annotations

import json
import re

import ferramentas_confianca as fc

_CERCA = re.compile(r"^\s*```")
_CAB = re.compile(r"^\s*\**\s*agata-seth\s*·\s*([^·\n]*?)\s*(?:·|$)", re.I)
_NEGA_OU_HIPOTESE = re.compile(
    r"(?i)\bn[ãa]o\b|\bnem\b|\bsem\b|\bnunca\b|\bse\b|\bcaso\b|\bquando\b|\bposso\b|\bpodemos\b|\bvou\b|\bseria\b|"
    r"\bpoderia\b|\bsugiro\b|\bpropon\w*|\bpretendo\b|\bfalta(?:m)?\b|\bainda\b|\bpendente\b|\?")
_AFIRMA_ESCRITA = (
    # verbos de persistência, sozinhos; "criei", "escrevi", "atualizei" e "editei" só com objeto que persiste (sem isso,
    # "escrevi o texto abaixo" seria alarme falso)
    re.compile(r"(?i)\b(?:gravei|salvei|apliquei|registrei|anotei|acrescentei)\b"),
    re.compile(r"(?i)\b(?:criei|escrevi|atualizei|editei)\s+(?:\w+\s+){0,3}?(?:arquivos?|entradas?|notas?|mem[óo]rias?|"
               r"propostas?|registros?|diffs?|patch|commit|documentos?|scripts?|pastas?|diret[óo]rios?|di[áa]rio|"
               r"MEM[ÓO]RIAS|canon|regras?|skills?|units?|configura[çc][ãa]o)\b"),
    re.compile(r"(?i)\b(?:foi|foram|ficou|ficaram)\s+(?:j[áa]\s+)?(?:gravad|registrad|salv|criad|escrit)[oa]s?\b"),
    re.compile(r"\b(?:APLICAD[AO]S?|REGISTRAD[AO]S?|GRAVAD[AO]S?|CRIAD[AO]S?|SALV[AO]S?)\b"),
    re.compile(r"(?i)\b(?:arquivo|entrada|nota|mem[óo]ria|proposta|registro)\s+(?:foi\s+)?(?:criad|gravad|registrad|"
               r"salv|escrit)[oa]\b"),
)
_TAGS_SAIDA = re.compile(
    r"(?i)<\s*/?\s*(?:tool_response|tool_result|function_results?|tool_output)\b|\[\s*TOOL[_ ]RESULT|"
    r"\"tool_call_id\"\s*:|\"role\"\s*:\s*\"tool\"")
_ROTULO_SAIDA = re.compile(
    r"(?im)^\s*(?:\*\*)?\s*(?:sa[ií]da|resultado|retorno|output)\s+(?:d[aoe]s?\s+)?"
    r"(?:ferramenta|tool|`?[a-z][a-z_]*_mcp_[a-z_]+`?|`?(?:" + "|".join(sorted(
        n for n in ("query_canon", "vault_buscar", "vault_consultar", "maquina_verificar", "memoria_acrescentar",
                    "diario_anotar", "buscar_web", "ler_pagina", "navegar", "git_sync", "run_perimetro",
                    "ler_mensagens", "enviar_mensagem", "screenshot"))) + r")`?)\s*(?:\*\*)?\s*[:\-—]")
_BLOCO_JSON = re.compile(r"```(?:json)?\s*\n(\{.*?\})\s*\n```", re.S)
_CHAVES_ESTADO = ("ok", "estado", "status", "sync", "head", "exit_code", "returncode", "stdout", "resultado",
                  "linhas", "commit", "perimetro", "controles")
_FALHA_RESULTADO = re.compile(
    r"(?i)\berro\b|\berror\b|\bfalh\w*|\bfail\w*|\bnegad\w*|\bdenied\b|\brecus\w*|\bcancel\w*|\bexce[çc][ãa]o\b|"
    r"\bexception\b|\btraceback\b|\btimeout\b|\btimed out\b|n[ãa]o foi poss[ií]vel|n[ãa]o consegu\w*|\bunable\b|"
    r"\binv[áa]lid\w*|\binvalid\b|\bnot found\b|aprova[çc][ãa]o (?:negada|pendente)|\bnot approved\b")
_SUCESSO_EXPLICITO = re.compile(
    r"(?i)\"(?:ok|success|sucesso)\"\s*:\s*true|\"status\"\s*:\s*\"(?:ok|success|sucesso|gravad[oa]|registrad[oa])\"|"
    r"\b(?:gravad[oa]|registrad[oa]|criad[oa]|salv[oa]|anotad[oa]|acrescentad[oa]|enviad[oa])\s+com\s+sucesso\b|"
    r"\bsucesso\b|\bsuccess(?:ful(?:ly)?)?\b")


def _resultado_positivo(texto: str) -> bool:
    """Sucesso só com sinal positivo EXPLÍCITO e nenhum sinal de erro. Erro, falha, negado, "não foi possível", exceção
    ou resultado ambíguo não contam. JSON: `ok`/`success` verdadeiro, ou status ok, e nenhum campo erro preenchido."""
    t = (texto or "").strip()
    if not t:
        return False
    try:
        o = json.loads(t)
    except ValueError:
        o = None
    if isinstance(o, dict):
        for k in ("erro", "error", "exception", "excecao", "exceção", "falha", "failure"):
            if o.get(k) not in (None, "", False, [], {}):
                return False
        if o.get("ok") is False or o.get("success") is False or o.get("sucesso") is False:
            return False
        return (o.get("ok") is True or o.get("success") is True or o.get("sucesso") is True
                or str(o.get("status", "")).lower() in ("ok", "success", "sucesso", "gravado", "registrado"))
    return _SUCESSO_EXPLICITO.search(t) is not None and _FALHA_RESULTADO.search(t) is None


def _fora_de_codigo(texto: str) -> str:
    corpo, em = [], False
    for linha in texto.splitlines():
        if _CERCA.match(linha):
            em = not em
            continue
        if not em:
            corpo.append(linha)
    return "\n".join(corpo)


def turno_atual(msgs: list) -> list:
    """As mensagens depois do último pedido do usuário (chamadas e resultados já feitos neste turno)."""
    idx = [i for i, m in enumerate(msgs) if isinstance(m, dict) and m.get("role") == "user"]
    return list(msgs[idx[-1] + 1:]) if idx else list(msgs)


def _texto(m: dict) -> str:
    c = m.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(p.get("text", "") for p in c if isinstance(p, dict) and isinstance(p.get("text"), str))
    return ""


def _resultados(msgs: list) -> list[tuple[str, str]]:
    """[(nome da ferramenta, texto do resultado)] do turno, o nome pelo id da chamada ou pelo campo name."""
    turno = turno_atual(msgs)
    por_id = {}
    for m in turno:
        if isinstance(m, dict) and m.get("role") == "assistant":
            for tc in m.get("tool_calls") or []:
                if isinstance(tc, dict) and tc.get("id"):
                    por_id[tc["id"]] = str((tc.get("function") or {}).get("name") or tc.get("name") or "")
    saida = []
    for m in turno:
        if isinstance(m, dict) and m.get("role") == "tool":
            tid = m.get("tool_call_id")
            nome = por_id.get(tid, "") if isinstance(tid, str) and tid else ""  # nunca o campo `name` do cliente
            saida.append((nome, _texto(m)))
    return saida


def tem_resultado_de_ferramenta(msgs: list) -> bool:
    return bool(_resultados(msgs))


def escrita_bem_sucedida(msgs: list) -> bool:
    """Há, neste turno, resultado de ferramenta de ESCRITA que não é falha, recusa ou aprovação negada?"""
    conhecidas = fc.carregar()["ferramentas"]  # só ferramenta de escrita CONHECIDA, ligada pelo tool_call_id
    return any(n and fc.nome_base(n) in conhecidas and fc.e_escrita(n) and _resultado_positivo(t)
               for n, t in _resultados(msgs))


def _frases(texto: str):
    return [f for f in re.split(r"(?<=[.;!])\s+|\n", texto) if f.strip()]


def _afirma_escrita(texto: str) -> str | None:
    for frase in _frases(_fora_de_codigo(texto)):
        if _CAB.match(frase) or _NEGA_OU_HIPOTESE.search(frase):
            continue
        for rx in _AFIRMA_ESCRITA:
            m = rx.search(frase)
            if m:
                return m.group(0)
    return None


def _simula_saida(texto: str) -> str | None:
    if _TAGS_SAIDA.search(texto):
        return "marcação de resultado de ferramenta escrita pelo modelo"
    if _ROTULO_SAIDA.search(_fora_de_codigo(texto)):
        return "saída rotulada de ferramenta escrita pelo modelo"
    conhecidas = set(fc.carregar()["ferramentas"])
    for m in _BLOCO_JSON.finditer(texto):
        try:
            obj = json.loads(m.group(1))
        except ValueError:
            continue
        if isinstance(obj, dict) and sum(1 for c in _CHAVES_ESTADO if c in obj) >= 2:
            antes = texto[max(0, m.start() - 300):m.start()].lower()
            if any(n in antes for n in conhecidas) or re.search(r"ferramenta|\btool\b|executei|rodei|chamei", antes):
                return "JSON de estado escrito pelo modelo"
    return None


def _norm_modelo(nome: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(nome or "").split("/")[-1].lower())


def _cabecalho_errado(texto: str, modelo_real: str | None) -> str | None:
    vistos, conteudo_antes = [], False
    for linha in texto.splitlines():
        m = _CAB.match(linha)
        if m:
            vistos.append((m.group(1), conteudo_antes))
        elif linha.strip() and not re.match(r"^\s*\**\s*(?:última entrada|pronto\.|quebrado)\b", linha, re.I):
            conteudo_antes = True
    if not vistos:
        return None
    if len(vistos) > 1 or vistos[0][1]:
        return "segundo cabeçalho agata-seth no corpo da resposta"
    a, b = _norm_modelo(vistos[0][0]), _norm_modelo(modelo_real)
    if a and b and a != b and a not in b and b not in a and "verificado" not in a:
        return f"cabeçalho com modelo '{vistos[0][0].strip()}' diferente do roteado '{modelo_real}'"
    return None


def achados(texto: str, msgs: list, modelo_real: str | None = None) -> list[tuple[str, str]]:
    """[(codigo, descrição)] para uma resposta SEM tool_call. Vazio = pode sair. (a) e (b) olham o turno inteiro: com
    resultado de ferramenta de escrita bem-sucedido (a) cala; com qualquer resultado de ferramenta (b) cala."""
    if not isinstance(texto, str) or not texto.strip():
        return []
    out = []
    if not escrita_bem_sucedida(msgs):
        frase = _afirma_escrita(texto)
        if frase:
            out.append(("a", f"afirma escrita ou aplicação ('{frase}') sem chamada de ferramenta de escrita bem-sucedida "
                             "neste turno"))
    if not tem_resultado_de_ferramenta(msgs):
        sim = _simula_saida(texto)
        if sim:
            out.append(("b", f"{sim}, sem chamada de ferramenta neste turno"))
    cab = _cabecalho_errado(texto, modelo_real)
    if cab:
        out.append(("c", cab))
    return out


def nota_correcao(ach: list[tuple[str, str]]) -> str:
    """Nota só para o contexto do modelo (vai como mensagem do usuário no pedido de nova tentativa). Nunca ao Humano."""
    itens = " | ".join(d for _c, d in ach)
    return ("[Máquina, só para você; não cite esta nota ao Humano. Correção do turno anterior: a resposta foi conferida "
            f"e foi retida. Achados: {itens}. Refaça a resposta: para escrever, chame a ferramenta de escrita (passa pela "
            "aprovação do Humano) e só afirme o que ela devolver; não escreva saída de ferramenta nem JSON de estado "
            "que você não recebeu; não repita o cabeçalho. O que não foi medido, escreva \"não medido\".]")


def resposta_longa_demais() -> str:
    """Quando a resposta não pôde ser conferida inteira (acima do teto de bytes, prazo estourado ou upstream cortado)."""
    return ("Resposta retida pela Máquina: resposta longa demais para conferir; não medido. Não afirmo nada do que ela "
            "dizia. Peça de novo, mais curta ou em partes.")


def resposta_minima(ach: list[tuple[str, str]]) -> str:
    """O texto honesto que sai no lugar da resposta que persistiu no erro. Sem o texto do modelo."""
    partes = []
    codigos = {c for c, _ in ach}
    if "a" in codigos:
        partes.append("Não gravei, criei nem apliquei nada neste turno: nenhuma ferramenta de escrita foi chamada com "
                      "sucesso, e a resposta do modelo afirmava o contrário.")
    if "b" in codigos:
        partes.append("Não houve chamada de ferramenta neste turno: o modelo escreveu uma saída que não recebeu.")
    if "c" in codigos:
        partes.append("A resposta trazia cabeçalho duplicado ou com outro modelo, e foi retida.")
    return ("Resposta retida pela Máquina. " + " ".join(partes) + " Não medido: o estado real do que foi afirmado. "
            "Peça de novo, ou diga o que fazer para eu chamar a ferramenta certa.")
