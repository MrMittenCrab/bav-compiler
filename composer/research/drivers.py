"""Driver wording, Markdown, figures, and publication helpers."""

from __future__ import annotations

from pathlib import Path
import re

from core.research.style import ResearchStyle, apply_research_style, finish_figure, new_figure
from modeler.research.drivers_view import (
    DriversView,
    date_text,
    fiscal_year_token,
    latest_growth_index,
    margin_reconstruction_complete,
    operating_profit_change,
)
from modeler.research.geo_conditions import (
    OFFSET_EXACT,
    OFFSET_GREATER,
    OFFSET_PARTIAL,
    geographic_claim_conditions,
)
from composer.research.selection import component_direction_phrase
from modeler.research.records import ResearchSelection

RESERVED_MODULES = ("Forecast", "Valuation", "Overview")
APPENDIX_HEADING = "## Appendix"
OBSOLETE_SECTIONS = (
    "## Context",
    "## Growth",
    "## Geography",
    "## Margin",
    "## Conclusions",
    "## Limits",
)
WORKPAPER_FIELDS = (
    "Kind",
    "Reconstruction",
    "Residual",
    "Stability",
    "Contradictions",
    "Result",
)
SECONDARY_HEADING = "## Secondary signals"
PRINCIPAL_HEADING = re.compile(r"^## \d+\.\s+\S")
SEGMENT_LABELS = {
    "americas": "Americas",
    "china_mainland": "China Mainland",
    "rest_of_world": "Rest of World",
}
POPULATION_LABELS = {
    "company_operated_stores": "company-operated stores",
    "company_operated_stores_and_direct_to_consumer": (
        "company-operated stores and direct-to-consumer"
    ),
    "company_operated_stores_and_ecommerce": (
        "company-operated stores and e-commerce"
    ),
}
_KIND_LABELS = {
    "identity": "identity",
    "reported_fact": "reported fact",
    "attributed_management_explanation": "management explanation",
    "observed_relationship": "observed relationship",
    "causal_hypothesis": "causal reading",
    "unestablished_inference": "unestablished",
}
_FORBIDDEN_RESEARCH = (
    "admitted",
    "fail-closed",
    "fail closed",
    "source unavailable",
    "standardizedfinancials",
    "hypothesis",
    "verdict",
    "audit-only",
    "audit only",
    "supported_descriptively",
    "segment_bridge",
    "provenance",
    "trainer",
    "answer key",
)


def drivers_filename(company: str) -> str:
    return f"{company}_Drivers.md"


def placeholder_filenames(company: str) -> tuple[str, ...]:
    return tuple(f"{company}_{module}.md" for module in RESERVED_MODULES)


def drivers_heading(company: str) -> str:
    return f"# {company} — Drivers"


def expected_sections(company: str) -> tuple[str, ...]:
    return (drivers_heading(company), APPENDIX_HEADING)


def is_principal_heading(line: str) -> bool:
    return bool(PRINCIPAL_HEADING.match(line))


def _completed_selection(view: DriversView) -> ResearchSelection:
    if view.selection is None:
        raise ValueError("Composer rendering requires completed selection")
    return view.selection


def _millions(thousands: float, digits: int = 1) -> float:
    return round(thousands / 1000.0, digits)


def _pct(value: float, digits: int = 2) -> str:
    return f"{value * 100:.{digits}f}%"


def _pp(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f} pp"


def _display_scale(view: DriversView) -> float:
    units = view.units.casefold()
    if "thousand" in units:
        return 1000.0
    return 1.0


def _display_amount(view: DriversView, native: float) -> float:
    return native / _display_scale(view)


def _money_view(view: DriversView, native: float | None, digits: int | None = None) -> str:
    if native is None:
        return "n/a"
    value = _display_amount(view, native)
    if digits is None:
        digits = 1 if view.currency == "USD" else 0
    sign = "−" if value < 0 else ""
    amount = f"{abs(value):,.{digits}f}"
    if view.currency == "USD":
        return f"{sign}${amount} million"
    return f"{sign}{view.currency} {amount} million"


def _research_safe(text: str) -> str:
    cleaned = text
    for source, target in (
        ("supported_descriptively", "supported descriptively"),
        ("fail-closed", "closed"),
        ("fail closed", "closed"),
        ("source unavailable", "unavailable"),
        ("standardizedfinancials", "standardized financials"),
        ("causal_hypothesis", "causal reading"),
        ("hypothesis", "reading"),
        ("Verdict", "Result"),
        ("verdict", "result"),
        ("audit-only", "kept out of the comparison"),
        ("audit only", "kept out of the comparison"),
        ("segment_bridge", "segment bridge"),
        ("provenance", "source note"),
        ("answer key", "reference"),
        ("Admitted ", "Reported "),
        ("admitted ", "reported "),
        ("admitted", "reported"),
        ("trainer", "practice file"),
    ):
        cleaned = cleaned.replace(source, target)
    return cleaned


def finding_sentence(item) -> str:
    status = "established" if item.established else "unestablished"
    limit = f" {item.limitation}" if item.limitation and not item.established else ""
    return _research_safe(
        f"{item.name.capitalize()}: {item.direction}. Residual: {item.residual}. "
        f"{status.capitalize()}.{limit}"
    )


def calendar_limitation(view: DriversView) -> str:
    selection = _completed_selection(view)
    if not selection.calendar_limited:
        return ""
    period = view.fifty_three_week_period
    if period is not None and period in view.periods:
        label = view.labels[view.periods.index(period)]
    else:
        label = view.issuer_fiscal_name or "The period"
    ended = date_text(period) if period is not None else ""
    naming = ""
    issuer = view.issuer_fiscal_name
    if issuer and label and fiscal_year_token(issuer) != fiscal_year_token(label):
        naming = f"; the issuer names it {issuer}"
    if ended:
        return (
            f"{label}, the year ended {ended}, is a 53-week year{naming}. "
            "Some later comparable-sales presentations exclude or realign that extra "
            "week and cannot be joined to the earlier observations."
        )
    return (
        f"{label} is a 53-week year{naming}. "
        "Some later comparable-sales presentations exclude or realign that extra "
        "week and cannot be joined to the earlier observations."
    )


def _opt_money(view: DriversView, thousands: float | None, digits: int | None = None) -> str:
    return _money_view(view, thousands, digits)


