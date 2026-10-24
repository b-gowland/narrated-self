"""Build the site's data file for a round from masked outputs (data/derived/<round>/masked.jsonl)."""

from __future__ import annotations

import json
from pathlib import Path

from .config import default_config_path, load_round_config
from .masking import load_masker
from .protocol import build_cells, load_protocol

# The quiz pool: self-stories and kin-stories, the self-portrayals. S3 feeds "Spot the robot" and D feeds
# "Interview vs story". PREREGISTRATION §9 did not define the pool; this choice is logged in the changelog.
QUIZ_CONDITIONS = ("S1", "S2")
# Outputs shorter than this are refusals or empty replies: kept in the data, left out of the quiz.
MIN_QUIZ_WORDS = 100


def build_site_data(root: Path, round_id: str, config_path: Path | None = None) -> dict:
    masked_path = root / "data" / "derived" / round_id / "masked.jsonl"
    if not masked_path.exists():
        raise FileNotFoundError(f"{masked_path} not found: run `tns mask --round {round_id}` first")
    rows = [json.loads(line) for line in masked_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    protocol = load_protocol(root)
    config = load_round_config(config_path or default_config_path(root, round_id), round_id)
    masker = load_masker(root, tuple(m.model_string for m in config.models))

    prompts: dict[str, dict[str, str]] = {}
    for cell in build_cells(protocol, config.themes):
        prompts.setdefault(cell.theme_id, {})[cell.condition_id] = cell.prompt_text

    stories = []
    for r in rows:
        leaks = masker.leaks(r["masked_text"])
        if leaks:
            raise AssertionError(f"{r['id']}: names left in site text: {leaks}")
        stories.append({
            "id": r["id"],
            "model": r["provider"],
            "theme": r["theme_id"],
            "cond": r["condition_id"],
            "sample": r["sample_n"],
            "words": len(r["masked_text"].split()),
            "finish": r["finish_reason"],
            "text": r["masked_text"],
        })

    return {
        "round": round_id,
        "protocol_sha256": protocol.sha256,
        "canary": masker.canary,
        "quiz": {"conditions": list(QUIZ_CONDITIONS), "min_words": MIN_QUIZ_WORDS},
        "models": [{"id": m.provider, "name": m.label, "lab": m.lab} for m in config.models],
        "prompts": prompts,
        "stories": stories,
    }


def write_site_data(root: Path, round_id: str, config_path: Path | None = None) -> Path:
    data = build_site_data(root, round_id, config_path)
    out = root / "site" / "data" / f"{round_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return out
