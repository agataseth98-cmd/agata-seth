"""Ler em voz alta as respostas da Seth no painel (11/11/2026, pedido do Humano: paridade com o LibreChat).

Fala só com a voz do sistema: o piper pt_BR-agata-last (porta 8890), pelo scripts/agata_falar.py. Daquele script
reaproveita o preparo do texto, a ligação e o desligamento do serviço, a checagem de modelo e os players. O script
não é editado. A diferença: fala por parágrafo, e para entre um parágrafo e o seguinte quando o Humano pede Parar.

Regras (decisão do Humano, 03/11/2026): nenhuma outra voz; o texto do Agata não sai da Máquina; fala só quando o
Humano pede ou o modo conversa está ligado. Quem não fala diz que NÃO falou (falou: false). Uma leitura por vez no
painel: a trava é a mesma da História (historia_painel._FALA_LOCK).

Interface: iniciar(texto) fala e só volta quando termina, para ou falha; parar() pede a parada, que vale entre
partes; estado() e resumo_voz() só leem. Nada disso grava o texto: o último motivo e o último uso ficam em memória.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
import threading
import urllib.error
from datetime import datetime
from pathlib import Path

import historia_painel

ROOT = Path(__file__).resolve().parents[2]
FALA_PY = ROOT / "scripts" / "agata_falar.py"
LIMITE_CORPO_BYTES = 65_536
TEMPO_TRECHO_S = 300
_TRAVA = historia_painel._FALA_LOCK  # uma leitura por vez no painel: a da Seth e a da História
MENSAGEM_OCUPADO = "já estou lendo em voz alta; aguarde o fim ou pare a leitura"

_ESTADO_LOCK = threading.Lock()
_PARAR = threading.Event()
_ESTADO = {"falando": False, "trecho": 0, "trechos": 0, "ultimo_uso": None, "ultimo_motivo": None}
_falar_mod = None


class ErroVoz(Exception):
    def __init__(self, status: int, motivo: str):
        super().__init__(motivo)
        self.status, self.motivo = status, motivo


def _falar():
    """O scripts/agata_falar.py, carregado uma vez. Usado só pelos helpers dele (não pelo main)."""
    global _falar_mod
    if _falar_mod is None:
        spec = importlib.util.spec_from_file_location("agata_falar_painel", FALA_PY)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        _falar_mod = modulo
    return _falar_mod


def _agora() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def _motivos(falar) -> dict:
    return {
        "completo": "falei a resposta inteira",
        "parado": "parei a leitura entre os trechos",
        "falha": "a voz do sistema falhou no meio da leitura",
        "texto": f"NÃO falei: o texto está vazio ou passa de {falar.MAX_TOTAL} caracteres depois de preparado. Peça um resumo.",
        "voz": "NÃO falei: a voz do sistema não respondeu, ou carregou outro modelo. Não falo com outra voz.",
        "player": "NÃO falei: não há player de áudio nesta máquina (mpv, paplay, pw-play, aplay ou ffplay).",
    }


def _resposta(codigo: str, feitas: int, total: int, motivo: str) -> dict:
    with _ESTADO_LOCK:
        _ESTADO["ultimo_motivo"] = motivo
    return {"schema_version": 1, "falou": feitas > 0, "completo": codigo == "completo", "codigo": codigo,
            "trechos_falados": feitas, "trechos": total, "motivo": motivo}


def iniciar(texto) -> dict:
    """Lê o texto em voz alta, em partes. Volta quando termina, para ou falha, com falou ou NÃO falou."""
    if not isinstance(texto, str) or not texto.strip():
        raise ErroVoz(400, "texto vazio: nada para ler")
    falar = _falar()
    motivos = _motivos(falar)
    fala = falar.preparar(texto)
    if not fala or len(fala) > falar.MAX_TOTAL:
        return _resposta("texto", 0, 0, motivos["texto"])
    tocador = falar.player()
    if tocador is None:
        return _resposta("player", 0, 0, motivos["player"])
    if not _TRAVA.acquire(blocking=False):
        raise ErroVoz(429, MENSAGEM_OCUPADO)
    try:
        return _ler(falar, falar.paragrafos(fala), tocador, motivos)
    finally:
        _TRAVA.release()


def _ler(falar, partes: list[str], tocador: list[str], motivos: dict) -> dict:
    total = len(partes)
    with _ESTADO_LOCK:
        _PARAR.clear()
        _ESTADO.update(falando=True, trecho=0, trechos=total, ultimo_uso=_agora())
    pasta = Path(tempfile.mkdtemp(prefix="agata-seth-voz-"))
    ligamos = False
    try:
        saude, ligamos = falar.garantir_servico()
        codigo, feitas, detalhe = _tocar(falar, partes, tocador, saude, pasta)
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
        if ligamos:
            falar.desligar()
        with _ESTADO_LOCK:
            _ESTADO["falando"] = False
    if codigo == "completo":
        motivo = motivos["completo"] + ("" if total == 1 else f" em {total} trechos")
    elif codigo == "parado":
        motivo = f"{motivos['parado']}: falei {feitas} de {total}" if feitas else "parei antes do primeiro trecho: nada foi falado"
    elif codigo == "falha":
        motivo = f"falei {feitas} de {total}; {detalhe}: NÃO falei o resto"
    else:
        motivo = motivos["voz"]
    return _resposta(codigo, feitas, total, motivo)


def _tocar(falar, partes: list[str], tocador: list[str], saude, pasta: Path) -> tuple[str, int, str]:
    """Pede e toca trecho por trecho. Devolve (código, trechos tocados, detalhe). Para só entre trechos."""
    if not saude or not str(saude.get("model", "")).startswith(falar.MODELO_DO_SISTEMA):
        return "voz", 0, ""
    feitas = 0
    for i, par in enumerate(partes, 1):
        if _PARAR.is_set():
            break
        with _ESTADO_LOCK:
            _ESTADO["trecho"] = i
        corpo = json.dumps({"model": "tts-1", "input": par, "voice": "agata", "response_format": "wav"}).encode("utf-8")
        try:
            audio, _cabecalhos = falar._http("/v1/audio/speech", corpo, timeout=TEMPO_TRECHO_S)
        except (urllib.error.URLError, OSError):
            return ("falha" if feitas else "voz"), feitas, f"a voz do sistema não respondeu no trecho {i}"
        if _PARAR.is_set():
            break
        arq = pasta / f"trecho-{i:02d}.wav"
        arq.write_bytes(audio)
        if subprocess.run([*tocador, str(arq)], check=False).returncode != 0:
            return ("falha" if feitas else "voz"), feitas, f"o player falhou no trecho {i}"
        feitas = i
    if feitas == len(partes):
        return "completo", feitas, ""
    return "parado", feitas, ""


def parar() -> dict:
    """Pede a parada. Vale entre trechos: o trecho que está tocando termina."""
    with _ESTADO_LOCK:
        lendo = _ESTADO["falando"]
        if lendo:
            _PARAR.set()
    if not lendo:
        return {"schema_version": 1, "falando": False, "motivo": "não estou lendo: nada para parar"}
    return {"schema_version": 1, "falando": True, "motivo": "parando: a leitura para depois do trecho que está tocando"}


def estado() -> dict:
    """Só leitura: se está lendo, em que trecho, e o último uso e motivo (em memória, desde o início do painel)."""
    with _ESTADO_LOCK:
        return {"schema_version": 1, "falando": _ESTADO["falando"], "trecho": _ESTADO["trecho"],
                "trechos": _ESTADO["trechos"], "ultimo_uso": _ESTADO["ultimo_uso"], "ultimo_motivo": _ESTADO["ultimo_motivo"]}


def resumo_voz() -> str:
    """Uma linha para a página Sentidos: piper agata-last no ar ou parado (sob demanda) e o último uso.
    Só lê o /health do piper. Não liga o serviço."""
    falar = _falar()
    saude = falar.saude()
    if saude is None:
        servico = "parado (sobe sob demanda, quando alguém pede para falar)"
    elif str(saude.get("model", "")).startswith(falar.MODELO_DO_SISTEMA):
        servico = "no ar"
    else:
        servico = f"no ar, mas com outro modelo ({saude.get('model')}): NÃO é a voz do sistema"
    with _ESTADO_LOCK:
        uso = _ESTADO["ultimo_uso"]
    quando = f"último uso: {uso}" if uso else "último uso: nenhum desde que o painel abriu"
    return f"piper pt_BR-agata-last · {servico} · {quando}"
