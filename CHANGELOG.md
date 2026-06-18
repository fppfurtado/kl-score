# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Formato canonical `## [<version>] - <date>` (Keep-a-Changelog) — ativa o probe
`/meta-status changelog-delta` per `meta-system` skill local (state em
`~/Projects/meta-system/.claude/local/meta-status-state.json`).

## [Unreleased]

### Added

- Bloco 2 do plano `meta-system/docs/plans/onda-3-knowledge-layer-scoring.md`
  implementa 4 métricas v0 (link_count + orphan_nodes + gaps_detected +
  enrichment_rate) em `kl_score/metrics.py` + parser do graph em
  `kl_score/parser.py`.
- Bloco 3 implementa tests pytest (fixtures de graph sintético + tests per
  métrica + integration test end-to-end).
- Bloco 4 emite baseline snapshot contra piloto Onda 2 do meta-system em
  `reports/baseline-<date>.md`.
- Bloco 5 cristaliza thresholds informados pelo baseline em
  `docs/decisions/ADR-001-metricas-canonical-v0.md`.

## [0.1.0] - 2026-06-18

### Added

- **Bootstrap repo standalone** per Bloco 1 do plano [meta-system Onda 3 do
  roadmap knowledge layer block-first](https://github.com/fppfurtado/meta-system/blob/main/docs/plans/onda-3-knowledge-layer-scoring.md)
  (commit `a4aeb13`). Cluster `cognitive` via Adendo 2026-06-18 a `meta-system`
  ADR-003 (extensão paralela direta ao precedente ADR-015 cluster meta +
  meta-portability).
- Estrutura mínima: `pyproject.toml` (setuptools + Click + Python ≥3.11 +
  entry-point `kl-score = kl_score.cli:main`), `kl_score/__init__.py`,
  `kl_score/cli.py` (skeleton Click com sub-comando `score` declarado;
  implementação no Bloco 2), `README.md` (propósito + métricas v0 + cross-refs),
  `LICENSE` (MIT — convention dos repos owned), `.gitignore` Python standard,
  `tests/__init__.py` placeholder Bloco 3, `docs/decisions/.gitkeep` placeholder
  Bloco 5, `reports/.gitkeep` placeholder Bloco 4.
- Pattern naming + scaffold isomorfo a `meta-portability` (precedente
  operacional CLI standalone Click pós-`meta-system` ADR-018).

### Notes

- Sub-comando `kl-score score` exit-1 com mensagem orientadora até Bloco 2
  implementar métricas; pattern fail-loud preserva detecção de invocação
  prematura.
