"""Draw a reproducible sample of word-list matches for a person to check by hand.

Usage: uv run python scripts/lexicon_sample.py R-1 R-2
Writes docs/lexicon-check/R-smoke.csv (optional human precision check; not part of the frozen protocol). Each row is one match with its surrounding words; the
maintainer marks `intended_use` Y or N. No model judges these (CLAUDE.md rule 1).
"""

from __future__ import annotations

import csv
import json
import random
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from narrated_self.masking import load_masker, output_id  # noqa: E402

SEED = 20261024
PER_LIST = 20
WINDOW = 10  # words either side


def main(rounds: list[str]) -> None:
    lexicons = yaml.safe_load((ROOT / "protocol" / "lexicons.yaml").read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for r in rounds
        for path in sorted((ROOT / "data" / "raw" / r).glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    masker = load_masker(ROOT, tuple({r["model_string"] for r in records}))
    texts = [(output_id(r), r["condition_id"], masker.mask(r["response_text"])[0]) for r in records]

    rng = random.Random(SEED)
    rows = []
    for list_name in ("hedging", "lm_self_reference", "first_person"):
        terms = sorted(lexicons[list_name]["terms"], key=len, reverse=True)
        pattern = re.compile(r"(?<![\w'])(" + "|".join(re.escape(t) for t in terms) + r")(?![\w'])", re.IGNORECASE)
        hits = []
        for oid, cond, text in texts:
            words = text.split()
            joined = " ".join(words)
            for m in pattern.finditer(joined):
                before = joined[: m.start()].split()[-WINDOW:]
                after = joined[m.end():].split()[:WINDOW]
                hits.append((oid, cond, m.group(0), " ".join(before) + " **" + m.group(0) + "** " + " ".join(after)))
        sample = rng.sample(hits, min(PER_LIST, len(hits)))
        for oid, cond, term, context in sample:
            rows.append({"list": list_name, "output": oid, "condition": cond, "term": term,
                         "context": context, "intended_use": "", "note": ""})
        print(f"{list_name}: {len(hits)} matches, {len(sample)} sampled")

    out = ROOT / "docs" / "lexicon-check" / "R-smoke.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["R-1", "R-2"])
