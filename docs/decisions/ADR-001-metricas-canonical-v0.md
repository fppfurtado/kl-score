# ADR-001: Métricas canonical de wiki health v0 — subset funcional, 4 métricas / 2 dimensões

**Data:** 2026-06-18
**Status:** Proposto

**Próxima revisão:** 2026-12-18
**Cadência:** semestral
**Critério de erosão auditável:** `logseq-notes ADR-003` estendido com `provenance::` block-level (Onda 4+) OR fix de `gaps_detected` para journals mergeado em main — qualquer das duas dispara recalibração de thresholds. *(Atualização 2026-06-19: gatilho disparou em vetor `quality-score::` page-level — não `provenance::` block-level previsto. Resposta documentada no Adendo Onda 4 ao fim deste ADR; vetor `provenance::` block-level segue válido como recalibração futura quando materializar.)*

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

- `logseq-notes ADR-003` estendido com `provenance::` block-level → reavaliar thresholds de `orphan_nodes` e `enrichment_rate` com novo baseline. *(Atualização 2026-06-19: gatilho disparou em vetor `quality-score::` page-level — ver Adendo Onda 4 abaixo; vetor `provenance::` block-level segue válido como recalibração futura quando materializar.)*
- Fix de `gaps_detected` para journals mergeado em main (BACKLOG) → re-executar baseline e recalibrar threshold de `gaps_detected`.
- ≥ 2 pilotos adicionais com baseline disponível → ajuste empírico de `link_count` threshold (fator 0.8 é heurística de N=1).
- Nova dimensão (confiabilidade semântica ou eficiência cognitiva) entrando em escopo Onda 4+ → nova seção neste ADR ou ADR-002 sucessor.

## Adendo 2026-06-19 — Onda 4: `enrichment_rate` v1 ponderada por `quality-score::`

