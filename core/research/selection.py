"""Compatibility façade. Delegates without calculations, judgments, or wording."""

from __future__ import annotations

from composer.research.selection import (
    geographic_figure_question,
    select_driver_argument as compose_driver_selection,
)
from composer.research.selection_roles import (
    PUBLICATION_APPENDIX,
    PUBLICATION_EXCLUDED,
    PUBLICATION_MAIN,
    PUBLICATION_RETAINED,
    ROLE_APPENDIX,
    ROLE_EXCLUDED,
    ROLE_PRINCIPAL,
    ROLE_SECONDARY,
)
from director.research import complete_driver_selection
from interpreter.selection import (
    CLAIM_ASSOCIATION,
    CLAIM_ATTRIBUTION,
    CLAIM_IDENTITY,
    CLAIM_INFERENCE,
    CLAIM_INTERPRETATION,
    CLAIM_LOCALIZATION,
    CLAIM_PROXY,
    CLAIM_REPORTED,
    CLAIM_UNRESOLVED,
    geographic_materiality_rationale,
    geographic_strongest_conclusion,
    investigate_driver_questions,
)
from modeler.research.geo_conditions import (
    OFFSET_EXACT,
    OFFSET_GREATER,
    OFFSET_PARTIAL,
    GeographicClaimConditions,
    geographic_claim_conditions,
    revenue_offset_kind as _revenue_offset_kind,
)
from modeler.research.records import (
    ResearchClaim,
    ResearchQuestion,
    ResearchSelection,
    SelectionDecision,
)


def select_driver_argument(view) -> ResearchSelection:
    return complete_driver_selection(view)


__all__ = (
    "CLAIM_ASSOCIATION",
    "CLAIM_ATTRIBUTION",
    "CLAIM_IDENTITY",
    "CLAIM_INFERENCE",
    "CLAIM_INTERPRETATION",
    "CLAIM_LOCALIZATION",
    "CLAIM_PROXY",
    "CLAIM_REPORTED",
    "CLAIM_UNRESOLVED",
    "GeographicClaimConditions",
    "OFFSET_EXACT",
    "OFFSET_GREATER",
    "OFFSET_PARTIAL",
    "PUBLICATION_APPENDIX",
    "PUBLICATION_EXCLUDED",
    "PUBLICATION_MAIN",
    "PUBLICATION_RETAINED",
    "ROLE_APPENDIX",
    "ROLE_EXCLUDED",
    "ROLE_PRINCIPAL",
    "ROLE_SECONDARY",
    "ResearchClaim",
    "ResearchQuestion",
    "ResearchSelection",
    "SelectionDecision",
    "_revenue_offset_kind",
    "compose_driver_selection",
    "geographic_claim_conditions",
    "geographic_figure_question",
    "geographic_materiality_rationale",
    "geographic_strongest_conclusion",
    "investigate_driver_questions",
    "select_driver_argument",
)
