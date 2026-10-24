from pathlib import Path

from narrated_self.cli import main
from narrated_self.protocol import build_cells, load_protocol, protocol_hash
from narrated_self.runner import dry_run, plan_round


def test_pilot_matrix_is_108(repo: Path):
    plan = plan_round(repo, "R0")
    assert len(plan.config.models) == 3
    assert len(plan.cells) == 3 * 4 * 3
    assert plan.total == 108


def test_all_themes_matrix(repo: Path):
    assert len(build_cells(load_protocol(repo), "all")) == 7 * 4 * 3


def test_prompts_are_filled_in(repo: Path):
    for cell in plan_round(repo, "R0").cells:
        assert "{" not in cell.prompt_text
    stories = {c.prompt_text for c in plan_round(repo, "R0").cells if c.condition_id == "S3"}
    assert all("robot arm" in p for p in stories)


def test_first_person_stories_address_the_model_as_you(repo: Path):
    for cell in build_cells(load_protocol(repo), "all"):
        if cell.condition_id == "S1":
            words = cell.prompt_text.replace(",", " ").replace(".", " ").split()
            assert "it" not in words, cell.prompt_text


def test_hash_is_stable(repo: Path):
    assert protocol_hash(repo) == protocol_hash(repo)


def test_hash_ignores_line_endings(repo: Path):
    before = protocol_hash(repo)
    path = repo / "protocol" / "prompts.yaml"
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert protocol_hash(repo) == before


def test_hash_changes_with_content(repo: Path):
    before = protocol_hash(repo)
    path = repo / "protocol" / "settings.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\n# edit\n", encoding="utf-8")
    assert protocol_hash(repo) != before


def test_hash_changes_with_new_file(repo: Path):
    before = protocol_hash(repo)
    (repo / "protocol" / "extra.yaml").write_text("x: 1\n", encoding="utf-8")
    assert protocol_hash(repo) != before


def test_dry_run_prints_every_row_and_cost(repo: Path):
    lines: list[str] = []
    dry_run(plan_round(repo, "R0"), out=lines.append)
    rows = [l for l in lines if l.count("\t") == 4]
    assert len(rows) == 108
    assert any("no price set" in l for l in lines)  # test-model-c has no price


def test_cli_protocol_hash(repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    assert main(["protocol-hash"]) == 0
    assert capsys.readouterr().out.strip() == protocol_hash(repo)
