"""Landlock LSM wrapper para Agata — só stdlib + ctypes.

Nunca depende de `python-landlock` (PyPI). O wrapper chama as syscalls
`landlock_create_ruleset`, `landlock_add_rule` e `landlock_restrict_self`
diretamente pelo número de syscall do kernel (444/445/446 em x86_64).

Princípio de segurança: Landlock so PERMITE. Nao existe regra de negar: um
caminho nao listado eh inacessivel por omissao. Nao ha `allow=False`.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import os
from typing import Optional

# Numeros de syscall x86_64 (conferidos em /usr/include/asm/unistd_64.h).
__NR_landlock_create_ruleset = 444
__NR_landlock_add_rule = 445
__NR_landlock_restrict_self = 446

PR_SET_NO_NEW_PRIVS = 38

# Regras.
LANDLOCK_RULE_PATH_BENEATH = 1
LANDLOCK_RULE_NET_PORT = 2

# Flags de criacao de ruleset (ABI lida em tempo de execucao).
LANDLOCK_CREATE_RULESET_VERSION = 1 << 0
LANDLOCK_CREATE_RULESET_ERRATA = 1 << 1

# Flags de restrict_self.
LANDLOCK_RESTRICT_SELF_LOG_SAME_EXEC_OFF = 1 << 0
LANDLOCK_RESTRICT_SELF_LOG_NEW_EXEC_ON = 1 << 1
LANDLOCK_RESTRICT_SELF_LOG_SUBDOMAINS_OFF = 1 << 2
LANDLOCK_RESTRICT_SELF_TSYNC = 1 << 3

# Direitos de sistema de arquivos (ABI 3).
FS_EXECUTE = 1 << 0
FS_WRITE_FILE = 1 << 1
FS_READ_FILE = 1 << 2
FS_READ_DIR = 1 << 3
FS_REMOVE_DIR = 1 << 4
FS_REMOVE_FILE = 1 << 5
FS_MAKE_CHAR = 1 << 6
FS_MAKE_DIR = 1 << 7
FS_MAKE_REG = 1 << 8
FS_MAKE_SOCK = 1 << 9
FS_MAKE_FIFO = 1 << 10
FS_MAKE_BLOCK = 1 << 11
FS_MAKE_SYM = 1 << 12
FS_REFER = 1 << 13
FS_TRUNCATE = 1 << 14
FS_IOCTL_DEV = 1 << 15
FS_RESOLVE_UNIX = 1 << 16

# Direitos de rede (conjunto separado, ABI 4). Nao misturar com bits de FS.
NET_BIND_TCP = 1 << 0
NET_CONNECT_TCP = 1 << 1

# Direito padrao de leitura de diretorio + arquivo para caminhos ro.
FS_RO_DIR = FS_READ_DIR | FS_READ_FILE

# Direito de gravacao limitada (propostas, memoria, logs).
FS_RW_DIR = (
    FS_READ_DIR
    | FS_READ_FILE
    | FS_WRITE_FILE
    | FS_MAKE_REG
    | FS_MAKE_DIR
    | FS_REMOVE_FILE
    | FS_REMOVE_DIR
)

# Direitos somente de arquivo (para ~/.config/agata/.env, que eh um arquivo;
# direitos de diretorio em arquivo dão EINVAL).
FS_RO_FILE = FS_READ_FILE | FS_EXECUTE


class _RulesetAttr(ctypes.Structure):
    """struct landlock_ruleset_attr: 2 x c_uint64 = 16 bytes (sem scoped,
    compatível com ABI < 6)."""
    _fields_ = [
        ("handled_access_fs", ctypes.c_uint64),
        ("handled_access_net", ctypes.c_uint64),
    ]


class _PathBeneathAttr(ctypes.Structure):
    """struct landlock_path_beneath_attr: packed, 12 bytes (u64 + s32)."""
    _pack_ = 1
    _fields_ = [
        ("allowed_access", ctypes.c_uint64),
        ("parent_fd", ctypes.c_int32),
    ]


_LIB = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6", use_errno=True)
_LIB.syscall.restype = ctypes.c_long
# Sem argtypes: syscall(2) é variadica; deixa o ctypes converter
# automaticamente. Ponteiros de struct passados como objetos c_void_p.


class LandlockError(RuntimeError):
    """Erro na criacao ou aplicacao de um ruleset Landlock."""


def _ptr(addr: int) -> ctypes.c_void_p:
    """Converte endereço de struct (int) para objeto c_void_p."""
    return ctypes.c_void_p(addr)


def _syscall_landlock(nr: int, *args) -> int:
    """Chama syscall(2) do landlock com até 6 argumentos após o nr.

    Ponteiros de struct devem ser passados como objetos c_void_p (via _ptr()).
    Inteiros (flags, tamanho, fd) são passados como ints puros.
    """
    padded = list(args) + [0, 0, 0, 0, 0, 0]
    ret = _LIB.syscall(nr, padded[0], padded[1], padded[2], padded[3], padded[4], padded[5])
    if ret < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))
    return ret


def _tentar_criar_ruleset(handled_access_fs: int, handled_access_net: int) -> Optional[int]:
    """Tenta criar um ruleset (flags=0). Retorna o fd ou None se o kernel rejeitar."""
    attr = _RulesetAttr(
        handled_access_fs=handled_access_fs,
        handled_access_net=handled_access_net,
    )
    try:
        return _syscall_landlock(
            __NR_landlock_create_ruleset,
            _ptr(ctypes.addressof(attr)),
            ctypes.sizeof(_RulesetAttr),
            0,
        )
    except OSError:
        return None


def ler_abi_versao() -> int:
    """Detecta a versão de ABI do Landlock em tempo de execucao.

    Tenta primeiro landlock_create_ruleset com LANDLOCK_CREATE_RULESET_VERSION.
    Se o kernel rejeitar (EINVAL), detecta por direitos:
    TRUNCATE (bit 14) existe so a partir da ABI 3; REFER (bit 13) so a partir da ABI 2;
    direitos basicos (bits 0..12) existem desde a ABI 1.
    """
    # Modo versao direto (especificacao do kernel).
    try:
        versao = _syscall_landlock(
            __NR_landlock_create_ruleset,
            None,  # modo versao: attr NULL e size 0 (senao EINVAL)
            0,
            LANDLOCK_CREATE_RULESET_VERSION,
        )
        if versao >= 1:
            return versao
    except OSError:
        pass

    # Fallback: probe de direitos por versao de ABI.
    if _tentar_criar_ruleset(FS_TRUNCATE, 0) is not None:
        return 3
    if _tentar_criar_ruleset(FS_REFER, 0) is not None:
        return 2
    if _tentar_criar_ruleset(FS_READ_FILE | FS_READ_DIR, 0) is not None:
        return 1
    raise LandlockError("kernel nao suporta Landlock (nenhum direito de FS aceito)")


def criar_ruleset(handled_access_fs: int, handled_access_net: int) -> int:
    """Cria um ruleset vazio e retorna o fd dele (flags=0, criacao normal)."""
    attr = _RulesetAttr(
        handled_access_fs=handled_access_fs,
        handled_access_net=handled_access_net,
    )
    return _syscall_landlock(
        __NR_landlock_create_ruleset,
        _ptr(ctypes.addressof(attr)),
        ctypes.sizeof(_RulesetAttr),
        0,
    )


def _abrir_caminho(path: str) -> int:
    """Abre um caminho com O_PATH. Tenta O_DIRECTORY primeiro (diretório),
    depois sem (arquivo ou diretório)."""
    try:
        return os.open(path, os.O_PATH | os.O_CLOEXEC | os.O_DIRECTORY)
    except IsADirectoryError:
        return os.open(path, os.O_PATH | os.O_CLOEXEC)
    except OSError:
        return os.open(path, os.O_PATH | os.O_CLOEXEC)


def add_path_rule(ruleset_fd: int, path: str, access: int) -> None:
    """Adiciona uma regra path-beneath (permitir `access` sobre `path`).

    `access` deve ser subconjunto de handled_access_fs do ruleset.
    """
    parent_fd = _abrir_caminho(path)
    try:
        attr = _PathBeneathAttr(allowed_access=access, parent_fd=parent_fd)
        _syscall_landlock(
            __NR_landlock_add_rule,
            ruleset_fd,
            LANDLOCK_RULE_PATH_BENEATH,
            _ptr(ctypes.addressof(attr)),
            0,  # flags (add_rule nao recebe tamanho)
        )
    finally:
        os.close(parent_fd)


def restrict_self(ruleset_fd: int, flags: int = 0) -> None:
    """Aplica o ruleset ao processo atual (restrict_self).

    Liga PR_SET_NO_NEW_PRIVS antes (exigido sem CAP_SYS_ADMIN).
    """
    if _LIB.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, "prctl(PR_SET_NO_NEW_PRIVS): " + os.strerror(errno))
    _syscall_landlock(
        __NR_landlock_restrict_self,
        ruleset_fd,
        flags,
    )


class RulesetProfile:
    """Perfil declarativo: nome + lista de (caminho, direitos-permitidos)."""

    def __init__(self, nome: str, regras: list[tuple[str, int]]):
        self.nome = nome
        self.regras = regras


def _fs_handled_por_abi(abi: int) -> int:
    """Todos os direitos de FS que a ABI conhece: o ruleset precisa "tratar"
    tudo, senao o que nao e tratado fica liberado (ex.: escrita)."""
    mascara = (1 << 13) - 1  # bits 0..12, ABI 1
    if abi >= 2:
        mascara |= FS_REFER
    if abi >= 3:
        mascara |= FS_TRUNCATE
    if abi >= 5:
        mascara |= FS_IOCTL_DEV
    if abi >= 9:
        mascara |= FS_RESOLVE_UNIX
    return mascara


# Direitos validos para quem nao e diretorio (senao add_rule da EINVAL).
_FS_SO_ARQUIVO = FS_EXECUTE | FS_WRITE_FILE | FS_READ_FILE | FS_TRUNCATE | FS_IOCTL_DEV


def compilar_regras(perfil: RulesetProfile) -> int:
    """Cria um ruleset com as regras do perfil e retorna o fd.

    O ruleset trata TODOS os direitos de FS da ABI: o que nao esta numa regra
    fica negado por omissao.
    """
    abi = ler_abi_versao()
    handled_fs = _fs_handled_por_abi(abi)
    handled_net = 0
    for _caminho, acesso in perfil.regras:
        if acesso & 0xFFFFFFFF00000000:
            handled_net |= acesso >> 32

    fd = criar_ruleset(handled_fs, handled_net)
    for caminho, acesso in perfil.regras:
        if acesso & 0xFFFFFFFF00000000:
            continue  # rede nao e path-beneath
        acesso &= handled_fs
        if not os.path.isdir(caminho):
            acesso &= _FS_SO_ARQUIVO
        add_path_rule(fd, caminho, acesso)
    return fd


def aplicar_perfil(perfil: RulesetProfile, flags: int = 0) -> int:
    """Cria ruleset do perfil e aplica ao processo atual. Retorna o fd do ruleset."""
    _ = ler_abi_versao()  # expoe a ABI em tempo de execucao
    fd = compilar_regras(perfil)
    restrict_self(fd, flags)
    return fd


# ---------------------------------------------------------------------------
# Perfis embutidos (allow-only; ~/.config/agata fora de TODOS).
# ---------------------------------------------------------------------------

def perfil_default(raiz_agata: str) -> RulesetProfile:
    """Leitura em agata; gravacao so em propostas, memoria, logs."""
    return RulesetProfile(
        "default",
        [
            (raiz_agata, FS_RO_DIR),
            (os.path.join(raiz_agata, "propostas"), FS_RW_DIR),
            (os.path.join(raiz_agata, "memoria"), FS_RW_DIR),
            (os.path.join(raiz_agata, "logs"), FS_RW_DIR),
        ],
    )


def perfil_bash_ro(raiz_agata: str) -> RulesetProfile:
    """Somente leitura em agata; sem gravacao."""
    return RulesetProfile("bash_ro", [(raiz_agata, FS_RO_DIR)])


def perfil_write(raiz_agata: str) -> RulesetProfile:
    """Leitura em agata; gravacao em propostas, memoria, logs."""
    return perfil_default(raiz_agata)


PERFIS = {
    "default": perfil_default,
    "bash_ro": perfil_bash_ro,
    "write": perfil_write,
}

__all__ = [
    "ler_abi_versao",
    "criar_ruleset",
    "add_path_rule",
    "restrict_self",
    "RulesetProfile",
    "compilar_regras",
    "aplicar_perfil",
    "perfil_default",
    "perfil_bash_ro",
    "perfil_write",
    "PERFIS",
    "LandlockError",
    "FS_RO_DIR",
    "FS_RW_DIR",
    "FS_RO_FILE",
    "NET_BIND_TCP",
    "NET_CONNECT_TCP",
]
