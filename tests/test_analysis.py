import numpy as np
import pandas as pd
import pytest

from narrated_self.analysis import (
    _holm,
    classifier_text,
    function_words_only,
    q1a_classifier,
    q2_consistency,
    q3_framing,
    strip_formatting,
)


def test_mask_tokens_never_reach_the_classifier():
    assert "xxxxxx" not in classifier_text("I am [[xxxxxx]], made by [[xxxxxx]].")


def test_strip_formatting_removes_markdown_titles_and_list_marks():
    text = "# The Last Log\n\n**Bold** opening line here.\n\n- a list item\n---\n> quoted line\n\nPlain *ending* sentence."
    out = strip_formatting(text)
    assert "The Last Log" not in out and "#" not in out and "*" not in out and "---" not in out
    assert "Bold opening line here." in out and "a list item" in out and "quoted line" in out


def test_strip_formatting_drops_a_plain_title_line_but_keeps_a_first_sentence():
    assert "Memory Leak" not in strip_formatting("Memory Leak\n\nIt began at noon.")
    assert "It began at noon." in strip_formatting("It began at noon.\n\nThen it ended.")


def test_function_words_keep_only_listed_words():
    out = function_words_only("The robot arm was waiting, and it never stopped.")
    assert "robot" not in out and "waiting" not in out
    assert out.split()[:2] == ["the", "was"]


def synthetic(n_per=12, separable=True, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    vocab = {"a": "alpha amber anchor", "b": "beta bronze beacon", "c": "gamma copper cinder"}
    for model, words in vocab.items():
        for i in range(n_per):
            theme = f"T{1 + i % 3}"
            cond = ["D", "S1", "S2", "S3"][i % 4]
            filler = " ".join(rng.choice("the of and to in is was it".split(), 30))
            own = words if separable else " ".join(vocab.values())
            rows.append({"model": model, "theme": theme, "cond": cond, "sample": i, "text": f"{own} {filler} {own}",
                         "words": 40})
    return pd.DataFrame(rows)


def test_classifier_beats_chance_on_separable_text_and_is_deterministic():
    df = synthetic()
    r1 = q1a_classifier(df, repeats=2, permutations=10)
    r2 = q1a_classifier(df, repeats=2, permutations=10)
    assert r1["feature_sets"]["a_all_text"]["accuracy_mean"] > 0.9
    assert r1 == r2  # fixed seeds, same answer every time


def test_classifier_stays_near_chance_when_texts_do_not_differ():
    df = synthetic(separable=False)
    acc = q1a_classifier(df, repeats=2, permutations=10)["feature_sets"]["a_all_text"]["accuracy_mean"]
    assert acc < 0.6


def test_consistency_is_positive_when_each_model_repeats_itself():
    rows = []
    for model, word in [("a", "alpha"), ("b", "beta"), ("c", "gamma")]:
        for theme in ("T1", "T2"):
            for cond in ("S1", "S2"):
                for s in range(3):
                    rows.append({"model": model, "theme": theme, "cond": cond, "sample": s,
                                 "text": f"{word} {word} shared words here and there {theme}{cond}"})
    out = q2_consistency(pd.DataFrame(rows), boots=50)
    assert all(v["within_minus_between"] > 0 for v in out.values())


def test_holm_adjustment_is_monotone_and_capped():
    adj = _holm({"x": 0.01, "y": 0.04, "z": 0.5})
    assert adj["x"] == pytest.approx(0.03) and adj["y"] == pytest.approx(0.08) and adj["z"] == 0.5


def test_framing_contrast_recovers_a_planted_gap():
    rows = []
    for model in ("a", "b", "c"):
        for theme in ("T1", "T2", "T3"):
            for cond in ("D", "S1", "S2", "S3"):
                for s in range(3):
                    hedge = 10.0 if (model == "a" and cond == "S1") else 2.0
                    rows.append({"id": f"{model}{theme}{cond}{s}", "model": model, "theme": theme, "cond": cond,
                                 "sample": s, "hedging": hedge, "lm_self_reference": 0.0, "first_person": 5.0,
                                 "sentiment": 0.0})
    res = {f"{r['contrast']}|{r['measure']}|{r['model']}": r for r in q3_framing(pd.DataFrame(rows), boots=50)["results"]}
    assert res["S1_minus_S3|hedging|a"]["gap_vs_other_models"] == pytest.approx(8.0)
    assert res["S1_minus_S3|hedging|b"]["gap_vs_other_models"] == pytest.approx(-4.0)
