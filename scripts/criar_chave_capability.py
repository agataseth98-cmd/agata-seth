#!/usr/bin/env python3
"""Cria uma chave local para capabilities; nunca imprime nem sobrescreve a chave."""
from __future__ import annotations

import os
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def main() -> int:
    pasta = Path.home() / ".config/agata"
    privado = pasta / "approval-capability-private.pem"
    publico = pasta / "approval-capability-public.pem"
    pasta.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent = pasta.stat()
    if parent.st_uid != os.getuid() or parent.st_mode & 0o077:
        print("diretório da chave deve pertencer ao usuário e ter modo 0700 ou mais restrito")
        return 2
    nonce_dir = Path.home() / ".cache/agata/approval-capabilities"
    nonce_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    nonce_stat = nonce_dir.stat()
    if nonce_stat.st_uid != os.getuid() or nonce_stat.st_mode & 0o077:
        print("diretório de nonces deve pertencer ao usuário e ter modo 0700 ou mais restrito")
        return 2
    if privado.exists() or publico.exists():
        print("par de chaves já existe parcialmente ou por completo; nenhuma alteração feita")
        return 1
    key = Ed25519PrivateKey.generate()
    private_pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption())
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW
    fds = []
    criados = []
    try:
        fds.append(os.open(privado, flags, 0o600))
        criados.append(privado)
        fds.append(os.open(publico, flags, 0o644))
        criados.append(publico)
    except FileExistsError:
        for fd in fds:
            os.close(fd)
        for path in criados:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        print("par de chaves já existe; nenhuma alteração feita")
        return 1
    try:
        os.write(fds[0], private_pem)
        os.fsync(fds[0])
        os.write(fds[1], public_pem)
        os.fsync(fds[1])
    finally:
        for fd in fds:
            os.close(fd)
    print("par Ed25519 criado; privada 0600, pública 0644; conteúdo não exibido")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
