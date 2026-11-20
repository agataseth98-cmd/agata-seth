"""Testes do lancador agata-run (Fase 2 do sandbox). Processo real, plataforma falsa.

A plataforma de teste e um script Python chamado `claude` num diretorio temporario
no PATH; nenhum claude/codex/opencode de verdade e executado. O pai nunca le o .env.
"""
import json
import os
import socket
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
RUN = RAIZ / "scripts" / "agata_run.py"
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "redesign" / "mcp"))
import agata_run  # noqa: E402
import landlock  # noqa: E402

try:
    landlock.ler_abi_versao()
    TEM_LANDLOCK = True
except Exception:
    TEM_LANDLOCK = False
precisa_landlock = pytest.mark.skipif(not TEM_LANDLOCK, reason="kernel sem Landlock")

FILHO = textwrap.dedent('''\
    #!/usr/bin/env python3
    import json, os, sys
    def tenta(f):
        try:
            f(); return "ok"
        except OSError as e:
            return type(e).__name__
    def abrir(p):
        open(p, "rb").read(1)
    def escrever(p):
        open(p, "ab").write(b"x")
    alvos = json.loads(os.environ.get("ALVOS", "{}"))
    def conecta(porta):
        import socket
        socket.create_connection(("127.0.0.1", porta), timeout=2).close()
    out = {"argv": sys.argv[1:],
           "env": {k: v for k, v in os.environ.items() if k.startswith("AGATA_")},
           "le_segredo": tenta(lambda: abrir(alvos["segredo"])) if "segredo" in alvos else None,
           "le_env_real": tenta(lambda: abrir(alvos["env_real"])) if "env_real" in alvos else None,
           "escreve_fora": tenta(lambda: escrever(alvos["fora"])) if "fora" in alvos else None,
           "escreve_dentro": tenta(lambda: escrever(alvos["dentro"])) if "dentro" in alvos else None,
           "conecta": tenta(lambda: conecta(alvos["porta"])) if "porta" in alvos else None,
           "le_dentro": tenta(lambda: abrir(alvos["dentro"])) if "dentro" in alvos else None}
    print(json.dumps(out))
''')

PERFIS = textwrap.dedent('''\
    perfis:
      default:
        regras:
          - caminho: {permitido}
            acesso: 12
          - caminho: {escrita}
            acesso: 446
''')


@pytest.fixture
def cenario(tmp_path):
    permitido = tmp_path / "permitido"
    escrita = permitido / "escrita"
    tmpc = permitido / "tmp"
    segredo = tmp_path / "segredo"
    fora = tmp_path / "fora"
    binc = tmp_path / "bin"
    home = tmp_path / "home"
    for d in (escrita, tmpc, segredo, fora, binc, home):
        d.mkdir(parents=True)
    (segredo / ".env").write_text("CHAVE=nao-e-segredo-real\n")
    (fora / "alvo.txt").write_text("a")
    (escrita / "alvo.txt").write_text("a")
    for nome in ("claude", "codex", "opencode"):
        f = binc / nome
        f.write_text(FILHO)
        f.chmod(0o755)
    perfis = tmp_path / "perfis.yaml"
    perfis.write_text(PERFIS.format(permitido=permitido, escrita=escrita))
    env = dict(os.environ)
    env.update({"PATH": f"{binc}:{os.environ['PATH']}", "HOME": str(home),
                "AGATA_TURNOS_DIR": str(tmp_path / "turnos"),
                "AGATA_RUN_TMP": str(tmpc),
                "AGATA_RUN_PORTAS": "443",
                "ALVOS": json.dumps({"segredo": str(segredo / ".env"), "fora": str(fora / "alvo.txt"),
                                     "dentro": str(escrita / "alvo.txt")})})
    for k in ("AGATA_LANDLOCK", "AGATA_RUN_TESTE_SEM_LANDLOCK", *agata_run.SEM_BROKER):
        env.pop(k, None)
    return {"env": env, "perfis": perfis, "bin": binc, "fora": fora, "escrita": escrita, "tmp": tmp_path}


def rodar(c, *args, plataforma="claude", extra=(), env=None):
    cmd = [sys.executable, str(RUN), "--modelo", "seth-codigo", "--sessao", "teste-sessao",
           "--plataforma", plataforma, "--sem-sync", "--perfis", str(c["perfis"]), *args]
    if extra:
        cmd += ["--", *extra]
    return subprocess.run(cmd, capture_output=True, text=True, env=env or c["env"], timeout=60)


def saida_filho(r):
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


