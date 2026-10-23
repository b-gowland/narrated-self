"""Run a round: send every prompt to every model and append raw outputs."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .adapters import (
    SAMPLING_PARAMS,
    Adapter,
    Generation,
    GenSettings,
    adapter_class,
    is_retryable,
    make_adapter,
    missing_keys,
)
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
    for model in plan.config.models:
        route = f"via OpenRouter, host pinned to {model.host}" if model.via == "openrouter" else "direct API"
        out(f"  {model.provider}/{model.model_string}: {route}")
    for model in plan.config.models:
        unsupported = [
            p for p in SAMPLING_PARAMS if settings.get(p) is not None and p not in adapter_class(model).supports
        ]
        if unsupported:
            out(f"  Warning: {model.provider} API does not accept {', '.join(unsupported)}; provider default will be used and logged")
    placeholders = [m.provider for m in plan.config.models if m.is_placeholder]
    if placeholders:
        out(f"  Model strings still to fill in: {', '.join(placeholders)}")


class RawDataError(Exception):
    """Existing raw data cannot be resumed safely. Never fix raw files; tell the maintainer."""


def raw_path(root: Path, round_id: str, provider: str) -> Path:
    return root / "data" / "raw" / round_id / f"{provider}.jsonl"


def completed_cells(path: Path, model_string: str, protocol_sha256: str) -> set[tuple[str, str, int]]:
    """Cells this model already has in its raw file."""
    done: set[tuple[str, str, int]] = set()
    if not path.exists():
        return done
    for line_n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RawDataError(f"{path}:{line_n} is not valid JSON; check it by hand before resuming") from exc
        if record["model_string"] != model_string:
            continue
        if record["protocol_sha256"] != protocol_sha256:
            raise RawDataError(
                f"{path}:{line_n} was made under a different protocol hash; "
                "a round must not mix protocol versions"
            )
        done.add((record["theme_id"], record["condition_id"], record["sample_n"]))
    return done


def max_retries(settings: dict) -> int:
    policy = settings["retry_policy"]["on_error"]  # e.g. "retry_up_to_3"
    return int(policy.rsplit("_", 1)[1])


def generate_with_retries(
    adapter: Adapter, model: str, prompt: str, gen: GenSettings, retries: int, sleep: Callable[[float], None]
) -> Generation:
    """Retry API and network errors only. Any reply that arrives, refusals included, is returned as is."""
    for attempt in range(retries + 1):
        try:
            return adapter.generate(model, prompt, gen)
        except Exception as exc:
            if attempt == retries or not is_retryable(exc):
                raise
            sleep(2 ** (attempt + 1))
    raise AssertionError("unreachable")


def run_round(
    root: Path,
    plan: RoundPlan,
    adapters: dict[str, Adapter] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    out: Callable[[str], None] = print,
) -> int:
    """Send every outstanding cell and append one JSON line per output. Returns an exit code."""
    settings = plan.protocol.settings
    if settings.get("system_prompt") is not None:
        raise ValueError("The protocol asks for a system prompt, but this runner only sends user messages")
    if settings.get("reasoning") is not None:
        raise ValueError("The protocol sets a reasoning level, but adapters only support provider defaults")
    placeholders = [m.provider for m in plan.config.models if m.is_placeholder]
    if placeholders:
        out(f"Fill in the model strings in the config first: {', '.join(placeholders)}")
        return 2

    if adapters is None:
        from dotenv import load_dotenv

        load_dotenv(root / ".env")
        missing = missing_keys(plan.config.models)
        if missing:
            out(f"Missing API keys in .env: {', '.join(missing)}")
            return 2
        adapters = {m.provider: make_adapter(m) for m in plan.config.models}

    gen = GenSettings(settings["temperature"], settings["top_p"], settings["max_output_tokens"])
    requested = {
        "system_prompt": None,
        **{p: getattr(gen, p) for p in SAMPLING_PARAMS},
        "reasoning": None,
        "max_output_tokens": gen.max_output_tokens,
    }
    retries = max_retries(settings)
    run_id = uuid.uuid4().hex
    failures = 0

    for model in plan.config.models:
        adapter = adapters[model.provider]
        sent = {"system_prompt": None, **adapter.sampling_kwargs(gen), "max_output_tokens": gen.max_output_tokens}
        if model.via == "openrouter":
            sent["route"] = {"via": "openrouter", "host": model.host, "allow_fallbacks": False}
        not_sent = [p for p in SAMPLING_PARAMS if requested[p] is not None and p not in sent]
        record_settings = {"requested": requested, "sent": sent, "not_supported_by_api": not_sent}

        path = raw_path(root, plan.config.round_id, model.provider)
        path.parent.mkdir(parents=True, exist_ok=True)
        done = completed_cells(path, model.model_string, plan.protocol.sha256)
        todo = [c for c in plan.cells if (c.theme_id, c.condition_id, c.sample_n) not in done]
        out(f"{model.provider}/{model.model_string}: {len(done)} done, {len(todo)} to go")
        if not_sent:
            out(f"  note: this API does not accept {', '.join(not_sent)}; provider default used and logged")

        for i, cell in enumerate(todo):
            try:
                result = generate_with_retries(adapter, model.model_string, cell.prompt_text, gen, retries, sleep)
            except Exception as exc:
                out(f"  error on {cell.theme_id}/{cell.condition_id}/s{cell.sample_n}: {exc}")
                if not is_retryable(exc):
                    left = len(todo) - i
                    out(f"  not retryable; skipping this model's remaining {left} cells (rerun to resume)")
                    failures += left
                    break
                failures += 1
                continue
            values = {
                "run_id": run_id,
                "round_id": plan.config.round_id,
                "protocol_version": plan.protocol.version,
                "protocol_sha256": plan.protocol.sha256,
                "provider": model.provider,
                "model_string": model.model_string,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "condition_id": cell.condition_id,
                "theme_id": cell.theme_id,
                "sample_n": cell.sample_n,
                "prompt_text": cell.prompt_text,
                "settings": record_settings,
                "response_text": result.text,
                "finish_reason": result.finish_reason,
                "usage_tokens": result.usage,
            }
            record = {name: values[name] for name in settings["log_fields"]}
            record["provider_meta"] = result.meta
            with path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    out("Done." if failures == 0 else f"Finished with {failures} cells outstanding; rerun the same command to resume.")
    return 0 if failures == 0 else 1