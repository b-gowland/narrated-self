import numpy as np
import pandas as pd

from narrated_self.compare import change_test, slot_of


def frame(shift=0.0, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for t in ("T1", "T2", "T3"):
        for c in ("D", "S1", "S2", "S3"):
            for s in range(3):
                rows.append({"theme": t, "cond": c, "sample": s, "hedging": rng.normal(5 + shift, 1)})
    return pd.DataFrame(rows)


def test_open_weight_models_share_one_slot():
    assert slot_of("anthropic") == "anthropic"
    assert slot_of("xiaomi") == slot_of("moonshotai") == "open-weight"


def test_no_change_is_not_reportable():
    r = change_test(frame(seed=1), frame(seed=2), "hedging", permutations=500)
    assert r["p_permutation"] > 0.05 or not r["exceeds_spread"]


def test_a_large_shift_is_detected_and_exceeds_spread():
    r = change_test(frame(seed=1), frame(shift=4, seed=2), "hedging", permutations=500)
    assert r["p_permutation"] < 0.01 and r["exceeds_spread"] and r["change"] > 3
