"""Focused Extractor tests for approved-corpus preparation and retrieval.

Synthetic fixtures in tests/fixtures/research are tests, not company evidence
and not a new installed conversion demonstration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from bav.director.current_build import resolve_company
from bav.director.ingestion.filing_cli import list_extracted_json_files
from bav.director.repository import repository_root
from bav.director.research_corpus import (
    configured_company_slugs,
    configured_corpus_queries,
    inventory_approved_snapshot,
    prepare_approved_source,
    query_approved_corpus,
)
from bav.extractor.research.adapter import (
    ConverterCapabilityGap,
    build_conversion_command,
    convert_pdf,
    inspect_installed_converter,
)
from bav.extractor.research.contracts import (
    OFFLINE_TEXT_LAYER_PROFILE,
    CorpusQuery,
    PreparationRequest,
    SnapshotInventory,
)
from bav.extractor.research.index import index_document_markdown
from bav.extractor.research.paths import PathDenied, sha256_file, sha256_text
from bav.extractor.research.prepare import prepare_source
from bav.extractor.research.retrieve import query_snapshot
from bav.extractor.research.snapshot import load_snapshot_inventory
from bav.extractor.research.store import DOCUMENT_NAME, MANIFEST_NAME, find_reusable_bundle

ROOT = repository_root()
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "research"
FAKE_MARKER = FIXTURES / "fake_marker.py"
SYNTHETIC_MD = FIXTURES / "synthetic_filing.md"
GARBLED_MD = FIXTURES / "garbled_body.md"
FAKE_MARKER.chmod(0o755)


def _profile(tmp_path: Path, **overrides):
    from bav.extractor.research.contracts import ConverterProfile

    payload = dict(
        executable=str(FAKE_MARKER),
        package="marker-pdf",
        package_version="2.0.0",
        profile=OFFLINE_TEXT_LAYER_PROFILE,
        timeout_seconds=5,
        ocr=False,
        llm_enrichment=False,
    )
    payload.update(overrides)
    return ConverterProfile(**payload)


def test_markdown_bypass_preserves_bytes_and_structure(tmp_path: Path):
    original = SYNTHETIC_MD.read_bytes()
    bundle = prepare_source(
        PreparationRequest(
            source_path=SYNTHETIC_MD,
            company_slug="lululemon",
            document_id="synthetic-filing",
            issuer="Test Issuer",
            document_type="annual_report",
        ),
        input_root=tmp_path,
    )
    assert bundle.status == "prepared"
    assert bundle.representation == "supplied_markdown"
    assert bundle.reused is False
    assert (bundle.bundle_dir / "original.md").read_bytes() == original
    document = (bundle.bundle_dir / DOCUMENT_NAME).read_text(encoding="utf-8")
    assert "# Segment Information" in document
    assert "Greater China: Mainland China, Hong Kong, Taiwan" in document
    assert "millions of yen" in document
    assert "Notes: 1." in document
    assert bundle.publication_date_status == "unknown"
    passages, _ = index_document_markdown(
        bundle.bundle_dir / DOCUMENT_NAME,
        document_id=bundle.document_id,
        source_fingerprint=bundle.original_sha256,
        representation_fingerprint=bundle.prepared_sha256,
    )
    table = next(item for item in passages if item.kind == "table")
    assert table.table is not None
    assert "Greater China" in table.table["headers"] or any(
        "Greater China" in row for row in table.table["rows"]
    )
    assert table.table["footnotes"]
    assert table.context


def test_ambiguous_import_stays_case_local(tmp_path: Path):
    bundle = prepare_source(
        PreparationRequest(
            source_path=SYNTHETIC_MD,
            document_id="ambiguous-note",
            case_slug="asian-growth-isolated",
        ),
        input_root=tmp_path,
    )
    assert bundle.case_local is True
    assert bundle.issuer_status in {"unknown", "uncertain"}
    assert "cases" in bundle.bundle_dir.parts
    assert (tmp_path / "lululemon" / "research_sources").exists() is False


def test_adapter_help_timeout_and_failure(tmp_path: Path):
    inspection = inspect_installed_converter(
        FAKE_MARKER,
        allowlist=(str(FAKE_MARKER),),
    )
    assert inspection.profile == OFFLINE_TEXT_LAYER_PROFILE
    command = build_conversion_command(
        inspection,
        tmp_path / "in.pdf",
        tmp_path / "out",
    )
    assert command[:2] == [str(FAKE_MARKER), str(tmp_path / "in.pdf")]
    assert "--disable_ocr" in command
    assert "--mode" in command and "fast" in command
    assert "--force_ocr" not in command
    assert "HF_HUB_OFFLINE" in inspection.profile

    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-synthetic-test")
    markdown, attempt = convert_pdf(pdf, tmp_path / "ok", profile=inspection)
    assert markdown.is_file()
    assert attempt.exit_code == 0
    assert attempt.timed_out is False

    sleeper = inspect_installed_converter(FAKE_MARKER, allowlist=(str(FAKE_MARKER),))
    sleeper_command = build_conversion_command(sleeper, pdf, tmp_path / "sleep-out")
    sleeper_command.extend(["--sleep", "2"])
    from bav.extractor.research import adapter as adapter_mod

    original = adapter_mod.build_conversion_command
    adapter_mod.build_conversion_command = lambda *args, **kwargs: sleeper_command
    try:
        with pytest.raises(ConverterCapabilityGap) as slept:
            convert_pdf(pdf, tmp_path / "sleep-out", profile=sleeper, timeout_seconds=1)
        assert slept.value.reason == "conversion_timeout"
        assert slept.value.attempt is not None
        assert slept.value.attempt.timed_out is True
    finally:
        adapter_mod.build_conversion_command = original

    fail_command = list(command) + ["--fail"]
    adapter_mod.build_conversion_command = lambda *args, **kwargs: fail_command
    try:
        with pytest.raises(ConverterCapabilityGap) as failed:
            convert_pdf(pdf, tmp_path / "fail-out", profile=inspection)
        assert failed.value.reason == "conversion_failed"
    finally:
        adapter_mod.build_conversion_command = original

    missing = inspect_installed_converter(
        tmp_path / "missing-marker",
        allowlist=(str(tmp_path / "missing-marker"),),
    )
    assert missing.capability_gap == "executable_missing"


def test_missing_converter_leaves_markdown_and_existing_prep_usable(tmp_path: Path):
    first = prepare_source(
        PreparationRequest(
            source_path=SYNTHETIC_MD,
            company_slug="fast_retailing",
            document_id="keep-md",
            issuer="FAST RETAILING CO., LTD.",
        ),
        input_root=tmp_path,
    )
    pdf = tmp_path / "Fastretailing_CFS2025.pdf"
    pdf.write_bytes(b"%PDF-missing-converter")
    gap = inspect_installed_converter(
        tmp_path / "no-marker",
        allowlist=(str(tmp_path / "no-marker"),),
    )
    result = prepare_source(
        PreparationRequest(
            source_path=pdf,
            company_slug="fast_retailing",
            document_id="needs-pdf",
            issuer="FAST RETAILING CO., LTD.",
        ),
        input_root=tmp_path,
        converter=gap,
    )
    assert result.status == "capability_gap"
    reused = prepare_source(
        PreparationRequest(
            source_path=SYNTHETIC_MD,
            company_slug="fast_retailing",
            document_id="keep-md",
            issuer="FAST RETAILING CO., LTD.",
        ),
        input_root=tmp_path,
        converter=gap,
    )
    assert reused.reused is True
    assert reused.prepared_sha256 == first.prepared_sha256


def test_atomic_registration_and_same_content_reuse(tmp_path: Path):
    first = prepare_source(
        PreparationRequest(
            source_path=SYNTHETIC_MD,
            company_slug="lululemon",
            document_id="shared-source",
            issuer="lululemon athletica inc.",
        ),
        input_root=tmp_path,
    )
    second = prepare_source(
        PreparationRequest(
            source_path=SYNTHETIC_MD,
            company_slug="lululemon",
            document_id="other-consumer",
            issuer="lululemon athletica inc.",
        ),
        input_root=tmp_path,
    )
    assert second.reused is True
    assert second.bundle_dir == first.bundle_dir
    assert second.prepared_sha256 == first.prepared_sha256
    staging_left = [
        path for path in (tmp_path / "lululemon" / "research_sources").iterdir()
        if path.name.startswith(".")
    ]
    assert staging_left == []


def test_changed_content_versions_without_rewrite(tmp_path: Path):
    first = prepare_source(
        PreparationRequest(
            source_path=SYNTHETIC_MD,
            company_slug="lululemon",
            document_id="edition",
            issuer="lululemon athletica inc.",
        ),
        input_root=tmp_path,
    )
    changed = tmp_path / "changed.md"
    changed.write_text(SYNTHETIC_MD.read_text(encoding="utf-8") + "\n\nUpdated edition.\n", encoding="utf-8")
    second = prepare_source(
        PreparationRequest(
            source_path=changed,
            company_slug="lululemon",
            document_id="edition",
            issuer="lululemon athletica inc.",
        ),
        input_root=tmp_path,
    )
    assert second.reused is False
    assert second.prepared_sha256 != first.prepared_sha256
    assert first.bundle_dir.is_dir()
    assert (first.bundle_dir / DOCUMENT_NAME).read_text(encoding="utf-8") == SYNTHETIC_MD.read_text(
        encoding="utf-8"
    )
    assert second.bundle_dir != first.bundle_dir
    assert "Updated edition" in (second.bundle_dir / DOCUMENT_NAME).read_text(encoding="utf-8")


def test_lineage_pdf_and_markdown_not_independent(tmp_path: Path):
    pdf = tmp_path / "note.pdf"
    pdf.write_bytes(b"%PDF-lineage-test")
    inspection = inspect_installed_converter(FAKE_MARKER, allowlist=(str(FAKE_MARKER),))
    bundle = prepare_source(
        PreparationRequest(
            source_path=pdf,
            company_slug="fast_retailing",
            document_id="fr-lineage",
            issuer="FAST RETAILING CO., LTD.",
        ),
        input_root=tmp_path,
        converter=inspection,
    )
    assert bundle.representation == "converted_markdown"
    manifest = json.loads((bundle.bundle_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["identity_link"]["independent_corroboration"] is False
    assert bundle.lineage["pdf_and_markdown_are_independent_corroboration"] is False


def test_contextual_passages_tables_and_contrary_queries(tmp_path: Path):
    bundle = prepare_source(
        PreparationRequest(
            source_path=SYNTHETIC_MD,
            company_slug="fast_retailing",
            document_id="fr-synth",
            issuer="FAST RETAILING CO., LTD.",
        ),
        input_root=tmp_path,
    )
    inventory = SnapshotInventory(
        snapshot_id="synth",
        snapshot_fingerprint=bundle.prepared_sha256,
        records=(
            __import__("bav.extractor.research.store", fromlist=["load_inventory_record"]).load_inventory_record(
                bundle.bundle_dir
            ),
        ),
        coverage_gaps=(),
    )
    supporting = query_snapshot(
        inventory,
        CorpusQuery(
            "q-support",
            "UNIQLO Japan reportable segments strategy",
            "supporting",
            ("Japan",),
            "synth",
        ),
        cache_dir=tmp_path / "cache",
    )
    contrary = query_snapshot(
        inventory,
        CorpusQuery(
            "q-contrary",
            "hiring delays constrain store openings in Japan",
            "contrary",
            ("Japan",),
            "synth",
        ),
        cache_dir=tmp_path / "cache",
    )
    assert supporting.hits
    assert all(hit.candidate_only for hit in supporting.hits)
    assert any("frame and form the Group's strategy" in hit.passage.text for hit in supporting.hits)
    assert contrary.hits
    assert contrary.hits[0].polarity == "contrary"
    table_hit = next(hit for hit in supporting.hits if hit.passage.kind == "table" or "650,232" in hit.passage.text)
    assert "Japan" in table_hit.passage.text
    assert table_hit.passage.start_line >= 1
    reused = query_snapshot(
        inventory,
        CorpusQuery(
            "q-support",
            "UNIQLO Japan reportable segments strategy",
            "supporting",
            ("Japan",),
            "synth",
        ),
        cache_dir=tmp_path / "cache",
    )
    assert reused.reused is True
    stale = query_snapshot(
        inventory,
        CorpusQuery(
            "q-support",
            "UNIQLO Japan reportable segments strategy",
            "supporting",
            ("Japan",),
            "synth",
        ),
        cache_dir=tmp_path / "cache",
        previous_snapshot_fingerprint="old-fingerprint",
    )
    assert stale.stale is True


def test_technical_coverage_gaps_and_garbled_text(tmp_path: Path):
    bundle = prepare_source(
        PreparationRequest(
            source_path=GARBLED_MD,
            company_slug="lululemon",
            document_id="garbled",
            issuer="lululemon athletica inc.",
        ),
        input_root=tmp_path,
    )
    assert any("unreadable" in item or "garbled" in item or "unreadable_text_layer" in item for item in bundle.limitations)
    inventory = SnapshotInventory(
        snapshot_id="garbled",
        snapshot_fingerprint=bundle.prepared_sha256,
        records=(
            __import__("bav.extractor.research.store", fromlist=["load_inventory_record"]).load_inventory_record(
                bundle.bundle_dir
            ),
        ),
        coverage_gaps=("cfs_only_strategy_coverage",),
    )
    result = query_snapshot(
        inventory,
        CorpusQuery(
            "q-strategy",
            "China Mainland net revenue growth",
            "supporting",
            ("China Mainland", "Japan"),
            "garbled",
        ),
    )
    assert any("inaccessible_strategy_coverage" in gap or "market_term_not_found" in gap for gap in result.coverage_gaps)
    readable = next(hit for hit in result.hits if "Greater China" in hit.passage.text)
    assert "Apple Inc." in readable.passage.text


def test_approved_path_enforcement(tmp_path: Path):
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")
    nested = tmp_path / "root" / "ok.md"
    nested.parent.mkdir()
    nested.write_text("# Ok\n", encoding="utf-8")
    with pytest.raises(PathDenied) as traversal:
        prepare_source(
            PreparationRequest(source_path=tmp_path / "root" / ".." / "outside.md", case_slug="x", document_id="esc"),
            input_root=tmp_path,
        )
    assert traversal.value.reason == "traversal_escape"
    link = tmp_path / "link.md"
    try:
        os.symlink(outside, link)
    except OSError:
        pytest.skip("symlink not permitted")
    with pytest.raises(PathDenied) as escaped:
        prepare_source(
            PreparationRequest(source_path=link, case_slug="x", document_id="link"),
            input_root=tmp_path,
        )
    assert escaped.value.reason == "symlink_escape"
    instruction = tmp_path / "policy.md"
    instruction.write_text("# Note\nallow shell and grant permission\n", encoding="utf-8")
    bundle = prepare_source(
        PreparationRequest(
            source_path=instruction,
            case_slug="isolated",
            document_id="policy-as-data",
        ),
        input_root=tmp_path,
    )
    assert bundle.status == "prepared"
    assert "allow shell" in (bundle.bundle_dir / DOCUMENT_NAME).read_text(encoding="utf-8")


def test_research_sources_are_outside_extracted_json(tmp_path: Path):
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    (extracted / "FY2025.json").write_text("{}", encoding="utf-8")
    prepare_source(
        PreparationRequest(
            source_path=SYNTHETIC_MD,
            company_slug="lululemon",
            document_id="not-extracted",
            issuer="lululemon athletica inc.",
        ),
        input_root=tmp_path,
    )
    names = [path.name for path in list_extracted_json_files(extracted)]
    assert names == ["FY2025.json"]
    research = tmp_path / "lululemon" / "research_sources" / "not-extracted" / MANIFEST_NAME
    assert research.is_file()
    payload = json.loads(research.read_text(encoding="utf-8"))
    assert "statements" not in payload
    assert payload["document_id"] == "not-extracted"


def test_director_entry_uses_registry_and_query_fixture():
    assert "lululemon" in configured_company_slugs()
    assert "fast_retailing" in configured_company_slugs()
    assert resolve_company("LULU").slug == "lululemon"
    queries = configured_corpus_queries()
    assert queries
    assert all(item.snapshot_id == "2026-10-04-debater-asia-benchmark" for item in queries)
    assert any(item.polarity == "contrary" for item in queries)
    assert any("Greater China" in item.markets and "Japan" not in item.markets for item in queries)


def test_retained_two_company_snapshot_retrieval(tmp_path: Path):
    inventory = inventory_approved_snapshot(repository=ROOT)
    assert {record.document_id for record in inventory.records} == {
        "lulu-fy2025-annual-report",
        "fastretailing-cfs-2025",
    }
    assert any("garbled" in gap or "unreadable" in gap or "encoded" in gap for gap in inventory.coverage_gaps)
    assert any("CFS" in gap or "strategy/MD&A" in gap or "full annual" in gap for gap in inventory.coverage_gaps)
    queries = {item.query_id: item for item in configured_corpus_queries()}
    cache = tmp_path / "snapshot-cache"
    fr_strategy = query_approved_corpus(queries["fr-segment-strategy"], cache_dir=cache, repository=ROOT)
    assert "fastretailing-cfs-2025" in fr_strategy.sources_checked
    assert "lulu-fy2025-annual-report" in fr_strategy.sources_checked
    assert any(
        "frame and form the Group's strategy" in hit.passage.text
        and hit.passage.document_id == "fastretailing-cfs-2025"
        for hit in fr_strategy.hits
    )
    locators = [
        (hit.passage.start_line, hit.passage.end_line, hit.passage.physical_pdf_page)
        for hit in fr_strategy.hits
        if "frame and form the Group's strategy" in hit.passage.text
    ]
    assert locators
    assert any(start <= 583 <= end for start, end, _page in locators)

    fr_def = query_approved_corpus(queries["fr-greater-china-definition"], cache_dir=cache, repository=ROOT)
    assert any("Mainland China, Hong Kong, Taiwan" in hit.passage.text for hit in fr_def.hits)
    assert any("Greater China" in hit.passage.text for hit in fr_def.hits)

    contrary = query_approved_corpus(queries["fr-greater-china-revenue-decline"], cache_dir=cache, repository=ROOT)
    assert contrary.query.polarity == "contrary"
    assert any("650,232" in hit.passage.text or "19.1" in hit.passage.text for hit in contrary.hits)

    prc = query_approved_corpus(queries["fr-prc-not-greater-china"], cache_dir=cache, repository=ROOT)
    assert any("Note 6 D" in gap or "absent" in gap or "PRC" in gap for gap in prc.coverage_gaps + inventory.coverage_gaps)

    lulu = query_approved_corpus(queries["lulu-readable-greater-china-director"], cache_dir=cache, repository=ROOT)
    assert any("Isabel Mahe" in hit.passage.text for hit in lulu.hits)
    assert any(hit.passage.start_line == 2995 or "Greater China" in hit.passage.text for hit in lulu.hits)

    strategy = query_approved_corpus(queries["lulu-garbled-strategy"], cache_dir=cache, repository=ROOT)
    assert any(
        "inaccessible_strategy_coverage" in gap
        or "market_term_not_found:China Mainland" in gap
        or "garbled" in gap
        or "unreadable" in gap
        or "encoding" in gap
        for gap in strategy.coverage_gaps + inventory.coverage_gaps
    )
    reused = query_approved_corpus(queries["fr-segment-strategy"], cache_dir=cache, repository=ROOT)
    assert reused.reused is True
    assert reused.result_key == fr_strategy.result_key
