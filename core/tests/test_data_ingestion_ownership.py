"""Canonical data/ingestion ownership and retained compatibility façades."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

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
}
REPRESENTATIVE = (
    ("modeler.data.interface", "StandardizedFinancials", ROOT / "modeler/data/interface.py"),
    ("modeler.data.validators", "validate_balance_sheet", ROOT / "modeler/data/validators.py"),
    ("modeler.data.standardized_io", "standardized_from_payload", ROOT / "modeler/data/standardized_io.py"),
    ("modeler.data.line_identity", "line_identity", ROOT / "modeler/data/line_identity.py"),
    ("modeler.data.issuer_fiscal", "issuer_fiscal_label", ROOT / "modeler/data/issuer_fiscal.py"),
    ("modeler.data.historical_operating_kpis", "validate_operating_kpi_fact", ROOT / "modeler/data/historical_operating_kpis.py"),
    ("modeler.data.historical_segments", "SEGMENT_BRIDGE_TOLERANCE", ROOT / "modeler/data/historical_segments.py"),
    ("director.data.schema", "validate_standardized", ROOT / "director/data/schema.py"),
    ("director.data.schema", "StatementKind", ROOT / "director/data/schema.py"),
    ("modeler.ingestion.base", "BaseIngestionAdapter", ROOT / "modeler/ingestion/base.py"),
    ("modeler.ingestion.reconciler", "reconcile_financials", ROOT / "modeler/ingestion/reconciler.py"),
    ("modeler.ingestion.filing_reconciler", "reconcile_filings", ROOT / "modeler/ingestion/filing_reconciler.py"),
    ("modeler.ingestion.filing_standardizer", "standardize_reconciled", ROOT / "modeler/ingestion/filing_standardizer.py"),
    ("modeler.ingestion.management_kpi", "bind_management_documents", ROOT / "modeler/ingestion/management_kpi.py"),
    ("modeler.ingestion.management_kpi_identity", "SUPPORTED_METRIC_MAPPINGS", ROOT / "modeler/ingestion/management_kpi_identity.py"),
    ("modeler.ingestion.management_kpi_reconciliation", "reconciliation_payload", ROOT / "modeler/ingestion/management_kpi_reconciliation.py"),
    ("modeler.ingestion.management_kpi_history", "selected_management_kpi_histories", ROOT / "modeler/ingestion/management_kpi_history.py"),
    ("modeler.ingestion.operating_kpi", "select_operating_kpi_facts", ROOT / "modeler/ingestion/operating_kpi.py"),
    ("modeler.ingestion.geographic_segment", "select_geographic_segment_facts", ROOT / "modeler/ingestion/geographic_segment.py"),
    ("modeler.ingestion.share_basis", "resolve_historical_share_basis", ROOT / "modeler/ingestion/share_basis.py"),
    ("modeler.ingestion.filing_validator", "operating_kpi_admission_issues", ROOT / "modeler/ingestion/filing_validator.py"),
    ("director.ingestion.filing_cli", "load_and_validate_extracted_dir", ROOT / "director/ingestion/filing_cli.py"),
    ("director.ingestion.note_handoff", "augment_extracted_filings", ROOT / "director/ingestion/note_handoff.py"),
    ("director.ingestion.filing_validator", "validate_extracted_filing", ROOT / "director/ingestion/filing_validator.py"),
    ("director.data.normalization_candidate", "AdoptionRecord", ROOT / "director/data/normalization_candidate.py"),
    ("director.data.normalization_candidate", "TreatmentRecord", ROOT / "director/data/normalization_candidate.py"),
    ("modeler.ingestion.normalization_candidate_admission", "construct_provisional_candidate", ROOT / "modeler/ingestion/normalization_candidate_admission.py"),
    ("modeler.ingestion.normalization_candidate_admission", "evaluate_adoption", ROOT / "modeler/ingestion/normalization_candidate_admission.py"),
    ("director.ingestion.normalization_candidate_admission", "run_normalization_candidate_handoff", ROOT / "director/ingestion/normalization_candidate_admission.py"),
    ("director.ingestion.normalization_candidate_admission", "save_admitted_normalization_candidate", ROOT / "director/ingestion/normalization_candidate_admission.py"),
    ("director.ingestion.normalization_candidate_admission", "load_admitted_normalization_candidate", ROOT / "director/ingestion/normalization_candidate_admission.py"),
    ("interpreter.normalization", "grouping_established_as_source_fact", ROOT / "interpreter/normalization.py"),
    ("extractor.ingestion.management_kpi_enrichment", "inspect_source_pdf", ROOT / "extractor/ingestion/management_kpi_enrichment.py"),
    ("modeler.ingestion.management_kpi_enrichment", "assess_definition_equivalence", ROOT / "modeler/ingestion/management_kpi_enrichment.py"),
    ("modeler.ingestion.management_kpi_enrichment", "build_group_decisions", ROOT / "modeler/ingestion/management_kpi_enrichment.py"),
    ("director.ingestion.management_kpi_enrichment", "enrich_management_working_copies", ROOT / "director/ingestion/management_kpi_enrichment.py"),
)
FACADE_PAIRS = (
    ("modeler.data.interface", "core.data.interface", "StandardizedFinancials"),
    ("modeler.data.validators", "core.data.validators", "validate_income_statement"),
    ("modeler.data.standardized_io", "core.data.standardized_io", "standardized_to_payload"),
    ("modeler.data.line_identity", "core.data.line_identity", "line_identity"),
    ("modeler.data.issuer_fiscal", "core.data.issuer_fiscal", "issuer_fiscal_label"),
    ("modeler.data.historical_operating_kpis", "core.data.historical_operating_kpis", "validate_operating_kpi_fact"),
    ("modeler.data.historical_segments", "core.data.historical_segments", "SEGMENT_BRIDGE_TOLERANCE"),
    ("director.data.schema", "core.data.schema", "validate_standardized"),
    ("modeler.ingestion.base", "core.ingestion.base", "BaseIngestionAdapter"),
    ("modeler.ingestion.reconciler", "core.ingestion.reconciler", "reconcile_financials"),
    ("modeler.ingestion.filing_reconciler", "core.ingestion.filing_reconciler", "reconcile_filings"),
    ("modeler.ingestion.filing_standardizer", "core.ingestion.filing_standardizer", "standardize_reconciled"),
    ("modeler.ingestion.management_kpi", "core.ingestion.management_kpi", "bind_management_documents"),
    ("modeler.ingestion.management_kpi_identity", "core.ingestion.management_kpi_identity", "SUPPORTED_METRIC_MAPPINGS"),
    ("modeler.ingestion.management_kpi_reconciliation", "core.ingestion.management_kpi_reconciliation", "reconciliation_payload"),
    ("modeler.ingestion.management_kpi_history", "core.ingestion.management_kpi_history", "selected_management_kpi_histories"),
    ("modeler.ingestion.operating_kpi", "core.ingestion.operating_kpi", "select_operating_kpi_facts"),
    ("modeler.ingestion.geographic_segment", "core.ingestion.geographic_segment", "select_geographic_segment_facts"),
    ("modeler.ingestion.share_basis", "core.ingestion.share_basis", "resolve_historical_share_basis"),
    ("director.ingestion.filing_cli", "core.ingestion.filing_cli", "load_and_validate_extracted_dir"),
    ("director.ingestion.note_handoff", "core.ingestion.note_handoff", "augment_extracted_filings"),
    ("director.ingestion.filing_validator", "core.ingestion.filing_validator", "validate_extracted_filing"),
    ("modeler.ingestion.filing_validator", "core.ingestion.filing_validator", "operating_kpi_admission_issues"),
    ("director.data.normalization_candidate", "core.ingestion.normalization_candidate_admission", "AdoptionRecord"),
    ("director.data.normalization_candidate", "core.ingestion.normalization_candidate_admission", "TreatmentRecord"),
    ("modeler.ingestion.normalization_candidate_admission", "core.ingestion.normalization_candidate_admission", "construct_provisional_candidate"),
    ("modeler.ingestion.normalization_candidate_admission", "core.ingestion.normalization_candidate_admission", "evaluate_adoption"),
    ("modeler.ingestion.normalization_candidate_admission", "core.ingestion.normalization_candidate_admission", "evaluate_treatment"),
    ("director.ingestion.normalization_candidate_admission", "core.ingestion.normalization_candidate_admission", "run_normalization_candidate_handoff"),
    ("director.ingestion.normalization_candidate_admission", "core.ingestion.normalization_candidate_admission", "save_admitted_normalization_candidate"),
    ("director.ingestion.normalization_candidate_admission", "core.ingestion.normalization_candidate_admission", "load_admitted_normalization_candidate"),
    ("director.ingestion.normalization_candidate_admission", "core.ingestion.normalization_candidate_admission", "HandoffResult"),
    ("extractor.ingestion.management_kpi_enrichment", "core.ingestion.management_kpi_enrichment", "inspect_source_pdf"),
    ("modeler.ingestion.management_kpi_enrichment", "core.ingestion.management_kpi_enrichment", "assess_definition_equivalence"),
    ("modeler.ingestion.management_kpi_enrichment", "core.ingestion.management_kpi_enrichment", "build_group_decisions"),
    ("director.ingestion.management_kpi_enrichment", "core.ingestion.management_kpi_enrichment", "enrich_management_working_copies"),
)


def _public_names(module) -> list[str]:
    return [name for name in dir(module) if not name.startswith("_")]


def test_canonical_definitions_are_owner_owned():
    for module_name, attr, path in REPRESENTATIVE:
        module = __import__(module_name, fromlist=[attr])
        assert Path(module.__file__).resolve() == path.resolve()
        assert callable(getattr(module, attr)) or getattr(module, attr) is not None


def test_compatibility_exports_are_identity_equal():
    from extractor.data.interface import (
        DataSourceAdapter as ext_adapter,
        DocumentManifest as ext_manifest,
        DocumentType as ext_type,
    )
    from core.data.interface import (
        DataSourceAdapter as facade_adapter,
        DocumentManifest as facade_manifest,
        DocumentType as facade_type,
    )
    from extractor.data.filing_validator import (
        FilingValidationIssue as ext_issue,
        bind_source_file as ext_bind,
        source_row_identity as ext_identity,
        validate_extracted_filing as ext_documentary,
    )
    from core.ingestion.filing_validator import (
        FilingValidationIssue as facade_issue,
        bind_source_file as facade_bind,
        source_row_identity as facade_identity,
        validate_extracted_filing_documentary as facade_documentary,
        _operating_kpi_admission_for_fact as facade_helper,
    )
    from modeler.ingestion.filing_validator import (
        _operating_kpi_admission_for_fact as canonical_helper,
    )
    from modeler.ingestion.reconciler import _merge_line_items as canonical_merge
    from core.ingestion.reconciler import _merge_line_items as facade_merge
    from modeler.ingestion.management_kpi_reconciliation import (
        _select_ordinary_group as canonical_select,
    )
    from core.ingestion.management_kpi_reconciliation import (
        _select_ordinary_group as facade_select,
    )

    assert facade_adapter is ext_adapter
    assert facade_manifest is ext_manifest
    assert facade_type is ext_type
    assert facade_issue is ext_issue
    assert facade_bind is ext_bind
    assert facade_identity is ext_identity
    assert facade_documentary is ext_documentary
    assert facade_helper is canonical_helper
    assert facade_merge is canonical_merge
    assert facade_select is canonical_select

    from core.data import __all__ as data_all
    from core.ingestion import __all__ as ingest_all

    assert data_all == [
        "DataSourceAdapter",
        "DocumentManifest",
        "FinancialPeriod",
        "LineItem",
        "ReconciliationReport",
        "StandardizedFinancials",
        "StatementKind",
        "validate_standardized",
        "validate_balance_sheet",
        "validate_cash_flow",
        "validate_income_statement",
    ]
    assert ingest_all == [
        "BaseIngestionAdapter",
        "ExcelExportAdapter",
        "HKManualDocumentAdapter",
        "reconcile_financials",
    ]

    for canonical_name, facade_name, attr in FACADE_PAIRS:
        canonical = __import__(canonical_name, fromlist=["*"])
        facade = __import__(facade_name, fromlist=["*"])
        assert getattr(facade, attr) is getattr(canonical, attr)
        if facade_name == "core.ingestion.filing_validator":
            continue
        if facade_name == "core.data.interface":
            continue
        if facade_name == "core.ingestion.normalization_candidate_admission":
            continue
        if facade_name == "core.ingestion.management_kpi_enrichment":
            continue
        for public in _public_names(canonical):
            assert getattr(facade, public) is getattr(canonical, public)
        stem = canonical_name.rsplit(".", 1)[-1]
        for private in PRIVATE_EXPORTS.get(stem, ()):
            assert getattr(facade, private) is getattr(canonical, private)


def test_facade_and_canonical_import_orders():
    samples = (
        ("modeler.data.interface", "core.data.interface", "StandardizedFinancials"),
        ("director.data.schema", "core.data.schema", "StatementKind"),
        ("modeler.ingestion.reconciler", "core.ingestion.reconciler", "reconcile_financials"),
        ("director.ingestion.filing_validator", "core.ingestion.filing_validator", "validate_extracted_filing"),
        ("modeler.ingestion.filing_validator", "core.ingestion.filing_validator", "operating_kpi_admission_issues"),
        ("director.ingestion.normalization_candidate_admission", "core.ingestion.normalization_candidate_admission", "run_normalization_candidate_handoff"),
        ("modeler.ingestion.normalization_candidate_admission", "core.ingestion.normalization_candidate_admission", "construct_provisional_candidate"),
        ("director.ingestion.management_kpi_enrichment", "core.ingestion.management_kpi_enrichment", "enrich_management_working_copies"),
        ("extractor.ingestion.management_kpi_enrichment", "core.ingestion.management_kpi_enrichment", "inspect_source_pdf"),
        ("modeler.ingestion.management_kpi_enrichment", "core.ingestion.management_kpi_enrichment", "build_group_decisions"),
    )
    orders = (
        "import {facade} as facade\nimport {canonical} as canonical\n",
        "import {canonical} as canonical\nimport {facade} as facade\n",
    )
    extras = (
        "from extractor.data.interface import DocumentManifest as ext_manifest\n"
        "from core.data.interface import DocumentManifest as facade_manifest\n"
        "assert facade_manifest is ext_manifest\n"
        "from modeler.ingestion.reconciler import _merge_line_items as canonical_merge\n"
        "from core.ingestion.reconciler import _merge_line_items as facade_merge\n"
        "assert facade_merge is canonical_merge\n"
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
        *(ROOT / "modeler/data" / f"{name}.py" for name in DATA_MOVED),
        ROOT / "director/data/schema.py",
        *(ROOT / "modeler/ingestion" / f"{name}.py" for name in INGEST_MOVED),
        ROOT / "modeler/ingestion/filing_validator.py",
        ROOT / "director/ingestion/filing_cli.py",
        ROOT / "director/ingestion/note_handoff.py",
        ROOT / "director/ingestion/filing_validator.py",
        ROOT / "director/data/normalization_candidate.py",
        ROOT / "modeler/ingestion/normalization_candidate_admission.py",
        ROOT / "director/ingestion/normalization_candidate_admission.py",
        ROOT / "interpreter/normalization.py",
        ROOT / "extractor/ingestion/management_kpi_enrichment.py",
        ROOT / "modeler/ingestion/management_kpi_enrichment.py",
        ROOT / "director/ingestion/management_kpi_enrichment.py",
    ]
    forbidden_data = {f"core.data.{name}" for name in DATA_MOVED} | {"core.data.schema"}
    forbidden_ingest = {f"core.ingestion.{name}" for name in INGEST_MOVED} | {
        "core.ingestion.filing_cli",
        "core.ingestion.note_handoff",
        "core.ingestion.filing_validator",
        "core.ingestion.normalization_candidate_admission",
        "core.ingestion.management_kpi_enrichment",
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
    from director.ingestion.management_kpi_enrichment import (
        PAGE_RESOLUTION_NAME as canonical_page,
        enrich_management_working_copies as canonical_enrich,
    )
    from extractor.ingestion.management_kpi_enrichment import (
        CalendarYearEvidence as canonical_calendar,
        SourceInspection as canonical_inspection,
        _metric_exclusion_evidence as canonical_exclusion,
        _metric_excludes_53rd_week as canonical_excludes,
        definition_features as canonical_features,
        inspect_source_pdf as canonical_inspect,
        validate_physical_page_binding as canonical_validate,
    )
    from modeler.ingestion.management_kpi_enrichment import (
        DEFINITION_EQUIVALENT as canonical_equivalent,
        assess_definition_equivalence as canonical_assess,
        build_group_decisions as canonical_decisions,
        enrich_management_payload as canonical_payload,
    )
    from core.ingestion.management_kpi_enrichment import (
        PAGE_RESOLUTION_NAME as facade_page,
        CalendarYearEvidence as facade_calendar,
        DEFINITION_EQUIVALENT as facade_equivalent,
        SourceInspection as facade_inspection,
        _metric_exclusion_evidence as facade_exclusion,
        _metric_excludes_53rd_week as facade_excludes,
        assess_definition_equivalence as facade_assess,
        build_group_decisions as facade_decisions,
        definition_features as facade_features,
        enrich_management_payload as facade_payload,
        enrich_management_working_copies as facade_enrich,
        inspect_source_pdf as facade_inspect,
        validate_physical_page_binding as facade_validate,
    )

    assert canonical_inspect is facade_inspect
    assert canonical_validate is facade_validate
    assert canonical_features is facade_features
    assert canonical_calendar is facade_calendar
    assert canonical_inspection is facade_inspection
    assert canonical_exclusion is facade_exclusion
    assert canonical_excludes is facade_excludes
    assert canonical_assess is facade_assess
    assert canonical_equivalent is facade_equivalent
    assert canonical_decisions is facade_decisions
    assert canonical_payload is facade_payload
    assert canonical_enrich is facade_enrich
    assert canonical_page is facade_page
    assert Path(canonical_inspect.__code__.co_filename).resolve() == (
        ROOT / "extractor/ingestion/management_kpi_enrichment.py"
    ).resolve()
    assert Path(canonical_assess.__code__.co_filename).resolve() == (
        ROOT / "modeler/ingestion/management_kpi_enrichment.py"
    ).resolve()
    assert Path(canonical_decisions.__code__.co_filename).resolve() == (
        ROOT / "modeler/ingestion/management_kpi_enrichment.py"
    ).resolve()
    assert Path(canonical_enrich.__code__.co_filename).resolve() == (
        ROOT / "director/ingestion/management_kpi_enrichment.py"
    ).resolve()


def test_normalization_candidate_canonical_ownership():
    from director.data.normalization_candidate import (
        AdoptionRecord as canonical_adoption,
        TreatmentRecord as canonical_treatment,
    )
    from director.ingestion.normalization_candidate_admission import (
        HandoffResult as canonical_handoff,
        load_admitted_normalization_candidate as canonical_load,
        run_normalization_candidate_handoff as canonical_run,
        save_admitted_normalization_candidate as canonical_save,
    )
    from interpreter.normalization import grouping_established_as_source_fact
    from modeler.ingestion.normalization_candidate_admission import (
        construct_provisional_candidate as canonical_construct,
        evaluate_adoption as canonical_evaluate_adoption,
        evaluate_treatment as canonical_evaluate_treatment,
    )
    from modeler.ingestion.normalization_candidate_admission_io import (
        AdmissionProvenanceError as canonical_error,
    )
    from core.ingestion.normalization_candidate_admission import (
        AdmissionProvenanceError as facade_error,
        AdoptionRecord as facade_adoption,
        TreatmentRecord as facade_treatment,
        HandoffResult as facade_handoff,
        construct_provisional_candidate as facade_construct,
        evaluate_adoption as facade_evaluate_adoption,
        evaluate_treatment as facade_evaluate_treatment,
        load_admitted_normalization_candidate as facade_load,
        run_normalization_candidate_handoff as facade_run,
        save_admitted_normalization_candidate as facade_save,
        _insert_constructed_line as facade_insert,
    )
    from modeler.ingestion.normalization_candidate_admission import (
        _insert_constructed_line as canonical_insert,
    )

    assert canonical_adoption is facade_adoption
    assert canonical_treatment is facade_treatment
    assert canonical_handoff is facade_handoff
    assert canonical_construct is facade_construct
    assert canonical_evaluate_adoption is facade_evaluate_adoption
    assert canonical_evaluate_treatment is facade_evaluate_treatment
    assert canonical_run is facade_run
    assert canonical_save is facade_save
    assert canonical_load is facade_load
    assert canonical_error is facade_error
    assert canonical_insert is facade_insert
    assert grouping_established_as_source_fact() is False
    assert grouping_established_as_source_fact("independently_supplied") is False
    assert Path(canonical_construct.__code__.co_filename).resolve() == (
        ROOT / "modeler/ingestion/normalization_candidate_admission.py"
    ).resolve()
    assert Path(canonical_run.__code__.co_filename).resolve() == (
        ROOT / "director/ingestion/normalization_candidate_admission.py"
    ).resolve()
    assert Path(grouping_established_as_source_fact.__code__.co_filename).resolve() == (
        ROOT / "interpreter/normalization.py"
    ).resolve()


def test_extractor_lazy_metric_mapping_uses_modeler_owner():
    source = (ROOT / "extractor/data/management_kpi_json.py").read_text()
    assert "from modeler.ingestion.management_kpi_identity import SUPPORTED_METRIC_MAPPINGS" in source
    assert "from core.ingestion.management_kpi_identity import SUPPORTED_METRIC_MAPPINGS" not in source


def test_relocated_implementations_do_not_import_legacy():
    paths = [
        *(ROOT / "modeler/data" / f"{name}.py" for name in DATA_MOVED),
        ROOT / "director/data/schema.py",
        *(ROOT / "modeler/ingestion" / f"{name}.py" for name in INGEST_MOVED),
        ROOT / "modeler/ingestion/filing_validator.py",
        ROOT / "director/ingestion/filing_cli.py",
        ROOT / "director/ingestion/note_handoff.py",
        ROOT / "director/ingestion/filing_validator.py",
        ROOT / "director/data/normalization_candidate.py",
        ROOT / "modeler/ingestion/normalization_candidate_admission.py",
        ROOT / "director/ingestion/normalization_candidate_admission.py",
        ROOT / "interpreter/normalization.py",
        ROOT / "extractor/ingestion/management_kpi_enrichment.py",
        ROOT / "modeler/ingestion/management_kpi_enrichment.py",
        ROOT / "director/ingestion/management_kpi_enrichment.py",
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
