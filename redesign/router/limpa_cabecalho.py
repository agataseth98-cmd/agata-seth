#!/usr/bin/env python3
"""limpa_cabecalho.py -- um cabeçalho só por resposta da Seth (anomalia do cabeçalho duplo, 17/10/2026).

O cabeçalho da Regra 1 é da Máquina ((705)): o gateway o injeta medido no começo da resposta. O modelo, hidratado com o
canon (que manda abrir com cabeçalho), às vezes escreve o dele logo depois -- no caso medido de 17/10 11:56, um bloco de
prontidão com `sync:` e `HEAD=` copiados, não medidos. Este filtro apaga o cabeçalho que o MODELO escreve no INÍCIO do texto,
imediatamente depois do injetado. Só age quando o injetado existe; só no começo (depois da primeira prosa, nada é tocado);
só linhas no formato do cabeçalho (`Agata · ...`, seguidas de `Última entrada:` e `pronto.`/`quebrado:`).

Funciona em STREAMING: segura no máximo o começo ainda ambíguo (um prefixo de "Agata ·", ou uma linha de cabeçalho sem a
quebra de linha) e solta tudo ao ver que não é cabeçalho, ou ao fim da resposta (`fim`). A contagem de linhas removidas vai
para um log (só a contagem e o rótulo, nunca o texto).

LIMITES (declarados): heurística de formato, não prova de verdade; cabeçalho que o modelo escreva no MEIO da resposta (depois
de ferramenta, por exemplo) não é tocado; o injetado precisa chegar como um fragmento só (é como `_injetar_sse` o escreve).
`--selftest` roda os casos.
"""
import json
import re
import sys

_ABRES = ("agata ·", "agata-seth ·")  # as duas formas do cabeçalho (agata-seth desde 17/10/2026)
_RESTO = re.compile(r"^\s*(?:\*\*)?\s*(?:última entrada\s*:|pronto\.|quebrado\s*:)", re.I)


class LimpaCabecalho:
    def __init__(self, injetado):
        self.injetado = (injetado or "").strip()
        # 'espera' -> viu o injetado? ; 'inicio' -> começo do texto do modelo ; 'resto' -> linhas após o cabeçalho ; 'livre'
        self.fase = "espera" if self.injetado else "livre"
        self.pend = ""
        self.removidas = 0

    def _eh_prefixo_cab(self, s):
        """True se `s` ainda pode virar "Agata ·" (vazio, ou um prefixo dele)."""
        t = s.lstrip().lstrip("*").lstrip().lower()
        return t == "" or any(len(t) < len(x) and x.startswith(t) for x in _ABRES)

    def _comeca_cab(self, s):
        return s.lstrip().lstrip("*").lstrip().lower().startswith(_ABRES)

    def passar(self, texto):
        if self.fase == "livre" or not texto:
            return texto
        if self.fase == "espera":
            if texto.strip() == self.injetado:
                self.fase = "inicio"
                return texto
            self.fase = "livre"           # o primeiro texto não é o injetado: nada a fazer
            return texto
        self.pend += texto
        saida = []
        while True:
            if self.fase == "livre":
                saida.append(self.pend)
                self.pend = ""
                break
            if self.fase == "inicio":
                if self._comeca_cab(self.pend):
                    if "\n" not in self.pend:
                        break             # linha de cabeçalho ainda sem fim: segura
                    _, self.pend = self.pend.split("\n", 1)
                    self.removidas += 1
                    self.fase = "resto"
                    continue
                if self._eh_prefixo_cab(self.pend):
                    break                 # pode virar "Agata ·": segura
                self.fase = "livre"
                continue
            # fase 'resto': descarta linhas em branco e "Última entrada:" / "pronto." / "quebrado:"
            if "\n" in self.pend:
                linha, resto = self.pend.split("\n", 1)
                if not linha.strip():
                    self.pend = resto
                    continue
                if _RESTO.match(linha):
                    self.pend = resto
                    self.removidas += 1
                    continue
                self.fase = "livre"
                continue
            if not self.pend.strip():
                break
            if _RESTO.match(self.pend):
                break                     # linha de rodapé do cabeçalho ainda sem fim: segura
            if any(r.startswith(self.pend.strip().lstrip("*").strip().lower()) for r in ("última entrada:", "pronto.", "quebrado:")):
                break                     # pode virar rodapé: segura
            self.fase = "livre"
        return "".join(saida)

    def fim(self):
        """Fim da resposta: solta o que estava segurando (menos uma linha de cabeçalho completa já descartável)."""
        resto, self.pend = self.pend, ""
        if self.fase == "inicio" and self._comeca_cab(resto):
            self.removidas += 1
            return ""
        if self.fase == "resto" and (not resto.strip() or _RESTO.match(resto)):
            return ""
        return resto


