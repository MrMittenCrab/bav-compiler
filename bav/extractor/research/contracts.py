"""Typed preparation, inventory and retrieval contracts for research sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping

Representation = Literal["supplied_markdown", "converted_markdown"]
IssuerStatus = Literal["assigned", "uncertain", "unknown"]
PublicationDateStatus = Literal["known", "unknown"]
QueryPolarity = Literal["supporting", "contrary", "either"]
PassageKind = Literal["text", "table", "footnote"]
PreparationStatus = Literal["prepared", "reused", "capability_gap", "denied", "failed"]

OFFLINE_TEXT_LAYER_PROFILE = (
    "mode=fast,disable_ocr,output_format=markdown,HF_HUB_OFFLINE=1,TRANSFORMERS_OFFLINE=1"
)
DEFAULT_CONVERTER_TIMEOUT_SECONDS = 600
RECORDED_MARKER_EXECUTABLE = "/Users/lizhiguo/.venvs/marker/bin/marker_single"
RECORDED_MARKER_PACKAGE = "marker-pdf"
RECORDED_MARKER_VERSION = "2.0.0"

MARKET_TERMS = (
    "Japan",
    "Greater China",
    "China Mainland",
    "PRC",
    "Rest of World",
)


@dataclass(frozen=True)
class ConverterProfile:
    executable: str
    package: str
    package_version: str
    profile: str = OFFLINE_TEXT_LAYER_PROFILE
    timeout_seconds: int = DEFAULT_CONVERTER_TIMEOUT_SECONDS
    ocr: bool = False
    llm_enrichment: bool = False

    @property
    def profile_id(self) -> str:
        return (
            f"{self.package}:{self.package_version}:"
            f"{self.profile}:ocr={self.ocr}:llm={self.llm_enrichment}"
        )


@dataclass(frozen=True)
class PreparationRequest:
    source_path: Path
    company_slug: str | None = None
    document_id: str | None = None
    case_slug: str | None = None
    issuer: str | None = None
    document_type: str | None = None
    period_end: str | None = None
    publication_date: str | None = None
    original_filename: str | None = None
    allow_conversion: bool = True


@dataclass(frozen=True)
class PreparedBundle:
    document_id: str
    company_slug: str | None
    case_slug: str | None
    bundle_dir: Path
    original_filename: str
    original_sha256: str
    prepared_sha256: str
    converter_profile_id: str | None
    representation: Representation
    status: PreparationStatus
    reused: bool
    case_local: bool
    limitations: tuple[str, ...]
    publication_date: str | None
    publication_date_status: PublicationDateStatus
    issuer_status: IssuerStatus
    lineage: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConversionAttempt:
    command: tuple[str, ...]
    env: Mapping[str, str]
    timeout_seconds: int
    exit_code: int | None
    elapsed_seconds: float
    stdout: str
    stderr: str
    timed_out: bool
    capability_gap: str | None = None


@dataclass(frozen=True)
class Passage:
    passage_id: str
    document_id: str
    heading: str
    text: str
    context: str
    start_line: int
    end_line: int
    start_offset: int
    end_offset: int
    kind: PassageKind
    table: Mapping[str, Any] | None
    physical_pdf_page: int | None
    printed_page_label: str | None
    limitations: tuple[str, ...]
    source_fingerprint: str
    representation_fingerprint: str


@dataclass(frozen=True)
class InventoryRecord:
    document_id: str
    company_slug: str | None
    case_local: bool
    original_filename: str
    original_sha256: str
    prepared_sha256: str
    converter_profile_id: str | None
    representation: Representation
    publication_date_status: PublicationDateStatus
    issuer_status: IssuerStatus
    limitations: tuple[str, ...]
    bundle_dir: Path


@dataclass(frozen=True)
class SnapshotInventory:
    snapshot_id: str
    snapshot_fingerprint: str
    records: tuple[InventoryRecord, ...]
    coverage_gaps: tuple[str, ...]


@dataclass(frozen=True)
class CorpusQuery:
    query_id: str
    text: str
    polarity: QueryPolarity
    markets: tuple[str, ...]
    snapshot_id: str


@dataclass(frozen=True)
class RetrievalHit:
    passage: Passage
    score: int
    polarity: QueryPolarity
    candidate_only: bool = True


@dataclass(frozen=True)
class RetrievalResult:
    query: CorpusQuery
    snapshot_fingerprint: str
    result_key: str
    hits: tuple[RetrievalHit, ...]
    sources_checked: tuple[str, ...]
    coverage_gaps: tuple[str, ...]
    reused: bool
    stale: bool
