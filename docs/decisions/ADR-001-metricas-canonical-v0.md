# ADR-001: Métricas canonical de wiki health v0 — subset funcional, 4 métricas / 2 dimensões

**Data:** 2026-06-18
**Status:** Proposto

**Próxima revisão:** 2026-12-18
**Cadência:** semestral
**Critério de erosão auditável:** `logseq-notes ADR-003` estendido com `provenance::` block-level (Onda 4+) OR fix de `gaps_detected` para journals mergeado em main — qualquer das duas dispara recalibração de thresholds.

## Origem

- **Plano upstream:** [`onda-3-knowledge-layer-scoring.md`](/storage/dev/projects/meta-system/docs/plans/onda-3-knowledge-layer-scoring.md) § Decisões §5 e §6 — "thresholds = baseline-first + ajuste empírico"; "ADR mecânico interno do kl-score registra métricas canonical + thresholds + invariantes"
- **Baseline empírico:** [`reports/baseline-2026-06-18.md`](../../reports/baseline-2026-06-18.md) — piloto Onda 2 (`pages/knowledge-layer.md`) como único ponto de dado v0
- **Schema de input:** [`logseq-notes ADR-003`](https://github.com/fppfurtado/logseq-notes/blob/master/docs/decisions/ADR-003-knowledge-layer-schema-mecanico.md) — define `provenance:: #enriched` (4 valores) consumido pelo parser read-only
- **Cluster cognitive:** [`meta-system ADR-003 Adendo 2026-06-18`](/storage/dev/projects/meta-system/docs/decisions/ADR-003-cluster-taxonomy.md) — estende critério do cluster `cognitive` para admitir ferramenta consumidora da Camada 4 (`kl-score` como sibling de `logseq-notes`)

## Contexto

O `kl-score` Onda 3 implementou 4 métricas v0 em 2 dimensões (topologia + taxa de progresso) nos Blocos 2–4 do plano upstream. O baseline do piloto Onda 2 (`pages/knowledge-layer.md`) revelou dois achados estruturais:

1. **Signal-zero honesto em 2 métricas**: `orphan_nodes = 0` e `enrichment_rate = 0%` cross-graph — não são métricas quebradas; o piloto Onda 2 marca `provenance:: #enriched` apenas como *page property* (linha 1 da page), não como *block property*. As métricas operam block-level; sem block-level markers no graph, o signal é zero por construção.

2. **Cross-repo false positives em `gaps_detected`**: 39 entidades reportadas como gaps são majoritariamente ADRs do `meta-system` (`[[ADR-001]]` a `[[ADR-064]]`) que vivem fora do graph Logseq. Ruído cross-repo esperado e documentado.

Este ADR codifica as 4 métricas como canonical v0, com thresholds informados pelo baseline e invariantes de implementação — base para Onda 4+ refinar ou estender.

## Decisão

### Métricas canonical v0

| Métrica | Sinal capturado | Dimensão |
|---|---|---|
| `link_count(page_path)` | Densidade de cross-links numa entity page | Topologia |
| `orphan_nodes(graph_root)` | Blocos `provenance:: #enriched` sem referência inbound (`[[ref]]` ou `((ref))`) de qualquer outra page/bloco no graph (cross-graph) | Topologia |
| `gaps_detected(graph_root, min_mention_count=2)` | Entidades `[[...]]` ≥ 2× sem entity page correspondente | Topologia |
| `enrichment_rate(graph_root)` | Fração de blocos com `provenance:: #enriched` / total | Taxa de progresso |

### Thresholds informados pelo baseline (piloto Onda 2, 1 ponto de dado)

- **`link_count` ≥ 10** — baseline = 13 para `pages/knowledge-layer.md`; threshold = baseline × 0.8 ≈ 10. Fator 0.8: margem conservadora para N=1 ponto de dado; ajuste empírico após ≥ 2 pilotos adicionais per plano upstream §5.
- **`orphan_nodes` n/a** — signal-zero por construção do schema page-level atual (baseline = 0; fórmula baseline × 1.2 = 0). Threshold entra em vigor quando schema block-level adotado (Onda 4+).
- **`gaps_detected` ≤ 47** — baseline = 39 (cross-graph, inclui cross-repo false positives); threshold = baseline × 1.2. **Divergência intencional do plano upstream** (que prescreve `≤ baseline_value` sem drift): buffer de 20% adotado porque o baseline contém ruído cross-repo documentado (ADRs do `meta-system` referenciados no graph sem entity page). Sem buffer, qualquer gap novo dispara revisão mesmo que seja apenas mais ruído cross-repo.
- **`enrichment_rate` n/a** — signal-zero por construção do schema page-level atual (baseline = 0%; fórmula baseline × 0.95 = 0%). Threshold `≥ 0%` entra em vigor quando schema block-level adotado (Onda 4+); até lá, trivialmente satisfeito e sem poder discriminante.

### Invariantes de implementação

- **Graph read-only**: `kl-score` nunca muta `pages/*.md`, `journals/*.md` nem nenhum outro arquivo do graph Logseq. Toda escrita é em `reports/` local.
- **Slug Logseq**: `/` → `___`, `:` → `%3A` (confirmado empiricamente no Bloco 2 cenário C — bug detectado só em uso real, não nos smoke tests).
- **Escopo default**: `pages/**/*.md` excluindo `sources/*` (per logseq-notes ADR-003 SD4 queries default).
- **Output**: report markdown standalone em `reports/`; nenhum property `quality-score::` inline no graph (deferido Onda 4+ if-pain).

## Consequências

### Benefícios

- Thresholds baseline-first evitam arbitrariedade — ancoragem em dado real, não intuição.
- Signal-zero honesto preserva auditabilidade: `orphan_nodes = 0` e `enrichment_rate = 0%` são diagnóstico do schema, não falha da ferramenta.
- Invariante read-only codificada como primeira-classe: qualquer PR que mute o graph falha no critério deste ADR.

### Trade-offs

- **Subset 4-métricas / 2-dimensões**: confiabilidade semântica e eficiência cognitiva explicitamente fora de escopo v0 (deferidas Onda 4+). Validação empírica da hipótese central de [ADR-013](https://github.com/fppfurtado/meta-system/blob/main/docs/decisions/ADR-013-adocao-knowledge-layer-destino-arquitetural-constelacao.md) § Limitações permanece **parcial** após Onda 3.
- **1 ponto de dado de baseline**: thresholds são heurísticos com fator conservador (0.8/1.2). Ajuste empírico depende de ≥ 2 pilotos adicionais.
- **Cross-repo false positives em `gaps_detected`**: ADRs do `meta-system` referenciados no graph sem entity page no Logseq inflam o contador. Ruído documentado; estratégia de filtragem cross-repo deferida Onda 4+.
- **Manutenção do cluster**: `kl-score` é 1 repo a manter no cluster `cognitive` (pós-Adendo a ADR-003 do meta-system); custo de manutenção proporcional à frequência de runs (v0: manual, sem automação).

### Limitações

- Schema block-level ausente no piloto Onda 2 torna 2 das 4 métricas inoperantes como indicadores reais. Caminhos Onda 4+:
  - (a) Estender logseq-notes ADR-003 com `provenance::` block-level nos blocos enriched.
  - (b) Propagar page-level provenance para blocos quando block-level ausente (descartado no Bloco 2 por ambiguidade semântica — decisão absorvida F3 design-reviewer).
  - (c) Manter signal-zero como diagnóstico explícito do schema atual.

## Alternativas consideradas

### Thresholds fixos arbitrários (ex.: `link_count ≥ 5`)

Descartado: sem base empírica para o graph real; risco de Goodhart (otimizar o indicador em vez do sinal subjacente). Baseline-first elimina arbitrariedade inicial.

### Cascatear thresholds em logseq-notes ADR-003

Descartado pelo plano upstream §6: "cascateamento incorreto; scoring tool tem ADR próprio". `logseq-notes ADR-003` define schema de input; este ADR define como o scoring tool o consome e o que mede.

### Incluir métricas de confiabilidade semântica v0

Descartado: pipeline de validação semântica (citation audit, claim coverage) exige substância editorial não disponível no piloto Onda 2. Deferido Onda 4+ per ADR-013 § Limitações.

### Output JSON estável para pipeline programático

Descartado: nenhum pipeline de consumo programático existe na Onda 3. Deferido Onda 4+ per YAGNI; v0 usa markdown standalone via `reports/`.

## Gatilhos de revisão

- `logseq-notes ADR-003` estendido com `provenance::` block-level → reavaliar thresholds de `orphan_nodes` e `enrichment_rate` com novo baseline.
- Fix de `gaps_detected` para journals mergeado em main (BACKLOG) → re-executar baseline e recalibrar threshold de `gaps_detected`.
- ≥ 2 pilotos adicionais com baseline disponível → ajuste empírico de `link_count` threshold (fator 0.8 é heurística de N=1).
- Nova dimensão (confiabilidade semântica ou eficiência cognitiva) entrando em escopo Onda 4+ → nova seção neste ADR ou ADR-002 sucessor.
