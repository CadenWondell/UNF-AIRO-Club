"""``ckit`` command line: validation, catalog, schemas, notebooks, and docs generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from clinical_ml_kits.core.errors import KitValidationError
from clinical_ml_kits.core.kit_schema import (
    LEVELS,
    ValidationContext,
    load_kit_definition,
    validate_kit,
)


def _is_kit_file(p: Path) -> bool:
    try:
        data = yaml.safe_load(p.read_text())
    except (OSError, yaml.YAMLError):
        return False
    return isinstance(data, dict) and "kit_schema" in data


def discover_kits(base: Path) -> list[Path]:
    """Kit definition files under ``base`` (any YAML with a ``kit_schema`` key)."""
    if base.is_file():
        return [base]
    return sorted(p for p in base.rglob("*.yaml") if _is_kit_file(p))


def _validate_one(path: Path, level: str, ctx: ValidationContext, *, provenance: bool) -> bool:
    from clinical_ml_kits.provenance.checks import check_kit, errors

    try:
        kit = load_kit_definition(path)
        report = validate_kit(kit, level, ctx)
    except KitValidationError as e:
        print(f"FAIL {path}: {e}", file=sys.stderr)
        return False
    ok = True
    if provenance:
        findings = check_kit(path, ctx)
        for f in findings:
            print(f"  {f}", file=sys.stderr if f.severity == "error" else sys.stdout)
        ok = not errors(findings)
    status = "PASS" if ok else "FAIL"
    print(
        f"{status} {kit.kit_id} status={kit.definition.status} level={level} "
        f"provisional={len(report.provisional)} unverified={len(report.unverified)}"
    )
    return ok


def cmd_validate(args: argparse.Namespace) -> int:
    ctx = ValidationContext.from_root(args.root)
    targets: list[Path] = []
    if args.all is not None:
        base = Path(args.all) if args.all else ctx.root / "kits"
        targets = discover_kits(base) if base.exists() else []
        if not targets:
            print(f"note: no kit definitions under {base}")
    targets += [Path(p) for p in args.paths]
    if not targets and args.all is None:
        print("nothing to validate: pass kit paths or --all", file=sys.stderr)
        return 2
    ok = all([_validate_one(p, args.level, ctx, provenance=args.all is not None) for p in targets])
    if args.all is not None:
        from clinical_ml_kits.core.catalog import Catalog
        from clinical_ml_kits.provenance.checks import check_definitions, errors

        findings = check_definitions(ctx)
        for f in findings:
            print(f"  {f}", file=sys.stderr if f.severity == "error" else sys.stdout)
        ok = ok and not errors(findings)
        cat = ctx.root / "kits" / "catalog.yaml"
        if cat.is_file():
            try:
                n = len(Catalog.load(cat).entries)
                print(f"PASS catalog entries={n}")
            except Exception as e:  # pydantic ValidationError or YAML error
                print(f"FAIL catalog: {e}", file=sys.stderr)
                ok = False
    return 0 if ok else 1


def cmd_catalog(args: argparse.Namespace) -> int:
    from clinical_ml_kits.core.catalog import Catalog

    ctx = ValidationContext.from_root(args.root)
    cat = Catalog.load(ctx.root / "kits" / "catalog.yaml")
    print(f"{'candidate_id':32} {'status':10} {'ref':4} {'verification':22} name")
    for e in cat.entries:
        ver = e.verification_state or "-"
        print(
            f"{e.candidate_id:32} {e.status:10} {'yes' if e.reference else '':4} {ver:22} {e.name}"
        )
    return 0


def cmd_schemas(args: argparse.Namespace) -> int:
    from clinical_ml_kits.core.schema_export import SCHEMAS, render_schema, write_schemas

    out = Path(args.out)
    if args.check:
        stale = [
            n
            for n in SCHEMAS
            if not (out / f"{n}.schema.json").is_file()
            or (out / f"{n}.schema.json").read_text() != render_schema(n)
        ]
        for n in stale:
            print(f"stale schema: {n}", file=sys.stderr)
        return 1 if stale else 0
    for p in write_schemas(out):
        print(p)
    return 0


def cmd_stamp(args: argparse.Namespace) -> int:
    from clinical_ml_kits.provenance.hashing import stamp_file

    for p in args.paths:
        stamp_file(Path(p))
        print(f"stamped {p}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ckit", description="Clinical ML Kit Framework tools")
    sub = ap.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate kit definitions at a level")
    v.add_argument("paths", nargs="*", help="kit.yaml files or kit directories")
    v.add_argument(
        "--all",
        nargs="?",
        const="",
        default=None,
        metavar="DIR",
        help="validate every kit under DIR (default: <root>/kits) plus provenance",
    )
    v.add_argument("--level", choices=LEVELS, default="schema")
    v.add_argument("--root", default=None, help="project root (definitions/, synthetic/)")
    v.set_defaults(func=cmd_validate)

    c = sub.add_parser("catalog", help="print the kit catalog status table")
    c.add_argument("--root", default=None)
    c.set_defaults(func=cmd_catalog)

    s = sub.add_parser("schemas", help="write or check docs/schemas/*.schema.json")
    s.add_argument("--out", default="docs/schemas")
    s.add_argument("--check", action="store_true")
    s.set_defaults(func=cmd_schemas)

    st = sub.add_parser(
        "stamp", help="stamp content hashes on verified refs (run only after human verification)"
    )
    st.add_argument("paths", nargs="+")
    st.set_defaults(func=cmd_stamp)

    _add_generation_commands(sub)
    return ap


def _kit_files(ctx: ValidationContext, kit_filter: str | None) -> list[Path]:
    """``kit.yaml`` files under ``<root>/kits`` (fixture kits: ``--root tests/fixtures``)."""
    base = ctx.root / "kits"
    files = sorted(base.rglob("kit.yaml")) if base.is_dir() else []
    if kit_filter:
        files = [p for p in files if load_kit_definition(p).kit_id == kit_filter]
    return files


def cmd_docs(args: argparse.Namespace) -> int:
    from clinical_ml_kits.provenance.report import log_path, render_for_kit

    ctx = ValidationContext.from_root(args.root)
    files = _kit_files(ctx, args.kit)
    if args.kit and not files:
        print(f"unknown kit {args.kit!r}", file=sys.stderr)
        return 1
    stale = 0
    for f in files:
        kit = load_kit_definition(f)
        text = render_for_kit(kit, ctx)
        out = log_path(kit)
        if args.check:
            if not out.is_file() or out.read_text() != text:
                print(f"stale verification log: {out}", file=sys.stderr)
                stale += 1
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text)
            print(f"wrote {out}")
    return 1 if stale else 0


def render_kit_notebook_text(kit_file: Path, ctx: ValidationContext) -> str:
    import importlib

    from clinical_ml_kits.notebooks.builder import SKELETONS, build_notebook, notebook_text

    kit = load_kit_definition(kit_file)
    family = kit.definition.template_family
    mod = importlib.import_module(f"clinical_ml_kits.templates.{family}.notebook")
    values = mod.notebook_values(kit, ctx)
    nb = build_notebook(
        SKELETONS / family,
        values,
        kit_id=kit.kit_id,
        title=kit.definition.name,
        extra_meta={"kit_version": kit.definition.kit_version},
    )
    return str(notebook_text(nb))


def cmd_notebooks(args: argparse.Namespace) -> int:
    from clinical_ml_kits.notebooks.builder import build_setup_check, notebook_text

    ctx = ValidationContext.from_root(args.root)
    files = _kit_files(ctx, args.kit)
    if args.kit and not files:
        print(f"unknown kit {args.kit!r}", file=sys.stderr)
        return 1
    outputs: list[tuple[Path, str]] = []
    for f in files:
        kit = load_kit_definition(f)
        if not kit.definition.generate_notebook:
            continue
        validate_kit(kit, "synthetic", ctx)  # notebooks are generated only for runnable kits
        outputs.append((f.parent / "kit.ipynb", render_kit_notebook_text(f, ctx)))
    if not args.kit and (ctx.root / "kits" / "catalog.yaml").is_file():
        outputs.append(
            (ctx.root / "kits" / "00_setup_check.ipynb", notebook_text(build_setup_check()))
        )
    stale = 0
    for path, text in outputs:
        if args.check:
            if not path.is_file() or path.read_text() != text:
                print(f"notebook drift: {path}", file=sys.stderr)
                stale += 1
        else:
            path.write_text(text)
            print(f"wrote {path}")
    return 1 if stale else 0


def _add_generation_commands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    n = sub.add_parser("notebooks", help="generate (or --check) kit notebooks")
    n.add_argument("--kit", default=None)
    n.add_argument("--check", action="store_true")
    n.add_argument("--root", default=None)
    n.set_defaults(func=cmd_notebooks)
    d = sub.add_parser("docs", help="generate (or --check) each kit's verification_log.md")
    d.add_argument("--kit", default=None)
    d.add_argument("--check", action="store_true")
    d.add_argument("--root", default=None)
    d.set_defaults(func=cmd_docs)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
