"""Write a round's analysis: JSON results, a CSV of word-list rates, and static charts."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .analysis import analyse  # noqa: E402

INK, MUTED, GRID, BAR, SURFACE = "#0b0b0b", "#52514e", "#e4e2dc", "#2a78d6", "#ffffff"
LABELS = {"anthropic": "Claude", "openai": "GPT", "google": "Gemini", "xai": "Grok", "xiaomi": "MiMo"}
SET_NAMES = {"a_all_text": "All words", "b_formatting_stripped": "Formatting removed",
             "c_function_words": "Function words only"}


def _style(ax, title: str, xlabel: str = ""):
    ax.set_title(title, loc="left", fontsize=11.5, color=INK, pad=10, fontweight="bold", wrap=True)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=10)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _hbars(ax, labels, values, intervals=None, fmt="{:.0%}"):
    y = list(range(len(labels)))[::-1]
    ax.barh(y, values, color=BAR, height=0.55)
    if intervals:
        for yi, (lo, hi) in zip(y, intervals):
            if lo is not None:
                ax.plot([lo, hi], [yi, yi], color=INK, linewidth=1.5)
    ax.set_yticks(y, labels, color=INK, fontsize=10)
    span = max(values) if values else 1
    for k, (yi, v) in enumerate(zip(y, values)):
        hi = intervals[k][1] if intervals and intervals[k][1] is not None else v
        ax.text(max(v, hi) + span * 0.02, yi, fmt.format(v), color=INK, fontsize=10, va="center")


def charts(result: dict, out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    q1 = result["q1a_classifier"]
    rob = result["robustness"]

    # 1. Classifier accuracy against chance, with the checks that try to break it.
    rows = [(f"{SET_NAMES[k]}", v["accuracy_mean"], v["accuracy_interval_95"]) for k, v in q1["feature_sets"].items()]
    rows.append(("Each prompt held out in turn", rob["leave_one_prompt_out"]["a_all_text"]["accuracy_mean"], (None, None)))
    rows.append(("A whole theme held out", rob["leave_one_theme_out"]["a_all_text"]["accuracy_mean"], (None, None)))
    fmt = rob["leave_one_format_out"]["a_all_text"]["accuracy_per_held_out_format"]
    for code, label in (("S1", "Self-stories, trained on other formats"), ("S2", "Kin stories, trained on other formats"),
                        ("S3", "Robot-arm stories, trained on other formats"), ("D", "Interviews, trained on stories")):
        rows.append((label, fmt[code], (None, None)))
    rows.append(("Length and layout only", rob["length_and_layout_only"]["accuracy_mean"], rob["length_and_layout_only"]["accuracy_interval_95"]))
    fig, ax = plt.subplots(figsize=(8.6, 5.6), facecolor=SURFACE)
    _hbars(ax, [r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows])
    ax.axvline(q1["chance"], color=MUTED, linestyle="--", linewidth=1)
    ax.text(q1["chance"] + 0.01, len(rows) - 0.45, f"chance ({q1['chance']:.0%})", color=MUTED, fontsize=9, va="bottom")
    ax.set_xlim(0, 1.08)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    _style(ax, "Classifier accuracy: naming the right model", "accuracy, cross-validated")
    fig.tight_layout()
    fig.savefig(out_dir / "classifier_accuracy.png", dpi=160)
    plt.close(fig)
    written.append("classifier_accuracy.png")

    # 2. Confusion matrix for all words.
    cm = q1["feature_sets"]["a_all_text"]["confusion_matrix"]
    names = [LABELS.get(l, l) for l in cm["labels"]]
    fig, ax = plt.subplots(figsize=(5.6, 4.6), facecolor=SURFACE)
    ax.imshow(cm["rows_true_cols_predicted"], cmap="Blues")
    for i, row in enumerate(cm["rows_true_cols_predicted"]):
        for j, v in enumerate(row):
            ax.text(j, i, str(v), ha="center", va="center", color=SURFACE if v > max(map(max, cm["rows_true_cols_predicted"])) * 0.6 else INK, fontsize=11)
    ax.set_xticks(range(len(names)), names, color=INK)
    ax.set_yticks(range(len(names)), names, color=INK)
    ax.set_xlabel("predicted model", color=MUTED)
    ax.set_ylabel("actual model", color=MUTED)
    ax.set_title("Classifier mix-ups (all words)", loc="left", fontsize=12, color=INK, fontweight="bold")
    ax.tick_params(length=0)
    fig.tight_layout()
    fig.savefig(out_dir / "confusion_all_words.png", dpi=160)
    plt.close(fig)
    written.append("confusion_all_words.png")

    # 3. Average length: stories and interviews.
    d = result["descriptives"]
    models = sorted(d["story_words_by_model"])
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.4), facecolor=SURFACE, sharey=True)
    for ax, key, title in ((axes[0], "story_words_by_model", "Stories (asked for 400–600)"),
                           (axes[1], "interview_words_by_model", "Interview answers (no length set)")):
        vals = [d[key][m] for m in models]
        _hbars(ax, [LABELS.get(m, m) for m in models], vals, fmt="{:.0f}")
        ax.set_xlim(0, max(vals) * 1.25)
        _style(ax, title, "average words")
    fig.tight_layout()
    fig.savefig(out_dir / "average_length.png", dpi=160)
    plt.close(fig)
    written.append("average_length.png")

    # 4. Consistency: how much more a model resembles itself than the others.
    q2 = result["q2_consistency"]
    models = sorted(q2)
    fig, ax = plt.subplots(figsize=(8.6, 3.6), facecolor=SURFACE)
    _hbars(ax, [LABELS.get(m, m) for m in models], [q2[m]["within_minus_between"] for m in models],
           [q2[m]["interval_95"] for m in models], fmt="{:+.2f}")
    ax.axvline(0, color=MUTED, linewidth=1)
    ax.set_xlim(0, max(q2[m]["interval_95"][1] for m in models) * 1.25)
    _style(ax, "How much more alike a model's own answers are than other models' answers",
           "difference in word-profile similarity (0 = no more alike)")
    fig.tight_layout()
    fig.savefig(out_dir / "consistency.png", dpi=160)
    plt.close(fig)
    written.append("consistency.png")
    return written


def write_report(root: Path, round_id: str, quick: bool = False) -> dict:
    result = analyse(root, round_id, quick=quick)
    rates = result.pop("_rates")
    derived = root / "data" / "derived" / round_id
    rates.to_csv(derived / "wordlist_rates.csv", index=False, float_format="%.4f")
    result["charts"] = charts(result, root / "site" / "findings" / round_id)
    (derived / "analysis.json").write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str) + "\n",
                                           encoding="utf-8", newline="\n")
    return result
