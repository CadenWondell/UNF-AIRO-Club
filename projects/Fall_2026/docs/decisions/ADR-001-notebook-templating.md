# ADR-001: Notebook cell templating with stdlib `string.Template`

- **Status**: accepted
- **Date**: 2026-10-15
- **Deciders**: framework maintainers
- **Context**: plan.md § 10, research R-16, tasks T042–T046

## Context

Kit notebooks are generated from one skeleton per template family. Cell templates contain real
Python (and Markdown) with kit values rendered literally (feature lists, `LogisticRegression(...)`
parameters, threshold rule, metrics). Python code is full of braces, quotes, and `%`, so the
templating syntax must not collide with Python syntax, and generation must be byte-deterministic.

## Decision

Use the standard library's `string.Template` (`$name` / `${name}` placeholders, `$$` escape):

- strict substitution only: a missing variable raises (never `safe_substitute`);
- placeholders on an indented line indent every line of a multiline value to the same column;
- rendering is a pure function of the template and values (byte-identical across runs);
- every rendered code cell must parse with `ast.parse`.

Values are rendered by the builder as Python literals (`repr`-style, strings double-quoted).

## Consequences

- No templating dependency (Jinja2 etc.); `$` is the only special character, which Python code
  rarely uses.
- No loops or conditionals in templates: the builder computes lists/blocks in Python and passes
  rendered strings. This keeps templates readable as plain notebooks.
- **Adopting a templating dependency requires a new ADR superseding this one and a plan.md update
  first.**
