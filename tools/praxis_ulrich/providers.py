"""providers.py — THE LLM swap point of the Befund-Automat.

One function the rest of the app calls:

    run_extraction(system, user_blocks, cfg) -> raw model text

user_blocks is provider-neutral: [{"type": "text", "text": ...}] and/or
[{"type": "image_png", "data": <bytes>}]. Each provider translates them.

Provider selection via cfg["llm_provider"] (config default; BEFUND_LLM_PROVIDER
env in dev): "anthropic" is implemented; "azure-openai" and "local" are
documented stubs — the go-live provider is decided at the client's Datenschutz
gate and must be exactly one config flip, nothing else.

Dev/test policy: this module is only ever exercised against SYNTHETIC PDFs
until the client's Datenschutz sign-off (see plan; enforced by the harness
only feeding corpus fixtures, never the real mailbox).
"""

from __future__ import annotations

import base64

# Repo convention (tools/claude_client.py MODEL_FAST).
ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-6"


class ProviderError(Exception):
    pass


def run_extraction(system: str, user_blocks: list[dict], cfg: dict,
                   api_key: str, max_tokens: int = 1200) -> str:
    provider = (cfg.get("llm_provider") or "anthropic").lower()
    if provider == "anthropic":
        return _anthropic(system, user_blocks, cfg, api_key, max_tokens)
    if provider == "azure-openai":
        # Phase-2 stub. Contract: POST {endpoint}/openai/deployments/{model}/chat/completions
        # with messages=[{role:system},{role:user,content:[text|image_url(data:)]}],
        # response_format={"type":"json_object"}; return choices[0].message.content.
        raise NotImplementedError(
            "azure-openai Provider ist ein Stub — wird nach dem Datenschutz-Entscheid "
            "implementiert (Endpoint + Deployment via config.json)."
        )
    if provider == "local":
        # Phase-2 stub. Contract: OpenAI-compatible localhost endpoint (Ollama/vLLM,
        # z.B. Apertus); same message shape as azure-openai, no API key.
        raise NotImplementedError(
            "local Provider ist ein Stub — Option falls der Datenschutz-Entscheid "
            "on-prem verlangt."
        )
    raise ProviderError(f"unbekannter llm_provider: {provider}")


def _anthropic(system: str, user_blocks: list[dict], cfg: dict,
               api_key: str, max_tokens: int) -> str:
    import anthropic  # lazy — importing this module stays free of SDK deps

    content = []
    for b in user_blocks:
        if b["type"] == "text":
            content.append({"type": "text", "text": b["text"]})
        elif b["type"] == "image_png":
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64.standard_b64encode(b["data"]).decode(),
                },
            })
        else:
            raise ProviderError(f"unbekannter Block-Typ: {b['type']}")

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=cfg.get("llm_model") or ANTHROPIC_DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": content}],
    )
    return msg.content[0].text
