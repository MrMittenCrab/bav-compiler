"""Compatibility façade. Implementation is split across Extractor, Modeler and Director."""

from extractor.data.filing_validator import (
    FilingValidationIssue,
    FilingValidationReport,
    bind_source_file,
    source_row_identity,
    validate_extracted_filing as validate_extracted_filing_documentary,
)
from modeler.ingestion.filing_validator import (
    operating_kpi_admission_issues,
    _operating_kpi_admission_for_fact,
)
from director.ingestion.filing_validator import validate_extracted_filing

__all__ = [
    "FilingValidationIssue",
    "FilingValidationReport",
    "bind_source_file",
    "operating_kpi_admission_issues",
    "source_row_identity",
    "validate_extracted_filing",
    "validate_extracted_filing_documentary",
]
