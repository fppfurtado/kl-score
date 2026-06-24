"""kl-score CLI entry-point.

Bloco 2: wire das 4 métricas v0 + emissão de report markdown standalone.
Onda 4+: modo --format json para consumo programático (contrato cross-repo
consumido pelo /wiki-lint; ver ADR-001 § Adendo modo JSON).
Graph é read-only em todos os caminhos.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import click

from kl_score import __version__
from kl_score.metrics import (
    _GAP_NOISE_PATTERNS,
    enrichment_rate,
    gaps_detected,
    orphan_nodes,
)
from kl_score.parser import iter_pages

JSON_SCHEMA_VERSION = "1.1"


def _compute_metrics(
    graph_path: Path,
    filter_namespace: str | None,
    exclude_gap_patterns: tuple[str, ...] = (),
) -> dict:
    """Computa as 4 métricas v0 uma vez; consumido pelos caminhos markdown e json."""
    pages = list(iter_pages(graph_path, filter_namespace=filter_namespace))
    per_page = [
        (
            p.path.relative_to(graph_path),
            sum(len(b.page_links) + len(b.block_refs) for b in p.blocks),
        )
        for p in pages
    ]
    return {
        "pages_scanned": len(pages),
        "per_page": per_page,
        "total_links": sum(c for _, c in per_page),
        "orphans": orphan_nodes(graph_path),
        "gaps": gaps_detected(
            graph_path, exclude_patterns=list(exclude_gap_patterns)
        ),
        "gap_filters_applied": [*_GAP_NOISE_PATTERNS, *exclude_gap_patterns],
        "rate": enrichment_rate(graph_path, filter_namespace=filter_namespace),
    }


def _build_json_payload(
    graph_path: Path, filter_namespace: str | None, m: dict
) -> dict:
    """Monta o envelope JSON estável (schema_version 1.1) — contrato do /wiki-lint."""
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "graph": str(graph_path),
        "filter_namespace": filter_namespace,
        "pages_scanned": m["pages_scanned"],
        "metrics": {
            "link_count": {
                "total": m["total_links"],
                "per_page": [
                    {"page": rel.as_posix(), "count": c}
                    for rel, c in m["per_page"]
                ],
            },
            "orphan_nodes": {
                "count": len(m["orphans"]),
                "items": [
                    {
                        "page": ref.page_path.relative_to(graph_path).as_posix(),
                        "uuid": ref.uuid,
                        "excerpt": ref.body_excerpt,
                    }
                    for ref in m["orphans"]
                ],
            },
            "gaps_detected": {
                "count": len(m["gaps"]),
                "items": list(m["gaps"]),
                "filters_applied": m["gap_filters_applied"],
            },
            "enrichment_rate": m["rate"],
        },
    }


def _render_markdown(
    graph_path: Path, filter_namespace: str | None, m: dict
) -> str:
    """Renderiza o report markdown standalone a partir das métricas computadas."""
    out: list[str] = []
    out.append(f"# kl-score report — {date.today().isoformat()}\n")
    out.append(f"Graph: `{graph_path}`")
    if filter_namespace:
        out.append(f"Filter namespace: `{filter_namespace}`")
    out.append(f"Pages escaneadas: {m['pages_scanned']}\n")

    out.append("## Métricas v0\n")

    out.append("### link_count\n")
    out.append(
        f"Total agregado: **{m['total_links']}** "
        f"(soma de `[[page-link]]` + `((block-ref))` no escopo filtrado)\n"
    )
    if m["per_page"]:
        out.append("Top 20 por count:\n")
        for rel, c in sorted(m["per_page"], key=lambda x: (-x[1], str(x[0])))[:20]:
            out.append(f"- `{rel}` — {c}")
        out.append("")

    out.append("### orphan_nodes\n")
    out.append(
        f"Blocos `provenance:: #enriched` sem `((uuid))` inbound "
        f"(cross-graph): **{len(m['orphans'])}**\n"
    )
    if m["orphans"]:
        out.append("Lista (max 20):\n")
        for ref in m["orphans"][:20]:
            out.append(f"- {ref}")
        out.append("")

    out.append("### gaps_detected\n")
    out.append(
        f"Entidades `[[mencionadas]]` ≥ 2x sem page correspondente "
        f"(slug `:triple-lowbar`, cross-graph): **{len(m['gaps'])}**\n"
    )
    if m["gaps"]:
        out.append("Lista (max 20):\n")
        for g in m["gaps"][:20]:
            out.append(f"- `[[{g}]]`")
        out.append("")

    out.append("### enrichment_rate\n")
    rate_scope = (
        f"namespace `{filter_namespace}`" if filter_namespace else "cross-graph"
    )
    out.append(
        f"Blocos com `provenance:: #enriched` / total ({rate_scope}): "
        f"**{m['rate']:.4f}** ({m['rate'] * 100:.2f}%)\n"
    )
    return "\n".join(out)


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
    required=False,
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path do report a emitir. Obrigatório em --format markdown; "
    "em --format json, omitir emite para stdout.",
)
@click.option(
    "--filter-namespace",
    "filter_namespace",
    default=None,
    help="Prefixo de namespace pra restringir escopo (ex: pages/knowledge-layer).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Formato de saída. markdown (default) emite report standalone; "
    "json emite envelope estável (schema_version 1.1) para consumo programático.",
)
@click.option(
    "--exclude-gap-pattern",
    "exclude_gap_patterns",
    multiple=True,
    help="Regex (substring, NÃO-ancorado) pra excluir entidades de "
    "gaps_detected — ex.: namespaces externos. Repetível. Ruído estrutural "
    "(ADR-NNN, #NN) já é filtrado por default; cuidado com padrões amplos "
    "(ex.: 'ADR' casaria 'Padrão ADR de Workflow').",
)
def score(
    graph_path: Path,
    output_path: Path | None,
    filter_namespace: str | None,
    output_format: str,
    exclude_gap_patterns: tuple[str, ...],
) -> None:
    """Computa 4 métricas v0 e emite report markdown ou JSON estável."""
    for pat in exclude_gap_patterns:
        try:
            re.compile(pat)
        except re.error as exc:
            raise click.ClickException(
                f"--exclude-gap-pattern regex inválido {pat!r}: {exc}"
            )
    m = _compute_metrics(graph_path, filter_namespace, exclude_gap_patterns)

    if output_format == "json":
        rendered = json.dumps(
            _build_json_payload(graph_path, filter_namespace, m),
            indent=2,
            ensure_ascii=False,
        )
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
            click.echo(f"JSON emitido em {output_path}")
        else:
            click.echo(rendered)
        return

    if output_path is None:
        raise click.ClickException(
            "modo markdown exige --output <path.md>; "
            "use --format json para emitir para stdout."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _render_markdown(graph_path, filter_namespace, m), encoding="utf-8"
    )
    click.echo(f"Report emitido em {output_path}")


if __name__ == "__main__":
    main()
