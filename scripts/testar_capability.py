"""Contraprovas offline da capability Ed25519 entre o chamador e o executor."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from redesign.mcp.capability import (
    canonical_json,
    digest_arguments,
    verificar_capability,
)
from redesign.router import seth_escriba


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="agata-cap-")
        self.root = Path(self.tmp.name)
        self.private_key_file = self.root / "private.pem"
        self.public_key_file = self.root / "public.pem"
        self.private_key = Ed25519PrivateKey.generate()
        self.private_key_file.write_bytes(self.private_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()))
        self.private_key_file.chmod(0o600)
        self.public_key_file.write_bytes(self.private_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        self.public_key_file.chmod(0o644)
        self.db = self.root / "nonce" / "used.sqlite3"
        self.args = {"texto": "revisado", "canal_id": "123"}
        self.token = self.issue(self.args)

    def tearDown(self):
        self.tmp.cleanup()

    def issue(self, args, **changes):
        claims = {
            "iss": "librechat-agata",
            "aud": "discord",
            "tool": "enviar_mensagem",
            "sub": "user-1",
            "args_sha256": digest_arguments(args),
            "iat": 1000,
            "exp": 1060,
            "jti": "nonce-" + str(changes.pop("nonce", "1")),
            **changes,
        }
        encoded = base64.urlsafe_b64encode(canonical_json(claims)).decode().rstrip("=")
        signature = self.private_key.sign(encoded.encode())
        sig = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        return encoded + "." + sig

    def issue_from_librechat_node(self, args, **changes):
        claims = {
            "iss": "librechat-agata", "aud": "discord", "tool": "enviar_mensagem",
            "sub": "user-1", "args_sha256": digest_arguments(args),
            "iat": 1000, "exp": 1060, "jti": "node-signature",
            **changes,
        }
        encoded = base64.urlsafe_b64encode(canonical_json(claims)).decode().rstrip("=")
        script = (
            "const c=require('node:crypto'),f=require('node:fs');"
            "const k=c.createPrivateKey(f.readFileSync(process.argv[1]));"
            "process.stdout.write(c.sign(null,Buffer.from(process.argv[2],'ascii'),k).toString('base64url'));"
        )
        signature = subprocess.check_output(
            ["node", "-e", script, str(self.private_key_file), encoded], text=True
        )
        return encoded + "." + signature

    def verify(self, token=None, *, audience="discord", tool="enviar_mensagem",
               arguments=None, now=1030):
        return verificar_capability(
            token or self.token, audience=audience, tool=tool,
            arguments=self.args if arguments is None else arguments,
            now=now, public_key_file=self.public_key_file, nonce_db=self.db,
        )

    def test_valid_call_consumes_one_time_nonce(self):
        claims = self.verify()
        self.assertEqual(claims["sub"], "user-1")
        with self.assertRaises(PermissionError):
            self.verify()

    def test_accepts_signature_emitted_by_librechat_node(self):
        token = self.issue_from_librechat_node(self.args)
        claims = self.verify(token)
        self.assertEqual(claims["jti"], "node-signature")

    def test_rejects_wrong_service_operation_arguments_and_expiry(self):
        cases = [
            dict(audience="browser"),
            dict(tool="preencher"),
            dict(arguments={"texto": "alterado", "canal_id": "123"}),
            dict(now=1060),
        ]
        for index, kwargs in enumerate(cases):
            with self.subTest(kwargs=kwargs):
                token = self.issue(self.args, nonce=f"bad-{index}")
                with self.assertRaises(PermissionError):
                    self.verify(token, **kwargs)

    def test_rejects_modified_signature_and_overlong_ttl(self):
        encoded, signature = self.token.split(".", 1)
        changed_signature = ("A" if signature[0] != "A" else "B") + signature[1:]
        with self.assertRaises(PermissionError):
            self.verify(encoded + "." + changed_signature)
        token = self.issue(self.args, exp=1200, nonce="long")
        with self.assertRaises(PermissionError):
            self.verify(token)

    def test_rejects_key_file_with_broad_permissions(self):
        self.public_key_file.chmod(0o666)
        with self.assertRaises(PermissionError):
            self.verify(self.issue(self.args, nonce="bad-key"))
        self.assertEqual(stat.S_IMODE(self.public_key_file.stat().st_mode), 0o666)

    def test_escriba_http_requires_and_consumes_capability(self):
        memories = self.root / "MEMÓRIAS.md"
        diary = self.root / "SETH-DIARIO.md"
        original = "topo\n<!-- ENTRADAS-NOVAS:AQUI -- não editar -->\n\nfim\n"
        memories.write_text(original, encoding="utf-8")
        database = self.root / "nonces" / "used.sqlite3"
        payload = {"titulo": "teste", "corpo": "conteúdo autorizado"}
        now = int(time.time())
        token = self.issue(payload, aud="escriba", tool="memoria_acrescentar", nonce="http",
                           iat=now, exp=now + 60)
        with patch.object(seth_escriba, "MEMORIAS", memories), patch.object(seth_escriba, "DIARIO", diary), \
             patch.dict(os.environ, {"AGATA_APPROVAL_PUBLIC_KEY_FILE": str(self.public_key_file),
                                     "AGATA_APPROVAL_NONCE_DB": str(database)}):
            server = seth_escriba.ThreadingHTTPServer(("127.0.0.1", 0), seth_escriba._H)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f"http://127.0.0.1:{server.server_port}/memoria"
            body = json.dumps(payload).encode()

            def post(auth=None):
                headers = {"Content-Type": "application/json"}
                if auth:
                    headers["Authorization"] = f"Bearer {auth}"
                request = urllib.request.Request(url, data=body, headers=headers)
                try:
                    with urllib.request.urlopen(request, timeout=3) as response:
                        return response.status
                except urllib.error.HTTPError as error:
                    code = error.code
                    error.close()
                    return code

            try:
                self.assertEqual(post(), 403)
                self.assertEqual(memories.read_text(encoding="utf-8"), original)
                self.assertEqual(post(token), 200)
                after = memories.read_text(encoding="utf-8")
                self.assertIn("conteúdo autorizado", after)
                self.assertEqual(post(token), 403)
                self.assertEqual(memories.read_text(encoding="utf-8"), after)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
