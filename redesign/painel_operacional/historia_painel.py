"""História canônica no painel: seção História, só leitura, mais o botão Ouvir.

Lê historia/ do checkout: tomo-NN/NN-titulo.md, com frontmatter. Não grava nada no diretório.
O Ouvir chama scripts/agata_falar.py com o corpo do texto (sem o frontmatter) e responde se falou, pelo
código de saída. A voz é a do sistema (decisão do Humano, 03/11/2026): quem não fala diz que não falou.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Caminhos lidos na hora da chamada (os testes trocam estes nomes por diretórios temporários).
HISTORIA_DIR = ROOT / "historia"
FALA = ROOT / "scripts" / "agata_falar.py"
TOMO_RE = re.compile(r"tomo-\d{2}")
TEXTO_RE = re.compile(r"\d{2}-[a-z0-9][a-z0-9-]*")
FRONT_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
LIMITE_TEXTO_BYTES = 65_536
TEMPO_FALA_S = 900
_FALA_LOCK = threading.Lock()
MOTIVOS_FALA = {
    0: "falei o texto",
    2: "não falei: o texto está vazio ou acima do limite de fala",
    3: "não falei: a voz do sistema não respondeu, ou não é a voz do sistema",
    4: "não falei: não há player de áudio local",
}


class ErroHistoria(Exception):
    def __init__(self, status: int, motivo: str):
        super().__init__(motivo)
        self.status, self.motivo = status, motivo


def frontmatter(texto: str) -> tuple[dict, str]:
    """Separa o bloco `---` do início. Só pares `chave: valor` de uma linha; aspas duplas externas saem."""
    casa = FRONT_RE.match(texto)
    if not casa:
        return {}, texto
    dados: dict = {}
    for linha in casa.group(1).splitlines():
        chave, sep, valor = linha.partition(":")
        chave = chave.strip()
        if sep and re.fullmatch(r"[a-z_]+", chave):
            valor = valor.strip()
            if len(valor) >= 2 and valor[0] == valor[-1] == '"':
                valor = valor[1:-1]
            dados[chave] = valor
    return dados, texto[casa.end():]


def _ler(arquivo: Path) -> str:
    try:
        if arquivo.stat().st_size > LIMITE_TEXTO_BYTES:
            raise ErroHistoria(413, "texto acima do limite")
        return arquivo.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raise ErroHistoria(500, "historia indisponivel")


def _tomos() -> list[Path]:
    if not HISTORIA_DIR.is_dir():
        return []
    return sorted(p for p in HISTORIA_DIR.iterdir() if p.is_dir() and TOMO_RE.fullmatch(p.name))


def _textos(pasta: Path) -> list[Path]:
    return sorted(p for p in pasta.glob("*.md") if TEXTO_RE.fullmatch(p.stem))


def _resumo(arquivo: Path) -> dict:
    dados, _corpo = frontmatter(_ler(arquivo))
    return {
        "id": arquivo.stem,
        "numero": dados.get("texto", ""),
        "titulo": dados.get("titulo", arquivo.stem),
        "periodo": dados.get("periodo", ""),
        "autor": dados.get("autor", ""),
        "estado": dados.get("estado", ""),
        "protocolo": dados.get("protocolo", ""),
        "_tomo": {"numeral": dados.get("tomo", ""), "titulo": dados.get("titulo_tomo", "")},
    }


def listar() -> dict:
    """Tomos e textos do diretório, na ordem de nome. Sem tomo com texto, o estado é vazio."""
    tomos = []
    for pasta in _tomos():
        resumos = [_resumo(arq) for arq in _textos(pasta)]
        if not resumos:
            continue
        primeiro = resumos[0].pop("_tomo")
        for resumo in resumos[1:]:
            resumo.pop("_tomo")
        tomos.append({"tomo": pasta.name, "numeral": primeiro["numeral"], "titulo": primeiro["titulo"], "textos": resumos})
    return {"schema_version": 1, "estado": "ok" if tomos else "vazio", "tomos": tomos}


def ler(tomo, texto) -> dict:
    """Um texto com frontmatter separado. Tomo e texto têm formato fixo: nada de caminho vindo do cliente."""
    if not (isinstance(tomo, str) and isinstance(texto, str) and TOMO_RE.fullmatch(tomo) and TEXTO_RE.fullmatch(texto)):
        raise ErroHistoria(400, "tomo ou texto fora do formato")
    arquivo = HISTORIA_DIR / tomo / f"{texto}.md"
    if not arquivo.is_file() or not arquivo.resolve().is_relative_to(HISTORIA_DIR.resolve()):
        raise ErroHistoria(404, "texto indisponivel")
    dados, corpo = frontmatter(_ler(arquivo))
    return {"schema_version": 1, "tomo": tomo, "texto": texto, "frontmatter": dados, "corpo": corpo}


def ouvir(tomo, texto) -> dict:
    """Lê o corpo do texto em voz alta com a voz do sistema. Uma fala por vez. Responde falou ou não falou."""
    doc = ler(tomo, texto)
    if not _FALA_LOCK.acquire(blocking=False):
        raise ErroHistoria(429, "ja estou lendo em voz alta; aguarde o fim")
    caminho = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as arq:
            caminho = arq.name
            arq.write(doc["corpo"])
        try:
            codigo = subprocess.run([sys.executable, "-I", str(FALA), "--arquivo", caminho], stdin=subprocess.DEVNULL,
                                    capture_output=True, timeout=TEMPO_FALA_S, check=False).returncode
        except subprocess.TimeoutExpired:
            codigo = -1
    finally:
        if caminho:
            os.unlink(caminho)
        _FALA_LOCK.release()
    if codigo == -1:
        motivo = "não falei até o fim: o tempo acabou"
    else:
        motivo = MOTIVOS_FALA.get(codigo, "não falei: a fala terminou com erro")
    return {"schema_version": 1, "falou": codigo == 0, "motivo": motivo}