@precisa_landlock
def test_filho_nao_abre_env_nem_escreve_fora(cenario):
    c = cenario
    alvos = json.loads(c["env"]["ALVOS"])
    alvos["env_real"] = os.path.expanduser("~/.config/agata/.env")  # so o filho tenta abrir
    c["env"]["ALVOS"] = json.dumps(alvos)
    r = rodar(c, extra=["--x"])
    o = saida_filho(r)
    assert o["le_segredo"] == "PermissionError"
    assert o["escreve_fora"] == "PermissionError"
    assert o["le_dentro"] == "ok" and o["escreve_dentro"] == "ok"
    assert o["env"]["AGATA_LANDLOCK_ACTIVE"] == "1"
    if os.path.exists(alvos["env_real"]):
        assert o["le_env_real"] == "PermissionError"
    assert (c["fora"] / "alvo.txt").read_text() == "a"
    assert "Landlock ativo" in r.stderr


@precisa_landlock
def test_hidratacao_e_turno_chegam_por_ambiente(cenario):
    o = saida_filho(rodar(cenario, extra=["--version"]))
    env = o["env"]
    assert o["argv"] == ["--version"]
    hid = json.loads(env["AGATA_HIDRATACAO_JSON"])
    assert {"REGRAS", "MEMORIAS", "PROJETO", "HEAD", "ultima_entrada"} <= set(hid)
    assert hid["REGRAS"] and hid["HEAD"]
    assert "t=1 (contador mecânico)" in env["AGATA_TURNO"]
    assert env["AGATA_MODEL_ID"] == "seth-codigo"
    assert env["AGATA_SESSAO_ID"] == "teste-sessao"
    assert env["AGATA_PLATFORM"] == "claude"
    for k in agata_run.SEM_BROKER:
        assert k not in env
    # segundo turno avanca o contador
    assert saida_filho(rodar(cenario))["env"]["AGATA_TURNO"].count("t=2 (contador") == 1


def test_broker_herdado_e_removido(cenario):
    env = dict(cenario["env"], AGATA_CAPABILITY_BROKER="x", AGATA_PRIVILEGED_EXECUTOR="y")
    o = saida_filho(rodar(cenario, env=dict(env, AGATA_LANDLOCK="0")))
    assert "AGATA_CAPABILITY_BROKER" not in o["env"] and "AGATA_PRIVILEGED_EXECUTOR" not in o["env"]


def test_landlock_zero_desliga(cenario):
    env = dict(cenario["env"], AGATA_LANDLOCK="0")
    r = rodar(cenario, env=env)
    o = saida_filho(r)
    assert o["env"]["AGATA_LANDLOCK_ACTIVE"] == "0"
    assert o["le_segredo"] == "ok"  # sem contencao o filho le (prova que o 0 desliga)
    assert "SEM contencao" in r.stderr


@precisa_landlock
def test_fallback_bwrap_quando_landlock_falha(cenario):
    if not shutil.which("bwrap"):
        pytest.skip("sem bwrap")
    env = dict(cenario["env"], AGATA_RUN_TESTE_SEM_LANDLOCK="1")
    r = rodar(cenario, env=env)
    if r.returncode != 0 and ("namespace" in r.stderr or "Operation not permitted" in r.stderr):
        pytest.skip("bwrap sem permissao de namespace neste ambiente: " + r.stderr[:120])
    o = saida_filho(r)
    assert "fallback bwrap" in r.stderr
    assert o["le_segredo"] != "ok"
    assert o["escreve_fora"] != "ok"


def test_dry_run_nao_executa_nem_avanca_turno(cenario):
    r = rodar(cenario, "--dry-run", extra=["--version"])
    assert r.returncode == 0
    plano = json.loads(r.stdout)
    assert plano["comando"][-1] == "--version" and plano["contencao"] == "landlock"
    assert plano["portas"] == [443]
    assert not (cenario["tmp"] / "turnos").exists()  # `atual` nao cria contador
    assert "AGATA_CAPABILITY_BROKER" not in plano["env"]


def test_dry_run_bwrap_monta_comando(cenario):
    env = dict(cenario["env"], AGATA_RUN_TESTE_SEM_LANDLOCK="1")
    plano = json.loads(rodar(cenario, "--dry-run", env=env).stdout)
    assert plano["contencao"] == "bwrap"
    b = plano["bwrap"]
    assert b[1] == "--unshare-all" and "--share-net" in b and "--" in b
    i = b.index("--")
    assert b[i + 1].endswith("/claude")
    rw = str(cenario["escrita"])
    assert ["--bind", rw, rw] == b[b.index(rw) - 1: b.index(rw) + 2]
    assert not any("segredo" in x for x in b)


def test_dry_run_com_landlock_zero(cenario):
    plano = json.loads(rodar(cenario, "--dry-run", env=dict(cenario["env"], AGATA_LANDLOCK="0")).stdout)
    assert plano["contencao"] == "desligado"


@pytest.mark.parametrize("plat", ["claude", "codex", "opencode"])
def test_montagem_por_plataforma(cenario, plat):
    plano = json.loads(rodar(cenario, "--dry-run", plataforma=plat, extra=["-p", "oi"]).stdout)
    assert plano["comando"] == [str(cenario["bin"] / plat), "-p", "oi"]
    assert agata_run.montar_comando(plat, ["a"]) == [plat, "a"]


