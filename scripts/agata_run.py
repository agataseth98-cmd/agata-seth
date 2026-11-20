#!/usr/bin/env python3
"""agata-run: lancador unico das plataformas (Claude Code, Codex, OpenCode, Gemini).

Fase 2 do sandbox. Aplica contencao Landlock (allow-only) ao proprio processo e
faz exec da plataforma: o lancador nao fica como pai, o filho herda a restricao
e nao a desfaz. Hidratacao e turno chegam ao filho por ambiente.

Uso:
  agata-run --modelo M --sessao ID --plataforma claude|codex|opencode|gemini
            [--dry-run] [--sem-sync] [--perfis ARQ.yaml] [-- args da plataforma]

Contencao (ordem):
  1. Landlock via redesign/mcp/landlock.py (aplicar_perfil / compilar_regras).
  2. Se Landlock falhar: fallback bwrap (redesign/grafo/sandbox.py), ATIVO por padrao.
  3. AGATA_LANDLOCK=0 desliga a contencao inteira (rollback gradual); o filho recebe
     AGATA_LANDLOCK_ACTIVE=0 e o aviso vai para stderr.

Limites declarados:
  - Rede: Landlock ABI 4 filtra connect TCP por PORTA, nao por host. As portas
    liberadas (padrao 53,80,443,11434,20127,20134; AGATA_RUN_PORTAS troca) valem para
    qualquer destino. UDP e bind nao sao filtrados. Em ABI < 4 a rede fica livre.
  - Sem lancador = sem contencao (quem roda a plataforma direto escapa).
  - Sem broker nem executor privilegiado (Fase 3): nenhum segredo e injetado e
    ~/.config/agata nao esta em perfil algum.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "redesign" / "mcp"))
sys.path.insert(0, str(RAIZ / "redesign" / "grafo"))

PLATAFORMAS = {
    "claude": "claude",
    "codex": "codex",
    "opencode": "opencode",
    "gemini": "gemini",
}

# Diretorios proprios de cada plataforma (estado/config dela, nao do Agata).
# (caminho relativo ao HOME, escrita?)
DIRS_PLATAFORMA = {
    "claude": [(".claude", True), (".claude.json", True), (".local/share/claude", False),
               (".local/state/claude", True), (".cache/claude", True), (".local/bin", False)],
    "codex": [(".codex", True), (".local/bin", False)],
    "opencode": [(".config/opencode", True), (".local/share/opencode", True),
                 (".local/state/opencode", True), (".cache/opencode", True),
                 (".opencode", False), (".local/bin", False)],
    "gemini": [(".gemini", True), (".local/bin", False)],
}

SISTEMA_RO = ["/usr", "/etc", "/bin", "/sbin", "/lib", "/lib64", "/opt", "/run", "/proc", "/sys"]
DEV_RW = ["/dev"]
PORTAS_PADRAO = "53,80,443,11434,20127,20134"
SEM_BROKER = ("AGATA_CAPABILITY_BROKER", "AGATA_PRIVILEGED_EXECUTOR")


def _acessos():
    import landlock as ll
    ro_exec = ll.FS_RO_DIR | ll.FS_EXECUTE
    rw = ll.FS_RW_DIR | ll.FS_EXECUTE
    return ll, ro_exec, rw


# ---------------------------------------------------------------- hidratacao
def _sha(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    except OSError:
        return None


def hidratar(raiz: Path = RAIZ) -> dict:
    """JSON de hidratacao: hashes do canon, HEAD curto e ultima entrada de MEMORIAS."""
    head = None
    try:
        r = subprocess.run(["git", "-C", str(raiz), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        head = r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        pass
    ultima = None
    try:
        linhas = (raiz / "MEMÓRIAS.md").read_text(encoding="utf-8").splitlines()
        inicio = next((i for i, l in enumerate(linhas) if "ENTRADAS-NOVAS" in l), -1)
        cand = [l for l in linhas[inicio + 1:] if l.startswith("(")]
        ultima = (cand[-1] if cand else None)
        if ultima:
            ultima = ultima[:400]
    except OSError:
        pass
    return {"REGRAS": _sha(raiz / "REGRAS.md"), "MEMORIAS": _sha(raiz / "MEMÓRIAS.md"),
            "PROJETO": _sha(raiz / "PROJETO.md"), "HEAD": head, "ultima_entrada": ultima}


def turno(sessao: str, modelo: str, avancar: bool = True, raiz: Path = RAIZ) -> str:
    cmd = [sys.executable, str(raiz / "scripts" / "turno.py"), "proximo" if avancar else "atual",
           "--sessao", sessao, "--modelo", modelo]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as e:
        return f"t=? (contador indisponivel: {e})"
    linha = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    return linha or f"t=? (contador sem saida, codigo {r.returncode})"


# ------------------------------------------------------------------- perfil
def _ler_yaml(texto: str) -> dict:
    """Le o formato de containment-profiles.yaml (perfis > nome > regras > - caminho/acesso).
    O venv do CI nao tem PyYAML: subconjunto proprio, sem dependencia. Formato fora disso
    levanta ValueError (nunca interpreta errado em silencio)."""
    perfis, atual, regra = {}, None, None
    for n, bruta in enumerate(texto.splitlines(), 1):
        linha = bruta.split("#", 1)[0].rstrip()
        if not linha.strip():
            continue
        ind, t = len(linha) - len(linha.lstrip()), linha.strip()
        if ind == 0:
            if t != "perfis:":
                raise ValueError(f"linha {n}: chave de topo inesperada: {t}")
        elif ind == 2 and t.endswith(":"):
            atual = perfis.setdefault(t[:-1], {"regras": []})
        elif ind == 4 and t == "regras:" and atual is not None:
            continue
        elif t.startswith("- caminho:") and atual is not None:
            regra = {"caminho": t.split(":", 1)[1].strip()}
            atual["regras"].append(regra)
        elif t.startswith("acesso:") and regra is not None:
            regra["acesso"] = int(t.split(":", 1)[1].strip())
        else:
            raise ValueError(f"linha {n}: formato nao suportado: {t}")
    return {"perfis": perfis} if perfis else {}


def carregar_perfil(modelo: str, plataforma: str, arquivo: Path | None = None) -> tuple[str, list]:
    """Precedencia: perfil do modelo > da plataforma > default. Retorna (nome, regras)."""
    arq = arquivo or (RAIZ / "config" / "containment-profiles.yaml")
    try:
        dados = _ler_yaml(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SystemExit(f"agata-run: perfis ilegiveis ({arq}): {e}")
    perfis = dados.get("perfis")
    if not isinstance(perfis, dict):
        raise SystemExit(f"agata-run: {arq} sem chave 'perfis'")
    for nome in (modelo, plataforma, "default"):
        p = perfis.get(nome)
        if p is not None:
            regras = []
            for r in (p.get("regras") or []):
                if "caminho" not in r or not isinstance(r.get("acesso"), int):
                    raise SystemExit(f"agata-run: regra invalida no perfil {nome}: {r}")
                regras.append((str(r["caminho"]), int(r["acesso"])))
            return nome, regras
    raise SystemExit("agata-run: nenhum perfil aplicavel (nem 'default')")


def regras_completas(regras_perfil: list, plataforma: str, exe: str | None,
                     home: str | None = None, tmp: list[str] | None = None) -> list:
    """Perfil + o que qualquer processo precisa para executar (sistema ro, /dev, tmp,
    dirs da plataforma, diretorio do executavel). So caminhos que existem."""
    ll, ro_exec, rw = _acessos()
    home = home or os.path.expanduser("~")
    tmp = tmp if tmp is not None else (os.environ.get("AGATA_RUN_TMP", "/tmp").split(os.pathsep))
    out = list(regras_perfil)
    out += [(p, ro_exec) for p in SISTEMA_RO]
    out += [(p, rw) for p in DEV_RW]
    out += [(p, rw) for p in tmp if p]
    for rel, escrita in DIRS_PLATAFORMA.get(plataforma, []):
        out.append((os.path.join(home, rel), rw if escrita else ro_exec))
    if exe:
        for d in {os.path.dirname(exe), os.path.dirname(os.path.realpath(exe))}:
            out.append((d, ro_exec))
        for alvo in _executaveis(exe):
            for d in _prefixos(alvo, home):
                out.append((d, ro_exec))
    visto, final = set(), []
    for c, a in out:
        if os.path.exists(c) and (c, a) not in visto:
            visto.add((c, a))
            final.append((c, a))
    return final


def _interprete(exe: str) -> str | None:
    """Interprete do shebang de exe (resolve `/usr/bin/env X` pelo PATH), ou None."""
    try:
        with open(exe, "rb") as f:
            l = f.readline(256)
    except OSError:
        return None
    if not l.startswith(b"#!"):
        return None
    partes = l[2:].decode("utf-8", "replace").split()
    if partes and os.path.basename(partes[0]) == "env":
        partes = [x for x in partes[1:] if not x.startswith("-")]
        return shutil.which(partes[0]) if partes else None
    return partes[0] if partes else None


def _executaveis(exe: str) -> list[str]:
    alvos = [exe]
    i = _interprete(exe)
    if i:
        alvos.append(i)
    return alvos


def _prefixos(alvo: str, home: str) -> list[str]:
    """Diretorios de instalacao do alvo (pai do bin, simbolico e resolvido), para leitura+exec.
    So vale quando o pai parece prefixo de instalacao (pyvenv.cfg ou lib/) e nunca e a raiz, o
    home ou um ancestral de ~/.config (o .env fica de fora)."""
    saida = []
    proibido = os.path.realpath(os.path.join(home, ".config"))
    for caminho in {alvo, os.path.realpath(alvo)}:
        pref = os.path.dirname(os.path.dirname(caminho))
        real = os.path.realpath(pref)
        if pref in ("", "/") or real in ("/", os.path.realpath(home)):
            continue
        if proibido == real or proibido.startswith(real + os.sep):
            continue
        if os.path.exists(os.path.join(pref, "pyvenv.cfg")) or os.path.isdir(os.path.join(pref, "lib")):
            saida.append(pref)
            # venv: a instalacao base (home = ... em pyvenv.cfg) tambem precisa de leitura+exec
            cfg = os.path.join(pref, "pyvenv.cfg")
            try:
                for linha in open(cfg, encoding="utf-8"):
                    if linha.split("=")[0].strip() == "home":
                        base = os.path.dirname(os.path.realpath(linha.split("=", 1)[1].strip()))
                        if base not in ("/", os.path.realpath(home)) and not (
                                proibido == base or proibido.startswith(base + os.sep)):
                            saida.append(base)
            except OSError:
                pass
    return saida


def portas() -> list[int]:
    bruto = os.environ.get("AGATA_RUN_PORTAS", PORTAS_PADRAO)
    return sorted({int(x) for x in bruto.split(",") if x.strip().isdigit()})


class _NetPortAttr(ctypes.Structure):
    _fields_ = [("allowed_access", ctypes.c_uint64), ("port", ctypes.c_uint64)]


def aplicar_landlock(regras: list, portas_net: list[int]) -> dict:
    """Aplica ao processo atual. Com ABI >= 4 e portas: usa compilar_regras (ruleset que
    trata connect TCP) + uma regra por porta + restrict_self. Senao, aplicar_perfil."""
    ll, _ro, _rw = _acessos()
    abi = ll.ler_abi_versao()
    perfil = ll.RulesetProfile("agata-run", regras)
    if abi >= 4 and portas_net:
        perfil.regras = regras + [("<rede>", ll.NET_CONNECT_TCP << 32)]
        fd = ll.compilar_regras(perfil)
        for p in portas_net:
            attr = _NetPortAttr(ll.NET_CONNECT_TCP, p)
            ll._syscall_landlock(445, fd, ll.LANDLOCK_RULE_NET_PORT,
                                 ll._ptr(ctypes.addressof(attr)), 0)
        ll.restrict_self(fd)
        return {"abi": abi, "rede": "porta", "portas": portas_net}
    ll.aplicar_perfil(perfil)
    return {"abi": abi, "rede": "livre", "portas": []}


def montar_bwrap(argv: list[str], regras: list, cwd: str | None = None) -> list[str]:
    """Comando bwrap de fallback: ro/rw vindos das regras (acesso com escrita = rw)."""
    import sandbox
    ll, _a, _b = _acessos()
    a = sandbox._base_args(True, cwd)
    escrita = ll.FS_WRITE_FILE
    vistos = {}
    for c, acesso in regras:
        if c in ("/usr", "/etc", "/proc", "/dev", "/bin", "/sbin", "/lib", "/lib64", "/sys"):
            continue
        c = os.path.abspath(c)
        vistos[c] = vistos.get(c, False) or bool(acesso & escrita)
    for c, rw in vistos.items():
        if c == "/tmp" or not os.path.exists(c):
            continue
        a += ["--bind" if rw else "--ro-bind", c, c]
    a += ["--setenv", "PATH", os.environ.get("PATH", "/usr/bin"),
          "--setenv", "HOME", os.environ.get("HOME", "/tmp")]
    return a + ["--"] + argv


# ---------------------------------------------------------------- montagem
def montar_comando(plataforma: str, extra: list[str]) -> list[str]:
    if plataforma not in PLATAFORMAS:
        raise SystemExit(f"agata-run: plataforma desconhecida: {plataforma}")
    return [PLATAFORMAS[plataforma]] + list(extra)


def montar_ambiente(base: dict, modelo: str, sessao: str, plataforma: str,
                    hidr: dict, linha_turno: str, ativo: bool) -> dict:
    env = {k: v for k, v in base.items() if k not in SEM_BROKER}
    env.update({
        "AGATA_HIDRATACAO_JSON": json.dumps(hidr, ensure_ascii=False),
        "AGATA_TURNO": linha_turno,
        "AGATA_MODEL_ID": modelo,
        "AGATA_SESSAO_ID": sessao,
        "AGATA_PLATFORM": plataforma,
        "AGATA_LANDLOCK_ACTIVE": "1" if ativo else "0",
    })
    return env


def sync() -> None:
    try:
        r = subprocess.run(["git", "-C", str(RAIZ), "pull", "--ff-only", "origin", "main"],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            print("AVISO agata-run: sync falhou, segue local: " + r.stderr.strip()[:200], file=sys.stderr)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"AVISO agata-run: sync falhou, segue local: {e}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(prog="agata-run", description=__doc__.split("\n\n")[0])
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--sessao", required=True)
    ap.add_argument("--plataforma", required=True)
    ap.add_argument("--dry-run", action="store_true", help="imprime o plano (JSON); nao contem nem executa")
    ap.add_argument("--sem-sync", action="store_true", help="nao roda git pull --ff-only")
    ap.add_argument("--perfis", type=Path, default=None, help="YAML de perfis (padrao config/containment-profiles.yaml)")
    a = ap.parse_args(argv)

    if a.plataforma not in PLATAFORMAS:
        print(f"agata-run: plataforma desconhecida: {a.plataforma}", file=sys.stderr)
        return 2
    cmd = montar_comando(a.plataforma, extra)
    exe = shutil.which(cmd[0])
    if exe is None and not a.dry_run:
        print(f"agata-run: executavel '{cmd[0]}' nao encontrado no PATH; nada executado", file=sys.stderr)
        return 127
    desligado = os.environ.get("AGATA_LANDLOCK") == "0"
    nome_perfil, regras_perfil = carregar_perfil(a.modelo, a.plataforma, a.perfis)
    regras = regras_completas(regras_perfil, a.plataforma, exe)

    if not a.dry_run and not a.sem_sync:
        sync()
    hidr = hidratar()
    linha = turno(a.sessao, a.modelo, avancar=not a.dry_run)
    forcar_bwrap = os.environ.get("AGATA_RUN_TESTE_SEM_LANDLOCK") == "1"

    if a.dry_run:
        modo = "desligado" if desligado else ("bwrap" if forcar_bwrap else "landlock")
        plano = {"plataforma": a.plataforma, "comando": [exe or cmd[0]] + cmd[1:], "perfil": nome_perfil,
                 "contencao": modo, "regras": [[c, ac] for c, ac in regras], "portas": portas(),
                 "turno": linha, "hidratacao": hidr, "env": sorted(k for k in
                 montar_ambiente({}, a.modelo, a.sessao, a.plataforma, hidr, linha, not desligado))}
        if modo == "bwrap":
            plano["bwrap"] = montar_bwrap([exe or cmd[0]] + cmd[1:], regras)
        print(json.dumps(plano, ensure_ascii=False, indent=2))
        return 0

    alvo = [exe] + cmd[1:]
    ativo = False
    if desligado:
        print("AVISO agata-run: AGATA_LANDLOCK=0, SEM contencao", file=sys.stderr)
    else:
        try:
            if forcar_bwrap:
                raise OSError("falha simulada de Landlock (teste)")
            info = aplicar_landlock(regras, portas())
            ativo = True
            print(f"agata-run: Landlock ativo (ABI {info['abi']}, rede {info['rede']})", file=sys.stderr)
        except (OSError, RuntimeError, ImportError) as e:
            if not shutil.which("bwrap"):
                print(f"agata-run: Landlock falhou ({e}) e bwrap ausente; recuso rodar sem contencao", file=sys.stderr)
                return 3
            print(f"AVISO agata-run: Landlock falhou ({e}); fallback bwrap", file=sys.stderr)
            alvo = montar_bwrap(alvo, regras)
            ativo = True
    env = montar_ambiente(dict(os.environ), a.modelo, a.sessao, a.plataforma, hidr, linha, ativo)
    try:
        os.execvpe(alvo[0], alvo, env)
    except OSError as e:
        print(f"agata-run: exec falhou: {e}", file=sys.stderr)
        return 126


if __name__ == "__main__":
    sys.exit(main())
