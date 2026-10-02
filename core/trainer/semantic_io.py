"""Compatibility façade. Delegates sidecar I/O to Modeler."""

from modeler.semantic_io import (
    answer_key_path_for,
    bav_path_for,
    company_stem_from_output,
    component_map_path_for,
    get_component,
    group_components_by_family,
    load_semantic_map,
    parse_cell_ref,
    reference_workbook_path,
    resolve_pair_paths,
    sidecar_paths,
    supporting_dir,
)

__all__ = [
    "answer_key_path_for",
    "bav_path_for",
    "company_stem_from_output",
    "component_map_path_for",
    "get_component",
    "group_components_by_family",
    "load_semantic_map",
    "parse_cell_ref",
    "reference_workbook_path",
    "resolve_pair_paths",
    "sidecar_paths",
    "supporting_dir",
]
