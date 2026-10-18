#!/usr/bin/env python3
"""limpa_laco.py -- trava de laço de repetição na resposta da Seth (sonda 18 da rodada de 17/10/2026).

Caso medido (banco do LibreChat, 18/10/2026; conversa da "Validação 18/30", 17/10 ~20:43): depois de uma chamada de
ferramenta, o codestral-latest escreveu a resposta, ecoou o bloco de estado que o gateway injeta, parafraseou a doutrina e
degenerou repetindo a mesma frase (~60 caracteres) até 117.771 caracteres. Nas outras duas corridas da mesma sonda, nada.

Este filtro olha o texto que o modelo está mandando e, quando o FIM dele vira periódico -- o mesmo trecho de p caracteres
repetido em sequência n vezes, com n = max(REPETICOES, ceil(JANELA_MIN / p)) -- para de repassar conteúdo, manda uma nota
curta ao Humano e fecha o SSE de forma válida (chunk com finish_reason "stop" e `data: [DONE]`). O gateway então solta o
upstream. Trecho curto precisa repetir mais (20 caracteres: 20 vezes; 100: 4 vezes), e trecho pobre (menos de
MIN_DISTINTOS caracteres diferentes ou sem letra: régua `-----`, linha de tabela `| --- |`) nunca conta.

O eco do bloco de estado (linha que começa com `AUDITORIA-TURNO-ANTERIOR: ` ou `MESMA-RESPOSTA: `, ou o marcador do
estado) só é REGISTRADO, não corta: no caso medido ele custou ~1,4 mil caracteres antes do laço, e cortar por ele pegaria
a Seth citando o próprio gateway numa conversa sobre o código. O log diz se houve eco; com dado, decide-se depois.

LIMITES (declarados): só o caminho SSE (o LibreChat usa stream; resposta não streaming passa intacta); laço não exato
(números que mudam a cada volta, paráfrase) não é pego; o que já saiu antes do corte já saiu -- o Humano vê as primeiras
repetições e a nota. Log: só contagens e o período, nunca o texto. `--selftest` roda os casos.
"""
import json
import math
import re
import sys

REPETICOES = 4          # mínimo de voltas seguidas do mesmo trecho
JANELA_MIN = 400        # o trecho repetido tem de cobrir pelo menos isto (caracteres)
PERIODO_MIN, PERIODO_MAX = 20, 500
MIN_DISTINTOS = 8
PASSO = 32              # testa a cada 32 caracteres novos
NOTA = ("\n\n[Corte da Máquina: a resposta entrou em laço de repetição e o resto foi descartado. "
        "Peça de novo se precisar.]")
_ECO = re.compile(r"(?m)^\s*(?:AUDITORIA-TURNO-ANTERIOR: |MESMA-RESPOSTA: |<!-- SETH:ESTADO-ATUAL -->)")


class TravaLaco:
    def __init__(self, repeticoes=REPETICOES):
        self.rep = max(2, int(repeticoes))
        self.texto = ""
        self._testado = 0
        self.cortado = False
        self.periodo = 0
        self.voltas = 0

    def _laco(self):
        t = self.texto
        for p in range(PERIODO_MIN, PERIODO_MAX + 1):
            n = max(self.rep, math.ceil(JANELA_MIN / p))
            w = p * n
            if w > len(t):
                break
            # periódico de período p na janela w  <=>  t[-w:-p] == t[-w+p:]
            if t[-1] == t[-1 - p] and t[-w:-p] == t[-w + p:]:
                u = t[-p:]
                if len(set(u)) >= MIN_DISTINTOS and any(c.isalpha() for c in u):
                    self.periodo, self.voltas = p, n
                    return True
        return False

    def passar(self, texto):
        """Devolve o que pode sair deste fragmento ("" depois do corte)."""
        if self.cortado or not texto:
            return "" if self.cortado else texto
        self.texto += texto
        if len(self.texto) - self._testado >= PASSO:
            self._testado = len(self.texto)
            if self._laco():
                self.cortado = True
                return ""
        return texto

    @property
    def eco(self):
        return bool(_ECO.search(self.texto))