def _opt_pct(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return _pct(value, digits)


def _opt_pp(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return _pp(value, digits)


def _opt_change_pp(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:+.{digits}f} pp"


def _opt_bps(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 10000:+.0f} bps"


def _revenue_offset_sentence(kind: str | None) -> str:
    if kind == OFFSET_GREATER:
        return "International growth more than offset the Americas revenue decline."
    if kind == OFFSET_EXACT:
        return "International growth exactly offset the Americas revenue decline."
    if kind == OFFSET_PARTIAL:
        return "International growth only partially offset the Americas revenue decline."
    return ""


def _geography_figure_alt(conditions) -> str:
    if conditions.revenue_offset is not None and conditions.americas_profit_declined:
        return "Did international revenue growth offset Americas profit deterioration?"
    return "How did geographic revenue and operating-profit changes compare?"


def _margin_component_block(view: DriversView) -> str:
    if not view.sga_ratio:
        return ""
    rows = [
        "| Fiscal year | Gross margin | SG&A / revenue | Impairment / revenue | Other operating items / revenue | Operating margin | Residual |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, label in enumerate(view.labels):
        imp = (
            "n/a"
            if view.impairment_ratio is None or index >= len(view.impairment_ratio)
            else _opt_pct(view.impairment_ratio[index], 2)
        )
        other = (
            "n/a"
            if view.other_operating_ratio is None
            or index >= len(view.other_operating_ratio)
            else _opt_pct(view.other_operating_ratio[index], 2)
        )
        residual = (
            "n/a"
            if view.operating_margin_residual is None
            or index >= len(view.operating_margin_residual)
            else _opt_pct(view.operating_margin_residual[index], 2)
        )
        sga = (
            "n/a"
            if index >= len(view.sga_ratio)
            else _opt_pct(view.sga_ratio[index], 1)
        )
        rows.append(
            f"| {label} | {_pct(view.gross_margin[index], 1)} | {sga} | {imp} | "
            f"{other} | {_pct(view.operating_margin[index], 1)} | {residual} |"
        )
    latest = latest_growth_index(view)
    if margin_reconstruction_complete(view, latest):
        lead = (
            "Operating margin is reconstructed as gross margin less SG&A/revenue, "
            "impairment or asset-related charges/revenue, and other reported "
            "operating items/revenue. Missing lines stay blank; they are not filled "
            "with zero."
        )
    else:
        lead = (
            "Operating margin is reconstructed from disclosed components when they "
            "are available. A residual remains when components are missing or do "
            "not complete the identity. Missing lines stay blank; they are not "
            "filled with zero."
        )
    return lead + "\n\n" + "\n".join(rows) + "\n"


def _amount_bridge_block(view: DriversView) -> str:
    if not view.gross_profit_change:
        return ""
    rows = [
        "| Fiscal year | Revenue effect | Gross-margin effect | Interaction | Gross-profit change | SG&A change | Impairment change | Other operating-item change | Reconstructed operating-profit change | Reported operating-profit change | Residual |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, label in enumerate(view.labels):
        if view.gross_profit_change[index] is None:
            continue
        rows.append(
            "| {label} | {rev} | {gm} | {ix} | {gp} | {sga} | {imp} | {other} | {recon} | {op} | {resid} |".format(
                label=label,
                rev=_opt_money(
                    view,
                    None
                    if view.gross_profit_revenue_effect is None
                    else view.gross_profit_revenue_effect[index],
                ),
                gm=_opt_money(
                    view,
                    None
                    if view.gross_profit_margin_effect is None
                    else view.gross_profit_margin_effect[index],
                ),
                ix=_opt_money(
                    view,
                    None
                    if view.gross_profit_interaction is None
                    else view.gross_profit_interaction[index],
                ),
                gp=_opt_money(view, view.gross_profit_change[index]),
                sga=_opt_money(
                    view, None if view.sga_change is None else view.sga_change[index]
                ),
                imp=_opt_money(
                    view,
                    None
                    if view.impairment_change is None
                    else view.impairment_change[index],
                ),
                other=_opt_money(
                    view,
                    None
                    if view.other_operating_change is None
                    else view.other_operating_change[index],
                ),
                recon=_opt_money(
                    view,
                    None
                    if view.reconstructed_operating_profit_change is None
                    else view.reconstructed_operating_profit_change[index],
                ),
                op=_opt_money(
                    view,
                    None
                    if view.operating_profit_change is None
                    else view.operating_profit_change[index],
                ),
                resid=_opt_money(
                    view,
                    None
                    if view.operating_profit_change_residual is None
                    else view.operating_profit_change_residual[index],
                ),
            )
        )
    convention = view.amount_bridge_convention or (
        "Gross-profit change uses prior gross margin on the revenue change, "
        "prior revenue on the gross-margin change, and an explicit interaction."
    )
    return (
        convention
        + " An expense increase reduces operating profit. Missing adjacent "
        "comparisons stay blank; they are not treated as zero.\n\n"
        + "\n".join(rows)
        + "\n"
    )


def _contrib_cell(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{_opt_change_pp(value)} ({_opt_bps(value)})"


def _margin_change_block(view: DriversView) -> str:
    if not view.gross_margin_contribution:
        return ""
    rows = [
        "| Fiscal year | Δgross margin | −Δ(SG&A/revenue) | −Δ(impairment/revenue) | −Δ(other operating items/revenue) | Reconstructed sum | Reported operating-margin change | Residual |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    present = False
    for index, label in enumerate(view.labels):
        gm = (
            None
            if view.gross_margin_contribution is None
            else view.gross_margin_contribution[index]
        )
        if gm is None and (
            view.reported_operating_margin_change is None
            or view.reported_operating_margin_change[index] is None
        ):
            continue
        present = True
        rows.append(
            "| {label} | {gm} | {sga} | {imp} | {other} | {recon} | {reported} | {resid} |".format(
                label=label,
                gm=_contrib_cell(gm),
                sga=_contrib_cell(
                    None
                    if view.sga_ratio_contribution is None
                    or index >= len(view.sga_ratio_contribution)
                    else view.sga_ratio_contribution[index]
                ),
                imp=_contrib_cell(
                    None
                    if view.impairment_ratio_contribution is None
                    or index >= len(view.impairment_ratio_contribution)
                    else view.impairment_ratio_contribution[index]
                ),
                other=_contrib_cell(
                    None
                    if view.other_operating_ratio_contribution is None
                    or index >= len(view.other_operating_ratio_contribution)
                    else view.other_operating_ratio_contribution[index]
                ),
                recon=_contrib_cell(
                    None
                    if view.reconstructed_contribution_sum is None
                    or index >= len(view.reconstructed_contribution_sum)
                    else view.reconstructed_contribution_sum[index]
                ),
                reported=_contrib_cell(
                    None
                    if view.reported_operating_margin_change is None
                    else view.reported_operating_margin_change[index]
                ),
                resid=_opt_change_pp(
                    None
                    if view.contribution_residual is None
                    or index >= len(view.contribution_residual)
                    else view.contribution_residual[index]
                ),
            )
        )
    if not present:
        return ""
    return (
        "Signed operating-margin contributions are Δgross margin, "
        "−Δ(SG&A/revenue), −Δ(impairment or asset-related charges/revenue), "
        "and −Δ(other reported operating items/revenue). Each term is "
        "calculated from unrounded ratios. Percentage points are the ratio "
        "change × 100; basis points are the same unrounded value × 10,000. "
        "Displayed figures are rounded after the calculation. A rise in an "
        "expense ratio is a negative contribution. Residual is reported "
        "operating-margin change minus the reconstructed contribution sum. "
        "Missing adjacent comparisons stay blank; they are not treated as "
        "zero.\n\n"
        + "\n".join(rows)
        + "\n"
    )


def _footprint_block(view: DriversView) -> str:
    if not view.footprint_store_effect:
        return ""
    rows = [
        "| Fiscal year | Store-count effect | Intensity effect | Interaction | Reconstructed revenue change | Residual |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    present = False
    for index, label in enumerate(view.labels):
        if view.footprint_store_effect[index] is None:
            continue
        present = True
        rows.append(
            "| {label} | {store} | {inten} | {ix} | {recon} | {resid} |".format(
                label=label,
                store=_opt_money(view, view.footprint_store_effect[index]),
                inten=_opt_money(
                    view,
                    None
                    if view.footprint_intensity_effect is None
                    else view.footprint_intensity_effect[index],
                ),
                ix=_opt_money(
                    view,
                    None
                    if view.footprint_interaction is None
                    else view.footprint_interaction[index],
                ),
                recon=_opt_money(
                    view,
                    None
                    if view.footprint_reconstructed_change is None
                    else view.footprint_reconstructed_change[index],
                ),
                resid=_opt_money(
                    view,
                    None
                    if view.footprint_residual is None
                    else view.footprint_residual[index],
                ),
            )
        )
    if not present:
        return ""
    return (
        "Company-wide revenue equals store count times company-wide revenue per "
        "store. The adjacent change uses prior intensity on the store-count "
        "change, prior store count on the intensity change, and an explicit "
        "interaction. Company-wide revenue per store includes non-store revenue "
        "and is an intensity proxy, not store productivity. The store-count term "
        "is an arithmetic allocation, not measured new-store revenue.\n\n"
        + "\n".join(rows)
        + "\n"
    )


def _geo_reconstruction_block(view: DriversView) -> str:
    if not view.geo_component_revenue or not view.geo_residual:
        return ""
    level_rows = [
        "| Fiscal year | Americas | China Mainland | Rest of World | Reconstructed | Reported | Residual |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, label in enumerate(view.labels):
        comps = view.geo_component_revenue[index]
        level_rows.append(
            "| {label} | {am} | {cn} | {rw} | {rec} | {rep} | {res} |".format(
                label=label,
                am=_opt_money(view, comps.get("americas")),
                cn=_opt_money(view, comps.get("china_mainland")),
                rw=_opt_money(view, comps.get("rest_of_world")),
                rec=_opt_money(
                    view,
                    None
                    if view.geo_reconstructed_revenue is None
                    else view.geo_reconstructed_revenue[index],
                ),
                rep=_opt_money(
                    view,
                    None
                    if view.geo_reported_revenue is None
                    else view.geo_reported_revenue[index],
                ),
                res=_opt_money(
                    view,
                    None if view.geo_residual is None else view.geo_residual[index],
                ),
            )
        )
    change_rows = [
        "| Fiscal year | Americas change | China Mainland change | Rest of World change | Americas growth contribution | China Mainland growth contribution | Rest of World growth contribution | Residual |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    has_change = False
    if view.geo_contribution_amounts:
        for index, label in enumerate(view.labels):
            amounts = view.geo_contribution_amounts[index]
            if all(value is None for value in amounts.values()):
                continue
            has_change = True
            contrib = view.geo_contributions[index]
            change_rows.append(
                "| {label} | {am} | {cn} | {rw} | {amg} | {cng} | {rwg} | {res} |".format(
                    label=label,
                    am=_opt_money(view, amounts.get("americas")),
                    cn=_opt_money(view, amounts.get("china_mainland")),
                    rw=_opt_money(view, amounts.get("rest_of_world")),
                    amg=_opt_pp(contrib.get("americas")),
                    cng=_opt_pp(contrib.get("china_mainland")),
                    rwg=_opt_pp(contrib.get("rest_of_world")),
                    res=_opt_money(
                        view,
                        None
                        if view.geo_contribution_residual is None
                        else view.geo_contribution_residual[index],
                    ),
                )
            )
    body = (
        "Consolidated revenue is reconstructed from the geographic components. "
        "Residuals are the reconstructed total minus reported revenue. Growth "
        "contributions are an arithmetic split of reported-currency revenue "
        "change and are not organic or constant-currency growth.\n\n"
        + "\n".join(level_rows)
        + "\n"
    )
    if has_change:
        body += "\n" + "\n".join(change_rows) + "\n"
    return body


def _max_abs(values: tuple[float | None, ...] | None) -> float | None:
    known = [abs(value) for value in (values or ()) if value is not None]
    if not known:
        return None
    return max(known)


def _residual_conclusion(view: DriversView) -> str:
    parts: list[str] = []
    for name, series, money in (
        ("component operating-margin identity", view.operating_margin_residual, False),
        ("component operating-margin contributions", view.contribution_residual, False),
        ("operating-profit amount bridge", view.operating_profit_change_residual, True),
        ("geographic reconstruction", view.geo_residual, True),
        ("geographic growth-contribution", view.geo_contribution_residual, True),
        ("store-count times company-wide revenue per store", view.footprint_residual, True),
    ):
        largest = _max_abs(series)
        if largest is None:
            parts.append(f"{name} has no adjacent comparison in the available history")
        elif largest < (1e-8 if not money else 1e-4):
            parts.append(f"{name} residual is {largest:.6g}")
        else:
            parts.append(f"{name} residual is {largest:.6g} and remains visible")
    return (
        "Residuals are computed from the validated reconstructions. "
        + "; ".join(parts)
        + ". Sales-per-square-foot productivity and mix, markdowns, freight, "
        "costs, or leverage remain unestablished."
    )


def _assessment_block(view: DriversView) -> str:
    if not view.assessments:
        return ""
    rows = [
        "| Relationship | Kind | Residual | Stability | Contradictions | Result |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in view.assessments:
        kind = _KIND_LABELS.get(item.kind, item.kind.replace("_", " "))
        rows.append(
            "| {name} | {kind} | {resid} | {stable} | {contra} | {result} |".format(
                name=_research_safe(item.name),
                kind=_research_safe(kind),
                resid=_research_safe(item.residual),
                stable=_research_safe(item.stability),
                contra=_research_safe(item.contradictions),
                result="established" if item.established else "unestablished",
            )
        )
    body = "\n".join(rows) + "\n"
    lowered = body.lower()
    for term in _FORBIDDEN_RESEARCH:
        if term in lowered:
            raise ValueError(f"Drivers assessment prose contains {term!r}")
    return (
        "Each material relationship is tested for direction, magnitude, "
        "reconstruction, residual, stability across periods, contradictions, "
        "and disclosure support.\n\n"
        + body
    )


def _margin_source_note(view: DriversView, latest: int) -> str:
    if margin_reconstruction_complete(view, latest):
        detail = "Signed identity only. Management estimates are not mixed into this bridge."
    else:
        detail = (
            "Partial signed decomposition; a residual remains. "
            "Management estimates are not mixed into this bridge."
        )
    return (
        f"Source: {view.display_name} BAV income statement.\n"
        + detail
    )


def _headline_paragraph(view: DriversView, selection: ResearchSelection) -> str:
    latest = latest_growth_index(view)
    label = view.labels[latest]
    rev_g = view.revenue_growth[latest] if latest < len(view.revenue_growth) else None
    op_change = operating_profit_change(view, latest)
    change = (
        f"In {label}, {view.display_name} revenue grew {_pct(rev_g)}."
        if rev_g is not None
        else f"In {label}, {view.display_name} reported results are reconstructed from the available statements."
    )
    if op_change is not None:
        change += f" Operating profit changed by {_money_view(view, op_change)}"
        if op_change < 0 and rev_g is not None and rev_g > 0:
            change += ", so growth did not preserve the prior profit level"
        change += "."
    explanation = ""
    if selection.is_principal("operating_margin_bridge"):
        om = (
            None
            if view.reported_operating_margin_change is None
            else view.reported_operating_margin_change[latest]
        )
        complete = margin_reconstruction_complete(view, latest)
        if om is not None and om < 0:
            explanation = (
                " Margin compression is the strongest supported explanation of the "
                "weaker profit outcome."
                if complete
                else (
                    " Margin compression is the material reported outcome; "
                    "disclosed components explain it only in part and a residual remains."
                )
            )
        elif om is not None and om > 0:
            explanation = (
                " An accounting-margin expansion reconstructs the stronger profit outcome."
                if complete
                else (
                    " Operating margin expanded; disclosed components provide a "
                    "partial explanation and a residual remains."
                )
            )
        else:
            explanation = (
                " The latest operating-margin identity reconstructs the profit movement."
                if complete
                else (
                    " The latest operating-margin movement is only partly explained "
                    "by disclosed components."
                )
            )
    if selection.is_principal("geographic_localization"):
        conditions = geographic_claim_conditions(view, latest)
        if conditions.revenue_offset is not None and conditions.consolidated_profit_weaker:
            explanation += (
                " International revenue offset did not prevent consolidated profit "
                "deterioration."
            )
        elif conditions.revenue_offset is not None:
            explanation += " Geographic evidence localizes where revenue changed."
    if selection.is_principal("footprint_intensity"):
        explanation += (
            " Store-count growth outpaced company-wide revenue, which is the "
            "distinct available growth comparison."
        )
    if selection.is_principal("cash_conversion"):
        explanation += (
            " Cash conversion is the material available explanation of the latest outcome."
        )
    unresolved = (
        " The economic mechanism remains independently unresolved."
        if selection.is_principal("operating_margin_bridge")
        or selection.is_principal("geographic_localization")
        else ""
    )
    return change + explanation + unresolved


def _growth_argument(view: DriversView, latest: int, *, with_figure: bool) -> list[str]:
    store_g = view.store_growth[latest] if latest < len(view.store_growth) else None
    rev_g = view.revenue_growth[latest] if latest < len(view.revenue_growth) else None
    intensity = None
    if latest > 0 and latest < len(view.revenue_per_store) and view.revenue_per_store:
        prior = view.revenue_per_store[latest - 1]
        current = view.revenue_per_store[latest]
        if prior:
            intensity = current / prior - 1.0
    store_term = (
        None
        if view.footprint_store_effect is None
        else view.footprint_store_effect[latest]
    )
    first = (
        f"Store expansion outpaced company-wide revenue in {view.labels[latest]}"
        + (
            f": company-operated stores rose {_pct(store_g)} while consolidated "
            f"revenue rose {_pct(rev_g)}"
            if store_g is not None and rev_g is not None
            else ""
        )
    )
    if intensity is not None and intensity < 0:
        first += f", so company-wide revenue per period-end store fell {_pct(abs(intensity))}"
    first += (
        ". Store count is an operating KPI. Revenue per store is a proxy that "
        "includes non-store revenue and is not store productivity."
    )
    if store_term is not None:
        first += (
            f" The {_money_view(view, store_term)} store-count term in the "
            "footprint identity is an arithmetic allocation, not measured "
            "new-store revenue."
        )
    paragraphs = [first]
    if with_figure:
        paragraphs.append(
            "![Did store-count growth outpace consolidated revenue growth?](../figures/drivers/growth.png)"
        )
        paragraphs.append(
            "The paired growth rates show the latest divergence without connecting "
            "comparable-sales observations. Opening dates, mix, digital revenue and "
            "an unequal-week comparison can produce the same pattern."
        )
    else:
        paragraphs.append(
            "Opening dates, mix, digital revenue and an unequal-week comparison can "
            "produce the same pattern without weaker store productivity."
        )
    return paragraphs


def _geography_argument(view: DriversView, latest: int, *, with_figure: bool) -> list[str]:
    conditions = geographic_claim_conditions(view, latest)
    offset_sentence = _revenue_offset_sentence(conditions.revenue_offset)
    profit = (
        {}
        if view.geo_profit_changes is None
        else view.geo_profit_changes[latest]
    )
    if conditions.revenue_offset == OFFSET_GREATER:
        first = (
            "International revenue more than offset the Americas decline. "
            + offset_sentence
        )
    elif conditions.revenue_offset == OFFSET_EXACT:
        first = (
            "International revenue exactly offset the Americas decline. "
            + offset_sentence
        )
    elif conditions.revenue_offset == OFFSET_PARTIAL:
        first = (
            "International revenue only partially offset the Americas decline. "
            + offset_sentence
        )
    else:
        first = (
            offset_sentence
            or "Geographic contributions localize where revenue and profit changed."
        )
    if conditions.consolidated_profit_weaker:
        bits = []
        if profit.get("americas") is not None:
            bits.append(f"Americas operating profit {_opt_money(view, profit.get('americas'))}")
        if conditions.reconciling is not None and conditions.corporate_burden_increased:
            bits.append(
                f"corporate/unallocated items {_opt_money(view, conditions.reconciling)}"
            )
        if bits:
            first += " " + " and ".join(bits) + " left a weaker consolidated profit outcome."
        elif conditions.americas_profit_declined:
            first += " The Americas profit decline left a weaker consolidated profit outcome."
        else:
            first += " Consolidated operating profit was weaker."
        if (
            conditions.americas_profit_declined
            and conditions.corporate_burden_increased
            and conditions.consolidated_profit is not None
        ):
            first += (
                f" Those changes reconcile to {_opt_money(view, conditions.consolidated_profit, 3)} "
                "and show an Americas profit decline and higher corporate/unallocated burden."
            )
    first += (
        " This is reported segment evidence and arithmetic localization, "
        "not a causal attribution or organic-growth claim."
    )
    paragraphs = [first]
    if with_figure:
        paragraphs.append(
            f"![{_geography_figure_alt(conditions)}](../figures/drivers/geography.png)"
        )
        paragraphs.append(
            "The aligned panels keep revenue and profit on separate scales and "
            "retain the corporate reconciliation on the profit side. Currency, mix, "
            "calendar effects and cost allocation remain alternatives."
        )
    return paragraphs


def _margin_argument(
    view: DriversView,
    latest: int,
    *,
    with_figure: bool,
    include_attribution: bool,
) -> list[str]:
    om = (
        None
        if view.reported_operating_margin_change is None
        else view.reported_operating_margin_change[latest]
    )
    gm = (
        None
        if view.gross_margin_contribution is None
        else view.gross_margin_contribution[latest]
    )
    sga = (
        None
        if view.sga_ratio_contribution is None
        or latest >= len(view.sga_ratio_contribution)
        else view.sga_ratio_contribution[latest]
    )
    complete = margin_reconstruction_complete(view, latest)
    lead = (
        f"{view.labels[latest]} operating margin moved from "
        f"{_pct(view.operating_margin[latest - 1], 1)} to "
        f"{_pct(view.operating_margin[latest], 1)}"
        + (f", {_opt_change_pp(om)}" if om is not None else "")
        + " using unrounded ratios."
    )
    direction = component_direction_phrase(gm, sga)
    if complete and direction:
        lead += (
            f" {direction[0].upper()}{direction[1:]} account for "
            "the reported operating-margin change as an identity."
        )
    elif direction:
        lead += (
            f" {direction[0].upper()}{direction[1:]} are the disclosed "
            "component contributions; they do not fully reconstruct the "
            "reported change and a residual remains."
        )
    elif gm is not None or sga is not None:
        lead += (
            " Disclosed components provide only a partial explanation; "
            "a residual remains."
        )
    lead += (
        " This is an identity and signed decomposition. It does not "
        "identify a price, mix or cost mechanism."
    )
    paragraphs = [lead]
    latest_period = view.periods[latest]
    attrs = [item for item in view.attributions if item.period == latest_period]
    if include_attribution and attrs:
        quantified = next((item for item in attrs if item.approximate_amount), None)
        locators = "; ".join(
            f"{item.source_file}, {item.page_reference}" for item in attrs
        )
        if quantified is not None:
            paragraphs.append(
                "Management attributes the latest-year pressure, including "
                f"{quantified.approximate_amount} of gross-profit reduction "
                f"({locators}). The amount is retained as management's "
                "attributed counterfactual estimate; it is not an independently "
                "verified causal estimate and is not inserted into the accounting bridge."
            )
        else:
            paragraphs.append(
                "Management attributes the latest-year pressure in source-bound "
                f"commentary ({locators}). The attribution is preserved with its "
                "locator and is not inserted into the accounting bridge."
            )
    if with_figure:
        alt = (
            "Which accounting components reconstruct the latest operating-margin change?"
            if complete
            else (
                "Which disclosed accounting components partly explain "
                "the latest operating-margin change?"
            )
        )
        paragraphs.append(f"![{alt}](../figures/drivers/margin.png)")
    return paragraphs


def _cash_argument(view: DriversView, latest: int, *, with_figure: bool) -> list[str]:
    cfo = None if view.cfo is None else view.cfo[latest]
    ni = None if view.net_income is None else view.net_income[latest]
    prior_cfo = None if view.cfo is None or latest < 1 else view.cfo[latest - 1]
    prior_ni = None if view.net_income is None or latest < 1 else view.net_income[latest - 1]
    cfo_change = None if view.cfo_change is None else view.cfo_change[latest]
    remainder = None if view.cfo_unexplained is None else view.cfo_unexplained[latest]
    conversion = None if cfo is None or ni in (None, 0) else cfo / ni
    prior_conversion = (
        None if prior_cfo is None or prior_ni in (None, 0) else prior_cfo / prior_ni
    )
    first = (
        f"Reported CFO moved from {_opt_money(view, prior_cfo)} to {_opt_money(view, cfo)} "
        f"while net income moved from {_opt_money(view, prior_ni)} to {_opt_money(view, ni)}"
    )
    if conversion is not None and prior_conversion is not None:
        first += f". CFO/net income moved from {prior_conversion:.2f} to {conversion:.2f}"
    if cfo_change is not None:
        ni_change = None if view.net_income_change is None else view.net_income_change[latest]
        first += (
            f". The cash change of {_opt_money(view, cfo_change)} is larger than "
            "the earnings change"
            if ni_change is not None and cfo_change < ni_change
            else f". Cash from operations changed by {_opt_money(view, cfo_change)}"
        )
    first += (
        ". These are reported amounts and derived diagnostics, not an "
        "earnings-quality judgment or a finding of manipulation."
    )
    if remainder is not None:
        first += (
            " The available operating-section component changes do not explain "
            f"the whole CFO movement; the signed unexplained remainder is "
            f"{_opt_money(view, remainder, 3)}."
        )
    paragraphs = [first]
    if with_figure:
        paragraphs.append(
            "![Did reported earnings continue to translate into operating cash flow?](../figures/drivers/cash.png)"
        )
    return paragraphs


def _history_table(view: DriversView) -> str:
    include_stores = bool(view.stores) and len(view.stores) == len(view.periods)
    headers = ["Fiscal year", "Period ended", "Revenue", "Operating profit", "Operating margin"]
    aligns = [" --- ", " --- ", " ---: ", " ---: ", " ---: "]
    if include_stores:
        headers.append("Company-operated stores")
        aligns.append(" ---: ")
    rows = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(aligns) + "|",
    ]
    for index, period in enumerate(view.periods):
        cells = [
            view.labels[index],
            date_text(period),
            _money_view(view, view.revenue[index]),
            _money_view(view, view.operating_profit[index]),
            _pct(view.operating_margin[index], 1) if index < len(view.operating_margin) else "n/a",
        ]
        if include_stores:
            cells.append(f"{view.stores[index]:.0f}")
        rows.append("| " + " | ".join(cells) + " |")
    return (
        "Historical levels used by the selected claims. Amounts are "
        f"{view.units}, shown in millions of {view.currency}.\n\n"
        + "\n".join(rows)
        + "\n"
    )


def _geo_profit_block(view: DriversView) -> str:
    if not view.geo_profit_changes:
        return ""
    rows = [
        "| Fiscal year | Americas | China Mainland | Rest of World | Corporate / unallocated | Consolidated | Residual |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    present = False
    for index, label in enumerate(view.labels):
        changes = view.geo_profit_changes[index]
        if all(value is None for value in changes.values()):
            continue
        present = True
        rows.append(
            "| {label} | {am} | {cn} | {rw} | {corp} | {cons} | {res} |".format(
                label=label,
                am=_opt_money(view, changes.get("americas")),
                cn=_opt_money(view, changes.get("china_mainland")),
                rw=_opt_money(view, changes.get("rest_of_world")),
                corp=_opt_money(
                    view,
                    None
                    if view.geo_reconciling_profit_change is None
                    else view.geo_reconciling_profit_change[index],
                ),
                cons=_opt_money(
                    view,
                    None
                    if view.geo_consolidated_profit_change is None
                    else view.geo_consolidated_profit_change[index],
                    3,
                ),
                res=_opt_money(
                    view,
                    None
                    if view.geo_profit_change_residual is None
                    else view.geo_profit_change_residual[index],
                ),
            )
        )
    if not present:
        return ""
    return (
        "Geographic operating-profit amount changes include corporate/"
        "unallocated items and reconcile to the consolidated change. This "
        "localizes the profit movement; it does not identify causes.\n\n"
        + "\n".join(rows)
        + "\n"
    )


def _compsales_block(view: DriversView) -> str:
    if not view.comparable_sales:
        return ""
    rows = [
        "| Fiscal year | Reported comparable sales | Population | Basis |",
        "| --- | ---: | --- | --- |",
    ]
    for point in view.comparable_sales:
        if point.period not in view.periods:
            continue
        rows.append(
            "| {label} | {pct} | {pop} | {basis} |".format(
                label=view.labels[view.periods.index(point.period)],
                pct=f"{point.percent:.0f}%",
                pop=POPULATION_LABELS.get(point.population, point.population),
                basis=point.basis,
            )
        )
    if view.store_only_comparable_sales is not None:
        point = view.store_only_comparable_sales
        if point.period in view.periods:
            rows.append(
                "| {label} | {pct} | {pop} | {basis} |".format(
                    label=view.labels[view.periods.index(point.period)],
                    pct=f"{point.percent:.0f}%",
                    pop=POPULATION_LABELS.get(point.population, point.population),
                    basis=point.basis,
                )
            )
    return (
        "Comparable-sales observations are retained as period-specific reported "
        "KPIs. Changing channel definitions and calendars prevent a connected "
        "trend; the observations cannot be joined as one deceleration series. "
        "Revenue growth minus comparable sales is not labeled new-store "
        "contribution.\n\n"
        + "\n".join(rows)
        + "\n"
    )


def _cash_block(view: DriversView) -> str:
    if view.cfo is None or view.net_income is None:
        return ""
    rows = [
        "| Fiscal year | CFO | Net income | CFO change | Component-change sum | Signed remainder | Inventory | Inventory change | CF inventory line |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    present = False
    for index, label in enumerate(view.labels):
        if view.cfo[index] is None and view.net_income[index] is None:
            continue
        present = True
        rows.append(
            "| {label} | {cfo} | {ni} | {chg} | {comp} | {rem} | {inv} | {ichg} | {cfinv} |".format(
                label=label,
                cfo=_opt_money(view, view.cfo[index]),
                ni=_opt_money(view, view.net_income[index]),
                chg=_opt_money(
                    view, None if view.cfo_change is None else view.cfo_change[index]
                ),
                comp=_opt_money(
                    view,
                    None
                    if view.cfo_component_sum is None
                    else view.cfo_component_sum[index],
                ),
                rem=_opt_money(
                    view,
                    None if view.cfo_unexplained is None else view.cfo_unexplained[index],
                    3,
                ),
                inv=_opt_money(view, None if view.inventory is None else view.inventory[index]),
                ichg=_opt_money(
                    view,
                    None if view.inventory_change is None else view.inventory_change[index],
                ),
                cfinv=_opt_money(
                    view,
                    None
                    if view.cf_inventory_adjustment is None
                    else view.cf_inventory_adjustment[index],
                ),
            )
        )
    if not present:
        return ""
    return (
        "CFO and net income are reported amounts. The component-change sum is "
        "the adjacent change in supported operating-section cash-flow lines. "
        "Total cash change, cash balances, investing and financing flows, and "
        "overlapping aggregates are excluded. The signed remainder is reported "
        "CFO change minus that sum and is not a complete CFO bridge. "
        "Balance-sheet inventory change is not a cash-flow-statement "
        "reconciliation. An incomplete explanation does not block the reported "
        "CFO movement.\n\n"
        + "\n".join(rows)
        + "\n"
    )


def _attribution_block(view: DriversView) -> str:
    if not view.attributions:
        return ""
    rows = [
        "| Period | Theme | Attribution | Approximate amount | Source | Section |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in view.attributions:
        label = (
            view.labels[view.periods.index(item.period)]
            if item.period in view.periods
            else item.period.isoformat()
        )
        rows.append(
            "| {label} | {theme} | {text} | {amt} | {src} | {sec} |".format(
                label=label,
                theme=item.theme.replace("_", " "),
                text=item.text,
                amt=item.approximate_amount or "qualitative",
                src=f"{item.source_file}, {item.page_reference}",
                sec=item.section,
            )
        )
    return (
        "Management attributions are source-bound disclosures. Approximate "
        "wording, period, counterfactual scope and locators are retained. The "
        "amounts are not independently verified and are not mixed with "
        "reconciled accounting-bridge components.\n\n"
        + "\n".join(rows)
        + "\n"
    )


def _selection_block(view: DriversView) -> str:
    selection = _completed_selection(view)
    rows = [
        "| Question | Decision | Reason | Strongest supported conclusion | Unresolved requirement |",
        "| --- | --- | --- | --- | --- |",
    ]
    by_id = {item.identifier: item for item in selection.questions}
    for decision in selection.decisions:
        question = by_id.get(decision.identifier)
        rows.append(
            "| {qid} | {action} | {reason} | {conc} | {need} |".format(
                qid=decision.identifier.replace("_", " "),
                action=decision.action,
                reason=_research_safe(decision.reason),
                conc="" if question is None else _research_safe(question.strongest_conclusion),
                need="" if question is None else _research_safe(question.unresolved_requirement),
            )
        )
    return (
        "Selection records why candidates were selected, combined, retained, "
        "deferred or excluded. There is no factor quota or numerical confidence "
        "score.\n\n"
        + "\n".join(rows)
        + "\n"
    )


def _principal_title(view: DriversView, identifier: str, latest: int) -> str:
    if identifier == "operating_margin_bridge":
        om = (
            None
            if view.reported_operating_margin_change is None
            or latest >= len(view.reported_operating_margin_change)
            else view.reported_operating_margin_change[latest]
        )
        if om is not None and om < 0:
            return "Operating-margin compression"
        if om is not None and om > 0:
            return "Operating-margin expansion"
        return "Operating-margin change"
    if identifier == "geographic_localization":
        conditions = geographic_claim_conditions(view, latest)
        if conditions.revenue_offset is not None and (
            conditions.americas_profit_declined or conditions.consolidated_profit_weaker
        ):
            return "Geographic growth and profit divergence"
        return "Geographic localization"
    if identifier == "footprint_intensity":
        return "Footprint and expansion economics"
    if identifier == "cash_conversion":
        return "Cash conversion"
    return identifier.replace("_", " ").capitalize()


def _principal_paragraphs(
    view: DriversView, identifier: str, latest: int, selection: ResearchSelection
) -> list[str]:
    figure_ids = set(selection.figure_ids)
    if identifier == "operating_margin_bridge":
        return _margin_argument(
            view,
            latest,
            with_figure="margin" in figure_ids,
            include_attribution=selection.is_principal("operating_margin_bridge")
            or selection.is_secondary("operating_margin_bridge"),
        )
    if identifier == "geographic_localization":
        return _geography_argument(view, latest, with_figure="geography" in figure_ids)
    if identifier == "footprint_intensity":
        return _growth_argument(view, latest, with_figure="growth" in figure_ids)
    if identifier == "cash_conversion":
        return _cash_argument(view, latest, with_figure="cash" in figure_ids)
    return []


def _secondary_paragraphs(view: DriversView, identifier: str, latest: int) -> list[str]:
    if identifier == "cash_conversion":
        return _cash_argument(view, latest, with_figure=False)
    if identifier == "geographic_localization":
        return _geography_argument(view, latest, with_figure=False)
    if identifier == "footprint_intensity":
        return _growth_argument(view, latest, with_figure=False)
    if identifier == "operating_margin_bridge":
        return _margin_argument(view, latest, with_figure=False, include_attribution=True)
    return []


def _growth_magnitude_sentence(view: DriversView) -> str:
    latest = latest_growth_index(view)
    store_g = view.store_growth[latest] if latest < len(view.store_growth) else None
    rev_g = view.revenue_growth[latest] if latest < len(view.revenue_growth) else None
    if store_g is None or rev_g is None:
        return ""
    return (
        f"In {view.labels[latest]}, company-operated stores grew {_pct(store_g)} "
        f"while consolidated revenue grew {_pct(rev_g)}.\n\n"
    )


def render_drivers_markdown(view: DriversView) -> str:
    selection = _completed_selection(view)
    latest = latest_growth_index(view)
    blocks = [drivers_heading(view.display_name), ""]
    blocks.append(_headline_paragraph(view, selection))
    for index, identifier in enumerate(selection.principal_ids, start=1):
        blocks.append("")
        blocks.append(f"## {index}. {_principal_title(view, identifier, latest)}")
        blocks.append("")
        blocks.extend(_principal_paragraphs(view, identifier, latest, selection))
    if selection.secondary_ids:
        blocks.append("")
        blocks.append(SECONDARY_HEADING)
        blocks.append("")
        named = []
        for identifier in selection.secondary_ids:
            title = _principal_title(view, identifier, latest)
            paragraphs = _secondary_paragraphs(view, identifier, latest)
            if not paragraphs:
                continue
            named.append(f"{title}: {paragraphs[0]}")
        blocks.extend(named)
    blocks.append("")
    blocks.append(APPENDIX_HEADING)
    blocks.append("")
    blocks.append("### Selected claims")
    blocks.append("")
    blocks.append(_selection_block(view))
    if (
        view.stores
        or view.comparable_sales
        or view.footprint_store_effect
        or selection.question("footprint_intensity")
        or selection.question("comparable_sales")
    ):
        blocks.append("### Growth evidence")
        blocks.append("")
        blocks.append(_growth_magnitude_sentence(view))
        blocks.append(_history_table(view))
        blocks.append(_footprint_block(view))
        blocks.append(_compsales_block(view))
        calendar = calendar_limitation(view).strip()
        if calendar:
            blocks.append(
                "The extra-week comparison is retained as a period-specific limit."
            )
            blocks.append("")
            blocks.append(calendar)
            blocks.append("")
    if view.geo_identities or view.geo_profit_changes:
        blocks.append("### Geographic evidence")
        blocks.append("")
        blocks.append(_geo_reconstruction_block(view))
        blocks.append(_geo_profit_block(view))
    if view.gross_margin or view.gross_margin_contribution or view.attributions:
        blocks.append("### Margin evidence")
        blocks.append("")
        blocks.append(_margin_component_block(view))
        blocks.append(_amount_bridge_block(view))
        blocks.append(_margin_change_block(view))
        blocks.append(_attribution_block(view))
    if view.cfo is not None or view.net_income is not None:
        blocks.append("### Cash evidence")
        blocks.append("")
        blocks.append(_cash_block(view))
    blocks.append("### Relationship records")
    blocks.append("")
    blocks.append(_assessment_block(view))
    blocks.append(_residual_conclusion(view))
    blocks.append("### Sources and methodology")
    blocks.append("")
    blocks.append(
        "Numbers come from the existing verified BAV calculation path. "
        "Reported facts, identities, proxies, localizations, management "
        "attributions and unresolved questions are kept distinct. Exact "
        "reconstruction does not establish causation. Missing observations "
        "stay unavailable; an explicit zero remains zero. Fiscal-year labels "
        "follow the issuer mapping and are not derived from the calendar year "
        "of the period-end date."
    )
    body = "\n".join(part for part in blocks if part is not None)
    lowered = body.lower()
    for term in _FORBIDDEN_RESEARCH:
        if term in lowered:
            raise ValueError(f"Drivers prose contains {term!r}")
    return body if body.endswith("\n") else body + "\n"


def _figure_period_label(view: DriversView, index: int) -> str:
    return f"{view.labels[index]}\n{view.periods[index].strftime('%-d %b %Y')}"


def plot_growth(view: DriversView, path: Path, style: ResearchStyle) -> None:
    fig, ax = new_figure(style)
    indexes = [
        i
        for i in range(len(view.periods))
        if view.revenue_growth[i] is not None and view.store_growth[i] is not None
    ]
    labels = []
    for index in indexes:
        label = _figure_period_label(view, index)
        if view.fifty_three_week_period == view.periods[index]:
            label = f"{label}\n53-week"
        labels.append(label)
    x = list(range(len(indexes)))
    width = 0.36
    revenue = [view.revenue_growth[i] * 100 for i in indexes]
    stores = [view.store_growth[i] * 100 for i in indexes]
    ax.bar(
        [i - width / 2 for i in x],
        revenue,
        width=width,
        color=style.series_color(0),
        label="Consolidated revenue growth",
    )
    ax.bar(
        [i + width / 2 for i in x],
        stores,
        width=width,
        color=style.series_color(1),
        label="Company-operated store-count growth",
    )
    ax.set_xticks(x, labels)
    ax.set_ylabel("Percent")
    ax.axhline(0, color=style.black, linewidth=0.8)
    ax.legend(loc="upper right")
    finish_figure(
        fig,
        ax,
        style,
        "Revenue growth versus store-count growth",
        f"Source: {view.display_name} BAV income statement and company-operated store counts.\n"
        "Comparable-sales observations are kept separate and are not connected here.",
        path,
    )


def _style_axis(ax, style: ResearchStyle) -> None:
    ax.set_facecolor(style.white)
    ax.tick_params(colors=style.black, width=0.8)
    for spine in ax.spines.values():
        spine.set_color(style.black)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.axhline(0, color=style.black, linewidth=0.8)


def plot_geography(view: DriversView, path: Path, style: ResearchStyle) -> None:
    from matplotlib import pyplot as plt

    latest = latest_growth_index(view)
    identities = list(view.geo_identities)
    labels = [
        SEGMENT_LABELS.get(identity, identity.replace("_", " ").title())
        for identity in identities
    ]
    revenue = []
    profit = []
    for identity in identities:
        amounts = (
            {}
            if view.geo_revenue_amount_changes is None
            else view.geo_revenue_amount_changes[latest]
        )
        profits = (
            {}
            if view.geo_profit_changes is None
            else view.geo_profit_changes[latest]
        )
        revenue.append(
            None if amounts.get(identity) is None else _millions(amounts[identity])
        )
        profit.append(
            None if profits.get(identity) is None else _millions(profits[identity])
        )
    reconciling = (
        None
        if view.geo_reconciling_profit_change is None
        else view.geo_reconciling_profit_change[latest]
    )
    if reconciling is not None:
        labels.append("Corporate / unallocated")
        revenue.append(None)
        profit.append(_millions(reconciling))
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 4.8), dpi=150)
    fig.patch.set_facecolor(style.white)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.76, bottom=0.28, wspace=0.32)
    x = list(range(len(labels)))
    for ax, values, title, ylabel in (
        (axes[0], revenue, "Revenue change", f"{view.currency} millions"),
        (axes[1], profit, "Operating-profit change", f"{view.currency} millions"),
    ):
        _style_axis(ax, style)
        heights = [0.0 if value is None else value for value in values]
        colors = [
            style.white if value is None else style.series_color(index)
            for index, value in enumerate(values)
        ]
        edges = [style.white if value is None else style.black for value in values]
        ax.bar(x, heights, color=colors, edgecolor=edges, linewidth=0.4)
        ax.set_xticks(x, labels, rotation=25, ha="right")
        ax.set_title(title, loc="left", color=style.black, fontsize=style.label_pt)
        ax.set_ylabel(ylabel)
    fig.suptitle(
        f"{view.labels[latest]} geographic revenue and operating-profit change",
        x=0.10,
        ha="left",
        color=style.black,
        fontsize=style.title_pt,
        fontweight="regular",
    )
    finish_figure(
        fig,
        axes[0],
        style,
        "Revenue change",
        f"Source: {view.display_name} BAV geographic segment analysis.\n"
        "Separate scales. Corporate/unallocated items appear only in the profit panel.",
        path,
    )


def plot_margin(view: DriversView, path: Path, style: ResearchStyle) -> None:
    latest = latest_growth_index(view)
    series = [
        (view.gross_margin_contribution, "Gross margin"),
        (view.sga_ratio_contribution, "SG&A / revenue"),
        (view.impairment_ratio_contribution, "Impairment / revenue"),
        (view.other_operating_ratio_contribution, "Other operating items"),
    ]
    labels = []
    heights = []
    for values, label in series:
        if not values or latest >= len(values) or values[latest] is None:
            continue
        labels.append(label)
        heights.append(values[latest] * 100)
    reported = (
        None
        if view.reported_operating_margin_change is None
        or latest >= len(view.reported_operating_margin_change)
        else view.reported_operating_margin_change[latest]
    )
    fig, ax = new_figure(style)
    x = list(range(len(labels)))
    ax.bar(x, heights, color=[style.series_color(i) for i in x], width=0.6)
    if reported is not None:
        ax.axhline(
            reported * 100,
            color=style.black,
            linewidth=1.0,
            linestyle="--",
            label="Reported operating-margin change",
        )
        ax.legend(loc="best")
    ax.set_xticks(x, labels, rotation=15, ha="right")
    ax.set_ylabel("Percentage-point contribution")
    ax.axhline(0, color=style.black, linewidth=0.8)
    finish_figure(
        fig,
        ax,
        style,
        f"{view.labels[latest]} operating-margin bridge",
        _margin_source_note(view, latest),
        path,
    )


def plot_cash(view: DriversView, path: Path, style: ResearchStyle) -> None:
    indexes = [
        i
        for i in range(len(view.periods))
        if view.cfo is not None
        and view.net_income is not None
        and view.cfo[i] is not None
        and view.net_income[i] is not None
    ]
    if len(indexes) > 2:
        indexes = indexes[-2:]
    labels = [_figure_period_label(view, i) for i in indexes]
    x = list(range(len(indexes)))
    width = 0.36
    fig, ax = new_figure(style)
    ax.bar(
        [i - width / 2 for i in x],
        [_millions(view.cfo[i]) for i in indexes],
        width=width,
        color=style.series_color(0),
        label="Cash from operations",
    )
    ax.bar(
        [i + width / 2 for i in x],
        [_millions(view.net_income[i]) for i in indexes],
        width=width,
        color=style.series_color(1),
        label="Net income",
    )
    ax.set_xticks(x, labels)
    ax.set_ylabel(f"Millions of {view.currency}")
    ax.axhline(0, color=style.black, linewidth=0.8)
    ax.legend(loc="best")
    finish_figure(
        fig,
        ax,
        style,
        "Cash from operations versus net income",
        f"Source: {view.display_name} BAV cash-flow and income statements.\n"
        "Diagnostic comparison only; not a manipulation finding or complete CFO explanation.",
        path,
    )


def write_placeholders(research_dir: Path, company: str) -> None:
    research_dir.mkdir(parents=True, exist_ok=True)
    for name in placeholder_filenames(company):
        (research_dir / name).write_bytes(b"")


_PLOT_BY_ID = {
    "growth": plot_growth,
    "geography": plot_geography,
    "margin": plot_margin,
    "cash": plot_cash,
}


def selected_figure_names(view: DriversView) -> tuple[str, ...]:
    selection = _completed_selection(view)
    names = []
    for identifier in selection.figure_ids:
        if identifier in _PLOT_BY_ID:
            names.append(f"{identifier}.png")
    return tuple(names)


def publish_completed_drivers(
    view: DriversView,
    output: Path,
    *,
    accent: str | None = None,
) -> DriversView:
    _completed_selection(view)
    style = apply_research_style(accent=accent)
    research_dir = output / "research"
    figures_dir = output / "figures" / "drivers"
    write_placeholders(research_dir, view.display_name)
    (research_dir / drivers_filename(view.display_name)).write_text(
        render_drivers_markdown(view), encoding="utf-8"
    )
    figures_dir.mkdir(parents=True, exist_ok=True)
    wanted = set(selected_figure_names(view))
    for existing in figures_dir.glob("*.png"):
        if existing.name not in wanted:
            existing.unlink()
    for name in wanted:
        identifier = name.removesuffix(".png")
        _PLOT_BY_ID[identifier](view, figures_dir / name, style)
    return view
