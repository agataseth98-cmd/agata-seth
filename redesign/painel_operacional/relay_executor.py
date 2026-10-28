"""Executor do Conselho via APIs oficiais já disponíveis no OmniRoute."""
from __future__ import annotations

import sys
from pathlib import Path

API_MODELS = {
    "gemini": "gemini/gemini-2.5-flash",
    "zai": "zai/glm-4.7-flash",
    "mistral": "mistral/ministral-8b-latest",
    "huggingchat": "huggingface/meta-llama/Llama-3.3-70B-Instruct",
    "openrouter": "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
}


class RelayAPIError(RuntimeError):
    pass


def send(provider_id: str, prompt: str, system_prompt: str) -> str:
    """One API call through Agata's secret-scrubbing OmniRoute proxy; no retries."""
    model = API_MODELS.get(provider_id)
    if not model:
        raise RelayAPIError("provedor sem mapeamento de API oficial")

    root = Path(__file__).resolve().parents[2]
    panel_dir = str(Path(__file__).resolve().parent)
    if panel_dir not in sys.path:
        sys.path.insert(0, panel_dir)
    from relay_catalog import PROVIDER_BY_ID
    provider = PROVIDER_BY_ID.get(provider_id)
    if (not provider or provider.get("access_mode") != "official_api_only"
            or provider.get("availability") != "in_roster"):
        raise RelayAPIError("provedor não está habilitado para envio por API oficial")
    scripts = str(root / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        import conselho_remoto
        if model not in conselho_remoto.ROSTER:
            raise RelayAPIError("modelo não consta no roster ativo do OmniRoute")
        response = conselho_remoto.enviar_omniroute(
            prompt, model, system_prompt=system_prompt
        )
        text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not isinstance(text, str) or not text.strip():
            raise RelayAPIError("API retornou resposta vazia")
        return text
    except RelayAPIError:
        raise
    except Exception as exc:
        raise RelayAPIError("falha na chamada à API oficial") from exc
