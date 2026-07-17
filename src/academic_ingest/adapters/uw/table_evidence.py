from __future__ import annotations

from dataclasses import dataclass

from selectolax.parser import HTMLParser, Node


def clean_text(node: Node) -> str:
    return " ".join(node.text(separator=" ", strip=True).split())


@dataclass(frozen=True)
class TableRowContext:
    heading: str | None
    headers: list[str]
    cells: list[str]
    footnote: str | None
    table_identifier: str
    row_identifier: str
    row_attributes: dict[str, str | None]

    @property
    def evidence_text(self) -> str:
        parts = []
        if self.heading:
            parts.append(self.heading)
        if self.headers:
            parts.append(" | ".join(self.headers))
        parts.append(" | ".join(self.cells))
        return "\n".join(parts)


def _heading_for(table: Node) -> str | None:
    ancestor = table.parent
    while ancestor is not None:
        heading = ancestor.css_first("h2, h3, h4")
        if heading is not None:
            return clean_text(heading)
        ancestor = ancestor.parent
    caption = table.css_first("caption")
    return clean_text(caption) if caption is not None else None


def _footnote_for(tree: HTMLParser, table: Node) -> str | None:
    target = table.attributes.get("data-footnote")
    if target:
        node = tree.css_first(target)
        if node is not None:
            return clean_text(node)
    ancestor = table.parent
    if ancestor is not None:
        note = ancestor.css_first(".footnote, .table-note, .subject-note")
        if note is not None:
            return clean_text(note)
    return None


def extract_table_rows(tree: HTMLParser) -> list[TableRowContext]:
    contexts: list[TableRowContext] = []
    for table_index, table in enumerate(tree.css("table"), start=1):
        headers = [clean_text(node) for node in table.css("thead th")]
        if not headers:
            first_row = table.css_first("tr")
            if first_row is not None:
                headers = [clean_text(node) for node in first_row.css("th")]
        table_identifier = table.attributes.get("id") or f"table-{table_index}"
        heading = _heading_for(table)
        footnote = _footnote_for(tree, table)
        data_rows = table.css("tbody tr") or [row for row in table.css("tr") if row.css("td")]
        pending_rowspans: dict[int, tuple[str, int]] = {}
        for row_index, row in enumerate(data_rows, start=1):
            values_by_column: dict[int, str] = {}
            for column, (value, remaining) in list(pending_rowspans.items()):
                values_by_column[column] = value
                if remaining <= 1:
                    del pending_rowspans[column]
                else:
                    pending_rowspans[column] = (value, remaining - 1)
            column = 0
            for cell in row.css("th, td"):
                while column in values_by_column:
                    column += 1
                value = clean_text(cell)
                try:
                    colspan = max(1, int(cell.attributes.get("colspan") or "1"))
                    rowspan = max(1, int(cell.attributes.get("rowspan") or "1"))
                except ValueError:
                    colspan, rowspan = 1, 1
                for offset in range(colspan):
                    target_column = column + offset
                    values_by_column[target_column] = value
                    if rowspan > 1:
                        pending_rowspans[target_column] = (value, rowspan - 1)
                column += colspan
            width = max(len(headers), max(values_by_column, default=-1) + 1)
            cells = [values_by_column.get(index, "") for index in range(width)]
            if not cells:
                continue
            contexts.append(
                TableRowContext(
                    heading=heading,
                    headers=headers,
                    cells=cells,
                    footnote=footnote,
                    table_identifier=table_identifier,
                    row_identifier=row.attributes.get("id") or f"row-{row_index}",
                    row_attributes=dict(row.attributes),
                )
            )
    return contexts
