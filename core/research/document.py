"""Compatibility façade. Delegates without calculations, judgments, or wording."""

from __future__ import annotations

from composer.research.document import (
    BODY_PT,
    CAPTION_PT,
    DEBUG_TERMS,
    HEADING_PT,
    LANDSCAPE,
    MM_PT,
    PAGE_MARGIN_MM,
    PORTRAIT,
    Body,
    FigureBlock,
    Heading,
    ListBlock,
    PublishedDocuments,
    TableBlock,
    publication_filenames,
    publish_company_documents,
    publish_resolved_company,
    require_pandoc,
    require_publication_libraries,
)

__all__ = (
    "BODY_PT",
    "CAPTION_PT",
    "DEBUG_TERMS",
    "HEADING_PT",
    "LANDSCAPE",
    "MM_PT",
    "PAGE_MARGIN_MM",
    "PORTRAIT",
    "Body",
    "FigureBlock",
    "Heading",
    "ListBlock",
    "PublishedDocuments",
    "TableBlock",
    "publication_filenames",
    "publish_company_documents",
    "publish_resolved_company",
    "require_pandoc",
    "require_publication_libraries",
)
