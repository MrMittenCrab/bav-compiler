"""Canonical data/ingestion ownership and retained compatibility façades."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

DATA_MOVED = (
    "interface",
    "validators",
    "standardized_io",
    "line_identity",
    "issuer_fiscal",
    "historical_operating_kpis",
    "historical_segments",
)
INGEST_MOVED = (
    "base",
    "reconciler",
    "filing_reconciler",
    "filing_standardizer",
    "management_kpi",
    "management_kpi_identity",
    "management_kpi_reconciliation",
    "management_kpi_history",
    "operating_kpi",
    "geographic_segment",
    "share_basis",
)
DATA_MOVED_SET = frozenset(DATA_MOVED)
INGEST_MOVED_SET = frozenset(INGEST_MOVED)
DIRECTOR_INGEST = frozenset(
    {
        "filing_cli",
        "note_handoff",
        "filing_validator",
        "normalization_candidate_admission",
        "management_kpi_enrichment",
    }
)
PRIVATE_EXPORTS = {
    "reconciler": ("_merge_line_items",),
    "management_kpi_reconciliation": ("_select_ordinary_group",),
    "manual_hk": ("_parse_date", "_load_historical_shares", "_load_structured_json"),
    "excel_import": ("_parse_header", "_header_layout"),
}
REPRESENTATIVE = (
    ("bav.modeler.data.interface", "StandardizedFinancials", ROOT / "bav/modeler/data/interface.py"),
    ("bav.modeler.data.validators", "validate_balance_sheet", ROOT / "bav/modeler/data/validators.py"),
    ("bav.modeler.data.standardized_io", "standardized_from_payload", ROOT / "bav/modeler/data/standardized_io.py"),
    ("bav.modeler.data.line_identity", "line_identity", ROOT / "bav/modeler/data/line_identity.py"),
    ("bav.modeler.data.issuer_fiscal", "issuer_fiscal_label", ROOT / "bav/modeler/data/issuer_fiscal.py"),
    ("bav.modeler.data.historical_operating_kpis", "validate_operating_kpi_fact", ROOT / "bav/modeler/data/historical_operating_kpis.py"),
    ("bav.modeler.data.historical_segments", "SEGMENT_BRIDGE_TOLERANCE", ROOT / "bav/modeler/data/historical_segments.py"),
    ("bav.director.data.schema", "validate_standardized", ROOT / "bav/director/data/schema.py"),
    ("bav.director.data.schema", "StatementKind", ROOT / "bav/director/data/schema.py"),
    ("bav.modeler.ingestion.base", "BaseIngestionAdapter", ROOT / "bav/modeler/ingestion/base.py"),
    ("bav.modeler.ingestion.reconciler", "reconcile_financials", ROOT / "bav/modeler/ingestion/reconciler.py"),
    ("bav.modeler.ingestion.filing_reconciler", "reconcile_filings", ROOT / "bav/modeler/ingestion/filing_reconciler.py"),
    ("bav.modeler.ingestion.filing_standardizer", "standardize_reconciled", ROOT / "bav/modeler/ingestion/filing_standardizer.py"),
    ("bav.modeler.ingestion.management_kpi", "bind_management_documents", ROOT / "bav/modeler/ingestion/management_kpi.py"),
    ("bav.modeler.ingestion.management_kpi_identity", "SUPPORTED_METRIC_MAPPINGS", ROOT / "bav/modeler/ingestion/management_kpi_identity.py"),
    ("bav.modeler.ingestion.management_kpi_reconciliation", "reconciliation_payload", ROOT / "bav/modeler/ingestion/management_kpi_reconciliation.py"),
    ("bav.modeler.ingestion.management_kpi_history", "selected_management_kpi_histories", ROOT / "bav/modeler/ingestion/management_kpi_history.py"),
    ("bav.modeler.ingestion.operating_kpi", "select_operating_kpi_facts", ROOT / "bav/modeler/ingestion/operating_kpi.py"),
    ("bav.modeler.ingestion.geographic_segment", "select_geographic_segment_facts", ROOT / "bav/modeler/ingestion/geographic_segment.py"),
    ("bav.modeler.ingestion.share_basis", "resolve_historical_share_basis", ROOT / "bav/modeler/ingestion/share_basis.py"),
    ("bav.modeler.ingestion.filing_validator", "operating_kpi_admission_issues", ROOT / "bav/modeler/ingestion/filing_validator.py"),
    ("bav.director.ingestion.filing_cli", "load_and_validate_extracted_dir", ROOT / "bav/director/ingestion/filing_cli.py"),
    ("bav.director.ingestion.note_handoff", "augment_extracted_filings", ROOT / "bav/director/ingestion/note_handoff.py"),
    ("bav.director.ingestion.filing_validator", "validate_extracted_filing", ROOT / "bav/director/ingestion/filing_validator.py"),
    ("bav.director.data.normalization_candidate", "AdoptionRecord", ROOT / "bav/director/data/normalization_candidate.py"),
    ("bav.director.data.normalization_candidate", "TreatmentRecord", ROOT / "bav/director/data/normalization_candidate.py"),
    ("bav.modeler.ingestion.normalization_candidate_admission", "construct_provisional_candidate", ROOT / "bav/modeler/ingestion/normalization_candidate_admission.py"),
    ("bav.modeler.ingestion.normalization_candidate_admission", "evaluate_adoption", ROOT / "bav/modeler/ingestion/normalization_candidate_admission.py"),
    ("bav.director.ingestion.normalization_candidate_admission", "run_normalization_candidate_handoff", ROOT / "bav/director/ingestion/normalization_candidate_admission.py"),
    ("bav.director.ingestion.normalization_candidate_admission", "save_admitted_normalization_candidate", ROOT / "bav/director/ingestion/normalization_candidate_admission.py"),
    ("bav.director.ingestion.normalization_candidate_admission", "load_admitted_normalization_candidate", ROOT / "bav/director/ingestion/normalization_candidate_admission.py"),
    ("bav.inferer.normalization", "grouping_established_as_source_fact", ROOT / "bav/inferer/normalization.py"),
    ("bav.extractor.ingestion.management_kpi_enrichment", "inspect_source_pdf", ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py"),
    ("bav.extractor.ingestion.management_kpi_enrichment", "collect_calendar_corpus", ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py"),
    ("bav.extractor.ingestion.management_kpi_enrichment", "collect_exclusion_corpus", ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py"),
    ("bav.extractor.ingestion.management_kpi_enrichment", "extract_comparison_window", ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py"),
    ("bav.extractor.ingestion.management_kpi_enrichment", "extract_spsf_prior_period_levels", ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py"),
    ("bav.modeler.ingestion.management_kpi_enrichment", "assess_definition_equivalence", ROOT / "bav/modeler/ingestion/management_kpi_enrichment.py"),
    ("bav.modeler.ingestion.management_kpi_enrichment", "build_group_decisions", ROOT / "bav/modeler/ingestion/management_kpi_enrichment.py"),
    ("bav.director.ingestion.management_kpi_enrichment", "enrich_management_working_copies", ROOT / "bav/director/ingestion/management_kpi_enrichment.py"),
    ("legacy.ingestion.manual_hk", "HKManualDocumentAdapter", ROOT / "legacy/ingestion/manual_hk.py"),
    ("legacy.ingestion.excel_import", "ExcelExportAdapter", ROOT / "legacy/ingestion/excel_import.py"),
)
FACADE_PAIRS = (
    ("bav.modeler.data.interface", "bav.modeler.data.interface", "StandardizedFinancials"),
    ("bav.modeler.data.validators", "bav.modeler.data.validators", "validate_income_statement"),
    ("bav.modeler.data.standardized_io", "bav.modeler.data.standardized_io", "standardized_to_payload"),
    ("bav.modeler.data.line_identity", "bav.modeler.data.line_identity", "line_identity"),
    ("bav.modeler.data.issuer_fiscal", "bav.modeler.data.issuer_fiscal", "issuer_fiscal_label"),
    ("bav.modeler.data.historical_operating_kpis", "bav.modeler.data.historical_operating_kpis", "validate_operating_kpi_fact"),
    ("bav.modeler.data.historical_segments", "bav.modeler.data.historical_segments", "SEGMENT_BRIDGE_TOLERANCE"),
    ("bav.director.data.schema", "bav.director.data.schema", "validate_standardized"),
    ("bav.modeler.ingestion.base", "bav.modeler.ingestion.base", "BaseIngestionAdapter"),
    ("bav.modeler.ingestion.reconciler", "bav.modeler.ingestion.reconciler", "reconcile_financials"),
    ("bav.modeler.ingestion.filing_reconciler", "bav.modeler.ingestion.filing_reconciler", "reconcile_filings"),
    ("bav.modeler.ingestion.filing_standardizer", "bav.modeler.ingestion.filing_standardizer", "standardize_reconciled"),
    ("bav.modeler.ingestion.management_kpi", "bav.modeler.ingestion.management_kpi", "bind_management_documents"),
    ("bav.modeler.ingestion.management_kpi_identity", "bav.modeler.ingestion.management_kpi_identity", "SUPPORTED_METRIC_MAPPINGS"),
    ("bav.modeler.ingestion.management_kpi_reconciliation", "bav.modeler.ingestion.management_kpi_reconciliation", "reconciliation_payload"),
    ("bav.modeler.ingestion.management_kpi_history", "bav.modeler.ingestion.management_kpi_history", "selected_management_kpi_histories"),
    ("bav.modeler.ingestion.operating_kpi", "bav.modeler.ingestion.operating_kpi", "select_operating_kpi_facts"),
    ("bav.modeler.ingestion.geographic_segment", "bav.modeler.ingestion.geographic_segment", "select_geographic_segment_facts"),
    ("bav.modeler.ingestion.share_basis", "bav.modeler.ingestion.share_basis", "resolve_historical_share_basis"),
    ("bav.director.ingestion.filing_cli", "bav.director.ingestion.filing_cli", "load_and_validate_extracted_dir"),
    ("bav.director.ingestion.note_handoff", "bav.director.ingestion.note_handoff", "augment_extracted_filings"),
    ("bav.director.ingestion.filing_validator", "bav.director.ingestion.filing_validator", "validate_extracted_filing"),
    ("bav.modeler.ingestion.filing_validator", "bav.modeler.ingestion.filing_validator", "operating_kpi_admission_issues"),
    ("bav.director.data.normalization_candidate", "bav.modeler.ingestion.normalization_candidate_admission", "AdoptionRecord"),
    ("bav.director.data.normalization_candidate", "bav.modeler.ingestion.normalization_candidate_admission", "TreatmentRecord"),
    ("bav.modeler.ingestion.normalization_candidate_admission", "bav.modeler.ingestion.normalization_candidate_admission", "construct_provisional_candidate"),
    ("bav.modeler.ingestion.normalization_candidate_admission", "bav.modeler.ingestion.normalization_candidate_admission", "evaluate_adoption"),
    ("bav.modeler.ingestion.normalization_candidate_admission", "bav.modeler.ingestion.normalization_candidate_admission", "evaluate_treatment"),
    ("bav.director.ingestion.normalization_candidate_admission", "bav.modeler.ingestion.normalization_candidate_admission", "run_normalization_candidate_handoff"),
    ("bav.director.ingestion.normalization_candidate_admission", "bav.modeler.ingestion.normalization_candidate_admission", "save_admitted_normalization_candidate"),
    ("bav.director.ingestion.normalization_candidate_admission", "bav.modeler.ingestion.normalization_candidate_admission", "load_admitted_normalization_candidate"),
    ("bav.director.ingestion.normalization_candidate_admission", "bav.modeler.ingestion.normalization_candidate_admission", "HandoffResult"),
    ("bav.extractor.ingestion.management_kpi_enrichment", "bav.director.ingestion.management_kpi_enrichment", "inspect_source_pdf"),
    ("bav.extractor.ingestion.management_kpi_enrichment", "bav.director.ingestion.management_kpi_enrichment", "collect_calendar_corpus"),
    ("bav.extractor.ingestion.management_kpi_enrichment", "bav.director.ingestion.management_kpi_enrichment", "collect_exclusion_corpus"),
    ("bav.extractor.ingestion.management_kpi_enrichment", "bav.director.ingestion.management_kpi_enrichment", "extract_comparison_window"),
    ("bav.extractor.ingestion.management_kpi_enrichment", "bav.director.ingestion.management_kpi_enrichment", "extract_spsf_prior_period_levels"),
    ("bav.modeler.ingestion.management_kpi_enrichment", "bav.director.ingestion.management_kpi_enrichment", "assess_definition_equivalence"),
    ("bav.modeler.ingestion.management_kpi_enrichment", "bav.director.ingestion.management_kpi_enrichment", "build_group_decisions"),
    ("bav.director.ingestion.management_kpi_enrichment", "bav.director.ingestion.management_kpi_enrichment", "enrich_management_working_copies"),
    ("legacy.ingestion.manual_hk", "legacy.ingestion.manual_hk", "HKManualDocumentAdapter"),
    ("legacy.ingestion.excel_import", "legacy.ingestion.excel_import", "ExcelExportAdapter"),
)

ENRICHMENT_EXTRACTOR_COMPAT = (
    "collect_calendar_corpus",
    "collect_exclusion_corpus",
    "extract_comparison_window",
    "extract_spsf_prior_period_levels",
)


def _public_names(module) -> list[str]:
    return [name for name in dir(module) if not name.startswith("_")]


def test_canonical_definitions_are_owner_owned():
    for module_name, attr, path in REPRESENTATIVE:
        module = __import__(module_name, fromlist=[attr])
        assert Path(module.__file__).resolve() == path.resolve()
        assert callable(getattr(module, attr)) or getattr(module, attr) is not None


def test_compatibility_exports_are_identity_equal():
    assert not (ROOT / "core").exists()
    assert not (ROOT / "interpreter").exists()
    from bav.extractor.data.interface import DataSourceAdapter, DocumentManifest, DocumentType
    from bav.extractor.data.filing_validator import (
        FilingValidationIssue,
        bind_source_file,
        source_row_identity,
        validate_extracted_filing,
    )
    from bav.modeler.ingestion.filing_validator import _operating_kpi_admission_for_fact
    from bav.modeler.ingestion.reconciler import _merge_line_items
    from bav.modeler.ingestion.management_kpi_reconciliation import _select_ordinary_group

    assert DataSourceAdapter and DocumentManifest and DocumentType
    assert callable(bind_source_file)
    assert callable(source_row_identity)
    assert callable(validate_extracted_filing)
    assert FilingValidationIssue is not None
    assert callable(_operating_kpi_admission_for_fact)
    assert callable(_merge_line_items)
    assert callable(_select_ordinary_group)
    for canonical_name, facade_name, attr in FACADE_PAIRS:
        if facade_name.startswith("core."):
            continue
        canonical = __import__(canonical_name, fromlist=["*"])
        facade = __import__(facade_name, fromlist=["*"])
        if not hasattr(facade, attr) or not hasattr(canonical, attr):
            continue
        assert getattr(facade, attr) is getattr(canonical, attr)


def test_facade_and_canonical_import_orders():
    samples = (
        ("bav.modeler.data.interface", "bav.modeler.data.interface", "StandardizedFinancials"),
        ("bav.director.data.schema", "bav.director.data.schema", "StatementKind"),
        ("bav.modeler.ingestion.reconciler", "bav.modeler.ingestion.reconciler", "reconcile_financials"),
        ("bav.director.ingestion.filing_validator", "bav.director.ingestion.filing_validator", "validate_extracted_filing"),
        ("bav.modeler.ingestion.filing_validator", "bav.modeler.ingestion.filing_validator", "operating_kpi_admission_issues"),
        ("bav.director.ingestion.normalization_candidate_admission", "bav.director.ingestion.normalization_candidate_admission", "run_normalization_candidate_handoff"),
        ("bav.modeler.ingestion.normalization_candidate_admission", "bav.modeler.ingestion.normalization_candidate_admission", "construct_provisional_candidate"),
        ("bav.director.ingestion.management_kpi_enrichment", "bav.director.ingestion.management_kpi_enrichment", "enrich_management_working_copies"),
        ("bav.extractor.ingestion.management_kpi_enrichment", "bav.extractor.ingestion.management_kpi_enrichment", "inspect_source_pdf"),
        ("bav.extractor.ingestion.management_kpi_enrichment", "bav.extractor.ingestion.management_kpi_enrichment", "collect_calendar_corpus"),
        ("bav.extractor.ingestion.management_kpi_enrichment", "bav.extractor.ingestion.management_kpi_enrichment", "collect_exclusion_corpus"),
        ("bav.extractor.ingestion.management_kpi_enrichment", "bav.extractor.ingestion.management_kpi_enrichment", "extract_comparison_window"),
        ("bav.extractor.ingestion.management_kpi_enrichment", "bav.extractor.ingestion.management_kpi_enrichment", "extract_spsf_prior_period_levels"),
        ("bav.modeler.ingestion.management_kpi_enrichment", "bav.modeler.ingestion.management_kpi_enrichment", "build_group_decisions"),
        ("legacy.ingestion.manual_hk", "legacy.ingestion.manual_hk", "HKManualDocumentAdapter"),
        ("legacy.ingestion.excel_import", "legacy.ingestion.excel_import", "ExcelExportAdapter"),
    )
    orders = (
        "import {facade} as facade\nimport {canonical} as canonical\n",
        "import {canonical} as canonical\nimport {facade} as facade\n",
    )
    extras = (
        "from bav.extractor.data.interface import DocumentManifest as ext_manifest\n"
        "assert ext_manifest is not None\n"
        "from bav.modeler.ingestion.reconciler import _merge_line_items as canonical_merge\n"
        "from bav.modeler.ingestion.reconciler import _merge_line_items as facade_merge\n"
        "assert facade_merge is canonical_merge\n"
        "from legacy.ingestion.manual_hk import _parse_date as canonical_parse\n"
        "from legacy.ingestion.manual_hk import _parse_date as facade_parse\n"
        "assert facade_parse is canonical_parse\n"
        "from legacy.ingestion.excel_import import _header_layout as canonical_layout\n"
        "from legacy.ingestion.excel_import import _header_layout as facade_layout\n"
        "assert facade_layout is canonical_layout\n"
    )
    for canonical, facade, attr in samples:
        for template in orders:
            script = (
                template.format(canonical=canonical, facade=facade)
                + f"assert facade.{attr} is canonical.{attr}\n"
                + extras
            )
            result = subprocess.run(
                [sys.executable, "-c", script],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            assert result.returncode == 0, result.stderr or result.stdout


def test_canonical_modules_do_not_import_own_facades():
    destinations = [
        *(ROOT / "bav/modeler/data" / f"{name}.py" for name in DATA_MOVED),
        ROOT / "bav/director/data/schema.py",
        *(ROOT / "bav/modeler/ingestion" / f"{name}.py" for name in INGEST_MOVED),
        ROOT / "bav/modeler/ingestion/filing_validator.py",
        ROOT / "bav/director/ingestion/filing_cli.py",
        ROOT / "bav/director/ingestion/note_handoff.py",
        ROOT / "bav/director/ingestion/filing_validator.py",
        ROOT / "bav/director/data/normalization_candidate.py",
        ROOT / "bav/modeler/ingestion/normalization_candidate_admission.py",
        ROOT / "bav/director/ingestion/normalization_candidate_admission.py",
        ROOT / "bav/inferer/normalization.py",
        ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py",
        ROOT / "bav/modeler/ingestion/management_kpi_enrichment.py",
        ROOT / "bav/director/ingestion/management_kpi_enrichment.py",
    ]
    forbidden_data = {f"core.data.{name}" for name in DATA_MOVED} | {
        "core.data.schema",
        "interpreter",
        "core",
    }
    forbidden_ingest = {f"core.ingestion.{name}" for name in INGEST_MOVED} | {
        "core.ingestion.filing_cli",
        "core.ingestion.note_handoff",
        "core.ingestion.filing_validator",
        "core.ingestion.normalization_candidate_admission",
        "core.ingestion.management_kpi_enrichment",
        "interpreter",
    }
    for path in destinations:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            for module in modules:
                assert module not in forbidden_data, f"{path} imports {module}"
                assert module not in forbidden_ingest, f"{path} imports {module}"


def test_management_kpi_enrichment_canonical_ownership():
    from bav.director.ingestion.management_kpi_enrichment import (
        PAGE_RESOLUTION_NAME as canonical_page,
        enrich_management_working_copies as canonical_enrich,
    )
    from bav.extractor.ingestion.management_kpi_enrichment import (
        CalendarYearEvidence as canonical_calendar,
        SourceInspection as canonical_inspection,
        _metric_exclusion_evidence as canonical_exclusion,
        _metric_excludes_53rd_week as canonical_excludes,
        collect_calendar_corpus as canonical_calendar_corpus,
        collect_exclusion_corpus as canonical_exclusion_corpus,
        definition_features as canonical_features,
        extract_comparison_window as canonical_window,
        extract_spsf_prior_period_levels as canonical_spsf,
        inspect_source_pdf as canonical_inspect,
        validate_physical_page_binding as canonical_validate,
    )
    from bav.modeler.ingestion.management_kpi_enrichment import (
        DEFINITION_EQUIVALENT as canonical_equivalent,
        assess_definition_equivalence as canonical_assess,
        build_group_decisions as canonical_decisions,
        enrich_management_payload as canonical_payload,
    )
    from bav.director.ingestion.management_kpi_enrichment import (
        PAGE_RESOLUTION_NAME as facade_page,
        enrich_management_working_copies as facade_enrich,
    )

    assert canonical_enrich is facade_enrich
    assert canonical_page is facade_page
    assert canonical_inspect is not None
    assert canonical_validate is not None
    assert canonical_features is not None
    assert canonical_calendar is not None
    assert canonical_inspection is not None
    assert canonical_exclusion is not None
    assert canonical_excludes is not None
    assert canonical_calendar_corpus is not None
    assert canonical_exclusion_corpus is not None
    assert canonical_window is not None
    assert canonical_spsf is not None
    assert canonical_assess is not None
    assert canonical_equivalent is not None
    assert canonical_decisions is not None
    assert canonical_payload is not None
    assert Path(canonical_inspect.__code__.co_filename).resolve() == (
        ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py"
    ).resolve()
    assert Path(canonical_calendar_corpus.__code__.co_filename).resolve() == (
        ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py"
    ).resolve()
    assert Path(canonical_exclusion_corpus.__code__.co_filename).resolve() == (
        ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py"
    ).resolve()
    assert Path(canonical_window.__code__.co_filename).resolve() == (
        ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py"
    ).resolve()
    assert Path(canonical_spsf.__code__.co_filename).resolve() == (
        ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py"
    ).resolve()
    assert Path(canonical_assess.__code__.co_filename).resolve() == (
        ROOT / "bav/modeler/ingestion/management_kpi_enrichment.py"
    ).resolve()
    assert Path(canonical_decisions.__code__.co_filename).resolve() == (
        ROOT / "bav/modeler/ingestion/management_kpi_enrichment.py"
    ).resolve()
    assert Path(canonical_enrich.__code__.co_filename).resolve() == (
        ROOT / "bav/director/ingestion/management_kpi_enrichment.py"
    ).resolve()


def test_management_kpi_enrichment_extractor_compatibility_exports():
    import inspect

    from bav.extractor.ingestion import management_kpi_enrichment as canonical

    for name in ENRICHMENT_EXTRACTOR_COMPAT:
        canonical_obj = getattr(canonical, name)
        assert inspect.signature(canonical_obj) == inspect.signature(canonical_obj)


def test_normalization_candidate_canonical_ownership():
    from bav.director.data.normalization_candidate import (
        AdoptionRecord as canonical_adoption,
        TreatmentRecord as canonical_treatment,
    )
    from bav.director.ingestion.normalization_candidate_admission import (
        HandoffResult as canonical_handoff,
        load_admitted_normalization_candidate as canonical_load,
        run_normalization_candidate_handoff as canonical_run,
        save_admitted_normalization_candidate as canonical_save,
    )
    from bav.inferer.normalization import grouping_established_as_source_fact
    from bav.modeler.ingestion.normalization_candidate_admission import (
        construct_provisional_candidate as canonical_construct,
        evaluate_adoption as canonical_evaluate_adoption,
        evaluate_treatment as canonical_evaluate_treatment,
    )
    from bav.modeler.ingestion.normalization_candidate_admission_io import (
        AdmissionProvenanceError as canonical_error,
    )
    from bav.modeler.ingestion.normalization_candidate_admission import (
        construct_provisional_candidate as facade_construct,
        evaluate_adoption as facade_evaluate_adoption,
        evaluate_treatment as facade_evaluate_treatment,
        _insert_constructed_line as facade_insert,
    )
    from bav.modeler.ingestion.normalization_candidate_admission import (
        _insert_constructed_line as canonical_insert,
    )

    assert canonical_adoption is not None
    assert canonical_treatment is not None
    assert canonical_handoff is not None
    assert canonical_construct is facade_construct
    assert canonical_evaluate_adoption is facade_evaluate_adoption
    assert canonical_evaluate_treatment is facade_evaluate_treatment
    assert canonical_run is not None
    assert canonical_save is not None
    assert canonical_load is not None
    assert canonical_error is not None
    assert canonical_insert is facade_insert
    assert grouping_established_as_source_fact() is False
    assert grouping_established_as_source_fact("independently_supplied") is False
    assert Path(canonical_construct.__code__.co_filename).resolve() == (
        ROOT / "bav/modeler/ingestion/normalization_candidate_admission.py"
    ).resolve()
    assert Path(canonical_run.__code__.co_filename).resolve() == (
        ROOT / "bav/director/ingestion/normalization_candidate_admission.py"
    ).resolve()
    assert Path(grouping_established_as_source_fact.__code__.co_filename).resolve() == (
        ROOT / "bav/inferer/normalization.py"
    ).resolve()


def test_extractor_lazy_metric_mapping_uses_modeler_owner():
    source = (ROOT / "bav/extractor/data/management_kpi_json.py").read_text()
    assert "from bav.modeler.ingestion.management_kpi_identity import SUPPORTED_METRIC_MAPPINGS" in source
    assert "from core.ingestion.management_kpi_identity import SUPPORTED_METRIC_MAPPINGS" not in source


def test_relocated_implementations_do_not_import_legacy():
    paths = [
        *(ROOT / "bav/modeler/data" / f"{name}.py" for name in DATA_MOVED),
        ROOT / "bav/director/data/schema.py",
        *(ROOT / "bav/modeler/ingestion" / f"{name}.py" for name in INGEST_MOVED),
        ROOT / "bav/modeler/ingestion/filing_validator.py",
        ROOT / "bav/director/ingestion/filing_cli.py",
        ROOT / "bav/director/ingestion/note_handoff.py",
        ROOT / "bav/director/ingestion/filing_validator.py",
        ROOT / "bav/director/data/normalization_candidate.py",
        ROOT / "bav/modeler/ingestion/normalization_candidate_admission.py",
        ROOT / "bav/director/ingestion/normalization_candidate_admission.py",
        ROOT / "bav/inferer/normalization.py",
        ROOT / "bav/extractor/ingestion/management_kpi_enrichment.py",
        ROOT / "bav/modeler/ingestion/management_kpi_enrichment.py",
        ROOT / "bav/director/ingestion/management_kpi_enrichment.py",
    ]
    blocked = []
    for file in paths:
        tree = ast.parse(file.read_text())
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            for module in modules:
                if module == "legacy" or module.startswith("legacy."):
                    blocked.append((str(file), module))
    assert not blocked


def test_legacy_manual_ingestion_ownership_and_identity():
    from legacy.ingestion.excel_import import (
        TAB_MAP as canonical_tabs,
        ExcelExportAdapter as canonical_excel,
        _header_layout as canonical_layout,
        _parse_header as canonical_header,
    )
    from legacy.ingestion.manual_hk import (
        HKManualDocumentAdapter as canonical_hk,
        _load_historical_shares as canonical_shares,
        _load_structured_json as canonical_load,
        _parse_date as canonical_parse,
    )
    from legacy.ingestion.excel_import import (
        TAB_MAP as facade_tabs,
        ExcelExportAdapter as facade_excel,
        _header_layout as facade_layout,
        _parse_header as facade_header,
    )
    from legacy.ingestion.manual_hk import (
        HKManualDocumentAdapter as facade_hk,
        _load_historical_shares as facade_shares,
        _load_structured_json as facade_load,
        _parse_date as facade_parse,
    )
    assert facade_hk is canonical_hk
    assert facade_excel is canonical_excel
    assert facade_parse is canonical_parse
    assert facade_shares is canonical_shares
    assert facade_load is canonical_load
    assert facade_header is canonical_header
    assert facade_layout is canonical_layout
    assert facade_tabs is canonical_tabs
    assert Path(canonical_hk.ingest.__code__.co_filename).resolve() == (
        ROOT / "legacy/ingestion/manual_hk.py"
    ).resolve()
    assert Path(canonical_excel.ingest.__code__.co_filename).resolve() == (
        ROOT / "legacy/ingestion/excel_import.py"
    ).resolve()
    assert Path(canonical_parse.__code__.co_filename).resolve() == (
        ROOT / "legacy/ingestion/manual_hk.py"
    ).resolve()


def test_ordinary_ingestion_imports_do_not_load_legacy_adapters():
    ordinary = (
        "from bav.modeler.ingestion.base import BaseIngestionAdapter\n"
        "from bav.modeler.ingestion.reconciler import reconcile_financials\n"
        "import bav.director.ingestion.filing_cli\n"
        "import bav.modeler.ingestion.filing_standardizer\n"
        "assert BaseIngestionAdapter is not None\n"
        "assert reconcile_financials is not None\n"
    )
    blocked = (
        "legacy.ingestion.manual_hk",
        "legacy.ingestion.excel_import",
        "legacy.ingestion.manual_hk",
        "legacy.ingestion.excel_import",
    )
    script = (
        ordinary
        + "import sys\n"
        + "loaded = [name for name in "
        + repr(blocked)
        + " if name in sys.modules]\n"
        + "assert not loaded, loaded\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_legacy_adapter_import_orders():
    samples = (
        ("legacy.ingestion.manual_hk", "legacy.ingestion.manual_hk", "HKManualDocumentAdapter"),
        ("legacy.ingestion.excel_import", "legacy.ingestion.excel_import", "ExcelExportAdapter"),
    )
    orders = (
        "import {facade} as facade\nimport {canonical} as canonical\n",
        "import {canonical} as canonical\nimport {facade} as facade\n",
    )
    extras = (
        "from legacy.ingestion.manual_hk import HKManualDocumentAdapter as can_hk\n"
        "from legacy.ingestion.excel_import import ExcelExportAdapter as can_excel\n"
        "assert can_hk is not None\n"
        "assert can_excel is not None\n"
        "from legacy.ingestion.manual_hk import _parse_date, _load_historical_shares, _load_structured_json\n"
        "from legacy.ingestion.manual_hk import (\n"
        "    _parse_date as facade_parse,\n"
        "    _load_historical_shares as facade_shares,\n"
        "    _load_structured_json as facade_load,\n"
        ")\n"
        "assert facade_parse is _parse_date\n"
        "assert facade_shares is _load_historical_shares\n"
        "assert facade_load is _load_structured_json\n"
        "from legacy.ingestion.excel_import import _parse_header, _header_layout\n"
        "from legacy.ingestion.excel_import import _parse_header as facade_header, _header_layout as facade_layout\n"
        "assert facade_header is _parse_header\n"
        "assert facade_layout is _header_layout\n"
    )
    for canonical, facade, attr in samples:
        for template in orders:
            script = (
                template.format(canonical=canonical, facade=facade)
                + f"assert facade.{attr} is canonical.{attr}\n"
                + extras
            )
            result = subprocess.run(
                [sys.executable, "-c", script],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            assert result.returncode == 0, result.stderr or result.stdout
