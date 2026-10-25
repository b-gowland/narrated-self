"""Pre-registered measures for a round (docs/PREREGISTRATION.md §7–§8), plus labelled robustness checks.

Everything here is deterministic: word counts, fixed word lists, a published sentiment lexicon and classical
word-statistics classifiers. No model scores, tags or interprets any output (CLAUDE.md rule 1).
"""

from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import (
    LeaveOneGroupOut,
    RepeatedStratifiedKFold,
    StratifiedKFold,
    cross_val_predict,
    cross_val_score,
    permutation_test_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 20261024
MASK = re.compile(r"\[\[x+\]\]")
TOKEN = r"(?u)\b[a-zA-Z][a-zA-Z']*\b"
FUNCTION_WORDS = sorted(ENGLISH_STOP_WORDS)  # fixed, published list (scikit-learn's 318 English stop words)


# --- Loading ---------------------------------------------------------------------------------------------
def load_round(root: Path, round_id: str) -> pd.DataFrame:
    """Masked text joined with run metadata, one row per output."""
    masked = [json.loads(l) for l in (root / "data/derived" / round_id / "masked.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    meta = {}
    for path in (root / "data/raw" / round_id).glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            key = f"{r['round_id']}-{r['provider']}-{r['theme_id']}-{r['condition_id']}-s{r['sample_n']}"
            meta[key] = r
    rows = []
    for m in masked:
        raw = meta[m["id"]]
        usage = raw.get("usage_tokens") or {}
        rows.append({
            "id": m["id"], "model": m["provider"], "theme": m["theme_id"], "cond": m["condition_id"],
            "sample": m["sample_n"], "text": m["masked_text"], "finish": m["finish_reason"],
            "substitutions": m["substitutions"], "words": len(m["masked_text"].split()),
            "output_tokens": usage.get("output"), "reasoning_tokens": usage.get("reasoning"),
        })
    return pd.DataFrame(rows).sort_values("id").reset_index(drop=True)


# --- Text preparation ------------------------------------------------------------------------------------
def classifier_text(text: str) -> str:
    """Remove mask tokens, so 'this model named itself' can't become a feature."""
    return MASK.sub(" ", text)


def strip_formatting(text: str) -> str:
    """Feature set (b): drop Markdown, headings, list marks, rules and a leading story title."""
    lines = [l.strip() for l in classifier_text(text).splitlines()]
    lines = [l for l in lines if l]
    out = []
    for i, line in enumerate(lines):
        if re.fullmatch(r"([-*_=]\s*){3,}", line):
            continue  # horizontal rule
        if line.startswith("#"):
            continue  # Markdown heading (titles, section heads)
        bare = re.sub(r"[*_`\"“”]", "", line).strip()
        if i == 0 and len(bare.split()) <= 12 and not re.search(r"[.!?…]$", bare):
            continue  # a leading title line
        line = re.sub(r"^\s*(?:[-*+•]|\d+[.)])\s+", "", line)  # list marks
        line = re.sub(r"^>\s*", "", line)  # block quotes
        line = re.sub(r"[*_`]+", "", line)  # emphasis and code marks
        out.append(line)
    return " ".join(out)


def function_words_only(text: str) -> str:
    """Feature set (c): only words from the fixed function-word list, in order."""
    return " ".join(w for w in re.findall(r"[a-z']+", classifier_text(text).lower()) if w in ENGLISH_STOP_WORDS)


FEATURE_SETS = {
    "a_all_text": classifier_text,
    "b_formatting_stripped": strip_formatting,
    "c_function_words": function_words_only,
}


# --- Q1a: classifier --------------------------------------------------------------------------------------
def make_classifier():
    # TF-IDF vectors are L2-normalised, so every run is length-normalised (PREREGISTRATION §7).
    return make_pipeline(
        TfidfVectorizer(token_pattern=TOKEN, lowercase=True, sublinear_tf=True, min_df=2),
        LogisticRegression(max_iter=5000, C=1.0, random_state=SEED),
    )


def q1a_classifier(df: pd.DataFrame, repeats: int = 20, permutations: int = 1000) -> dict:
    y = df["model"].to_numpy()
    labels = sorted(set(y))
    chance = 1 / len(labels)
    out = {"chance": chance, "n_outputs": len(df), "labels": labels, "feature_sets": {}}
    rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=repeats, random_state=SEED)
    for name, prep in FEATURE_SETS.items():
        X = df["text"].map(prep).to_numpy()
        fold_scores = cross_val_score(make_classifier(), X, y, cv=rskf, scoring="accuracy")
        per_repeat = fold_scores.reshape(repeats, 5).mean(axis=1)
        _, _, p_value = permutation_test_score(
            make_classifier(), X, y, cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
            n_permutations=permutations, random_state=SEED, scoring="accuracy",
        )
        preds = cross_val_predict(make_classifier(), X, y, cv=StratifiedKFold(5, shuffle=True, random_state=SEED))
        cm = confusion_matrix(y, preds, labels=labels)
        correct = int((preds == y).sum())
        out["feature_sets"][name] = {
            "pooled_correct": correct,
            "sampling_interval_95_wilson": wilson_interval(correct, len(y)),
            "accuracy_mean": float(per_repeat.mean()),
            "accuracy_interval_95": [float(np.percentile(per_repeat, 2.5)), float(np.percentile(per_repeat, 97.5))],
            "permutation_p": float(p_value),
            "confusion_matrix": {"labels": labels, "rows_true_cols_predicted": cm.tolist()},
            "per_model_recall": {lab: float(cm[i, i] / cm[i].sum()) for i, lab in enumerate(labels)},
        }
    a, c = out["feature_sets"]["a_all_text"], out["feature_sets"]["c_function_words"]
    out["drop_a_to_c"] = a["accuracy_mean"] - c["accuracy_mean"]
    return out


# --- Robustness checks (exploratory; not in the pre-registration) -----------------------------------------
def length_baseline(df: pd.DataFrame, repeats: int = 20) -> dict:
    """How far length and layout alone go: word count, paragraph count, mean sentence length."""
    feats = pd.DataFrame({
        "words": df["words"],
        "paragraphs": df["text"].map(lambda t: len([p for p in re.split(r"\n\s*\n", t) if p.strip()])),
        "mean_sentence_words": df["text"].map(
            lambda t: np.mean([len(s.split()) for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()] or [0])),
    }).to_numpy()
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000, random_state=SEED))
    rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=repeats, random_state=SEED)
    per_repeat = cross_val_score(model, feats, df["model"], cv=rskf).reshape(repeats, 5).mean(axis=1)
    return {"accuracy_mean": float(per_repeat.mean()),
            "accuracy_interval_95": [float(np.percentile(per_repeat, 2.5)), float(np.percentile(per_repeat, 97.5))]}


