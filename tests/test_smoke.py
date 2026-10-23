import json
from pathlib import Path

from narrated_self.runner import plan_round, raw_path, run_round
from narrated_self.smoke import smoke_plan, summarise
from test_runner import fakes


def test_smoke_is_one_sample_per_prompt_under_r_minus_1(repo: Path):
    plan = smoke_plan(plan_round(repo, "R0"))
    assert plan.config.round_id == "R-1"
    assert plan.total == 3 * 12
    assert run_round(repo, plan, adapters=fakes(), sleep=lambda s: None, out=lambda s: None) == 0
    recs = [json.loads(l) for l in raw_path(repo, "R-1", "openai").read_text(encoding="utf-8").splitlines()]
    assert len(recs) == 12
    assert {r["sample_n"] for r in recs} == {1}
    assert {r["round_id"] for r in recs} == {"R-1"}
    assert not raw_path(repo, "R0", "openai").exists()


def test_smoke_summary_never_prints_response_text(repo: Path):
    plan = smoke_plan(plan_round(repo, "R0"))
    run_round(repo, plan, adapters=fakes(), sleep=lambda s: None, out=lambda s: None)
    lines: list[str] = []
    summarise(repo, plan, out=lines.append)
    assert not any("reply" in l for l in lines)  # fake replies are "reply N"
    assert any("12 outputs" in l for l in lines)