def _chunk(texto, base=None):
    o = {"object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {"content": texto}, "finish_reason": None}]}
    if isinstance(base, dict):
        for k in ("id", "created", "model"):
            if base.get(k) is not None:
                o[k] = base[k]
    return b"data: " + json.dumps(o, ensure_ascii=False).encode("utf-8") + b"\n\n"


def limpar_sse_linha(linha, estados, injetado):
    """Uma linha `data: ...` (bytes). `estados`: dict índice -> LimpaCabecalho (mutado). Segura o começo ambíguo e o solta antes do
    `finish_reason`/`[DONE]`. Tool_calls, role e o resto passam intactos."""
    if not linha.startswith(b"data:"):
        return linha
    corpo = linha[5:].strip()
    if corpo == b"[DONE]":
        resto = "".join(e.fim() for e in estados.values())
        return (_chunk(resto) if resto else b"") + linha
    try:
        o = json.loads(corpo)
    except ValueError:
        return linha
    if not isinstance(o, dict):
        return linha
    mudou, extra = False, b""
    for ch in o.get("choices") or []:
        d = ch.get("delta") or {}
        est = estados.setdefault(ch.get("index", 0), LimpaCabecalho(injetado))
        c = d.get("content")
        if isinstance(c, str) and c:
            novo = est.passar(c)
            if novo != c:
                d["content"] = novo
                mudou = True
        if ch.get("finish_reason"):
            resto = est.fim()
            if resto:
                extra += _chunk(resto, o)
    fim = b"\n" if linha.endswith(b"\n") else b""
    if not mudou and not extra:
        return linha
    corpo_novo = linha if not mudou else b"data: " + json.dumps(o, ensure_ascii=False).encode("utf-8") + fim
    # chunk com content vazio não precisa sair; o resto solto vem ANTES da linha com finish_reason
    return extra + corpo_novo


def limpar_json(corpo, injetado):
    """Resposta NÃO streaming. Devolve (bytes, nº de linhas removidas)."""
    try:
        o = json.loads(corpo)
        total = 0
        for ch in o.get("choices") or []:
            m = ch.get("message") or {}
            c = m.get("content")
            if isinstance(c, str) and injetado and c.startswith(injetado):
                resto = c[len(injetado):]
                est = LimpaCabecalho(injetado)
                est.fase = "inicio"
                saida = est.passar(resto) + est.fim()
                if saida != resto:
                    m["content"] = injetado + saida
                    total += est.removidas
        if not total:
            return corpo, 0
        return json.dumps(o, ensure_ascii=False).encode("utf-8"), total
    except (ValueError, AttributeError, TypeError):
        return corpo, 0


def _selftest():
    CAB = "Agata · ministral-14b-latest (Mistral, nuvem; medido pela Máquina neste turno) · t=4 (contador mecânico) · 2026-10-17 11:56 -0300 (relógio da Máquina)\n\n"
    DUP = ("Agata · modelo: ministral-14b-latest · sync: PASS · HEAD=4975b44 · 2026-10-17 11:56 -0300\n"
           "Última entrada: (741) DIÁRIO — x\n\nSistemas operacionais.")

    def rodar(frags, injetado=CAB):
        est = LimpaCabecalho(injetado)
        return "".join(est.passar(f) for f in frags) + est.fim()

    def sse(frags, injetado=CAB, fim=True):
        est, saida = {}, []
        for f in frags:
            linha = b"data: " + json.dumps({"id": "x", "choices": [{"index": 0, "delta": {"content": f}}]}, ensure_ascii=False).encode() + b"\n\n"
            saida.append(limpar_sse_linha(linha, est, injetado))
        if fim:
            saida.append(limpar_sse_linha(b'data: {"id":"x","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n', est, injetado))
            saida.append(limpar_sse_linha(b"data: [DONE]\n\n", est, injetado))
        txt = ""
        for l in b"".join(saida).split(b"\n"):
            if l.startswith(b"data: {"):
                for ch in json.loads(l[5:]).get("choices") or []:
                    txt += (ch.get("delta") or {}).get("content") or ""
        return txt, b"".join(saida)

    casos = []
    casos.append(("apaga o bloco de prontidão duplicado e deixa o injetado + corpo",
                  rodar([CAB, DUP]) == CAB + "Sistemas operacionais."))
    casos.append(("fragmentado em pedaços de 3 caracteres", rodar([CAB] + [DUP[i:i + 3] for i in range(0, len(DUP), 3)]) == CAB + "Sistemas operacionais."))
    casos.append(("fragmentado em 1 caractere", rodar([CAB] + list(DUP)) == CAB + "Sistemas operacionais."))
    casos.append(("duplicado na forma nova (agata-seth ·) também sai", rodar([CAB, "agata-seth · modelo: x · sync: PASS · HEAD=1\nÚltima entrada: (1) x\npronto.\nCorpo."]) == CAB + "Corpo."))
    casos.append(("injetado na forma nova: o duplicado do modelo sai", rodar([CAB.replace("Agata ·", "agata-seth ·", 1), "agata-seth · x · t=4 · hora\nCorpo."], injetado=CAB.replace("Agata ·", "agata-seth ·", 1)) == CAB.replace("Agata ·", "agata-seth ·", 1) + "Corpo."))
    casos.append(("linha de turno duplicada (t=...) também sai",
                  rodar([CAB, "Agata · ministral · t=4 (contador mecânico) · 2026-10-17 11:56\nResposta."]) == CAB + "Resposta."))
    casos.append(("cabeçalho em negrito do modelo sai", rodar([CAB, "**Agata · x · t=4 · hora**\nCorpo."]) == CAB + "Corpo."))
    casos.append(("prosa normal passa intacta", rodar([CAB, "Sincronizado. Agata · não é cabeçalho aqui."]) == CAB + "Sincronizado. Agata · não é cabeçalho aqui."))
    casos.append(("começa com 'Aga' mas não é cabeçalho: solta tudo", rodar([CAB, "Agarrei o ponto.", " Fim."]) == CAB + "Agarrei o ponto. Fim."))
    casos.append(("só 'Agat' e acaba: não perde o texto", rodar([CAB, "Agat"]) == CAB + "Agat"))
    casos.append(("sem injetado o filtro não age", rodar(["Agata · modelo: x · sync: PASS\nCorpo."], injetado=None) == "Agata · modelo: x · sync: PASS\nCorpo."))
    casos.append(("1º texto que não é o injetado desliga o filtro", rodar(["Agata · x · t=4\nCorpo."]) == "Agata · x · t=4\nCorpo."))
    casos.append(("cabeçalho no meio do texto não é tocado",
                  rodar([CAB, "Resposta.\nAgata · x · t=4 · hora\nMais."]) == CAB + "Resposta.\nAgata · x · t=4 · hora\nMais."))
    casos.append(("rodapé depois de prosa não é tocado", rodar([CAB, "Texto.\npronto.\nFim."]) == CAB + "Texto.\npronto.\nFim."))
    casos.append(("cabeçalho só, sem corpo: não devolve lixo", rodar([CAB, "Agata · x · t=4 · hora"]) == CAB))
    t1, raw = sse([CAB, DUP[:20], DUP[20:]])
    casos.append(("SSE: injetado + corpo, duplicata sumiu", t1 == CAB + "Sistemas operacionais." and b"[DONE]" in raw))
    t2, raw2 = sse([CAB, "Agat"])
    casos.append(("SSE: texto retido sai ANTES do finish_reason", t2 == CAB + "Agat" and raw2.index(b"Agat") < raw2.index(b"finish_reason")))
    casos.append(("SSE: tool_calls e role passam intactos",
                  limpar_sse_linha(b'data: {"choices":[{"index":0,"delta":{"role":"assistant","tool_calls":[{"id":"1"}]}}]}\n\n', {}, CAB)
                  == b'data: {"choices":[{"index":0,"delta":{"role":"assistant","tool_calls":[{"id":"1"}]}}]}\n\n'))
    j = json.dumps({"choices": [{"message": {"content": CAB + DUP}}]}, ensure_ascii=False).encode()
    novo, n = limpar_json(j, CAB)
    casos.append(("JSON não streaming: remove e conta", json.loads(novo)["choices"][0]["message"]["content"] == CAB + "Sistemas operacionais." and n == 2))
    novo2, n2 = limpar_json(json.dumps({"choices": [{"message": {"content": "sem injetado"}}]}).encode(), CAB)
    casos.append(("JSON sem o injetado passa", n2 == 0))
    ruins = [n for n, ok in casos if not ok]
    for n, ok in casos:
        print(("OK    " if ok else "FALHOU"), n)
    print(f"limpa_cabecalho selftest: {len(casos) - len(ruins)}/{len(casos)}")
    return 1 if ruins else 0


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else 0)
