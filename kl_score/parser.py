"""Parser read-only do graph Logseq markdown.

Schema canonical do graph em logseq-notes ADR-003. Parser NUNCA muta o graph
(hard invariant per CLAUDE.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

_PAGE_LINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")
_BLOCK_REF_RE = re.compile(r"\(\(([0-9a-fA-F-]{8,})\)\)")
_PROPERTY_RE = re.compile(r"^\s*([\w-]+)::\s*(.*)$")
_BULLET_RE = re.compile(r"^(\s*)-\s+(.*)$")


@dataclass
class Block:
    page_path: Path
    body: str
    indent_level: int
    properties: dict[str, str] = field(default_factory=dict)
    page_links: set[str] = field(default_factory=set)
    block_refs: set[str] = field(default_factory=set)

    @property
    def uuid(self) -> str | None:
        return self.properties.get("id")

    @property
    def provenance(self) -> str | None:
        raw = self.properties.get("provenance")
        if raw is None:
            return None
        return raw.lstrip("#").strip()


@dataclass
class Page:
    path: Path
    properties: dict[str, str] = field(default_factory=dict)
    blocks: list[Block] = field(default_factory=list)

    @property
    def page_links(self) -> set[str]:
        return {link for b in self.blocks for link in b.page_links}

    @property
    def block_refs(self) -> set[str]:
        return {ref for b in self.blocks for ref in b.block_refs}

    @property
    def quality_score(self) -> str | None:
        raw = self.properties.get("quality-score")
        if raw is None:
            return None
        return raw.lstrip("#").strip()


def _extract_inline(text: str) -> tuple[set[str], set[str]]:
    return (
        set(_PAGE_LINK_RE.findall(text)),
        set(_BLOCK_REF_RE.findall(text)),
    )


def parse_page(path: Path) -> Page:
    """Parseia uma page Logseq markdown.

    Page properties: linhas `key:: value` antes do primeiro bullet.
    Block properties: linhas `key:: value` indentadas após um bullet (associadas
    ao bloco corrente).
    """
    text = path.read_text(encoding="utf-8")
    page = Page(path=path)

    in_page_properties = True
    current_block: Block | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            in_page_properties = False
            continue

        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            in_page_properties = False
            indent = bullet_match.group(1)
            body = bullet_match.group(2)
            level = len(indent.expandtabs(2)) // 2
            current_block = Block(page_path=path, body=body, indent_level=level)
            links, refs = _extract_inline(body)
            current_block.page_links |= links
            current_block.block_refs |= refs
            page.blocks.append(current_block)
            continue

        prop_match = _PROPERTY_RE.match(line)
        if prop_match:
            key, value = prop_match.group(1), prop_match.group(2).strip()
            if in_page_properties:
                page.properties[key] = value
            elif current_block is not None:
                current_block.properties[key] = value
            continue

        if current_block is not None and not in_page_properties:
            current_block.body += "\n" + line
            links, refs = _extract_inline(line)
            current_block.page_links |= links
            current_block.block_refs |= refs

    return page


def iter_pages(
    graph_root: Path, filter_namespace: str | None = None
) -> Iterator[Page]:
    """Itera pages do graph.

    Default sources-exclude só aplica quando `filter_namespace=None`. Explícito
    sobrepõe implícito — `--filter-namespace sources/foo` retorna conteúdo de
    sources/ (operador sabe o que pediu).
    """
    pages_dir = graph_root / "pages"
    if not pages_dir.is_dir():
        return

    normalized: str | None
    if filter_namespace is None:
        normalized = None
    else:
        n = filter_namespace.lstrip("/")
        if not n.startswith("pages/"):
            n = f"pages/{n}"
        normalized = n

    for md_path in sorted(pages_dir.rglob("*.md")):
        rel = md_path.relative_to(graph_root).as_posix()
        if normalized is None:
            if rel.startswith("pages/sources/"):
                continue
        else:
            if not rel.startswith(normalized):
                continue
        yield parse_page(md_path)


def iter_journals(graph_root: Path) -> Iterator[Page]:
    """Itera journals do graph (paralelo a iter_pages, sem filtro)."""
    journals_dir = graph_root / "journals"
    if not journals_dir.is_dir():
        return
    for md_path in sorted(journals_dir.rglob("*.md")):
        yield parse_page(md_path)


def iter_blocks(page: Page) -> Iterator[Block]:
    """Itera blocos de uma page (ordem natural de leitura)."""
    yield from page.blocks
