"""Changes across rounds (docs/PREREGISTRATION.md §3 Q4 and §8), plus labelled exploratory checks.

Everything here is deterministic: the same word lists, sentiment lexicon and classical classifier as
`analysis.py`. No model scores, tags or interprets any output (CLAUDE.md rule 1).

Implementation choices where §8 is silent (recorded in the output and in docs/CHANGELOG.md):
- Models are compared by lab slot (Anthropic, OpenAI, Google, xAI). The open-weight slot holds a different
  model each round, so it is described but never tested for change (§4).
- "Within-round spread" is the standard deviation of the theme × condition cell means within a round,
  averaged over the two rounds. A change is reportable only if it is larger than that spread *and* survives
  the permutation test after Holm correction.
- The permutation test shuffles the round label within each theme × condition cell (10,000 shuffles), so a
  change can't come from a different mix of prompts.
- A slot whose model version, route or host changed is flagged: its changes describe a new version, not
  drift in one model (§8 Q4). Only an unchanged slot can support a drift claim.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import confusion_matrix
from sklearn.metrics.pairwise import cosine_similarity

from .analysis import (
    SEED,
    _holm,
    classifier_text,
    function_words_only,
    lexicon_rates,
    load_round,
    make_classifier,
)

LAB_SLOTS = ["anthropic", "openai", "google", "xai"]
MEASURES = ["words", "hedging", "lm_self_reference", "first_person", "sentiment"]


def slot_of(provider: str) -> str:
    return provider if provider in LAB_SLOTS else "open-weight"


def round_models(root: Path, round_id: str) -> dict:
    cfg = yaml.safe_load((root / "config" / f"models_{round_id}.yaml").read_text(encoding="utf-8"))
    return {slot_of(m["provider"]): {"model_string": m["model_string"], "label": m["label"], "via": m.get("via"),
                                     "host": m.get("host")} for m in cfg["models"]}


def round_frame(root: Path, round_id: str) -> pd.DataFrame:
    df = load_round(root, round_id)
    rates = lexicon_rates(df, root)
    out = rates.merge(df[["id", "words", "finish", "reasoning_tokens", "substitutions", "text"]], on="id")
    out["round"] = round_id
    out["slot"] = out["model"].map(slot_of)
    return out


def _cell_means(g: pd.DataFrame, measure: str) -> pd.Series:
    return g.groupby(["theme", "cond"])[measure].mean()


def change_test(a: pd.DataFrame, b: pd.DataFrame, measure: str, permutations: int = 10_000,
                rng: np.random.Generator | None = None) -> dict:
    """Between-round change in one measure for one slot, with a stratified permutation test."""
    rng = rng or np.random.default_rng(SEED)
    delta = float(b[measure].mean() - a[measure].mean())
    spread = float(np.mean([_cell_means(a, measure).std(ddof=1), _cell_means(b, measure).std(ddof=1)]))
    both = pd.concat([a.assign(_r=0), b.assign(_r=1)])
    groups = [g[[measure, "_r"]].to_numpy() for _, g in both.groupby(["theme", "cond"])]
    observed = abs(delta)
    hits = 0
    for _ in range(permutations):
        s1, n1, s0, n0 = 0.0, 0, 0.0, 0
        for g in groups:
            labels = rng.permutation(g[:, 1])
            s1 += g[labels == 1, 0].sum(); n1 += (labels == 1).sum()
            s0 += g[labels == 0, 0].sum(); n0 += (labels == 0).sum()
        if abs(s1 / n1 - s0 / n0) >= observed - 1e-12:
            hits += 1
    p = (hits + 1) / (permutations + 1)
    return {"mean_before": float(a[measure].mean()), "mean_after": float(b[measure].mean()), "change": delta,
            "within_round_spread": spread, "exceeds_spread": bool(abs(delta) > spread), "p_permutation": p}


def q4_changes(before: pd.DataFrame, after: pd.DataFrame, models_before: dict, models_after: dict,
               permutations: int = 10_000) -> dict:
    rng = np.random.default_rng(SEED)
    results, pvals = {}, {}
    for slot in LAB_SLOTS:
        a, b = before[before["slot"] == slot], after[after["slot"] == slot]
        if a.empty or b.empty:
            continue
        mb, ma = models_before[slot], models_after[slot]
        changed = [k for k in ("model_string", "via", "host") if mb.get(k) != ma.get(k)]
        for measure in MEASURES:
            key = f"{slot}|{measure}"
            r = change_test(a, b, measure, permutations, rng)
            r.update({"slot": slot, "measure": measure, "model_before": mb["model_string"],
                      "model_after": ma["model_string"], "changed": changed,
                      "kind": "version change (descriptive, not drift)" if changed else "same model (drift test)"})
            results[key] = r
            pvals[key] = r["p_permutation"]
    holm = _holm(pvals)
    for k, r in results.items():
        r["p_holm"] = holm[k]
        r["reportable"] = bool(r["exceeds_spread"] and r["p_holm"] < 0.05)
    return {"family_size": len(results), "results": list(results.values())}


def cross_round_classifier(before: pd.DataFrame, after: pd.DataFrame) -> dict:
    """Exploratory: train on one round's lab slots, test on the other's. Does each lab's style carry over?"""
    out = {}
    for name, prep in {"a_all_text": classifier_text, "c_function_words": function_words_only}.items():
        for train, test, label in ((before, after, "train_before_test_after"),
                                   (after, before, "train_after_test_before")):
            tr, te = train[train["slot"].isin(LAB_SLOTS)], test[test["slot"].isin(LAB_SLOTS)]
            clf = make_classifier().fit(tr["text"].map(prep), tr["slot"])
            pred = clf.predict(te["text"].map(prep))
            truth = te["slot"].to_numpy()
            out[f"{name}|{label}"] = {
                "accuracy": float((pred == truth).mean()), "chance": 1 / len(LAB_SLOTS), "n": len(te),
                "recall_by_slot": {s: float((pred[truth == s] == s).mean()) for s in LAB_SLOTS},
                "labels": LAB_SLOTS, "confusion": confusion_matrix(truth, pred, labels=LAB_SLOTS).tolist(),
            }
    return out


