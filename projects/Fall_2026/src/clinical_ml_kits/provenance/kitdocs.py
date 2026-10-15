"""KitDocs completeness: the 12 FR-156 reviewer questions in each kit README."""

from __future__ import annotations

import re
from pathlib import Path

FR156_QUESTIONS: tuple[str, ...] = (
    "What is the clinical question?",
    "What official documentation was used?",
    "How was the cohort created?",
    "How were positive labels (cases) created?",
    "How were controls created?",
    "What is the index (as-of) time?",
    "Which features are included?",
    "Which features are deliberately excluded, and why?",
    "How do raw fields map to framework features?",
    "Which decisions come directly from documentation?",
    "Which decisions are project-specific methodological choices?",
    "Which items remain unverified?",
)
_LINK = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")


def _slug(heading: str) -> str:
    """GitHub-style heading anchor."""
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def _anchors(md: Path) -> set[str]:
    return {_slug(m.group(1)) for m in re.finditer(r"^#+\s+(.*)$", md.read_text(), re.M)}


def _sections(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    parts = re.split(r"^##\s+(.*)$", text, flags=re.M)
    for i in range(1, len(parts), 2):
        out[parts[i].strip()] = parts[i + 1].strip()
    return out


def link_resolves(docs_dir: Path, target: str) -> bool:
    if re.match(r"^[a-z]+://", target):
        return False  # answers must link to repository files or anchors
    file_part, _, anchor = target.partition("#")
    path = (docs_dir / file_part).resolve() if file_part else docs_dir / "README.md"
    if not path.exists():
        return False
    if anchor:
        return path.is_file() and path.suffix == ".md" and anchor in _anchors(path)
    return True


def readme_issues(docs_dir: Path) -> list[str]:
    """Problems with the README's FR-156 answers (empty list when complete)."""
    readme = docs_dir / "README.md"
    if not readme.is_file():
        return ["README.md missing"]
    sections = _sections(readme.read_text())
    issues: list[str] = []
    for q in FR156_QUESTIONS:
        body = sections.get(q)
        if body is None:
            issues.append(f"missing FR-156 question heading {q!r}")
            continue
        links = _LINK.findall(body)
        if not body or not links:
            issues.append(f"{q!r} has no answer with a relative link")
            continue
        broken = [t for t in links if not link_resolves(docs_dir, t)]
        if len(broken) == len(links):
            issues.append(f"{q!r}: no link resolves ({broken})")
    return issues
