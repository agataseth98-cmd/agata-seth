#!/usr/bin/env python3
"""Conexões de modelos da nova versão — um contrato, três modos.

Decisão do Humano (04/11/2026): Claude e ChatGPT entram como exemplos de conexão, por
todas as vias disponíveis, para futuros usuários ligarem os modelos de sua preferência:

- `navegador`: o Conselho em Rede (relay do painel, já existente). Cada envio exige a
  aprovação do Humano na fila do painel; por isso este módulo NUNCA envia por essa via,
  só informa o estado do adaptador (`relay_catalog.py`).
- `cli`: o programa de linha de comando da assinatura (`claude -p`, `codex exec`),
  rodado em pasta temporária vazia, sem ferramentas e sem sessão persistida.
- `api`: HTTP com chave do cofre (`segredos.py`). Formatos `anthropic` e `openai`
  (este serve para qualquer API compatível com a da OpenAI).

Toda chamada passa por três portas antes de sair: (1) orçamento do painel
(`redesign/nova_versao/orcamento.py`: a categoria precisa estar ligada e dentro do teto);
(2) privacidade: texto com dado pessoal (régua do `sanitizar.py`) não sai para provedor
remoto; (3) custo: modo API só chama com tarifa datada informada pelo Humano, e o gasto
estimado acumulado não passa do teto em R$.

Catálogo: `provedores.json` (repo) + `provedores.local.json` no cofre (provedores que o
usuário acrescentou pelo painel: só API, só https). Ajustes do usuário (modelo, tarifa,
câmbio) ficam em `ajustes.local.json` no cofre. CLI só vem do catálogo versionado:
o painel nunca cadastra comando para executar.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
for _p in (AQUI, REPO / "redesign" / "nova_versao", REPO / "redesign" / "router", REPO / "redesign" / "painel_operacional"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import eventos  # noqa: E402
import orcamento  # noqa: E402
import segredos  # noqa: E402

MODOS = ("navegador", "cli", "api")
FORMATOS = ("anthropic", "openai")
RE_MODELO = re.compile(r"^[A-Za-z0-9._:/@-]{1,80}$")


def _ler_json(p: Path, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar_json(p: Path, dado) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(p.parent, 0o700)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(dado, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def catalogo() -> list[dict]:
    base = _ler_json(AQUI / "provedores.json", {}).get("provedores", [])
    locais = _ler_json(segredos.pasta() / "provedores.local.json", [])
    ids = {p["id"] for p in base}
    out = [dict(p, origem="catalogo") for p in base]
    for p in locais if isinstance(locais, list) else []:
        if isinstance(p, dict) and p.get("id") not in ids:
            out.append({**p, "origem": "local"})
    aj = _ler_json(segredos.pasta() / "ajustes.local.json", {})
    for p in out:
        a = aj.get(p["id"]) or {}
        if p.get("api") and a.get("api_modelo"):
            p["api"] = {**p["api"], "modelo": a["api_modelo"]}
        if p.get("cli") and a.get("cli_modelo"):
            p["cli"] = {**p["cli"], "modelo": a["cli_modelo"]}
        p["tarifa"] = a.get("tarifa")
    return out


def provedor(pid: str) -> dict:
    for p in catalogo():
        if p["id"] == pid:
            return p
    raise ValueError("provedor fora do catálogo")


def adicionar_local(pid: str, nome: str, formato: str, url: str, env: str | None, modelo: str | None) -> dict:
    """Provedor novo pelo painel: só API, só https, sem comando."""
    if not segredos.RE_ID.match(pid or "") or formato not in FORMATOS:
        raise ValueError("id ou formato inválido")
    if not isinstance(url, str) or not re.match(r"^https://[A-Za-z0-9.-]+(:\d+)?(/[\w./%-]*)?$", url):
        raise ValueError("a URL precisa ser https e sem parâmetros")
    if modelo is not None and not RE_MODELO.match(modelo):
        raise ValueError("modelo inválido")
    if env is not None and not re.match(r"^[A-Z][A-Z0-9_]{2,60}$", env):
        raise ValueError("nome de variável inválido")
    if any(p["id"] == pid for p in catalogo()):
        raise ValueError("id já existe")
    nome = str(nome or pid)[:60]
    caminho = segredos.pasta() / "provedores.local.json"
    locais = _ler_json(caminho, [])
    locais.append({"id": pid, "nome": nome, "categoria_orcamento": {"api": "pago"},
                   "api": {"formato": formato, "url": url, "env": env, "prefixo_chave": None, "modelo": modelo}})
    _gravar_json(caminho, locais)
    eventos.registrar("decision", "provedor_adicionado", f"conexao:{pid}", actor="humano-painel", componente="conexoes",
                      formato=formato, url=url)
    return provedor(pid)


def ajustar(pid: str, *, api_modelo=None, cli_modelo=None, tarifa=None) -> dict:
    """Modelo e tarifa escolhidos pelo Humano. Tarifa: USD por milhão de tokens, com fonte e data."""
    provedor(pid)
    for m in (api_modelo, cli_modelo):
        if m is not None and m != "" and not RE_MODELO.match(m):
            raise ValueError("modelo inválido")
    if tarifa is not None:
        if not isinstance(tarifa, dict):
            raise ValueError("tarifa inválida")
        try:
            ent, sai, cambio = float(tarifa["entrada_usd_mtok"]), float(tarifa["saida_usd_mtok"]), float(tarifa["cambio_brl"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("tarifa precisa de entrada, saída e câmbio numéricos") from None
        if not (0 <= ent <= 1000 and 0 <= sai <= 1000 and 0 < cambio <= 100):
            raise ValueError("tarifa fora do limite")
        fonte = str(tarifa.get("fonte") or "")[:200]
        data = str(tarifa.get("data") or "")
        if not fonte or not re.match(r"^\d{4}-\d{2}-\d{2}$", data):
            raise ValueError("tarifa precisa de fonte e data (AAAA-MM-DD)")
        tarifa = {"entrada_usd_mtok": ent, "saida_usd_mtok": sai, "cambio_brl": cambio, "fonte": fonte, "data": data}
    caminho = segredos.pasta() / "ajustes.local.json"
    aj = _ler_json(caminho, {})
    atual = dict(aj.get(pid) or {})
    if api_modelo is not None:
        atual["api_modelo"] = api_modelo or None
    if cli_modelo is not None:
        atual["cli_modelo"] = cli_modelo or None
    if tarifa is not None:
        atual["tarifa"] = tarifa
    aj[pid] = atual
    _gravar_json(caminho, aj)
    eventos.registrar("decision", "ajuste", f"conexao:{pid}", actor="humano-painel", componente="conexoes", depois=atual)
    return provedor(pid)


def _relay_estado(relay_id: str | None):
    try:
        import relay_catalog  # noqa: E402
        p = relay_catalog.PROVIDER_BY_ID.get(relay_id)
        return p.get("adapter_state") if p else None
    except Exception:  # noqa: BLE001
        return None


def estado() -> list[dict]:
    out = []
    for p in catalogo():
        modos = {}
        if p.get("navegador"):
            modos["navegador"] = {"disponivel": False, "adaptador": _relay_estado(p["navegador"].get("relay_id")),
                                  "motivo": "envio só pelo Conselho em Rede, com aprovação do Humano por envio"}
        if p.get("cli"):
            achado = shutil.which(p["cli"]["binario"])
            modos["cli"] = {"disponivel": bool(achado), "instalado": bool(achado), "login": "não medido",
                            "modelo": p["cli"].get("modelo"), "categoria": p["categoria_orcamento"].get("cli")}
        if p.get("api"):
            ch = segredos.estado_de(p["id"], p["api"].get("env"))
            tem = ch["no_cofre"] or ch["no_ambiente"]
            falta = [x for x, ok in (("chave", tem), ("modelo", p["api"].get("modelo")), ("tarifa", p.get("tarifa"))) if not ok]
            modos["api"] = {"disponivel": not falta, "falta": falta, "chave": ch, "modelo": p["api"].get("modelo"),
                            "formato": p["api"]["formato"], "url": p["api"]["url"], "tarifa": p.get("tarifa"),
                            "categoria": p["categoria_orcamento"].get("api")}
        out.append({"id": p["id"], "nome": p["nome"], "origem": p["origem"], "modos": modos})
    return out


def _gasto_path() -> Path:
    return eventos.dados() / "conexoes" / "gasto.jsonl"


def gasto_total_reais() -> float:
    try:
        return round(sum(json.loads(x).get("reais", 0) for x in _gasto_path().read_text().splitlines() if x.strip()), 6)
    except OSError:
        return 0.0


def _privado(texto: str) -> bool:
    try:
        import sanitizar  # noqa: E402
        return bool(sanitizar.varrer_pessoal(texto, sanitizar._nomes_projeto()))
    except Exception:  # noqa: BLE001 — sem a régua, não se arrisca: trata como privado
        return True


def _post(url: str, cabecalhos: dict, corpo: dict, timeout: int):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **cabecalhos})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _chamar_api(p: dict, prompt: str, max_tokens: int, timeout: int, post=None) -> dict:
    api = p["api"]
    chave = segredos._para_chamada(p["id"], api.get("env"))
    if not chave:
        return {"ok": False, "falha_etapa": "configuracao", "erro": "sem chave no cofre nem no ambiente"}
    post = post or _post
    if api["formato"] == "anthropic":
        d = post(api["url"], {"x-api-key": chave, "anthropic-version": "2023-06-01"},
                 {"model": api["modelo"], "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}, timeout)
        texto = "".join(b.get("text", "") for b in d.get("content", []) if isinstance(b, dict))
        u = d.get("usage") or {}
        usage = {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens")}
    else:
        d = post(api["url"], {"Authorization": f"Bearer {chave}"},
                 {"model": api["modelo"], "max_completion_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}, timeout)
        texto = ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        u = d.get("usage") or {}
        usage = {"input_tokens": u.get("prompt_tokens"), "output_tokens": u.get("completion_tokens")}
    return {"ok": True, "texto": texto, "usage": usage, "modelo": d.get("model") or api["modelo"]}


def _chamar_cli(p: dict, prompt: str, timeout: int, rodar=None) -> dict:
    cli = p["cli"]
    rodar = rodar or subprocess.run
    with tempfile.TemporaryDirectory(prefix="agata-cli-") as t:
        saida = os.path.join(t, "ultima.txt")
        argv = [a.replace("{prompt}", prompt).replace("{saida_arquivo}", saida) for a in cli["argv"]]
        if cli.get("modelo") and cli.get("argv_modelo"):
            par = [a.replace("{modelo}", cli["modelo"]) for a in cli["argv_modelo"]]
            argv = argv[:-1] + par + argv[-1:]
        r = rodar(argv, cwd=t, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            return {"ok": False, "falha_etapa": "transporte", "erro": (r.stderr or r.stdout or "").strip()[-200:]}
        usage = {"input_tokens": None, "output_tokens": None}
        if cli.get("saida") == "json_result":
            d = json.loads(r.stdout)
            texto = d.get("result") or ""
            u = d.get("usage") or {}
            usage = {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens")}
        else:
            texto = Path(saida).read_text(encoding="utf-8") if os.path.exists(saida) else r.stdout
    return {"ok": True, "texto": texto.strip(), "usage": usage, "modelo": cli.get("modelo") or "padrão do CLI"}


def chamar(pid: str, modo: str, prompt: str, *, max_tokens: int = 200, chamadas_ja: int = 0, post=None, rodar=None) -> dict:
    """Uma chamada. Nunca levanta por falha do provedor: devolve `ok: False` com a etapa."""
    if modo not in MODOS:
        raise ValueError("modo fora da lista")
    p = provedor(pid)
    base = {"provedor": pid, "modo": modo, "latencia_ms": None, "usage": {"input_tokens": None, "output_tokens": None}}
    if modo == "navegador" or not p.get(modo):
        return {**base, "ok": False, "falha_etapa": "autorizacao",
                "erro": "via navegador só com aprovação do Humano por envio (Conselho em Rede)" if modo == "navegador"
                else "modo não disponível para este provedor"}
    categoria = p["categoria_orcamento"].get(modo)
    ok, motivo = orcamento.permite(categoria, chamadas_ja)
    if not ok:
        return {**base, "ok": False, "falha_etapa": "orcamento", "erro": motivo}
    if _privado(prompt):
        return {**base, "ok": False, "falha_etapa": "privacidade", "erro": "dado pessoal não sai para provedor remoto"}
    o = orcamento.ler()
    if modo == "api":
        if not p["api"].get("modelo"):
            return {**base, "ok": False, "falha_etapa": "configuracao", "erro": "modelo da API não escolhido"}
        if not p.get("tarifa"):
            return {**base, "ok": False, "falha_etapa": "custo", "erro": "sem tarifa datada: custo não estimável"}
        t = p["tarifa"]
        teto_chamada = (len(prompt) / 3 * t["entrada_usd_mtok"] + max_tokens * t["saida_usd_mtok"]) / 1e6 * t["cambio_brl"]
        if gasto_total_reais() + teto_chamada > o["teto_reais"]:
            return {**base, "ok": False, "falha_etapa": "custo", "erro": "teto em R$ seria ultrapassado"}
    t0 = time.monotonic()
    try:
        r = _chamar_api(p, prompt, max_tokens, o["timeout_s"], post) if modo == "api" else _chamar_cli(p, prompt, o["timeout_s"], rodar)
    except (urllib.error.URLError, OSError, ValueError, subprocess.TimeoutExpired, KeyError) as e:
        r = {"ok": False, "falha_etapa": "transporte", "erro": f"{e.__class__.__name__}: {str(e)[:160]}"}
    r = {**base, **r, "latencia_ms": round((time.monotonic() - t0) * 1000)}
    if modo == "api" and r.get("ok"):
        t = p["tarifa"]; u = r["usage"]
        reais = ((u.get("input_tokens") or 0) * t["entrada_usd_mtok"] + (u.get("output_tokens") or 0) * t["saida_usd_mtok"]) / 1e6 * t["cambio_brl"]
        r["reais_estimado"] = round(reais, 6)
        _gasto_path().parent.mkdir(parents=True, exist_ok=True)
        with open(_gasto_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "provedor": pid, "reais": r["reais_estimado"],
                                "usage": u, "tarifa_fonte": t["fonte"], "tarifa_data": t["data"]}) + "\n")
    return r


if __name__ == "__main__":
    print(json.dumps(estado(), ensure_ascii=False, indent=1))
