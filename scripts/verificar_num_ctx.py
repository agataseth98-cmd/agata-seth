#!/usr/bin/env python3
"""Verifica se o num_ctx configurado por modelo em custom_providers chega
inteiro ao corpo HTTP que sairia para o Ollama -- em duas camadas.

Camada 1 (sempre roda, qualquer python3 com o hermes-agent no path):
config.yaml real -> get_custom_provider_context_length -> logica de
_ollama_num_ctx (agent_init.py) -> ChatCompletionsTransport.build_kwargs
real. Nenhuma rede, nenhuma dependencia externa.

Camada 2 (precisa do venv do hermes-agent, ``openai``/``httpx`` instalados):
pega o mesmo kwargs da camada 1 e chama openai.OpenAI(...).chat.completions
.create(**kwargs) de verdade, mas com httpx.Client.send interceptado --
captura o request.body exatamente como sairia pela rede e ABORTA antes do
envio real. Zero chamada de rede, zero GPU, zero custo de cota. Compara
kwargs["extra_body"]["options"]["num_ctx"] (camada 1) contra o que
realmente estaria no corpo JSON (camada 2). Se divergirem, o merge de
``agent/transports/chat_completions.py`` entre as duas camadas esta
provado como o ponto de perda.

Nasceu de MEMORIAS (121)-(126), sistema Agata: quarta camada de
truncamento silencioso achada na mesma semana. Pergunta permanente que
este script responde: o que o payload carrega e igual ao que sairia de
verdade pela rede, para cada modelo?

Uso:
  python3 scripts/verificar_num_ctx.py [modelo1 modelo2 ...]              (so camada 1)
  ~/.hermes/hermes-agent/venv/bin/python3 scripts/verificar_num_ctx.py    (camadas 1+2)
Sem argumentos, testa os modelos ja presentes em custom_providers mais
qualquer um passado que ainda nao esteja no mapa (mostra ausencia como
resultado, nao como erro).
"""
import json
import sys
from pathlib import Path

HERMES_AGENT_ROOT = Path.home() / ".hermes" / "hermes-agent"
sys.path.insert(0, str(HERMES_AGENT_ROOT))

from hermes_cli.config import load_config, get_compatible_custom_providers, get_custom_provider_context_length  # noqa: E402
from providers import get_provider_profile  # noqa: E402
from agent.transports.chat_completions import ChatCompletionsTransport  # noqa: E402

BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODELS = ["qwen2.5-14b-64k", "qwen3-14b-64k", "qwen3.5:9b"]

try:
    import httpx
    import openai
    _HTTP_LAYER_AVAILABLE = True
except ImportError:
    _HTTP_LAYER_AVAILABLE = False


def resolve_ollama_num_ctx(config: dict, model: str, base_url: str, config_context_length: int | None) -> tuple[int | None, str]:
    """Replica agent_init.py linhas ~1861-1899, para decidir agent._ollama_num_ctx."""
    model_cfg = config.get("model", {}) if isinstance(config, dict) else {}
    override = model_cfg.get("ollama_num_ctx") if isinstance(model_cfg, dict) else None
    if override is not None:
        try:
            return int(override), "override global (model.ollama_num_ctx)"
        except (TypeError, ValueError):
            pass
    # Sem override: so auto-detectaria via query_ollama_num_ctx se base_url
    # for local -- nao chamado aqui de proposito (script nao faz rede).
    return None, "sem override global, dependeria de auto-deteccao via rede (nao testado aqui)"


class _Intercepted(Exception):
    """Abortar o envio de verdade depois de capturar o request."""


def capture_real_http_body(kwargs: dict) -> dict | str:
    """Chama openai.OpenAI(...).chat.completions.create(**kwargs) com
    httpx.Client.send interceptado -- devolve o corpo JSON real que sairia
    pela rede, sem nenhum byte de fato trafegar. Nunca toca no Ollama.
    """
    captured = {}
    orig_send = httpx.Client.send

    def _intercepting_send(self, request, **_kw):
        body = request.read()
        try:
            captured["body_json"] = json.loads(body)
        except Exception as e:  # pragma: no cover -- defensivo
            captured["body_parse_error"] = str(e)
        raise _Intercepted("interceptado antes do envio real -- nenhum byte trafegou")

    httpx.Client.send = _intercepting_send
    try:
        client = openai.OpenAI(base_url=BASE_URL, api_key="ollama-local-placeholder")
        try:
            client.chat.completions.create(**kwargs)
        except Exception:
            # A SDK envolve qualquer exceção levantada dentro de send() em
            # APIConnectionError -- o que importa é que 'captured' já foi
            # preenchido antes disso, não o tipo da exceção que borbulhou.
            pass
    finally:
        httpx.Client.send = orig_send

    if "body_json" in captured:
        return captured["body_json"]
    return captured.get("body_parse_error", "corpo não capturado -- request pode não ter chegado a httpx.Client.send")


