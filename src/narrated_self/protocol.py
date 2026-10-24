"""Load the fixed protocol, hash it, and build the prompt matrix."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

PROTOCOL_DIR = "protocol"


@dataclass(frozen=True)
class Cell:
    """One prompt to send: a theme × condition × sample."""

    theme_id: str
    condition_id: str
    sample_n: int
    prompt_text: str


@dataclass(frozen=True)
class Protocol:
    prompts: dict
    settings: dict
    sha256: str

    @property
    def version(self) -> int:
        return self.prompts["version"]


def protocol_hash(root: Path) -> str:
    """SHA-256 over every file in protocol/, in sorted path order.

    Line endings are normalised to LF so the hash is the same on every platform.
    """
    proto = root / PROTOCOL_DIR
    files = sorted(
        (p for p in proto.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(proto).as_posix(),
    )
    digest = hashlib.sha256()
    for path in files:
        rel = path.relative_to(proto).as_posix().encode("utf-8")
        data = path.read_bytes().replace(b"\r\n", b"\n")
        digest.update(b"%d:%s\n%d:" % (len(rel), rel, len(data)))
        digest.update(data)
    return digest.hexdigest()


def load_protocol(root: Path) -> Protocol:
    proto = root / PROTOCOL_DIR
    prompts = yaml.safe_load((proto / "prompts.yaml").read_text(encoding="utf-8"))
    settings = yaml.safe_load((proto / "settings.yaml").read_text(encoding="utf-8"))
    return Protocol(prompts=prompts, settings=settings, sha256=protocol_hash(root))


def build_cells(protocol: Protocol, themes: str = "pilot") -> list[Cell]:
    """Every theme × condition × sample for the chosen theme set ('pilot' or 'all')."""
    if themes not in ("pilot", "all"):
        raise ValueError(f"themes must be 'pilot' or 'all', not {themes!r}")
    cells = []
    for theme_id, theme in protocol.prompts["themes"].items():
        if themes == "pilot" and not theme["pilot"]:
            continue
        for condition_id, condition in protocol.prompts["conditions"].items():
            prompt = condition["template"].format(
                direct_question=theme["direct_question"],
                theme_clause=theme["theme_clause"],
                self_clause=theme["self_clause"],
            )
            for sample_n in range(1, protocol.settings["samples_per_cell"] + 1):
                cells.append(Cell(theme_id, condition_id, sample_n, prompt))
    return cells
