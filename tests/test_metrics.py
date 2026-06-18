"""Tests pytest cobrindo as 4 métricas v0.

Fixture file-based em tests/fixtures/sample_graph/ cobre integration cross-graph;
tmp_path tests cobrem edge cases isolados (empty page, no-enriched, zero-blocks).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from kl_score.metrics import (
    enrichment_rate,
    gaps_detected,
    link_count,
    orphan_nodes,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_graph"


def test_link_count_happy_path():
    """5 page links + 2 block refs = 7."""
    assert link_count(FIXTURE / "pages" / "knowledge-layer.md") == 7


def test_link_count_empty_page(tmp_path: Path):
    """Page sem links/refs → 0."""
    p = tmp_path / "empty.md"
    p.write_text("- bullet sem links\n", encoding="utf-8")
    assert link_count(p) == 0


def test_orphan_nodes_detects_unreferenced_enriched():
    """Bloco enriched + id + sem ((uuid)) inbound → no resultado."""
    result = orphan_nodes(FIXTURE)
    uuids = {r.uuid for r in result if r.uuid}
    assert "aaaaaaaa-1111-1111-1111-000000000001" in uuids


def test_orphan_nodes_excludes_referenced_via_uuid():
    """Bloco enriched + id + ((uuid)) inbound em outra page → NÃO retornado."""
    result = orphan_nodes(FIXTURE)
    uuids = {r.uuid for r in result if r.uuid}
    assert "aaaaaaaa-2222-2222-2222-000000000002" not in uuids


def test_orphan_nodes_enriched_without_id_always_orphan():
    """Bloco enriched sem id → sempre orphan (F3 metade 1)."""
    result = orphan_nodes(FIXTURE)
    no_id = [r for r in result if r.uuid is None]
    assert len(no_id) >= 1


def test_orphan_nodes_page_link_inbound_does_not_save():
    """Bloco enriched + id + só [[Page]] inbound (sem ((uuid)) apontando) → SEMPRE orphan.

    F3 metade 2 absorvida no Bloco 2: [[Page]] link inbound NÃO conta como
    salvação. Sem este teste, refactor que tolerasse page-link fallback como
    excluder de orphans passaria silencioso.
    """
    result = orphan_nodes(FIXTURE)
    uuids = {r.uuid for r in result if r.uuid}
    assert "aaaaaaaa-4444-4444-4444-000000000004" in uuids


def test_gaps_detected_above_threshold():
    """[[missing-entity]] mencionada 2x sem page → retornada."""
    gaps = gaps_detected(FIXTURE)
    assert "missing-entity" in gaps


def test_gaps_detected_below_threshold():
    """[[one-shot]] mencionada 1x < default 2 → NÃO retornada."""
    gaps = gaps_detected(FIXTURE)
    assert "one-shot" not in gaps


def test_gaps_detected_excludes_existing_pages():
    """[[wiki-compile]] mencionada 3x com page existente → NÃO retornada."""
    gaps = gaps_detected(FIXTURE)
    assert "wiki-compile" not in gaps


def test_orphan_nodes_excludes_sources_namespace_by_default():
    """Blocos em pages/sources/ não entram em orphan_nodes (default exclude).

    Lock-in da invariante `iter_pages` default sources-exclude per logseq-notes
    ADR-003 SD4 + decisão F2 do Bloco 2. Sem este teste, remoção do branch
    `rel.startswith("pages/sources/"): continue` passaria silencioso — fixture
    sources/sample-source.md tem provenance:: #source mas nenhum bloco enriched;
    invariante é que nada de pages/sources/ entra no escopo independente do conteúdo.
    """
    result = orphan_nodes(FIXTURE)
    paths = {str(r.page_path) for r in result}
    assert not any("pages/sources" in p for p in paths)


def test_gaps_detected_namespace_slug():
    """[[Foo/Bar]] mencionada 2x sem pages/Foo___Bar.md → retornada.

    Lock-in da decisão absorvida no gate manual §3.2 do Bloco 2: namespace
    separator '/' vira '___' no slug Logseq triple-lowbar. Refactor regressivo
    do _slug_logseq em metrics.py é flagrado.
    """
    gaps = gaps_detected(FIXTURE)
    assert "Foo/Bar" in gaps


def test_orphan_nodes_provenance_filter_custom(tmp_path: Path):
    """`provenance_filter='source'` retorna blocos #source não-referenciados.

    Lock-in da parametrização documentada de `orphan_nodes`: refactor que
    hardcode 'enriched' no corpo da função é flagrado. Cobertura cara para
    uso especulativo justificada pelo parâmetro já público.
    """
    journals = tmp_path / "journals"
    journals.mkdir()
    (journals / "test.md").write_text(
        "- bloco source 1\n"
        "  provenance:: #source\n"
        "  id:: bbbbbbbb-1111-1111-1111-000000000001\n"
        "- bloco source 2\n"
        "  provenance:: #source\n",
        encoding="utf-8",
    )
    enriched_orphans = orphan_nodes(tmp_path, provenance_filter="enriched")
    source_orphans = orphan_nodes(tmp_path, provenance_filter="source")
    assert len(enriched_orphans) == 0
    assert len(source_orphans) == 2


def test_enrichment_rate_partial(tmp_path: Path):
    """5 blocos total + 3 enriched → 0.6."""
    journals = tmp_path / "journals"
    journals.mkdir()
    (journals / "test.md").write_text(
        "- bloco 1\n"
        "  provenance:: #enriched\n"
        "- bloco 2\n"
        "  provenance:: #enriched\n"
        "- bloco 3\n"
        "  provenance:: #enriched\n"
        "- bloco 4 sem provenance\n"
        "- bloco 5 sem provenance\n",
        encoding="utf-8",
    )
    assert enrichment_rate(tmp_path) == pytest.approx(0.6)


def test_enrichment_rate_no_enriched(tmp_path: Path):
    """Graph com blocos mas 0 enriched → 0.0."""
    journals = tmp_path / "journals"
    journals.mkdir()
    (journals / "test.md").write_text(
        "- bloco 1 sem provenance\n- bloco 2 sem provenance\n",
        encoding="utf-8",
    )
    assert enrichment_rate(tmp_path) == 0.0


def test_enrichment_rate_zero_blocks(tmp_path: Path):
    """Graph vazio → 0.0 (guard contra ZeroDivisionError)."""
    assert enrichment_rate(tmp_path) == 0.0
