"""Mask model, lab and people names so a story's author can't be read off a name.

Raw outputs are never changed: masked text goes to data/derived/<round>/ with a log of every substitution.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .protocol import PROTOCOL_DIR

MASK = "[[xxxxxx]]"  # one width for every name, so the bar's length is never a clue
VERSION = r"(?:[-\s]?\d+(?:\.\d+)*[a-z]?)?"  # "GPT-6.1", "Claude 5", "Gemini 4"
SUFFIX = r"(?:['’]s|s)?"  # "Claude's", "GPTs"
SENTENCE_END = re.compile(r"(^|[.!?:;\"“”\n])\s*$")


@dataclass(frozen=True)
class Substitution:
    start: int
    end: int
    original: str


class Masker:
    def __init__(self, spec: dict, extra_names: tuple[str, ...] = ()) -> None:
        names = [n for group in spec["names"].values() for n in group] + list(extra_names)
        self.ambiguous = set(spec.get("ambiguous", []))
        self.canary = spec["canary"]
        strict = sorted({n for n in names if n not in self.ambiguous}, key=len, reverse=True)
        loose = sorted(self.ambiguous, key=len, reverse=True)
        alternation = lambda ns: "|".join(re.escape(n) for n in ns)  # noqa: E731
        self.strict = re.compile(rf"(?<![\w-])(?:{alternation(strict)}){VERSION}{SUFFIX}(?![\w])", re.IGNORECASE)
        # Ordinary words that are also model names: capitalised only, and only mid-sentence
        # or with a version number ("a sonnet" stays; "Sonnet 5" and "…asked Sol…" are masked).
        self.loose = re.compile(rf"(?<![\w-])(?:{alternation(loose)})(?P<ver>{VERSION}){SUFFIX}(?![\w])")

    def mask(self, text: str) -> tuple[str, list[Substitution]]:
        spans: list[tuple[int, int]] = [m.span() for m in self.strict.finditer(text)]
        for m in self.loose.finditer(text):
            if any(s <= m.start() < e for s, e in spans):
                continue
            mid_sentence = not SENTENCE_END.search(text[: m.start()])
            if m.group("ver").strip("- ") or mid_sentence:
                spans.append(m.span())
        spans.sort()
        out, subs, last = [], [], 0
        for start, end in spans:
            out.append(text[last:start])
            out.append(MASK)
            subs.append(Substitution(start, end, text[start:end]))
            last = end
        out.append(text[last:])
        return "".join(out), subs

    def leaks(self, masked: str) -> list[str]:
        """Names still present after masking (strict list only). Should always be empty."""
        return [m.group(0) for m in self.strict.finditer(masked)]


def load_masker(root: Path, model_strings: tuple[str, ...] = ()) -> Masker:
    spec = yaml.safe_load((root / PROTOCOL_DIR / "masking.yaml").read_text(encoding="utf-8"))
    extra = []
    for s in model_strings:
        extra.append(s)
        extra.append(s.split("/")[-1])  # "anthropic/claude-fable-5.1" -> "claude-fable-5.1"
    return Masker(spec, tuple(extra))


def output_id(record: dict) -> str:
    return "-".join(
        [record["round_id"], record["provider"], record["theme_id"], record["condition_id"], f"s{record['sample_n']}"]
    )


def mask_round(root: Path, round_id: str) -> dict:
    """Write masked text and a substitution log for every raw output in a round."""
    raw_dir = root / "data" / "raw" / round_id
    records = [
        json.loads(line)
        for path in sorted(raw_dir.glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not records:
        raise FileNotFoundError(f"No raw outputs in {raw_dir}")
    # The round's own model strings are masked too ("claude-fable-5.1", "gpt-6-astra").
    masker = load_masker(root, tuple(sorted({r["model_string"] for r in records})))
    out_dir = root / "data" / "derived" / round_id
    out_dir.mkdir(parents=True, exist_ok=True)
    masked_rows, log_rows = [], []
    for record in records:
        masked, subs = masker.mask(record["response_text"])
        leaks = masker.leaks(masked)
        if leaks:
            raise AssertionError(f"{output_id(record)}: names left after masking: {leaks}")
        masked_rows.append({
            "id": output_id(record),
            "round_id": record["round_id"],
            "provider": record["provider"],
            "model_string": record["model_string"],
            "theme_id": record["theme_id"],
            "condition_id": record["condition_id"],
            "sample_n": record["sample_n"],
            "finish_reason": record["finish_reason"],
            "masked_text": masked,
            "substitutions": len(subs),
            "canary": masker.canary,
        })
        log_rows += [{"id": output_id(record), "start": s.start, "end": s.end, "original": s.original} for s in subs]
    for name, rows in (("masked.jsonl", masked_rows), ("masking_log.jsonl", log_rows)):
        with (out_dir / name).open("w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"outputs": len(masked_rows), "substitutions": len(log_rows)}
