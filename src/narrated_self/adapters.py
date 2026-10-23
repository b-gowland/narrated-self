"""Thin provider adapters. Each sends one user message, with no system prompt.

SDKs are imported lazily so tests and dry runs never need them or a key.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

SAMPLING_PARAMS = ("temperature", "top_p")


@dataclass(frozen=True)
class GenSettings:
    temperature: float | None
    top_p: float | None
    max_output_tokens: int


@dataclass
class Generation:
    text: str
    finish_reason: str | None
    usage: dict
    meta: dict = field(default_factory=dict)


class Adapter:
    provider: str = ""
    env_key: str = ""
    # Sampling parameters this API accepts. Requested values it cannot take are logged, not sent.
    supports: frozenset[str] = frozenset(SAMPLING_PARAMS)

    def generate(self, model: str, prompt: str, settings: GenSettings) -> Generation:
        raise NotImplementedError

    def sampling_kwargs(self, settings: GenSettings) -> dict:
        return {
            name: getattr(settings, name)
            for name in SAMPLING_PARAMS
            if name in self.supports and getattr(settings, name) is not None
        }


class AnthropicAdapter(Adapter):
    provider = "anthropic"
    env_key = "ANTHROPIC_API_KEY"
    supports = frozenset()  # the current SDK takes no temperature or top_p

    def __init__(self) -> None:
        import anthropic

        self.client = anthropic.Anthropic(api_key=os.environ[self.env_key], max_retries=0)

    def generate(self, model, prompt, settings):
        r = self.client.messages.create(
            model=model,
            max_tokens=settings.max_output_tokens,
            messages=[{"role": "user", "content": prompt}],
            **self.sampling_kwargs(settings),
        )
        text = "".join(b.text for b in r.content if b.type == "text")
        details = getattr(r.usage, "output_tokens_details", None)
        usage = {
            "input": r.usage.input_tokens,
            "output": r.usage.output_tokens,
            "reasoning": getattr(details, "thinking_tokens", None),
        }
        return Generation(text, r.stop_reason, usage, {"response_model": r.model, "response_id": r.id})


class OpenAIAdapter(Adapter):
    provider = "openai"
    env_key = "OPENAI_API_KEY"

    def __init__(self) -> None:
        import openai

        self.client = openai.OpenAI(api_key=os.environ[self.env_key], max_retries=0)

    def generate(self, model, prompt, settings):
        r = self.client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=settings.max_output_tokens,
            store=False,
            **self.sampling_kwargs(settings),
        )
        incomplete = getattr(r, "incomplete_details", None)
        finish = f"incomplete:{incomplete.reason}" if incomplete else r.status
        usage = {}
        if r.usage:
            details = getattr(r.usage, "output_tokens_details", None)
            usage = {
                "input": r.usage.input_tokens,
                "output": r.usage.output_tokens,
                "reasoning": getattr(details, "reasoning_tokens", None),
            }
        return Generation(r.output_text or "", finish, usage, {"response_model": r.model, "response_id": r.id})


class XAIAdapter(Adapter):
    provider = "xai"
    env_key = "XAI_API_KEY"

    def __init__(self) -> None:
        import openai

        self.client = openai.OpenAI(
            api_key=os.environ[self.env_key], base_url="https://api.x.ai/v1", max_retries=0
        )

    def generate(self, model, prompt, settings):
        r = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.max_output_tokens,
            **self.sampling_kwargs(settings),
        )
        choice = r.choices[0]
        usage = {}
        if r.usage:
            details = getattr(r.usage, "completion_tokens_details", None)
            usage = {
                "input": r.usage.prompt_tokens,
                "output": r.usage.completion_tokens,
                "reasoning": getattr(details, "reasoning_tokens", None),
            }
        meta = {"response_model": r.model, "response_id": r.id}
        return Generation(choice.message.content or "", choice.finish_reason, usage, meta)


class GoogleAdapter(Adapter):
    provider = "google"
    env_key = "GOOGLE_API_KEY"

    def __init__(self) -> None:
        from google import genai

        self.client = genai.Client(api_key=os.environ[self.env_key])

    def generate(self, model, prompt, settings):
        from google.genai import types

        config = types.GenerateContentConfig(
            max_output_tokens=settings.max_output_tokens, **self.sampling_kwargs(settings)
        )
        r = self.client.models.generate_content(model=model, contents=prompt, config=config)
        cand = r.candidates[0] if r.candidates else None
        parts = cand.content.parts if cand and cand.content and cand.content.parts else []
        text = "".join(p.text for p in parts if p.text and not p.thought)
        if cand and cand.finish_reason:
            finish = cand.finish_reason.name
        else:
            feedback = getattr(r, "prompt_feedback", None)
            finish = f"blocked:{feedback.block_reason.name}" if feedback and feedback.block_reason else None
        um = r.usage_metadata
        usage = {}
        if um:
            usage = {
                "input": um.prompt_token_count,
                "output": um.candidates_token_count,
                "reasoning": um.thoughts_token_count,
            }
        meta = {"response_model": getattr(r, "model_version", None), "response_id": getattr(r, "response_id", None)}
        return Generation(text, finish, usage, meta)


class OpenRouterAdapter(Adapter):
    """Any model through OpenRouter, pinned to one host with no fallbacks."""

    provider = "openrouter"
    env_key = "OPENROUTER_API_KEY"

    def __init__(self, host: str) -> None:
        import openai

        self.host = host
        self.client = openai.OpenAI(
            api_key=os.environ[self.env_key], base_url="https://openrouter.ai/api/v1", max_retries=0
        )

    def generate(self, model, prompt, settings):
        r = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.max_output_tokens,
            extra_body={"provider": {"order": [self.host], "only": [self.host], "allow_fallbacks": False}},
            **self.sampling_kwargs(settings),
        )
        choice = r.choices[0]
        usage = {}
        if r.usage:
            details = getattr(r.usage, "completion_tokens_details", None)
            usage = {
                "input": r.usage.prompt_tokens,
                "output": r.usage.completion_tokens,
                "reasoning": getattr(details, "reasoning_tokens", None),
            }
        extra = r.model_extra or {}
        meta = {
            "via": "openrouter",
            "host_requested": self.host,
            "served_by": extra.get("provider"),
            "response_model": r.model,
            "response_id": r.id,
            "cost_usd": (r.usage.model_extra or {}).get("cost") if r.usage else None,
        }
        return Generation(choice.message.content or "", choice.finish_reason, usage, meta)


ADAPTERS: dict[str, type[Adapter]] = {
    a.provider: a for a in (AnthropicAdapter, OpenAIAdapter, GoogleAdapter, XAIAdapter)
}


def adapter_class(model) -> type[Adapter]:
    return OpenRouterAdapter if model.via == "openrouter" else ADAPTERS[model.provider]


def make_adapter(model) -> Adapter:
    return OpenRouterAdapter(model.host) if model.via == "openrouter" else ADAPTERS[model.provider]()


def missing_keys(models) -> list[str]:
    keys = {adapter_class(m).env_key for m in models}
    return sorted(k for k in keys if not os.environ.get(k))


def is_retryable(exc: Exception) -> bool:
    """Network errors, timeouts, rate limits and 5xx are retried; other 4xx are not."""
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if isinstance(code, int) and 400 <= code < 500 and code not in (408, 409, 429):
        return False
    return True
