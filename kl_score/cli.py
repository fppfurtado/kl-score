"""kl-score CLI entry-point.

Bloco 1 (bootstrap): skeleton CLI declarando sub-comando `score` com flags canonical.
Implementação das 4 métricas (link_count, orphan_nodes, gaps_detected, enrichment_rate)
vive no Bloco 2 (`kl_score/metrics.py` + `kl_score/parser.py`).
"""

import click

from kl_score import __version__


@click.group()
@click.version_option(__version__, prog_name="kl-score")
def main() -> None:
    """kl-score — scoring objetivo de wiki health da knowledge layer."""


@main.command()
@click.option(
    "--graph",
    "graph_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path do graph Logseq (diretório que contém pages/ + journals/).",
)
@click.option(
    "--output",
    "output_path",
    required=True,
    type=click.Path(dir_okay=False),
    help="Path do report markdown standalone a emitir.",
)
@click.option(
    "--filter-namespace",
    "filter_namespace",
    default=None,
    help="Prefixo de namespace pra restringir escopo (ex: pages/knowledge-layer).",
)
def score(graph_path: str, output_path: str, filter_namespace: str | None) -> None:
    """Computa 4 métricas v0 funcional contra o graph e emite report markdown."""
    raise click.ClickException(
        "métricas v0 não implementadas (Bloco 1 = bootstrap; Bloco 2 implementa "
        "link_count + orphan_nodes + gaps_detected + enrichment_rate em metrics.py)"
    )


if __name__ == "__main__":
    main()
