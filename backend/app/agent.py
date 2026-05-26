"""Thin wrapper around the Microsoft Agent Framework (direct OpenAI).

Exposes a single async helper, `run_agent`, that sends one message to the model
and returns the reply text plus token usage. The client/agent is created lazily
once and reused across requests.

Config (env vars, read automatically by the framework):
- OPENAI_API_KEY              required — your platform.openai.com key
- OPENAI_MODEL                optional — defaults to "gpt-4o-mini"
"""

import os

from agent_framework.openai import OpenAIChatCompletionClient

DEFAULT_MODEL = "gpt-4o-mini"

_agent = None


def _model() -> str:
    return os.getenv("OPENAI_CHAT_COMPLETION_MODEL") or os.getenv(
        "OPENAI_MODEL", DEFAULT_MODEL
    )


def _get_agent():
    """Create the agent once (lazy singleton)."""
    global _agent
    if _agent is None:
        # OpenAIChatCompletionClient reads OPENAI_API_KEY + the model from the
        # environment. Make sure the model var it looks for is populated.
        os.environ.setdefault("OPENAI_CHAT_COMPLETION_MODEL", _model())
        client = OpenAIChatCompletionClient()
        _agent = client.as_agent(
            name="PipelineHello",
            instructions="You are a helpful assistant. Keep your answers short.",
        )
    return _agent


def _usage_get(usage, key: str):
    """Read a token count from usage_details.

    In agent-framework 1.6 `UsageDetails` is a dict subclass, so we read by key;
    we also fall back to attribute access to stay robust across versions.
    """
    if usage is None:
        return None
    if isinstance(usage, dict):
        return usage.get(key)
    return getattr(usage, key, None)


async def run_agent(message: str) -> dict:
    """Run one prompt and return reply text + token usage.

    Returns a dict: {text, input_tokens, output_tokens, total_tokens, model}.
    Token fields may be None if the provider doesn't return usage.
    """
    result = await _get_agent().run(message)

    usage = getattr(result, "usage_details", None)
    return {
        "text": result.text,
        "input_tokens": _usage_get(usage, "input_token_count"),
        "output_tokens": _usage_get(usage, "output_token_count"),
        "total_tokens": _usage_get(usage, "total_token_count"),
        "model": _model(),
    }