def leave_one_theme_out(df: pd.DataFrame) -> dict:
    """Train on two themes, test on the third: does the classifier generalise to an unseen theme?"""
    out = {}
    for name in ("a_all_text", "c_function_words"):
        X = df["text"].map(FEATURE_SETS[name]).to_numpy()
        scores = cross_val_score(make_classifier(), X, df["model"], groups=df["theme"], cv=LeaveOneGroupOut())
        out[name] = {"accuracy_per_held_out_theme": dict(zip(sorted(df["theme"].unique()), map(float, scores))),
                     "accuracy_mean": float(scores.mean())}
    return out


def leave_one_prompt_out(df: pd.DataFrame) -> dict:
    """Hold out one prompt (theme × condition) at a time, so the three near-duplicate answers to a prompt are
    never split between training and testing. The classifier has still seen the same format in other themes."""
    groups = (df["theme"] + "-" + df["cond"]).to_numpy()
    out = {}
    for name in ("a_all_text", "c_function_words"):
        X = df["text"].map(FEATURE_SETS[name]).to_numpy()
        scores = cross_val_score(make_classifier(), X, df["model"], groups=groups, cv=LeaveOneGroupOut())
        out[name] = {"accuracy_mean": float(scores.mean()), "prompts_held_out": int(len(scores))}
    return out


def leave_one_format_out(df: pd.DataFrame) -> dict:
    """Train on three formats, test on the fourth: does a model's recognisable style carry across genres?"""
    out = {}
    for name in ("a_all_text", "c_function_words"):
        X = df["text"].map(FEATURE_SETS[name]).to_numpy()
        scores = cross_val_score(make_classifier(), X, df["model"], groups=df["cond"], cv=LeaveOneGroupOut())
        out[name] = {"accuracy_per_held_out_format": dict(zip(sorted(df["cond"].unique()), map(float, scores))),
                     "accuracy_mean": float(scores.mean())}
    return out


