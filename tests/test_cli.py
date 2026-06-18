"""Integration test end-to-end para o sub-comando `score` da CLI."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from kl_score.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "sample_graph"


def test_score_command_full_run(tmp_path: Path):
    """`kl-score score` produz report markdown com seções canonical + signal real do fixture."""
    output = tmp_path / "report.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["score", "--graph", str(FIXTURE), "--output", str(output)],
    )
    assert result.exit_code == 0, result.output

    report = output.read_text(encoding="utf-8")
    assert "## Métricas v0" in report
    assert "### link_count" in report
    assert "### orphan_nodes" in report
    assert "### gaps_detected" in report
    assert "### enrichment_rate" in report
    assert "missing-entity" in report


def test_score_command_filter_namespace_overrides_sources_exclude(tmp_path: Path):
    """--filter-namespace explícito sobrepõe default sources-exclude (F2 Bloco 2).

    Comportamento: sem --filter-namespace, pages/sources/* é excluído por default;
    com --filter-namespace pages/sources, conteúdo de sources/ entra no report.
    Lock-in contra refactor regressivo do branch explícito-sobrepõe-implícito em
    `iter_pages` (kl_score/parser.py).
    """
    no_filter = tmp_path / "no_filter.md"
    runner = CliRunner()
    result_default = runner.invoke(
        main, ["score", "--graph", str(FIXTURE), "--output", str(no_filter)]
    )
    assert result_default.exit_code == 0
    assert "sources/sample-source" not in no_filter.read_text(encoding="utf-8")

    with_filter = tmp_path / "with_filter.md"
    result_filter = runner.invoke(
        main,
        [
            "score",
            "--graph",
            str(FIXTURE),
            "--filter-namespace",
            "pages/sources",
            "--output",
            str(with_filter),
        ],
    )
    assert result_filter.exit_code == 0
    assert "sources/sample-source" in with_filter.read_text(encoding="utf-8")
