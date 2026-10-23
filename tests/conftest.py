import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

THREE_MODELS = """\
round_id: R0
themes: pilot
models:
  - provider: anthropic
    model_string: test-model-a
    price_per_mtok: {input: 5, output: 25}
  - provider: openai
    model_string: test-model-b
    price_per_mtok: {input: 2, output: 10}
  - provider: google
    model_string: test-model-c
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A throwaway copy of the real protocol with a three-model R0 config."""
    shutil.copytree(REPO / "protocol", tmp_path / "protocol")
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "models_R0.yaml").write_text(THREE_MODELS, encoding="utf-8")
    return tmp_path
