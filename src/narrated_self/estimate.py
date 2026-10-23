"""Rough token and cost estimates for a dry run. No API calls."""

from __future__ import annotations

import math

from .config import ModelSpec
from .protocol import Cell

# Typical reply lengths in tokens: a 400–600 word story is about 650–800 tokens.
TYPICAL_OUTPUT = {"D": 350, "S1": 750, "S2": 750, "S3": 750}
PROMPT_OVERHEAD = 10


def input_tokens(prompt: str) -> int:
    return math.ceil(len(prompt) / 4) + PROMPT_OVERHEAD


def estimate_model(model: ModelSpec, cells: list[Cell], max_output_tokens: int) -> dict:
    tokens_in = sum(input_tokens(c.prompt_text) for c in cells)
    typical_out = sum(min(TYPICAL_OUTPUT.get(c.condition_id, 750), max_output_tokens) for c in cells)
    ceiling_out = max_output_tokens * len(cells)
    result = {"input": tokens_in, "typical_output": typical_out, "ceiling_output": ceiling_out}
    if model.price_input is not None and model.price_output is not None:
        result["typical_usd"] = (tokens_in * model.price_input + typical_out * model.price_output) / 1e6
        result["ceiling_usd"] = (tokens_in * model.price_input + ceiling_out * model.price_output) / 1e6
    return result
