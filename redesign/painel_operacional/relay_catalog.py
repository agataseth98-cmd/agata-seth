"""Adaptadores de chat em aba Chromium do Conselho em Rede."""

from __future__ import annotations


PROVIDERS = (
    {"id": "deepseek", "name": "DeepSeek", "kind": "chat", "access_mode": "browser_tab_only", "adapter_state": "experimental", "site": "https://chat.deepseek.com/"},
    {"id": "gemini", "name": "Gemini", "kind": "chat", "access_mode": "browser_tab_only", "adapter_state": "experimental", "site": "https://gemini.google.com/"},
    {"id": "zai", "name": "Z.ai / GLM", "kind": "chat", "access_mode": "browser_tab_only", "adapter_state": "experimental", "site": "https://chat.z.ai/"},
    {"id": "chatgpt", "name": "ChatGPT", "kind": "chat", "access_mode": "browser_tab_only", "adapter_state": "experimental", "site": "https://chatgpt.com/"},
    {"id": "claude", "name": "Claude", "kind": "chat", "access_mode": "browser_tab_only", "adapter_state": "experimental", "site": "https://claude.ai/"},
    {"id": "grok", "name": "Grok", "kind": "chat", "access_mode": "browser_tab_only", "adapter_state": "experimental", "site": "https://grok.com/"},
    {"id": "qwen", "name": "Qwen", "kind": "chat", "access_mode": "browser_tab_only", "adapter_state": "experimental", "site": "https://qwen.ai/"},
    {"id": "mistral", "name": "Le Chat / Mistral", "kind": "chat", "access_mode": "browser_tab_only", "adapter_state": "experimental", "site": "https://chat.mistral.ai/"},
    {"id": "kimi", "name": "Kimi", "kind": "chat", "access_mode": "browser_tab_only", "adapter_state": "experimental", "site": "https://www.kimi.com/"},
)

PROVIDER_BY_ID = {provider["id"]: provider for provider in PROVIDERS}


def snapshot(active_providers=()) -> list[dict[str, str]]:
    """Retorna adaptadores declarados e se há aba detectada agora."""
    active = set(active_providers)
    return [{**provider, "tab_open": provider["id"] in active} for provider in PROVIDERS]
