"""Repository data guard: blocks participant-like data from entering the repository.

Usage (pre-commit passes staged file names):  python tests/repo/data_guard.py FILE... [--root DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEADER = "provenance: independently authored synthetic; not derived from any participant data"
MAX_BYTES = 512 * 1024
DATA_EXT = {
    ".csv",
    ".tsv",
    ".parquet",
    ".feather",
    ".xlsx",
    ".xls",
    ".pkl",
    ".pickle",
    ".h5",
    ".sas7bdat",
    ".dta",
    ".sav",
    ".avro",
    ".orc",
    ".joblib",
    ".npz",
    ".npy",
}
BINARY_EXT = DATA_EXT - {".csv", ".tsv"}
SUSPICIOUS_NAME = re.compile(r"(person|participant|patient|cohort|omop|cdr|export|mrn)", re.I)
ID_COLUMN = re.compile(r"^(person_id|participant_id|patient_id|research_id|mrn|subject_id)$", re.I)


def _rel(p: Path, root: Path) -> str:
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def _check_one(p: Path, root: Path) -> list[str]:
    rel = _rel(p, root)
    in_synthetic = rel.startswith("synthetic/") or "/synthetic/" in rel
    ext = p.suffix.lower()
    problems: list[str] = []
    if ext == ".ipynb":
        try:
            nb = json.loads(p.read_text())
        except (OSError, ValueError):
            return [f"{rel}: unreadable notebook"]
        if any(c.get("outputs") for c in nb.get("cells", []) if c.get("cell_type") == "code"):
            problems.append(f"{rel}: notebook has outputs (strip them with nbstripout)")
        return problems
    if ext not in DATA_EXT:
        return []
    if in_synthetic:
        if ext in BINARY_EXT:
            return [f"{rel}: binary data files are not allowed, even under synthetic/"]
        first = p.read_text(errors="replace").splitlines()[:1]
        if not first or HEADER not in first[0]:
            problems.append(f"{rel}: synthetic data must start with '# {HEADER}'")
        return problems
    problems.append(f"{rel}: data file outside synthetic/ ({ext})")
    if SUSPICIOUS_NAME.search(p.name):
        problems.append(f"{rel}: participant-like file name")
    if p.stat().st_size > MAX_BYTES:
        problems.append(f"{rel}: data file larger than {MAX_BYTES} bytes")
    if ext in {".csv", ".tsv"}:
        head = p.read_text(errors="replace").splitlines()[:1]
        cols = re.split(r"[,\t;|]", head[0]) if head else []
        if any(ID_COLUMN.match(c.strip().strip('"')) for c in cols):
            problems.append(f"{rel}: person-identifier column")
    return problems


def check_paths(paths: list[Path], root: Path) -> list[str]:
    out: list[str] = []
    for p in paths:
        if p.is_file():
            out += _check_one(p, root)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--all", action="store_true", help="scan every file under --root")
    args = ap.parse_args(argv)
    root = Path(args.root)
    files = [Path(f) for f in args.files]
    if args.all:
        skip = {".git", ".venv", "node_modules", ".specify", ".claude"}
        files = [
            p
            for p in root.rglob("*")
            if p.is_file() and not (set(p.relative_to(root).parts) & skip)
        ]
    problems = check_paths(files, root)
    for prob in problems:
        print(f"data-guard: {prob}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
