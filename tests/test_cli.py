"""Integration test end-to-end para o sub-comando `score` da CLI."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
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


def _run_json(*extra: str) -> dict:
    """Roda `score --format json` e parseia o stdout como dict (contrato cross-repo)."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["score", "--graph", str(FIXTURE), "--format", "json", *extra]
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def test_score_json_stdout_is_valid_envelope():
    """`score --format json` sem --output emite envelope JSON válido em stdout."""
    payload = _run_json()
    assert payload["schema_version"] == "1.1"
    assert payload["graph"] == str(FIXTURE)
    assert payload["filter_namespace"] is None
    assert isinstance(payload["pages_scanned"], int)


def test_score_json_envelope_has_four_metrics_with_lists():
    """As 4 métricas v0 + listas estruturadas aparecem no envelope (não só agregados)."""
    metrics = _run_json()["metrics"]
    assert set(metrics) == {
        "link_count",
        "orphan_nodes",
        "gaps_detected",
        "enrichment_rate",
    }

    # link_count: total agregado + per_page integral
    assert isinstance(metrics["link_count"]["total"], int)
    assert isinstance(metrics["link_count"]["per_page"], list)
    assert all(
        {"page", "count"} <= set(p) for p in metrics["link_count"]["per_page"]
    )

    # orphan_nodes: count + items como objetos estruturados (page/uuid/excerpt), não str
    orphans = metrics["orphan_nodes"]
    assert orphans["count"] == len(orphans["items"])
    assert all({"page", "uuid", "excerpt"} == set(it) for it in orphans["items"])

    # gaps_detected: count + items como nomes de entidade (str)
    gaps = metrics["gaps_detected"]
    assert gaps["count"] == len(gaps["items"])
    assert all(isinstance(g, str) for g in gaps["items"])
    assert "missing-entity" in gaps["items"]

    # enrichment_rate: float
    assert isinstance(metrics["enrichment_rate"], float)


def test_score_json_orphan_uuid_nullable_is_explicit_null():
    """`uuid` é `str | None`: chave sempre presente, None serializa como null JSON.

    Trava o ponto mais frágil do contrato — orphan sem `id::` produz `uuid: null`
    (não chave-ausente, não ""). /wiki-lint precisa tolerar null nesse campo.
    """
    items = _run_json()["metrics"]["orphan_nodes"]["items"]
    assert any(it["uuid"] is None for it in items)
    assert any(isinstance(it["uuid"], str) for it in items)
    assert all("uuid" in it for it in items)


def test_score_json_metric_values_match_fixture_signal():
    """Asserts de valor (não só de tipo) ancorados no signal real da fixture."""
    payload = _run_json()
    metrics = payload["metrics"]
    assert payload["pages_scanned"] == 3
    assert metrics["link_count"]["total"] == 12
    assert metrics["orphan_nodes"]["count"] == 3
    # gaps namespaced sai como nome-de-exibição (Foo/Bar), não slug (Foo___Bar)
    assert metrics["gaps_detected"]["items"] == ["Foo/Bar", "missing-entity"]
    # enrichment_rate ponderado por quality-score (ADR-001 Adendo)
    assert metrics["enrichment_rate"] == pytest.approx(0.3077, abs=1e-4)


def test_score_json_per_page_is_integral_not_truncated():
    """per_page no JSON lista todas as pages do escopo (sem top-N do markdown)."""
    payload = _run_json()
    per_page = payload["metrics"]["link_count"]["per_page"]
    # fixture tem 3 pages no escopo default; JSON não trunca
    assert len(per_page) == 3
    assert len(per_page) == payload["pages_scanned"]


def test_score_json_empty_namespace_keeps_stable_envelope():
    """--filter-namespace sem pages mantém o envelope estruturalmente estável."""
    payload = _run_json("--filter-namespace", "pages/inexistente")
    metrics = payload["metrics"]
    assert payload["pages_scanned"] == 0
    assert metrics["link_count"]["per_page"] == []
    assert metrics["link_count"]["total"] == 0
    # as 4 chaves continuam presentes — envelope não degrada com escopo vazio
    assert set(metrics) == {
        "link_count",
        "orphan_nodes",
        "gaps_detected",
        "enrichment_rate",
    }


def test_score_json_is_deterministic():
    """Contrato cross-repo: listas ordenadas determinísticas; runs byte-idênticos."""
    runner = CliRunner()
    args = ["score", "--graph", str(FIXTURE), "--format", "json"]
    first = runner.invoke(main, args).output
    second = runner.invoke(main, args).output
    assert first == second
    assert json.loads(first)["metrics"]["gaps_detected"]["items"] == [
        "Foo/Bar",
        "missing-entity",
    ]


