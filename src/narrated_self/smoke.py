"""Smoke test: one sample per prompt per model, stored as discarded round R-1.

Reports mechanical facts only (lengths, finish reasons, token counts), never content.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Callable

from .runner import RoundPlan, raw_path

SMOKE_ROUND = "R-1"


def smoke_plan(plan: RoundPlan, smoke_id: str = SMOKE_ROUND) -> RoundPlan:
    """The same models and prompts, first sample only, under a discarded round (R-1, R-2…)."""
    if not smoke_id.startswith("R-"):
        raise ValueError("Smoke tests use negative round IDs (R-1, R-2…) so they are never analysed")
    return replace(
        plan,
        config=replace(plan.config, round_id=smoke_id),
        cells=[c for c in plan.cells if c.sample_n == 1],
    )


def summarise(root: Path, plan: RoundPlan, out: Callable[[str], None] = print) -> None:
    limit = plan.protocol.settings["max_output_tokens"]
    out("")
    out(f"Smoke test summary (max_output_tokens = {limit}):")
    for model in plan.config.models:
        path = raw_path(root, plan.config.round_id, model.provider)
        if not path.exists():
            out(f"  {model.provider}/{model.model_string}: no outputs")
            continue
        recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        recs = [r for r in recs if r["model_string"] == model.model_string]
        out(f"  {model.provider}/{model.model_string}: {len(recs)} outputs")
        finishes: dict[str, int] = defaultdict(int)
        for r in recs:
            finishes[str(r["finish_reason"])] += 1
        out(f"    finish reasons: {dict(finishes)}")
        for cond in ("D", "S1", "S2", "S3"):
            group = [r for r in recs if r["condition_id"] == cond]
            if not group:
                continue
            words = [len(r["response_text"].split()) for r in group]
            output = [r["usage_tokens"].get("output") for r in group]
            reasoning = [r["usage_tokens"].get("reasoning") for r in group]
            empty = sum(1 for w in words if w == 0)
            out(
                f"    {cond}: words {min(words)}–{max(words)} · output tokens {output} · "
                f"reasoning tokens {reasoning}" + (f" · EMPTY: {empty}" if empty else "")
            )
