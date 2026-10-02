"""Director-owned complete-build policy.

This table declares module identity, completion status, ordering, required
inputs, dependencies and writer identities. Modeler binds preparation and
workbook writers. Forecast remains deferred.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BuildModulePolicy:
    id: str
    status: str
    workbook_capable: bool = True
    complete_analysis: bool = True
    depends_on: tuple[str, ...] = ("historical",)
    current_ready: bool = True
    writers: tuple[str, ...] = ()
    spec_key: str = "default"
    required_inputs: tuple = ()


BUILD_MODULES = (
    BuildModulePolicy(
        "historical",
        "complete",
        depends_on=(),
        writers=("source", "condensed", "dupont", "judgment"),
    ),
    BuildModulePolicy(
        "normalization",
        "complete",
        writers=("normalization_judgment", "normalization"),
    ),
    BuildModulePolicy("quality", "complete", writers=("quality",)),
    BuildModulePolicy("working_capital", "complete", writers=("working_capital",)),
    BuildModulePolicy("profitability_driver", "complete", writers=("dupont",)),
    BuildModulePolicy("profitability_change", "complete", writers=("dupont",)),
    BuildModulePolicy("roe_attribution", "complete", writers=("dupont",)),
    BuildModulePolicy(
        "quality_change",
        "complete",
        depends_on=("quality",),
        writers=("quality",),
    ),
    BuildModulePolicy("per_share", "complete", writers=("per_share",)),
    BuildModulePolicy(
        "per_share_attribution",
        "complete",
        depends_on=("per_share",),
        writers=("per_share",),
    ),
    BuildModulePolicy(
        "normalized_per_share",
        "complete",
        depends_on=("normalization", "per_share"),
        writers=("per_share",),
    ),
    BuildModulePolicy("fixed_asset", "complete", writers=("dupont",)),
    BuildModulePolicy("lease_liability", "complete", writers=("dupont",)),
    BuildModulePolicy("ownership_attribution", "complete", writers=("ownership",)),
    BuildModulePolicy("goodwill_intangibles", "complete", writers=("dupont",)),
    BuildModulePolicy("lease_rou", "complete", writers=("dupont",)),
    BuildModulePolicy("deferred_tax", "complete", writers=("dupont",)),
    BuildModulePolicy("capex", "complete", writers=("dupont",)),
    BuildModulePolicy("lease_repayment", "complete", writers=("dupont",)),
    BuildModulePolicy("acquisition_cash", "complete", writers=("dupont",)),
    BuildModulePolicy("share_repurchase", "complete", writers=("dupont",)),
    BuildModulePolicy("cash_rollforward", "complete", writers=("dupont",)),
    BuildModulePolicy("reported_margin", "complete", writers=("dupont",)),
    BuildModulePolicy("inventory_analysis", "complete", writers=("dupont",)),
    BuildModulePolicy(
        "geographic",
        "complete",
        writers=("geographic",),
        spec_key="geographic",
    ),
    BuildModulePolicy(
        "operating_kpi",
        "complete",
        writers=(
            "operating_kpi",
            "comparable_sales",
            "sales_per_square_foot",
            "revenue_per_store",
        ),
        spec_key="operating_kpi",
    ),
    BuildModulePolicy(
        "revenue_driver",
        "complete",
        depends_on=("historical", "operating_kpi"),
        writers=("revenue_driver",),
        spec_key="revenue_driver",
    ),
    BuildModulePolicy("forecast", "deferred", current_ready=False),
)
