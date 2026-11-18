#!/usr/bin/env python3
"""Configurar modelos pela linha de comando: `listar` e `adicionar`.

Decisão do Humano (17/11/2026): "todos os modelos, inclusive os pagos, devem ser usados por
dentro do sistema Agata obedecendo as mesmas regras, e deve ser fácil configurar".

- `listar`: provedores do catálogo e do cofre local, com o endpoint e se a chave existe.
  A chave é checada só pelo NOME da variável (`segredos.estado_de`); nenhum valor é lido.
- `adicionar`: acrescenta ao `provedores.json` um bloco só de API (sem `cli` e sem
  `navegador`: comando nunca entra por aqui). Recusa id repetido, endpoint com esquema, host
  ou porta inválidos (fora do gateway local), `--chave-env` que não seja nome de variável e
  argumento desconhecido. Nenhuma mensagem de erro repete o valor recusado.
  A leitura, a checagem de id, a gravação do catálogo e a tarifa ficam sob a mesma trava
  (`flock` no cofre), para que duas adições não se percam. Com `--tarifa-*`, a tarifa é
  gravada por `adaptadores.ajustar`, o mesmo caminho do painel; se qualquer passo falhar, o
  o catálogo volta e só a tarifa deste id sai de ajustes, ainda sob a trava.

Regra mecânica do nome de chave: maiúsculas, dígitos e `_`; bloco longo sem `_` é tratado
como chave crua. Todo modelo adicionado sai por `adaptadores.chamar()`: orçamento,
privacidade, custo e cofre valem igual para todos. O endpoint muda só o destino.

Uso:
  configurar.py listar [--json]
  configurar.py adicionar --id ID --base-url URL --chave-env NOME --modelos a,b
                          [--formato openai|anthropic] [--nome NOME]
                          [--tarifa-entrada USD --tarifa-saida USD --cambio BRL
                           --tarifa-fonte TEXTO --tarifa-data AAAA-MM-DD]
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import json
import math
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
for _p in (AQUI, REPO / "redesign" / "nova_versao"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import adaptadores  # noqa: E402
import eventos  # noqa: E402
import orcamento  # noqa: E402
import segredos  # noqa: E402

CATALOGO = AQUI / "provedores.json"
SUFIXO = {"openai": "/chat/completions", "anthropic": "/messages"}
# Casam com fullmatch. Host: rótulos DNS (sem ponto vazio, sem hífen na borda); porta: 1-65535 (checada à parte).
RE_HTTPS = re.compile(r"https://([A-Za-z0-9.-]+)(?::(\d+))?(/[\w./%-]*)?")
RE_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?")
# Gateway local: :20127 é o sanitizador (à frente); :20128 é o OmniRoute direto.
RE_GATEWAY = re.compile(r"http://127\.0\.0\.1:(?:20127|20128)(?:/[\w./%-]*)?")
RE_NOME_VAR = re.compile(r"[A-Z][A-Z0-9_]{2,60}")
RE_DATA = re.compile(r"\d{4}-\d{2}-\d{2}")
LOCK_NOME = "provedores.lock"
MAX_MODELOS = 10
MSG_URL = ("--base-url precisa ser https (provedor direto) ou o gateway local http://127.0.0.1:20127 "
           "(sanitizador) ou http://127.0.0.1:20128 (OmniRoute); sem usuário, senha, parâmetros, "
           "e com host e porta válidos.")
MSG_CHAVE = ("--chave-env recebe o NOME da variável de ambiente (ex.: OPENAI_API_KEY), nunca a chave. "
             "A chave é gravada pelo painel (aba Conexões) ou exportada no ambiente; o catálogo não guarda segredo.")
MSG_TARIFA = ("tarifa: --tarifa-entrada, --tarifa-saida, --cambio, --tarifa-fonte e --tarifa-data vão juntos "
              "(US$ por milhão de tokens, R$ por US$, fonte e data AAAA-MM-DD)")


class _Parser(argparse.ArgumentParser):
    """argparse repete o argumento desconhecido e o valor inválido na mensagem de erro. Aqui o erro
    sai só com o uso, sem repetir nenhum valor digitado (um segredo colado no lugar errado não vaza)."""

    def error(self, message: str):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: erro: argumentos inválidos (valores não são repetidos); veja o uso acima\n")
        raise SystemExit(2)


def _url_permitida(url: str) -> bool:
    if RE_GATEWAY.fullmatch(url):
        return True
    m = RE_HTTPS.fullmatch(url)
    if not m:
        return False
    host, porta = m.group(1), m.group(2)
    if len(host) > 253 or not all(RE_LABEL.fullmatch(rotulo) for rotulo in host.split(".")):
        return False
    return porta is None or 1 <= int(porta) <= 65535


def _modelo_ok(m) -> bool:
    return isinstance(m, str) and bool(adaptadores.RE_MODELO.match(m))


def validar_nome_var(nome) -> str:
    """Só nome de variável. Recusa o que tem cara de chave: minúsculas, pontuação, espaço, ou
    bloco longo sem `_` (chave crua em maiúsculas)."""
    if not isinstance(nome, str) or not RE_NOME_VAR.fullmatch(nome) or ("_" not in nome and len(nome) > 20):
        raise ValueError(MSG_CHAVE)
    return nome


def endereco(base_url, formato: str) -> str:
    """Endpoint de chat a partir da base (…/v1). Se a base já traz o sufixo, não duplica."""
    if formato not in adaptadores.FORMATOS:
        raise ValueError("formato inválido: use openai ou anthropic")
    if not isinstance(base_url, str):
        raise ValueError(MSG_URL)
    base = base_url.strip().rstrip("/")
    url = base if base.endswith(SUFIXO[formato]) else base + SUFIXO[formato]
    if not _url_permitida(url):
        raise ValueError(MSG_URL)
    return url


def modelos_de(texto) -> list[str]:
    if not isinstance(texto, str):
        raise ValueError("--modelos recebe uma lista separada por vírgula")
    itens = [m.strip() for m in texto.split(",") if m.strip()]
    if not itens or len(itens) > MAX_MODELOS:
        raise ValueError(f"--modelos precisa de 1 a {MAX_MODELOS} modelos, separados por vírgula")
    if not all(_modelo_ok(m) for m in itens):
        raise ValueError("modelo com caractere inválido: use letras, números e . _ : / @ -")
    if len(set(itens)) != len(itens):
        raise ValueError("modelo repetido em --modelos")
    return itens


def _numero(valor, nome: str, lo: float, hi: float, aberto: bool = False) -> float:
    if isinstance(valor, str):
        valor = valor.strip().replace(",", ".")
    try:
        x = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{nome} precisa ser um número") from None
    dentro = (lo < x if aberto else lo <= x) and x <= hi
    if not math.isfinite(x) or not dentro:
        raise ValueError(f"{nome} fora do limite")
    return x


def _tarifa(entrada, saida, cambio, fonte, data) -> dict | None:
    """Mesmas regras de `adaptadores.ajustar`, validadas antes de qualquer gravação."""
    campos = (entrada, saida, cambio, fonte, data)
    if all(c is None for c in campos):
        return None
    if any(c is None for c in campos):
        raise ValueError(MSG_TARIFA)
    ent = _numero(entrada, "--tarifa-entrada", 0, 1000)
    sai = _numero(saida, "--tarifa-saida", 0, 1000)
    cb = _numero(cambio, "--cambio", 0, 100, aberto=True)
    fonte_txt = str(fonte).strip()
    if not fonte_txt or len(fonte_txt) > 200:
        raise ValueError("--tarifa-fonte precisa de texto, até 200 caracteres")
    data_txt = str(data).strip()
    if not RE_DATA.fullmatch(data_txt):
        raise ValueError("--tarifa-data precisa ser AAAA-MM-DD")
    try:
        datetime.datetime.strptime(data_txt, "%Y-%m-%d")
    except ValueError:
        raise ValueError("--tarifa-data precisa ser uma data real (AAAA-MM-DD)") from None
    return {"entrada_usd_mtok": ent, "saida_usd_mtok": sai, "cambio_brl": cb, "fonte": fonte_txt, "data": data_txt}


def _validar_api(api, pid: str) -> None:
    erro = f"provedor {pid}: bloco api fora do schema"
    if not isinstance(api, dict) or api.get("formato") not in adaptadores.FORMATOS:
        raise ValueError(erro + " (formato)")
    if not isinstance(api.get("url"), str) or not _url_permitida(api["url"]):
        raise ValueError(erro + " (url)")
    env = api.get("env")
    if env is not None and (not isinstance(env, str) or not RE_NOME_VAR.fullmatch(env)):
        raise ValueError(erro + " (env deve ser nome de variável)")
    if api.get("prefixo_chave") is not None and not isinstance(api.get("prefixo_chave"), str):
        raise ValueError(erro + " (prefixo_chave)")
    if api.get("modelo") is not None and not _modelo_ok(api.get("modelo")):
        raise ValueError(erro + " (modelo)")
    mods = api.get("modelos")
    if mods is not None and (not isinstance(mods, list) or not mods or not all(_modelo_ok(m) for m in mods)):
        raise ValueError(erro + " (modelos)")


def validar_provedor(p) -> dict:
    if not isinstance(p, dict):
        raise ValueError("provedor fora do schema: não é objeto")
    pid = p.get("id")
    if not isinstance(pid, str) or not segredos.RE_ID.fullmatch(pid):
        raise ValueError("id de provedor inválido")
    if not isinstance(p.get("nome"), str) or not p["nome"]:
        raise ValueError(f"provedor {pid}: falta nome")
    cat = p.get("categoria_orcamento")
    if not isinstance(cat, dict) or not cat or set(cat) - {"api", "cli"} or any(v not in orcamento.PROVEDORES for v in cat.values()):
        raise ValueError(f"provedor {pid}: categoria_orcamento fora do schema")
    if not any(p.get(k) for k in ("navegador", "cli", "api")):
        raise ValueError(f"provedor {pid}: sem caminho (navegador, cli ou api)")
    if p.get("navegador") is not None and not isinstance(p["navegador"], dict):
        raise ValueError(f"provedor {pid}: navegador fora do schema")
    if p.get("cli") is not None and not isinstance(p["cli"], dict):
        raise ValueError(f"provedor {pid}: cli fora do schema")
    if p.get("api") is not None:
        _validar_api(p["api"], pid)
    return p


def validar_catalogo(d) -> dict:
    if not isinstance(d, dict) or d.get("schema_version") != 1 or not isinstance(d.get("provedores"), list):
        raise ValueError("catálogo fora do schema 1 (falta schema_version 1 ou provedores)")
    for p in d["provedores"]:
        validar_provedor(p)
    ids = [p["id"] for p in d["provedores"]]
    if len(set(ids)) != len(ids):
        raise ValueError("id repetido no catálogo")
    return d


def ler(caminho: Path | None = None) -> dict:
    caminho = CATALOGO if caminho is None else caminho
    try:
        d = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"catálogo ilegível: {caminho.name}") from e
    return validar_catalogo(d)


def _locais() -> list[dict]:
    """Provedores que o painel acrescentou (cofre). Ilegível vira erro: senão o id repetido passaria."""
    caminho = segredos.pasta() / "provedores.local.json"
    if not caminho.exists():
        return []
    try:
        d = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError("provedores.local.json ilegível: não dá para checar id repetido") from e
    if not isinstance(d, list):
        raise ValueError("provedores.local.json fora do schema")
    return [validar_provedor(p) for p in d]


def listar() -> list[dict]:
    base = ler()["provedores"]
    ids = {p["id"] for p in base}
    todos = [(p, "catalogo") for p in base] + [(p, "local") for p in _locais() if p["id"] not in ids]
    out = []
    for p, origem in todos:
        api = p.get("api") or {}
        modelos = api.get("modelos") or ([api["modelo"]] if api.get("modelo") else [])
        item = {"id": p["id"], "nome": p["nome"], "origem": origem,
                "modos": [m for m in ("navegador", "cli", "api") if p.get(m)],
                "endpoint": api.get("url"), "modelos": modelos,
                "chave_env": api.get("env"), "chave": None}
        if api:
            st = segredos.estado_de(p["id"], api.get("env"))
            item["chave"] = {"no_cofre": st["no_cofre"], "no_ambiente": st["no_ambiente"]}
        out.append(item)
    return out


@contextlib.contextmanager
def _trava():
    """Trava exclusiva (flock) sobre ler, checar id e gravar o catálogo. Fica no cofre (0700, fora do
    repo): `*.lock` não é ignorado no repositório, e a trava não deve virar arquivo rastreável."""
    pasta = segredos.pasta()
    pasta.mkdir(parents=True, exist_ok=True)
    os.chmod(pasta, 0o700)
    fd = os.open(pasta / LOCK_NOME, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _gravar(caminho: Path, dado: dict) -> None:
    modo = caminho.stat().st_mode & 0o777
    fd, tmp = tempfile.mkstemp(dir=caminho.parent, prefix=".tmp-provedores-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            os.fchmod(f.fileno(), modo)
            f.write(json.dumps(dado, ensure_ascii=False, indent=2) + "\n")
        os.replace(tmp, caminho)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _ajustes_arquivo() -> Path:
    """O mesmo arquivo que `adaptadores.ajustar` escreve."""
    return segredos.pasta() / "ajustes.local.json"


def _ler_ajustes() -> dict | None:
    """ajustes.local.json como dict; None se o arquivo não existe. Ilegível conta como vazio,
    como em adaptadores._ler_json."""
    p = _ajustes_arquivo()
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _snapshot_tarifa(pid: str) -> dict:
    """O que havia em ajustes para o id antes da tarifa: se o arquivo existia, o modo dele e o valor da chave."""
    aj = _ler_ajustes()
    modo = stat.S_IMODE(_ajustes_arquivo().stat().st_mode) if aj is not None else None
    return {"arquivo": aj is not None, "modo": modo, "tinha": pid in (aj or {}), "valor": (aj or {}).get(pid)}


def _desfazer_tarifa(pid: str, snap: dict) -> None:
    """Desfaz só a chave do id adicionado. Relê o arquivo atual, para não apagar o que o painel
    gravou depois (outros ids). Remove o arquivo só se ficar vazio e ele não existia antes."""
    p = _ajustes_arquivo()
    aj = _ler_ajustes() or {}
    if snap["tinha"]:
        aj[pid] = snap["valor"]
    else:
        aj.pop(pid, None)
    if not aj and not snap["arquivo"]:
        if p.exists():
            p.unlink()
        return
    modo = snap["modo"] if snap["arquivo"] else 0o600   # adaptadores.ajustar regrava com 0600
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".tmp-ajustes-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            os.fchmod(f.fileno(), modo)
            f.write(json.dumps(aj, ensure_ascii=False, indent=1))
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def adicionar(pid, base_url, chave_env, modelos, *, formato: str = "openai", nome=None,
              tarifa_entrada=None, tarifa_saida=None, cambio=None, tarifa_fonte=None, tarifa_data=None,
              actor: str = "humano-cli") -> dict:
    """Acrescenta o provedor ao catálogo versionado. Com tarifa, grava também em ajustes (via
    `adaptadores.ajustar`, que lê o catálogo de `adaptadores.AQUI`). Tudo é validado antes de gravar.
    Catálogo, tarifa e registro de evento saem sob a mesma trava; se qualquer passo falhar depois da
    primeira gravação, o catálogo volta e, em ajustes, só a chave deste id é desfeita (o ledger é append-only e guarda
    o que foi tentado)."""
    if not isinstance(pid, str) or not segredos.RE_ID.fullmatch(pid):
        raise ValueError("id inválido: minúsculas, números, _ ou -, de 2 a 41 caracteres")
    url = endereco(base_url, formato)
    env = validar_nome_var(chave_env)
    mods = modelos_de(modelos)
    tarifa = _tarifa(tarifa_entrada, tarifa_saida, cambio, tarifa_fonte, tarifa_data)
    with _trava():
        doc = ler()
        ocupados = {p["id"] for p in doc["provedores"]} | {p["id"] for p in _locais()}
        if pid in ocupados:
            raise ValueError("id já existe no catálogo ou nos provedores locais")
        bloco = {"id": pid, "nome": str(nome or pid)[:60], "categoria_orcamento": {"api": "pago"},
                 "api": {"formato": formato, "url": url, "env": env, "prefixo_chave": None,
                         "modelo": mods[0], "modelos": mods}}
        novo = {**doc, "provedores": [*doc["provedores"], bloco]}
        validar_catalogo(novo)
        snap_tarifa = _snapshot_tarifa(pid) if tarifa is not None else None
        try:
            _gravar(CATALOGO, novo)
            if tarifa is not None:
                adaptadores.ajustar(pid, tarifa=tarifa)
            eventos.registrar("decision", "provedor_adicionado", f"conexao:{pid}", actor=actor,
                              componente="conexoes", formato=formato, url=url, modelos=len(mods),
                              tarifa=tarifa is not None)
        except BaseException:
            _gravar(CATALOGO, doc)               # ainda sob a trava: desfaz o provedor
            if tarifa is not None:
                _desfazer_tarifa(pid, snap_tarifa)  # só a chave deste id; o resto é do painel
            raise
    return bloco


def _chave_txt(i: dict) -> str:
    c = i["chave"]
    if c is None:
        return "-"
    if c["no_cofre"]:
        return "no cofre"
    if c["no_ambiente"]:
        return f"variável {i['chave_env']}"
    return "ausente"


def main(argv=None) -> int:
    ap = _Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="comando", required=True)
    li = sub.add_parser("listar", help="provedores, endpoint e se a chave existe (só pelo nome)")
    li.add_argument("--json", action="store_true")
    ad = sub.add_parser("adicionar", help="acrescenta um provedor de API ao catálogo")
    ad.add_argument("--id", required=True)
    ad.add_argument("--base-url", required=True, help="https do provedor, ou http://127.0.0.1:20127/v1 (gateway)")
    ad.add_argument("--chave-env", required=True, help="NOME da variável (ex.: OPENAI_API_KEY), nunca a chave")
    ad.add_argument("--modelos", required=True, help="a,b (o primeiro é o padrão)")
    ad.add_argument("--formato", default="openai", choices=adaptadores.FORMATOS)
    ad.add_argument("--nome")
    ad.add_argument("--tarifa-entrada", help="US$ por milhão de tokens de entrada")
    ad.add_argument("--tarifa-saida", help="US$ por milhão de tokens de saída")
    ad.add_argument("--cambio", help="R$ por US$")
    ad.add_argument("--tarifa-fonte", help="página oficial de preços (até 200 caracteres)")
    ad.add_argument("--tarifa-data", help="data em que você conferiu a tarifa (AAAA-MM-DD)")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0)
    try:
        if a.comando == "listar":
            itens = listar()
            if a.json:
                print(json.dumps(itens, ensure_ascii=False, indent=1))
            else:
                for i in itens:
                    print(f"{i['id']:<14} {i['origem']:<9} {','.join(i['modos']):<22} "
                          f"chave: {_chave_txt(i):<26} {i['endpoint'] or '-'}")
            return 0
        bloco = adicionar(a.id, a.base_url, a.chave_env, a.modelos, formato=a.formato, nome=a.nome,
                          tarifa_entrada=a.tarifa_entrada, tarifa_saida=a.tarifa_saida, cambio=a.cambio,
                          tarifa_fonte=a.tarifa_fonte, tarifa_data=a.tarifa_data)
    except ValueError as e:
        print(f"recusado: {e}", file=sys.stderr)
        return 2
    estado = segredos.estado_de(bloco["id"], bloco["api"]["env"])
    chave = "no cofre" if estado["no_cofre"] else (f"variável {bloco['api']['env']} presente" if estado["no_ambiente"]
                                                  else f"ausente: grave a chave pelo painel ou exporte {bloco['api']['env']}")
    if a.tarifa_entrada is not None:
        tarifa = f"tarifa gravada (fonte {a.tarifa_fonte.strip()}, data {a.tarifa_data.strip()})"
    else:
        tarifa = "sem tarifa: a chamada é recusada (custo) até você definir a tarifa na aba Conexões do painel"
    print(f"adicionado: {bloco['id']} · endpoint {bloco['api']['url']} · modelos {', '.join(bloco['api']['modelos'])}"
          f" · chave: {chave} · {tarifa} · pago: ligue a categoria no painel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
