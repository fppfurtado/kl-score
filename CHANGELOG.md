# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Formato canonical `## [<version>] - <date>` (Keep-a-Changelog) — ativa o probe
`/meta-status changelog-delta` per `meta-system` skill local (state em
`~/Projects/meta-system/.claude/local/meta-status-state.json`).

## [Unreleased]

### Added

- Modo `--format json|markdown` (default `markdown`) no comando `score`:
  emite envelope JSON estável (`schema_version 1.0`) com as 4 métricas v0 +
  as listas estruturadas (`orphan_nodes` como objeto `page`/`uuid`/`excerpt`,
  `gaps_detected`, `per_page` integral). `--output` passa a opcional — modo
  `json` sem `--output` emite para stdout (`| jq`); `markdown` sem `--output`
  falha loud. Contrato cross-repo consumido pelo `/wiki-lint`
  (meta-bridge #19); ver `docs/decisions/ADR-001` § Adendo 2026-06-24.
- Filtro de ruído estrutural em `gaps_detected` (#9): entidades casando
  `^ADR-\d+$` (ADRs cross-repo) ou `^#\d+$` (refs numéricas) são filtradas por
  default; flag `--exclude-gap-pattern <regex>` (repetível, substring) estende
  o filtro para namespaces externos. Envelope JSON sobe para
  `schema_version 1.1` com campo aditivo `gaps_detected.filters_applied`.

### Notes

- ADR-001 Adendo terceiro (2026-06-24): re-calibração de thresholds pós-drift
  block-level. `gaps_detected` re-baseline `≤ 47` → `≤ 85`; `link_count`
  preservado `≥ 10` (N≥3 confirma o floor); `orphan_nodes`/`enrichment_rate`
  mantidos `n/a` (signal block-level emergente, sem contraste discriminante).
  Refinamento de ruído de `gaps_detected` rastreado em #9. Baseline em
  `reports/baseline-2026-06-24.md`.
- ADR-001 Adendo quarto (2026-06-24): re-aperto `gaps_detected` `≤ 85` → `≤ 44`
  (baseline filtrado, **sem buffer** — o ×1.2 absorvia ruído agora filtrado;
  manter reabsorveria débito de curadoria real). Quebra de série: baselines
  39/47/71 são pré-filtro, não comparáveis com pós-filtro. Baseline em
  `reports/baseline-gaps-filtrado-2026-06-24.md`.

## [0.2.0] - 2026-06-23

### Added

- Bloco 2 do plano `meta-system/docs/plans/onda-3-knowledge-layer-scoring.md`
  implementa 4 métricas v0 (link_count + orphan_nodes + gaps_detected +
  enrichment_rate) em `kl_score/metrics.py` + parser do graph em
  `kl_score/parser.py`.
- Bloco 3 implementa tests pytest (fixtures de graph sintético + tests per
  métrica + integration test end-to-end).
- Bloco 4 emite baseline snapshot contra piloto Onda 2 do meta-system em
  `reports/baseline-2026-06-18.md`.
- Bloco 5 cristaliza thresholds informados pelo baseline em
  `docs/decisions/ADR-001-metricas-canonical-v0.md`.
- Onda 4: parser estendido com `Page.quality_score` (property `quality-score::`) e
  `enrichment_rate` v1 ponderada por grau de completude (`#rascunho` / `#parcial` /
  `#completo`) per ADR-001 Adendo 2026-06-19.

### Fixed

- `gaps_detected` fall-through para `journals_dir/<slug>.md`; restrito a
  `pages/*.md` por default.
- Slug Logseq triple-lowbar (`___`) corrigido em `gaps_detected`.

### Notes

- ADR-001 Adendo segundo (Faceta 2 Onda 4): recalibração de thresholds
  `enrichment_rate` com buffer para ruído estrutural documentado.
- Reports smoke Onda 4 adicionados como evidência de validação.
- `paths.backlog` declarado como `forge` no bloco config do toolkit.

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
