"""Falha segura da voz do Agata.

Funcoes puras, sem rede. Regra do Humano: se a voz falhar, o sistema nao
pode ficar mudo nem inventar. Volta para texto e diz que nao falou.
"""

AVISO_SEM_VOZ = "A voz não respondeu; segue por texto."


def resposta_ao_usuario(texto: str, audio_ok: bool, motivo_falha: str | None) -> dict:
    """Monta a resposta ao usuario conforme o estado do audio.

    So devolve "falou": True quando o audio saiu (audio_ok is True).
    Qualquer outro valor de audio_ok cai no modo texto (fail-safe).
    motivo_falha nao entra no dict devolvido; fica para quem registra o erro.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("texto vazio: nada para responder")

    if audio_ok is True:
        return {"modo": "voz", "texto": texto, "falou": True}

    return {
        "modo": "texto",
        "texto": texto,
        "falou": False,
        "aviso": AVISO_SEM_VOZ,
    }


def transcricao_segura(resultado: dict | None) -> dict:
    """Valida o resultado de STT sem propagar excecao nem texto inventado."""
    motivo_vazio = "transcrição vazia ou ausente"

    if not isinstance(resultado, dict):
        return {"ok": False, "motivo": motivo_vazio, "texto": None}

    texto = resultado.get("texto")
    if not isinstance(texto, str) or not texto.strip():
        return {"ok": False, "motivo": motivo_vazio, "texto": None}

    return {"ok": True, "texto": texto, "motivo": None}
