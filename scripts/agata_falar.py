#!/usr/bin/env python3
"""agata_falar.py -- lê um texto em voz alta com a VOZ DO SISTEMA (piper-tts local, modelo pt_BR-agata-last).

Decisão do Humano, 03/11/2026: quando um modelo fala, a voz é a do sistema, sem negociação. Por isso o script
recusa falar se o piper-tts carregou outro modelo (ex.: o de reserva pt_BR-faber-medium) ou se não responde:
dizer "não falei" é correto, falar com outra voz não é. Nada sai da Máquina: só 127.0.0.1, nunca TTS externo.

Fluxo: prepara o texto para fala (sem código, tabela, caminho, URL nem marcação), liga o piper-tts.service se
estiver parado (e o desliga depois, se foi este script que ligou), pede o áudio por parágrafo e toca com o
primeiro player local que existir (mpv, paplay, pw-play, aplay, ffplay). Não ouve o resultado: só confirma
que o serviço respondeu e o player terminou sem erro.

Uso:
  agata_falar.py [--texto T | --arquivo F | (stdin)] [--sem-tocar] [--salvar-wav DIR] [--manter-servico]
  agata_falar.py --preparar [--texto T | --arquivo F]     (só mostra o texto que seria falado)
  agata_falar.py --selftest
Exit 0 = falou (ou preparou); 2 = uso; 3 = a voz do sistema não está disponível (nada foi falado); 4 = sem player.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

PORTA = int(os.environ.get("PIPER_TTS_PORT", "8890"))
BASE = f"http://127.0.0.1:{PORTA}"
UNIDADE = "piper-tts.service"
MODELO_DO_SISTEMA = "pt_BR-agata"
PLAYERS = (("mpv", ["--no-video", "--really-quiet"]), ("paplay", []), ("pw-play", []), ("aplay", ["-q"]), ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]))
MAX_PARAGRAFO = 1500
MAX_TOTAL = 12000
SIGLAS = {"SDD": "S-D-D", "LLM": "L-L-M", "LLMs": "L-L-Ms", "CI": "C-I", "GPU": "G-P-U", "API": "A-P-I", "MCP": "M-C-P", "RAG": "R-A-G",
          "TTS": "T-T-S", "PR": "pull request", "PRs": "pull requests", "CLI": "C-L-I", "P-8": "P-oito"}


def preparar(texto: str) -> str:
    """Texto escrito -> texto para falar: sem código, tabela, caminho, URL, marcação; siglas soletradas."""
    t = re.sub(r"```.*?```", " ", texto, flags=re.S)
    t = re.sub(r"`([^`\n]*)`", lambda m: "" if re.search(r"[/\\._]", m.group(1)) and " " not in m.group(1) else m.group(1), t)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    linhas = []
    for ln in t.splitlines():
        s = ln.strip()
        if not s or re.fullmatch(r"[|\-: ]+", s) or s.startswith("|"):
            linhas.append("")
            continue
        s = re.sub(r"^#+\s*", "", s)
        s = re.sub(r"^[-*•]\s+", "", s)
        s = re.sub(r"^\d+[.)]\s+", "", s)
        s = re.sub(r"^>\s*", "", s)
        s = re.sub(r"[*~]+", "", s)
        s = re.sub(r"(?<![A-Za-z0-9])_+|_+(?![A-Za-z0-9])", "", s)  # itálico com underscore, sem comer pt_BR
        s = " ".join(w for w in s.split() if not re.search(r"[A-Za-z0-9]/[A-Za-z0-9._-]+|\.(py|sh|md|js|json|yml|yaml|txt|service|diff)\b", w))
        linhas.append(s)
    t = "\n".join(linhas)
    for sigla, fala in SIGLAS.items():
        t = re.sub(rf"(?<![A-Za-z0-9-]){re.escape(sigla)}(?![A-Za-z0-9-])", fala, t)
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def paragrafos(texto: str) -> list[str]:
    saida = []
    for bloco in re.split(r"\n\s*\n", texto):
        bloco = bloco.replace("\n", " ").strip()
        while len(bloco) > MAX_PARAGRAFO:
            corte = bloco.rfind(". ", 0, MAX_PARAGRAFO)
            corte = corte + 1 if corte > 200 else MAX_PARAGRAFO
            saida.append(bloco[:corte].strip()); bloco = bloco[corte:].strip()
        if bloco:
            saida.append(bloco)
    return saida


def _http(caminho: str, corpo: bytes | None = None, timeout: int = 60) -> tuple[bytes, dict]:
    req = urllib.request.Request(BASE + caminho, data=corpo, headers={"Content-Type": "application/json"} if corpo else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), dict(r.headers)


def saude() -> dict | None:
    try:
        return json.loads(_http("/health", timeout=3)[0])
    except (urllib.error.URLError, OSError, ValueError):
        return None


def garantir_servico() -> tuple[dict | None, bool]:
    """(saúde, ligamos_nós). Liga a unidade se estiver parada e espera ~30 s."""
    h = saude()
    if h:
        return h, False
    systemctl = os.environ.get("AGATA_FALAR_SYSTEMCTL", "systemctl")
    try:
        subprocess.run([systemctl, "--user", "start", UNIDADE], capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None, False
    for _ in range(30):
        h = saude()
        if h:
            return h, True
        time.sleep(1)
    return None, True


def desligar() -> None:
    try:
        subprocess.run([os.environ.get("AGATA_FALAR_SYSTEMCTL", "systemctl"), "--user", "stop", UNIDADE], capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        pass


def player() -> list[str] | None:
    for nome, args in PLAYERS:
        caminho = shutil.which(nome)
        if caminho:
            return [caminho, *args]
    return None


def falar(texto: str, tocar: bool = True, salvar: Path | None = None, manter: bool = False) -> int:
    fala = preparar(texto)
    if not fala:
        print("nada para falar depois de preparar o texto", file=sys.stderr)
        return 2
    if len(fala) > MAX_TOTAL:
        print(f"texto falado com {len(fala)} caracteres; o limite é {MAX_TOTAL}: fale o resumo", file=sys.stderr)
        return 2
    tocador = player() if tocar else None
    if tocar and tocador is None:
        print("sem player de áudio local (mpv, paplay, pw-play, aplay, ffplay): não falei", file=sys.stderr)
        return 4
    h, ligamos = garantir_servico()
    try:
        if not h:
            print("a voz do sistema (piper-tts) não respondeu: NÃO falei", file=sys.stderr)
            return 3
        if not str(h.get("model", "")).startswith(MODELO_DO_SISTEMA):
            print(f"o piper-tts carregou '{h.get('model')}', não a voz do sistema ({MODELO_DO_SISTEMA}): NÃO falei com outra voz", file=sys.stderr)
            return 3
        pasta = Path(salvar) if salvar else Path(tempfile.mkdtemp(prefix="agata-voz-"))
        pasta.mkdir(parents=True, exist_ok=True)
        for i, par in enumerate(paragrafos(fala), 1):
            corpo = json.dumps({"model": "tts-1", "input": par, "voice": "agata", "response_format": "wav"}).encode()
            audio, _cab = _http("/v1/audio/speech", corpo, timeout=300)
            arq = pasta / f"fala-{i:02d}.wav"
            arq.write_bytes(audio)
            if tocador:
                if subprocess.run([*tocador, str(arq)], check=False).returncode != 0:
                    print(f"o player falhou no trecho {i}", file=sys.stderr)
                    return 4
        if not salvar:
            shutil.rmtree(pasta, ignore_errors=True)
        return 0
    except (urllib.error.URLError, OSError) as exc:
        print(f"falha ao gerar o áudio: {str(exc)[:120]}: não falei", file=sys.stderr)
        return 3
    finally:
        if ligamos and not manter:
            desligar()


def _selftest() -> int:
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    global BASE, PLAYERS
    falhou = 0
    def conferir(nome, cond):
        nonlocal falhou
        print(("PASS " if cond else "FALHA ") + nome); falhou += 0 if cond else 1
    p = preparar("# Título\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\nVeja `scripts/x.py` e **negrito** em https://exemplo.com e [link](http://x.y).\n\n```\ncodigo()\n```\n\nO SDD usa PR e o L-L-M. 1. item um")
    conferir("preparar tira código, tabela, caminho, URL e marcação", all(x not in p for x in ("```", "|", "scripts/x.py", "http", "**", "codigo()")))
    conferir("preparar soletra siglas e mantém o texto", "S-D-D" in p and "pull request" in p and "Título" in p and "negrito" in p)
    conferir("preparar preserva underscore dentro de nome (pt_BR)", "pt_BR-agata" in preparar("modelo pt_BR-agata-last e _itálico_"))
    conferir("preparar não toca em palavra comum que contém sigla", preparar("O CIRCO e a APIA") == "O CIRCO e a APIA")
    longo = ("Frase um. " * 400).strip()
    conferir("parágrafo longo é cortado em pedaços de até o limite", all(len(x) <= MAX_PARAGRAFO for x in paragrafos(longo)) and len(paragrafos(longo)) >= 3)
    estado = {"modelo": "pt_BR-agata-last.onnx", "pedidos": 0}
    class Falso(BaseHTTPRequestHandler):
        def do_GET(self):
            corpo = json.dumps({"status": "ok", "model": estado["modelo"]}).encode()
            self.send_response(200); self.send_header("Content-Length", str(len(corpo))); self.end_headers(); self.wfile.write(corpo)
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"])); estado["pedidos"] += 1
            self.send_response(200); self.send_header("Content-Length", "4"); self.end_headers(); self.wfile.write(b"RIFF")
        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Falso); threading.Thread(target=srv.serve_forever, daemon=True).start()
    BASE = f"http://127.0.0.1:{srv.server_address[1]}"
    PLAYERS = (("true", []),)
    conferir("fala com a voz do sistema e toca (player falso)", falar("Olá. Teste de voz.", tocar=True) == 0 and estado["pedidos"] == 1)
    estado["modelo"] = "pt_BR-faber-medium.onnx"; estado["pedidos"] = 0
    conferir("recusa falar com outra voz (modelo de reserva)", falar("Olá.", tocar=False) == 3 and estado["pedidos"] == 0)
    estado["modelo"] = "pt_BR-agata-last.onnx"
    PLAYERS = (("comando-que-nao-existe-xyz", []),)
    conferir("sem player local diz que não falou", falar("Olá.", tocar=True) == 4)
    d = Path(tempfile.mkdtemp())
    conferir("--salvar-wav grava um arquivo por parágrafo", falar("Um.\n\nDois.", tocar=False, salvar=d) == 0 and len(list(d.glob("fala-*.wav"))) == 2)
    srv.shutdown(); srv.server_close()
    BASE = "http://127.0.0.1:9"
    os.environ["AGATA_FALAR_SYSTEMCTL"] = "true"
    conferir("serviço fora do ar: NÃO fala e o código é 3", falar("Olá.", tocar=False) == 3)
    return 1 if falhou else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    def opt(nome):
        return argv[argv.index(nome) + 1] if nome in argv and argv.index(nome) + 1 < len(argv) else None
    if "--texto" in argv:
        texto = opt("--texto") or ""
    elif "--arquivo" in argv:
        try:
            texto = Path(opt("--arquivo") or "").read_text(encoding="utf-8")
        except OSError as exc:
            print(f"não consegui ler o arquivo: {exc}", file=sys.stderr)
            return 2
    elif not sys.stdin.isatty():
        texto = sys.stdin.read()
    else:
        print(__doc__, file=sys.stderr)
        return 2
    if "--preparar" in argv:
        print(preparar(texto))
        return 0
    salvar = Path(opt("--salvar-wav")) if opt("--salvar-wav") else None
    return falar(texto, tocar="--sem-tocar" not in argv, salvar=salvar, manter="--manter-servico" in argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
