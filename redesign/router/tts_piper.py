#!/usr/bin/env python3
"""Shim OpenAI-compat pra Piper TTS -- voz pt-BR local, rápida, sem GPU.

Motivo (MEMÓRIAS (387)): as vozes pt-BR do Kokoro (`pf_dora` etc.) não têm
nota de qualidade no model card oficial e pronunciam português errado
("transcreve errado", relato do Humano no teste da Seth). Kokoro seguia em
CPU numa máquina com RTX 4060 -> também lento. Piper `pt_BR-faber-medium`
(corpus CML-TTS, treino real de pt-BR) resolve os dois: RTF ~0,13 em CPU,
zero VRAM, então não briga com o cérebro local da Seth (`qwen3.5-9b-64k`,
que ocupa ~90% da 4060 quando gera).

Fala só o dialeto OpenAI que o LibreChat usa:
  POST /v1/audio/speech  {input, voice?, response_format?, speed?}
  GET  /health
  GET  /v1/models

Zero dependência além do que já está no venv do Piper + ffmpeg (conversão de
formato). Um processo `piper` por requisição (curto -- o modelo carrega em
~0,2s). NÃO faz streaming: devolve o buffer inteiro. Loopback só.

Env:
  PIPER_TTS_PORT   porta (default 8890)
  PIPER_TTS_HOST   host  (default 127.0.0.1 -- não expor)
  PIPER_MODEL      caminho do .onnx (default: voices/pt_BR-agata-last.onnx se existir -- a voz treinada da
                   Agata, ver tts-piper/instalar-agata.sh --, senão voices/pt_BR-faber-medium.onnx)
  PIPER_TRATAMENTO sistema (default) | off. Tratamento de áudio "sistema" depois da síntese (ffmpeg);
                   sem ffmpeg ou com erro, a voz sai crua e o cabeçalho X-Agata-Tratamento diz por quê
  PIPER_VELOCIDADE velocidade base da fala (default 0.88 = ritmo de reunião esclarecedora; 1.0 = natural do modelo)
  PIPER_PYTHON     python do venv do Piper (default: tts-piper/.venv/bin/python ao lado deste arquivo)
"""
import json
import os
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "scripts"))
from http_seguro import ler_corpo_limitado, ServidorConcorrenciaLimitada  # noqa: E402
HOST = os.environ.get("PIPER_TTS_HOST", "127.0.0.1")
PORT = int(os.environ.get("PIPER_TTS_PORT", "8890"))


def _modelo_padrao(voices=None):
    """A voz treinada da Agata se estiver instalada; senão a genérica. Remover o arquivo = voltar."""
    voices = voices or os.path.join(AQUI, "tts-piper", "voices")
    agata = os.path.join(voices, "pt_BR-agata-last.onnx")
    return agata if os.path.exists(agata) else os.path.join(voices, "pt_BR-faber-medium.onnx")


MODEL = os.environ.get("PIPER_MODEL") or _modelo_padrao()
PYTHON = os.environ.get("PIPER_PYTHON", os.path.join(AQUI, "tts-piper", ".venv", "bin", "python"))
FFMPEG = shutil.which("ffmpeg")

# Tratamento "sistema" (timbre `agata-sistema-tratado` do PROJETO, "Personalidade da Seth", com o eco
# "jarvis" escolhido pelo Humano em 16/10/2026: dobra metálica leve + 3 ecos curtos de 25, 50 e 90 ms).
# Custo medido: ~0,05 s para 3 s de áudio e 0,10 s para 12,8 s (RTF 0,008), perto de nada diante do RTF
# 0,13 do Piper. O `rubberband=tempo=0.95` alonga a fala em ~6%.
CADEIA_SISTEMA = (
    "rubberband=tempo=0.95,highpass=f=90,equalizer=f=2800:t=q:w=1.0:g=2.5,highshelf=g=-2:f=9000,"
    "chorus=0.7:0.9:35|55:0.3|0.25:0.25|0.4:2|1.5,aecho=0.8:0.7:25|50|90:0.3|0.2|0.12,"
    "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80"
)
TRATAMENTO = os.environ.get("PIPER_TRATAMENTO", "sistema").strip().lower()
try:
    VELOCIDADE_BASE = float(os.environ.get("PIPER_VELOCIDADE", "0.88"))
