#!/usr/bin/env python3
"""
openvino-embeddings — endpoint de embedding na iGPU Intel via OpenVINO (Agata, Fase 2 / P2-03).

Modelo: intfloat/multilingual-e5-small (384 dim, PT-BR + multilingue), IR OpenVINO int8
exportado por optimum-cli (P2-03 passo 1). mean-pooling mascarado + L2-normalize.

Serve POST /embed em 127.0.0.1:20134 no formato OpenAI embeddings -- o OmniRoute / o grafo
consomem sem adaptador. **Zero vector DB** (invariante da Fase 6): so devolve o vetor.

e5 exige prefixo `query: ` ou `passage: `. O endpoint aceita `input_type` ("query" default
| "passage") e nao duplica se o texto ja vier prefixado.

Uso:
  embeddings_server.py                       # sobe o servico
  embeddings_server.py --selftest            # 2 frases proximas + 1 distante -> cossenos
  embeddings_server.py --selftest --device CPU
Env: OVE_MODEL_DIR, OVE_DEVICE (default GPU.0), OVE_BIND (default 127.0.0.1:20134)
"""
import io
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

HOME = os.path.expanduser("~")
MODEL_DIR = os.environ.get(
    "OVE_MODEL_DIR", os.path.join(HOME, ".cache/agata/openvino/embeddings/multilingual-e5-small-int8")
)
DEVICE = os.environ.get("OVE_DEVICE", "GPU.0")  # GPU.0 = iGPU Intel (GPU.1 seria a 4060)
BIND = os.environ.get("OVE_BIND", "127.0.0.1:20134")
MODEL_NAME = "multilingual-e5-small"
MAX_TOKENS = 512

_MODEL = None
_TOK = None
_DEVICE = None


def _load(device):
    global _MODEL, _TOK, _DEVICE
    if _MODEL is not None and _DEVICE == device:
        return
    from optimum.intel import OVModelForFeatureExtraction
    from transformers import AutoTokenizer
    t0 = time.time()
    _MODEL = OVModelForFeatureExtraction.from_pretrained(MODEL_DIR, device=device)
    _TOK = AutoTokenizer.from_pretrained(MODEL_DIR)
    _DEVICE = device
    sys.stderr.write(f"[emb] modelo carregado em {device} em {time.time()-t0:.1f}s ({MODEL_DIR})\n")
    sys.stderr.flush()


def _prefix(text, input_type):
    t = text.lstrip()
    if t.startswith("query:") or t.startswith("passage:"):
        return text
    return f"{input_type}: {text}"


def embed(texts, input_type="query", device=None):
    device = device or DEVICE
    _load(device)
    prepared = [_prefix(t, input_type) for t in texts]
    batch = _TOK(prepared, padding=True, truncation=True, max_length=MAX_TOKENS, return_tensors="pt")
    out = _MODEL(**batch)
    last = out.last_hidden_state
    last = last.numpy() if hasattr(last, "numpy") else np.asarray(last)
    mask = batch["attention_mask"].numpy()[..., None].astype(np.float32)
    pooled = (last * mask).sum(axis=1) / np.clip(mask.sum(axis=1), 1e-9, None)
    pooled = pooled / np.clip(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12, None)
    n_tokens = int(batch["attention_mask"].sum().item())
    return pooled.astype(np.float32), n_tokens


def _openai_response(vecs, n_tokens):
    return {
        "object": "list",
        "data": [
            {"object": "embedding", "index": i, "embedding": v.tolist()}
            for i, v in enumerate(vecs)
        ],
        "model": MODEL_NAME,
        "usage": {"prompt_tokens": n_tokens, "total_tokens": n_tokens},
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "device": _DEVICE or DEVICE, "model": MODEL_NAME, "dim": 384})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path not in ("/embed", "/v1/embeddings"):
            self._send(404, {"error": "not_found"})
            return
        n = int(self.headers.get("content-length", 0))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
            inp = req.get("input")
            if isinstance(inp, str):
                inp = [inp]
            if not inp or not isinstance(inp, list):
                self._send(400, {"error": "need 'input': str | [str]"})
                return
            itype = req.get("input_type", "query")
            vecs, ntok = embed(inp, input_type=itype)
            self._send(200, _openai_response(vecs, ntok))
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": type(e).__name__, "detail": str(e)})

    def log_message(self, *a):
        pass


def _cos(a, b):
    return float(np.dot(a, b))


def _selftest(device):
    pares = [
        "a âncora de sha detecta uma versão velha do canon",
        "o detector de defasagem compara o sha do commit com o remoto",
        "o gato dorme no sofá da sala o dia inteiro",
    ]
    t0 = time.time()
    v, ntok = embed(pares, input_type="query", device=device)
    dt = time.time() - t0
    print(json.dumps({
        "device": device, "dim": int(v.shape[1]), "n": len(pares),
        "proc_s": round(dt, 3), "tokens": ntok,
        "cos_proximas_0_1": round(_cos(v[0], v[1]), 4),
        "cos_distante_0_2": round(_cos(v[0], v[2]), 4),
    }, ensure_ascii=False, indent=2))
    ok = _cos(v[0], v[1]) > _cos(v[0], v[2])
    print("OK" if ok else "FALHA", "-- frases próximas mais parecidas que a distante" if ok else "-- margem invertida")
    return 0 if ok else 1


def main():
    args = sys.argv[1:]
    device = DEVICE
    if "--device" in args:
        i = args.index("--device")
        device = args[i + 1]
        del args[i:i + 2]
    if args and args[0] == "--selftest":
        sys.exit(_selftest(device))
    host, port = BIND.split(":")
    _load(device)
    srv = ThreadingHTTPServer((host, int(port)), Handler)
    sys.stderr.write(f"[emb] ouvindo em http://{host}:{port}  device={device}\n")
    sys.stderr.flush()
    srv.serve_forever()


if __name__ == "__main__":
    main()
