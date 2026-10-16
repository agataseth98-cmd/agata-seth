#!/usr/bin/env python3
"""limpa_emoji.py -- remove emoji da PROSA da resposta da Seth (E-2, decisão do Humano de 16/10/2026: "remover").

Puro e sem rede. A regex é a MESMA do aviso da auditoria (`auditoria_turno._EMOJI`, E-1): uma só régua. Não remove em:
bloco de código (``` ao início da linha), código em linha (`...`), citação entre aspas ("..." “...” «...») nem linha de citação (`>`).
Funciona em STREAMING: o estado (bloco de código, aspas, crase, início de linha) atravessa os fragmentos de `delta.content`.
Um emoji de várias partes (ZWJ, seletor, tom de pele) que atravesse dois fragmentos é removido peça a peça: o seletor U+FE0F
e o tom de pele estão na regex, e o ZWJ (U+200D) só é removido logo depois de um emoji removido.

LIMITES (declarados): detecta bloco de código só pela cerca ``` no início da linha; não entende HTML/Markdown aninhado; aspas
não fechadas valem até o fim da linha; é heurística de estilo, não filtro de segurança. A contagem de removidos vai para um log
(só códigos Unicode e contagem, nunca o texto) -- o aviso da auditoria deixa de ver o emoji no turno seguinte porque o cliente
guarda a resposta já limpa; o log é a medida do que o MODELO produziu.

Uso como módulo: `LimpaEmoji().passar(texto) -> texto`; `limpar_sse_linha(linha_bytes, estados)`; `limpar_json(corpo_bytes)`.
`--selftest` roda os casos.
"""
import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditoria_turno import _EMOJI  # noqa: E402  (mesma régua do aviso)

_ABRE = {'"': '"', "“": "”", "«": "»"}


class LimpaEmoji:
    def __init__(self):
        self.em_bloco = False      # dentro de ``` ... ```
        self.em_inline = False     # dentro de `...` (reinicia na quebra de linha)
        self.fecha_aspas = None    # caractere que fecha a citação aberta (reinicia na quebra de linha)
        self.inicio = True         # só espaços desde o início da linha
        self.linha_cit = False     # linha começa com '>'
        self.prefixo = ""          # primeiros caracteres não-espaço da linha (detectar ```)
        self.removeu_antes = False
        self.removidos = []        # pontos de código removidos (só para o log)

    def _fim_de_linha(self):
        self.em_inline = False
        self.fecha_aspas = None
        self.inicio = True
        self.linha_cit = False
        self.prefixo = ""
        self.removeu_antes = False

    def passar(self, texto):
        saida = []
        for ch in texto:
            if ch == "\n":
                saida.append(ch)
                self._fim_de_linha()
                continue
            # detecção da cerca ``` no início da linha (atravessa fragmentos)
            if self.inicio and not ch.isspace():
                self.prefixo += ch
                if self.prefixo.startswith(">"):
                    self.linha_cit = True
                if len(self.prefixo) == 3 or (not set(self.prefixo) <= {"`"}):
                    if self.prefixo == "```":
                        self.em_bloco = not self.em_bloco
                    self.inicio = False
            protegido = self.em_bloco or self.em_inline or self.fecha_aspas or self.linha_cit or self.prefixo.startswith("`")
            if not self.em_bloco and ch == "`" and not self.prefixo.startswith("```"):
                self.em_inline = not self.em_inline
            elif not self.em_bloco and not self.em_inline and not self.linha_cit:
                if self.fecha_aspas:
                    if ch == self.fecha_aspas:
                        self.fecha_aspas = None
                elif ch in _ABRE:
                    self.fecha_aspas = _ABRE[ch]
            if not protegido and _EMOJI.fullmatch(ch):
                self.removidos.append(f"U+{ord(ch):04X}")
                self.removeu_antes = True
                continue
            if not protegido and ch == "‍" and self.removeu_antes:   # ZWJ solto depois de emoji removido
                continue
            self.removeu_antes = False
            saida.append(ch)
        return "".join(saida)


def limpar_sse_linha(linha, estados):
    """`linha`: uma linha `data: {...}` (bytes, com ou sem \\n). `estados`: dict índice-da-escolha -> LimpaEmoji (mutado).
    Só mexe em `choices[].delta.content` (texto). tool_calls, role e o resto passam intactos. Qualquer coisa que não seja JSON
    de chat passa intacta."""
    if not linha.startswith(b"data:") or b'"content"' not in linha:
        return linha
    corpo = linha[5:].strip()
    if corpo == b"[DONE]":
        return linha
    try:
        o = json.loads(corpo)
        mudou = False
        for ch in o.get("choices") or []:
            d = ch.get("delta") or {}
            c = d.get("content")
            if isinstance(c, str) and c:
                est = estados.setdefault(ch.get("index", 0), LimpaEmoji())
                novo = est.passar(c)
                if novo != c:
                    d["content"] = novo
                    mudou = True
        if not mudou:
            return linha
        fim = b"\n" if linha.endswith(b"\n") else b""
        return b"data: " + json.dumps(o, ensure_ascii=False).encode("utf-8") + fim
    except (ValueError, AttributeError, TypeError):
        return linha


