"""T118: the generated toy notebook runs end to end in synthetic mode with no edits."""

from __future__ import annotations

import copy
import json
import time
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient

TOY = Path(__file__).resolve().parents[1] / "fixtures" / "kits" / "toy_binary"
PARAMS = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "synthetic"
    / "generator_params"
    / "toy_binary.yaml"
)

INSTRUMENT = """
import numpy as np, yaml
_g = np.asarray(data.train.groups)
_folds = list(search.cv.split(data.train.X, data.train.y, groups=data.train.groups))
assert len(_folds) == search.n_splits_ == 5
for _tr, _va in _folds:
    assert not set(_g[_tr]) & set(_g[_va]), "a patient group appears in both train and validation"
assert len(data.run_log) == 1, "final_evaluation must run exactly once"
_m = data.run_manifest
_p = yaml.safe_load(open(PARAMS_PATH))
assert _m.synthetic_population["path"].endswith("toy_binary.yaml")
assert _m.synthetic_population["seed"] == _p["seed"]
assert _m.synthetic_population["n_persons"] == _p["n_persons"] == len(kit.adapter.persons())
assert "golden" not in kit.adapter.source_label
print("INSTRUMENTATION-OK")
"""


@pytest.mark.notebook
def test_toy_notebook_executes_without_edits() -> None:
    nb = nbformat.read(TOY / "kit.ipynb", as_version=4)
    original = copy.deepcopy(nb)
    nb.cells.append(
        nbformat.v4.new_code_cell(f"PARAMS_PATH = {json.dumps(str(PARAMS))}\n" + INSTRUMENT)
    )
    start = time.monotonic()
    NotebookClient(
        nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(TOY)}}
    ).execute()
    elapsed = time.monotonic() - start
    assert elapsed < 300, elapsed
    out = "".join(o.get("text", "") for o in nb.cells[-1].outputs)
    assert "INSTRUMENTATION-OK" in out
    # the committed notebook itself was not modified by the test
    assert nbformat.read(TOY / "kit.ipynb", as_version=4) == original