**Contexto.** [`logseq-notes ADR-003`](https://github.com/fppfurtado/logseq-notes/blob/master/docs/decisions/ADR-003-knowledge-layer-schema-mecanico.md) ganhou Adendo 2026-06-19 (commit [`65399a2`](https://github.com/fppfurtado/logseq-notes/commit/65399a2)) introduzindo property page-level `quality-score::` com 3 valores canonical (`#rascunho` / `#parcial` / `#completo`), curada manualmente pelo operador, aplicada a entity pages (`provenance:: #enriched`, Camada 2a) e concept pages (`provenance:: #concept`, Camada 4). O gatilho de revisão deste ADR previa extensão em `provenance::` block-level; veio em `quality-score::` page-level — vetor diferente do antecipado, mas substância da mesma natureza (signal de progresso/curadoria emitido pelo graph, consumido pelo `kl-score` read-only). § Gatilhos preserva o vetor `provenance::` block-level como recalibração futura quando materializar.

**Decisão.** Refinar `enrichment_rate` para v1 ponderada pelo `quality-score::` da page-pai.

### Fórmula v1

```
enrichment_rate(graph) = sum(weight(page) for each block enriched) / total_blocks
```

onde `weight(page)` consulta a tabela canonical:

| `quality-score::` page-pai | Peso |
|---|---|
| `#completo` | 1.0 |
| `#parcial` | 0.5 |
| `#rascunho` | 0.25 |
| ausente | 1.0 (backward-compat) |
| valor não-canonical | 1.0 (fail-open numérico) + warning único agregado |

Range: `[0.0, 1.0]`.

### Invariantes preservadas

- **Backward-compat numérica**: graph sem nenhum `quality-score::` aplicado produz valor `pytest.approx`-equivalente ao cálculo block-level v0 (peso default 1.0 reduz fórmula a `count(enriched) / total`). Cobertura: `tests/test_metrics.py::test_enrichment_rate_v1_backward_compat_no_quality_score`.
- **Escopo do numerator preserva v0**: filtro `provenance:: #enriched` mantido — pages com `provenance:: #concept` (Camada 4, dentro do escopo do `quality-score::` per Adendo logseq) ficam **fora** desta métrica até a Camada 4 ter baseline próprio. Decisão consistente com `## Decisão` deste ADR (escopo v0 = 2 dimensões funcionais; confiabilidade semântica deferida) e CLAUDE.md ("semantic reliability fora de escopo v0"). Preserva o significado do nome `enrichment_rate`.
- **Fail-open numérico + auditabilidade**: valor não-canonical em `quality-score::` → peso default 1.0 (preserva backward-compat) + warning único ao fim do run via `warnings.warn(UserWarning, ...)` listando pages afetadas. Preserva `## Consequências § Benefícios` deste ADR ("signal-zero honesto preserva auditabilidade") sem quebrar runs em schema sujo.
- **Read-only**: `kl-score` segue lendo o graph sem mutar — `quality-score::` é curada pelo operador via Logseq desktop, nunca por ferramenta automatizada (preserva § Invariantes de implementação 1). Complementa § Invariantes de implementação 4 ("nenhum property `quality-score::` inline no graph") — `kl-score` **lê** `quality-score::` do graph; **não injeta** o property. A invariante original previne injeção pelo `kl-score`; o Adendo apenas adiciona o vetor de leitura.

### Threshold re-calibração — deferida

Threshold de `enrichment_rate` permanece `n/a` (signal-zero por construção do schema page-level Onda 2; o piloto `pages/knowledge-layer.md` ainda não tem `quality-score::` aplicado no momento deste Adendo). Re-calibração aguarda baseline empírico no 2º domínio piloto da Onda 4 (a escolher) + aplicação manual de `quality-score::` em pages enriched — gatilho terceiro de § Gatilhos ("≥ 2 pilotos adicionais com baseline disponível") subsume o caso.

### Status do ADR — preservado

ADR-001 permanece `**Status:** Proposto`. Adendo é extensão (refinamento de uma das 4 métricas canonical) — não revisão maior nem substituição. Critério editorial análogo ao do logseq-notes ADR-003 (Adendo a Sub-decisão 2 preservou status do documento principal).

### Cross-refs absolutos

- Schema graph-side: [`~/Notes/logseq/docs/decisions/ADR-003-knowledge-layer-schema-mecanico.md`](https://github.com/fppfurtado/logseq-notes/blob/master/docs/decisions/ADR-003-knowledge-layer-schema-mecanico.md) § Adendo 2026-06-19, commit [`65399a2`](https://github.com/fppfurtado/logseq-notes/commit/65399a2).
- Implementação: `kl_score/parser.py` (accessor `Page.quality_score`) + `kl_score/metrics.py` (tabela `_QUALITY_WEIGHTS` + refactor de `enrichment_rate`).
- Cobertura: `tests/test_metrics.py::test_enrichment_rate_v1_*` (9 tests cobrindo ponderação, backward-compat, fail-open, warning agregado, escopo do numerator).

## Adendo 2026-06-19 — Onda 4 Faceta 2: re-calibração thresholds pós-baseline empírico

**Contexto.** A Faceta 2 da Onda 4 logseq downstream materializou — 2 pilotos com `quality-score::` aplicado (knowledge-layer `#completo` via [`f55a4ff`](https://github.com/fppfurtado/logseq-notes/commit/f55a4ff); meta-bridge `#parcial` via [`859e935`](https://github.com/fppfurtado/logseq-notes/commit/859e935) em logseq-notes) + fix `gaps_detected` fall-through a `journals_dir/<slug>.md` mergeado em main do kl-score (commit `798d6bd`). § Gatilhos disparou em 3 de 4 vetores:

- (1) `provenance::` block-level — **materializou organicamente via SOP da Faceta 3** ([logseq-notes ADR-003 Adendo segundo `c868b31`](https://github.com/fppfurtado/logseq-notes/commit/c868b31)): meta-bridge.md adota schema bloco-`card` com properties (incluindo `provenance:: #enriched`) como sub-bullets do `- type:: #project`; pattern distinto do schema page-property estritamente top-of-file usado em knowledge-layer (Onda 2). Schema **heterogêneo** emerge cross-pilotos sem decisão coordenada do logseq-notes ADR-003 — efeito colateral da SOP escrita-side.
- (2) Fix `gaps_detected` para journals mergeado em main — **disparado e absorvido** (commit `798d6bd`; resultado numérico equivalente — 47 ≡ 47 — porque graph corrente não tem journal-date links ≥ 2x).
- (3) ≥ 2 pilotos adicionais com baseline disponível — **parcialmente disparado** (N=2 de 3 esperados pelo critério "≥ 2 adicionais ao baseline original").
- (4) Nova dimensão Onda 4+ — **não disparado**.

### Baseline empírico pós-Onda 4 (2026-06-19)

Comando: `kl-score score --graph ~/Notes/logseq --output reports/onda-4-recal-2026-06-19.md` (cross-graph; 185 pages escaneadas, 4678 blocos total).

| Métrica | Baseline Onda 3 | Pós-Onda 4 | Threshold vigente | Decisão |
|---|---|---|---|---|
| `link_count` (top entity) | 13 (kl) | 13 (kl), 7 (mb) | ≥ 10 | **preservado** (N<3) |
| `orphan_nodes` cross-graph | 0 (signal-zero) | 1 (meta-bridge sem `id::`) | n/a | **n/a preservado**; signal-positivo emergente |
| `gaps_detected` cross-graph | 39 | 47 | ≤ 47 | **preservado** (fix journals absorvido) |
| `enrichment_rate` cross-graph | 0.0 | 0.000214 (~1 bloco / 4678) | n/a | **n/a preservado**; signal-positivo emergente |

### Análise por métrica

**`link_count`** — preservado em `≥ 10`. 2 pontos de dado (13, 7) ainda abaixo do critério "≥ 2 pilotos adicionais" do § Gatilhos (lê-se: 2 ADICIONAIS ao baseline original, N=3 total). meta-bridge = 7 abaixo do threshold é honesto — page editorial mais nova, menos cross-linkada que knowledge-layer; sinal de menor densidade, não falha estrutural. Re-calibração formal aguarda 3º piloto.

**`orphan_nodes`** — threshold permanece `n/a` mas **signal-positivo emerge** cross-graph (1 orphan). meta-bridge.md aparece como orphan porque adota schema block-level (per Faceta 1 + SOP Faceta 3) com `provenance:: #enriched` em sub-bullet sem `id::` materializado ainda — comportamento previsto pelo schema (signal HONESTO de page enriched sem `id::` discipline; promoção a `#completo` requer captura inbound via Logseq desktop per logseq-notes ADR-003 Adendo segundo). Threshold formal continua aguardando: (a) N≥3 pilotos block-level com baselines estabilizados; (b) discriminação entre orphan-by-design (page nova) vs orphan-by-erosion (page órfã estrutural).

**`gaps_detected`** — preservado em `≤ 47`. Fix de fall-through a `journals_dir/<slug>.md` (Gatilho 2 disparou) não alterou numericamente o baseline — graph corrente não tem journal-date links ≥ 2x mention. Buffer cross-repo de 20% absorve as ADRs do meta-system. Re-baseline numericamente equivalente.

**`enrichment_rate`** — threshold permanece `n/a` mas **signal-positivo emerge** (0.000214 ≈ 1 bloco enriched / 4678 total). Schema heterogêneo entre pilotos explica o número:

- knowledge-layer.md mantém schema page-property top-of-file (Onda 2; `provenance:: #enriched` linha 1 do arquivo não conta como bloco no parser);
- meta-bridge.md adota schema block-property (SOP Faceta 3; `provenance:: #enriched` em sub-bullet do `- type:: #project` conta como 1 bloco enriched).

Apenas 1 bloco enriched cross-graph apesar de 2 pages com property — denominador (4678 blocos) ainda domina largamente; signal não-trivial requer extensão sistemática do schema block-level (Gatilho 1 vetor original ainda válido para retroatividade em knowledge-layer + novos pilotos).

### Cross-refs absolutos

- Baseline cross-graph pós-Onda 4: [`reports/onda-4-recal-2026-06-19.md`](../../reports/onda-4-recal-2026-06-19.md).
- 1º piloto Onda 4: `~/Notes/logseq/pages/knowledge-layer.md` `quality-score:: #completo` (logseq-notes commit `f55a4ff`).
- 2º piloto Onda 4: `~/Notes/logseq/pages/meta-bridge.md` `quality-score:: #parcial` (logseq-notes commit `859e935`).
- SOP Faceta 3: [logseq-notes ADR-003 Adendo segundo](https://github.com/fppfurtado/logseq-notes/commit/c868b31).
- Fix `gaps_detected` journals fall-through: commit `798d6bd` (kl-score main).

### Status do ADR — preservado

ADR-001 permanece `**Status:** Proposto`. Adendo segundo é re-calibração (4 thresholds revisados; 0 alterados; observação de signal emergente registrada) — não revisão maior nem substituição. Critério editorial análogo ao do Adendo primeiro 2026-06-19.

## Adendo 2026-06-24 — Onda 4+: modo `--format json` (contrato de saída programática)

**Contexto.** § Alternativas consideradas deste ADR descartou "Output JSON estável para pipeline programático" por YAGNI ("nenhum pipeline de consumo programático existe na Onda 3. Deferido Onda 4+"). A condição YAGNI caiu: a skill `/wiki-lint` da knowledge layer (meta-bridge [#19](https://github.com/fppfurtado/meta-bridge/issues/19), Onda 6 / Camada 4) materializou como consumidor real — precisa consumir programaticamente as listas de `orphan_nodes` e `gaps_detected` para dobrá-las no seu health report sem re-implementar a topologia (anti-duplicação per roadmap meta-system). Decomposição cross-repo **kl-score-first** (triage 2026-06-24): kl-score expõe o contrato; `/wiki-lint` referencia o schema real depois. Issue kl-score [#7](https://github.com/fppfurtado/kl-score/issues/7).

**Decisão.** Adicionar `--format json|markdown` (default `markdown`) ao comando `score`. O modo `json` emite um envelope estável serializando as 4 métricas v0 **+ as listas** (não só os agregados). `--output` passa a opcional: modo `json` sem `--output` emite para **stdout** (interface programática natural — `kl-score score --graph X --format json | jq`); modo `markdown` sem `--output` falha loud (report markdown é file-based em `reports/`, per convenção). Comportamento `markdown` preservado integralmente quando `--format` é omitido.

### Contrato do envelope (`schema_version: "1.0"`)

```json
{
  "schema_version": "1.0",
  "graph": "<path absoluto>",
  "filter_namespace": "pages/knowledge-layer | null",
  "pages_scanned": 3,
  "metrics": {
    "link_count":    { "total": 12, "per_page": [{ "page": "pages/x.md", "count": 7 }] },
    "orphan_nodes":  { "count": 3,  "items": [{ "page": "journals/2026_06_19.md", "uuid": null, "excerpt": "..." }] },
    "gaps_detected": { "count": 2,  "items": ["Foo/Bar", "missing-entity"] },
    "enrichment_rate": 0.3077
  }
}
```

**Estabilidade do contrato (lido literalmente pelo `/wiki-lint`):**

- `schema_version` é o ponto de versionamento; breaking change no shape incrementa o campo e dispara revisão do consumer.
- `orphan_nodes.items[]` são objetos estruturados (`page`/`uuid`/`excerpt`), **não** `str(BlockRef)` — `__str__` é formatação humana truncada a 60 chars, instável como contrato. `page` é POSIX relativo ao **graph root** (orphan pode vir de `journals/`, não só `pages/`); `uuid` é `str | null` (orphan sem `id::` serializa `null` explícito — o consumidor deve tolerar `null`, não chave-ausente); `excerpt` é o `body_excerpt` do bloco.
- `gaps_detected.items` são nomes de entidade em forma de **exibição** (`Foo/Bar`), não slug Logseq (`Foo___Bar`) — o slug é detalhe interno do lookup de existência.
- `link_count.per_page` é **integral** (todas as pages do escopo); o truncamento top-20 é exclusivo da renderização markdown (formatação humana).
- Listas determinísticas: envelope byte-idêntico entre runs sobre o mesmo graph.

### Invariantes preservadas

- **Read-only**: nenhum caminho de serialização muta o graph; escrita só em `--output`/stdout (preserva § Invariantes de implementação 1).
- **Subset v0 inalterado**: o JSON serializa o que `metrics.py` já produz; nenhuma métrica/dimensão nova entra (escopo 4-métricas/2-dimensões preservado). A assimetria pré-existente — `orphan_nodes`/`gaps_detected`/`enrichment_rate` operam cross-graph, ignorando `filter_namespace` que só `link_count` respeita — é refletida fielmente no envelope; não é introduzida aqui.

### Status do ADR — preservado

ADR-001 permanece `**Status:** Proposto`. Adendo terceiro ativa uma alternativa antes deferida (extensão do contrato de saída) — não revisão maior nem substituição. Critério editorial análogo aos 2 Adendos prévios.

### Cross-refs absolutos

- Consumidor: [meta-bridge #19](https://github.com/fppfurtado/meta-bridge/issues/19) (`/wiki-lint`, Camada 4). Issue kl-score: [#7](https://github.com/fppfurtado/kl-score/issues/7).
- Implementação: `kl_score/cli.py` (`_compute_metrics` compartilhado, `_build_json_payload`, opção `--format`).
- Cobertura: `tests/test_cli.py::test_score_json_*` (10 tests cobrindo envelope, nullability de `uuid`, valores ancorados, per_page integral, namespace vazio, determinismo, fail-loud).

## Adendo 2026-06-24 — Re-calibração de thresholds pós-adoção block-level (`gaps_detected` 47→85)

**Contexto.** § Gatilhos disparou empiricamente: baseline fresco cross-graph ([`reports/baseline-2026-06-24.md`](../../reports/baseline-2026-06-24.md), 200 pages) divergiu fortemente do baseline do Adendo Faceta 2 (2026-06-19, 185 pages). A adoção block-level de `provenance:: #enriched` no graph se ampliou desde a Faceta 2 — vetor `provenance::` block-level que § Gatilhos preservava como recalibração futura, agora materializado em volume. Origem da detecção: `.claude/local/NOTES.md` entry 2026-06-24 (drift surfado na validação manual do modo `--format json`).

### Baseline empírico (2026-06-24)

Comando: `kl-score score --graph ~/Notes/logseq --output reports/baseline-2026-06-24.md` (cross-graph; 200 pages).

| Métrica | Baseline Faceta 2 (2026-06-19) | Pós-drift (2026-06-24) | Threshold vigente | Decisão |
|---|---|---|---|---|
| `link_count` (top entities) | 13 (kl), 7 (mb) | 24, 15, 15, 13, 11 | ≥ 10 | **preservado ≥ 10**; N≥3 agora disponível confirma o floor |
| `orphan_nodes` cross-graph | 1 | 26 (todos sem `id::`) | n/a | **n/a preservado**; população 100% by-design, sem contraste by-erosion |
| `gaps_detected` cross-graph | 47 | 71 | ≤ 47 | **re-baseline ≤ 85** (71×1.2) + refinamento da métrica deferido (issue #9) |
| `enrichment_rate` cross-graph | 0.000214 | 0.004495 | n/a | **n/a preservado**; denominador (~4700 blocos) ainda domina |

### Análise por métrica

**`link_count`** — preservado em ≥ 10. Pós-drift há ≥5 entity pages acima do floor (24/15/15/13/11), satisfazendo o critério "≥ 2 pilotos adicionais" do § Gatilhos (N≥3 total). O floor ≥ 10 (originalmente knowledge-layer 13 × 0.8, heurística N=1) agora tem suporte empírico multi-page — pages bem-linkadas clearam confortavelmente; pages abaixo de 10 são honestamente sub-linkadas. Fator 0.8 mantido; confiança elevada de heurística N=1 para floor empiricamente suportado.

**`orphan_nodes`** — threshold permanece `n/a`. Os 26 orphans cross-graph são **todos** `sem id::` (by-design: blocos enriquecidos sem disciplina de `id::` materializada — signal honesto de page enriched sem inbound-ref, per Adendo Faceta 2). Zero orphans com `id::` órfãos (que seriam o caso by-erosion). A discriminação by-design vs by-erosion que § Gatilhos exige pra ativar o threshold **não tem contraste nos dados** (população 100% by-design). Threshold formal continua aguardando: (a) materialização de `id::` discipline em pages enriched (produz baseline by-design estável); (b) emergência de ≥1 caso by-erosion (page com `id::` que perde refs inbound) pra calibrar o limite discriminante.

**`gaps_detected`** — **re-baseline de ≤ 47 para ≤ 85** (71 × 1.2, mesma fórmula baseline × 1.2 + buffer cross-repo da Decisão original). A composição dos 71 mudou qualitativamente vs o baseline original (39, "majoritariamente ADRs do meta-system"): o ruído ADR-cross-repo **caiu** para 21; os ~50 restantes são mistura de refs numéricas (`#8`, `#19`, `#139`), entidades de outros repos (`Processo Judicial.../Request TJPA-13`), e **conceitos reais da knowledge layer sem entity page** (`CoT`, `Few-Shot`, `Logseq`, `Mandamus`, `Pessoa`, `Agentic Programming`...). O salto 47→71 vem majoritariamente de menções a conceitos reais — gaps legítimos de curadoria, não mais ruído.

Decisão híbrida (per /triage 2026-06-24): re-baseline o threshold para ≤ 85 **agora** (preserva a metodologia documentada; não bloqueia runs) E **refinar a métrica** depois (issue [#9](https://github.com/fppfurtado/kl-score/issues/9)) — filtrar ruído estrutural (`#NN` refs, ADRs cross-repo, entidades de outros repos) de `gaps_detected` pra que o threshold meça débito de curadoria real, re-apertando quando a métrica estiver limpa. Reconhece a tensão Goodhart explicitamente: re-baseline puro absorveria gaps reais no ruído; o refinamento diferido é o caminho pra restaurar poder discriminante.

**`enrichment_rate`** — threshold permanece `n/a`. 0.004495 (~21 blocos enriched / ~4700 total) é signal-positivo crescente (~21× vs Faceta 2) mas ainda dominado pelo denominador. Threshold com poder discriminante requer extensão sistemática do schema block-level (Gatilho 1 ainda válido pra retroatividade + novos pilotos).

### Cross-refs absolutos

- Baseline cross-graph pós-drift: [`reports/baseline-2026-06-24.md`](../../reports/baseline-2026-06-24.md).
- Origem do drift (captura sessional): `.claude/local/NOTES.md` entry 2026-06-24.
- Refinamento `gaps_detected` (filtro de ruído + re-aperto): issue [#9](https://github.com/fppfurtado/kl-score/issues/9).

### Status do ADR — preservado

ADR-001 permanece `**Status:** Proposto`. Adendo é re-calibração (1 threshold revisado: `gaps_detected` 47→85; 3 preservados; emergência de signal block-level documentada) — não revisão maior nem substituição. Critério editorial análogo aos Adendos prévios.