def test_score_json_filter_namespace_propagates():
    """--filter-namespace é refletido no envelope JSON."""
    payload = _run_json("--filter-namespace", "pages/knowledge-layer")
    assert payload["filter_namespace"] == "pages/knowledge-layer"


def test_score_json_to_file_writes_envelope(tmp_path: Path):
    """`score --format json --output <file>` grava o JSON no arquivo."""
    output = tmp_path / "metrics.json"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "score",
            "--graph",
            str(FIXTURE),
            "--format",
            "json",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.1"


def test_score_markdown_without_output_fails_loud():
    """modo markdown (default) sem --output falha loud, não no-op silencioso."""
    runner = CliRunner()
    result = runner.invoke(main, ["score", "--graph", str(FIXTURE)])
    assert result.exit_code != 0
    assert "--output" in result.output


def test_score_json_gaps_filters_applied_default():
    """filters_applied lista os padrões estruturais built-in por default."""
    fa = _run_json()["metrics"]["gaps_detected"]["filters_applied"]
    assert fa == [r"^ADR-\d+$", r"^#\d+$"]


def test_score_json_exclude_gap_pattern_extends_and_filters():
    """--exclude-gap-pattern entra em filters_applied e filtra os items."""
    # fixture tem gap 'Foo/Bar'; --exclude-gap-pattern Bar o remove (substring)
    payload = _run_json("--exclude-gap-pattern", "Bar")
    gaps = payload["metrics"]["gaps_detected"]
    assert gaps["filters_applied"] == [r"^ADR-\d+$", r"^#\d+$", "Bar"]
    assert not any("Bar" in g for g in gaps["items"])
    assert gaps["count"] == len(gaps["items"])


def test_score_invalid_exclude_gap_pattern_fails_loud():
    """regex inválido em --exclude-gap-pattern falha loud (não traceback cru)."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["score", "--graph", str(FIXTURE), "--format", "json",
         "--exclude-gap-pattern", "["],
    )
    assert result.exit_code != 0
    assert "exclude-gap-pattern" in result.output
    assert "Traceback" not in result.output


def test_filters_applied_patterns_are_effective(tmp_path: Path):
    """Cada pattern declarado em filters_applied de fato remove uma entidade que casa.

    Fecha o loop declarado→aplicado: filters_applied não pode mentir sobre o que
    o filtro removeu (contrato cross-repo consumido pelo /wiki-lint).
    """
    pages = tmp_path / "pages"
    pages.mkdir()
    (tmp_path / "journals").mkdir()
    (pages / "ref.md").write_text(
        "- a [[ADR-001]]\n- a [[ADR-001]]\n"
        "- b [[#19]]\n- b [[#19]]\n"
        "- c [[Request TJPA-13]]\n- c [[Request TJPA-13]]\n"
        "- d [[real-concept]]\n- d [[real-concept]]\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["score", "--graph", str(tmp_path), "--format", "json",
         "--exclude-gap-pattern", "TJPA"],
    )
    assert result.exit_code == 0, result.output
    gaps = json.loads(result.output)["metrics"]["gaps_detected"]
    assert gaps["filters_applied"] == [r"^ADR-\d+$", r"^#\d+$", "TJPA"]
    # cada pattern declarado é efetivo: nenhum item sobrevivente casa qualquer um
    for pat in gaps["filters_applied"]:
        assert not any(re.search(pat, item) for item in gaps["items"])
    # conceito real preservado
    assert "real-concept" in gaps["items"]


def test_score_json_filter_namespace_scopes_only_enrichment():
    """--filter-namespace escopa enrichment_rate; orphan/gaps seguem globais."""
    glob = _run_json()["metrics"]
    scoped = _run_json("--filter-namespace", "pages/knowledge-layer")["metrics"]
    # enrichment_rate escopa — valores ancorados (não só desigualdade)
    assert glob["enrichment_rate"] == pytest.approx(0.3077, abs=1e-4)
    assert scoped["enrichment_rate"] == pytest.approx(0.0)
    # orphan_nodes / gaps_detected são globais — inalterados pelo filtro
    assert glob["orphan_nodes"]["count"] == scoped["orphan_nodes"]["count"]
    assert glob["gaps_detected"]["count"] == scoped["gaps_detected"]["count"]