except ValueError:
    VELOCIDADE_BASE = 0.88
if not 0.5 <= VELOCIDADE_BASE <= 1.5:
    VELOCIDADE_BASE = 0.88

# sample_rate vem do .json ao lado do modelo (Piper grava isso lá).
try:
    with open(MODEL + ".json", encoding="utf-8") as f:
        SAMPLE_RATE = int(json.load(f)["audio"]["sample_rate"])
except Exception:  # noqa: BLE001 -- default do medium
    SAMPLE_RATE = 22050

# response_format -> (args de saída do ffmpeg, mime). "wav" não passa por ffmpeg.
FORMATOS = {
    "mp3": (["-f", "mp3", "-b:a", "128k"], "audio/mpeg"),
    "opus": (["-f", "opus"], "audio/opus"),
    "aac": (["-f", "adts"], "audio/aac"),
    "flac": (["-f", "flac"], "audio/flac"),
    "wav": (None, "audio/wav"),
    "pcm": (None, "audio/L16"),
}


def limpar_markdown(texto):
    """Interpreta a marcação em vez de lê-la: a voz não diz asterisco, #, crase nem barra.
    Negrito vira ênfase por pausa (vírgulas); título e item de lista fecham com ponto, para cada ideia ter o seu fôlego."""
    import re
    t = re.sub(r"```.*?```", " ", texto, flags=re.S)                  # bloco de código não se lê
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)                   # [texto](url) -> texto
    t = re.sub(r"https?://\S+", " ", t)                                 # URL solta não se lê
    t = re.sub(r"(?m)^\s*>+\s?", "", t)                                 # citação
    t = re.sub(r"(?m)^\s*[-=_*]{3,}\s*$", " ", t)                       # régua horizontal
    t = re.sub(r"(?m)^\s*\|?[\s:|-]+\|[\s:|-]*$", " ", t)             # separador de tabela
    t = t.replace("|", ", ")                                             # célula de tabela vira pausa

    def _fecha(s):
        fim = s.rstrip("*_`~ ")
        return s if not fim or fim[-1] in ".!?:;" else s.rstrip() + "."

    t = re.sub(r"(?m)^\s{0,3}#{1,6}\s*(.+?)\s*$", lambda m: "\x01" + m.group(1).strip("*_ ") + "\x02.", t)   # título: ênfase + ponto
    t = re.sub(r"(?m)^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$", lambda m: _fecha(m.group(1)), t)               # item: sem marcador, com ponto
    t = re.sub(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1", "\x01\\2\x02", t, flags=re.S)                           # negrito -> ênfase
    t = re.sub(r"(\*|_)(?=\S)(.+?)(?<=\S)\1", r"\2", t, flags=re.S) if "*" in t else t                    # itálico simples
    t = re.sub(r"(?<!\w)_(?=\S)(.+?)(?<=\S)_(?!\w)", r"\1", t)        # _itálico_ (snake_case fica)
    t = re.sub(r"\s*\x01(.+?)\x02", r", \1,", t, flags=re.S)             # ênfase = pausa antes e depois
    t = t.replace("\x01", "").replace("\x02", "").replace("*", "").replace("`", "").replace("~~", "")
    t = re.sub(r",(\s*[.!?:;,])", r"\1", t)                              # vírgula colada em pontuação some
    t = re.sub(r"([.!?:;])\s*,", r"\1", t)
    t = re.sub(r"(?m)^\s*,\s*", "", t)                                   # sem vírgula abrindo a linha
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def sintetizar(texto, speed=1.0):
    """texto -> PCM s16le mono cru (bytes). speed 1.0 = natural; >1 acelera."""
    length_scale = 1.0 / speed if speed and speed > 0 else 1.0
    proc = subprocess.run(
        [PYTHON, "-m", "piper", "-m", MODEL, "--output-raw",
         "--length-scale", f"{length_scale:.4f}"],
        input=texto.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace")[:500])
    return proc.stdout


def tratar(pcm):
    """PCM cru -> (PCM tratado, estado). NUNCA levanta: a voz não pode derrubar a Seth. Sem ffmpeg, com
    filtro ausente ou erro, devolve o PCM cru e o estado explica (`indisponivel:<motivo>`)."""
    if TRATAMENTO == "off":
        return pcm, "off"
    if not FFMPEG:
        return pcm, "indisponivel:sem-ffmpeg"
    try:
        out = subprocess.run(
            [FFMPEG, "-hide_banner", "-loglevel", "error",
             "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", "-",
             "-af", CADEIA_SISTEMA, "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-"],
            input=pcm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        return pcm, "indisponivel:" + type(e).__name__
    if out.returncode != 0 or not out.stdout:
        return pcm, f"indisponivel:ffmpeg-{out.returncode}"
    return out.stdout, "sistema"


def para_formato(pcm, fmt):
    """PCM cru -> bytes no formato pedido. wav/pcm sem ffmpeg; resto via ffmpeg."""
    if fmt == "pcm":
        return pcm
    if fmt == "wav" or not FFMPEG:
        # embrulha o PCM num header WAV mínimo (44 bytes), sem ffmpeg
        import struct
        n = len(pcm)
        hdr = b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack(
            "<IHHIIHH", 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16
        ) + b"data" + struct.pack("<I", n)
        return hdr + pcm
    args, _ = FORMATOS[fmt]
    out = subprocess.run(
        [FFMPEG, "-hide_banner", "-loglevel", "error",
         "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", "-",
         *args, "-"],
        input=pcm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace")[:500])
    return out.stdout


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _json(self, code, obj):
        corpo = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *a):  # silencia o log por request
        pass

    def do_GET(self):
        if self.path.rstrip("/") == "/health":
            return self._json(200, {"status": "ok", "engine": "piper",
                                    "model": os.path.basename(MODEL),
                                    "sample_rate": SAMPLE_RATE, "ffmpeg": bool(FFMPEG),
                                    "tratamento": TRATAMENTO})
        if self.path.rstrip("/") == "/v1/models":
            return self._json(200, {"object": "list", "data": [
                {"id": "tts-1", "object": "model", "owned_by": "piper"},
                {"id": "tts-1-hd", "object": "model", "owned_by": "piper"},
                {"id": "piper", "object": "model", "owned_by": "piper"},
            ]})
        return self._json(404, {"error": {"message": "not found", "type": "not_found"}})

    def do_POST(self):
        if self.path.rstrip("/") not in ("/v1/audio/speech", "/audio/speech"):
            return self._json(404, {"error": {"message": "not found", "type": "not_found"}})
        corpo = ler_corpo_limitado(self)
        if corpo is None:
            return
        try:
            req = json.loads(corpo or b"{}")
        except Exception:  # noqa: BLE001
            return self._json(400, {"error": {"message": "corpo não é JSON", "type": "invalid_request_error"}})

        texto = limpar_markdown((req.get("input") or "").strip())
        if not texto:
            return self._json(400, {"error": {"message": "campo 'input' vazio", "type": "invalid_request_error"}})
        fmt = (req.get("response_format") or "mp3").lower()
        if fmt not in FORMATOS:
            fmt = "mp3"
        try:
            speed = float(req.get("speed", 1.0))
        except (TypeError, ValueError):
            speed = 1.0

        # `voice` é ignorado de propósito: o modelo (faber ou agata-last) tem 1
        # locutor. Fica no shape só pra não quebrar o cliente. Multi-voz =
        # trocar o modelo por um multi-speaker e mapear aqui.
        try:
            pcm = sintetizar(texto, speed * VELOCIDADE_BASE)
            pcm, tratamento = tratar(pcm)
            if tratamento.startswith("indisponivel"):
                print(f"piper-tts: AVISO — tratamento de áudio {tratamento}; voz crua nesta resposta", file=sys.stderr)
            audio = para_formato(pcm, fmt)
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"error": {"message": f"piper falhou: {e}", "type": "server_error"}})

        _, mime = FORMATOS[fmt]
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(audio)))
        self.send_header("X-Agata-Tratamento", tratamento)
        self.end_headers()
        self.wfile.write(audio)


