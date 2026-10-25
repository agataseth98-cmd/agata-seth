#!/usr/bin/env python3
"""Capivara — registro de capacidades dos modelos das filas (roteamento por capacidade, passo 1).

V9, seção 35; desenho em "Área de trabalho/DESENHO_roteamento_por_capacidade_rascunho.md",
seções 3 e 8. Grava `config/capivara/capacidades.json`. Não muda rota nenhuma: o gateway
não lê este arquivo. Lê fatos, nunca escreve canon.

Cada modelo tem quatro camadas, nunca fundidas num "capaz = sim":
- `catalogo`  — o que o OmniRoute lista em `/v1/models` (provedor, id resolvido, janela,
                modalidades, ferramentas, raciocínio), com a data da leitura;
- `declarado` — o que a documentação OFICIAL do provedor diz
                (`config/capivara/janelas-documentadas.json`), com fonte e data;
- `medido`    — ensaios locais, um registro por medição, com proveniência completa
                (vazio até existir protocolo versionado: passo 2);
- `observado` — produção ou sombra (vazio até o passo 4).
Ao regenerar, `medido` e `observado` são preservados: medição não se descarta.

Uso:
  capivara_capacidades.py              lê o catálogo (só leitura) e grava o registro
  capivara_capacidades.py --conferir   valida o registro gravado (saída 1 se inválido)
  capivara_capacidades.py --selftest
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / "config" / "capivara" / "capacidades.json"
DOCUMENTADAS = RAIZ / "config" / "capivara" / "janelas-documentadas.json"
FILAS = ("seth-rapido", "seth-livre", "seth-pesado", "seth-codigo")
CAMADAS = ("catalogo", "declarado", "medido", "observado")
# Proveniência mínima de toda medição ou observação (desenho, seção 8).
PROVENIENCIA = ("metrica", "valor", "protocolo", "amostra", "provedor", "endpoint",
                "versao_resolvida", "data")
PROIBIDAS = ("capaz", "capable")  # veredito fundido, sem camada nem prova


# --- montagem (pura, sem rede) ------------------------------------------------------
def camada_catalogo(item: dict | None, lido_em: str) -> dict | None:
    if not item:
        return None
    cap = item.get("capabilities") or {}
    return {"fonte": "omniroute /v1/models", "lido_em": lido_em,
            "provedor": item.get("owned_by"), "id_resolvido": item.get("root"),
            "janela": item.get("context_length") or item.get("max_input_tokens"),
            "saida_max": item.get("max_output_tokens"),
            "entrada": item.get("input_modalities"), "saida": item.get("output_modalities"),
            "ferramentas": cap.get("tool_calling"), "raciocinio": cap.get("reasoning"),
            "gratis": item.get("free")}


def camada_declarado(doc: dict | None) -> dict | None:
    if not doc:
        return None
    return {"fonte": doc["fonte"], "janela": doc.get("janela"), "saida_max": doc.get("saida_max")}


def montar(filas: dict, catalogo: dict, documentadas: dict, anterior: dict, lido_em: str) -> dict:
    velhos = anterior.get("modelos") or {}
    modelos = {}
    for m in sorted({x for ordem in filas.values() for x in ordem}):
        v = velhos.get(m) or {}
        modelos[m] = {"catalogo": camada_catalogo(catalogo.get(m), lido_em),
                      "declarado": camada_declarado(documentadas.get(m)),
                      "medido": list(v.get("medido") or []),
                      "observado": list(v.get("observado") or [])}
    # Modelo que saiu das filas mas tem medição: fica, marcado, para não perder o dado.
    for m, v in velhos.items():
        if m not in modelos and (v.get("medido") or v.get("observado")):
            modelos[m] = {"catalogo": None, "declarado": None, "medido": [], "observado": [],
                          **v, "fora_das_filas": True}
    return {"_como_usar": "Gerado por scripts/capivara_capacidades.py. Não muda rota: o gateway não "
                          "lê este arquivo. `medido` e `observado` só recebem registros com "
                          "proveniência completa (" + ", ".join(PROVENIENCIA) + ").",
            "gerado_em": lido_em, "filas": filas, "modelos": modelos}


def conferir(reg: dict) -> list[str]:
    erros = []
    modelos = reg.get("modelos")
    if not isinstance(modelos, dict) or not modelos:
        return ["registro sem modelos"]
    for m, v in modelos.items():
        if not isinstance(v, dict):
            erros.append(f"{m}: entrada não é objeto")
            continue
        for k in v:
            if k.lower() in PROIBIDAS:
                erros.append(f"{m}: campo '{k}' funde as camadas (proibido)")
        for c in CAMADAS:
            if c not in v:
                erros.append(f"{m}: falta a camada '{c}'")
        for c in ("medido", "observado"):
            regs = v.get(c)
            if not isinstance(regs, list):
                erros.append(f"{m}.{c}: deveria ser lista")
                continue
            for i, r in enumerate(regs):
                faltam = [p for p in PROVENIENCIA if not isinstance(r, dict) or r.get(p) in (None, "")]
                if faltam:
                    erros.append(f"{m}.{c}[{i}]: falta proveniência ({', '.join(faltam)})")
                elif not (isinstance(r["amostra"], int) and r["amostra"] >= 1):
                    erros.append(f"{m}.{c}[{i}]: amostra deve ser inteiro >= 1")
    return erros


def carregar(caminho: Path = REGISTRO) -> dict:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# --- leitura (rede, só leitura) -------------------------------------------------------
def ler_catalogo() -> tuple[dict, dict]:
    sys.path.insert(0, str(RAIZ / "scripts"))
    import urllib.request
    import queda_por_elo as q  # noqa: E402  (filas, token interno, abridor sem proxy)
    filas = q.ler_filas(quais=FILAS)
    req = urllib.request.Request(q.PROXY + "/v1/models", headers={"X-Agata-Token": q._token_interno()})
    with q._SEM_PROXY.open(req, timeout=30) as r:
        dados = json.load(r)
    cat = {m["id"]: m for m in dados.get("data", []) if isinstance(m, dict) and m.get("id")}
    return filas, cat


def _selftest() -> int:
    filas = {"seth-rapido": ["a/x", "ollama-local/y"], "seth-codigo": ["a/x", "b/z"]}
    cat = {"a/x": {"owned_by": "a", "root": "x-2026", "context_length": 256000, "max_output_tokens": 64000,
                   "input_modalities": ["text"], "output_modalities": ["text"],
                   "capabilities": {"tool_calling": True, "reasoning": False}, "free": True}}
    doc = {"b/z": {"janela": 128000, "fonte": "https://exemplo/doc (lido em 13/10/2026)"}}
    med = {"metrica": "sucesso_ferramenta", "valor": 0.9, "protocolo": "p1", "amostra": 30,
           "provedor": "a", "endpoint": "a/x", "versao_resolvida": "x-2026", "data": "2026-10-23"}
    ant = {"modelos": {"a/x": {"medido": [med]}, "velho/w": {"medido": [med]}, "velho/v": {}}}
    r = montar(filas, cat, doc, ant, "2026-10-23 13:50 -0300")
    m = r["modelos"]
    ruim = json.loads(json.dumps(r))
    ruim["modelos"]["a/x"]["medido"].append({"metrica": "x", "valor": 1})
    ruim["modelos"]["b/z"]["capaz"] = True
    sem_amostra = json.loads(json.dumps(r))
    sem_amostra["modelos"]["a/x"]["medido"][0]["amostra"] = 0
    casos = [
        ("todo modelo das filas entra, uma vez", {"a/x", "b/z", "ollama-local/y"} <= set(m)),
        ("catálogo traz ferramentas e id resolvido", m["a/x"]["catalogo"]["ferramentas"] is True
         and m["a/x"]["catalogo"]["id_resolvido"] == "x-2026"),
        ("sem catálogo -> camada None, não 'falso'", m["b/z"]["catalogo"] is None),
        ("declarado vem só da documentação, com fonte", m["b/z"]["declarado"]["fonte"].startswith("https://")
         and m["a/x"]["declarado"] is None),
        ("medição anterior é preservada", m["a/x"]["medido"] == [med]),
        ("modelo fora das filas com medição fica, marcado", m["velho/w"].get("fora_das_filas") is True),
        ("modelo fora das filas sem medição sai", "velho/v" not in m),
        ("registro montado passa na conferência", conferir(r) == []),
        ("medição sem proveniência é recusada", any("falta proveniência" in e for e in conferir(ruim))),
        ("campo 'capaz' é recusado", any("funde as camadas" in e for e in conferir(ruim))),
        ("amostra < 1 é recusada", any("amostra" in e for e in conferir(sem_amostra))),
        ("registro vazio é inválido", conferir({}) != []),
        ("registro ausente -> {}", carregar(Path("/nao/existe.json")) == {}),
    ]
    reg2 = montar(filas, cat, doc, {}, "2026-10-24 20:00 -0300")
    res2 = {"a/x": {"medido": [dict(med, metrica="taxa_erro", valor=0.0)]}}
    rots = [{"rodada": "R1", "modelo": "a/x", "item": "cod-01", "rotulo": "boa"},
            {"rodada": "R1", "modelo": "a/x", "item": "cod-02", "rotulo": "parcial"},
            {"rodada": "R1", "modelo": "a/x", "item": "fer-01", "rotulo": "ruim_grave"},
            {"rodada": "R2", "modelo": "a/x", "item": "cod-03", "rotulo": "ruim"}]
    n1 = incorporar(reg2, "R1", res2, rots)
    n2 = incorporar(reg2, "R1", res2, rots)
    med2 = {x["metrica"]: x for x in reg2["modelos"]["a/x"]["medido"]}
    casos += [
        ("incorporar: qualidade por tipo (boa=1, parcial=0,5)", med2.get("qualidade_codigo", {}).get("valor") == 0.75
         and med2["qualidade_codigo"]["amostra"] == 2 and med2.get("qualidade_ferramenta", {}).get("valor") == 0.0),
        ("incorporar: só os rótulos da rodada pedida", med2["qualidade_codigo"]["amostra"] == 2),
        ("incorporar: não duplica na 2ª vez", n1 > 0 and n2 == 0),
        ("incorporar: registro continua válido", conferir(reg2) == []),
    ]
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


TIPO_POR_PREFIXO = {"cod": "codigo", "fer": "ferramenta", "json": "json", "longo": "contexto_longo", "conv": "conversa"}
PESO_ROTULO = {"boa": 1.0, "parcial": 0.5, "ruim": 0.0, "ruim_grave": 0.0}


def incorporar(reg: dict, rodada: str, resumo: dict, rotulos: list[dict]) -> int:
    """Leva para `medido` as medidas mecânicas do `resumo.json` de uma rodada do benchmark e
    a qualidade por tipo de tarefa tirada dos rótulos daquela rodada (boa=1, parcial=0,5,
    ruim=0). Só modelos já no registro; o que já está (mesmo protocolo e métrica) não duplica."""
    novos = 0
    for modelo, v in (reg.get("modelos") or {}).items():
        r = resumo.get(modelo)
        if not r:
            continue
        base = dict(r["medido"][0]) if r.get("medido") else None
        if base is None:
            continue
        registros = [dict(x, protocolo=f"{x['protocolo']} rodada:{rodada}") for x in r["medido"]]
        por_tipo: dict = {}
        for rot in rotulos:
            if rot.get("rodada") == rodada and rot.get("modelo") == modelo and rot.get("rotulo") in PESO_ROTULO:
                tipo = TIPO_POR_PREFIXO.get(rot["item"].split("-")[0])
                if tipo:
                    por_tipo.setdefault(tipo, []).append(PESO_ROTULO[rot["rotulo"]])
        for tipo, ps in sorted(por_tipo.items()):
            registros.append({"protocolo": f"{base['protocolo']} rodada:{rodada} rotulo-humano-ou-criterio",
                              "provedor": base["provedor"], "endpoint": base["endpoint"],
                              "versao_resolvida": base["versao_resolvida"], "data": base["data"],
                              "metrica": f"qualidade_{tipo}", "valor": round(sum(ps) / len(ps), 3), "amostra": len(ps)})
        ja = {(x.get("protocolo"), x.get("metrica")) for x in v.get("medido") or []}
        for x in registros:
            if (x["protocolo"], x["metrica"]) not in ja:
                v.setdefault("medido", []).append(x)
                novos += 1
    return novos


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    if argv[:1] == ["--incorporar"] and len(argv) >= 2:
        # --incorporar DIR_DA_RODADA [...]: lê DIR/resumo.json e ../rotulos.jsonl (fora do repositório)
        reg = carregar()
        total = 0
        for d in argv[1:]:
            pasta = Path(d)
            rotulos_arq = pasta.parent / "rotulos.jsonl"
            rotulos = [json.loads(l) for l in rotulos_arq.read_text(encoding="utf-8").splitlines() if l.strip()] \
                if rotulos_arq.exists() else []
            total += incorporar(reg, pasta.name, json.loads((pasta / "resumo.json").read_text(encoding="utf-8")),
                                rotulos)
        erros = conferir(reg)
        if erros:
            print("INVÁLIDO, nada gravado:\n  " + "\n  ".join(erros))
            return 1
        REGISTRO.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"incorporadas {total} medidas novas")
        return 0
    if argv == ["--conferir"]:
        erros = conferir(carregar())
        print("OK: registro válido" if not erros else "INVÁLIDO:\n  " + "\n  ".join(erros))
        return 1 if erros else 0
    if argv:
        print(__doc__)
        return 2
    filas, cat = ler_catalogo()
    doc = json.loads(DOCUMENTADAS.read_text(encoding="utf-8")).get("modelos", {})
    reg = montar(filas, cat, doc, carregar(), time.strftime("%Y-%m-%d %H:%M %z"))
    erros = conferir(reg)
    if erros:
        print("INVÁLIDO, nada gravado:\n  " + "\n  ".join(erros))
        return 1
    REGISTRO.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for m, v in reg["modelos"].items():
        c = v["catalogo"] or {}
        print(f"{m:55} janela={str(c.get('janela')):>8} ferramentas={c.get('ferramentas')} "
              f"declarado={'sim' if v['declarado'] else 'não'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