def _chunk(base, delta, finish=None):
    o = {"object": "chat.completion.chunk", "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
    if isinstance(base, dict):
        for k in ("id", "created", "model"):
            if base.get(k) is not None:
                o[k] = base[k]
    return b"data: " + json.dumps(o, ensure_ascii=False).encode("utf-8") + b"\n\n"


def limpar_sse(saida, estados, repeticoes=REPETICOES):
    """`saida`: bytes já filtrados (uma ou mais linhas SSE). `estados`: dict índice -> TravaLaco (mutado).
    Devolve (bytes, cortou_agora). Depois do corte, tudo vira b"" -- quem chama para de ler o upstream."""
    if any(e.cortado for e in estados.values()):
        return b"", False
    out = []
    for linha in saida.splitlines(keepends=True):
        if not linha.startswith(b"data:"):
            out.append(linha)
            continue
        try:
            o = json.loads(linha[5:])
        except ValueError:
            out.append(linha)
            continue
        if not isinstance(o, dict):
            out.append(linha)
            continue
        for ch in o.get("choices") or []:
            d = ch.get("delta") or {}
            c = d.get("content")
            if not (isinstance(c, str) and c):
                continue
            est = estados.setdefault(ch.get("index", 0), TravaLaco(repeticoes))
            novo = est.passar(c)
            if est.cortado:
                out.append(_chunk(o, {"content": NOTA}) + _chunk(o, {}, "stop") + b"data: [DONE]\n\n")
                return b"".join(out), True
            d["content"] = novo
        out.append(linha)
    return b"".join(out), False


def _selftest():
    import random

    def sse(frags):
        return [b"data: " + json.dumps({"id": "x", "model": "m", "choices": [{"index": 0, "delta": {"content": f}}]},
                                       ensure_ascii=False).encode() + b"\n\n" for f in frags]

    def rodar(texto, tam=7, rep=REPETICOES):
        est, saida, cortou = {}, [], False
        frags = [texto[i:i + tam] for i in range(0, len(texto), tam)]
        for linha in sse(frags) + [b'data: {"id":"x","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n',
                                   b"data: [DONE]\n\n"]:
            b, c = limpar_sse(linha, est, rep)
            saida.append(b)
            cortou = cortou or c
        txt = ""
        bruto = b"".join(saida)
        for l in bruto.split(b"\n"):
            if l.startswith(b"data: {"):
                for ch in json.loads(l[5:]).get("choices") or []:
                    txt += (ch.get("delta") or {}).get("content") or ""
        return txt, bruto, cortou, est.get(0)

    frase = "Não cite o arquivo histórico sem `vault_consultar extras/`. "
    eco = ("ativa\n\nAUDITORIA-TURNO-ANTERIOR: OK\nMESMA-RESPOSTA: continuação da sua resposta depois de ferramenta.\n\n"
           "Não cite o canon sem a ferramenta `query_canon`. ")
    laco = eco + frase * 2000  # ~120 mil caracteres, como no caso medido
    t1, b1, c1, e1 = rodar(laco)
    prosa = ("O serviço agata-manutencao.service existe e está ativo desde 20:41. A unidade roda o backup do vault, "
             "a consolidação e a checagem do perímetro. ") * 1
    casos = [
        ("laço medido (eco + frase repetida, 120 mil): corta cedo, nota, finish_reason e [DONE] uma vez",
         c1 and len(t1) < 2500 and t1.endswith(NOTA) and b1.count(b"[DONE]") == 1
         and b1.count(b'"finish_reason": "stop"') == 1 and e1.periodo == len(frase)),
        ("eco do estado é registrado", e1.eco),
        ("prosa normal passa intacta", rodar(prosa)[0] == prosa and not rodar(prosa)[2]),
        ("régua de 300 traços e tabela repetida não cortam",
         not rodar("Resumo:\n" + "-" * 300 + "\n" + "| --- | --- | --- |\n" * 40 + "fim")[2]),
        ("3 linhas iguais de código (abaixo do mínimo) não cortam",
         not rodar("```\n" + "    self.assertEqual(soma(1, 2), 3)\n" * 3 + "```\nOk.")[2]),
        ("texto aleatório longo (20 mil) não corta",
         not rodar("".join(random.Random(7).choice("abcdefghij klmnop.,\n") for _ in range(20000)))[2]),
        ("fragmento de 1 caractere também corta", rodar(frase * 50, tam=1)[2]),
        ("tool_calls e linhas sem conteúdo passam intactas",
         limpar_sse(b'data: {"choices":[{"index":0,"delta":{"tool_calls":[{"index":0}]}}]}\n', {})[0]
         == b'data: {"choices":[{"index":0,"delta":{"tool_calls":[{"index":0}]}}]}\n'),
        ("depois do corte, nada mais sai",
         limpar_sse(b'data: {"choices":[{"index":0,"delta":{"content":"x"}}]}\n', {0: e1})[0] == b""),
    ]
    falhas = 0
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
        falhas += 0 if ok else 1
    print(f"(laço medido: {len(t1)} caracteres saíram de {len(laco)}; período {e1.periodo}, {e1.voltas} voltas)")
    print(f"\n{'SELFTEST OK' if not falhas else f'SELFTEST FALHOU ({falhas})'}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        raise SystemExit(_selftest())
    print(__doc__)
