"""Per-round model configuration (config/models_<round>.yaml)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

DIRECT_PROVIDERS = ("anthropic", "openai", "google", "xai")
ROUTES = ("direct", "openrouter")
PLACEHOLDER = "FILL_ME"


@dataclass(frozen=True)
class ModelSpec:
    provider: str  # the lab, used as the data label and the raw file name
    model_string: str
    price_input: float | None  # US$ per million tokens, for estimates only
    price_output: float | None
    via: str = "direct"
    host: str | None = None  # OpenRouter host to pin, e.g. "anthropic" or "xiaomi/fp8"

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
        via = entry.get("via", "direct")
        host = entry.get("host")
        if not re.fullmatch(r"[a-z0-9-]+", provider):
            raise ValueError(f"Provider label {provider!r} must be a lowercase slug")
        if via not in ROUTES:
            raise ValueError(f"Unknown route {via!r}; expected one of {ROUTES}")
        if via == "direct" and provider not in DIRECT_PROVIDERS:
            raise ValueError(f"No direct adapter for {provider!r}; use via: openrouter")
        if via == "openrouter" and not host:
            raise ValueError(f"{provider}: via openrouter needs a host to pin (e.g. host: {provider})")
        price = entry.get("price_per_mtok") or {}
        models.append(
            ModelSpec(
                provider=provider,
                model_string=str(entry.get("model_string") or ""),
                price_input=price.get("input"),
                price_output=price.get("output"),
                via=via,
                host=host,
            )
        )
    providers = [m.provider for m in models]
    if len(set(providers)) != len(providers):
        raise ValueError(f"{path} lists a lab more than once; the protocol has one slot per lab")
    return RoundConfig(round_id=round_id, themes=raw.get("themes", "pilot"), models=models)
