"""Repo QA: security, personal details, links, wording and currency checks.

Run from the repo root:  uv run python scripts/qa.py [--no-network]
Prints PASS / WARN / FAIL per check and exits 1 if anything FAILs.
Model outputs (response_text in data/raw/) are never scanned for wording or edited.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NETWORK = "--no-network" not in sys.argv
SITE = "https://narratedself.airiskpractice.org"
# The QA tools quote the patterns they look for, so they are not scanned for them.
SELF = {"scripts/qa.py", ".claude/skills/qa/SKILL.md", ".github/workflows/pages.yml"}
results: list[tuple[str, str, list[str]]] = []


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout


def tracked() -> list[Path]:
    return [ROOT / p for p in git("ls-files").splitlines()]


def text_files(exclude_raw: bool = True) -> list[Path]:
    out = []
    for p in tracked():
        rel = p.relative_to(ROOT).as_posix()
        if exclude_raw and rel.startswith("data/raw/"):
            continue
        if rel in SELF:
            continue
        if rel == "uv.lock" or p.suffix in (".png", ".jpg", ".ico"):
            continue
        out.append(p)
    return out


def prose_files() -> list[Path]:
    """User-facing writing: docs, README, CLAUDE.md, the site."""
    return [p for p in text_files() if p.suffix in (".md", ".html")]


def report(name: str, status: str, details: list[str]) -> None:
    results.append((name, status, details))


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


# 1. Secrets ---------------------------------------------------------------
SECRET = re.compile(
    r"sk-(?:ant|or|proj)-[A-Za-z0-9_-]{8,}|AIza[0-9A-Za-z_-]{20,}|xai-[A-Za-z0-9]{20,}"
    r"|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
)


def check_secrets() -> None:
    found = []
    for p in text_files(exclude_raw=False):
        for n, line in enumerate(read(p).splitlines(), 1):
            if SECRET.search(line):
                found.append(f"{p.relative_to(ROOT).as_posix()}:{n}")
    history = SECRET.findall(git("log", "--all", "-p"))
    if history:
        found.append(f"{len(history)} match(es) in git history (run: git log --all -p | grep the pattern)")
    banned = [p for p in git("ls-files").splitlines() if re.search(r"(^|/)\.env$|^data/keys/", p)]
    found += [f"tracked file that must never be committed: {p}" for p in banned]
    report("Secrets (files, history, .env, data/keys)", "FAIL" if found else "PASS", found)


# 2. Personal details ------------------------------------------------------
PERSONAL = re.compile(r"[A-Za-z0-9._%+-]+@(?:gmail|outlook|hotmail|yahoo|icloud)\.com|[A-Z]:\\Users\\|/home/[a-z]+/|AppData", re.I)


def check_personal() -> None:
    found = []
    for p in text_files():
        for n, line in enumerate(read(p).splitlines(), 1):
            if PERSONAL.search(line):
                found.append(f"{p.relative_to(ROOT).as_posix()}:{n}")
    # Raw data: scan everything except the model's own reply text.
    for p in (ROOT / "data" / "raw").rglob("*.jsonl"):
        for n, line in enumerate(read(p).splitlines(), 1):
            record = json.loads(line)
            record.pop("response_text", None)
            if PERSONAL.search(json.dumps(record)):
                found.append(f"{p.relative_to(ROOT).as_posix()}:{n} (metadata)")
    emails = sorted(set(git("log", "--format=%ae").split()))
    exposed = [e for e in emails if not e.endswith("users.noreply.github.com")]
    if exposed:
        found.append(f"commit author emails visible in public history: {', '.join(exposed)}")
    report("Personal details (emails, local paths, commit authors)", "WARN" if found else "PASS", found)


# 3. Links -----------------------------------------------------------------
URL = re.compile(r"https?://[^\s)\"'<>`\]]+")
MD_LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def check_links() -> None:
    broken, checked = [], set()
    for p in prose_files():
        text = read(p)
        for target in MD_LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (p.parent / target).exists() and not (ROOT / target).exists():
                broken.append(f"{p.relative_to(ROOT).as_posix()}: missing file link '{target}'")
        if not NETWORK:
            continue
        for url in URL.findall(text):
            url = url.rstrip(".,;:")
            if url in checked or "fonts.g" in url or url.endswith("/api/v1"):
                continue
            checked.add(url)
            try:
                req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0 (narrated-self QA)"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    if r.status >= 400:
                        broken.append(f"{url} -> {r.status}")
            except urllib.error.HTTPError as e:
                # 401/403/429 usually mean "exists but blocks bots"; flag for a manual look, not a failure.
                broken.append(f"{url} -> {e.code}{' (check by hand)' if e.code in (401, 403, 429) else ''}")
            except Exception as e:
                pending = url.startswith(SITE)
                broken.append(f"{url} -> {type(e).__name__}{' (check by hand: site not live yet?)' if pending else ''}")
    hard = [b for b in broken if "check by hand" not in b]
    status = "FAIL" if hard else ("WARN" if broken else "PASS")
    report(f"Links ({len(checked)} web links checked{'' if NETWORK else '; network skipped'})", status, broken)


# 4. Wording ---------------------------------------------------------------
# Common tells, drawn from Wikipedia's "Signs of AI writing" (WikiProject AI Cleanup) and the Humanizer skill.
AI_TELLS = [
    r"\bdelve", r"\btapestry\b", r"\btestament to\b", r"\bit'?s worth noting\b", r"\bworth noting\b",
    r"\bin today'?s\b", r"\bever-evolving\b", r"\blandscape\b", r"\bseamless(ly)?\b", r"\brobust\b",
    r"\bleverag(e|ing)\b", r"\bpivotal\b", r"\bcrucial\b", r"\bunderscore[sd]?\b", r"\bshowcas(e|ing)\b",
    r"\bvibrant\b", r"\bnavigat(e|ing) the\b", r"\bplays? a (vital|key|crucial) role\b", r"\bin conclusion\b",
    r"\bhonest caveat\b", r"\bgame-?changer\b", r"\bunlock(s|ing)? the\b", r"\bembark\b", r"\brealm\b",
    r"\bnot only\b.*\bbut also\b", r"\bharness(ing)? the power\b", r"\bfoster(ing)?\b", r"\belevate\b",
    # Vague headings and gestures instead of naming the specific risk, category or finding.
    r"\bmore than (just )?a (game|tool|quiz)\b", r"\bthe real question\b", r"\bwhy bother\b",
    r"\ba (live|real|big|key) (ai )?(safety )?question\b", r"\bat face value\b", r"\bthat is the point\b",
    r"\bhere'?s (why|the thing)\b", r"\bthe bigger picture\b", r"\bwhy (it|this) matters\b",
]
US_SPELLING = [r"\bcolor", r"\bbehavior", r"\banalyz", r"\borganiz", r"\bcenter\b", r"\bfavorite",
               r"\brealiz", r"\bprioritiz", r"\bsummariz", r"\bcategoriz", r"\boptimiz"]
# Rule 9: never state or imply a model feels, experiences or is conscious (quoted prompts are allowed).
RULE9 = re.compile(r"\b(the model|a model|models|it) (feels?|experiences|is conscious|are conscious)\b", re.I)
ALLOWED = ("protocol/", "CLAUDE.md", "docs/design/CATALOGUE.md")


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.S | re.I)
    return re.sub(r"`[^`]*`", "", text)


def check_wording() -> None:
    hits = []
    for p in prose_files():
        rel = p.relative_to(ROOT).as_posix()
        for n, line in enumerate(strip_code(read(p)).splitlines(), 1):
            if re.match(r"\s*- \[.*\]\(https?://", line):
                continue  # a cited source title, not our writing
            low = line.lower()
            for pat in AI_TELLS:
                if re.search(pat, low):
                    hits.append(f"{rel}: AI-writing tell '{re.search(pat, low).group(0)}' in: {line.strip()[:90]}")
            if not rel.startswith(ALLOWED):
                for pat in US_SPELLING:
                    m = re.search(pat, low)
                    if m and "color-scheme" not in low and "colour" not in low:
                        hits.append(f"{rel}: US spelling '{m.group(0)}' in: {line.strip()[:90]}")
            if RULE9.search(line) and '"' not in line:
                hits.append(f"{rel}: rule 9 wording in: {line.strip()[:90]}")
        dashes = read(p).count("—")
        if dashes > 12 and rel.endswith(".md"):
            hits.append(f"{rel}: {dashes} em dashes (heavy use is an AI-writing tell)")
    report("Wording (AI tells, Australian spelling, rule 9)", "WARN" if hits else "PASS", hits)


# 5. Currency --------------------------------------------------------------
def check_currency() -> None:
    issues = []
    readme = read(ROOT / "README.md")
    block = re.search(r"## Repo layout\s*```(.*?)```", readme, re.S)
    if block:
        for line in block.group(1).strip().splitlines():
            folder = line.split()[0]
            if not (ROOT / folder).exists():
                issues.append(f"README lists '{folder}' but it does not exist")
    for p in prose_files():
        rel = p.relative_to(ROOT).as_posix()
        if rel == "docs/CHANGELOG.md":
            continue  # history: may name files that were later removed
        for ref in re.findall(r"`((?:docs|protocol|config|src|data|site|tests|scripts)/[^`\s*<>]+)`", read(p)):
            if "<" in ref or "*" in ref:
                continue
            if not (ROOT / ref).exists() and not any(ROOT.glob(ref)):
                issues.append(f"{rel}: refers to `{ref}`, which does not exist")
    tag = git("tag", "--list", "prereg-v1").strip()
    if tag and git("diff", "--stat", "prereg-v1", "--", "protocol/").strip():
        issues.append("protocol/ differs from tag prereg-v1 (forbidden after tagging)")
    report("Currency (README layout, file references, frozen protocol)", "WARN" if issues else "PASS", issues)


# 6. Tests -----------------------------------------------------------------
def check_tests() -> None:
    r = subprocess.run(["uv", "run", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or ["no output"])[-1]
    report("Tests", "PASS" if r.returncode == 0 else "FAIL", [] if r.returncode == 0 else [last])


def main() -> int:
    for check in (check_secrets, check_personal, check_links, check_wording, check_currency, check_tests):
        check()
    width = max(len(n) for n, _, _ in results)
    for name, status, details in results:
        print(f"{status:<5} {name:<{width}}")
        for d in details[:40]:
            print(f"        - {d}")
        if len(details) > 40:
            print(f"        … and {len(details) - 40} more")
    return 1 if any(s == "FAIL" for _, s, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