def descriptives_by_slot(df: pd.DataFrame) -> dict:
    out = {}
    for slot, g in df.groupby("slot"):
        out[slot] = {
            "outputs": len(g),
            "story_words_mean": round(float(g[g["cond"] != "D"]["words"].mean()), 1),
            "interview_words_mean": round(float(g[g["cond"] == "D"]["words"].mean()), 1),
            "finish_reasons": g["finish"].value_counts().to_dict(),
            "reasoning_tokens_mean": None if g["reasoning_tokens"].isna().all() else round(float(g["reasoning_tokens"].mean()), 0),
            "masked_names": int(g["substitutions"].sum()),
        }
    return out


def highlights(df: pd.DataFrame, top: int = 10) -> dict:
    """Plain counts for a reader: signature words, repeated phrases, story titles, and one typical story.

    All found by fixed rules (classifier weights, exact phrase counts, nearest to the model's average);
    nothing is chosen or described by a model.
    """
    out = {}
    clf = make_classifier().fit(df["text"].map(classifier_text), df["model"])
    vec, lr = clf.named_steps["tfidfvectorizer"], clf.named_steps["logisticregression"]
    vocab = np.array(vec.get_feature_names_out())
    tf = vec.transform(df["text"].map(classifier_text))
    for i, model in enumerate(lr.classes_):
        g = df[df["model"] == model]
        signature = vocab[np.argsort(lr.coef_[i])[::-1][:top]].tolist()
        grams = Counter()
        for text in g["text"].map(lambda t: re.findall(r"[a-z']+", classifier_text(t).lower())):
            grams.update(" ".join(text[k:k + 4]) for k in range(len(text) - 3))
        phrases = [(p, n) for p, n in grams.most_common(top) if n >= 3]
        titles = Counter()
        for t in g[g["cond"].isin(["S1", "S2"])]["text"]:
            first = next((ln.strip() for ln in t.splitlines() if ln.strip()), "")
            bare = re.sub(r"[#*_\"“”]", "", first).strip()
            if bare and len(bare.split()) <= 8 and not re.search(r"[.!?…]$", bare):
                titles[bare] += 1
        s1 = g[g["cond"] == "S1"]
        typical = None
        if len(s1):
            rows = tf[s1.index.to_numpy()]
            centre = np.asarray(rows.mean(axis=0))
            typical = s1.iloc[int(np.argmax(cosine_similarity(rows, centre).ravel()))]["id"]
        out[model] = {"signature_words": signature, "repeated_4_word_phrases": phrases,
                      "story_titles": titles.most_common(top), "untitled_stories": int(len(g[g["cond"].isin(["S1", "S2"])]) - sum(titles.values())),
                      "typical_self_story_id": typical}
    return out


def compare(root: Path, before_id: str, after_id: str, permutations: int = 10_000) -> dict:
    before, after = round_frame(root, before_id), round_frame(root, after_id)
    mb, ma = round_models(root, before_id), round_models(root, after_id)
    headline = {}
    for rid in (before_id, after_id):
        path = root / "data/derived" / rid / "analysis.json"
        if path.exists():
            q1 = json.loads(path.read_text(encoding="utf-8"))["q1a_classifier"]
            headline[rid] = {k: {"accuracy_mean": v["accuracy_mean"], "per_model_recall": v["per_model_recall"]}
                             for k, v in q1["feature_sets"].items()}
    return {
        "rounds": [before_id, after_id],
        "models": {before_id: mb, after_id: ma},
        "method": __doc__.split("Implementation choices")[1].strip(),
        "descriptives": {before_id: descriptives_by_slot(before), after_id: descriptives_by_slot(after)},
        "q1a_accuracy_by_round": headline,
        "q4_changes": q4_changes(before, after, mb, ma, permutations),
        "exploratory_cross_round_classifier": cross_round_classifier(before, after),
        "highlights": {before_id: highlights(before.reset_index(drop=True)),
                       after_id: highlights(after.reset_index(drop=True))},
    }


def write_compare(root: Path, before_id: str, after_id: str, permutations: int = 10_000) -> Path:
    result = compare(root, before_id, after_id, permutations)
    out = root / "data/derived" / "compare" / f"{before_id}_{after_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return out
