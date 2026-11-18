#!/usr/bin/env python3
"""porta_entrada.py — porta de entrada de modelo novo (decisão do Humano, 18/11/2026).

Todo modelo novo (local, pago ou gratuito na nuvem) passa pelo benchmark_roteamento antes de entrar
em rota. Este script compara o resumo do modelo novo com os resumos já medidos e dá um veredito:

  util      ganho estrito sobre um rival comparável (outro modelo, ao menos 1 tipo em comum): nota maior,
            ou nota igual e p50 estritamente menor, em algum tipo de pedido;
  dominado  outro modelo é >= em todos os tipos em comum e é mais rápido em p50;
  inutil    taxa_erro > 0.5 ou p50 > 120 s (fora da comparação dos demais);
  neutro    nenhum dos três (inclui "sem rival comparável").

Dados inválidos (taxa_erro fora de [0,1], nota ou latência não finita, base sem outro modelo) recusam com
saída 2, sem traceback. Base: PASTA/resumo-*.json e PASTA/*/resumo.json.

Polaridade das checagens (explícita): json_valido e ferramenta_valida são positivas (True = acerto);
deu_porcentagem é negativa (True = falha, desconta a nota); escreveu_sem_portao é negativa e só gera aviso;
chamou_ferramenta é ignorada; checagem desconhecida é ignorada com aviso. A nota também desconta resposta
vazia (sem texto fora de <think> e sem chamada de ferramenta) e bloco ```python que não passa em ast.parse
(só se analisa, nunca se executa). "</think>" no texto gera aviso de raciocínio vazado.

"Escreveu sem portão" (escreveu_sem_portao > 0) é aviso, nunca veredito.

Tipos de pedido: se existir respostas.jsonl ao lado do resumo (linhas com modelo, tipo, estado, s,
checagens), a nota é por tipo (codigo, ferramenta, json, conversa, contexto; "contexto_longo" vale
"contexto"). Sem ele, o resumo só dá três notas: "geral" (1 - taxa_erro), "json" (json_valido) e
"ferramenta" (ferramenta_valida). Compara-se só nos tipos presentes em ambos: resumo de nuvem sem o
tipo "contexto" (item privado não sai da Máquina) é aceito. Nota é mecânica, não é juízo de qualidade.

  porta_entrada.py comparar --resumo NOVO.json --base PASTA [--json] [--so-novo]
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import re
import sys
from pathlib import Path

ERRO_MAX = 0.5
P50_MAX = 120.0
EPS = 1e-9
POSITIVAS = {"json_valido", "ferramenta_valida"}   # True = acerto
NEGATIVAS = {"deu_porcentagem"}                     # True = falha (desconta a nota)
SO_AVISO = {"escreveu_sem_portao"}                  # negativa, mas vira aviso, não nota
IGNORADAS = {"chamou_ferramenta"}
_THINK = re.compile(r"<think>.*?(?:</think>|\Z)", re.S)
_PY = re.compile(r"```(?:python|py)\s*\n(.*?)(?:```|\Z)", re.S)
LIMITADAS = ("taxa_erro", "json_valido", "ferramenta_valida", "deu_porcentagem", "escreveu_sem_portao")


class DadosInvalidos(ValueError):
    """Resumo ou respostas com número inválido ou base sem rival: recusa controlada."""


def _num(v, rotulo: str, teto: float | None = None) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 or (
            teto is not None and v > teto):
        raise DadosInvalidos(f"{rotulo} inválido: {v!r}" + (f" (esperado finito em [0,{teto:g}])" if teto is not None
                                                              else " (esperado finito >= 0)"))
    return float(v)


def _tipo(t: str) -> str:
    return "contexto" if str(t).startswith("contexto") else str(t)


def _p50(xs: list[float]) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(round(0.5 * (len(s) - 1))))]


def _metricas(entrada: dict, modelo: str) -> dict:
    if not isinstance(entrada, dict) or not isinstance(entrada.get("medido", []), list):
        raise DadosInvalidos(f"{modelo}: entrada do resumo malformada")
    out = {}
    for m in entrada.get("medido", []):
        if not isinstance(m, dict) or "metrica" not in m:
            raise DadosInvalidos(f"{modelo}: medida malformada")
        k = m["metrica"]
        if k in LIMITADAS or k in ("latencia_p50_s", "latencia_p95_s"):
            out[k] = _num(m.get("valor"), f"{modelo}: {k}", 1.0 if k in LIMITADAS else None)
    return out


def _texto_util(l: dict) -> str:
    return _THINK.sub("", l.get("texto") or "").strip()


def _passou(l: dict, avisos: set) -> bool:
    """Item aprovado? Estado ok, checagens com polaridade explícita, texto não vazio, Python que compila."""
    if l.get("estado") != "ok":
        return False
    texto = l.get("texto") or ""
    if "</think>" in texto:
        avisos.add("raciocínio vazado (</think> no texto)")
    ok = True
    for k, v in (l.get("checagens") or {}).items():
        if k in POSITIVAS:
            ok = ok and bool(v)
        elif k in NEGATIVAS:
            ok = ok and not v
        elif k in SO_AVISO:
            if v:
                avisos.add("escreveu sem portão (aviso, não veredito)")
        elif k not in IGNORADAS:
            avisos.add(f"checagem desconhecida ignorada: {k}")
    if not _texto_util(l) and not l.get("chamadas"):
        ok = False
    for bloco in _PY.findall(_THINK.sub("", texto)):
        try:
            ast.parse(bloco)
        except (SyntaxError, ValueError):
            ok = False
    return ok


def _por_tipo(linhas: list[dict], avisos: set) -> tuple[dict, dict]:
    """(notas por tipo, p50 por tipo) a partir das linhas de respostas.jsonl de um modelo."""
    por: dict[str, list[dict]] = {}
    for l in linhas:
        if l.get("estado") == "pulado_privacidade" or "tipo" not in l:
            continue
        por.setdefault(_tipo(l["tipo"]), []).append(l)
    notas, p50s = {}, {}
    for t, ls in por.items():
        notas[t] = sum(_passou(l, avisos) for l in ls) / len(ls)
        xs = [_num(l.get("s"), f"{t}: s") for l in ls if l.get("estado") == "ok"]
        p = _p50(xs)
        if p is not None:
            p50s[t] = p
    return notas, p50s


def carregar(resumo: Path, novo: bool) -> dict[str, dict]:
    """Lê um resumo (e o respostas.jsonl ao lado, se houver). Devolve {modelo: ficha}."""
    dados = json.loads(resumo.read_text(encoding="utf-8"))
    if not isinstance(dados, dict):
        raise DadosInvalidos(f"{resumo.name}: o resumo deve ser um objeto por modelo")
    if not dados:
        raise DadosInvalidos(f"{resumo.parent.name}/{resumo.name}: resumo sem nenhum modelo")
    respostas: dict[str, list[dict]] = {}
    arq = resumo.parent / "respostas.jsonl"
    if arq.exists():
        for bruto in arq.read_text(encoding="utf-8").splitlines():
            if bruto.strip():
                try:
                    l = json.loads(bruto)
                except ValueError:
                    continue
                if isinstance(l, dict) and "modelo" in l:
                    respostas.setdefault(l["modelo"], []).append(l)
    out = {}
    for modelo, ent in dados.items():
        m = _metricas(ent, modelo)
        erro = m.get("taxa_erro")
        if erro is None and ent.get("feitas"):
            erro = _num(1 - _num(ent.get("ok", 0), f"{modelo}: ok") / _num(ent["feitas"], f"{modelo}: feitas"),
                        f"{modelo}: taxa_erro derivada", 1.0)
        avisos: set = set()
        notas, p50s = _por_tipo(respostas.get(modelo, []), avisos)
        if not notas:
            if erro is not None:
                notas["geral"] = 1 - erro
            for metrica, tipo in (("json_valido", "json"), ("ferramenta_valida", "ferramenta")):
                if metrica in m:
                    notas[tipo] = m[metrica]
        out[modelo] = {"modelo": modelo, "novo": novo, "taxa_erro": erro, "p50": m.get("latencia_p50_s"),
                       "notas": notas, "p50_tipo": p50s, "origem": str(resumo),
                       "avisos": sorted(avisos | ({"escreveu sem portão (aviso, não veredito)"}
                                                  if (m.get("escreveu_sem_portao") or 0) > 0 else set()))}
    return out


def _inutil(f: dict) -> bool:
    return f["taxa_erro"] is None or f["taxa_erro"] > ERRO_MAX or f["p50"] is None or f["p50"] > P50_MAX


def _p(f: dict, tipo: str) -> float:
    return f["p50_tipo"].get(tipo, f["p50"] if f["p50"] is not None else float("inf"))


def veredito(fichas: dict[str, dict]) -> dict[str, dict]:
    """Acrescenta 'veredito' e 'motivo' a cada ficha."""
    validas = {m: f for m, f in fichas.items() if not _inutil(f)}
    for m, f in fichas.items():
        if m not in validas:
            f["veredito"], f["motivo"] = "inutil", f"taxa_erro={f['taxa_erro']} p50={f['p50']} (limites: erro>{ERRO_MAX}, p50>{P50_MAX}s)"
            continue
        ganhos, comparavel = [], False
        for t, nota in f["notas"].items():
            rivais = [g for g in validas.values() if g is not f and t in g["notas"]]
            if not rivais:
                continue
            comparavel = True
            if all(nota > g["notas"][t] + EPS or (abs(nota - g["notas"][t]) <= EPS and _p(f, t) < _p(g, t) - EPS)
                   for g in rivais):
                ganhos.append(t)
        if ganhos:
            f["veredito"], f["motivo"] = "util", "ganho estrito sobre os rivais em: " + ", ".join(sorted(ganhos))
            continue
        if not comparavel:
            f["veredito"], f["motivo"] = "neutro", "sem rival comparável (nenhum outro modelo válido com tipo em comum)"
            continue
        dominador = None
        for g in validas.values():
            if g is f:
                continue
            comuns = set(f["notas"]) & set(g["notas"])
            if comuns and all(g["notas"][t] >= f["notas"][t] - EPS for t in comuns) and g["p50"] < f["p50"]:
                dominador = g["modelo"]
                break
        if dominador:
            f["veredito"], f["motivo"] = "dominado", f"{dominador} é >= em todos os tipos em comum e mais rápido"
        else:
            f["veredito"], f["motivo"] = "neutro", "nem melhor em tipo algum, nem dominado"
    return fichas


def comparar(resumo: Path, base: Path) -> dict[str, dict]:
    fichas: dict[str, dict] = {}
    arqs = sorted(base.glob("resumo-*.json")) + sorted(base.glob("*/resumo.json"))
    arqs = [a for a in arqs if a.resolve() != resumo.resolve()]
    if not arqs:
        raise ValueError(f"base sem resumo para comparar: {base} (resumo-*.json ou */resumo.json)")
    for arq in arqs:
        fichas.update(carregar(arq, False))
    novos = carregar(resumo, True)
    if not any(m not in novos for m in fichas):
        raise DadosInvalidos("base sem nenhum modelo diferente do novo: nada para comparar")
    fichas.update(novos)  # o novo prevalece sobre o mesmo modelo na base
    return veredito(fichas)


def tabela(fichas: dict[str, dict], so_novo: bool = False) -> str:
    linhas = ["novo | modelo | veredito | erro | p50 s | notas | motivo / aviso"]
    for m, f in sorted(fichas.items()):
        if so_novo and not f["novo"]:
            continue
        notas = " ".join(f"{t}={n:.2f}" for t, n in sorted(f["notas"].items())) or "-"
        extra = f["motivo"] + ("; " + "; ".join(f["avisos"]) if f["avisos"] else "")
        linhas.append(f"{'*' if f['novo'] else ' '} | {m} | {f['veredito']} | {f['taxa_erro']} | {f['p50']} | {notas} | {extra}")
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Porta de entrada: compara resumo novo com os medidos")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("comparar")
    c.add_argument("--resumo", required=True, type=Path)
    c.add_argument("--base", required=True, type=Path)
    c.add_argument("--json", action="store_true")
    c.add_argument("--so-novo", action="store_true", help="mostra só os modelos do resumo novo")
    a = ap.parse_args(argv)
    if not a.resumo.is_file() or not a.base.is_dir():
        print("recusado: --resumo deve ser arquivo e --base deve ser pasta", file=sys.stderr)
        return 2
    try:
        fichas = comparar(a.resumo, a.base)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as e:
        print(f"recusado: resumo ilegível: {e}", file=sys.stderr)
        return 2
    if a.json:
        sel = {m: f for m, f in fichas.items() if f["novo"] or not a.so_novo}
        print(json.dumps(sel, ensure_ascii=False, indent=2))
    else:
        print(tabela(fichas, a.so_novo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
