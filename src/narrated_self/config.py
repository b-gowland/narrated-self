"""Per-round model configuration (config/models_<round>.yaml)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

PROVIDERS = ("anthropic", "openai", "google", "xai")
PLACEHOLDER = "FILL_ME"


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model_string: str
    price_input: float | None  # US$ per million tokens, for estimates only
    price_output: float | None

    @property
    def is_placeholder(self) -> bool:
        return self.model_string.strip() in ("", PLACEHOLDER)


@dataclass(frozen=True)
class RoundConfig:
    round_id: str
    themes: str
    models: list[ModelSpec]


def default_config_path(root: Path, round_id: str) -> Path:
    return root / "config" / f"models_{round_id}.yaml"


def load_round_config(path: Path, round_id: str) -> RoundConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw.get("round_id") != round_id:
        raise ValueError(f"{path} is for round {raw.get('round_id')!r}, not {round_id!r}")
    models = []
    for entry in raw["models"]:
        provider = entry["provider"]
        if provider not in PROVIDERS:
            raise ValueError(f"Unknown provider {provider!r}; expected one of {PROVIDERS}")
        price = entry.get("price_per_mtok") or {}
        models.append(
            ModelSpec(
                provider=provider,
                model_string=str(entry.get("model_string") or ""),
                price_input=price.get("input"),
                price_output=price.get("output"),
            )
        )
    keys = [(m.provider, m.model_string) for m in models]
    if len(set(keys)) != len(keys):
        raise ValueError(f"{path} lists the same model twice")
    return RoundConfig(round_id=round_id, themes=raw.get("themes", "pilot"), models=models)
