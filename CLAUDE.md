# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e ".[dev]"     # editable install + dev deps (Click, pytest)
pytest tests/               # full test suite
pytest tests/test_foo.py::test_bar -v   # single test
kl-score score --graph ~/Notes/logseq --output reports/<date>.md   # main CLI
```

Python ≥3.11. `uv.lock` is gitignored — `pip` (editable) is the canonical workflow per README; `uv` is fine locally but don't commit the lock.

## Architecture

CLI standalone (`kl-score`) that consumes a **Logseq markdown graph** read-only and emits a **wiki-health report** as standalone markdown. Operational layer of a multi-repo knowledge layer roadmap — substantive decisions live upstream, not here.

**Hard invariant: the graph is read-only.** `kl-score` parses `pages/*.md` + `journals/*.md` and writes only to its own `reports/` directory. Never inject `quality-score::` properties or otherwise mutate the source graph (writes still deferred; reads via `Page.quality_score` consumed by `metrics.enrichment_rate` since Onda 4 — see ADR-001 Adendo 2026-06-19).

**v0 scope (4 metrics, 2 dimensions):**
- `link_count`, `orphan_nodes`, `gaps_detected` (topology)
- `enrichment_rate` (progress rate — blocks tagged `provenance:: #enriched`)

Semantic reliability + pipeline efficiency metrics are explicitly out-of-scope for v0 per ADR-001 trade-off.

**Layout (Onda 3 + Onda 4 shipped):**
- `kl_score/cli.py` — Click group + `score` subcommand
- `kl_score/parser.py` — Logseq graph parser (pages + journals; `Page.quality_score`)
- `kl_score/metrics.py` — the 4 v0 metrics; `enrichment_rate` v1 pondera por `quality-score::` per ADR-001 Adendo 2026-06-19
- `tests/` — pytest, synthetic graph fixtures + per-metric tests + e2e
- `reports/` — emitted reports (Onda 2 baseline + Onda 4 smokes)
- `docs/decisions/ADR-001-*.md` — canonical thresholds (v0 + Onda 4 Adendo)

## Cross-repo context

This repo is one node in a 3-repo cluster. Files referenced here matter for design decisions:

- `~/Projects/meta-system` — doctrine. ADR-013 (central hypothesis), ADR-016 (CLI-standalone packaging), ADR-003 Adendo 2026-06-18 (cluster `cognitive`). The driving plan is `docs/plans/onda-3-knowledge-layer-scoring.md`.
- `~/Projects/meta-portability` — precedent CLI-standalone scaffold; kl-score is isomorphic to it (Click, packaging, naming). Mirror its conventions when in doubt.
- `~/Notes/logseq` — the actual graph this tool reads. Its ADR-003 defines the `provenance::` schema (4 values) that the parser consumes.

When a design question can't be answered locally, the answer almost certainly lives in `meta-system/docs/decisions/` or `meta-system/docs/plans/onda-3-*`.

## Conventions

- Commit messages, ADRs, plans, and code comments are in **Portuguese (Brazilian)**, matching the upstream `meta-system` style. Match the existing tone — don't switch to English.
- CHANGELOG follows Keep-a-Changelog `## [<version>] - <date>` exactly; the format activates a `/meta-status changelog-delta` probe upstream, so don't reformat headings.
- Fail loud: when a feature isn't implemented yet (e.g. `score` subcommand pre-Bloco-2), raise with an orienting message rather than silently no-op. Pattern is intentional.

## Pragmatic Toolkit

<!-- pragmatic-toolkit:config -->
```yaml
paths:
  backlog: forge
  plans_dir: local
test_command: "uv run pytest -q --no-header"
```
