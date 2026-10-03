"""Classification-judgment rationale, consequence, and prompt ownership."""

from __future__ import annotations

from dataclasses import dataclass

CONSEQUENCE_PROMPT = (
    "Explain which reformulated balance(s) change under the alternative treatment "
    "and how that changes profitability/leverage interpretation."
)


@dataclass(frozen=True)
class ClassificationJudgmentTemplate:
    topic: str
    options: tuple[str, ...]
    model_rationale: str
    consequence_prompt: str
    model_consequence: str


CLASSIFICATION_JUDGMENT_TEMPLATES: dict[str, ClassificationJudgmentTemplate] = {
    "lease_liability_operating_vs_financing": ClassificationJudgmentTemplate(
        topic="Lease liability operating vs financing",
        options=("Operating Long-Term Liability", "Financial Liability"),
        model_rationale=(
            "The reference model keeps the liability in operating long-term liabilities "
            "under its current lease convention. Treating it as a financial liability is "
            "also defensible when the lease obligation is viewed as debt-like financing."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Operating-liability treatment lowers NOLA/NOA; financial-liability treatment "
            "raises Net Debt by the same balance. Implied equity is unchanged from this "
            "classification switch alone, but RNOA versus FLEV/Spread interpretation changes."
        ),
    ),
    "pension_obligation_operating_vs_financing": ClassificationJudgmentTemplate(
        topic="Pension obligation operating vs financing",
        options=("Operating Long-Term Liability", "Financial Liability"),
        model_rationale=(
            "The reference model keeps the obligation in operating long-term liabilities "
            "under its current employee-benefit convention. A financial-liability treatment "
            "is also defensible when the obligation is analyzed as debt-like funding."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Operating-liability treatment lowers NOLA/NOA; financial-liability treatment "
            "raises Net Debt by the same balance. Implied equity is unchanged from this "
            "classification switch alone, but RNOA versus FLEV/Spread interpretation changes."
        ),
    ),
    "short_term_investment_financial_vs_operating": ClassificationJudgmentTemplate(
        topic="Short-term investment operating vs financing",
        options=("Financial Asset", "Operating Working Capital Asset"),
        model_rationale=(
            "The reference model treats a generic short-term investment as a financial asset "
            "absent evidence that it is required for operations. Operating-WC treatment "
            "requires company-specific evidence that the balance is necessary for normal "
            "operations."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Financial-asset treatment lowers Net Debt; operating-WC treatment raises "
            "NOWC/NOA by the same balance. Implied equity is unchanged from this "
            "classification switch alone, but operating-capital and leverage metrics change."
        ),
    ),
    "associate_investment_operating_vs_financial": ClassificationJudgmentTemplate(
        topic="Equity-method investment operating vs financing",
        options=("Operating Long-Term Asset", "Financial Asset"),
        model_rationale=(
            "The reference model treats the investment as an operating long-term asset when "
            "it is viewed as strategically tied to the operating business. Financial-asset "
            "treatment is defensible when the holding is primarily non-operating/investment "
            "in nature."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Operating-asset treatment raises NOLA/NOA; financial-asset treatment lowers "
            "Net Debt by the same balance. Implied equity is unchanged from this "
            "classification switch alone, but RNOA and leverage interpretation change."
        ),
    ),
    "financial_asset_current_financial_vs_operating": ClassificationJudgmentTemplate(
        topic="Current financial asset: financial vs operating",
        options=("Financial Asset", "Operating Working Capital Asset"),
        model_rationale=(
            "The reference model treats a generically disclosed current financial "
            "instrument as a financial asset absent evidence that it is integral to "
            "normal operations or an operating hedge."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Financial-asset treatment lowers Net Debt; operating-WC treatment raises "
            "NOWC/NOA by the same balance. Implied equity is unchanged by the "
            "classification switch alone."
        ),
    ),
    "financial_asset_noncurrent_financial_vs_operating": ClassificationJudgmentTemplate(
        topic="Non-current financial asset: financial vs operating",
        options=("Financial Asset", "Operating Long-Term Asset"),
        model_rationale=(
            "The reference model treats a generically disclosed non-current financial "
            "instrument as a financial asset absent evidence that it is strategically "
            "or operationally required."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Financial-asset treatment lowers Net Debt; operating-LT treatment raises "
            "NOLA/NOA by the same balance. Implied equity is unchanged by the "
            "classification switch alone."
        ),
    ),
    "financial_liability_current_financial_vs_operating": ClassificationJudgmentTemplate(
        topic="Current financial liability: financial vs operating",
        options=("Financial Liability", "Operating Working Capital Liability"),
        model_rationale=(
            "The reference model treats a generically disclosed current financial "
            "instrument as a financial liability absent evidence that it is an "
            "operating payable or operating hedge."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Financial-liability treatment raises Net Debt; operating-WC-liability "
            "treatment lowers NOWC/NOA by the same balance. Implied equity is unchanged "
            "by the classification switch alone."
        ),
    ),
    "financial_liability_noncurrent_financial_vs_operating": ClassificationJudgmentTemplate(
        topic="Non-current financial liability: financial vs operating",
        options=("Financial Liability", "Operating Long-Term Liability"),
        model_rationale=(
            "The reference model treats a generically disclosed non-current financial "
            "instrument as a financial liability absent evidence that it is an "
            "operating long-term obligation or operating hedge."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Financial-liability treatment raises Net Debt; operating-LT-liability "
            "treatment lowers NOLA/NOA by the same balance. Implied equity is unchanged "
            "by the classification switch alone."
        ),
    ),
    "other_current_asset_operating_vs_financial": ClassificationJudgmentTemplate(
        topic="Other current asset: operating vs financial",
        options=("Operating Working Capital Asset", "Financial Asset"),
        model_rationale=(
            "The residual current-asset concept proves balance-sheet side and horizon "
            "but not whether the balance is operating working capital or a financial "
            "asset in economic substance."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Operating-WC treatment raises NOWC/NOA; financial-asset treatment lowers "
            "Net Debt by the same balance. Implied equity is unchanged by the "
            "classification switch alone."
        ),
    ),
    "other_noncurrent_asset_operating_vs_financial": ClassificationJudgmentTemplate(
        topic="Other non-current asset: operating vs financial",
        options=("Operating Long-Term Asset", "Financial Asset"),
        model_rationale=(
            "The residual non-current-asset concept proves balance-sheet side and "
            "horizon but not whether the balance is an operating long-term asset or a "
            "financial asset in economic substance."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Operating-LT treatment raises NOLA/NOA; financial-asset treatment lowers "
            "Net Debt by the same balance. Implied equity is unchanged by the "
            "classification switch alone."
        ),
    ),
    "other_current_liability_operating_vs_financial": ClassificationJudgmentTemplate(
        topic="Other current liability: operating vs financial",
        options=("Operating Working Capital Liability", "Financial Liability"),
        model_rationale=(
            "The residual current-liability concept proves balance-sheet side and "
            "horizon but not whether the balance is an operating working-capital "
            "liability or a financial liability in economic substance."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Operating-WC-liability treatment lowers NOWC/NOA; financial-liability "
            "treatment raises Net Debt by the same balance. Implied equity is unchanged "
            "by the classification switch alone."
        ),
    ),
    "other_noncurrent_liability_operating_vs_financial": ClassificationJudgmentTemplate(
        topic="Other non-current liability: operating vs financial",
        options=("Operating Long-Term Liability", "Financial Liability"),
        model_rationale=(
            "The residual non-current-liability concept proves balance-sheet side and "
            "horizon but not whether the balance is an operating long-term liability or "
            "a financial liability in economic substance."
        ),
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=(
            "Operating-LT-liability treatment lowers NOLA/NOA; financial-liability "
            "treatment raises Net Debt by the same balance. Implied equity is unchanged "
            "by the classification switch alone."
        ),
    ),
}
