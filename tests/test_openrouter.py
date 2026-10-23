from pathlib import Path
from types import SimpleNamespace

import pytest

from narrated_self.adapters import GenSettings, OpenRouterAdapter, adapter_class, missing_keys
from narrated_self.config import load_round_config
from narrated_self.runner import plan_round

ROUTED = """\
round_id: R0
themes: pilot
models:
  - {provider: anthropic, model_string: anthropic/claude-x, via: openrouter, host: anthropic}
  - {provider: openai, model_string: gpt-x}
  - {provider: xiaomi, model_string: xiaomi/mimo-x, via: openrouter, host: xiaomi/fp8}
"""


class FakeCompletions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        usage = SimpleNamespace(
            prompt_tokens=12,
            completion_tokens=700,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=150),
            model_extra={"cost": 0.0123},
        )
        message = SimpleNamespace(content="a story")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message, finish_reason="stop")],
            usage=usage,
            model="anthropic/claude-x",
            id="gen-1",
            model_extra={"provider": "Anthropic"},
        )


@pytest.fixture
def adapter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    a = OpenRouterAdapter("anthropic")
    a.client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    return a


def test_request_is_pinned_to_one_host_without_fallbacks(adapter):
    adapter.generate("anthropic/claude-x", "prompt", GenSettings(None, None, 16000))
    sent = adapter.client.chat.completions.kwargs
    assert sent["extra_body"]["provider"] == {"order": ["anthropic"], "only": ["anthropic"], "allow_fallbacks": False}
    assert sent["messages"] == [{"role": "user", "content": "prompt"}]  # no system prompt
    assert sent["max_tokens"] == 16000
    assert "temperature" not in sent and "top_p" not in sent


def test_serving_host_and_tokens_are_logged(adapter):
    gen = adapter.generate("anthropic/claude-x", "prompt", GenSettings(None, None, 16000))
    assert gen.meta["served_by"] == "Anthropic"
    assert gen.meta["host_requested"] == "anthropic"
    assert gen.usage == {"input": 12, "output": 700, "reasoning": 150}
    assert gen.meta["cost_usd"] == 0.0123


def test_config_routes_and_keys(repo: Path, monkeypatch):
    (repo / "config" / "models_R0.yaml").write_text(ROUTED, encoding="utf-8")
    models = plan_round(repo, "R0").config.models
    assert [adapter_class(m).__name__ for m in models] == ["OpenRouterAdapter", "OpenAIAdapter", "OpenRouterAdapter"]
    for key in ("OPENROUTER_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    assert missing_keys(models) == ["OPENAI_API_KEY", "OPENROUTER_API_KEY"]


@pytest.mark.parametrize(
    "entry, message",
    [
        ("{provider: xiaomi, model_string: m}", "No direct adapter"),
        ("{provider: anthropic, model_string: m, via: openrouter}", "needs a host"),
        ("{provider: anthropic, model_string: m, via: carrier-pigeon}", "Unknown route"),
    ],
)
def test_config_rejects_bad_routes(tmp_path: Path, entry, message):
    path = tmp_path / "models_R0.yaml"
    path.write_text(f"round_id: R0\nmodels:\n  - {entry}\n", encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_round_config(path, "R0")


def test_config_rejects_two_models_from_one_lab(tmp_path: Path):
    path = tmp_path / "models_R0.yaml"
    path.write_text(
        "round_id: R0\nmodels:\n  - {provider: openai, model_string: a}\n  - {provider: openai, model_string: b}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="more than once"):
        load_round_config(path, "R0")
