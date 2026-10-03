"""Gated opt-in normalization candidate handoff (Step 9M.2.4.1.1.1.68)."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from extractor.data.filing_json import load_extracted_filing
from extractor.data.filing_validator import source_row_identity
from modeler.data.historical_segments import SEGMENT_BRIDGE_TOLERANCE
from modeler.data.line_identity import line_identity
from modeler.data.standardized_io import standardized_from_payload, standardized_to_payload
from director.data.normalization_candidate import (
    AUTHORIZATION_INDEPENDENT,
    AUTHORIZATION_SYNTHETIC,
    AdoptionRecord,
    TreatmentRecord,
)
from director.ingestion.normalization_candidate_admission import (
    load_admitted_normalization_candidate,
    run_normalization_candidate_handoff,
    save_admitted_normalization_candidate,
)
from modeler.ingestion.normalization_candidate_admission import (
    ANALYTICAL_CONCEPT,
    ANALYTICAL_LABEL,
    ANALYTICAL_SELECTOR,
    AUTHORIZED_IS_IDENTITIES,
    CF_AUDIT_IDENTITIES,
    LEDGER_PERIODS,
    SIGN_TRANSFORMATION,
    construct_provisional_candidate,
)
from modeler.ingestion.normalization_candidate_admission_io import AdmissionProvenanceError
from modeler.financial_math import AnchorMetrics, HistoricalSeries
from modeler.normalization import (
    SUPPORTED_NORMALIZATION_SCOPE,
    compute_normalization_series,
    normalization_cases,
    resolve_income_statement_selector,
)
from modeler.period_axis import canonical_fiscal_periods
from modeler.ratio_values import UNDEFINED_RATIO

ROOT = Path(__file__).resolve().parents[2]
COMPARISON_B = "eb65dc63845b940162c48e39ae9af7598d2a3078"
REVIEWED_CHECKPOINT = "38f5774170c577aa10eb5f03c4cbe99ed7cff789"
AUTHENTICATED_B = "95efb965cd896e462814459b843d9a992358c7a9"
REVIEWED_CHECKPOINT_1091 = "1a82323aac1309141f480e550277ffb2f56b35ca"
REVIEWED_BASELINE_1091 = "250d57178d4b32b3b12a13ba9a08677789d59183"
REVIEWED_CHECKPOINT_1092 = "7cf143f53036afcb981fb4118b830e73b4fa58b6"
REVIEWED_CHECKPOINT_1093 = "02d1f58e55a1823896f71e3090fd236d3448008c"
REVIEWED_PARENT_1093 = "a7e50356d5129066bad5a90ba8f54d801243f926"
REVIEWED_CHECKPOINT_1094 = "06a7184194cd9cb462eebf262790e88d3808a92a"
REVIEWED_PARENT_1094 = "d260153bbda7014d7069c2247f80db75890f61f9"
EXPECTED_BRANCH = "checkpoint/20260913-183303"
WORK_ID = "97863636032d4cc68fa5872fcc3f895d"
IMPLEMENTATION_MD = ROOT / "IMPLEMENTATION.md"
# Historical reviewed attempt — comparator only, never live authorization.
HISTORICAL_REVIEWED_ATTEMPT = "afa6820bb22e4c8da5b7fcc1a3a3c26b"
HISTORICAL_REVIEWED_CHECKPOINT = "fe04b6ceaec34f825e6c56c2351508ed7fc79078"
HISTORICAL_REVIEWED_B = "418f7dc23a52c925d88f9a76ab32cfc33b70e204"
HISTORICAL_REVIEWED_PLAN = "57858697f3f94db58c9e344d7023d3bf"
AUTOCYCLE_DIR = ROOT / ".git" / "autocycle"
RESUME_STATE = AUTOCYCLE_DIR / "resume-state"
IMPLEMENTATION_BASELINE = AUTOCYCLE_DIR / "implementation-baseline.json"
LATEST_IMPLEMENTATION = AUTOCYCLE_DIR / "latest-implementation"
WORK_STATE = AUTOCYCLE_DIR / "work-state.json"
REQUIRED_PROVENANCE_FIELDS = (
    "observation_fingerprints",
    "source_hashes",
    "physical_pages",
    "printed_pages",
    "row_identities",
    "transformation",
    "sign_conversions_applied",
    "face_reported_usd_thousands",
)
LIVE_DIR = ROOT / "build" / "input" / "lululemon" / "evidence" / "prior-live"
EXTRACTED_DIR = ROOT / "build" / "input" / "lululemon" / "extracted"
SOURCE_DIR = ROOT / "build" / "input" / "lululemon" / "source"
RECONCILED_STD = ROOT / "build" / "input" / "lululemon" / "reconciled" / "standardized.json"
ORDINARY_DIR = ROOT / "core" / "tests" / "fixtures" / "ordinary_reconcile" / "lululemon"
ORDINARY_STD = ORDINARY_DIR / "standardized.json"
ASSUMPTIONS = ROOT / "core" / "tests" / "fixtures" / "ordinary_reconcile" / "lululemon_assumptions.json"
EXTRACTED_FILINGS = (
    EXTRACTED_DIR / "LULU_FY2022.json",
    EXTRACTED_DIR / "LULU_FY2023.json",
    EXTRACTED_DIR / "LULU_FY2024.json",
    EXTRACTED_DIR / "LULU_FY2025.json",
)
RETAINED_LIVE_STD = "6c9aad59b04a5995742c68e08f1a704953796fc9fad97a036b08aeeab59051e5"
RETAINED_LIVE_PROV = "5067c1d04aa93c18062fe7eb90558a86394283b7d9fe45899761f71cfb615951"
RETAINED_LIVE_CONFLICTS = "d8a33012f6ea73126ac4e2ece3613e7011c11cb2b581745d8c3563e3c2e978e0"
ORDINARY_STD_SHA256 = "a3568c29e883c8ba57af23da7b4286641a3c5f929af311e2e9593c5f63ea2287"
EXPECTED_FACE = (0, 407913, 74501, 0, 0)
EXPECTED_ANALYTICAL = (0, -407913, -74501, 0, 0)
EXPECTED_NONRECURRING_PRETAX = (0, 407913, 74501, 0, 0)
EXPECTED_RECURRING_PRETAX = (0, 0, 0, 0, 0)
NOTE_TAX_EFFECTS = (28171, 26085)
# Independently specified from extracted source.page and bound PDF printed-page inspection.
EXPECTED_PHYSICAL_PAGES = {
    "2022-01-30": (50, 56),
    "2023-01-29": (50, 51, 56),
    "2024-01-28": (51, 56),
    "2025-02-02": (51,),
    "2026-02-01": (51,),
}
EXPECTED_PRINTED_PAGES = {
    "2022-01-30": (46, 50),
    "2023-01-29": (46, 50),
    "2024-01-28": (50,),
    "2025-02-02": (),
    "2026-02-01": (),
}
RESOLVED_PRINTED_PAGES = {
    ("LULU_FY2022_Annual_Report.pdf", 50): 46,
    ("LULU_FY2022_Annual_Report.pdf", 53): 49,
    ("LULU_FY2023_Annual_Report.pdf", 56): 50,
    ("LULU_FY2023_Annual_Report.pdf", 59): 53,
}
BOUND_SOURCE_SHA256 = {
    "LULU_FY2022_Annual_Report.pdf": "b344d1e7a710259fa06f88773dee0b3827334820ce2b881fe6b95ca2ae275e4e",
    "LULU_FY2023_Annual_Report.pdf": "cd47ea251d608d06a3e58b5d782f2d41d5a231a994d2f7993267a430cb13c0f1",
    "LULU_FY2024_Annual_Report.pdf": "9268fd530db162babdd1ec4363cf388ebce57125d83b7e097aba6f98ba0ca7ec",
    "LULU_FY2025_Annual_Report.pdf": "82e00f900cc912a7d79596409594156b7779c3a193783ea8fecf87bc013c71cc",
}
ORDINARY_SELECTORS = (
    "concept:impairment_and_restructuring",
    "concept:restructuring_expense",
    "label:Impairment of assets and restructuring costs",
    "label:Impairment of goodwill and other assets, restructuring costs",
    "label:Impairment of goodwill and other assets",
)
C1 = "3f6f5dde023847e3347a4c830d822614a28c81a9"
C2 = "20d93331bd3c1b3cccd72a3bf5c805453789e189"
EXTRACT_BLOB = "5e3ef5cfdbfebcf5871dd7e75fad81654d669151"
RELOCATED = {
    "benchmark/fast_retailing/extracted/FY2021.json": "build/input/fast_retailing/extracted/FY2021.json",
    "benchmark/fast_retailing/extracted/FY2022.json": "build/input/fast_retailing/extracted/FY2022.json",
    "benchmark/fast_retailing/extracted/FY2023.json": "build/input/fast_retailing/extracted/FY2023.json",
    "benchmark/fast_retailing/extracted/FY2024.json": "build/input/fast_retailing/extracted/FY2024.json",
    "benchmark/fast_retailing/extracted/FY2025.json": "build/input/fast_retailing/extracted/FY2025.json",
    "benchmark/fast_retailing/reconciled/conflicts.json": "build/input/fast_retailing/reconciled/conflicts.json",
    "benchmark/fast_retailing/reconciled/provenance.json": "build/input/fast_retailing/reconciled/provenance.json",
    "benchmark/fast_retailing/reconciled/standardized.json": "build/input/fast_retailing/reconciled/standardized.json",
    "benchmark/fast_retailing/source_manifest.json": "build/input/fast_retailing/source_manifest.json",
    "benchmark/fast_retailing/source/Fastretailing_CFS2021.pdf": "build/input/fast_retailing/source/Fastretailing_CFS2021.pdf",
    "benchmark/fast_retailing/source/Fastretailing_CFS2022.pdf": "build/input/fast_retailing/source/Fastretailing_CFS2022.pdf",
    "benchmark/fast_retailing/source/Fastretailing_CFS2023.pdf": "build/input/fast_retailing/source/Fastretailing_CFS2023.pdf",
    "benchmark/fast_retailing/source/Fastretailing_CFS2024.pdf": "build/input/fast_retailing/source/Fastretailing_CFS2024.pdf",
    "benchmark/fast_retailing/source/Fastretailing_CFS2025.pdf": "build/input/fast_retailing/source/Fastretailing_CFS2025.pdf",
    "benchmark/lululemon/extracted/LULU_FY2022.json": "build/input/lululemon/extracted/LULU_FY2022.json",
    "benchmark/lululemon/extracted/LULU_FY2023.json": "build/input/lululemon/extracted/LULU_FY2023.json",
    "benchmark/lululemon/extracted/LULU_FY2024.json": "build/input/lululemon/extracted/LULU_FY2024.json",
    "benchmark/lululemon/extracted/LULU_FY2025.json": "build/input/lululemon/extracted/LULU_FY2025.json",
    "benchmark/lululemon/reconciled/conflicts.json": "core/tests/fixtures/ordinary_reconcile/lululemon/conflicts.json",
    "benchmark/lululemon/reconciled/provenance.json": "core/tests/fixtures/ordinary_reconcile/lululemon/provenance.json",
    "benchmark/lululemon/reconciled/standardized.json": "core/tests/fixtures/ordinary_reconcile/lululemon/standardized.json",
    "benchmark/lululemon/source/LULU_FY2022_Annual_Report.pdf": "build/input/lululemon/source/LULU_FY2022_Annual_Report.pdf",
    "benchmark/lululemon/source/LULU_FY2023_Annual_Report.pdf": "build/input/lululemon/source/LULU_FY2023_Annual_Report.pdf",
    "benchmark/lululemon/source/LULU_FY2024_Annual_Report.pdf": "build/input/lululemon/source/LULU_FY2024_Annual_Report.pdf",
    "benchmark/lululemon/source/LULU_FY2025_Annual_Report.pdf": "build/input/lululemon/source/LULU_FY2025_Annual_Report.pdf",
}
STAYED = {
    "example/DEMO_HK_Answer_Key.xlsx": "legacy/example/DEMO_HK_Answer_Key.xlsx",
    "example/DEMO_HK_Assumptions.json": "legacy/example/DEMO_HK_Assumptions.json",
    "example/DEMO_HK_Standardized.json": "legacy/example/DEMO_HK_Standardized.json",
    "example/DEMO_HK_Trainer.xlsx": "legacy/example/DEMO_HK_Trainer.xlsx",
    "example/GOOGL_Demo_Integrated_Financials.xlsx": "legacy/example/GOOGL_Demo_Integrated_Financials.xlsx",
}
RETIRED = [
    "release/fast_retailing/FastRetailing_Answer_Key.assumptions.json",
    "release/fast_retailing/FastRetailing_Answer_Key.component_map.json",
    "release/fast_retailing/FastRetailing_Answer_Key.xlsx",
    "release/fast_retailing/FastRetailing_Trainer.xlsx",
    "release/fast_retailing/README.md",
    "release/fast_retailing/availability.json",
    "release/fast_retailing/rowmap.json",
    "release/fast_retailing/supporting/conflicts.json",
    "release/fast_retailing/supporting/provenance.json",
    "release/fast_retailing/supporting/standardized.json",
    "release/lululemon/Lululemon_Answer_Key.assumptions.json",
    "release/lululemon/Lululemon_Answer_Key.component_map.json",
    "release/lululemon/Lululemon_Answer_Key.xlsx",
    "release/lululemon/Lululemon_Trainer.xlsx",
    "release/lululemon/README.md",
    "release/lululemon/availability.json",
    "release/lululemon/rowmap.json",
    "release/lululemon/supporting/conflicts.json",
    "release/lululemon/supporting/provenance.json",
    "release/lululemon/supporting/standardized.json",
]
EXTRACTED_EIGHT_RELOCATED = {
    "benchmark/lululemon/extracted/LULU_FY2022.json": "build/input/lululemon/extracted/LULU_FY2022.json",
    "benchmark/lululemon/extracted/LULU_FY2023.json": "build/input/lululemon/extracted/LULU_FY2023.json",
    "benchmark/lululemon/extracted/LULU_FY2024.json": "build/input/lululemon/extracted/LULU_FY2024.json",
    "benchmark/lululemon/extracted/LULU_FY2025.json": "build/input/lululemon/extracted/LULU_FY2025.json",
    "benchmark/lululemon/extracted/LULU_FY2022_management_kpis.json": "build/input/lululemon/extracted/LULU_FY2022_management_kpis.json",
    "benchmark/lululemon/extracted/LULU_FY2023_management_kpis.json": "build/input/lululemon/extracted/LULU_FY2023_management_kpis.json",
    "benchmark/lululemon/extracted/LULU_FY2024_management_kpis.json": "build/input/lululemon/extracted/LULU_FY2024_management_kpis.json",
    "benchmark/lululemon/extracted/LULU_FY2025_management_kpis.json": "build/input/lululemon/extracted/LULU_FY2025_management_kpis.json",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _git_out(args: list[str]) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def _read_resume_state() -> dict[str, str]:
    values: dict[str, str] = {}
    if not RESUME_STATE.is_file():
        return values
    for line in RESUME_STATE.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip("'")
    return values


def _read_implementation_baseline() -> dict[str, Any]:
    if not IMPLEMENTATION_BASELINE.is_file():
        return {}
    payload = json.loads(IMPLEMENTATION_BASELINE.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _read_latest_implementation_head() -> str:
    if not LATEST_IMPLEMENTATION.is_file():
        return ""
    for line in LATEST_IMPLEMENTATION.read_text(encoding="utf-8").splitlines():
        if line.startswith("HEAD:"):
            return line.split(":", 1)[1].strip()
    return ""


def _read_work_state() -> dict[str, Any]:
    if not WORK_STATE.is_file():
        return {}
    payload = json.loads(WORK_STATE.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _read_autocycle_plan(path: Path | None = None) -> dict[str, Any]:
    text = (path or IMPLEMENTATION_MD).read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("AUTOCYCLE_PLAN:"):
            payload = json.loads(line.split(":", 1)[1].strip())
            return payload if isinstance(payload, dict) else {}
    return {}


def _require_git_commit(sha: str) -> str:
    if not sha:
        raise AssertionError("unavailable_implement_base")
    try:
        kind = _git_out(["git", "cat-file", "-t", sha])
    except subprocess.CalledProcessError as exc:
        raise AssertionError("unavailable_implement_base") from exc
    if kind != "commit":
        raise AssertionError("unavailable_implement_base")
    return sha


def _live_controller_records() -> dict[str, Any]:
    return {
        "resume": _read_resume_state(),
        "baseline": _read_implementation_baseline(),
        "latest_head": _read_latest_implementation_head(),
        "work_state": _read_work_state(),
        "plan": _read_autocycle_plan(),
    }


def _isolate_controller_records() -> dict[str, Any]:
    """Copy live controller record shapes without mutating controller files."""
    return copy.deepcopy(_live_controller_records())


def _branch_controller_state(work_state: dict[str, Any], branch: str) -> dict[str, Any]:
    payload = ((work_state.get("branches") or {}).get(branch) or {})
    return payload if isinstance(payload, dict) else {}


def _resolve_implement_base_sha(records: dict[str, Any] | None = None) -> str:
    if records is None:
        resume = _read_resume_state()
        baseline = _read_implementation_baseline()
        latest = _read_latest_implementation_head()
    else:
        resume = records.get("resume") if isinstance(records.get("resume"), dict) else {}
        baseline = records.get("baseline") if isinstance(records.get("baseline"), dict) else {}
        latest = str(records.get("latest_head") or "")
    sha = str(resume.get("IMPLEMENT_BASE_SHA") or "").strip()
    if sha:
        _require_git_commit(sha)
        baseline_head = str(baseline.get("head") or "").strip()
        if baseline_head and baseline_head != sha:
            raise AssertionError("inconsistent_baseline")
        return sha
    baseline_head = str(baseline.get("head") or "").strip()
    latest = str(latest or "").strip()
    candidates = [value for value in (baseline_head, latest) if value]
    if not candidates:
        raise AssertionError("unavailable_implement_base")
    if len(set(candidates)) != 1:
        raise AssertionError("inconsistent_baseline")
    return _require_git_commit(candidates[0])


def _authorize_head_against_baseline(
    *,
    head: str,
    branch: str,
    implement_base: str,
    recorded_checkpoint: str = "",
    recorded_checkpoint_parent: str = "",
    attempt_id: str = "",
    bound_attempt_id: str = "",
    work_id: str = "",
    bound_work_id: str = "",
    attempt_baseline: str = "",
    head_parent: str = "",
) -> str:
    """Authorize implementation-at-B or that same attempt's recorded checkpoint.

    Ownership bindings must be nonempty and matching. HEAD == B does not
    bypass them. Ancestry or an unrecorded direct child is not enough.
    """
    del head_parent  # retained for callers; never authorizes a fallback
    if not implement_base or not head or not branch:
        raise AssertionError("unavailable_baseline_binding")
    if branch != EXPECTED_BRANCH:
        raise AssertionError("inconsistent_branch")
    if not work_id or not bound_work_id or not attempt_id or not bound_attempt_id:
        raise AssertionError("unavailable_ownership_binding")
    if work_id != bound_work_id or attempt_id != bound_attempt_id:
        raise AssertionError("mismatched_attempt")
    if not attempt_baseline:
        raise AssertionError("unavailable_ownership_binding")
    if attempt_baseline != implement_base:
        raise AssertionError("mismatched_baseline")
    if head == implement_base:
        return "implementation"
    if (
        recorded_checkpoint
        and head == recorded_checkpoint
        and recorded_checkpoint_parent == implement_base
    ):
        return "checkpoint"
    raise AssertionError("unauthorized_checkpoint")


def _plan_bound_attempt(
    attempts: list[Any],
    *,
    plan_id: str,
    implement_base: str,
) -> dict[str, Any]:
    if not plan_id or not implement_base:
        return {}
    matches = [
        attempt
        for attempt in attempts
        if isinstance(attempt, dict)
        and str(attempt.get("plan_id") or "").strip() == plan_id
        and str(attempt.get("plan_sha") or "").strip() == implement_base
    ]
    if len(matches) != 1:
        return {}
    return matches[0]


def _running_attempt_for_baseline(
    attempts: list[Any],
    *,
    implement_base: str,
) -> dict[str, Any]:
    running = [
        attempt
        for attempt in attempts
        if isinstance(attempt, dict)
        and str(attempt.get("phase") or "").strip() == "running"
        and str(attempt.get("plan_sha") or "").strip() == implement_base
    ]
    if len(running) != 1:
        return {}
    return running[0]


def _repository_bound_attempt(
    attempts: list[Any],
    *,
    head: str,
    implement_base: str,
) -> dict[str, Any]:
    if not head or not implement_base:
        return {}
    if head == implement_base:
        return _running_attempt_for_baseline(attempts, implement_base=implement_base)
    recorded = [
        attempt
        for attempt in attempts
        if isinstance(attempt, dict)
        and str(attempt.get("checkpoint_sha") or "").strip() == head
    ]
    if len(recorded) == 1:
        return recorded[0]
    return _running_attempt_for_baseline(attempts, implement_base=implement_base)


def _checkpoint_parent(sha: str) -> str:
    if not sha:
        return ""
    try:
        return _git_out(["git", "rev-parse", f"{sha}^"])
    except subprocess.CalledProcessError:
        return ""


def _authenticate_current_repository_baseline(
    records: dict[str, Any] | None = None,
) -> dict[str, str]:
    live = records is None
    records = records or _live_controller_records()
    resume = records.get("resume") if isinstance(records.get("resume"), dict) else {}
    baseline = records.get("baseline") if isinstance(records.get("baseline"), dict) else {}
    plan = records.get("plan") if isinstance(records.get("plan"), dict) else {}
    work_state = records.get("work_state") if isinstance(records.get("work_state"), dict) else {}
    implement_base = _resolve_implement_base_sha(None if live else records)
    branch = str(resume.get("STATE_BRANCH") or "").strip()
    git_branch = str(records.get("git_branch") or "").strip()
    if not git_branch:
        git_branch = _git_out(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    baseline_branch = str(baseline.get("branch") or "").strip()
    if not branch or branch != git_branch or (baseline_branch and baseline_branch != branch):
        raise AssertionError("inconsistent_branch")
    head = str(records.get("git_head") or "").strip()
    if not head:
        head = _git_out(["git", "rev-parse", "HEAD"])
    if live:
        _require_git_commit(head)
    branch_state = _branch_controller_state(work_state, branch)
    allocated = branch_state.get("allocated") if isinstance(branch_state.get("allocated"), dict) else {}
    work = branch_state.get("work") if isinstance(branch_state.get("work"), dict) else {}
    attempts = branch_state.get("attempts") if isinstance(branch_state.get("attempts"), list) else []
    expected_work_id = str(plan.get("work_id") or "").strip()
    observed_work_id = str(work.get("id") or "").strip()
    step_id = str(plan.get("step_id") or "").strip()
    allocated_step = allocated.get(step_id) if step_id else None
    allocated_step = allocated_step if isinstance(allocated_step, dict) else {}
    allocated_work_id = str(allocated_step.get("work_id") or "").strip()
    allocated_source = str(allocated_step.get("source") or "").strip()
    plan_id = str(plan.get("plan_id") or "").strip()
    expected_attempt = _plan_bound_attempt(
        attempts,
        plan_id=plan_id,
        implement_base=implement_base,
    )
    observed_attempt = _repository_bound_attempt(
        attempts,
        head=head,
        implement_base=implement_base,
    )
    expected_attempt_id = str(expected_attempt.get("id") or "").strip()
    observed_attempt_id = str(observed_attempt.get("id") or "").strip()
    if not expected_work_id or not observed_work_id or not expected_attempt_id or not observed_attempt_id:
        raise AssertionError("unavailable_ownership_binding")
    if allocated_work_id and allocated_work_id != expected_work_id:
        raise AssertionError("mismatched_attempt")
    if allocated_source and allocated_source != implement_base:
        raise AssertionError("mismatched_baseline")
    recorded_checkpoint = str(observed_attempt.get("checkpoint_sha") or "").strip()
    attempt_baseline = str(observed_attempt.get("plan_sha") or "").strip()
    recorded_parent = ""
    if recorded_checkpoint:
        recorded_parent = str(records.get("git_checkpoint_parent") or "").strip()
        if not recorded_parent:
            recorded_parent = _checkpoint_parent(recorded_checkpoint)
    head_parent = str(records.get("git_head_parent") or "").strip()
    if not head_parent and head != implement_base:
        head_parent = _checkpoint_parent(head)
    state = _authorize_head_against_baseline(
        head=head,
        branch=branch,
        implement_base=implement_base,
        recorded_checkpoint=recorded_checkpoint,
        recorded_checkpoint_parent=recorded_parent,
        attempt_id=expected_attempt_id,
        bound_attempt_id=observed_attempt_id,
        work_id=expected_work_id,
        bound_work_id=observed_work_id,
        attempt_baseline=attempt_baseline,
        head_parent=head_parent,
    )
    return {
        "state": state,
        "implement_base": implement_base,
        "head": head,
        "branch": branch,
        "recorded_checkpoint": recorded_checkpoint,
        "recorded_checkpoint_parent": recorded_parent,
        "work_id": expected_work_id,
        "bound_work_id": observed_work_id,
        "attempt_id": expected_attempt_id,
        "bound_attempt_id": observed_attempt_id,
        "attempt_baseline": attempt_baseline,
    }


def _snapshot_obs(observations: list[dict]) -> str:
    return json.dumps(observations, sort_keys=True, default=str)


def _locator_attached(obs: dict, page_lookup: dict) -> dict:
    """Independently attach physical/printed locators from the bound page lookup."""
    row = dict(obs)
    info = page_lookup.get((str(obs.get("source_file") or ""), int(obs.get("pdf_page") or 0)), {})
    row["physical_page"] = obs.get("pdf_page")
    row["printed_page"] = info.get("printed_page")
    row["printed_page_status"] = info.get("printed_status")
    return row


def _independent_fingerprint(obs: dict) -> str:
    payload = json.dumps(dict(obs), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _page_lookup() -> dict[tuple[str, int], dict[str, object]]:
    return {
        key: {"printed_page": printed, "printed_status": "resolved"}
        for key, printed in RESOLVED_PRINTED_PAGES.items()
    }


def _derive_observations_from_extracted() -> list[dict]:
    """Build observations from extracted statement rows; not from admission output."""
    authorized = set(AUTHORIZED_IS_IDENTITIES) | set(CF_AUDIT_IDENTITIES)
    observations: list[dict] = []
    for path in EXTRACTED_FILINGS:
        filing = load_extracted_filing(path)
        source_file = filing.filing.source_file
        declared = filing.filing.source_sha256
        if declared != BOUND_SOURCE_SHA256[source_file]:
            pytest.fail(
                f"extracted source hash unbound: {path.name} {declared} "
                f"!= {BOUND_SOURCE_SHA256[source_file]}"
            )
        if _sha256(SOURCE_DIR / source_file) != declared:
            pytest.fail(f"source PDF hash mismatch: {source_file}")
        for statement, rows in (
            ("income_statement", filing.income_statement),
            ("cash_flow", filing.cash_flow),
        ):
            for row in rows:
                ident = source_row_identity(statement, row)
                if ident not in authorized:
                    continue
                for period, cell in row.values.items():
                    observations.append(
                        {
                            "currency": filing.filing.currency,
                            "kind": "statement",
                            "label": row.label,
                            "pdf_page": row.source.page,
                            "period": period.isoformat(),
                            "presentation_role": str(cell.presentation_role),
                            "row_identity": ident,
                            "section": row.section,
                            "source_file": source_file,
                            "source_sha256_declared": declared,
                            "statement": statement,
                            "suggested_concept": row.suggested_concept,
                            "unit_scale": filing.filing.unit_scale,
                            "value": cell.value,
                        }
                    )
    return observations


@pytest.fixture(scope="module")
def retained():
    observations = _derive_observations_from_extracted()
    live_bytes = (LIVE_DIR / "standardized.json").read_bytes()
    ordinary_bytes = ORDINARY_STD.read_bytes()
    reconciled_bytes = RECONCILED_STD.read_bytes()
    live_payload = json.loads(live_bytes.decode("utf-8"))
    ordinary_payload = json.loads(ordinary_bytes.decode("utf-8"))
    reconciled_payload = json.loads(reconciled_bytes.decode("utf-8"))
    return {
        "observations": observations,
        "page_lookup": _page_lookup(),
        "live_payload": live_payload,
        "ordinary_payload": ordinary_payload,
        "reconciled_payload": reconciled_payload,
        "live": standardized_from_payload(copy.deepcopy(live_payload), strict=True),
        "obs_snapshot": _snapshot_obs(observations),
        "live_std_bytes": live_bytes,
        "ordinary_std_bytes": ordinary_bytes,
        "reconciled_std_bytes": reconciled_bytes,
    }


def _axis_is_obs(observations: list[dict]) -> list[dict]:
    return [
        obs
        for obs in observations
        if obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        and obs.get("period") in LEDGER_PERIODS
    ]


def _synthetic_adoption(construction, company: str = "LULU") -> AdoptionRecord:
    return AdoptionRecord(
        company=company,
        axis=tuple(construction.axis),
        member_identities=tuple(construction.member_identities),
        analytical_concept=ANALYTICAL_CONCEPT,
        analytical_label=ANALYTICAL_LABEL,
        source_evidence_fingerprints=tuple(construction.used_fingerprints),
        mapping_decision="adopt_three_is_identities_as_one_analytical_aggregate",
        decision_authority="synthetic_test_authority",
        rationale=(
            "SYNTHETIC test authorization only; not a Lululemon accounting judgment "
            "and not established by overlapping amounts or suggested_concept"
        ),
        analytical_scope=SUPPORTED_NORMALIZATION_SCOPE,
        decision_status="adopted",
        authorization_kind=AUTHORIZATION_SYNTHETIC,
    )


def _independent_adoption(construction, company: str = "LULU") -> AdoptionRecord:
    return AdoptionRecord(
        company=company,
        axis=tuple(construction.axis),
        member_identities=tuple(construction.member_identities),
        analytical_concept=ANALYTICAL_CONCEPT,
        analytical_label=ANALYTICAL_LABEL,
        source_evidence_fingerprints=tuple(construction.used_fingerprints),
        mapping_decision="adopt_three_is_identities_as_one_analytical_aggregate",
        decision_authority="independently_supplied_authority",
        rationale=(
            "Independently supplied grouping decision; not a Lululemon accounting "
            "judgment and not established by overlapping amounts or suggested_concept"
        ),
        analytical_scope=SUPPORTED_NORMALIZATION_SCOPE,
        decision_status="adopted",
        authorization_kind=AUTHORIZATION_INDEPENDENT,
    )


def _synthetic_treatment(**overrides) -> TreatmentRecord:
    payload = dict(
        scope=SUPPORTED_NORMALIZATION_SCOPE,
        reference_treatment="Non-recurring",
        rationale="SYNTHETIC test treatment; not a real-company judgment",
        consequence_note="SYNTHETIC consequence; pretax add-back only, after-tax unresolved",
        aggregate_or_component="aggregate",
        cogs_boundary="exclude_studio_cogs",
        deductibility="unresolved",
        etr_disposition="unresolved",
    )
    payload.update(overrides)
    return TreatmentRecord(**payload)


def _dummy_anchor(n: int) -> AnchorMetrics:
    zeros = [0.0] * n
    undefined = [UNDEFINED_RATIO] * n
    return AnchorMetrics(
        revenue=0.0,
        nowc=0.0,
        nola=0.0,
        net_debt=0.0,
        nopat=0.0,
        equity=0.0,
        noa=0.0,
        leverage=0.0,
        hist_avg_after_tax_cod=UNDEFINED_RATIO,
        effective_tax_rate=UNDEFINED_RATIO,
        net_interest=UNDEFINED_RATIO,
        net_interest_after_tax=UNDEFINED_RATIO,
        dupont={},
        reformulation=None,
        historical=HistoricalSeries(
            revenue=list(zeros),
            net_income=list(zeros),
            pretax_income=list(zeros),
            tax_expense=list(zeros),
            effective_tax_rate=list(undefined),
            net_interest=list(undefined),
            net_interest_after_tax=list(undefined),
            nopat=list(zeros),
        ),
    )


def _handoff(retained, **kwargs):
    kwargs.setdefault("observations", retained["observations"])
    kwargs.setdefault("financials", copy.deepcopy(retained["live"]))
    kwargs.setdefault("bound_source_hashes", BOUND_SOURCE_SHA256)
    kwargs.setdefault("page_lookup", retained["page_lookup"])
    return run_normalization_candidate_handoff(**kwargs)


def _page_lookup_rows(page_lookup: dict) -> list[list[object]]:
    return [
        [source, page, info["printed_page"]]
        for (source, page), info in sorted(page_lookup.items())
    ]


def _independent_expected_provenance(observations: list[dict], page_lookup: dict) -> dict[str, dict]:
    """Source-derived expectations computed before any persist/reload."""
    expected: dict[str, dict] = {}
    for period in LEDGER_PERIODS:
        members = [
            _locator_attached(obs, page_lookup)
            for obs in observations
            if obs.get("period") == period and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        ]
        expected[period] = {
            "observation_fingerprints": tuple(
                _independent_fingerprint(obs) for obs in members
            ),
            "source_hashes": tuple(
                sorted({str(obs["source_sha256_declared"]) for obs in members})
            ),
            "physical_pages": EXPECTED_PHYSICAL_PAGES[period],
            "printed_pages": EXPECTED_PRINTED_PAGES[period],
            "row_identities": tuple(sorted({str(obs["row_identity"]) for obs in members})),
            "transformation": SIGN_TRANSFORMATION,
            "sign_conversions_applied": 1,
            "face_reported_usd_thousands": EXPECTED_FACE[LEDGER_PERIODS.index(period)],
        }
    return expected


def _independent_printed_status(obs: dict) -> str:
    if obs.get("printed_page_status"):
        return str(obs["printed_page_status"])
    if obs.get("printed_page") is not None:
        return "resolved"
    physical = obs.get("physical_page", obs.get("pdf_page"))
    if physical in (None, "", 0):
        return "unavailable"
    return "unresolved"


def _independent_observation_evidence(observations: list[dict], page_lookup: dict) -> list[dict]:
    rows: list[dict] = []
    for period in LEDGER_PERIODS:
        members = [
            _locator_attached(obs, page_lookup)
            for obs in observations
            if obs.get("period") == period and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        ]
        for obs in members:
            physical = obs.get("physical_page")
            if physical in (None, "", 0):
                physical = None
            else:
                physical = int(physical)
            rows.append(
                {
                    "fingerprint": _independent_fingerprint(obs),
                    "source_file": str(obs["source_file"]),
                    "source_hash": str(obs["source_sha256_declared"]),
                    "row_identity": str(obs["row_identity"]),
                    "physical_page": physical,
                    "printed_page": obs.get("printed_page"),
                    "printed_page_status": _independent_printed_status(obs),
                    "period": period,
                    "reported_amount": int(obs["value"]),
                    "currency": str(obs["currency"]),
                    "unit_scale": str(obs["unit_scale"]),
                }
            )
    return rows


def _documentary_needles() -> dict[str, bool]:
    return {
        ANALYTICAL_CONCEPT: False,
        ANALYTICAL_LABEL: False,
        SIGN_TRANSFORMATION: False,
        "observation_fingerprints": False,
        "sign_conversions_applied": False,
        "printed_page": False,
    }


def _documentary_hits(payload: object) -> dict[str, bool]:
    text = json.dumps(payload, default=str)
    return {needle: needle in text for needle in _documentary_needles()}


def _admission_persist_names() -> list[str]:
    import core.ingestion.normalization_candidate_admission as admission

    tokens = ("persist", "write_", "reload", "dump", "save_", "to_json", "from_json")
    return sorted(
        name
        for name in dir(admission)
        if any(token in name.lower() for token in tokens)
    )


def _materialize_git_tree(dest: Path, sha: str) -> None:
    archive = subprocess.check_output(
        ["git", "archive", sha, "core", "modeler", "extractor", "director", "interpreter"],
        cwd=ROOT,
    )
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(dest, filter="data")


def _run_isolated_compare(era: str, tree: Path, casebook: dict) -> dict:
    driver = ROOT / "director" / "tests" / "normalization_candidate_isolated_driver.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tree)
    env["PYTHONNOUSERSITE"] = "1"
    result = subprocess.run(
        [sys.executable, str(driver), era],
        cwd=str(tree),
        input=json.dumps(casebook),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"isolated {era} compare failed: {result.stderr or result.stdout}")
    return json.loads(result.stdout)


def _admit(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    financials = copy.deepcopy(retained["live"])
    original = standardized_to_payload(financials)
    result = run_normalization_candidate_handoff(
        retained["observations"],
        financials,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_synthetic_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert standardized_to_payload(financials) == original
    return result


def _run_fresh_load_process(standardized_path: Path, admission_path: Path):
    driver = ROOT / "director" / "tests" / "normalization_candidate_isolated_driver.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["PYTHONNOUSERSITE"] = "1"
    return subprocess.run(
        [sys.executable, str(driver), "load_bundle"],
        cwd=str(ROOT),
        input=json.dumps(
            {
                "standardized_path": str(standardized_path),
                "admission_path": str(admission_path),
                "ledger_periods": list(LEDGER_PERIODS),
            }
        ),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _run_fresh_load(standardized_path: Path, admission_path: Path) -> dict:
    result = _run_fresh_load_process(standardized_path, admission_path)
    if result.returncode != 0:
        pytest.fail(f"fresh load failed: {result.stderr or result.stdout}")
    return json.loads(result.stdout)


def _run_fresh_load_rejection(standardized_path: Path, admission_path: Path) -> dict:
    result = _run_fresh_load_process(standardized_path, admission_path)
    if result.returncode == 0:
        pytest.fail(f"fresh load unexpectedly succeeded: {result.stdout}")
    payload = json.loads(result.stdout)
    assert payload.get("rejected") is True
    return payload


def _persist_admitted(retained, admitted, root: Path) -> tuple[Path, Path]:
    std_path = root / "standardized.json"
    adm_path = root / "normalization_candidate_admission.json"
    save_admitted_normalization_candidate(
        admitted, standardized_path=std_path, admission_path=adm_path
    )
    return std_path, adm_path


def _write_mutated_bundle(root: Path, payload: dict, name: str) -> Path:
    path = root / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _current_branch_state(records: dict[str, Any]) -> dict[str, Any]:
    return _branch_controller_state(records["work_state"], EXPECTED_BRANCH)


def _attempt_by_id(attempts: list[Any], attempt_id: str) -> dict[str, Any]:
    if not attempt_id:
        return {}
    matches = [
        attempt
        for attempt in attempts
        if isinstance(attempt, dict) and str(attempt.get("id") or "").strip() == attempt_id
    ]
    if len(matches) != 1:
        return {}
    return matches[0]


def _apply_isolated_lifecycle(
    records: dict[str, Any],
    *,
    implement_base: str,
    plan_id: str,
    work_id: str,
    attempt_id: str,
    head: str,
    phase: str,
    checkpoint_sha: str | None = None,
    checkpoint_parent: str = "",
) -> dict[str, Any]:
    records["resume"]["IMPLEMENT_BASE_SHA"] = implement_base
    records["resume"]["STATE_BRANCH"] = EXPECTED_BRANCH
    baseline = records.get("baseline")
    if isinstance(baseline, dict):
        baseline["head"] = implement_base
        baseline["branch"] = EXPECTED_BRANCH
    records["plan"]["plan_id"] = plan_id
    records["plan"]["work_id"] = work_id
    records["plan"]["step_id"] = "10.9.4"
    branch = _current_branch_state(records)
    work = branch.get("work")
    if not isinstance(work, dict):
        branch["work"] = {"id": work_id}
    else:
        work["id"] = work_id
    allocated = branch.get("allocated")
    if not isinstance(allocated, dict):
        branch["allocated"] = {}
        allocated = branch["allocated"]
    allocated["10.9.4"] = {
        "source": implement_base,
        "status": "opened",
        "work_id": work_id,
    }
    source = _attempt_by_id(branch.get("attempts") or [], attempt_id)
    if not source:
        raise AssertionError("unavailable_ownership_binding")
    bound = copy.deepcopy(source)
    bound["id"] = attempt_id
    bound["work_id"] = work_id
    bound["plan_id"] = plan_id
    bound["plan_sha"] = implement_base
    bound["phase"] = phase
    bound["checkpoint_sha"] = checkpoint_sha
    branch["attempts"] = [bound]
    records["git_head"] = head
    records["git_branch"] = EXPECTED_BRANCH
    records["git_checkpoint_parent"] = checkpoint_parent
    records["git_head_parent"] = "" if head == implement_base else checkpoint_parent
    return records


def _isolated_implementation_records(
    *,
    implement_base: str,
    plan_id: str,
    attempt_id: str,
    work_id: str = WORK_ID,
) -> dict[str, Any]:
    """Fixture evidence: implementation-at-B, independent of the live phase."""
    return _apply_isolated_lifecycle(
        _isolate_controller_records(),
        implement_base=implement_base,
        plan_id=plan_id,
        work_id=work_id,
        attempt_id=attempt_id,
        head=implement_base,
        phase="running",
        checkpoint_sha=None,
        checkpoint_parent="",
    )


def _isolated_checkpoint_records(
    *,
    implement_base: str,
    plan_id: str,
    attempt_id: str,
    checkpoint_sha: str,
    checkpoint_parent: str,
    work_id: str = WORK_ID,
) -> dict[str, Any]:
    """Fixture evidence: exact recorded checkpoint, independent of the live phase."""
    return _apply_isolated_lifecycle(
        _isolate_controller_records(),
        implement_base=implement_base,
        plan_id=plan_id,
        work_id=work_id,
        attempt_id=attempt_id,
        head=checkpoint_sha,
        phase="checkpointed",
        checkpoint_sha=checkpoint_sha,
        checkpoint_parent=checkpoint_parent,
    )


def _live_bound_attempt() -> tuple[str, dict[str, Any], dict[str, Any]]:
    records = _live_controller_records()
    implement_base = _resolve_implement_base_sha()
    plan = records["plan"] if isinstance(records.get("plan"), dict) else {}
    branch = _branch_controller_state(records["work_state"], EXPECTED_BRANCH)
    attempts = branch.get("attempts") if isinstance(branch.get("attempts"), list) else []
    attempt = _plan_bound_attempt(
        attempts,
        plan_id=str(plan.get("plan_id") or "").strip(),
        implement_base=implement_base,
    )
    return implement_base, plan, attempt


def _expected_live_lifecycle() -> dict[str, str]:
    """Independently derive the authenticated live lifecycle from controller + Git."""
    implement_base, plan, attempt = _live_bound_attempt()
    if not attempt:
        raise AssertionError("unavailable_ownership_binding")
    head = _git_out(["git", "rev-parse", "HEAD"])
    _require_git_commit(head)
    git_branch = _git_out(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if git_branch != EXPECTED_BRANCH:
        raise AssertionError("inconsistent_branch")
    work_id = str(plan.get("work_id") or "").strip()
    attempt_id = str(attempt.get("id") or "").strip()
    attempt_baseline = str(attempt.get("plan_sha") or "").strip()
    recorded_checkpoint = str(attempt.get("checkpoint_sha") or "").strip()
    records = _live_controller_records()
    observed_work = str(
        ((_branch_controller_state(records["work_state"], EXPECTED_BRANCH).get("work") or {}).get("id") or "")
    ).strip()
    if not work_id or not observed_work or not attempt_id:
        raise AssertionError("unavailable_ownership_binding")
    if work_id != observed_work:
        raise AssertionError("mismatched_attempt")
    if attempt_baseline != implement_base:
        raise AssertionError("mismatched_baseline")
    if head == implement_base:
        if str(attempt.get("phase") or "").strip() != "running":
            raise AssertionError("unavailable_ownership_binding")
        return {
            "state": "implementation",
            "implement_base": implement_base,
            "head": implement_base,
            "branch": EXPECTED_BRANCH,
            "recorded_checkpoint": recorded_checkpoint,
            "recorded_checkpoint_parent": "",
            "work_id": work_id,
            "bound_work_id": observed_work,
            "attempt_id": attempt_id,
            "bound_attempt_id": attempt_id,
            "attempt_baseline": attempt_baseline,
        }
    if recorded_checkpoint and head == recorded_checkpoint:
        recorded_parent = _checkpoint_parent(recorded_checkpoint)
        if recorded_parent != implement_base:
            raise AssertionError("unauthorized_checkpoint")
        return {
            "state": "checkpoint",
            "implement_base": implement_base,
            "head": recorded_checkpoint,
            "branch": EXPECTED_BRANCH,
            "recorded_checkpoint": recorded_checkpoint,
            "recorded_checkpoint_parent": recorded_parent,
            "work_id": work_id,
            "bound_work_id": observed_work,
            "attempt_id": attempt_id,
            "bound_attempt_id": attempt_id,
            "attempt_baseline": attempt_baseline,
        }
    raise AssertionError("unauthorized_checkpoint")


def _assert_authenticated_lifecycle(actual: dict[str, str], expected: dict[str, str]) -> None:
    assert actual["state"] == expected["state"]
    assert actual["implement_base"] == expected["implement_base"]
    assert actual["head"] == expected["head"]
    assert actual["branch"] == expected["branch"] == EXPECTED_BRANCH
    assert actual["work_id"] and actual["work_id"] == actual["bound_work_id"] == expected["work_id"]
    assert (
        actual["attempt_id"]
        and actual["attempt_id"] == actual["bound_attempt_id"] == expected["attempt_id"]
    )
    assert actual["attempt_baseline"] == expected["attempt_baseline"] == expected["implement_base"]
    if expected["state"] == "implementation":
        assert actual["head"] == expected["implement_base"]
        return
    assert expected["state"] == "checkpoint"
    assert actual["head"] == actual["recorded_checkpoint"] == expected["recorded_checkpoint"]
    assert (
        actual["recorded_checkpoint_parent"]
        == expected["recorded_checkpoint_parent"]
        == expected["implement_base"]
    )
    assert actual["head"] != expected["implement_base"]


def _bound_attempt(records: dict[str, Any]) -> dict[str, Any]:
    attempts = _current_branch_state(records).get("attempts") or []
    if len(attempts) != 1 or not isinstance(attempts[0], dict):
        raise AssertionError("unavailable_ownership_binding")
    return attempts[0]


def _reject_ownership_mutations(valid: dict[str, Any]) -> None:
    missing_expected_work = copy.deepcopy(valid)
    missing_expected_work["plan"]["work_id"] = ""
    with pytest.raises(AssertionError, match="unavailable_ownership_binding"):
        _authenticate_current_repository_baseline(missing_expected_work)

    missing_observed_work = copy.deepcopy(valid)
    _current_branch_state(missing_observed_work)["work"]["id"] = ""
    with pytest.raises(AssertionError, match="unavailable_ownership_binding"):
        _authenticate_current_repository_baseline(missing_observed_work)

    missing_expected_attempt = copy.deepcopy(valid)
    missing_expected_attempt["plan"]["plan_id"] = "missing-plan-id"
    with pytest.raises(AssertionError, match="unavailable_ownership_binding"):
        _authenticate_current_repository_baseline(missing_expected_attempt)

    missing_observed_attempt = copy.deepcopy(valid)
    observed = _bound_attempt(missing_observed_attempt)
    observed["id"] = ""
    observed["phase"] = "abandoned"
    observed["checkpoint_sha"] = None
    with pytest.raises(AssertionError, match="unavailable_ownership_binding"):
        _authenticate_current_repository_baseline(missing_observed_attempt)

    mismatched_work = copy.deepcopy(valid)
    _current_branch_state(mismatched_work)["work"]["id"] = "unrelated-work"
    with pytest.raises(AssertionError, match="mismatched_attempt"):
        _authenticate_current_repository_baseline(mismatched_work)

    mismatched_allocated_work = copy.deepcopy(valid)
    _current_branch_state(mismatched_allocated_work)["allocated"]["10.9.4"]["work_id"] = (
        "unrelated-work"
    )
    with pytest.raises(AssertionError, match="mismatched_attempt"):
        _authenticate_current_repository_baseline(mismatched_allocated_work)

    mismatched_attempt = copy.deepcopy(valid)
    branch = _current_branch_state(mismatched_attempt)
    expected = _bound_attempt(mismatched_attempt)
    observed = copy.deepcopy(expected)
    expected["phase"] = "abandoned"
    expected["checkpoint_sha"] = "not-the-head"
    observed["id"] = "unrelated-attempt"
    observed["plan_id"] = "unrelated-plan"
    branch["attempts"] = [expected, observed]
    with pytest.raises(AssertionError, match="mismatched_attempt"):
        _authenticate_current_repository_baseline(mismatched_attempt)

    wrong_branch = copy.deepcopy(valid)
    wrong_branch["git_branch"] = "main"
    with pytest.raises(AssertionError, match="inconsistent_branch"):
        _authenticate_current_repository_baseline(wrong_branch)


def _reject_baseline_binding(valid: dict[str, Any], *, foreign_baseline: str) -> None:
    mismatched_alloc = copy.deepcopy(valid)
    _current_branch_state(mismatched_alloc)["allocated"]["10.9.4"]["source"] = foreign_baseline
    with pytest.raises(AssertionError, match="mismatched_baseline"):
        _authenticate_current_repository_baseline(mismatched_alloc)

    head = str(valid.get("git_head") or "").strip()
    implement_base = str((valid.get("resume") or {}).get("IMPLEMENT_BASE_SHA") or "").strip()
    if not head or head == implement_base:
        return
    mismatched_attempt_baseline = copy.deepcopy(valid)
    branch = _current_branch_state(mismatched_attempt_baseline)
    expected = _bound_attempt(mismatched_attempt_baseline)
    observed = copy.deepcopy(expected)
    expected["phase"] = "abandoned"
    expected["checkpoint_sha"] = "not-the-head"
    observed["plan_id"] = "unrelated-plan"
    observed["plan_sha"] = foreign_baseline
    branch["attempts"] = [expected, observed]
    with pytest.raises(AssertionError, match="mismatched_baseline"):
        _authenticate_current_repository_baseline(mismatched_attempt_baseline)
