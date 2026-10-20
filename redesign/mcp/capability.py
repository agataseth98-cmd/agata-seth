"""Verificação de capabilities efêmeras emitidas após aprovação humana.

LibreChat assina com Ed25519; executores locais só recebem a chave pública.
O token autentica uma única chamada, argumentos, usuário, expiração e nonce.
"""
from __future__ import annotations

import hashlib
import json
import os
import base64
import sqlite3
import stat
import time
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

PUBLIC_KEY_FILE = Path(os.environ.get(
    "AGATA_APPROVAL_PUBLIC_KEY_FILE",
    str(Path.home() / ".config/agata/approval-capability-public.pem"),
))
NONCE_DB = Path(os.environ.get(
    "AGATA_APPROVAL_NONCE_DB",
    str(Path.home() / ".cache/agata/approval-capabilities/used.sqlite3"),
))
MAX_TTL = 90


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest_arguments(arguments: object) -> str:
    return hashlib.sha256(canonical_json(arguments)).hexdigest()


def _public_key(path: Path = PUBLIC_KEY_FILE) -> Ed25519PublicKey:
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        st = os.fstat(fd)
        if (not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid()
                or stat.S_IMODE(st.st_mode) & 0o022 or st.st_nlink != 1):
            raise PermissionError("arquivo de chave pública de capability inseguro")
        data = os.read(fd, 4097).strip()
        if len(data) < 64 or len(data) > 4096:
            raise PermissionError("chave pública de capability ausente ou tamanho inválido")
        key = serialization.load_pem_public_key(data)
        if not isinstance(key, Ed25519PublicKey):
            raise PermissionError("tipo de chave de capability inválido")
        return key
    finally:
        os.close(fd)


def verificar_capability(token: str | None, *, audience: str, tool: str,
                         arguments: object, now: int | None = None,
                         public_key_file: Path = PUBLIC_KEY_FILE,
                         nonce_db: Path = NONCE_DB) -> dict:
    """Valida e consome um token; falha fechada com PermissionError."""
    try:
        encoded, signature = (token or "").split(".", 1)
        payload_bytes = base64.b64decode(
            encoded + "=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
        claims = json.loads(payload_bytes)
        if not isinstance(claims, dict):
            raise ValueError("claims inválidos")
        raw_signature = base64.b64decode(
            signature + "=" * (-len(signature) % 4), altchars=b"-_", validate=True)
        _public_key(public_key_file).verify(raw_signature, encoded.encode("ascii"))
        instante = int(time.time()) if now is None else int(now)
        iat, exp = int(claims["iat"]), int(claims["exp"])
        if iat > instante + 5 or exp <= instante or exp - iat > MAX_TTL:
            raise ValueError("capability expirada ou fora da janela")
        if (claims.get("iss") != "librechat-agata"
                or claims.get("aud") != audience or claims.get("tool") != tool
                or not isinstance(claims.get("sub"), str)
                or claims.get("args_sha256") != digest_arguments(arguments)
                or not isinstance(claims.get("jti"), str)
                or not claims["jti"]):
            raise ValueError("capability não corresponde à chamada")
        nonce_db.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        parent_stat = nonce_db.parent.stat()
        if parent_stat.st_uid != os.getuid() or parent_stat.st_mode & 0o077:
            raise PermissionError("diretório de nonces inseguro")
        if nonce_db.exists() or nonce_db.is_symlink():
            db_stat = nonce_db.lstat()
            if (not stat.S_ISREG(db_stat.st_mode) or db_stat.st_uid != os.getuid()
                    or stat.S_IMODE(db_stat.st_mode) & 0o077 or db_stat.st_nlink != 1):
                raise PermissionError("banco de nonces inseguro")
        with sqlite3.connect(nonce_db, timeout=5, isolation_level=None) as db:
            os.chmod(nonce_db, 0o600)
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("CREATE TABLE IF NOT EXISTS used (jti TEXT PRIMARY KEY, exp INTEGER NOT NULL)")
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM used WHERE exp <= ?", (instante,))
            try:
                db.execute("INSERT INTO used(jti, exp) VALUES (?, ?)",
                           (claims["jti"], exp))
            except sqlite3.IntegrityError as e:
                db.rollback()
                raise ValueError("capability já utilizada") from e
            db.commit()
        return claims
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError,
            InvalidSignature,
            UnicodeError, sqlite3.Error) as e:
        raise PermissionError(f"capability rejeitada: {type(e).__name__}") from None
