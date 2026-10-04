"""Index source-faithful Markdown into bounded, located passages."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from bav.extractor.research.contracts import Passage
from bav.extractor.research.paths import sha256_text

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
LETTER_RE = re.compile(r"[A-Za-z]")
NONSPACE_RE = re.compile(r"\S")
OVERSIZE_CHARS = 8000
UNREADABLE_LETTER_RATIO = 0.35
WINDOW_CHARS = 1800
CONTEXT_CHARS = 1800
BOUNDED_CONTEXT_LIMITATION = "bounded_context_omitted_qualification"
QUALIFICATION_HINT_RE = re.compile(
    r"\b(exclud(?:e|es|ed|ing)|except|attributable|currency|not\s+|notes?:|units?)\b",
    re.I,
)


def index_document_markdown(
    document_md: Path,
    *,
    document_id: str,
    source_fingerprint: str,
    representation_fingerprint: str | None = None,
    known_pages: Mapping[tuple[int, int], int] | None = None,
    existing_limitations: tuple[str, ...] = (),
) -> tuple[tuple[Passage, ...], tuple[str, ...]]:
    text = document_md.read_bytes().decode("utf-8")
    prepared_hash = representation_fingerprint or sha256_text(text)
    lines = text.split("\n")
    offsets = _line_offsets(text)
    sections = _split_sections(lines)
    passages: list[Passage] = []
    limitations = list(existing_limitations)
    for index, section in enumerate(sections):
        start, end, heading = section
        body = "\n".join(lines[start - 1 : end])
        section_limits: list[str] = []
        if _is_unreadable(body):
            section_limits.append("unreadable_text_layer")
            if "unreadable_text_layer" not in limitations:
                limitations.append("unreadable_text_layer")
        if len(body) > OVERSIZE_CHARS:
            section_limits.append("oversized_section")
            if "oversized_section_not_fully_indexed" not in limitations:
                limitations.append("oversized_section_not_fully_indexed")
        blocks = _blocks_in_section(lines, start, end)
        if not blocks:
            blocks = [(start, end, "text")]
        for block_index, (block_start, block_end, kind) in enumerate(blocks):
            block_text = "\n".join(lines[block_start - 1 : block_end]).rstrip()
            if not block_text.strip():
                continue
            selected, truncated = _bound_text(block_text)
            block_limits = list(section_limits)
            if truncated:
                block_limits.append("oversized_section")
            footnotes = _following_footnotes(lines, block_end, end)
            locator_end = block_end
            if footnotes and kind != "footnote":
                selected = selected + "\n" + footnotes
                locator_end = _footnote_end_line(lines, block_end, end) or block_end
            context, context_limits, context_span = _adjacent_context(lines, blocks, block_index)
            block_limits.extend(context_limits)
            table = _table_payload(selected) if kind == "table" else None
            physical = None
            if known_pages:
                physical = known_pages.get((block_start, locator_end))
                if physical is None:
                    physical = known_pages.get((block_start, block_end))
            end_line, end_offset = _selected_end_locator(
                lines,
                offsets,
                block_start,
                selected,
                fallback_end=locator_end,
            )
            passage_id = _passage_id(document_id, block_start, end_line, selected)
            passages.append(
                Passage(
                    passage_id=passage_id,
                    document_id=document_id,
                    heading=_clean_heading(heading),
                    text=selected,
                    context=context,
                    start_line=block_start,
                    end_line=end_line,
                    start_offset=offsets[block_start - 1],
                    end_offset=end_offset,
                    kind=kind,  # type: ignore[arg-type]
                    table=table,
                    physical_pdf_page=physical,
                    printed_page_label=None,
                    limitations=tuple(dict.fromkeys(block_limits)),
                    source_fingerprint=source_fingerprint,
                    representation_fingerprint=prepared_hash,
                    context_start_line=context_span[0] if context_span else None,
                    context_end_line=context_span[1] if context_span else None,
                )
            )
    return tuple(passages), tuple(dict.fromkeys(limitations))


def write_passages_json(
    path: Path,
    *,
    document_id: str,
    passages: tuple[Passage, ...],
    limitations: tuple[str, ...],
) -> None:
    payload = {
        "document_id": document_id,
        "limitations": list(limitations),
        "passages": [passage_to_dict(item) for item in passages],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def passage_to_dict(passage: Passage) -> dict[str, Any]:
    return {
        "id": passage.passage_id,
        "document_id": passage.document_id,
        "heading": passage.heading,
        "text": passage.text,
        "context": passage.context,
        "kind": passage.kind,
        "table": passage.table,
        "locator": {
            "markdown_lines": [passage.start_line, passage.end_line],
            "offsets": [passage.start_offset, passage.end_offset],
            "context_markdown_lines": (
                [passage.context_start_line, passage.context_end_line]
                if passage.context_start_line is not None and passage.context_end_line is not None
                else None
            ),
            "physical_pdf_page": passage.physical_pdf_page,
            "printed_page_label": passage.printed_page_label,
        },
        "limitations": list(passage.limitations),
        "source_fingerprint": passage.source_fingerprint,
        "representation_fingerprint": passage.representation_fingerprint,
    }


def _line_offsets(text: str) -> list[int]:
    """Offsets follow LF-separated Markdown lines; lone CR stays inside the line."""
    offsets = [0]
    total = 0
    parts = text.split("\n")
    for index, line in enumerate(parts[:-1]):
        total += len(line) + 1
        offsets.append(total)
    return offsets


def _split_sections(lines: list[str]) -> list[tuple[int, int, str]]:
    headings = []
    for number, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line.rstrip("\r"))
        if match:
            headings.append((number, match.group(2)))
    if not headings:
        return [(1, len(lines) or 1, "")]
    sections: list[tuple[int, int, str]] = []
    for index, (start, heading) in enumerate(headings):
        end = headings[index + 1][0] - 1 if index + 1 < len(headings) else len(lines)
        sections.append((start, max(start, end), heading))
    if headings[0][0] > 1:
        sections.insert(0, (1, headings[0][0] - 1, ""))
    return sections


def _blocks_in_section(lines: list[str], start: int, end: int) -> list[tuple[int, int, str]]:
    blocks: list[tuple[int, int, str]] = []
    cursor = start
    while cursor <= end:
        line = lines[cursor - 1]
        if _is_table_line(line):
            table_start = cursor
            while cursor <= end and _is_table_line(lines[cursor - 1]):
                cursor += 1
            footnote_end = cursor - 1
            lookahead = cursor
            while lookahead <= end and not lines[lookahead - 1].strip():
                lookahead += 1
            if lookahead <= end and _is_footnote_line(lines[lookahead - 1]):
                cursor = lookahead
                while cursor <= end and (
                    _is_footnote_line(lines[cursor - 1]) or not lines[cursor - 1].strip()
                ):
                    if _is_footnote_line(lines[cursor - 1]):
                        footnote_end = cursor
                    cursor += 1
            blocks.append((table_start, footnote_end, "table"))
            continue
        if _is_footnote_line(line):
            note_start = cursor
            while cursor <= end and (
                _is_footnote_line(lines[cursor - 1]) or not lines[cursor - 1].strip()
            ):
                cursor += 1
            blocks.append((note_start, cursor - 1, "footnote"))
            continue
        para_start = cursor
        while cursor <= end and not _is_table_line(lines[cursor - 1]) and not _is_footnote_line(lines[cursor - 1]):
            if not lines[cursor - 1].strip() and cursor > para_start:
                break
            cursor += 1
        if cursor > para_start:
            blocks.append((para_start, cursor - 1 if cursor > para_start else para_start, "text"))
        if cursor == para_start:
            cursor += 1
        elif cursor <= end and not lines[cursor - 1].strip():
            cursor += 1
    return blocks


def _is_table_line(line: str) -> bool:
    stripped = line.rstrip("\r").strip()
    return stripped.startswith("|") and stripped.count("|") >= 2


def _is_footnote_line(line: str) -> bool:
    stripped = line.rstrip("\r").strip()
    return bool(re.match(r"^(Notes?:|Note\s+\d+|[*>]\s)", stripped, re.I))


def _following_footnotes(lines: list[str], after: int, section_end: int) -> str:
    collected: list[str] = []
    cursor = after + 1
    while cursor <= section_end and not lines[cursor - 1].strip():
        cursor += 1
    while cursor <= section_end and _is_footnote_line(lines[cursor - 1]):
        collected.append(lines[cursor - 1])
        cursor += 1
    return "\n".join(collected)


def _footnote_end_line(lines: list[str], after: int, section_end: int) -> int | None:
    cursor = after + 1
    while cursor <= section_end and not lines[cursor - 1].strip():
        cursor += 1
    last = None
    while cursor <= section_end and _is_footnote_line(lines[cursor - 1]):
        last = cursor
        cursor += 1
    return last


def _adjacent_context(
    lines: list[str],
    blocks: list[tuple[int, int, str]],
    index: int,
) -> tuple[str, tuple[str, ...], tuple[int, int] | None]:
    """Same-section neighboring paragraphs, never other-section openings."""
    prev_blocks = blocks[:index]
    next_blocks = blocks[index + 1 :]
    necessary: list[tuple[int, int]] = []
    optional: list[tuple[int, int]] = []
    if prev_blocks:
        necessary.append((prev_blocks[-1][0], prev_blocks[-1][1]))
        optional.extend((start, end) for start, end, _kind in reversed(prev_blocks[:-1]))
    if next_blocks:
        necessary.append((next_blocks[0][0], next_blocks[0][1]))
        optional.extend((start, end) for start, end, _kind in next_blocks[1:])
    parts: list[tuple[int, int, str]] = []
    limits: list[str] = []
    used = 0
    for start, end in necessary:
        text = "\n".join(lines[start - 1 : end]).rstrip()
        if not text.strip():
            continue
        if len(text) > CONTEXT_CHARS:
            kept, _truncated = _bound_text(text)
            parts.append((start, end, kept))
            used += len(kept)
            limits.append(BOUNDED_CONTEXT_LIMITATION)
        else:
            parts.append((start, end, text))
            used += len(text) + (2 if used else 0)
    for start, end in optional:
        text = "\n".join(lines[start - 1 : end]).rstrip()
        if not text.strip():
            continue
        extra = len(text) + (2 if parts else 0)
        if used + extra <= CONTEXT_CHARS:
            parts.append((start, end, text))
            used += extra
            continue
        if _looks_like_qualification(text):
            limits.append(BOUNDED_CONTEXT_LIMITATION)
        break
    if not parts:
        return "", tuple(dict.fromkeys(limits)), None
    parts.sort(key=lambda item: item[0])
    context = "\n\n".join(item[2] for item in parts)
    return context, tuple(dict.fromkeys(limits)), (parts[0][0], parts[-1][1])


def _looks_like_qualification(text: str) -> bool:
    return bool(QUALIFICATION_HINT_RE.search(text))


def _selected_end_locator(
    lines: list[str],
    offsets: list[int],
    start_line: int,
    selected: str,
    *,
    fallback_end: int,
) -> tuple[int, int]:
    if not lines:
        return 1, 0
    fallback = min(max(fallback_end, start_line), len(lines))
    fallback_offset = offsets[fallback - 1] + len(lines[fallback - 1])
    if not selected:
        return fallback, fallback_offset
    accumulated: list[str] = []
    for number in range(start_line, len(lines) + 1):
        accumulated.append(lines[number - 1])
        joined = "\n".join(accumulated)
        if joined == selected or joined.rstrip() == selected:
            return number, offsets[number - 1] + len(lines[number - 1])
        if len(joined) >= len(selected) and joined.startswith(selected):
            prefix = "\n".join(accumulated[:-1])
            consumed = len(selected) - len(prefix) - (1 if prefix else 0)
            return number, offsets[number - 1] + max(consumed, 0)
    return fallback, fallback_offset


def _table_payload(text: str) -> dict[str, Any] | None:
    rows = []
    units = None
    for line in text.splitlines():
        if _is_table_line(line):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells if cell):
                rows.append(cells)
        if "yen" in line.lower() or "million" in line.lower() or "usd" in line.lower():
            units = line.strip()
    if not rows:
        return None
    return {
        "headers": rows[0],
        "rows": rows[1:],
        "units": units,
        "footnotes": [line for line in text.splitlines() if _is_footnote_line(line)],
    }


def _bound_text(text: str) -> tuple[str, bool]:
    if len(text) <= WINDOW_CHARS:
        return text, False
    cut = text[:WINDOW_CHARS]
    boundary = max(cut.rfind("\n\n"), cut.rfind(". "), cut.rfind("\n"))
    if boundary < WINDOW_CHARS // 2:
        boundary = WINDOW_CHARS
    return text[:boundary].rstrip(), True


def _is_unreadable(text: str) -> bool:
    nonspace = NONSPACE_RE.findall(text)
    if len(nonspace) < 80:
        return False
    letters = LETTER_RE.findall(text)
    return (len(letters) / len(nonspace)) < UNREADABLE_LETTER_RATIO


def _clean_heading(heading: str) -> str:
    return re.sub(r"\*+", "", heading).strip()


def _passage_id(document_id: str, start: int, end: int, text: str) -> str:
    digest = hashlib.sha256(f"{document_id}:{start}:{end}:{text}".encode("utf-8")).hexdigest()[:12]
    return f"{document_id}:{start}-{end}:{digest}"
