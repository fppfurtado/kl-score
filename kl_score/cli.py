"""kl-score CLI entry-point.

Bloco 2: wire das 4 métricas v0 + emissão de report markdown standalone.
Graph é read-only em todos os caminhos.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import click

from kl_score import __version__
from kl_score.metrics import (
    enrichment_rate,
    gaps_detected,
    orphan_nodes,
)
from kl_score.parser import iter_pages


@click.group()
@click.version_option(__version__, prog_name="kl-score")
def main() -> None:
    """kl-score — scoring objetivo de wiki health da knowledge layer."""


@main.command()
@click.option(
    "--graph",
    "graph_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path do graph Logseq (diretório que contém pages/ + journals/).",
)
@click.option(
    "--output",
    "output_path",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path do report markdown standalone a emitir.",
)
@click.option(
    "--filter-namespace",
    "filter_namespace",
    default=None,
    help="Prefixo de namespace pra restringir escopo (ex: pages/knowledge-layer).",
)
def score(
    graph_path: Path, output_path: Path, filter_namespace: str | None
) -> None:
    """Computa 4 métricas v0 e emite report markdown."""
    pages = list(iter_pages(graph_path, filter_namespace=filter_namespace))

    per_page = [
        (
            p.path.relative_to(graph_path),
            sum(len(b.page_links) + len(b.block_refs) for b in p.blocks),
        )
        for p in pages
    ]
    total_links = sum(c for _, c in per_page)

    orphans = orphan_nodes(graph_path)
    gaps = gaps_detected(graph_path)
    rate = enrichment_rate(graph_path)

    out: list[str] = []
    out.append(f"# kl-score report — {date.today().isoformat()}\n")
    out.append(f"Graph: `{graph_path}`")
    if filter_namespace:
        out.append(f"Filter namespace: `{filter_namespace}`")
    out.append(f"Pages escaneadas: {len(pages)}\n")

    out.append("## Métricas v0\n")

    out.append("### link_count\n")
    out.append(
        f"Total agregado: **{total_links}** "
        f"(soma de `[[page-link]]` + `((block-ref))` no escopo filtrado)\n"
    )
    if per_page:
        out.append("Top 20 por count:\n")
        for rel, c in sorted(per_page, key=lambda x: (-x[1], str(x[0])))[:20]:
            out.append(f"- `{rel}` — {c}")
        out.append("")

    out.append("### orphan_nodes\n")
    out.append(
        f"Blocos `provenance:: #enriched` sem `((uuid))` inbound "
        f"(cross-graph): **{len(orphans)}**\n"
    )
    if orphans:
        out.append("Lista (max 20):\n")
        for ref in orphans[:20]:
            out.append(f"- {ref}")
        out.append("")

    out.append("### gaps_detected\n")
    out.append(
        f"Entidades `[[mencionadas]]` ≥ 2x sem page correspondente "
        f"(legacy OR triple-lowbar, cross-graph): **{len(gaps)}**\n"
    )
    if gaps:
        out.append("Lista (max 20):\n")
        for g in gaps[:20]:
            out.append(f"- `[[{g}]]`")
        out.append("")

    out.append("### enrichment_rate\n")
    out.append(
        f"Blocos com `provenance:: #enriched` / total (cross-graph): "
        f"**{rate:.4f}** ({rate * 100:.2f}%)\n"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(out), encoding="utf-8")
    click.echo(f"Report emitido em {output_path}")


if __name__ == "__main__":
    main()
