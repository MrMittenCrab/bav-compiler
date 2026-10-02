"""Operating-CFO classification. A change_in_ substring is not enough."""

from __future__ import annotations

from core.data.interface import StandardizedFinancials

_CFO_CONCEPT_ALIASES = {
    "net_change_in_cash": "change_in_cash",
    "operating_cash_flow": "net_cash_from_operating_activities",
    "investing_cash_flow": "net_cash_from_investing_activities",
    "financing_cash_flow": "net_cash_from_financing_activities",
    "effect_of_exchange_rate_on_cash": "effect_of_fx_on_cash",
    "depreciation_amortization": "depreciation_and_amortization",
}
_CFO_EXCLUDED_CONCEPTS = frozenset(
    {
        "net_cash_from_operating_activities",
        "net_cash_from_investing_activities",
        "net_cash_from_financing_activities",
        "operating_cash_flow",
        "investing_cash_flow",
        "financing_cash_flow",
        "cash_generated_from_operations",
        "cash_beginning",
        "cash_ending",
        "change_in_cash",
        "net_change_in_cash",
        "effect_of_fx_on_cash",
        "effect_of_exchange_rate_on_cash",
        "capital_expenditures",
        "acquisition_net_of_cash_acquired",
        "other_investing_activities",
        "other_financing_activities",
        "others_net_investing",
        "others_net_financing",
        "proceeds_from_stock_based_compensation",
        "repurchase_of_common_stock",
        "shares_withheld_for_stock_based_compensation",
        "settlement_of_net_investment_hedges",
        "pretax_income",
    }
)
_CFO_OPERATING_ADJUSTMENT_HINTS = (
    "cash_flow_net_income",
    "deferred_income",
    "depreciation",
    "stock_based_compensation",
    "studio_obsolescence",
    "derecognition",
    "settlement_of_derivatives",
)
_CFO_NONOPERATING_HINTS = (
    "investing",
    "financing",
    "capital_expenditures",
    "payments_for_",
    "proceeds_from_",
    "dividends_paid",
    "bank_deposits",
    "repayment_of_",
    "repayments_of_",
    "repurchase_",
)
_CFO_OPERATING_CHANGE_SUBJECTS = (
    "inventor",
    "receivable",
    "payable",
    "accrued",
    "prepaid",
    "income_tax",
    "other_liabilit",
    "other_asset",
    "other_non_current",
    "lease_assets_and_liabilities",
    "unredeemed_gift_card",
    "accounts_payable",
)


def _normalize_cfo_concept(concept: str) -> str:
    return _CFO_CONCEPT_ALIASES.get(concept, concept)


def _is_cash_total_or_balance(concept: str) -> bool:
    canon = _normalize_cfo_concept(concept)
    if concept in _CFO_EXCLUDED_CONCEPTS or canon in _CFO_EXCLUDED_CONCEPTS:
        return canon in {
            "change_in_cash",
            "cash_beginning",
            "cash_ending",
        } or concept in {"change_in_cash", "net_change_in_cash", "cash_beginning", "cash_ending"}
    return canon in {"change_in_cash", "cash_beginning", "cash_ending"} or "change_in_cash" in concept


def _is_investing_or_financing(concept: str) -> bool:
    canon = _normalize_cfo_concept(concept)
    return any(hint in concept or hint in canon for hint in _CFO_NONOPERATING_HINTS)


def _is_overlapping_cfo_aggregate(concept: str) -> bool:
    canon = _normalize_cfo_concept(concept)
    return canon in {
        "net_cash_from_operating_activities",
        "cash_generated_from_operations",
        "pretax_income",
    } or concept in {
        "cash_generated_from_operations",
        "operating_cash_flow",
        "pretax_income",
    }


def _is_operating_working_capital_change(concept: str) -> bool:
    if "change_in_" not in concept and "change_in_" not in _normalize_cfo_concept(concept):
        return False
    if _is_cash_total_or_balance(concept):
        return False
    return any(token in concept for token in _CFO_OPERATING_CHANGE_SUBJECTS)


def _is_cfo_component(concept: str) -> bool:
    if concept in _CFO_EXCLUDED_CONCEPTS or _normalize_cfo_concept(concept) in _CFO_EXCLUDED_CONCEPTS:
        return False
    if _is_cash_total_or_balance(concept):
        return False
    if _is_investing_or_financing(concept):
        return False
    if _is_overlapping_cfo_aggregate(concept):
        return False
    if any(hint in concept for hint in _CFO_OPERATING_ADJUSTMENT_HINTS):
        return True
    return _is_operating_working_capital_change(concept)


def is_cfo_component(concept: str) -> bool:
    """Classify a cash-flow line as a supported operating CFO component.

    Operating identity and statement context control inclusion. A
    ``change_in_`` substring alone does not establish operating classification.
    Total cash changes, cash balances, investing/financing flows and
    overlapping aggregates are excluded.
    """
    return _is_cfo_component(concept)


def selected_cfo_concepts(financials: StandardizedFinancials) -> tuple[str, ...]:
    return tuple(
        item.concept
        for item in financials.cash_flow
        if _is_cfo_component(item.concept)
    )
