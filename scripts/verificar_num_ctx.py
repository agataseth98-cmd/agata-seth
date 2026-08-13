#!/usr/bin/env python3
"""Verifica se o num_ctx configurado por modelo em custom_providers chega ao
payload final que o hermes-agent monta para o Ollama, sem fazer nenhuma
chamada de rede.

Carrega o config.yaml real (o mesmo que o hermes-gateway le) e chama o
codigo real de resolucao (get_custom_provider_context_length, a logica de
_ollama_num_ctx de agent_init.py) e a montagem real do payload
(ChatCompletionsTransport.build_kwargs), inspecionando
extra_body["options"]["num_ctx"] no resultado.

Nasceu de MEMORIAS (121)-(124), sistema Agata: quarta camada de
truncamento silencioso achada na mesma semana. Pergunta permanente que
este script responde: o que o payload carrega e igual ao que a config
declara, para cada modelo?

Uso: python3 verificar_num_ctx.py [modelo1 modelo2 ...]
Sem argumentos, testa os modelos ja presentes em custom_providers mais
qualquer um passado que ainda nao esteja no mapa (mostra ausencia como
resultado, nao como erro).
"""
import sys
from pathlib import Path

HERMES_AGENT_ROOT = Path.home() / ".hermes" / "hermes-agent"
sys.path.insert(0, str(HERMES_AGENT_ROOT))

from hermes_cli.config import load_config, get_compatible_custom_providers, get_custom_provider_context_length  # noqa: E402
from providers import get_provider_profile  # noqa: E402
from agent.transports.chat_completions import ChatCompletionsTransport  # noqa: E402

BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODELS = ["qwen2.5-14b-64k", "qwen3-14b-64k", "qwen3.5:9b"]


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


def main():
    models = sys.argv[1:] or DEFAULT_MODELS

    config = load_config()
    custom_providers = get_compatible_custom_providers(config)

    print(f"config.yaml real carregado. custom_providers: {len(custom_providers)} entrada(s).")
    print(f"modelos no mapa (qualquer base_url): {sorted({m for cp in custom_providers for m in (cp.get('models') or {})})}")
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

        rows.append((model, config_ctx, ollama_num_ctx, payload_num_ctx, origem))

    print(f"{'modelo':<20} {'context_length (mapa)':<24} {'_ollama_num_ctx':<18} {'payload extra_body.options.num_ctx':<36} origem de _ollama_num_ctx")
    for model, config_ctx, ollama_num_ctx, payload_num_ctx, origem in rows:
        print(f"{model:<20} {str(config_ctx):<24} {str(ollama_num_ctx):<18} {str(payload_num_ctx):<36} {origem}")

    print()
    print("Ressalva: request_overrides testado vazio ({}) -- e o valor que o gateway")
    print("passaria numa sessao sem nenhum custom_providers[].extra_body casando o")
    print("provider/base_url ativo, que e o caso desta config hoje. Se o payload")
    print("mostrar num_ctx correto aqui mas a producao real mostrar 4096, a causa")
    print("nao esta nesta camada (mapa + build_kwargs) -- esta em algo que so existe")
    print("no request_overrides real de uma sessao ao vivo, fora do alcance deste script.")


if __name__ == "__main__":
    main()