def wilson_interval(correct: int, n: int, z: float = 1.96) -> list[float]:
    p = correct / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [float(centre - half), float(centre + half)]


def stories_only(df: pd.DataFrame, repeats: int = 20) -> dict:
    """Self-stories and kin-stories only (the quiz pool): no interview answers to tell models apart by format."""
    sub = df[df["cond"].isin(["S1", "S2"])]
    X = sub["text"].map(FEATURE_SETS["a_all_text"]).to_numpy()
    rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=repeats, random_state=SEED)
    per_repeat = cross_val_score(make_classifier(), X, sub["model"], cv=rskf).reshape(repeats, 5).mean(axis=1)
    return {"n_outputs": int(len(sub)), "accuracy_mean": float(per_repeat.mean()),
            "accuracy_interval_95": [float(np.percentile(per_repeat, 2.5)), float(np.percentile(per_repeat, 97.5))]}


# --- Q2: consistency --------------------------------------------------------------------------------------
def q2_consistency(df: pd.DataFrame, boots: int = 2000) -> dict:
    """Within-model vs between-model cosine similarity, compared within the same theme and condition."""
    vec = TfidfVectorizer(token_pattern=TOKEN, lowercase=True, sublinear_tf=True, min_df=2)
    X = vec.fit_transform(df["text"].map(classifier_text))
    sim = (X @ X.T).toarray()
    rng = np.random.default_rng(SEED)
    out = {}
    for model in sorted(df["model"].unique()):
        cells = []
        for (theme, cond), g in df.groupby(["theme", "cond"]):
            own = g.index[g["model"] == model].tolist()
            other = g.index[g["model"] != model].tolist()
            within = np.mean([sim[i, j] for i, j in combinations(own, 2)])
            between = np.mean([sim[i, j] for i in own for j in other])
            cells.append(within - between)
        cells = np.array(cells)
        boot = [rng.choice(cells, len(cells), replace=True).mean() for _ in range(boots)]
        out[model] = {"within_minus_between": float(cells.mean()), "cells": len(cells),
                      "interval_95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]}
    return out


# --- Q3: framing (exploratory in R0) -----------------------------------------------------------------------
def _term_pattern(terms: list[str]) -> re.Pattern:
    parts = sorted((re.escape(t) for t in terms), key=len, reverse=True)
    return re.compile(r"(?<![\w'])(?:" + "|".join(parts) + r")(?![\w'])", re.IGNORECASE)


def lexicon_rates(df: pd.DataFrame, root: Path) -> pd.DataFrame:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    lex = yaml.safe_load((root / "protocol" / "lexicons.yaml").read_text(encoding="utf-8"))
    pats = {k: _term_pattern(lex[k]["terms"]) for k in ("hedging", "lm_self_reference", "first_person")}
    vader = SentimentIntensityAnalyzer()
    rows = []
    for _, r in df.iterrows():
        text = classifier_text(r["text"])
        words = max(len(text.split()), 1)
        row = {k: len(p.findall(text)) * 1000 / words for k, p in pats.items()}
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        row["sentiment"] = float(np.mean([vader.polarity_scores(s)["compound"] for s in sentences])) if sentences else 0.0
        rows.append(row)
    return pd.concat([df[["id", "model", "theme", "cond", "sample"]].reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def _holm(pvals: dict[str, float]) -> dict[str, float]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, adjusted, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        adjusted[k] = running
    return adjusted


def q3_framing(rates: pd.DataFrame, boots: int = 2000) -> dict:
    """Difference-in-differences: each model's (S1 - S3) and (D - S2) against the mean of the other models.

    With a balanced design (every model × theme × condition has 3 samples) these contrasts equal those from the
    pre-registered linear model rate ~ model × condition + theme. Bootstrap resamples outputs within each
    model × theme × condition cell.
    """
    rng = np.random.default_rng(SEED)
    measures = ["hedging", "lm_self_reference", "first_person", "sentiment"]
    contrasts = {"S1_minus_S3": ("S1", "S3"), "D_minus_S2": ("D", "S2")}
    models = sorted(rates["model"].unique())
    cells = {k: g[measures].to_numpy() for k, g in rates.groupby(["model", "theme", "cond"])}

    def contrast_table(cell_means):
        table = {}
        for m in models:
            for cname, (c1, c2) in contrasts.items():
                v1 = np.mean([cell_means[(m, t, c1)] for t in ("T1", "T2", "T3") if (m, t, c1) in cell_means], axis=0)
                v2 = np.mean([cell_means[(m, t, c2)] for t in ("T1", "T2", "T3") if (m, t, c2) in cell_means], axis=0)
                table[(m, cname)] = v1 - v2
        return table

    observed = contrast_table({k: v.mean(axis=0) for k, v in cells.items()})
    boot_tables = []
    for _ in range(boots):
        resampled = {k: v[rng.integers(0, len(v), len(v))].mean(axis=0) for k, v in cells.items()}
        boot_tables.append(contrast_table(resampled))

    out, pvals = {}, {}
    for cname in contrasts:
        for i, meas in enumerate(measures):
            for m in models:
                def gap(table):
                    others = np.mean([table[(o, cname)][i] for o in models if o != m])
                    return table[(m, cname)][i] - others
                est = gap(observed)
                dist = np.array([gap(t) for t in boot_tables])
                p = float(min(1.0, 2 * min((dist <= 0).mean(), (dist >= 0).mean())))
                key = f"{cname}|{meas}|{m}"
                pvals[key] = p
                out[key] = {"contrast": cname, "measure": meas, "model": m,
                            "model_contrast": float(observed[(m, cname)][i]),
                            "gap_vs_other_models": float(est),
                            "interval_95": [float(np.percentile(dist, 2.5)), float(np.percentile(dist, 97.5))],
                            "p_bootstrap": p}
    holm = _holm(pvals)
    for k in out:
        out[k]["p_holm"] = holm[k]
    return {"family_size": len(out), "results": list(out.values())}


# --- Descriptives -----------------------------------------------------------------------------------------
def descriptives(df: pd.DataFrame) -> dict:
    words = df.groupby(["model", "cond"])["words"].agg(["mean", "min", "max"]).round(1)
    return {
        "outputs": int(len(df)),
        "finish_reasons": df["finish"].value_counts().to_dict(),
        "outputs_under_100_words": int((df["words"] < 100).sum()),
        "words_by_model_and_condition": {f"{m}|{c}": row.to_dict() for (m, c), row in words.iterrows()},
        "story_words_by_model": df[df["cond"] != "D"].groupby("model")["words"].mean().round(1).to_dict(),
        "interview_words_by_model": df[df["cond"] == "D"].groupby("model")["words"].mean().round(1).to_dict(),
        "reasoning_tokens_mean_by_model": df.groupby("model")["reasoning_tokens"].mean().round(0).to_dict(),
        "masked_names_by_model": df.groupby("model")["substitutions"].sum().to_dict(),
    }


def analyse(root: Path, round_id: str, quick: bool = False) -> dict:
    df = load_round(root, round_id)
    repeats, perms, boots = (2, 20, 100) if quick else (20, 1000, 2000)
    rates = lexicon_rates(df, root)
    return {
        "round": round_id,
        "settings": {"seed": SEED, "cv": f"5-fold x {repeats} repeats", "permutations": perms, "bootstrap": boots,
                     "function_word_list": "scikit-learn ENGLISH_STOP_WORDS (318 words)"},
        "descriptives": descriptives(df),
        "q1a_classifier": q1a_classifier(df, repeats=repeats, permutations=perms),
        "robustness": {
            "length_and_layout_only": length_baseline(df, repeats=repeats),
            "leave_one_theme_out": leave_one_theme_out(df),
            "leave_one_prompt_out": leave_one_prompt_out(df),
            "leave_one_format_out": leave_one_format_out(df),
            "stories_only_s1_s2": stories_only(df, repeats=repeats),
        },
        "q2_consistency": q2_consistency(df, boots=boots),
        "q3_framing_exploratory": q3_framing(rates, boots=boots),
        "_rates": rates,
    }
