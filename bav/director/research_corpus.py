"""Director application entry for approved research-source preparation and retrieval.

No reasoning provider is invoked. Company names and benchmark queries live in
configuration and fixtures, not in retrieval scoring.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bav.director.current_build import PROJECTS, resolve_company
from bav.director.repository import repository_root
from bav.extractor.research.adapter import inspect_installed_converter
from bav.extractor.research.contracts import CorpusQuery, PreparationRequest, PreparedBundle, RetrievalResult, SnapshotInventory
from bav.extractor.research.prepare import prepare_source
from bav.extractor.research.retrieve import query_snapshot
from bav.extractor.research.snapshot import DEFAULT_SNAPSHOT_ID, load_snapshot_inventory

QUERY_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "extractor"
    / "research"
    / "fixtures"
    / "asia_benchmark_queries.json"
)


def configured_company_slugs() -> tuple[str, ...]:
    return tuple(item[1] for item in PROJECTS)


def load_benchmark_queries(*, path: Path | None = None) -> dict[str, Any]:
    target = path or QUERY_FIXTURE
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "queries" not in payload:
        raise ValueError("benchmark query fixture must be an object with queries")
    return payload


def prepare_approved_source(
    request: PreparationRequest,
    *,
    input_root: Path | None = None,
    repository: Path | None = None,
    converter=None,
) -> PreparedBundle:
    root = repository or repository_root()
    if request.company_slug:
        resolve_company(request.company_slug)
    return prepare_source(
        request,
        input_root=input_root or (root / "build" / "input"),
        converter=inspect_installed_converter() if converter is None else converter,
    )


def inventory_approved_snapshot(
    snapshot_id: str = DEFAULT_SNAPSHOT_ID,
    *,
    input_root: Path | None = None,
    repository: Path | None = None,
) -> SnapshotInventory:
    root = repository or repository_root()
    return load_snapshot_inventory(
        snapshot_id,
        input_root=input_root or (root / "build" / "input"),
        repository=root,
    )


def query_approved_corpus(
    query: CorpusQuery,
    *,
    input_root: Path | None = None,
    repository: Path | None = None,
    cache_dir: Path | None = None,
    previous_snapshot_fingerprint: str | None = None,
) -> RetrievalResult:
    inventory = inventory_approved_snapshot(
        query.snapshot_id,
        input_root=input_root,
        repository=repository,
    )
    root = repository or repository_root()
    resolved_input = input_root or (root / "build" / "input")
    cache = cache_dir or (
        resolved_input / "research_snapshots" / query.snapshot_id / "retrieval_cache"
    )
    return query_snapshot(
        inventory,
        query,
        cache_dir=cache,
        previous_snapshot_fingerprint=previous_snapshot_fingerprint,
    )


def configured_corpus_queries() -> tuple[CorpusQuery, ...]:
    payload = load_benchmark_queries()
    snapshot_id = str(payload.get("snapshot_id") or DEFAULT_SNAPSHOT_ID)
    queries = []
    for item in payload.get("queries") or ():
        queries.append(
            CorpusQuery(
                query_id=str(item["id"]),
                text=str(item["text"]),
                polarity=item.get("polarity") or "either",
                markets=tuple(item.get("markets") or ()),
                snapshot_id=snapshot_id,
            )
        )
    return tuple(queries)
