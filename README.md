# kl-score

CLI standalone para **scoring objetivo de wiki health da knowledge layer** — instrumenta o graph Logseq markdown com métricas auditáveis pra validação empírica da hipótese central do `meta-system` ADR-013 ("curadoria majoritariamente autônoma; supervisão de exceção"). Camada Meta operacional do roadmap multi-onda da knowledge layer; integra-se ao cluster `cognitive` per `meta-system` ADR-003 § Adendo 2026-06-18.

Onda 3 do roadmap [`docs/plans/roadmap-knowledge-layer-logseq-block-first.md`](https://github.com/fppfurtado/meta-system/blob/main/docs/plans/roadmap-knowledge-layer-logseq-block-first.md) materializou o **subset funcional v0 (4 métricas, 2 dimensões)** — substância completa em [`docs/decisions/ADR-001-metricas-canonical-v0.md`](docs/decisions/ADR-001-metricas-canonical-v0.md) (Bloco 5 do plano upstream; pendente até Bloco 4 baseline informar thresholds).

## Métricas v0

Subset funcional cobrindo **topologia** + **taxa de progresso** (confiabilidade semântica + eficiência de pipeline deferidas pra Onda 4+ per Trade-off ADR-001):

| Métrica | Dimensão | Sinal | Threshold (informado pelo baseline) |
|---|---|---|---|
| `link_count` | topologia | cross-link density por entity page | `≥ baseline_value × 0.8` |
| `orphan_nodes` | topologia | isolamento de blocos `provenance:: #enriched` sem refs inbound | `≤ baseline_value × 1.2` |
| `gaps_detected` | topologia | entidades referenciadas ≥N vezes sem entity page correspondente | `≤ baseline_value` |
| `enrichment_rate` | taxa de progresso | blocos com `provenance:: #enriched` / total | `≥ baseline_value × 0.95` |

## Install

```bash
pip install -e ~/Projects/kl-score
```

Editable install local — sem publish PyPI v0 per Trade-off ADR-001 (paralelo a `meta-portability` ADR-018).

## Usage

```bash
# baseline contra piloto Onda 2 do meta-system
kl-score score \
  --graph ~/Notes/logseq \
  --filter-namespace pages/knowledge-layer \
  --output reports/baseline-2026-06-19.md

# scoring cross-graph (sem filtro)
kl-score score --graph ~/Notes/logseq --output reports/full-graph.md
```

Output: report markdown standalone em `reports/<date>.md` com seção `## Métricas v0` + 4 sub-seções por métrica + valores numéricos + listas quando relevante. Graph permanece **read-only** — kl-score nunca muta o graph (property `quality-score::` inline deferida pra Onda 4+ if-pain per `meta-system` plano Onda 3 decisão pré-tomada 4).

## Dev

```bash
pip install -e ".[dev]"
pytest tests/
```

## Cross-refs

- **meta-system doctrine** (`~/Projects/meta-system`):
  - [ADR-013 § Limitações](https://github.com/fppfurtado/meta-system/blob/main/docs/decisions/ADR-013-adocao-knowledge-layer-destino-arquitetural-constelacao.md) — hipótese central + 2 pré-condições (eficiência, confiabilidade)
  - [ADR-016 § Critério](https://github.com/fppfurtado/meta-system/blob/main/docs/decisions/ADR-016-target-aware-packaging-mecanico-substitui-mcp-first.md) — CLI standalone resolvido (4/4 critério)
  - [ADR-003 Adendo 2026-06-18](https://github.com/fppfurtado/meta-system/blob/main/docs/decisions/ADR-003-cluster-taxonomy.md) — cluster `cognitive` estendido pra admitir ferramenta consumidora da Camada 4 (paralelo a ADR-015 cluster meta)
  - [ADR-021](https://github.com/fppfurtado/meta-system/blob/main/docs/decisions/ADR-021-auto-critica-permanente-4o-principio-fundamental.md) — princípio 4 auto-crítica permanente arma gatilhos de revisão do subset v0
  - [roadmap § Onda 3](https://github.com/fppfurtado/meta-system/blob/main/docs/plans/roadmap-knowledge-layer-logseq-block-first.md) — escopo + 6 métricas propostas (4 entram v0)
  - [plano Onda 3](https://github.com/fppfurtado/meta-system/blob/main/docs/plans/onda-3-knowledge-layer-scoring.md) — substância completa cross-repo
- **logseq-notes** (`~/Notes/logseq`):
  - [ADR-003 schema mecânico Onda 2](https://github.com/fppfurtado/logseq-notes/blob/master/docs/decisions/ADR-003-knowledge-layer-schema-mecanico.md) — provenance:: 4 valores (consumido read-only por kl-score parser)

## License

MIT
