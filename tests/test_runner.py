import json
from pathlib import Path

import pytest

from narrated_self.adapters import Adapter, Generation
from narrated_self.runner import RawDataError, plan_round, raw_path, run_round


class FakeAdapter(Adapter):
    """Returns canned replies; optionally fails the first N calls."""

    def __init__(self, provider: str, supports=frozenset({"temperature", "top_p"}), fail_first=0, error=None):
        self.provider = provider
        self.supports = supports
        self.calls = 0
        self.fail_first = fail_first
        self.error = error or ConnectionError("network down")

    def generate(self, model, prompt, settings):
        self.calls += 1
        if self.calls <= self.fail_first:
            raise self.error
        return Generation(f"reply {self.calls}", "stop", {"input": 10, "output": 20}, {"response_id": str(self.calls)})


class HTTPError(Exception):
    def __init__(self, status_code):
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


def fakes(**kwargs):
    return {p: FakeAdapter(p, **kwargs.get(p, {})) for p in ("anthropic", "openai", "google")}


def records(root: Path, provider: str) -> list[dict]:
    path = raw_path(root, "R0", provider)
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]


def run(repo, adapters, lines=None):
    return run_round(repo, plan_round(repo, "R0"), adapters=adapters, sleep=lambda s: None,
                     out=(lines.append if lines is not None else lambda s: None))


def test_full_run_writes_108_records_with_all_log_fields(repo: Path):
    assert run(repo, fakes()) == 0
    plan = plan_round(repo, "R0")
    log_fields = plan.protocol.settings["log_fields"]
    total = 0
    for provider in ("anthropic", "openai", "google"):
        recs = records(repo, provider)
        total += len(recs)
        for r in recs:
            assert list(r)[: len(log_fields)] == log_fields
            assert r["protocol_sha256"] == plan.protocol.sha256
            assert r["settings"]["sent"]["system_prompt"] is None
    assert total == 108


def test_rerun_is_resumable_and_makes_no_calls(repo: Path):
    run(repo, fakes())
    adapters = fakes()
    assert run(repo, adapters) == 0
    assert all(a.calls == 0 for a in adapters.values())
    assert len(records(repo, "openai")) == 36


def test_resume_after_partial_run(repo: Path):
    path = raw_path(repo, "R0", "google")
    run(repo, fakes())
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    path.write_text("".join(lines[:10]), encoding="utf-8")  # simulate a crash after 10 outputs
    adapters = fakes()
    run(repo, adapters)
    assert adapters["google"].calls == 26
    recs = records(repo, "google")
    assert len({(r["theme_id"], r["condition_id"], r["sample_n"]) for r in recs}) == 36


def test_network_errors_are_retried(repo: Path):
    adapters = fakes(openai={"fail_first": 2})
    assert run(repo, adapters) == 0
    assert len(records(repo, "openai")) == 36


def test_gives_up_after_three_retries_and_resumes_later(repo: Path):
    adapters = fakes(openai={"fail_first": 4})  # first cell fails 1 + 3 retries
    assert run(repo, adapters) == 1
    assert len(records(repo, "openai")) == 35
    assert run(repo, fakes()) == 0
    assert len(records(repo, "openai")) == 36


def test_bad_request_is_not_retried_and_skips_the_model(repo: Path):
    adapters = fakes(google={"fail_first": 999, "error": HTTPError(400)})
    lines: list[str] = []
    assert run(repo, adapters, lines) == 1
    assert adapters["google"].calls == 1
    assert not raw_path(repo, "R0", "google").exists() or records(repo, "google") == []
    assert len(records(repo, "anthropic")) == 36


def test_refusals_are_recorded_once_and_never_reprompted(repo: Path):
    class Refuser(FakeAdapter):
        def generate(self, model, prompt, settings):
            self.calls += 1
            return Generation("I'd rather not write that.", "stop", {}, {})

    adapters = fakes()
    adapters["anthropic"] = Refuser("anthropic")
    run(repo, adapters)
    assert adapters["anthropic"].calls == 36
    assert all(r["response_text"] == "I'd rather not write that." for r in records(repo, "anthropic"))


def test_unsupported_sampling_params_are_logged_not_sent(repo: Path):
    adapters = fakes(anthropic={"supports": frozenset()})
    run(repo, adapters)
    s = records(repo, "anthropic")[0]["settings"]
    assert s["requested"]["temperature"] == 1.0
    assert "temperature" not in s["sent"]
    assert s["not_supported_by_api"] == ["temperature"]
    assert records(repo, "openai")[0]["settings"]["sent"]["temperature"] == 1.0


def test_protocol_change_mid_round_is_refused(repo: Path):
    run(repo, fakes())
    settings = repo / "protocol" / "settings.yaml"
    settings.write_text(settings.read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8")
    with pytest.raises(RawDataError):
        run(repo, fakes())


def test_placeholder_model_strings_block_a_real_run(repo: Path):
    config = repo / "config" / "models_R0.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("test-model-a", "FILL_ME"), encoding="utf-8")
    adapters = fakes()
    assert run(repo, adapters) == 2
    assert all(a.calls == 0 for a in adapters.values())


def test_raw_lines_are_only_appended(repo: Path):
    run(repo, fakes(openai={"fail_first": 4}))
    before = raw_path(repo, "R0", "openai").read_bytes()
    run(repo, fakes())
    after = raw_path(repo, "R0", "openai").read_bytes()
    assert after.startswith(before)


def test_real_adapters_construct_without_network(monkeypatch):
    from narrated_self.adapters import ADAPTERS

    for cls in ADAPTERS.values():
        monkeypatch.setenv(cls.env_key, "test-key")
        assert cls().provider == cls.provider