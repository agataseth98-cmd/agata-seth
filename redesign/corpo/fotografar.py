#!/usr/bin/env python3
"""Corpo operacional — fotografia datada da Máquina, só leitura.

Origem: Experimento GPT, conclusões (034)–(036) e `inventario-servicos-agata-2026-11-04.md`;
promove a coleta de `auditoria-2026-11-04/coletar_evidencias.py` a componente.

O que lê (GET e comandos de leitura, nunca POST, nunca reinício, nunca geração):
- `systemctl --user show` das unidades declaradas em UNIDADES;
- portas em escuta (`ss -ltn`);
- Ollama `/api/tags` (instalado) e OmniRoute `/api/models` (anunciado) e `/api/combos` (em fila);
- disco, memória, carga e temperatura (`/proc`, `/sys`, `shutil.disk_usage`).

Para cada modelo ou rota, separa os campos que o inventário pede (§5): instalado, anunciado,
elegível, testado, em fila e pronto. "Testado" e "elegível" só vêm de medição própria
(lote 2) — aqui ficam `null` (não medido), nunca deduzidos do catálogo.

Grava `<dados>/corpo/fotografias.jsonl` (append) e devolve o dicionário.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[0] / "nova_versao"))
import eventos  # noqa: E402

UNIDADES = ("omniroute.service", "omniroute-sanitizer.service", "seth-gateway.service", "seth-escriba.service",
            "seth-verificador.service", "openvino-embeddings.service", "laya-roteador.service",
            "painel-operacional.service", "ollama.service")
OLLAMA = "http://127.0.0.1:11434"
OMNI = "http://127.0.0.1:20128"
REVALIDAR_S = 3600  # inventário datado não é monitor contínuo: depois disso, refotografar


def _cmd(*argv, timeout=10) -> dict:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return {"ok": p.returncode == 0, "saida": p.stdout}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "erro": e.__class__.__name__}


def _get(url: str, timeout=4):
    """Só GET. Devolve (dados, erro)."""
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except Exception as e:  # noqa: BLE001
        return None, f"{e.__class__.__name__} {getattr(e, 'code', '') or ''}".strip()


def servicos(show=None) -> dict:
    r = (show or _cmd)("systemctl", "--user", "show", *UNIDADES, "-p", "Id", "-p", "ActiveState", "-p", "SubState")
    out, atual = {}, {}
    for ln in (r.get("saida") or "").splitlines() + [""]:
        if not ln.strip():
            if atual.get("Id"):
                out[atual["Id"]] = f"{atual.get('ActiveState', '?')}/{atual.get('SubState', '?')}"
            atual = {}
            continue
        k, _, v = ln.partition("=")
        atual[k] = v
    return out


def portas(ss=None) -> list[int]:
    r = (ss or _cmd)("ss", "-ltnH")
    vistas = set()
    for ln in (r.get("saida") or "").splitlines():
        partes = ln.split()
        if len(partes) >= 4 and ":" in partes[3]:
            p = partes[3].rsplit(":", 1)[1]
            if p.isdigit():
                vistas.add(int(p))
    return sorted(vistas)


def recursos() -> dict:
    d = {}
    try:
        u = shutil.disk_usage(str(Path.home()))
        d["disco_livre_pct"] = round(100 * u.free / u.total, 1)
    except OSError:
        d["disco_livre_pct"] = None
    try:
        mem = dict(ln.split(":", 1) for ln in Path("/proc/meminfo").read_text().splitlines() if ":" in ln)
        total = int(mem["MemTotal"].split()[0]); disp = int(mem["MemAvailable"].split()[0])
        d["memoria_disponivel_pct"] = round(100 * disp / total, 1)
    except (OSError, KeyError, ValueError):
        d["memoria_disponivel_pct"] = None
    try:
        d["carga_1min_por_cpu"] = round(os.getloadavg()[0] / (os.cpu_count() or 1), 2)
    except OSError:
        d["carga_1min_por_cpu"] = None
    temps = []
    for z in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            temps.append(int(z.read_text().strip()) / 1000)
        except (OSError, ValueError):
            pass
    d["temperatura_max_c"] = max(temps) if temps else None
    return d


def modelos(get=None) -> dict:
    get = get or _get
    tags, e1 = get(f"{OLLAMA}/api/tags")
    cat, e2 = get(f"{OMNI}/api/models")
    combos, e3 = get(f"{OMNI}/api/combos")
    tab: dict[str, dict] = {}

    def linha(m):
        return tab.setdefault(m, {"instalado": None, "anunciado": None, "elegivel": None, "testado": None,
                                  "em_fila": [], "pronto": None})
    for m in (tags or {}).get("models", []) if tags else []:
        linha("ollama-local/" + m.get("name", "?"))["instalado"] = True
    for m in (cat or {}).get("models", []) if cat else []:
        nome = m.get("fullModel") or m.get("id")
        if nome:
            linha(nome)["anunciado"] = bool(m.get("available"))
    for c in (combos or {}).get("combos", []) if combos else []:
        for el in c.get("models", []):
            nome = el.get("model") if isinstance(el, dict) else el
            if nome:
                linha(nome)["em_fila"].append(c.get("name"))
    erros = {k: v for k, v in (("ollama", e1), ("catalogo", e2), ("combos", e3)) if v}
    return {"tabela": tab, "erros": erros}


def fotografar(gravar: bool = True, **fontes) -> dict:
    agora = time.time()
    foto = {"schema_version": 1, "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(agora)),
            "revalidar_ate": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(agora + REVALIDAR_S)),
            "escopo": "leitura: GET e comandos de estado; sem POST, sem reinício, sem geração",
            "servicos": servicos(fontes.get("show")), "portas": portas(fontes.get("ss")),
            "recursos": fontes.get("recursos") or recursos(), "modelos": modelos(fontes.get("get"))}
    if gravar:
        p = eventos.dados() / "corpo" / "fotografias.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(foto, ensure_ascii=False) + "\n")
    return foto


def ultima() -> dict | None:
    p = eventos.dados() / "corpo" / "fotografias.jsonl"
    try:
        *_, fim = p.read_text(encoding="utf-8").splitlines()
        return json.loads(fim)
    except (OSError, ValueError):
        return None


if __name__ == "__main__":
    f = fotografar()
    print(json.dumps({k: f[k] for k in ("quando", "servicos", "recursos")} | {"modelos": len(f["modelos"]["tabela"]),
                     "erros": f["modelos"]["erros"]}, ensure_ascii=False, indent=1))
