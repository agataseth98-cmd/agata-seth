"""Testes da Fase 1 do sandbox Landlock (apenas stdlib + ctypes).

Prova de verdade:
  1. ABI do Landlock lida em tempo de execucao (>= 1).
  2. criar_ruleset retorna um file descriptor valido (>= 0).
  3. ~/.config/agata/.env inacessível ao processo contido (PermissionError/EACCES)
     — sem ler o conteúdo do .env. (processo filho contido)
  4. Escrita fora dos caminhos permitidos negada (PermissionError/EACCES).
     (processo filho contido)
  5. Sem regra de negar: caminho não listado é inacessível por omissão.
  6. ~/.config/agata fora de todos os perfis de contenção.

Os testes 3 e 4 rodam em subprocess contido, sem skip.
"""
from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from landlock import (  # noqa: E402
    ler_abi_versao,
    criar_ruleset,
    add_path_rule,
    restrict_self,
    FS_READ_DIR,
    FS_READ_FILE,
    FS_WRITE_FILE,
    FS_MAKE_REG,
    FS_MAKE_DIR,
    FS_REMOVE_FILE,
    FS_REMOVE_DIR,
)

ENV = os.path.expanduser("~/.config/agata/.env")

# Direitos para /tmp (diretorio): leitura + gravacao de diretorio e arquivo.
TMP_RIGHTS = (
    FS_READ_DIR | FS_READ_FILE | FS_WRITE_FILE |
    FS_MAKE_REG | FS_MAKE_DIR | FS_REMOVE_FILE | FS_REMOVE_DIR
)


def _executar_filho_contido(permitido: str, outro: str) -> dict:
    """Lanca um subprocess que aplica um perfil (RW so em `permitido`) e testa acessos."""
    codigo = (
        "import os, json, sys\n"
        "sys.path.insert(0, %r)\n"
        "from landlock import RulesetProfile, aplicar_perfil, FS_RW_DIR\n"
        "permitido, outro, env = %r, %r, %r\n"
        "aplicar_perfil(RulesetProfile('t', [(permitido, FS_RW_DIR)]))\n"
        "r = {}\n"
        "def tenta(chave, f):\n"
        "    try:\n"
        "        f(); r[chave] = 'ok'\n"
        "    except PermissionError as e:\n"
        "        r[chave] = 'EACCES'\n"
        "    except OSError as e:\n"
        "        r[chave] = 'errno=%%d' %% e.errno\n"
        "def grava(d):\n"
        "    fd = os.open(os.path.join(d, 'x'), os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600)\n"
        "    os.write(fd, b'a'); os.close(fd)\n"
        "tenta('escrita_permitida', lambda: grava(permitido))\n"
        "tenta('leitura_permitida', lambda: os.close(os.open(os.path.join(permitido, 'x'), os.O_RDONLY)))\n"
        "tenta('escrita_fora', lambda: grava(outro))\n"
        "tenta('env', lambda: os.close(os.open(env, os.O_RDONLY)))\n"
        "print(json.dumps(r), flush=True)\n"
    ) % (os.path.dirname(os.path.abspath(__file__)), permitido, outro, ENV)

    proc = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, timeout=20,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"filho falhou (rc={proc.returncode}): stderr={proc.stderr.strip()}"
        )
    return json.loads(proc.stdout.strip())


@pytest.fixture
def dois_dirs(tmp_path):
    permitido = tmp_path / "permitido"
    outro = tmp_path / "outro"
    permitido.mkdir()
    outro.mkdir()
    return str(permitido), str(outro)


def test_abi_landlock_lido_em_execucao():
    """O kernel expõe a versão de ABI do Landlock via syscall 444."""
    abi = ler_abi_versao()
    assert isinstance(abi, int)
    assert abi >= 1, f"esperava ABI >= 1, veio {abi}"


def test_criar_ruleset_retorna_fd_valido():
    """criar_ruleset deve retornar um file descriptor valido (>= 0)."""
    fd = criar_ruleset(TMP_RIGHTS, 0)
    assert isinstance(fd, int)
    assert fd >= 0, f"esperava fd >= 0, veio {fd}"


def test_add_rule_funciona_neste_kernel(tmp_path):
    """add_rule retorna 0 (antes o wrapper passava um tamanho no lugar de flags)."""
    fd = criar_ruleset(TMP_RIGHTS, 0)
    add_path_rule(fd, str(tmp_path), TMP_RIGHTS)
    os.close(fd)


def test_env_inacessivel_processo_contido(dois_dirs):
    """~/.config/agata/.env nao listado -> PermissionError no filho contido.

    O pai nunca le o conteudo do .env; so o filho contido tenta abrir.
    """
    dados = _executar_filho_contido(*dois_dirs)
    assert dados["env"] == "EACCES", dados


def test_escrita_fora_do_permitido_negada(dois_dirs):
    dados = _executar_filho_contido(*dois_dirs)
    assert dados["escrita_fora"] == "EACCES", dados


def test_dentro_do_permitido_funciona(dois_dirs):
    dados = _executar_filho_contido(*dois_dirs)
    assert dados["escrita_permitida"] == "ok", dados
    assert dados["leitura_permitida"] == "ok", dados


def test_yaml_acessos_batem_com_constantes():
    """Os numeros do YAML devem ser os valores reais de FS_RO_DIR e FS_RW_DIR."""
    from landlock import FS_RO_DIR, FS_RW_DIR
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "..", "config", "containment-profiles.yaml")
    numeros = set()
    for linha in open(caminho):
        linha = linha.split("#")[0].strip()
        if linha.startswith("acesso:"):
            numeros.add(int(linha.split(":")[1]))
    assert numeros <= {FS_RO_DIR, FS_RW_DIR}, numeros


def test_sem_regra_de_negar_caminho_nao_listado_eh_inacessivel():
    """Confirmacao de design: so caminhos listados sao permitidos; o resto cai por omissao.
    Nenhuma regra de `allow=False` e usada em nenhum ponto.
    """
    fonte = inspect.getsource(restrict_self)
    fonte += inspect.getsource(criar_ruleset)
    fonte += inspect.getsource(add_path_rule)
    assert "allow=False" not in fonte, "nao deve existir regra de negar (allow=False)"
    assert "deny" not in fonte.lower(), "nao deve existir conceito de deny"


def test_config_agata_fora_de_todos_perfis():
    """~/.config/agata nao pode aparecer em nenhum perfil de contencao."""
    perfis_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "config", "containment-profiles.yaml",
    )
    with open(perfis_path) as f:
        texto = f.read()

    assert "/home/orusoua/.config/agata" not in texto
    assert os.path.expanduser("~/.config/agata") not in texto
