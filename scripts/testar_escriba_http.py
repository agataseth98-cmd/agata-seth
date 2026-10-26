"""Provas HTTP reais do Escriba, isoladas em diretório temporário e porta efêmera."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from redesign.mcp.capability import canonical_json, digest_arguments
from redesign.router import seth_escriba as escriba


def _signed(private_key, audience: str, tool: str, arguments: dict, jti: str) -> str:
    now = int(time.time())
    claims = {
        "iss": "librechat-agata", "aud": audience, "tool": tool,
        "sub": "fixture-user", "args_sha256": digest_arguments(arguments),
        "iat": now, "exp": now + 60, "jti": jti,
    }
    encoded = base64.urlsafe_b64encode(canonical_json(claims)).decode().rstrip("=")
    signature = private_key.sign(encoded.encode("ascii"))
    return encoded + "." + base64.urlsafe_b64encode(signature).decode().rstrip("=")


def _post(url: str, payload: dict, *, project_token: str | None = None,
          capability: str | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if project_token is not None:
        headers["X-Agata-Project-Token"] = project_token
    if capability is not None:
        headers["Authorization"] = f"Bearer {capability}"
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read())
        finally:
            error.close()


def _report(label: str, status: int, condition: bool, detail: str) -> None:
    result = "PASSOU" if condition else "FALHOU"
    print(f"{label}: HTTP {status}; {detail}: {result}")
    if not condition:
        raise AssertionError(f"{label}: {detail}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="agata-escriba-http-") as temporary:
        root = Path(temporary)
        project = root / "project"
        project.mkdir(mode=0o700)
        config = root / ".config/agata/projetos"
        config.mkdir(parents=True, mode=0o700)
        project_token = "fixture-project-token-0123456789-abcdefghijklmnopqrstuvwxyz"
        token_path = config / (hashlib.sha256(str(project.resolve()).encode()).hexdigest() + ".token")
        token_path.write_text(project_token + "\n", encoding="utf-8")
        token_path.chmod(0o600)
        private_key = Ed25519PrivateKey.generate()
        public_key_path = root / "approval-public.pem"
        public_key_path.write_bytes(private_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        public_key_path.chmod(0o644)
        memories = root / "MEMÓRIAS.md"
        memories_before = "topo\n<!-- ENTRADAS-NOVAS:AQUI -- fixture -->\n\nfim\n"
        memories.write_text(memories_before, encoding="utf-8")
        diary = root / "SETH-DIARIO.md"
        diary_before = "# diário fixture\n\n<!-- ENTRADAS-NOVAS:AQUI -- fixture -->\n\n"
        diary.write_text(diary_before, encoding="utf-8")
        nonce_db = root / ".cache/agata/approval-capabilities/used.sqlite3"

        sys.path.insert(0, str(ROOT / "redesign" / "router"))
        import cache_conselho  # (M2) o espelho do /diario vai para um cache temporário, nunca o real
        cache_teste = root / "cache-conselho" / "cache.jsonl"
        with patch.object(escriba, "MEMORIAS", memories), patch.object(escriba, "DIARIO", diary), \
             patch.object(cache_conselho, "ARQ", cache_teste), \
             patch.object(escriba.Path, "home", return_value=root), \
             patch.dict(os.environ, {
                 "AGATA_PROJETO_RAIZ": str(project),
                 "AGATA_APPROVAL_PUBLIC_KEY_FILE": str(public_key_path),
                 "AGATA_APPROVAL_NONCE_DB": str(nonce_db),
             }):
            server = escriba.ThreadingHTTPServer(("127.0.0.1", 0), escriba._H)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                before = memories.read_bytes()
                status, _ = _post(base + "/memoria", {"titulo": "fixture", "corpo": "conteúdo limpo"})
                _report("sem token", status, status == 403 and memories.read_bytes() == before,
                        "MEMÓRIAS intacta")

                status, _ = _post(base + "/memoria", {"titulo": "fixture", "corpo": "conteúdo limpo"},
                                  project_token="x" * len(project_token))
                _report("token errado", status, status == 403 and memories.read_bytes() == before,
                        "MEMÓRIAS intacta")

                status, response = _post(base + "/memoria", {
                    "titulo": "fixture", "corpo": "ghp_" + "x" * 36,
                }, project_token=project_token)
                _report("texto com segredo", status,
                        status == 400 and "nada foi gravado" in response.get("error", "")
                        and memories.read_bytes() == before,
                        "segredo recusado e MEMÓRIAS intacta")

                token_path.chmod(0o644)
                status, _ = _post(base + "/memoria", {"titulo": "fixture", "corpo": "conteúdo limpo"},
                                  project_token=project_token)
                _report("token 0644", status, status == 403 and memories.read_bytes() == before,
                        "token inseguro recusado e MEMÓRIAS intacta")
                token_path.chmod(0o600)

                with patch.dict(os.environ, {}, clear=True):
                    status, _ = _post(base + "/memoria", {"titulo": "fixture", "corpo": "conteúdo limpo"},
                                      project_token=project_token)
                _report("raiz ausente", status, status == 403 and memories.read_bytes() == before,
                        "escrita recusada e MEMÓRIAS intacta")

                memory_payload = {"titulo": "regressão fixture", "corpo": "corpo limpo de teste"}
                memory_cap = _signed(private_key, "escriba", "memoria_acrescentar", memory_payload, "memory-1")
                status, response = _post(base + "/memoria", memory_payload,
                                         project_token=project_token, capability=memory_cap)
                memory_after = memories.read_text(encoding="utf-8")
                _report("regressão /memoria", status,
                        status == 200 and response.get("ok") is True
                        and "corpo limpo de teste" in memory_after
                        and memory_after.startswith("topo\n<!-- ENTRADAS-NOVAS:AQUI -- fixture -->\n\n")
                        and memory_after.endswith("\n\nfim\n"),
                        "gravação e verificação pós-escrita passaram")

                diary_payload = {"texto": "entrada limpa de teste"}
                diary_cap = _signed(private_key, "escriba", "diario_anotar", diary_payload, "diary-1")
                status, response = _post(base + "/diario", diary_payload,
                                         project_token=project_token, capability=diary_cap)
                diary_after = diary.read_text(encoding="utf-8")
                _report("regressão /diario", status,
                        status == 200 and response.get("ok") is True
                        and "entrada limpa de teste" in diary_after
                        and diary_after.startswith("# diário fixture\n\n<!-- ENTRADAS-NOVAS:AQUI -- fixture -->\n"),
                        "gravação e verificação pós-escrita passaram")
                _report("espelho do /diario no cache do Conselho (M2)", status,
                        (response.get("cache_conselho") or {}).get("ok") is True and cache_teste.exists()
                        and "entrada limpa de teste" in cache_teste.read_text(encoding="utf-8"),
                        "a anotação entrou no cache temporário, com autor Seth")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