def _selftest():
    """Offline: sem Piper, sem modelo, sem rede. Confere o tratamento, o fallback e o instalador."""
    import math
    import struct
    import tempfile
    global TRATAMENTO, FFMPEG, CADEIA_SISTEMA
    res = {}
    seno = b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 220 * i / SAMPLE_RATE)))
                    for i in range(SAMPLE_RATE * 2))   # 2 s a 220 Hz
    salvo = (TRATAMENTO, FFMPEG, CADEIA_SISTEMA)
    try:
        tem_rubber = False
        if salvo[1]:
            ff = subprocess.run([salvo[1], "-hide_banner", "-filters"], stdout=subprocess.PIPE, text=True).stdout
            tem_rubber = " rubberband " in ff
        TRATAMENTO = "sistema"
        FFMPEG = salvo[1]
        if tem_rubber:
            out, est = tratar(seno)
            res["1 tratamento aplica a cadeia: estado=sistema, voz alongada ~6% e diferente da crua"] = \
                est == "sistema" and out != seno and 1.0 < len(out) / len(seno) < 1.15
        else:
            print("SKIP 1: ffmpeg sem o filtro rubberband (o serviço degrada para voz crua e avisa)")
        TRATAMENTO = "off"
        out, est = tratar(seno)
        res["2 PIPER_TRATAMENTO=off devolve a voz crua"] = est == "off" and out == seno
        TRATAMENTO = "sistema"
        FFMPEG = None
        out, est = tratar(seno)
        res["3 sem ffmpeg devolve a voz crua e diz por quê"] = est == "indisponivel:sem-ffmpeg" and out == seno
        FFMPEG = salvo[1]
        CADEIA_SISTEMA = "filtro_que_nao_existe=1"
        out, est = tratar(seno)
        res["4 filtro inválido não derruba: voz crua e estado indisponivel"] = \
            est.startswith("indisponivel") and out == seno
        CADEIA_SISTEMA = salvo[2]
        wav = para_formato(seno, "wav")
        res["5 wav: cabeçalho RIFF e tamanho dos dados coerentes"] = \
            wav[:4] == b"RIFF" and struct.unpack("<I", wav[40:44])[0] == len(seno) and len(wav) == 44 + len(seno)
        res["6 a cadeia canônica é a aprovada em 16/10/2026 (eco jarvis)"] = \
            "aecho=0.8:0.7:25|50|90:0.3|0.2|0.12" in salvo[2] and "chorus=0.7:0.9:35|55" in salvo[2] \
            and "acompressor=threshold=-18dB:ratio=2.5" in salvo[2]
        res["9a negrito vira ênfase por pausa, sem asteriscos"] = \
            limpar_markdown("Isto é **muito importante** e *assim* também.") == "Isto é, muito importante, e assim também."
        res["9b título, lista, link, crase e código"] = limpar_markdown(
            "## Resultado\n- item **um**\n- veja [o canon](https://x.y/z) e `grep`\n```\nrm -rf\n```") == \
            "Resultado.\nitem, um.\nveja o canon e grep."
        res["9c snake_case e texto simples não são mexidos"] = \
            limpar_markdown("o arquivo seth_gateway ficou pronto") == "o arquivo seth_gateway ficou pronto"
        tab = limpar_markdown("| a | b |\n|---|---|\n| 1 | 2 |")
        res["9d tabela: sem barras nem traços"] = "|" not in tab and "-" not in tab
        res["9e nenhum símbolo de markdown sobra num texto misto"] = not any(
            c in limpar_markdown("**Resultado:** o *gateway* __ok__ `x` ~~z~~") for c in "*_`#~")
        res["9f velocidade base mais lenta que a natural (reunião esclarecedora)"] = 0.5 <= VELOCIDADE_BASE < 1.0
        with tempfile.TemporaryDirectory() as td:
            res["7a sem a voz instalada, o padrão é a genérica"] = \
                _modelo_padrao(td).endswith("pt_BR-faber-medium.onnx")
            open(os.path.join(td, "pt_BR-agata-last.onnx"), "wb").close()
            res["7b com a voz instalada, o padrão é a treinada"] = _modelo_padrao(td).endswith("pt_BR-agata-last.onnx")
        # instalador, em cópia temporária, com arquivos de mentira e manifesto próprio
        with tempfile.TemporaryDirectory() as td:
            ori = os.path.join(td, "origem")
            os.makedirs(ori)
            dados = {"v.onnx": b"modelo falso\n", "v.onnx.json": b"{}\n"}
            for k, v in dados.items():
                with open(os.path.join(ori, k), "wb") as f:
                    f.write(v)
            man = os.path.join(td, "man.sha256")
            import hashlib
            with open(man, "w") as f:
                f.write("# teste\n")
                for k, v in dados.items():
                    f.write(f"{hashlib.sha256(v).hexdigest()}  {k}\n")
            sandbox = os.path.join(td, "tts-piper")
            os.makedirs(sandbox)
            shutil.copy(os.path.join(AQUI, "tts-piper", "instalar-agata.sh"), sandbox)
            env = dict(os.environ, AGATA_VOZ_ORIGEM=ori, AGATA_VOZ_MANIFESTO=man)
            a = subprocess.run(["bash", os.path.join(sandbox, "instalar-agata.sh")], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            b = subprocess.run(["bash", os.path.join(sandbox, "instalar-agata.sh")], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            res["8a instalador instala os arquivos conferidos"] = a.returncode == 0 and \
                os.path.exists(os.path.join(sandbox, "voices", "v.onnx")) and "instalado: v.onnx" in a.stdout
            res["8b instalador é idempotente"] = b.returncode == 0 and "já instalado: v.onnx" in b.stdout
            with open(os.path.join(ori, "v.onnx"), "wb") as f:
                f.write(b"adulterado\n")
            os.unlink(os.path.join(sandbox, "voices", "v.onnx"))
            c = subprocess.run(["bash", os.path.join(sandbox, "instalar-agata.sh")], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            res["8c hash divergente: recusa e não instala"] = c.returncode != 0 and \
                not os.path.exists(os.path.join(sandbox, "voices", "v.onnx")) and "diverge" in c.stderr
    finally:
        TRATAMENTO, FFMPEG, CADEIA_SISTEMA = salvo
    for k, v in res.items():
        print(("OK    " if v else "FALHOU"), k)
    ruins = [k for k, v in res.items() if not v]
    print(f"tts_piper selftest: {len(res) - len(ruins)}/{len(res)} verificações OK")
    return 1 if ruins else 0


def main():
    if "--selftest" in sys.argv[1:]:
        return _selftest()
    if not os.path.exists(MODEL):
        print(f"ABORTADO: modelo não encontrado em {MODEL}. Rode tts-piper/instalar.sh.", file=sys.stderr)
        return 1
    if not os.path.exists(PYTHON):
        print(f"ABORTADO: python do venv não encontrado em {PYTHON}. Rode tts-piper/instalar.sh.", file=sys.stderr)
        return 1
    srv = ServidorConcorrenciaLimitada((HOST, PORT), H)
    print(f"piper-tts: {HOST}:{PORT} · modelo {os.path.basename(MODEL)} · {SAMPLE_RATE}Hz · ffmpeg={'sim' if FFMPEG else 'não'}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
