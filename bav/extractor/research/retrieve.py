"""Deterministic lexical and heading retrieval over an approved snapshot."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from bav.extractor.research.contracts import (
    CorpusQuery,
    InventoryRecord,
    Passage,
    RetrievalHit,
    RetrievalResult,
    SnapshotInventory,
)
from bav.extractor.research.index import index_document_markdown, passage_to_dict
from bav.extractor.research.paths import sha256_text
from bav.extractor.research.store import DOCUMENT_NAME, verify_bundle_hashes

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9,%.'-]{1,}")
PHRASES = (
    "greater china",
    "china mainland",
    "rest of world",
    "uniqlo japan",
    "hong kong",
)


def result_key(query: CorpusQuery, snapshot_fingerprint: str) -> str:
    payload = f"{query.snapshot_id}|{query.query_id}|{query.text}|{query.polarity}|{','.join(query.markets)}|{snapshot_fingerprint}"
    return sha256_text(payload)


def query_snapshot(
    inventory: SnapshotInventory,
    query: CorpusQuery,
    *,
    cache_dir: Path | None = None,
    previous_snapshot_fingerprint: str | None = None,
) -> RetrievalResult:
    key = result_key(query, inventory.snapshot_fingerprint)
    stale = bool(
        previous_snapshot_fingerprint
        and previous_snapshot_fingerprint != inventory.snapshot_fingerprint
    )
    if cache_dir is not None:
        cached = cache_dir / f"{key}.json"
        if cached.is_file() and not stale:
            payload = json.loads(cached.read_text(encoding="utf-8"))
            if payload.get("snapshot_fingerprint") == inventory.snapshot_fingerprint:
                return _result_from_payload(payload, reused=True, stale=False)
    tokens = _tokens(query.text)
    hits: list[RetrievalHit] = []
    sources_checked: list[str] = []
    coverage = list(inventory.coverage_gaps)
    for record in inventory.records:
        sources_checked.append(record.document_id)
        ok, problems = verify_bundle_hashes(record.bundle_dir)
        if not ok:
            coverage.extend(f"{record.document_id}:{item}" for item in problems)
            continue
        passages = _passages_for(record)
        for passage in passages:
            score = _score(passage, tokens, query.markets)
            if score <= 0:
                continue
            hits.append(
                RetrievalHit(
                    passage=passage,
                    score=score,
                    polarity=query.polarity,
                    candidate_only=True,
                )
            )
        coverage.extend(_market_coverage(record, passages, query.markets))
    hits.sort(key=lambda item: (-item.score, item.passage.start_line, item.passage.passage_id))
    result = RetrievalResult(
        query=query,
        snapshot_fingerprint=inventory.snapshot_fingerprint,
        result_key=key,
        hits=tuple(hits),
        sources_checked=tuple(sources_checked),
        coverage_gaps=tuple(dict.fromkeys(coverage)),
        reused=False,
        stale=stale,
    )
    if cache_dir is not None and not stale:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"{key}.json").write_text(
            json.dumps(_result_to_payload(result), indent=2) + "\n",
            encoding="utf-8",
        )
    return result


def _passages_for(record: InventoryRecord) -> tuple[Passage, ...]:
    document = record.bundle_dir / DOCUMENT_NAME
    known_pages = _known_pages_from_existing(record.bundle_dir)
    passages, _limits = index_document_markdown(
        document,
        document_id=record.document_id,
        source_fingerprint=record.original_sha256,
        representation_fingerprint=record.prepared_sha256,
        known_pages=known_pages,
        existing_limitations=record.limitations,
    )
    return passages


def _known_pages_from_existing(bundle_dir: Path) -> dict[tuple[int, int], int]:
    path = bundle_dir / "passages.json"
    pages: dict[tuple[int, int], int] = {}
    if not path.is_file():
        return pages
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return pages
    for item in payload.get("passages") or []:
        locator = item.get("locator") or {}
        lines = locator.get("markdown_lines")
        page = locator.get("physical_pdf_page")
        if isinstance(lines, list) and len(lines) == 2 and isinstance(page, int):
            pages[(int(lines[0]), int(lines[1]))] = page
    return pages


def _tokens(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    phrases = [phrase for phrase in PHRASES if phrase in lowered]
    words = [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
    return tuple(dict.fromkeys([*phrases, *words]))


def _score(passage: Passage, tokens: tuple[str, ...], markets: tuple[str, ...]) -> int:
    hay_heading = passage.heading.lower()
    hay_text = passage.text.lower()
    score = 0
    for token in tokens:
        if len(token) < 2:
            continue
        if token in hay_heading:
            score += 6
        if token in hay_text:
            score += 2
    for market in markets:
        needle = market.lower()
        if needle and needle in hay_text:
            score += 3
    return score


def _market_coverage(
    record: InventoryRecord,
    passages: tuple[Passage, ...],
    markets: tuple[str, ...],
) -> tuple[str, ...]:
    gaps: list[str] = []
    joined = "\n".join(item.text for item in passages).lower()
    readable = any("unreadable_text_layer" not in item.limitations for item in passages)
    for market in markets:
        if market.lower() not in joined:
            if not readable:
                gaps.append(f"{record.document_id}:inaccessible_strategy_coverage:{market}")
            else:
                gaps.append(f"{record.document_id}:market_term_not_found:{market}")
    return tuple(gaps)


def _result_to_payload(result: RetrievalResult) -> dict:
    return {
        "query": {
            "query_id": result.query.query_id,
            "text": result.query.text,
            "polarity": result.query.polarity,
            "markets": list(result.query.markets),
            "snapshot_id": result.query.snapshot_id,
        },
        "snapshot_fingerprint": result.snapshot_fingerprint,
        "result_key": result.result_key,
        "hits": [
            {
                "score": hit.score,
                "polarity": hit.polarity,
                "candidate_only": hit.candidate_only,
                "passage": passage_to_dict(hit.passage),
            }
            for hit in result.hits
        ],
        "sources_checked": list(result.sources_checked),
        "coverage_gaps": list(result.coverage_gaps),
        "reused": result.reused,
        "stale": result.stale,
    }


def _result_from_payload(payload: dict, *, reused: bool, stale: bool) -> RetrievalResult:
    query_payload = payload["query"]
    query = CorpusQuery(
        query_id=query_payload["query_id"],
        text=query_payload["text"],
        polarity=query_payload["polarity"],
        markets=tuple(query_payload["markets"]),
        snapshot_id=query_payload["snapshot_id"],
    )
    hits = []
    for item in payload.get("hits") or []:
        passage_payload = item["passage"]
        locator = passage_payload.get("locator") or {}
        lines = locator.get("markdown_lines") or [0, 0]
        offsets = locator.get("offsets") or [0, 0]
        hits.append(
            RetrievalHit(
                passage=Passage(
                    passage_id=passage_payload["id"],
                    document_id=passage_payload["document_id"],
                    heading=passage_payload.get("heading") or "",
                    text=passage_payload.get("text") or "",
                    context=passage_payload.get("context") or "",
                    start_line=int(lines[0]),
                    end_line=int(lines[1]),
                    start_offset=int(offsets[0]),
                    end_offset=int(offsets[1]),
                    kind=passage_payload.get("kind") or "text",
                    table=passage_payload.get("table"),
                    physical_pdf_page=locator.get("physical_pdf_page"),
                    printed_page_label=locator.get("printed_page_label"),
                    limitations=tuple(passage_payload.get("limitations") or ()),
                    source_fingerprint=passage_payload.get("source_fingerprint") or "",
                    representation_fingerprint=passage_payload.get("representation_fingerprint") or "",
                ),
                score=int(item.get("score") or 0),
                polarity=item.get("polarity") or query.polarity,
                candidate_only=bool(item.get("candidate_only", True)),
            )
        )
    return RetrievalResult(
        query=query,
        snapshot_fingerprint=payload["snapshot_fingerprint"],
        result_key=payload["result_key"],
        hits=tuple(hits),
        sources_checked=tuple(payload.get("sources_checked") or ()),
        coverage_gaps=tuple(payload.get("coverage_gaps") or ()),
        reused=reused,
        stale=stale,
    )