def main():
    models = sys.argv[1:] or DEFAULT_MODELS

    config = load_config()
    custom_providers = get_compatible_custom_providers(config)

    print(f"config.yaml real carregado. custom_providers: {len(custom_providers)} entrada(s).")
    print(f"modelos no mapa (qualquer base_url): {sorted({m for cp in custom_providers for m in (cp.get('models') or {})})}")
    print(f"camada 2 (corpo HTTP real via interceptação de httpx): {'disponível' if _HTTP_LAYER_AVAILABLE else 'INDISPONÍVEL -- rode com o venv do hermes-agent'}")
    print()

    profile = get_provider_profile("custom")
    if profile is None:
        print("ERRO: profile 'custom' nao resolvido por providers.get_provider_profile — parando.")
        sys.exit(1)

    transport = ChatCompletionsTransport()
    rows = []

    for model in models:
        config_ctx = get_custom_provider_context_length(
            model=model, base_url=BASE_URL, custom_providers=custom_providers,
        )
        ollama_num_ctx, origem = resolve_ollama_num_ctx(config, model, BASE_URL, config_ctx)

        kwargs = transport.build_kwargs(
            model=model,
            messages=[{"role": "user", "content": "teste, nao enviado a rede nenhuma"}],
            tools=None,
            base_url=BASE_URL,
            timeout=60,
            max_tokens=None,
            max_tokens_param_fn=lambda n: {"max_tokens": n},
            reasoning_config=None,
            request_overrides={},  # baseline limpo -- ver ressalva no rodape
            session_id="verificar_num_ctx",
            provider_profile=profile,
            ollama_num_ctx=ollama_num_ctx,
            supports_reasoning=False,
            qwen_session_metadata=None,
        )
        payload_num_ctx = (kwargs.get("extra_body") or {}).get("options", {}).get("num_ctx")

        http_num_ctx = None
        http_note = "não testado (camada 2 indisponível)"
        if _HTTP_LAYER_AVAILABLE:
            body = capture_real_http_body(kwargs)
            if isinstance(body, dict):
                http_num_ctx = body.get("options", {}).get("num_ctx")
                http_note = "capturado de verdade, request abortado antes do envio"
            else:
                http_note = f"falha ao capturar: {body}"

        rows.append((model, config_ctx, ollama_num_ctx, payload_num_ctx, http_num_ctx, http_note, origem))

    header = f"{'modelo':<20} {'mapa':<10} {'_ollama_num_ctx':<16} {'kwargs num_ctx':<16} {'corpo HTTP num_ctx':<20} nota"
    print(header)
    for model, config_ctx, ollama_num_ctx, payload_num_ctx, http_num_ctx, http_note, origem in rows:
        print(f"{model:<20} {str(config_ctx):<10} {str(ollama_num_ctx):<16} {str(payload_num_ctx):<16} {str(http_num_ctx):<20} {http_note}")
        if payload_num_ctx != http_num_ctx and _HTTP_LAYER_AVAILABLE:
            print(f"   *** DIVERGÊNCIA: kwargs tinha {payload_num_ctx}, corpo HTTP real tinha {http_num_ctx} — merge raso provado para {model} ***")

    print()
    print("Ressalva: request_overrides testado vazio ({}) -- e o valor que o gateway")
    print("passaria numa sessao sem nenhum custom_providers[].extra_body casando o")
    print("provider/base_url ativo, que e o caso desta config hoje. Se kwargs e corpo")
    print("HTTP baterem aqui mas a producao real mostrar 4096, a causa nao esta em")
    print("nenhuma das duas camadas testadas -- esta em algo que so existe no")
    print("request_overrides real de uma sessao ao vivo, fora do alcance deste script.")


if __name__ == "__main__":
    main()
