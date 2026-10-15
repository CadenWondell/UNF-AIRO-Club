"""T040: the repository data guard blocks participant-like data (temporary files only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_guard import HEADER, MAX_BYTES, check_paths


def _w(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p


def test_planted_persons_csv_rejected(tmp_path: Path) -> None:
    p = _w(tmp_path, "docs/persons.csv", "a,b\n1,2\n")
    assert check_paths([p], tmp_path)


def test_person_id_column_rejected(tmp_path: Path) -> None:
    p = _w(tmp_path, "kits/x/table.csv", "person_id,value\n1,2\n")
    assert check_paths([p], tmp_path)
    p2 = _w(tmp_path, "kits/x/t.tsv", "participant_id\tv\n1\t2\n")
    assert check_paths([p2], tmp_path)


def test_large_data_file_rejected(tmp_path: Path) -> None:
    p = _w(tmp_path, "docs/blob.csv", "x\n" + "1\n" * (MAX_BYTES // 2 + 10))
    assert check_paths([p], tmp_path)


def test_parquet_outside_synthetic_rejected(tmp_path: Path) -> None:
    p = tmp_path / "kits" / "data.parquet"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"PAR1....")
    assert check_paths([p], tmp_path)


def test_synthetic_file_with_header_passes(tmp_path: Path) -> None:
    p = _w(tmp_path, "synthetic/golden/x.csv", f"# {HEADER}\nperson_id,value\nSYN-1,2\n")
    assert check_paths([p], tmp_path) == []


def test_synthetic_file_without_header_rejected(tmp_path: Path) -> None:
    p = _w(tmp_path, "synthetic/golden/x.csv", "person_id,value\n1,2\n")
    assert check_paths([p], tmp_path)


def test_notebook_with_outputs_rejected(tmp_path: Path) -> None:
    nb = {
        "cells": [
            {
                "cell_type": "code",
                "source": "1",
                "outputs": [{"output_type": "stream", "name": "stdout", "text": "x"}],
                "metadata": {},
                "execution_count": 1,
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    p = _w(tmp_path, "kits/x/kit.ipynb", json.dumps(nb))
    assert check_paths([p], tmp_path)


def test_ordinary_source_passes(tmp_path: Path) -> None:
    p = _w(tmp_path, "src/x.py", "person_id = 'not data'\n")
    assert check_paths([p], tmp_path) == []


@pytest.mark.parametrize("name", ["persons.csv", "cohort_export.csv"])
def test_main_exit_code(tmp_path: Path, name: str) -> None:
    from data_guard import main

    p = _w(tmp_path, f"docs/{name}", "a\n1\n")
    assert main([str(p), "--root", str(tmp_path)]) == 1