def limpar_json(corpo):
    """Resposta NÃO streaming: `choices[].message.content`. Devolve (bytes, [pontos de código removidos])."""
    try:
        o = json.loads(corpo)
        removidos = []
        for ch in o.get("choices") or []:
            m = ch.get("message") or {}
            c = m.get("content")
            if isinstance(c, str) and c:
                est = LimpaEmoji()
                novo = est.passar(c)
                if novo != c:
                    m["content"] = novo
                    removidos += est.removidos
        if not removidos:
            return corpo, []
        return json.dumps(o, ensure_ascii=False).encode("utf-8"), removidos
    except (ValueError, AttributeError, TypeError):
        return corpo, []


def _selftest():
    E1, E2, E3, E4 = "✅", "\U0001F600", "❌", "⚠️"
    casos = []
    L = lambda t: LimpaEmoji().passar(t)
    casos.append(("remove da prosa", L(f"Feito {E1} e ok {E2}.") == "Feito  e ok ."))
    casos.append(("preserva acento e símbolos tipográficos", L("ação → © ✓ ★ ™") == "ação → © ✓ ★ ™"))
    casos.append(("preserva em bloco de código", L(f"a\n```\nx = '{E1}'\n```\nb {E2}") == f"a\n```\nx = '{E1}'\n```\nb "))
    casos.append(("preserva em código em linha", L(f"use `{E3}` aqui {E3}") == f"use `{E3}` aqui "))
    casos.append(("preserva em citação entre aspas", L(f'ele disse "ok {E1}" e {E1}') == f'ele disse "ok {E1}" e '))
    casos.append(("preserva em linha de citação >", L(f"> {E1} citado\ntexto {E1}") == f"> {E1} citado\ntexto "))
    casos.append(("remove emoji de duas peças (VS16)", L(f"x {E4} y") == "x  y"))
    casos.append(("ZWJ solto após emoji removido sai; ZWJ legítimo fica", L("a\U0001F468‍\U0001F469b") == "ab" and L("a‍b") == "a‍b"))
    # streaming: fragmentos que cortam cerca, aspas e emoji
    est = LimpaEmoji()
    frag = ["Veja\n", "``", "`\nx=", E1, "\n``", "`\nfim ", E2, " \"cit", E1, "ado\" ", E3]
    sai = "".join(est.passar(f) for f in frag)
    casos.append(("streaming: cerca ``` partida em 2 fragmentos", sai == f"Veja\n```\nx={E1}\n```\nfim  \"cit{E1}ado\" "))
    est = LimpaEmoji()
    casos.append(("streaming: contagem de removidos", (est.passar(f"a{E1}"), est.passar(f"b{E2}"), est.removidos) == ("a", "b", ["U+2705", "U+1F600"])))
    # SSE: só o texto muda; tool_calls e [DONE] intactos
    st = {}
    l1 = b'data: {"choices":[{"index":0,"delta":{"content":"ok \\u2705 fim"}}]}\n'
    l2 = b'data: {"choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\\"a\\":\\"\\u2705\\"}"}}]}}]}\n'
    r1 = limpar_sse_linha(l1, st)
    casos.append(("SSE: content limpo", b"\xe2\x9c\x85" not in r1 and b"ok  fim" in r1 and r1.endswith(b"\n")))
    casos.append(("SSE: tool_calls intactos", limpar_sse_linha(l2, st) == l2))
    casos.append(("SSE: [DONE] e comentário intactos", limpar_sse_linha(b"data: [DONE]\n", st) == b"data: [DONE]\n" and limpar_sse_linha(b": ka\n", st) == b": ka\n"))
    casos.append(("SSE: lixo não derruba", limpar_sse_linha(b'data: {"content": quebrado\n', st) == b'data: {"content": quebrado\n'))
    corpo = json.dumps({"choices": [{"message": {"content": f"Pronto {E1}"}}]}).encode()
    novo, rem = limpar_json(corpo)
    casos.append(("JSON não streaming: limpa e devolve removidos", json.loads(novo)["choices"][0]["message"]["content"] == "Pronto " and rem == ["U+2705"]))
    casos.append(("JSON sem emoji: bytes idênticos", limpar_json(b'{"choices":[{"message":{"content":"oi"}}]}') == (b'{"choices":[{"message":{"content":"oi"}}]}', [])))
    casos.append(("JSON inválido passa", limpar_json(b"nao json") == (b"nao json", [])))
    ruins = 0
    for nome, ok in casos:
        print(("PASS  " if ok else "FALHA ") + nome)
        ruins += not ok
    print(f"limpa_emoji selftest: {len(casos) - ruins}/{len(casos)}")
    return 1 if ruins else 0


if __name__ == "__main__":
    sys.exit(_selftest() if len(sys.argv) > 1 and sys.argv[1] == "--selftest" else 0)
