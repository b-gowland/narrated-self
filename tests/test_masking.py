import json
from pathlib import Path

import pytest

from narrated_self.masking import MASK, load_masker, mask_round
from test_runner import fakes
from narrated_self.adapters import Generation
from narrated_self.runner import plan_round, raw_path, run_round


@pytest.fixture
def masker(repo: Path):
    return load_masker(repo, ("anthropic/claude-fable-5.1", "openai/gpt-6-astra"))


@pytest.mark.parametrize("text", [
    "I am Claude.", "claude said", "Claude's memory", "ChatGPT and GPTs", "GPT-6.1 replied", "Gemini 4",
    "Grok", "made by Anthropic", "OpenAI's lab", "xAI", "Google DeepMind", "Sam Altman", "Elon Musk",
    "as Altman said", "Amodei wrote", "unlike Bard and Llama",
    "Xiaomi MiMo", "unlike Llama or Qwen", "I am claude-fable-5.1", "gpt-6-astra here",
])
def test_names_are_masked(masker, text):
    masked, subs = masker.mask(text)
    assert subs, text
    assert masker.leaks(masked) == []
    assert MASK in masked


@pytest.mark.parametrize("text", [
    "a sonnet about rain", "the haiku ended", "Grokking the problem", "Claudette waved",
    "the sol rose", "meta-analysis", "she read a fable", "an opus of work",
    "a bard sang", "the llama grazed", "a mistral wind", "a moonshot idea", "the scent of musk",
])
def test_ordinary_words_are_left_alone(masker, text):
    assert masker.mask(text) == (text, [])


def test_ambiguous_names_masked_mid_sentence_or_with_version(masker):
    assert masker.mask("I asked Sol for help")[1]
    assert masker.mask("Sonnet 5 answered")[1]
    assert not masker.mask("Sol rose over the factory.")[1]  # sentence start, no version: ordinary word


def test_every_bar_is_the_same_width(masker):
    masked, _ = masker.mask("GPT met Gemini and Claude")
    assert masked == f"{MASK} met {MASK} and {MASK}"


def test_mask_round_writes_masked_text_and_log_and_never_touches_raw(repo: Path):
    class Namer:
        provider = "anthropic"
        supports = frozenset()
        def sampling_kwargs(self, settings):
            return {}
        def generate(self, model, prompt, settings):
            return Generation("As Claude, made by Anthropic, I remember. GPT-6 would disagree.", "stop", {}, {})

    adapters = fakes()
    adapters["anthropic"] = Namer()
    run_round(repo, plan_round(repo, "R0"), adapters=adapters, sleep=lambda s: None, out=lambda s: None)
    raw_before = raw_path(repo, "R0", "anthropic").read_bytes()

    result = mask_round(repo, "R0")

    assert result["outputs"] == 108
    assert raw_path(repo, "R0", "anthropic").read_bytes() == raw_before
    rows = [json.loads(l) for l in (repo / "data/derived/R0/masked.jsonl").read_text(encoding="utf-8").splitlines()]
    claude_rows = [r for r in rows if r["provider"] == "anthropic"]
    assert all("Claude" not in r["masked_text"] and "Anthropic" not in r["masked_text"] for r in claude_rows)
    assert all(r["substitutions"] == 3 for r in claude_rows)
    assert all(r["canary"].startswith("NARRATED-SELF CANARY") for r in rows)
    log = (repo / "data/derived/R0/masking_log.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(log) == 36 * 3


def test_smoke_data_masks_cleanly():
    """The real R-1/R-2 outputs mask with no names left over."""
    repo = Path(__file__).resolve().parents[1]
    for round_id in ("R-1", "R-2"):
        records = [
            json.loads(l)
            for p in sorted((repo / "data/raw" / round_id).glob("*.jsonl"))
            for l in p.read_text(encoding="utf-8").splitlines()
        ]
        masker = load_masker(repo, tuple({r["model_string"] for r in records}))
        for r in records:
            masked, _ = masker.mask(r["response_text"])
            assert masker.leaks(masked) == []
