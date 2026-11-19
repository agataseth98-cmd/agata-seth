#!/usr/bin/env python3
"""Placar de modelos por tipo de pedido (19/11/2026): todo modelo tem sua chance no que é bom.

Agrega, por modelo x tipo (conversa, codigo, json, ferramenta, contexto), o que já foi medido:
nota (mesma lógica de scripts/porta_entrada.py, importada, não duplicada), latência p50/p95, n,
data, protocolo (prompt neutro ou --prompt-real), custo, confiança do provedor e estado no painel.

  placar.py gerar [--fontes DIR ...] [--saida ARQ]     grava placar.json (0600)
  placar.py melhores --tipo T --classe publico|pessoal [--n N] [--placar ARQ] [--json]

Confiança: local (hardware da Máquina) | pago_sem_treino (só por override em tarifas.json) | gratuito
(sem garantia de não treinar). Classe publico aceita qualquer confiança; pessoal só local; segredo, nenhum.
Estado: última decisão em decisoes.jsonl do catálogo; standby (ou aposentado/vetado) tira o modelo.
Amostra pequena (n < 6) entra com aviso e peso menor (nota puxada para 0,5); nenhum modelo é descartado
por amostra pequena. Nota é mecânica, não é juízo de qualidade. Não chama provedor, só lê arquivos.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TIPOS = ("conversa", "codigo", "json", "ferramenta", "contexto")
CLASSES = ("publico", "pessoal")
N_MIN = 6
LOCAIS = ("ollama-local", "llamacpp-local", "llama-cpp", "ollama", "llamacpp")
FORA = {"standby", "aposentado", "vetado"}
HOME = Path(os.path.expanduser("~"))
FONTES_PADRAO = [
    HOME / ".local/share/agata/benchmark",
    HOME / "agata-arquivo/catalogo-modelos-18-11/prova-nvidia",
    HOME / "agata-arquivo/roteador-capacidade-17-11/competicao-locais/ollama-18-11",
    HOME / "agata-arquivo/medicao-conversa-19-11",
]


def _porta():
    spec = importlib.util.spec_from_file_location("porta_entrada", RAIZ / "scripts" / "porta_entrada.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("porta_entrada", mod)
    spec.loader.exec_module(mod)
    return mod


PE = _porta()


def pasta_saida() -> Path:
    return Path(os.environ.get("AGATA_PLACAR_DIR") or HOME / ".local/share/agata/placar")


def decisoes_arq() -> Path:
    return Path(os.environ.get("AGATA_CATALOGO_DECISOES") or HOME / ".local/share/agata/catalogo-modelos/decisoes.jsonl")


def _jsonl(arq: Path):
    if not arq.is_file():
        return
    for bruto in arq.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            d = json.loads(bruto)
        except ValueError:
            continue
        if isinstance(d, dict):
            yield d


def confianca(modelo: str, tarifas: dict) -> str:
    prov = modelo.split("/", 1)[0]
    ov = (tarifas.get(modelo) or tarifas.get(prov) or {}).get("confianca")
    if ov in ("local", "pago_sem_treino", "gratuito"):
        return ov
    return "local" if prov in LOCAIS else "gratuito"


def custo(modelo: str, tarifas: dict) -> dict:
    prov = modelo.split("/", 1)[0]
    t = tarifas.get(modelo) or tarifas.get(prov) or {}
    if prov in LOCAIS:
        return {"tipo": "gratuito", "tarifa": None, "nota": "hardware local"}
    if t.get("tarifa"):
        return {"tipo": "pago", "tarifa": t["tarifa"], "nota": None}
    if t.get("custo") == "pago":
        return {"tipo": "pago", "tarifa": None, "nota": "sem tarifa informada"}
    return {"tipo": "gratuito", "tarifa": None, "nota": "cota gratuita (não medida)"}


def estados(arq: Path) -> dict[str, dict]:
    """Última decisão por id no painel (a mais recente vence)."""
    out: dict[str, dict] = {}
    for d in sorted(_jsonl(arq), key=lambda x: str(x.get("quando", ""))):
        if d.get("id") and d.get("para"):
            out[d["id"]] = {"estado": d["para"], "quando": d.get("quando")}
    return out


def _p(xs: list[float], q: float):
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(math.ceil(q * len(s))) - 1)] if q >= 0.95 else PE._p50(s)


def _protocolo(entrada: dict, linhas: list[dict]) -> tuple[str, str]:
    medido = [m for m in entrada.get("medido", []) if isinstance(m, dict)]
    proto = next((m.get("protocolo") for m in medido if m.get("protocolo")), "") or ""
    real = "prompt-real" in proto or any(str(l.get("item", "")).endswith("_mcp_canon") for l in linhas)
    return proto, ("prompt_real" if real else "neutro")


def _data(entrada: dict, pasta: Path) -> str:
    ds = [m["data"] for m in entrada.get("medido", []) if isinstance(m, dict) and m.get("data")]
    if ds:
        return max(ds)
    return pasta.name[:8] if pasta.name[:8].isdigit() else ""


def _resumos(fonte: Path):
    if fonte.is_file():
        yield fonte
        return
    vistos = set()
    for padrao in ("resumo.json", "resumo-*.json"):
        for a in sorted(fonte.rglob(padrao)):
            if a not in vistos:
                vistos.add(a)
                yield a


def _respostas(resumo: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    arq = resumo.parent / "respostas.jsonl"
    for l in _jsonl(arq):
        if "modelo" in l:
            out.setdefault(l["modelo"], []).append(l)
    return out


def coletar(fontes: list[Path]) -> tuple[dict, list[str]]:
    """{modelo: {tipo: registro}} com o registro mais recente (empate: maior n) de cada par."""
    placar: dict[str, dict] = {}
    avisos: list[str] = []
    for fonte in fontes:
        if not fonte.exists():
            avisos.append(f"fonte ausente: {fonte}")
            continue
        for arq in _resumos(fonte):
            try:
                dados = json.loads(arq.read_text(encoding="utf-8"))
                if not isinstance(dados, dict):
                    raise ValueError("resumo não é objeto")
                resp = _respostas(arq)
            except (ValueError, OSError) as e:
                avisos.append(f"{arq}: ilegível ({e})")
                continue
            for modelo, ent in dados.items():
                try:
                    regs = _registros(modelo, ent, resp.get(modelo, []), arq, str(arq.parent))
                except (PE.DadosInvalidos, TypeError, AttributeError, KeyError) as e:
                    avisos.append(f"{arq} {modelo}: {e}")
                    continue
                for tipo, reg in regs.items():
                    atual = placar.setdefault(modelo, {}).get(tipo)
                    if atual is None or (reg["data"], reg["n"]) > (atual["data"], atual["n"]):
                        reg["execucoes"] = (atual or {}).get("execucoes", 0) + 1
                        placar[modelo][tipo] = reg
                    else:
                        atual["execucoes"] = atual.get("execucoes", 1) + 1
    return placar, avisos


def _registros(modelo: str, ent: dict, linhas: list[dict], arq: Path, origem: str) -> dict[str, dict]:
    proto, prompt = _protocolo(ent, linhas)
    data = _data(ent, arq.parent)
    base = {"data": data, "protocolo": proto, "prompt": prompt, "origem": origem}
    regs: dict[str, dict] = {}
    por: dict[str, list[dict]] = {}
    for l in linhas:
        if l.get("estado") != "pulado_privacidade" and "tipo" in l:
            por.setdefault(PE._tipo(l["tipo"]), []).append(l)
    for t, ls in por.items():
        if t not in TIPOS:
            continue
        av: set = set()
        notas, _ = PE._por_tipo(ls, av)
        xs = [PE._num(l.get("s"), f"{t}: s") for l in ls if l.get("estado") == "ok"]
        regs[t] = dict(base, nota=notas[t], n=len(ls), p50=_p(xs, 0.5), p95=_p(xs, 0.95), avisos=sorted(av))
    if not regs:  # sem respostas.jsonl: só o resumo (json, ferramenta); reaproveita porta_entrada.carregar
        ficha = PE.carregar(arq, False)[modelo]
        for t in ("json", "ferramenta"):
            if t in ficha["notas"]:
                n = next((m.get("amostra") for m in ent.get("medido", []) if m.get("metrica") == "taxa_erro"), None)
                regs[t] = dict(base, nota=ficha["notas"][t], n=int(n or 0), p50=ficha["p50"],
                               p95=next((m["valor"] for m in ent.get("medido", []) if m.get("metrica") == "latencia_p95_s"), None),
                               avisos=ficha["avisos"] + ["sem respostas.jsonl: nota do resumo"])
    return regs


def _vereditos(fontes: list[Path]) -> dict[str, str]:
    out = {}
    for f in fontes:
        for arq in ([f] if f.is_file() else f.rglob("vereditos-manuais.jsonl") if f.exists() else []):
            for d in _jsonl(arq):
                if d.get("modelo") and d.get("veredito"):
                    out[d["modelo"]] = f"{d['veredito']}: {d.get('motivo', '')}"[:160]
    return out


def gerar(fontes: list[Path], saida: Path, decisoes: Path | None = None, tarifas: dict | None = None) -> dict:
    tarifas = tarifas if tarifas is not None else _tarifas()
    cru, avisos = coletar(fontes)
    est = estados(decisoes or decisoes_arq())
    ver = _vereditos(fontes)
    modelos = {}
    for m, tipos in sorted(cru.items()):
        for t, r in tipos.items():
            r["peso"] = round(min(1.0, r["n"] / N_MIN), 3)
            r["nota_ajustada"] = round(r["nota"] * r["peso"] + 0.5 * (1 - r["peso"]), 4)
            if r["n"] < N_MIN:
                r["avisos"] = r["avisos"] + [f"amostra pequena (n={r['n']} < {N_MIN}): peso menor"]
        e = est.get(m, {})
        ent = {"confianca": confianca(m, tarifas), "custo": custo(m, tarifas), "tipos": tipos,
               "estado_painel": e.get("estado"), "estado_em": e.get("quando")}
        if m in ver:
            ent["veredito_manual"] = ver[m]
        modelos[m] = ent
    doc = {"schema_version": 1, "n_modelos": len(modelos), "fontes": [str(f) for f in fontes], "avisos": avisos,
           "modelos": modelos}
    saida.parent.mkdir(parents=True, exist_ok=True)
    tmp = saida.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, saida)
    return doc


def _tarifas() -> dict:
    arq = pasta_saida() / "tarifas.json"
    try:
        d = json.loads(arq.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def elegivel(ent: dict, classe: str) -> bool:
    if classe not in CLASSES:  # segredo (ou classe desconhecida): nenhum
        return False
    if ent.get("estado_painel") in FORA:
        return False
    return ent["confianca"] == "local" if classe == "pessoal" else True


def melhores(doc: dict, tipo: str, classe: str) -> list[dict]:
    if tipo not in TIPOS:
        raise ValueError(f"tipo desconhecido: {tipo} (use {', '.join(TIPOS)})")
    lista = []
    for m, ent in doc["modelos"].items():
        r = ent["tipos"].get(tipo)
        if r is None or not elegivel(ent, classe):
            continue
        lista.append({"modelo": m, "nota": r["nota"], "nota_ajustada": r["nota_ajustada"], "n": r["n"],
                      "p50": r["p50"], "p95": r["p95"], "confianca": ent["confianca"], "custo": ent["custo"]["tipo"],
                      "prompt": r["prompt"], "data": r["data"], "avisos": r["avisos"]})
    lista.sort(key=lambda x: (-x["nota_ajustada"], x["p50"] if x["p50"] is not None else float("inf"), x["modelo"]))
    return lista


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Placar de modelos por tipo de pedido")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gerar")
    g.add_argument("--fontes", nargs="*", type=Path, default=None)
    g.add_argument("--saida", type=Path, default=None)
    g.add_argument("--decisoes", type=Path, default=None)
    m = sub.add_parser("melhores")
    m.add_argument("--tipo", required=True)
    m.add_argument("--classe", required=True)
    m.add_argument("--n", type=int, default=0)
    m.add_argument("--placar", type=Path, default=None)
    m.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "gerar":
        saida = a.saida or pasta_saida() / "placar.json"
        doc = gerar(a.fontes or FONTES_PADRAO, saida, a.decisoes)
        print(f"placar: {doc['n_modelos']} modelos, {len(doc['avisos'])} avisos -> {saida}")
        return 0
    arq = a.placar or pasta_saida() / "placar.json"
    try:
        doc = json.loads(arq.read_text(encoding="utf-8"))
        lista = melhores(doc, a.tipo, a.classe)
    except (OSError, ValueError, KeyError) as e:
        print(f"recusado: {e}", file=sys.stderr)
        return 2
    if a.n > 0:
        lista = lista[:a.n]
    if a.json:
        print(json.dumps(lista, ensure_ascii=False, indent=2))
    else:
        for i, x in enumerate(lista, 1):
            av = " [amostra pequena]" if x["n"] < N_MIN else ""
            print(f"{i}. {x['modelo']} nota={x['nota']:.2f} n={x['n']} p50={x['p50']} {x['confianca']}/{x['custo']} "
                  f"{x['prompt']} {x['data']}{av}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