def test_gemini_ausente_erro_sem_executar(cenario):
    env = dict(cenario["env"], PATH=str(cenario["bin"]) + ":/usr/bin")
    if shutil.which("gemini", path=env["PATH"]):
        pytest.skip("gemini instalado")
    r = rodar(cenario, plataforma="gemini", env=env)
    assert r.returncode == 127 and "nao encontrado" in r.stderr
    assert agata_run.montar_comando("gemini", ["--version"]) == ["gemini", "--version"]


def test_plataforma_invalida(cenario):
    r = rodar(cenario, plataforma="invalida")
    assert r.returncode != 0 and "desconhecida" in r.stderr


def test_help_e_sem_termos_proibidos():
    r = subprocess.run([str(RAIZ / "scripts" / "agata-run"), "--help"], capture_output=True, text=True)
    assert r.returncode == 0 and "--plataforma" in r.stdout
    fonte = (RUN.read_text() + (RAIZ / "scripts" / "agata-run").read_text()).lower()
    for termo in ("sudo", "apt ", "pip install", "pacman -s"):
        assert termo not in fonte


def test_precedencia_de_perfil(tmp_path):
    arq = tmp_path / "p.yaml"
    arq.write_text("perfis:\n  default:\n    regras:\n      - caminho: /a\n        acesso: 12\n"
                   "  claude:\n    regras:\n      - caminho: /b\n        acesso: 12\n"
                   "  m1:\n    regras:\n      - caminho: /c\n        acesso: 12\n")
    assert agata_run.carregar_perfil("m1", "claude", arq)[0] == "m1"
    assert agata_run.carregar_perfil("x", "claude", arq)[0] == "claude"
    assert agata_run.carregar_perfil("x", "codex", arq)[0] == "default"


def test_perfil_ausente_falha(tmp_path):
    arq = tmp_path / "p.yaml"
    arq.write_text("outra: 1\n")
    with pytest.raises(SystemExit):
        agata_run.carregar_perfil("x", "claude", arq)


def test_yaml_real_do_repo_le_todos_os_perfis():
    dados = agata_run._ler_yaml((RAIZ / "config" / "containment-profiles.yaml").read_text())
    assert {"default", "bash_ro", "write", "seth-livre", "seth-codigo"} <= set(dados["perfis"])
    assert dados["perfis"]["seth-codigo"]["regras"][1] == {"caminho": "/home/orusoua/agata/propostas", "acesso": 446}


@precisa_landlock
@pytest.mark.skipif(not TEM_LANDLOCK or landlock.ler_abi_versao() < 4, reason="rede por porta exige ABI 4")
def test_rede_so_nas_portas_liberadas(cenario):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)
    porta = srv.getsockname()[1]
    try:
        alvos = json.loads(cenario["env"]["ALVOS"])
        alvos["porta"] = porta
        cenario["env"]["ALVOS"] = json.dumps(alvos)
        # porta fora da lista (so 443): negada
        assert saida_filho(rodar(cenario))["conecta"] == "PermissionError"
        # porta liberada: passa (limite: vale para qualquer host, Landlock filtra porta)
        env = dict(cenario["env"], AGATA_RUN_PORTAS=f"443,{porta}")
        assert saida_filho(rodar(cenario, env=env))["conecta"] == "ok"
    finally:
        srv.close()


@precisa_landlock
def test_interprete_fora_de_usr_roda_e_env_segue_negado(cenario, tmp_path):
    """Filho com shebang `env python3` resolvendo para um venv fora de /usr (como o do CI)."""
    c = cenario
    venv = tmp_path / "venv-fora"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True,
                   capture_output=True, timeout=60)
    c["env"]["PATH"] = f"{venv / 'bin'}:{c['env']['PATH']}"
    alvos = json.loads(c["env"]["ALVOS"])
    alvos["env_real"] = os.path.expanduser("~/.config/agata/.env")
    c["env"]["ALVOS"] = json.dumps(alvos)
    r = rodar(c, extra=["--x"])
    o = saida_filho(r)  # sem o prefixo do interprete: "Fatal Python error: init_import_site"
    assert "Fatal Python error" not in r.stderr
    assert o["le_segredo"] == "PermissionError"
    if os.path.exists(alvos["env_real"]):
        assert o["le_env_real"] == "PermissionError"


def test_prefixos_do_interprete_nao_abrem_config(tmp_path):
    venv = tmp_path / "v"
    (venv / "bin").mkdir(parents=True)
    (venv / "pyvenv.cfg").write_text("home = /usr/bin\n")
    py = venv / "bin" / "python3"
    py.write_text("x")
    home = tmp_path / "h"
    (home / ".config" / "agata").mkdir(parents=True)
    assert str(venv) in agata_run._prefixos(str(py), str(home))
    assert agata_run._prefixos(str(home / "bin" / "x"), str(home)) == []
    (home / "lib").mkdir()
    assert agata_run._prefixos(str(home / "bin" / "x"), str(home)) == []
