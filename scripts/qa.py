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
    return [p for p in text_files() if p.suffix in (".md", ".html")
            or (p.suffix == ".js" and p.relative_to(ROOT).as_posix().startswith("site/"))]


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
        for target in (MD_LINK.findall(strip_code(text)) if p.suffix == ".md" else []):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (p.parent / target).exists() and not (ROOT / target).exists():
                broken.append(f"{p.relative_to(ROOT).as_posix()}: missing file link '{target}'")
        if not NETWORK:
            continue
        for url in URL.findall(text):
            url = url.rstrip(".,;:")
            if url in checked or "fonts.g" in url or url.endswith("/api/v1") or "127.0.0.1" in url or "localhost" in url or url.rstrip("/") == "https://narratedself-api.airiskpractice.org":
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
                    if m and "color-scheme" not in low and "colour" not in low and "behavioral and brain" not in low:
                        hits.append(f"{rel}: US spelling '{m.group(0)}' in: {line.strip()[:90]}")
            if RULE9.search(line) and '"' not in line:
                hits.append(f"{rel}: rule 9 wording in: {line.strip()[:90]}")
        dashes = read(p).count("—")
        if dashes > 12 and rel.endswith(".md"):
            hits.append(f"{rel}: {dashes} em dashes (heavy use is an AI-writing tell)")
    report("Wording (AI tells, Australian spelling, rule 9)", "WARN" if hits else "PASS", hits)


# 4b. Sentence structure ----------------------------------------------------------
# Structural tells from Wikipedia's "Signs of AI writing" and common style guides. Frequency matters more
# than any single use, so each hit is a prompt to reread the sentence, not an automatic failure.
STRUCTURE = [
    ("negative parallelism", re.compile(
        r"\bnot (just|only|merely)\b|\b(isn'?t|is not|aren'?t|wasn'?t)\b[^.?!]{0,60}\b(it'?s|they'?re|but)\b"
        r"|\brather than\b|\binstead of\b[^.?!]{0,40},", re.I)),
    ("copula avoidance", re.compile(r"\b(serves|stands|acts|functions) as\b|\bboasts\b", re.I)),
    ("superficial -ing tail", re.compile(
        r",\s+(highlighting|underscoring|showcasing|reflecting|emphasi[sz]ing|ensuring|demonstrating|illustrating|making it)\b", re.I)),
    ("stock reveal", re.compile(r"\b(trick question|the catch|the twist|here'?s the thing|plot twist|spoiler)\b", re.I)),
    ("parallel fragments", re.compile(r"(?:^|[.!?]\s+)(\w+) (\w+)[.,] \1 (\w+)[.!]", re.I)),
]
def sentences_of(line: str) -> list[str]:
    """Split on sentence ends followed by a space, so URLs and numbers like 4.5:1 don't break sentences."""
    line = re.sub(r"\]\([^)]*\)", "]", line)  # drop Markdown link targets
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]


def visible_text(p: Path) -> str:
    """User-facing text: Markdown without code; HTML without tags, plus the strings inside its scripts."""
    raw = read(p)
    if p.suffix == ".js":
        raw = f"<script>{raw}</script>"  # site script: read only its user-facing strings
    elif p.suffix != ".html":
        return strip_code(raw)
    strings = []
    code = re.compile(r"=>|;|&&|\|\||===|\)\.|\.\.\.|^\s*[).,]|\.map\(|\bconst\b|\breturn\b|\bfunction\b|\$\(|\)\s*\{")
    for block in re.findall(r"<script[^>]*>(.*?)</script>", raw, flags=re.S | re.I):
        block = re.sub(r"\$\{[^}]*\}", "N", block)
        # Double-quoted strings only: template literals mix text and code too much to read reliably.
        found = re.findall(r'"((?:[^"\\\n]|\\.){25,})"', block)
        strings += [s for s in found if " " in s and not code.search(s)]
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "\n", raw, flags=re.S | re.I)
    text = re.sub(r"<(h[1-6]|p|li|div|summary|td|th|pre)[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return text + "\n" + "\n".join(re.sub(r"\$\{[^}]*\}", "N", s) for s in strings)


def protocol_prompts() -> list[str]:
    """Exact prompt wording from the protocol: quoted on the site and in docs, and never reworded."""
    import yaml
    prompts = yaml.safe_load(read(ROOT / "protocol" / "prompts.yaml"))
    texts = []
    for theme in prompts["themes"].values():
        texts += [theme["direct_question"], theme["theme_clause"], theme["self_clause"]]
    return texts


def check_structure() -> None:
    hits = []
    prompts = protocol_prompts()
    for p in prose_files():
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(("docs/design/CATALOGUE.md", "protocol/", "docs/PREREGISTRATION.md")):  # frozen or quoted
            continue
        text = visible_text(p)
        bold_labels = 0
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith(("#", "|", "- [", "* [")) or re.match(r"\s*- \[.*\]\(https?://", line):
                continue
            if re.match(r"^[-*] \*\*[^*]{1,40}[:.]\*\*", s) or re.match(r"^[-*] \*\*[^*]{1,40}\*\*[:.]", s):
                bold_labels += 1
            for name, pat in STRUCTURE:
                m = pat.search(s)
                if m:
                    hits.append(f"{rel}: {name} in: {s[:100]}")
            sentences = sentences_of(s)
            run = 0
            for x in sentences:
                run = run + 1 if len(x.split()) <= 5 else 0
                if run == 3:
                    hits.append(f"{rel}: staccato fragments (3+ very short sentences in a row) in: {s[:100]}")
                    break
            questions = [x for x in sentences if x.endswith("?") and '"' not in x and "“" not in x
                         and not any(x.strip("? ") in q or q in x for q in prompts)]
            if questions and not (len(sentences) == 1 and len(s) < 100):
                hits.append(f"{rel}: rhetorical question in body text: {questions[0][:100]}")
        # Reference registers (threats, credentials, change entries) use bold labels by design; reader-facing
        # pages (README, site, guides) should not.
        registers = ("docs/RESEARCH_REVIEW.md", "docs/OPERATIONS.md", "docs/CHANGELOG.md")
        if bold_labels > 6 and rel not in registers:
            hits.append(f"{rel}: {bold_labels} bold-label bullet lines (\"- **Label:** text\"); vary the structure")
    report("Sentence structure (fragments, contrasts, rhetorical questions)", "WARN" if hits else "PASS", hits)


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
    for check in (check_secrets, check_personal, check_links, check_wording, check_structure, check_currency, check_tests):
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
