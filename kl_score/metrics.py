"""4 métricas v0 funcional.

Dimensões: topologia (link_count, orphan_nodes, gaps_detected) + taxa de
progresso (enrichment_rate). Decisões substantivas em
.claude/local/plans/bloco-2-parser-metrics-cli.md (handle local) e
~/Projects/meta-system/docs/plans/onda-3-knowledge-layer-scoring.md (canonical).
"""

from __future__ import annotations

import warnings
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from kl_score.parser import Page, iter_journals, iter_pages, parse_page

_QUALITY_WEIGHTS: dict[str, float] = {
    "completo": 1.0,
    "parcial": 0.5,
    "rascunho": 0.25,
}


@dataclass(frozen=True)
class BlockRef:
    page_path: Path
    body_excerpt: str
    uuid: str | None

    def __str__(self) -> str:
        name = self.page_path.name
        uuid_part = f"(({self.uuid[:8]}))" if self.uuid else "(sem id::)"
        excerpt = self.body_excerpt[:60].replace("\n", " ")
        return f"{name} {uuid_part} — {excerpt}"


def link_count(page_path: Path) -> int:
    """[[page-link]] + ((block-ref)) count na page. Dimensão topologia."""
    page = parse_page(page_path)
    return sum(len(b.page_links) + len(b.block_refs) for b in page.blocks)


def _iter_all(graph_root: Path):
    yield from iter_pages(graph_root)
    yield from iter_journals(graph_root)


def orphan_nodes(
    graph_root: Path, provenance_filter: str = "enriched"
) -> list[BlockRef]:
    """Blocos `provenance:: #<filter>` sem `((uuid))` apontando ao bloco.

    Granularidade fina exclusiva: [[Page]] inbound NÃO conta — isolamento é
    semântica de bloco, não de page. Bloco enriquecido sem `id::` é sempre
    orphan (não pode ser target de `((uuid))`).
    """
    enriched_blocks = []
    all_block_refs: set[str] = set()

    for page in _iter_all(graph_root):
        for block in page.blocks:
            if block.provenance == provenance_filter:
                enriched_blocks.append(block)
            all_block_refs |= block.block_refs

    return [
        BlockRef(
            page_path=b.page_path,
            body_excerpt=b.body.split("\n")[0][:80],
            uuid=b.uuid,
        )
        for b in enriched_blocks
        if b.uuid is None or b.uuid not in all_block_refs
    ]


def _slug_logseq(entity: str) -> str:
    """Slug Logseq `:file/name-format :triple-lowbar` per evidência empírica.

    Regra observada em ~/Notes/logseq/logseq/config.edn:421 + filenames reais:
    namespace separator `/` → `___`; `:` → `%3A` (URL-encoded). Espaços e
    acentos PRESERVADOS no filename (regra NÃO se aplica a espaços, como o
    nome `triple-lowbar` poderia sugerir).
    """
    return entity.replace("/", "___").replace(":", "%3A")


def gaps_detected(
    graph_root: Path, min_mention_count: int = 2
) -> list[str]:
    """Entidades `[[Entity]]` mencionadas ≥ N vezes sem page correspondente.

    Slug aplicado per regra `:triple-lowbar` observada empiricamente: `/` vira
    `___`, `:` vira `%3A`, espaços/acentos preservados.
    """
    pages_dir = graph_root / "pages"
    mention_counts: Counter[str] = Counter()

    for page in _iter_all(graph_root):
        for block in page.blocks:
            for link in block.page_links:
                mention_counts[link] += 1

    gaps: list[str] = []
    for entity, count in sorted(mention_counts.items()):
        if count < min_mention_count:
            continue
        if not (pages_dir / f"{_slug_logseq(entity)}.md").exists():
            gaps.append(entity)

    return gaps


def enrichment_rate(graph_root: Path) -> float:
    """Blocos `provenance:: #enriched` ponderados por `quality-score::` da page-pai / total. Range [0.0, 1.0].

    Pesos: `#completo`=1.0, `#parcial`=0.5, `#rascunho`=0.25. Page sem
    `quality-score::` ou com valor não-canonical → peso default 1.0 (backward-
    compat numérica com v0: graph sem nenhum `quality-score::` produz valor
    idêntico ao cálculo v0). Valores não-canonical disparam um warning único ao
    fim do run listando pages afetadas — preserva auditabilidade do ADR-001 §
    Benefícios sem quebrar runs em schema sujo.

    Dimensão taxa de progresso. Zero blocos → 0.0.
    """
    total = 0
    weighted_enriched = 0.0
    unknown_quality_pages: list[Path] = []
    for page in _iter_all(graph_root):
        score = page.quality_score
        if score is None:
            weight = 1.0
        elif score in _QUALITY_WEIGHTS:
            weight = _QUALITY_WEIGHTS[score]
        else:
            unknown_quality_pages.append(page.path)
            weight = 1.0
        for block in page.blocks:
            total += 1
            if block.provenance == "enriched":
                weighted_enriched += weight
    if unknown_quality_pages:
        paths_str = ", ".join(str(p) for p in unknown_quality_pages)
        warnings.warn(
            f"quality-score:: com valor não-canonical em "
            f"{len(unknown_quality_pages)} page(s): {paths_str}",
            UserWarning,
            stacklevel=2,
        )
    if total == 0:
        return 0.0
    return weighted_enriched / total
