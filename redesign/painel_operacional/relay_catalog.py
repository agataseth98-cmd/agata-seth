"""Roster RelayCouncil: registra provedores sem habilitar automação DOM."""

from __future__ import annotations


PROVIDERS = (
    {"id": "deepseek", "name": "DeepSeek", "kind": "model-service", "access_mode": "official_api_only", "availability": "candidate", "terms_review": "web_automation_restricted", "policy_url": "https://platform.deepseek.com/downloads/DeepSeek%20User%20Agreement.pdf"},
    {"id": "gemini", "name": "Gemini", "kind": "model-service", "access_mode": "official_api_only", "availability": "in_roster", "terms_review": "api_terms_required", "source_ref": "config/modelos-gratuitos.md"},
    {"id": "zai", "name": "Z.ai / GLM", "kind": "model-service", "access_mode": "official_api_only", "availability": "in_roster", "terms_review": "web_automation_restricted", "policy_url": "https://chat.z.ai/legal-agreement/terms-of-service", "source_ref": "config/modelos-gratuitos.md"},
    {"id": "chatgpt", "name": "ChatGPT", "kind": "model-service", "access_mode": "official_api_only", "availability": "candidate", "terms_review": "web_output_extraction_prohibited", "policy_url": "https://openai.com/policies/terms-of-use/"},
    {"id": "claude", "name": "Claude", "kind": "model-service", "access_mode": "official_api_only", "availability": "candidate", "terms_review": "api_terms_required", "policy_url": "https://www.anthropic.com/legal"},
    {"id": "grok", "name": "Grok", "kind": "model-service", "access_mode": "official_api_only", "availability": "candidate", "terms_review": "api_terms_required", "policy_url": "https://x.ai/legal/terms-of-service"},
    {"id": "qwen", "name": "Qwen", "kind": "model-service", "access_mode": "official_api_only", "availability": "candidate", "terms_review": "web_automation_prohibited", "policy_url": "https://qwen.ai/termsservice"},
    {"id": "mistral", "name": "Le Chat / Mistral", "kind": "model-service", "access_mode": "official_api_only", "availability": "in_roster", "terms_review": "api_terms_required", "source_ref": "config/modelos-gratuitos.md"},
    {"id": "kimi", "name": "Kimi", "kind": "model-service", "access_mode": "official_api_only", "availability": "candidate", "terms_review": "api_terms_required"},
    {"id": "copilot", "name": "Microsoft Copilot", "kind": "model-service", "access_mode": "manual_only", "availability": "candidate", "terms_review": "unverified"},
    {"id": "meta-ai", "name": "Meta AI", "kind": "model-service", "access_mode": "manual_only", "availability": "candidate", "terms_review": "unverified"},
    {"id": "poe", "name": "Poe", "kind": "model-router", "access_mode": "manual_only", "availability": "candidate", "terms_review": "unverified"},
    {"id": "you", "name": "You.com", "kind": "model-router", "access_mode": "official_api_only", "availability": "candidate", "terms_review": "api_terms_required"},
    {"id": "huggingchat", "name": "HuggingChat / Inference Providers", "kind": "model-router", "access_mode": "official_api_only", "availability": "in_roster", "terms_review": "api_terms_required", "source_ref": "config/modelos-gratuitos.md"},
    {"id": "duck-ai", "name": "Duck.ai", "kind": "model-router", "access_mode": "manual_only", "availability": "candidate", "terms_review": "unverified"},
    {"id": "openrouter", "name": "OpenRouter", "kind": "model-router", "access_mode": "official_api_only", "availability": "in_roster", "terms_review": "api_terms_required", "source_ref": "config/modelos-gratuitos.md"},
    {"id": "groq", "name": "GroqCloud API", "kind": "model-router", "access_mode": "official_api_only", "availability": "candidate", "terms_review": "api_terms_required", "policy_url": "https://console.groq.com/docs/legal"},
)

PROVIDER_BY_ID = {provider["id"]: provider for provider in PROVIDERS}


def snapshot() -> list[dict[str, str]]:
    """Retorna cópias e não expõe o roster mutável ao handler."""
    return [dict(provider) for provider in PROVIDERS]
