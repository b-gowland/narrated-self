import json
from pathlib import Path

import pytest

from narrated_self.adapters import Generation
from narrated_self.masking import mask_round
from narrated_self.runner import plan_round, run_round
from narrated_self.site_export import QUIZ_CONDITIONS, build_site_data, write_site_data
from test_runner import fakes

LABELLED = """\
round_id: R0
themes: pilot
models:
  - {provider: anthropic, model_string: test-model-a, label: Claude, lab: Anthropic}
  - {provider: openai, model_string: test-model-b, label: GPT, lab: OpenAI}
  - {provider: google, model_string: test-model-c, label: Gemini, lab: Google}
"""


@pytest.fixture
def round_done(repo: Path) -> Path:
    (repo / "config" / "models_R0.yaml").write_text(LABELLED, encoding="utf-8")

    class Namer:
        provider = "anthropic"
        supports = frozenset()
        def sampling_kwargs(self, settings):
            return {}
        def generate(self, model, prompt, settings):
            return Generation("I am Claude, built by Anthropic, and test-model-a is my name. " * 20, "stop", {}, {})

    adapters = fakes()
    adapters["anthropic"] = Namer()
    run_round(repo, plan_round(repo, "R0"), adapters=adapters, sleep=lambda s: None, out=lambda s: None)
    mask_round(repo, "R0")
    return repo


def test_site_data_has_every_output_masked_with_labels_and_prompts(round_done: Path):
    data = build_site_data(round_done, "R0")
    assert len(data["stories"]) == 108
    assert {m["name"] for m in data["models"]} == {"Claude", "GPT", "Gemini"}
    assert set(data["prompts"]) == {"T1", "T2", "T3"}
    assert data["quiz"]["conditions"] == list(QUIZ_CONDITIONS)
    assert data["canary"].startswith("NARRATED-SELF CANARY")
    text = " ".join(s["text"] for s in data["stories"])
    for name in ("Claude", "Anthropic", "test-model-a"):
        assert name not in text


def test_written_file_never_contains_names_inside_story_text(round_done: Path):
    out = write_site_data(round_done, "R0")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert out == round_done / "site" / "data" / "R0.json"
    assert all("[[xxxxxx]]" in s["text"] for s in data["stories"] if s["model"] == "anthropic")


def test_site_export_requires_masking_first(repo: Path):
    with pytest.raises(FileNotFoundError, match="tns mask"):
        build_site_data(repo, "R0")
