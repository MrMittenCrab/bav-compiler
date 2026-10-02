"""Modeler execution of Director complete-build policy.

Registration is intentional: a Python analytical module alone is not a workbook
module. An eligible entry supplies preparation/specs and workbook writers. Input
package presence is checked before applicability or metric-level availability.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Callable

from director.build_contract import BUILD_MODULES as BUILD_MODULE_POLICY
from .component_catalog import (
    ComponentSpec,
    geographic_spec_identity,
    operating_kpi_spec_identity,
    revenue_driver_spec_identity,
)

if TYPE_CHECKING:
    from openpyxl import Workbook
    from modeler.data.interface import StandardizedFinancials
    from modeler.workbook import ReferenceModelBuilder
    from .semantic_map import SemanticMap


@dataclass(frozen=True)
class RequiredInput:
    name: str
    supplied: Callable[[StandardizedFinancials], bool]


@dataclass(frozen=True)
class WorkbookWriter:
    """Shared sheet writers run once, after every module has prepared its specs."""

    id: str
    order: int
    write: Callable[[ReferenceModelBuilder, Workbook], None]


def _spec_key(spec: ComponentSpec) -> tuple:
    return spec.family_id, spec.period_index


@dataclass(frozen=True)
class BuildModule:
    id: str
    status: str
    workbook_capable: bool
    complete_analysis: bool
    prepare: Callable[[ReferenceModelBuilder, int], tuple[ComponentSpec, ...]] | None = None
    writers: tuple[WorkbookWriter, ...] = ()
    depends_on: tuple[str, ...] = ()
    required_inputs: tuple[RequiredInput, ...] = ()
    applicable: Callable[[ReferenceModelBuilder], bool] | None = None
    spec_key: Callable[[ComponentSpec], tuple] = _spec_key
    current_ready: bool = False


def complete_build_modules(financials: StandardizedFinancials, *, current_snapshot: bool = False) -> tuple[BuildModule, ...]:
    """Snapshot and validate the registry; never select by available input alone."""
    selected = []
    seen = set()
    ready = set()
    for module in BUILD_MODULES:
        if module.id in seen:
            raise ValueError(f"Duplicate Build module: {module.id}")
        seen.add(module.id)
        if module.status not in {"complete", "incomplete", "deferred"}:
            raise ValueError(f"Unknown Build completion status: {module.id}: {module.status}")
        if not (module.workbook_capable and (
            (module.status == "complete" and module.complete_analysis)
            or (current_snapshot and module.current_ready and module.status != "deferred")
        )):
            continue
        if not callable(module.prepare) or not module.writers:
            raise ValueError(f"Build module {module.id}: missing workbook/spec integration")
        for writer in module.writers:
            if not callable(writer.write):
                raise ValueError(f"Build module {module.id}: invalid workbook writer {writer.id}")
        for dependency in module.depends_on:
            if dependency not in ready:
                raise ValueError(f"Build module {module.id}: dependency {dependency} must be registered before it and eligible")
        for requirement in module.required_inputs:
            if not requirement.supplied(financials):
                raise ValueError(f"Build module {module.id}: missing required input: {requirement.name}")
        selected.append(module)
        ready.add(module.id)
    return tuple(selected)


def prepare_complete_build(builder: ReferenceModelBuilder) -> tuple[ComponentSpec, ...]:
    """Prepare in registry order and assign globally unique component order."""
    specs = []
    builder.module_specs = {}
    builder.workbook_writers = {}
    for module in builder.build_modules:
        if module.applicable is not None and not module.applicable(builder):
            continue
        for dependency in module.depends_on:
            if dependency not in builder.module_specs:
                raise ValueError(
                    f"Build module {module.id}: dependency {dependency} is not applicable"
                )
        assert module.prepare is not None
        prepared = tuple(module.prepare(builder, len(specs) + 1))
        # Source-unavailable filtering can leave holes in a family's local order.
        # Rebase after filtering, so the following module cannot overlap it.
        ordered = tuple(replace(spec, order=len(specs) + i + 1) for i, spec in enumerate(prepared))
        builder.module_specs[module.id] = ordered
        setattr(builder, f"{module.id}_specs", ordered)
        setattr(builder, f"_{module.id}_spec_index", {
            module.spec_key(s): s for s in ordered
        })
        specs.extend(ordered)
        for writer in module.writers:
            previous = builder.workbook_writers.setdefault(writer.id, writer)
            if previous != writer:
                raise ValueError(f"Conflicting Build workbook writer: {writer.id}")
    ids = [s.id for s in specs]
    keys = [s.semantic_key for s in specs]
    if len(set(ids)) != len(ids) or len(set(keys)) != len(keys):
        raise ValueError("Duplicate Build component identity")
    return tuple(specs)


def write_complete_build(builder: ReferenceModelBuilder, workbook: Workbook) -> None:
    # Stable sorting preserves registration order for equal writer priorities.
    for writer in sorted(builder.workbook_writers.values(), key=lambda w: w.order):
        writer.write(builder, workbook)


def verify_complete_build(expected_specs: tuple[ComponentSpec, ...], semantic_map: SemanticMap) -> None:
    """Reject missing, extra, reordered or substituted runtime components."""
    def identity(component):
        return (component.id, component.semantic_key, component.family_id,
                component.period_index, component.period_end, component.order,
                tuple(component.depends_on))

    expected = [identity(s) for s in expected_specs]
    actual = [identity(c) for c in semantic_map.all_ordered()]
    if actual != expected:
        missing = sorted({s[0] for s in expected} - {s[0] for s in actual})
        extra = sorted({s[0] for s in actual} - {s[0] for s in expected})
        raise ValueError(
            "Complete Build semantic component mismatch: "
            f"expected={len(expected)}, actual={len(actual)}, missing={missing}, extra={extra}; "
            "ordered identities must match the runtime contract"
        )


def _writer(method: str, order: int, *, when: str | None = None) -> WorkbookWriter:
    def write(builder, workbook):
        if when is None or getattr(builder, when):
            getattr(builder, method)(workbook)
    return WorkbookWriter(method, order, write)


SOURCE = _writer("_build_source_tabs", 0)
CONDENSED = _writer("_build_condensed", 1)
DUPONT = _writer("_build_dupont", 2)
JUDGMENT = _writer("_build_accounting_judgment", 3)
OWNERSHIP = _writer("_build_ownership_attribution", 4, when="ownership_attribution_series")
NORMALIZATION_JUDGMENT = _writer("_build_normalization_judgment", 5, when="normalization_cases")
NORMALIZATION = _writer("_build_earnings_normalization", 6, when="normalization_cases")
QUALITY = _writer("_build_earnings_quality", 7, when="quality_series")
WORKING_CAPITAL = _writer("_build_working_capital_analysis", 8, when="working_capital_series")
PER_SHARE = _writer("_build_per_share_analysis", 9, when="per_share_series")
GEOGRAPHIC = _writer("_build_geographic_segment", 10, when="geographic_series")
OPERATING_KPI = _writer("_build_store_count", 11, when="operating_kpi_series")
COMPARABLE_SALES = _writer(
    "_build_comparable_sales", 12, when="comparable_sales_schedule"
)
SALES_PER_SQUARE_FOOT = _writer(
    "_build_sales_per_square_foot", 13, when="sales_per_square_foot_schedule"
)
REVENUE_PER_STORE = _writer(
    "_build_revenue_per_store", 14, when="revenue_per_store_schedule"
)
REVENUE_DRIVER = _writer(
    "_build_revenue_driver", 15, when="revenue_driver_schedule"
)

_WRITERS = {
    "source": SOURCE,
    "condensed": CONDENSED,
    "dupont": DUPONT,
    "judgment": JUDGMENT,
    "ownership": OWNERSHIP,
    "normalization_judgment": NORMALIZATION_JUDGMENT,
    "normalization": NORMALIZATION,
    "quality": QUALITY,
    "working_capital": WORKING_CAPITAL,
    "per_share": PER_SHARE,
    "geographic": GEOGRAPHIC,
    "operating_kpi": OPERATING_KPI,
    "comparable_sales": COMPARABLE_SALES,
    "sales_per_square_foot": SALES_PER_SQUARE_FOOT,
    "revenue_per_store": REVENUE_PER_STORE,
    "revenue_driver": REVENUE_DRIVER,
}

_SPEC_KEYS = {
    "default": _spec_key,
    "geographic": lambda s: (s.family_id, s.period_index, geographic_spec_identity(s)),
    "operating_kpi": lambda s: (s.family_id, s.period_index, operating_kpi_spec_identity(s)),
    "revenue_driver": lambda s: (s.family_id, s.period_index, revenue_driver_spec_identity(s)),
}


def _prepare_for(module_id: str):
    def prepare(builder, start_order):
        return getattr(builder, f"_prepare_{module_id}")(start_order)
    return prepare


def _bind_policy(policy) -> BuildModule:
    writers = tuple(_WRITERS[name] for name in policy.writers)
    prepare = _prepare_for(policy.id) if writers else None
    return BuildModule(
        policy.id,
        policy.status,
        policy.workbook_capable,
        policy.complete_analysis,
        prepare,
        writers,
        policy.depends_on,
        policy.required_inputs,
        spec_key=_SPEC_KEYS[policy.spec_key],
        current_ready=policy.current_ready,
    )


# Bound executable modules. Tests that extend the contract replace this tuple.
# Ordering, required inputs and deferred statuses come from Director policy.
BUILD_MODULES = tuple(_bind_policy(policy) for policy in BUILD_MODULE_POLICY)
