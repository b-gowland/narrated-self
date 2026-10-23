"""Run a round: send every prompt to every model and append raw outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .config import RoundConfig, default_config_path, load_round_config
from .estimate import estimate_model
from .protocol import Cell, Protocol, build_cells, load_protocol


@dataclass(frozen=True)
class RoundPlan:
    protocol: Protocol
    config: RoundConfig
    cells: list[Cell]

    @property
    def total(self) -> int:
        return len(self.config.models) * len(self.cells)


def plan_round(root: Path, round_id: str, config_path: Path | None = None) -> RoundPlan:
    protocol = load_protocol(root)
    config = load_round_config(config_path or default_config_path(root, round_id), round_id)
    return RoundPlan(protocol, config, build_cells(protocol, config.themes))


def dry_run(plan: RoundPlan, out: Callable[[str], None] = print) -> None:
    """Print the full prompt matrix and a cost estimate. Makes no API calls."""
    settings = plan.protocol.settings
    out(f"Round {plan.config.round_id} · protocol v{plan.protocol.version} · sha256 {plan.protocol.sha256}")
    out(
        f"{len(plan.config.models)} models × {len(plan.cells)} prompts "
        f"({plan.config.themes} themes × conditions × {settings['samples_per_cell']} samples) = {plan.total} outputs"
    )
    out("")
    for model in plan.config.models:
        for cell in plan.cells:
            out(
                f"{model.provider}/{model.model_string}\t{cell.theme_id}\t{cell.condition_id}\t"
                f"s{cell.sample_n}\t{cell.prompt_text}"
            )
    out("")
    out("Estimate (tokens; 'typical' assumes ~500-word stories, 'ceiling' assumes every reply hits max_output_tokens):")
    total_typical = total_ceiling = 0.0
    priced = True
    for model in plan.config.models:
        est = estimate_model(model, plan.cells, settings["max_output_tokens"])
        line = (
            f"  {model.provider}/{model.model_string}: in {est['input']:,} · "
            f"out typical {est['typical_output']:,} · ceiling {est['ceiling_output']:,}"
        )
        if "typical_usd" in est:
            line += f" · US${est['typical_usd']:.2f} typical, US${est['ceiling_usd']:.2f} ceiling"
            total_typical += est["typical_usd"]
            total_ceiling += est["ceiling_usd"]
        else:
            line += " · no price set in config"
            priced = False
        out(line)
    if priced:
        out(f"  Total: US${total_typical:.2f} typical, US${total_ceiling:.2f} ceiling")
    out("  Reasoning models may use extra hidden tokens; check each provider's billing after the first run.")
    placeholders = [m.provider for m in plan.config.models if m.is_placeholder]
    if placeholders:
        out(f"  Model strings still to fill in: {', '.join(placeholders)}")
