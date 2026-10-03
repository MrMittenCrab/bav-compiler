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
from core.model.normalization import (
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
WORK_ID = "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"
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
STAYED = [
    "example/DEMO_HK_Answer_Key.xlsx",
    "example/DEMO_HK_Assumptions.json",
    "example/DEMO_HK_Standardized.json",
    "example/DEMO_HK_Trainer.xlsx",
    "example/GOOGL_Demo_Integrated_Financials.xlsx",
]
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


def test_segment_bridge_tolerance_unchanged():
    assert SEGMENT_BRIDGE_TOLERANCE == 0.0


def test_authenticated_retained_evidence_and_eleven_observations(retained):
    is_obs = _axis_is_obs(retained["observations"])
    assert len(is_obs) == 11
    assert tuple(AUTHORIZED_IS_IDENTITIES) == (
        "income_statement||impairment of goodwill and other assets|impairment_and_restructuring",
        "income_statement||impairment of goodwill and other assets, restructuring costs|impairment_and_restructuring",
        "income_statement||impairment of assets and restructuring costs|impairment_and_restructuring",
    )
    excluded = [
        obs
        for obs in retained["observations"]
        if obs.get("period") == "2021-01-31"
        and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
    ]
    assert len(excluded) == 1
    assert excluded[0]["value"] == 0
    assert excluded[0]["source_file"] == "LULU_FY2022_Annual_Report.pdf"
    assert _sha256(LIVE_DIR / "standardized.json") == RETAINED_LIVE_STD
    assert _sha256(LIVE_DIR / "provenance.json") == RETAINED_LIVE_PROV
    assert _sha256(LIVE_DIR / "conflicts.json") == RETAINED_LIVE_CONFLICTS
    assert _sha256(ORDINARY_STD) == ORDINARY_STD_SHA256
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()
    assert retained["ordinary_std_bytes"] == ORDINARY_STD.read_bytes()
    assert retained["reconciled_std_bytes"] == RECONCILED_STD.read_bytes()
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    for obs in retained["observations"]:
        assert obs["currency"] == "USD"
        assert obs["unit_scale"] == "thousands"
        assert obs["source_sha256_declared"] == BOUND_SOURCE_SHA256[obs["source_file"]]
        assert obs["row_identity"]
        assert obs["period"]


def test_provisional_construction_from_observations_not_hand_entered(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    assert construction.constructed is True
    assert construction.face_series == EXPECTED_FACE
    assert construction.analytical_series == EXPECTED_ANALYTICAL
    assert construction.grouping_is_accepted_source_fact is False
    assert construction.production_activation_authorized is False
    assert construction.mapping_status == "provisional_equivalence_unresolved"
    assert construction.line is not None
    assert construction.line.concept == ANALYTICAL_CONCEPT
    assert construction.line.label == ANALYTICAL_LABEL
    assert sum(row.n_is_observations for row in construction.periods) == 11
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    used: set[str] = set()
    for row in construction.periods:
        assert row.face_retained_unchanged is True
        assert row.zero_filled is False
        assert row.missing is False
        assert row.transformation == SIGN_TRANSFORMATION
        assert row.transformation == "analytical_amount = -reported_face_expense"
        assert row.sign_conversions_applied == 1
        assert row.grouping_is_accepted_source_fact is False
        assert row.studio_cogs_included is False
        assert set(row.row_identities) <= set(AUTHORIZED_IS_IDENTITIES)
        assert row.physical_pages == EXPECTED_PHYSICAL_PAGES[row.period]
        assert row.printed_pages == EXPECTED_PRINTED_PAGES[row.period]
        assert row.source_hashes
        assert set(row.source_hashes) <= set(BOUND_SOURCE_SHA256.values())
        members = [
            obs
            for obs in retained["observations"]
            if obs.get("period") == row.period
            and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        ]
        expected_fps = tuple(
            _independent_fingerprint(_locator_attached(obs, retained["page_lookup"]))
            for obs in members
        )
        assert set(row.observation_fingerprints) == set(expected_fps)
        assert not used.intersection(row.observation_fingerprints)
        used.update(row.observation_fingerprints)
    assert len(used) == 11


def test_real_lululemon_path_blocks_production_without_adoption(retained):
    original_n = len(retained["live"].income_statement)
    original_concepts = [item.concept for item in retained["live"].income_statement]
    result = _handoff(retained)
    assert result.constructed is True
    assert result.production_admitted is False
    assert result.real_company_acceptance is False
    assert result.blocked_reason == "absent_adoption"
    assert result.candidate_configuration is None
    assert result.face_series == EXPECTED_FACE
    assert result.analytical_series == EXPECTED_ANALYTICAL
    assert result.grouping_is_accepted_source_fact is False
    assert len(retained["live"].income_statement) == original_n
    assert [item.concept for item in retained["live"].income_statement] == original_concepts
    assert ANALYTICAL_CONCEPT not in original_concepts
    assert json.loads(ASSUMPTIONS.read_text(encoding="utf-8")).get("normalizationCandidates") == []


@pytest.mark.parametrize(
    "name,kwargs,reason",
    [
        (
            "missing_period_evidence",
            {"drop_period": "2022-01-30"},
            "missing_period_evidence",
        ),
        (
            "altered_or_unbound_source_hash",
            {"alter_binding": True},
            "altered_or_unbound_source_hash",
        ),
        (
            "conflicting_overlapping_observations",
            {"conflict_value": 999999},
            "conflicting_overlapping_observations",
        ),
        (
            "unauthorized_identity_membership",
            {"unauthorized": True},
            "unauthorized_identity_membership",
        ),
        (
            "cash_flow_substitution_forbidden",
            {"cf_members": True},
            "cash_flow_substitution_forbidden",
        ),
        (
            "studio_cogs_excluded",
            {"studio": True},
            "studio_cogs_excluded",
        ),
        (
            "aggregate_and_component_double_count",
            {"component": True},
            "aggregate_and_component_double_count",
        ),
        (
            "absent_sign_conversion",
            {"sign_conversion": "absent"},
            "absent_sign_conversion",
        ),
        (
            "repeated_sign_conversion",
            {"sign_conversion": "repeated"},
            "repeated_sign_conversion",
        ),
        (
            "observation_used_more_than_once",
            {"duplicate": True},
            "observation_used_more_than_once",
        ),
    ],
)
def test_retained_construction_rejection_probes_leave_inputs_unchanged(retained, name, kwargs, reason):
    observations = copy.deepcopy(retained["observations"])
    member_identities = AUTHORIZED_IS_IDENTITIES
    sign_conversion = kwargs.get("sign_conversion", "once")
    allow_cf = False
    if kwargs.get("drop_period"):
        observations = [
            obs
            for obs in observations
            if not (
                obs.get("period") == kwargs["drop_period"]
                and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
            )
        ]
    if kwargs.get("alter_binding"):
        for obs in observations:
            if (
                obs.get("period") == "2023-01-29"
                and obs.get("row_identity") == AUTHORIZED_IS_IDENTITIES[0]
            ):
                obs["source_sha256_declared"] = "0" * 64
                break
    if kwargs.get("conflict_value") is not None:
        for obs in observations:
            if (
                obs.get("period") == "2023-01-29"
                and obs.get("row_identity") == AUTHORIZED_IS_IDENTITIES[1]
            ):
                obs["value"] = kwargs["conflict_value"]
                break
    if kwargs.get("unauthorized"):
        observations.append(
            {
                "currency": "USD",
                "kind": "statement",
                "label": "Selling, general and administrative expenses",
                "pdf_page": 50,
                "period": "2023-01-29",
                "presentation_role": "current_period",
                "row_identity": "income_statement||selling, general and administrative expenses|sga",
                "section": "",
                "source_file": "LULU_FY2022_Annual_Report.pdf",
                "source_sha256_declared": BOUND_SOURCE_SHA256["LULU_FY2022_Annual_Report.pdf"],
                "statement": "income_statement",
                "suggested_concept": "sga",
                "unit_scale": "thousands",
                "value": 1,
            }
        )
        member_identities = AUTHORIZED_IS_IDENTITIES + (
            "income_statement||selling, general and administrative expenses|sga",
        )
    if kwargs.get("cf_members"):
        member_identities = CF_AUDIT_IDENTITIES
    if kwargs.get("studio"):
        observations.append(
            {
                "currency": "USD",
                "kind": "statement",
                "label": "lululemon Studio obsolescence provision",
                "pdf_page": 59,
                "period": "2023-01-29",
                "presentation_role": "current_period",
                "row_identity": (
                    "cash_flow|cash flows from operating activities|"
                    "lululemon studio obsolescence provision|studio_obsolescence_provision"
                ),
                "section": "Cash flows from operating activities",
                "source_file": "LULU_FY2023_Annual_Report.pdf",
                "source_sha256_declared": BOUND_SOURCE_SHA256["LULU_FY2023_Annual_Report.pdf"],
                "statement": "cash_flow",
                "suggested_concept": "studio_obsolescence_provision",
                "unit_scale": "thousands",
                "value": 62928,
            }
        )
        member_identities = AUTHORIZED_IS_IDENTITIES + (
            "cash_flow|cash flows from operating activities|"
            "lululemon studio obsolescence provision|studio_obsolescence_provision",
        )
    if kwargs.get("component"):
        observations.append(
            {
                "currency": "USD",
                "kind": "statement",
                "label": "Goodwill impairment component of IS aggregate",
                "pdf_page": 65,
                "period": "2023-01-29",
                "presentation_role": "current_period",
                "row_identity": (
                    "income_statement||goodwill impairment component of is aggregate|"
                    "goodwill_impairment_component"
                ),
                "section": "",
                "source_file": "LULU_FY2022_Annual_Report.pdf",
                "source_sha256_declared": BOUND_SOURCE_SHA256["LULU_FY2022_Annual_Report.pdf"],
                "statement": "income_statement",
                "suggested_concept": "goodwill_impairment_component",
                "unit_scale": "thousands",
                "value": 362492,
            }
        )
        member_identities = AUTHORIZED_IS_IDENTITIES + (
            "income_statement||goodwill impairment component of is aggregate|"
            "goodwill_impairment_component",
        )
    if kwargs.get("duplicate"):
        first_is = next(
            obs
            for obs in observations
            if obs.get("period") == "2023-01-29"
            and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        )
        observations.append(copy.deepcopy(first_is))

    financials = copy.deepcopy(retained["live"])
    original_payload = standardized_to_payload(financials)
    original_obs = _snapshot_obs(retained["observations"])
    result = run_normalization_candidate_handoff(
        observations,
        financials,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        member_identities=member_identities,
        sign_conversion=sign_conversion,
    )
    assert result.constructed is False
    assert result.production_admitted is False
    assert result.blocked_reason == reason, (name, result.blocked_reason, result.gate)
    assert result.candidate_configuration is None
    assert result.constructed_financials is None
    assert standardized_to_payload(financials) == original_payload
    assert _snapshot_obs(retained["observations"]) == original_obs


def test_ambiguous_selector_still_rejected_by_existing_resolver(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    isolated = copy.deepcopy(retained["live"])
    isolated.income_statement = list(isolated.income_statement)
    isolated.income_statement.append(construction.line)
    isolated.income_statement.append(
        type(construction.line)(
            label=ANALYTICAL_LABEL + " duplicate",
            concept=ANALYTICAL_CONCEPT,
            values=dict(construction.line.values),
        )
    )
    with pytest.raises(ValueError, match="matched 2"):
        resolve_income_statement_selector(isolated, ANALYTICAL_SELECTOR)


def test_provisional_adoption_and_technical_equivalence_cannot_authorize(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    base = _synthetic_adoption(construction)
    cases = {
        "provisional_adoption": base.__class__(
            **{**base.__dict__, "decision_status": "provisional"}
        ),
        "boolean_approved": base.__class__(**{**base.__dict__, "approved": True}),
        "matching_concept": base.__class__(
            **{**base.__dict__, "equivalent_by_concept": True}
        ),
        "agreeing_amounts": base.__class__(
            **{**base.__dict__, "equivalent_by_agreeing_amounts": True}
        ),
        "rationale_matching_concept": base.__class__(
            **{**base.__dict__, "rationale": "matching concept across three labels"}
        ),
    }
    financials = copy.deepcopy(retained["live"])
    original = standardized_to_payload(financials)
    result = _handoff(retained, financials=financials, adoption=cases["provisional_adoption"])
    assert result.blocked_reason == "provisional_adoption"
    assert result.production_admitted is False
    assert standardized_to_payload(financials) == original
    for key in ("boolean_approved", "matching_concept", "agreeing_amounts", "rationale_matching_concept"):
        blocked = _handoff(retained, adoption=cases[key])
        assert blocked.production_admitted is False
        assert blocked.blocked_reason == "contradictory_adoption"
        assert blocked.real_company_acceptance is False


def test_altered_decision_bindings_and_stale_adoption(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    base = _synthetic_adoption(construction)
    mismatched = [
        base.__class__(**{**base.__dict__, "company": "NOT_LULU"}),
        base.__class__(**{**base.__dict__, "axis": LEDGER_PERIODS[1:]}),
        base.__class__(
            **{**base.__dict__, "member_identities": AUTHORIZED_IS_IDENTITIES[:2]}
        ),
        base.__class__(**{**base.__dict__, "analytical_concept": "impairment_and_restructuring"}),
    ]
    for record in mismatched:
        result = _handoff(retained, adoption=record, treatment=_synthetic_treatment())
        assert result.blocked_reason == "mismatched_adoption"
        assert result.production_admitted is False
        assert result.candidate_configuration is None
    stale = base.__class__(
        **{**base.__dict__, "source_evidence_fingerprints": ("0" * 64,)}
    )
    stale_result = _handoff(retained, adoption=stale, treatment=_synthetic_treatment())
    assert stale_result.blocked_reason == "stale_adoption"
    assert stale_result.production_admitted is False


def test_missing_treatment_rationale_consequence_and_conflicting_scope(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    adoption = _synthetic_adoption(construction)
    financials = copy.deepcopy(retained["live"])
    original = standardized_to_payload(financials)
    absent = _handoff(retained, financials=financials, adoption=adoption)
    assert absent.blocked_reason == "absent_treatment"
    assert absent.production_admitted is False
    assert standardized_to_payload(financials) == original
    missing_rationale = _handoff(
        retained,
        adoption=adoption,
        treatment=_synthetic_treatment(rationale=""),
    )
    assert missing_rationale.blocked_reason == "missing_treatment_rationale"
    missing_note = _handoff(
        retained,
        adoption=adoption,
        treatment=_synthetic_treatment(consequence_note=""),
    )
    assert missing_note.blocked_reason == "missing_treatment_consequence"
    conflicting = _handoff(
        retained,
        adoption=adoption,
        treatment=_synthetic_treatment(scope="note_item_specific_tax"),
    )
    assert conflicting.blocked_reason == "conflicting_scope"
    unresolved_scope = _handoff(
        retained,
        adoption=adoption,
        treatment=_synthetic_treatment(aggregate_or_component="component"),
    )
    assert unresolved_scope.blocked_reason == "unresolved_scope"
    unresolved_treatment = _handoff(
        retained,
        adoption=adoption,
        treatment=_synthetic_treatment(reference_treatment="Maybe"),
    )
    assert unresolved_treatment.blocked_reason == "unresolved_recurring_treatment"
    assert all(
        row.production_admitted is False
        for row in (
            absent,
            missing_rationale,
            missing_note,
            conflicting,
            unresolved_scope,
            unresolved_treatment,
        )
    )


def test_synthetic_admission_export_reload_and_hypothetical_pretax(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    financials = copy.deepcopy(retained["live"])
    original_n = len(financials.income_statement)
    result = run_normalization_candidate_handoff(
        retained["observations"],
        financials,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_synthetic_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert result.constructed is True
    assert result.production_admitted is True
    assert result.real_company_acceptance is False
    assert result.authorization_kind == AUTHORIZATION_SYNTHETIC
    assert result.mapping_status == "synthetic_test_authorization"
    assert result.grouping_is_accepted_source_fact is False
    assert result.after_tax_available is False
    assert result.note_tax_effects_attributed is False
    assert result.tax_disposition == "unresolved"
    assert result.face_series == EXPECTED_FACE
    assert result.analytical_series == EXPECTED_ANALYTICAL
    assert result.candidate_configuration is not None
    assert result.candidate_configuration["selector"] == ANALYTICAL_SELECTOR
    assert result.candidate_configuration["referenceTreatment"] == "Non-recurring"
    assert len(financials.income_statement) == original_n
    isolated = result.constructed_financials
    assert isolated is not None
    assert len(isolated.income_statement) == original_n + 1
    exported = standardized_to_payload(isolated)
    reloaded = standardized_from_payload(exported, strict=True)
    item = resolve_income_statement_selector(reloaded, ANALYTICAL_SELECTOR)
    ident = line_identity(item)
    assert item.label == ANALYTICAL_LABEL
    assert item.concept == ANALYTICAL_CONCEPT
    dates = [date.fromisoformat(p) for p in LEDGER_PERIODS]
    assert tuple(int(item.values[period]) for period in dates) == EXPECTED_ANALYTICAL
    assert ident.key() == (
        f"concept={ANALYTICAL_CONCEPT}|label={ANALYTICAL_LABEL.casefold()}"
    )
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()
    for row in result.periods:
        assert row.transformation == SIGN_TRANSFORMATION
        assert row.source_hashes
        assert set(row.source_hashes) <= set(BOUND_SOURCE_SHA256.values())
        assert row.physical_pages == EXPECTED_PHYSICAL_PAGES[row.period]
        assert row.printed_pages == EXPECTED_PRINTED_PAGES[row.period]
        assert set(row.row_identities) <= set(AUTHORIZED_IS_IDENTITIES)
        assert row.observation_fingerprints
        members = [
            obs
            for obs in retained["observations"]
            if obs.get("period") == row.period
            and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        ]
        expected_fps = {
            _independent_fingerprint(_locator_attached(obs, retained["page_lookup"]))
            for obs in members
        }
        assert set(row.observation_fingerprints) == expected_fps
    for selector in ORDINARY_SELECTORS:
        with pytest.raises(ValueError, match="matched no income-statement line"):
            resolve_income_statement_selector(reloaded, selector)
    periods = canonical_fiscal_periods(reloaded)
    cases_nr = normalization_cases(
        reloaded, periods, {"normalizationCandidates": [result.candidate_configuration]}
    )
    rec_cfg = dict(result.candidate_configuration)
    rec_cfg["referenceTreatment"] = "Recurring"
    rec_cfg["referenceRationale"] = "SYNTHETIC recurring probe; not adopted"
    rec_cfg["consequenceNote"] = "SYNTHETIC recurring probe; not adopted"
    cases_rec = normalization_cases(
        reloaded, periods, {"normalizationCandidates": [rec_cfg]}
    )
    anchor = _dummy_anchor(len(periods))
    series_nr = compute_normalization_series(
        reloaded, periods, anchor, cases_nr, treatments={cases_nr[0].id: "Non-recurring"}
    )
    series_rec = compute_normalization_series(
        reloaded, periods, anchor, cases_rec, treatments={cases_rec[0].id: "Recurring"}
    )
    assert tuple(int(v) for v in series_nr.pretax_adjustment) == EXPECTED_NONRECURRING_PRETAX
    assert tuple(int(v) for v in series_rec.pretax_adjustment) == EXPECTED_RECURRING_PRETAX
    assert series_nr.after_tax_adjustment[0] == 0.0
    assert series_nr.after_tax_adjustment[3] == 0.0
    assert series_nr.after_tax_adjustment[4] == 0.0
    assert series_nr.after_tax_adjustment[1] == UNDEFINED_RATIO
    assert series_nr.after_tax_adjustment[2] == UNDEFINED_RATIO
    blob = json.dumps(result.candidate_configuration)
    assert "28171" not in blob and "26085" not in blob
    assert NOTE_TAX_EFFECTS[0] not in series_nr.pretax_adjustment
    assert json.loads(ASSUMPTIONS.read_text(encoding="utf-8")).get("normalizationCandidates") == []


def test_repeated_admission_rejected_and_inputs_unchanged(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    first = _handoff(
        retained,
        adoption=_synthetic_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert first.production_admitted is True
    isolated = first.constructed_financials
    assert isolated is not None
    original = standardized_to_payload(isolated)
    repeated = run_normalization_candidate_handoff(
        retained["observations"],
        isolated,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_synthetic_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert repeated.blocked_reason == "repeated_admission"
    assert repeated.production_admitted is False
    assert repeated.candidate_configuration is None
    assert standardized_to_payload(isolated) == original


def test_ordinary_outputs_and_selectors_unchanged(retained):
    live = standardized_from_payload(copy.deepcopy(retained["live_payload"]), strict=True)
    ordinary = standardized_from_payload(copy.deepcopy(retained["ordinary_payload"]), strict=True)
    reconciled = standardized_from_payload(copy.deepcopy(retained["reconciled_payload"]), strict=True)
    for std in (live, ordinary):
        for selector in ORDINARY_SELECTORS + (ANALYTICAL_SELECTOR,):
            with pytest.raises(ValueError, match="matched no income-statement line"):
                resolve_income_statement_selector(std, selector)
    for std in (live, ordinary, reconciled):
        assert (
            normalization_cases(std, canonical_fiscal_periods(std), {"normalizationCandidates": []})
            == ()
        )
        assert not any(item.concept == ANALYTICAL_CONCEPT for item in std.income_statement)
    with pytest.raises(ValueError, match="matched no income-statement line"):
        resolve_income_statement_selector(reconciled, ANALYTICAL_SELECTOR)
    assert _sha256(LIVE_DIR / "standardized.json") == RETAINED_LIVE_STD
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()
    assert retained["ordinary_std_bytes"] == ORDINARY_STD.read_bytes()
    assert retained["reconciled_std_bytes"] == RECONCILED_STD.read_bytes()
    assert json.loads(ASSUMPTIONS.read_text(encoding="utf-8")).get("normalizationCandidates") == []


def test_protected_artifacts_and_eight_extracts_unchanged():
    matches = 0
    for old, new in RELOCATED.items():
        wt = _git_out(["git", "hash-object", str(ROOT / new)])
        c1 = _git_out(["git", "rev-parse", f"{C1}:{old}"])
        c2 = _git_out(["git", "rev-parse", f"{C2}:{old}"])
        assert wt == c1 == c2, (old, new)
        matches += 1
    for rel in STAYED:
        wt = _git_out(["git", "hash-object", str(ROOT / rel)])
        c1 = _git_out(["git", "rev-parse", f"{C1}:{rel}"])
        c2 = _git_out(["git", "rev-parse", f"{C2}:{rel}"])
        assert wt == c1 == c2, rel
        matches += 1
    for rel in RETIRED:
        c1 = _git_out(["git", "rev-parse", f"{C1}:{rel}"])
        c2 = _git_out(["git", "rev-parse", f"{C2}:{rel}"])
        assert c1 == c2, rel
        assert not (ROOT / rel).is_file(), rel
        matches += 1
    assert matches == 50
    extract_matches = 0
    for old, new in EXTRACTED_EIGHT_RELOCATED.items():
        wt = _git_out(["git", "hash-object", str(ROOT / new)])
        at = _git_out(["git", "rev-parse", f"{EXTRACT_BLOB}:{old}"])
        assert wt == at, (old, new)
        extract_matches += 1
    assert extract_matches == 8


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
    driver = ROOT / "core" / "tests" / "normalization_candidate_isolated_driver.py"
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


def test_admission_provenance_persistence_reload(retained):
    expected = _independent_expected_provenance(
        retained["observations"], retained["page_lookup"]
    )
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    admitted = run_normalization_candidate_handoff(
        retained["observations"],
        copy.deepcopy(retained["live"]),
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_synthetic_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert admitted.production_admitted is True
    isolated = admitted.constructed_financials
    assert isolated is not None
    exported = standardized_to_payload(isolated)
    del admitted
    del isolated
    del construction

    with tempfile.TemporaryDirectory() as tmp:
        std_path = Path(tmp) / "standardized.json"
        std_path.write_text(json.dumps(exported), encoding="utf-8")
        del exported
        reloaded_payload = json.loads(std_path.read_text(encoding="utf-8"))
        reloaded = standardized_from_payload(reloaded_payload, strict=True)

    item = resolve_income_statement_selector(reloaded, ANALYTICAL_SELECTOR)
    ident = line_identity(item)
    dates = [date.fromisoformat(period) for period in LEDGER_PERIODS]
    recovered_line = next(
        row
        for row in reloaded_payload["income_statement"]
        if row.get("concept") == ANALYTICAL_CONCEPT
    )
    assert item.label == ANALYTICAL_LABEL
    assert item.concept == ANALYTICAL_CONCEPT
    assert tuple(int(item.values[period]) for period in dates) == EXPECTED_ANALYTICAL
    assert ident.key() == (
        f"concept={ANALYTICAL_CONCEPT}|label={ANALYTICAL_LABEL.casefold()}"
    )
    assert set(recovered_line) == {"label", "concept", "values"}
    assert item.source_doc == ""
    assert item.source_page == ""
    assert "provenance" not in reloaded_payload
    missing = [field for field in REQUIRED_PROVENANCE_FIELDS if field not in recovered_line]
    assert missing == list(REQUIRED_PROVENANCE_FIELDS)
    for period, expect in expected.items():
        assert expect["physical_pages"] == EXPECTED_PHYSICAL_PAGES[period]
        assert expect["printed_pages"] == EXPECTED_PRINTED_PAGES[period]
        assert expect["transformation"] == SIGN_TRANSFORMATION
        assert expect["sign_conversions_applied"] == 1
        assert expect["face_reported_usd_thousands"] == EXPECTED_FACE[
            LEDGER_PERIODS.index(period)
        ]
        assert expect["observation_fingerprints"]
        assert expect["source_hashes"]
        assert expect["row_identities"]
        recovered_period = recovered_line["values"].get(period)
        assert int(recovered_period) == EXPECTED_ANALYTICAL[LEDGER_PERIODS.index(period)]
        assert recovered_line.get("observation_fingerprints") != expect[
            "observation_fingerprints"
        ]
    assert EXPECTED_PRINTED_PAGES["2025-02-02"] == ()
    assert EXPECTED_PRINTED_PAGES["2026-02-01"] == ()
    assert "save_admitted_normalization_candidate" in _admission_persist_names()
    live_hits = _documentary_hits(_load_json(LIVE_DIR / "provenance.json"))
    ordinary_hits = _documentary_hits(_load_json(ORDINARY_DIR / "provenance.json"))
    assert live_hits == _documentary_needles()
    assert ordinary_hits == _documentary_needles()
    from modeler.ingestion.filing_standardizer import reconciliation_provenance_payload

    try:
        reconciliation_provenance_payload(reloaded)
        documentary_accepts = True
    except Exception as exc:
        documentary_accepts = False
        documentary_error = type(exc).__name__
    assert documentary_accepts is False
    assert documentary_error == "TypeError"
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()


def test_b_and_current_isolated_agreement(retained):
    parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT}^"])
    assert parent == COMPARISON_B
    reviewed_parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT_1091}^"])
    assert reviewed_parent == REVIEWED_BASELINE_1091
    reviewed_1092_parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT_1092}^"])
    assert reviewed_1092_parent == AUTHENTICATED_B
    reviewed_1093_parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT_1093}^"])
    assert reviewed_1093_parent == REVIEWED_PARENT_1093
    reviewed_1094_parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT_1094}^"])
    assert reviewed_1094_parent == REVIEWED_PARENT_1094
    expected_live = _expected_live_lifecycle()
    binding = _authenticate_current_repository_baseline()
    _assert_authenticated_lifecycle(binding, expected_live)
    implement_base = binding["implement_base"]
    assert implement_base != REVIEWED_CHECKPOINT_1094
    assert binding["attempt_id"] != HISTORICAL_REVIEWED_ATTEMPT
    assert binding["recorded_checkpoint"] != HISTORICAL_REVIEWED_CHECKPOINT
    casebook = {
        "observations": retained["observations"],
        "live_payload": retained["live_payload"],
        "ordinary_payload": retained["ordinary_payload"],
        "bound_source_hashes": BOUND_SOURCE_SHA256,
        "page_lookup": _page_lookup_rows(retained["page_lookup"]),
        "ordinary_selectors": list(ORDINARY_SELECTORS),
        "expected_analytical": list(EXPECTED_ANALYTICAL),
        "required_provenance_fields": list(REQUIRED_PROVENANCE_FIELDS),
    }
    current = _run_isolated_compare("current", ROOT, casebook)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pre_tree = root / "pre"
        auth_tree = root / "auth"
        implement_tree = root / "implement_b"
        pre_tree.mkdir()
        auth_tree.mkdir()
        implement_tree.mkdir()
        _materialize_git_tree(pre_tree, COMPARISON_B)
        _materialize_git_tree(auth_tree, AUTHENTICATED_B)
        _materialize_git_tree(implement_tree, implement_base)
        pre_admission = (pre_tree / "core/ingestion/normalization_candidate_admission.py").read_bytes()
        assert pre_admission == subprocess.check_output(
            ["git", "show", f"{COMPARISON_B}:core/ingestion/normalization_candidate_admission.py"],
            cwd=ROOT,
        )
        auth_admission = (auth_tree / "core/ingestion/normalization_candidate_admission.py").read_bytes()
        assert auth_admission == subprocess.check_output(
            ["git", "show", f"{AUTHENTICATED_B}:core/ingestion/normalization_candidate_admission.py"],
            cwd=ROOT,
        )
        implement_admission = (
            implement_tree / "core/ingestion/normalization_candidate_admission.py"
        ).read_bytes()
        assert implement_admission == subprocess.check_output(
            ["git", "show", f"{implement_base}:core/ingestion/normalization_candidate_admission.py"],
            cwd=ROOT,
        )
        baseline = _run_isolated_compare("b", pre_tree, casebook)
        authenticated = _run_isolated_compare("authenticated_b", auth_tree, casebook)
        implement_b = _run_isolated_compare("authenticated_b", implement_tree, casebook)
    current_gates = {
        key: value
        for key, value in current.items()
        if key not in {"persistence", "repaired_persistence"}
    }
    baseline_gates = {
        key: value
        for key, value in baseline.items()
        if key not in {"persistence", "repaired_persistence"}
    }
    authenticated_gates = {
        key: value
        for key, value in authenticated.items()
        if key not in {"persistence", "repaired_persistence"}
    }
    implement_b_gates = {
        key: value
        for key, value in implement_b.items()
        if key not in {"persistence", "repaired_persistence"}
    }
    assert current_gates == baseline_gates
    assert current_gates == authenticated_gates
    assert current_gates == implement_b_gates
    assert current["construction"]["face_series"] == list(EXPECTED_FACE)
    assert current["construction"]["analytical_series"] == list(EXPECTED_ANALYTICAL)
    assert current["absent_adoption"]["blocked_reason"] == "absent_adoption"
    assert current["absent_adoption"]["production_admitted"] is False
    assert current["synthetic_admission"]["production_admitted"] is True
    assert current["synthetic_admission"]["real_company_acceptance"] is False
    assert current["synthetic_admission"]["pretax"]["nonrecurring"] == list(EXPECTED_NONRECURRING_PRETAX)
    assert current["synthetic_admission"]["pretax"]["recurring"] == list(EXPECTED_RECURRING_PRETAX)
    assert current["repeated_admission"]["blocked_reason"] == "repeated_admission"
    assert current["ordinary_outputs"]["live"]["has_analytical"] is False
    assert current["ordinary_outputs"]["ordinary"]["empty_candidates"] is True
    persistence = current["persistence"]
    assert persistence["standardized_reload"]["recovered_values"] == list(EXPECTED_ANALYTICAL)
    assert persistence["standardized_reload"]["missing_required_fields"] == list(
        REQUIRED_PROVENANCE_FIELDS
    )
    assert persistence["standardized_reload"]["source_doc"] == ""
    assert persistence["standardized_reload"]["source_page"] == ""
    assert "save_admitted_normalization_candidate" in persistence["contract"]["admission_persist_names"]
    assert persistence["contract"]["documentary_accepts_standardized"] is False
    assert persistence["contract"]["documentary_error"] == "TypeError"
    assert persistence["contract"]["limitation"] == "no_admission_provenance_persist_reload"
    assert baseline["persistence"]["contract"]["admission_persist_names"] == []
    assert authenticated["persistence"]["contract"]["admission_persist_names"] == []
    assert baseline["persistence"]["contract"]["limitation"] == "no_admission_provenance_persist_reload"
    assert authenticated["persistence"]["contract"]["limitation"] == "no_admission_provenance_persist_reload"
    assert baseline["repaired_persistence"]["available"] is False
    assert authenticated["repaired_persistence"]["available"] is False
    assert implement_b["repaired_persistence"]["available"] is True
    assert implement_b["repaired_persistence"]["recovered_values"] == list(EXPECTED_ANALYTICAL)
    repaired = current["repaired_persistence"]
    assert repaired["available"] is True
    assert repaired["recovered_values"] == list(EXPECTED_ANALYTICAL)
    assert repaired["face_values"] == list(EXPECTED_FACE)
    assert repaired["transformation"] == SIGN_TRANSFORMATION
    assert repaired["sign_conversions_applied"] == 1
    assert repaired["authorization_kind"] == AUTHORIZATION_SYNTHETIC
    assert repaired["after_tax_available"] is False
    assert repaired["observations"]
    assert any(item["printed_page_status"] == "unresolved" for item in repaired["observations"])
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()


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
    driver = ROOT / "core" / "tests" / "normalization_candidate_isolated_driver.py"
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


def test_production_admission_bundle_save_load_fresh_process(retained):
    expected = _independent_observation_evidence(
        retained["observations"], retained["page_lookup"]
    )
    admitted = _admit(retained)
    assert admitted.production_admitted is True
    original_obs = _snapshot_obs(retained["observations"])
    with tempfile.TemporaryDirectory() as tmp:
        std_path = Path(tmp) / "standardized.json"
        adm_path = Path(tmp) / "normalization_candidate_admission.json"
        save_admitted_normalization_candidate(
            admitted,
            standardized_path=std_path,
            admission_path=adm_path,
        )
        del admitted
        recovered = _run_fresh_load(std_path, adm_path)
        bundle = load_admitted_normalization_candidate(std_path, adm_path)
    assert recovered["concept"] == ANALYTICAL_CONCEPT
    assert recovered["label"] == ANALYTICAL_LABEL
    assert recovered["identity_key"] == (
        f"concept={ANALYTICAL_CONCEPT}|label={ANALYTICAL_LABEL.casefold()}"
    )
    assert recovered["values"] == list(EXPECTED_ANALYTICAL)
    assert recovered["face_values"] == list(EXPECTED_FACE)
    assert recovered["analytical_values"] == list(EXPECTED_ANALYTICAL)
    assert recovered["fiscal_periods"] == list(LEDGER_PERIODS)
    assert recovered["transformation"] == SIGN_TRANSFORMATION
    assert recovered["sign_conversions_applied"] == 1
    assert recovered["authorization_kind"] == AUTHORIZATION_SYNTHETIC
    assert recovered["mapping_status"] == "synthetic_test_authorization"
    assert recovered["after_tax_available"] is False
    assert recovered["tax_disposition"] == "unresolved"
    assert recovered["grouping_is_accepted_source_fact"] is False
    assert recovered["real_company_acceptance"] is False
    assert recovered["candidate_configuration"]["selector"] == ANALYTICAL_SELECTOR
    recovered_obs = recovered["observations"]
    assert recovered_obs == expected
    assert len(recovered_obs) == 11
    by_period = {period: [] for period in LEDGER_PERIODS}
    for item in recovered_obs:
        by_period[item["period"]].append(item)
        assert item["source_hash"] in BOUND_SOURCE_SHA256.values()
        assert item["row_identity"] in AUTHORIZED_IS_IDENTITIES
        assert item["currency"] == "USD"
        assert item["unit_scale"] == "thousands"
        assert item["printed_page_status"] in {"resolved", "unresolved", "unavailable"}
        if item["printed_page_status"] != "resolved":
            assert item["printed_page"] is None
        if item["printed_page_status"] == "unresolved":
            assert item["physical_page"] is not None
            assert item["printed_page"] != item["physical_page"]
    assert {item["printed_page_status"] for item in by_period["2025-02-02"]} == {"unresolved"}
    assert {item["printed_page_status"] for item in by_period["2026-02-01"]} == {"unresolved"}
    assert any(item["printed_page_status"] == "resolved" for item in recovered_obs)
    assert tuple(int(v) for v in bundle.analytical_values) == EXPECTED_ANALYTICAL
    assert tuple(int(v) for v in bundle.face_values) == EXPECTED_FACE
    assert bundle.sign_conversions_applied == 1
    for period, expect in _independent_expected_provenance(
        retained["observations"], retained["page_lookup"]
    ).items():
        members = [item for item in recovered_obs if item["period"] == period]
        assert {item["fingerprint"] for item in members} == set(expect["observation_fingerprints"])
        assert {item["source_hash"] for item in members} == set(expect["source_hashes"])
        assert {item["row_identity"] for item in members} == set(expect["row_identities"])
        assert {item["physical_page"] for item in members} == set(expect["physical_pages"])
        assert {item["printed_page"] for item in members if item["printed_page"] is not None} == set(
            expect["printed_pages"]
        )
        assert {item["reported_amount"] for item in members} == {expect["face_reported_usd_thousands"]}
    repeated = run_normalization_candidate_handoff(
        retained["observations"],
        bundle.financials,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_synthetic_adoption(
            construct_provisional_candidate(
                retained["observations"],
                bound_source_hashes=BOUND_SOURCE_SHA256,
                page_lookup=retained["page_lookup"],
            )
        ),
        treatment=_synthetic_treatment(),
    )
    assert repeated.blocked_reason == "repeated_admission"
    assert repeated.production_admitted is False
    assert _snapshot_obs(retained["observations"]) == original_obs
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()


def test_admission_bundle_rejects_mismatched_missing_and_blocked(retained):
    admitted = _admit(retained)
    blocked = _handoff(retained)
    assert blocked.production_admitted is False
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        std_path = root / "standardized.json"
        adm_path = root / "normalization_candidate_admission.json"
        save_admitted_normalization_candidate(
            admitted, standardized_path=std_path, admission_path=adm_path
        )
        with pytest.raises(AdmissionProvenanceError, match="blocked_or_provisional_handoff"):
            save_admitted_normalization_candidate(
                blocked,
                standardized_path=root / "blocked.json",
                admission_path=root / "blocked_admission.json",
            )
        construction = construct_provisional_candidate(
            retained["observations"],
            bound_source_hashes=BOUND_SOURCE_SHA256,
            page_lookup=retained["page_lookup"],
        )
        provisional = _handoff(
            retained,
            adoption=_synthetic_adoption(construction).__class__(
                **{**_synthetic_adoption(construction).__dict__, "decision_status": "provisional"}
            ),
            treatment=_synthetic_treatment(),
        )
        assert provisional.blocked_reason == "provisional_adoption"
        with pytest.raises(AdmissionProvenanceError, match="blocked_or_provisional_handoff"):
            save_admitted_normalization_candidate(
                provisional,
                standardized_path=root / "provisional.json",
                admission_path=root / "provisional_admission.json",
            )
        assert not (root / "blocked.json").exists()
        assert not (root / "blocked_admission.json").exists()
        assert not (root / "provisional.json").exists()
        assert not (root / "provisional_admission.json").exists()

        missing_adm = root / "missing_admission.json"
        with pytest.raises(AdmissionProvenanceError, match="missing_admission_evidence"):
            load_admitted_normalization_candidate(std_path, missing_adm)

        company = json.loads(adm_path.read_text(encoding="utf-8"))
        company["company"] = "NOT_LULU"
        company_path = root / "company.json"
        company_path.write_text(json.dumps(company), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="mismatched_company_binding"):
            load_admitted_normalization_candidate(std_path, company_path)

        line = json.loads(adm_path.read_text(encoding="utf-8"))
        line["analytical_line"]["concept"] = "impairment_and_restructuring"
        line["analytical_line"]["identity"] = "concept=impairment_and_restructuring|label=x"
        line_path = root / "line.json"
        line_path.write_text(json.dumps(line), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="mismatched_line_binding"):
            load_admitted_normalization_candidate(std_path, line_path)

        period = json.loads(adm_path.read_text(encoding="utf-8"))
        period["fiscal_periods"] = list(LEDGER_PERIODS[1:])
        period_path = root / "period.json"
        period_path.write_text(json.dumps(period), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="mismatched_period_binding"):
            load_admitted_normalization_candidate(std_path, period_path)

        value_std = json.loads(std_path.read_text(encoding="utf-8"))
        for item in value_std["income_statement"]:
            if item.get("concept") == ANALYTICAL_CONCEPT:
                item["values"][LEDGER_PERIODS[1]] = 1
        value_path = root / "value.json"
        value_path.write_text(json.dumps(value_std), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="mismatched_value_binding"):
            load_admitted_normalization_candidate(value_path, adm_path)

        stale = json.loads(adm_path.read_text(encoding="utf-8"))
        stale["observations"][0]["fingerprint"] = "0" * 64
        stale_path = root / "stale.json"
        stale_path.write_text(json.dumps(stale), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="stale_admission_evidence"):
            load_admitted_normalization_candidate(std_path, stale_path)

        missing_obs = json.loads(adm_path.read_text(encoding="utf-8"))
        missing_obs["observations"] = [
            item
            for item in missing_obs["observations"]
            if item["period"] != LEDGER_PERIODS[0]
        ]
        missing_path = root / "missing_obs.json"
        missing_path.write_text(json.dumps(missing_obs), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="missing_admission_evidence"):
            load_admitted_normalization_candidate(std_path, missing_path)

        ambiguous_std = json.loads(std_path.read_text(encoding="utf-8"))
        analytical = next(
            item
            for item in ambiguous_std["income_statement"]
            if item.get("concept") == ANALYTICAL_CONCEPT
        )
        ambiguous_std["income_statement"].append(copy.deepcopy(analytical))
        ambiguous_path = root / "ambiguous.json"
        ambiguous_path.write_text(json.dumps(ambiguous_std), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="ambiguous_admission_linkage"):
            load_admitted_normalization_candidate(ambiguous_path, adm_path)

    ordinary = standardized_from_payload(copy.deepcopy(retained["ordinary_payload"]), strict=True)
    assert not any(item.concept == ANALYTICAL_CONCEPT for item in ordinary.income_statement)
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]


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


def test_production_loader_rejects_four_demonstrated_bypasses(retained):
    admitted = _admit(retained)
    original_obs = _snapshot_obs(retained["observations"])
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        std_path, adm_path = _persist_admitted(retained, admitted, root)
        valid = json.loads(adm_path.read_text(encoding="utf-8"))

        provisional = copy.deepcopy(valid)
        provisional["adoption"]["decision_status"] = "provisional"
        provisional_path = _write_mutated_bundle(root, provisional, "provisional.json")
        with pytest.raises(AdmissionProvenanceError, match="blocked_or_provisional_handoff"):
            load_admitted_normalization_candidate(std_path, provisional_path)
        rejected = _run_fresh_load_rejection(std_path, provisional_path)
        assert rejected["reason"] == "blocked_or_provisional_handoff"

        empty_treatment = copy.deepcopy(valid)
        empty_treatment["treatment"] = {}
        empty_path = _write_mutated_bundle(root, empty_treatment, "empty_treatment.json")
        with pytest.raises(AdmissionProvenanceError, match="missing_admission_evidence"):
            load_admitted_normalization_candidate(std_path, empty_path)
        rejected = _run_fresh_load_rejection(std_path, empty_path)
        assert rejected["reason"] == "missing_admission_evidence"

        synthetic_as_real = copy.deepcopy(valid)
        synthetic_as_real["real_company_acceptance"] = True
        synthetic_path = _write_mutated_bundle(root, synthetic_as_real, "synthetic_as_real.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, synthetic_path)
        rejected = _run_fresh_load_rejection(std_path, synthetic_path)
        assert rejected["reason"] == "inconsistent_admission_binding"

        changed_hash = copy.deepcopy(valid)
        changed_hash["observations"][0]["source_hash"] = "0" * 64
        hash_path = _write_mutated_bundle(root, changed_hash, "changed_source_hash.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, hash_path)
        rejected = _run_fresh_load_rejection(std_path, hash_path)
        assert rejected["reason"] == "inconsistent_admission_binding"

        recovered = _run_fresh_load(std_path, adm_path)
        assert recovered["real_company_acceptance"] is False
        assert recovered["authorization_kind"] == AUTHORIZATION_SYNTHETIC
    assert _snapshot_obs(retained["observations"]) == original_obs
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()


def test_admission_bundle_rejects_authorization_treatment_and_fingerprint_disagreement(retained):
    admitted = _admit(retained)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        std_path, adm_path = _persist_admitted(retained, admitted, root)
        valid = json.loads(adm_path.read_text(encoding="utf-8"))

        auth_mismatch = copy.deepcopy(valid)
        auth_mismatch["authorization_kind"] = AUTHORIZATION_INDEPENDENT
        auth_path = _write_mutated_bundle(root, auth_mismatch, "auth_mismatch.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, auth_path)
        assert _run_fresh_load_rejection(std_path, auth_path)["reason"] == (
            "inconsistent_admission_binding"
        )

        config_mismatch = copy.deepcopy(valid)
        config_mismatch["candidate_configuration"]["referenceTreatment"] = "Recurring"
        config_path = _write_mutated_bundle(root, config_mismatch, "config_mismatch.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, config_path)
        assert _run_fresh_load_rejection(std_path, config_path)["reason"] == (
            "inconsistent_admission_binding"
        )

        fingerprint_mismatch = copy.deepcopy(valid)
        fingerprint_mismatch["observations"][0]["reported_amount"] = 1
        fp_path = _write_mutated_bundle(root, fingerprint_mismatch, "fingerprint_mismatch.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, fp_path)
        assert _run_fresh_load_rejection(std_path, fp_path)["reason"] == (
            "inconsistent_admission_binding"
        )
        stale_inputs = copy.deepcopy(valid)
        stale_inputs["observations"][0]["fingerprint_inputs"]["value"] = 1
        stale_inputs_path = _write_mutated_bundle(root, stale_inputs, "stale_inputs.json")
        with pytest.raises(AdmissionProvenanceError, match="stale_admission_evidence"):
            load_admitted_normalization_candidate(std_path, stale_inputs_path)
        assert _run_fresh_load_rejection(std_path, stale_inputs_path)["reason"] == (
            "stale_admission_evidence"
        )

        missing_inputs = copy.deepcopy(valid)
        for item in missing_inputs["observations"]:
            item.pop("fingerprint_inputs", None)
        missing_path = _write_mutated_bundle(root, missing_inputs, "missing_inputs.json")
        with pytest.raises(AdmissionProvenanceError, match="stale_admission_evidence"):
            load_admitted_normalization_candidate(std_path, missing_path)
        assert _run_fresh_load_rejection(std_path, missing_path)["reason"] == (
            "stale_admission_evidence"
        )

        old_schema = copy.deepcopy(valid)
        old_schema["schema"] = "normalization_candidate_admission/v1"
        old_path = _write_mutated_bundle(root, old_schema, "old_schema.json")
        with pytest.raises(AdmissionProvenanceError, match="stale_admission_evidence"):
            load_admitted_normalization_candidate(std_path, old_path)
        assert _run_fresh_load_rejection(std_path, old_path)["reason"] == (
            "stale_admission_evidence"
        )


def test_independent_authorization_bundle_save_load_fresh_process(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    financials = copy.deepcopy(retained["live"])
    original = standardized_to_payload(financials)
    admitted = run_normalization_candidate_handoff(
        retained["observations"],
        financials,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_independent_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert standardized_to_payload(financials) == original
    assert admitted.production_admitted is True
    assert admitted.authorization_kind == AUTHORIZATION_INDEPENDENT
    assert admitted.real_company_acceptance is True
    assert admitted.mapping_status == "independently_supplied_decision"
    assert admitted.grouping_is_accepted_source_fact is False
    expected = _independent_observation_evidence(
        retained["observations"], retained["page_lookup"]
    )
    with tempfile.TemporaryDirectory() as tmp:
        std_path, adm_path = _persist_admitted(retained, admitted, Path(tmp))
        recovered = _run_fresh_load(std_path, adm_path)
        bundle = load_admitted_normalization_candidate(std_path, adm_path)
    assert recovered["authorization_kind"] == AUTHORIZATION_INDEPENDENT
    assert recovered["real_company_acceptance"] is True
    assert recovered["mapping_status"] == "independently_supplied_decision"
    assert recovered["grouping_is_accepted_source_fact"] is False
    assert recovered["values"] == list(EXPECTED_ANALYTICAL)
    assert recovered["face_values"] == list(EXPECTED_FACE)
    assert recovered["observations"] == expected
    assert bundle.authorization_kind == AUTHORIZATION_INDEPENDENT
    assert bundle.real_company_acceptance is True
    assert bundle.grouping_is_accepted_source_fact is False
    assert recovered["transformation"] == SIGN_TRANSFORMATION
    assert recovered["sign_conversions_applied"] == 1
    assert all(
        item["period"] == expect["period"]
        for item, expect in zip(recovered["observations"], expected, strict=True)
    )
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()


def test_production_loader_rejects_period_reassignment_and_false_transformation(retained):
    admitted = _admit(retained)
    original_obs = _snapshot_obs(retained["observations"])
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        std_path, adm_path = _persist_admitted(retained, admitted, root)
        valid = json.loads(adm_path.read_text(encoding="utf-8"))
        assert valid["transformation"] == SIGN_TRANSFORMATION
        source_period = "2025-02-02"
        reassigned_period = "2026-02-01"
        moved = copy.deepcopy(valid)
        target = next(item for item in moved["observations"] if item["period"] == source_period)
        assert target["fingerprint_inputs"]["period"] == source_period
        target["period"] = reassigned_period
        assert target["fingerprint_inputs"]["period"] == source_period
        moved_path = _write_mutated_bundle(root, moved, "period_reassigned.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, moved_path)
        assert _run_fresh_load_rejection(std_path, moved_path)["reason"] == (
            "inconsistent_admission_binding"
        )

        false_transform = copy.deepcopy(valid)
        false_transform["transformation"] = "analytical_amount = reported_face_expense"
        transform_path = _write_mutated_bundle(root, false_transform, "false_transform.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, transform_path)
        assert _run_fresh_load_rejection(std_path, transform_path)["reason"] == (
            "inconsistent_admission_binding"
        )

        missing_period = copy.deepcopy(valid)
        missing_period["observations"][0].pop("period", None)
        assert missing_period["observations"][0]["fingerprint_inputs"]["period"]
        missing_path = _write_mutated_bundle(root, missing_period, "missing_period.json")
        with pytest.raises(AdmissionProvenanceError, match="missing_admission_evidence"):
            load_admitted_normalization_candidate(std_path, missing_path)
        assert _run_fresh_load_rejection(std_path, missing_path)["reason"] == (
            "missing_admission_evidence"
        )

        recovered = _run_fresh_load(std_path, adm_path)
        assert recovered["transformation"] == SIGN_TRANSFORMATION
        assert any(item["period"] == source_period for item in recovered["observations"])
        assert any(item["period"] == reassigned_period for item in recovered["observations"])
    assert _snapshot_obs(retained["observations"]) == original_obs
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()


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


def test_baseline_authentication_implementation_and_checkpoint_bindings():
    current_b = _resolve_implement_base_sha()
    resume = _read_resume_state()
    assert resume.get("IMPLEMENT_BASE_SHA") == current_b
    assert resume.get("STATE_BRANCH") == EXPECTED_BRANCH
    _require_git_commit(current_b)
    assert current_b != HISTORICAL_REVIEWED_B
    expected_live = _expected_live_lifecycle()
    current_attempt_id = expected_live["attempt_id"]
    current_plan_id = str(_read_autocycle_plan().get("plan_id") or "").strip()
    assert current_attempt_id
    assert current_plan_id
    assert current_attempt_id != HISTORICAL_REVIEWED_ATTEMPT
    assert current_plan_id != HISTORICAL_REVIEWED_PLAN

    shared = dict(
        branch=EXPECTED_BRANCH,
        work_id=WORK_ID,
        bound_work_id=WORK_ID,
        attempt_id=current_attempt_id,
        bound_attempt_id=current_attempt_id,
        attempt_baseline=current_b,
    )
    assert _authorize_head_against_baseline(
        head=current_b,
        implement_base=current_b,
        **shared,
    ) == "implementation"
    assert _authorize_head_against_baseline(
        head=HISTORICAL_REVIEWED_CHECKPOINT,
        branch=EXPECTED_BRANCH,
        implement_base=HISTORICAL_REVIEWED_B,
        recorded_checkpoint=HISTORICAL_REVIEWED_CHECKPOINT,
        recorded_checkpoint_parent=HISTORICAL_REVIEWED_B,
        work_id=WORK_ID,
        bound_work_id=WORK_ID,
        attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
        bound_attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
        attempt_baseline=HISTORICAL_REVIEWED_B,
    ) == "checkpoint"

    missing_identity_kwargs = dict(
        head=current_b,
        branch=EXPECTED_BRANCH,
        implement_base=current_b,
        attempt_baseline=current_b,
    )
    with pytest.raises(AssertionError, match="unavailable_ownership_binding"):
        _authorize_head_against_baseline(**missing_identity_kwargs)
    with pytest.raises(AssertionError, match="unavailable_ownership_binding"):
        _authorize_head_against_baseline(
            work_id=WORK_ID,
            bound_work_id="",
            attempt_id="present",
            bound_attempt_id="present",
            **missing_identity_kwargs,
        )
    with pytest.raises(AssertionError, match="unavailable_ownership_binding"):
        _authorize_head_against_baseline(
            work_id=WORK_ID,
            bound_work_id=WORK_ID,
            attempt_id="",
            bound_attempt_id="present",
            **missing_identity_kwargs,
        )
    with pytest.raises(AssertionError, match="mismatched_attempt"):
        _authorize_head_against_baseline(
            head=current_b,
            implement_base=current_b,
            work_id=WORK_ID,
            bound_work_id="unrelated-work",
            attempt_id="same",
            bound_attempt_id="same",
            attempt_baseline=current_b,
            branch=EXPECTED_BRANCH,
        )
    with pytest.raises(AssertionError, match="mismatched_attempt"):
        _authorize_head_against_baseline(
            head=current_b,
            implement_base=current_b,
            work_id=WORK_ID,
            bound_work_id=WORK_ID,
            attempt_id="expected-attempt",
            bound_attempt_id="observed-attempt",
            attempt_baseline=current_b,
            branch=EXPECTED_BRANCH,
        )
    with pytest.raises(AssertionError, match="mismatched_baseline"):
        _authorize_head_against_baseline(
            head=current_b,
            implement_base=current_b,
            work_id=WORK_ID,
            bound_work_id=WORK_ID,
            attempt_id="same",
            bound_attempt_id="same",
            attempt_baseline=HISTORICAL_REVIEWED_B,
            branch=EXPECTED_BRANCH,
        )
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authorize_head_against_baseline(
            head=HISTORICAL_REVIEWED_CHECKPOINT,
            implement_base=current_b,
            recorded_checkpoint="",
            recorded_checkpoint_parent="",
            head_parent=current_b,
            **shared,
        )
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authorize_head_against_baseline(
            head=HISTORICAL_REVIEWED_CHECKPOINT,
            implement_base=current_b,
            recorded_checkpoint=REVIEWED_CHECKPOINT_1094,
            recorded_checkpoint_parent=REVIEWED_PARENT_1094,
            head_parent=current_b,
            **shared,
        )
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authorize_head_against_baseline(
            head=current_b,
            implement_base=HISTORICAL_REVIEWED_B,
            recorded_checkpoint=HISTORICAL_REVIEWED_CHECKPOINT,
            recorded_checkpoint_parent=HISTORICAL_REVIEWED_B,
            work_id=WORK_ID,
            bound_work_id=WORK_ID,
            attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
            bound_attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
            attempt_baseline=HISTORICAL_REVIEWED_B,
            branch=EXPECTED_BRANCH,
        )
    with pytest.raises(AssertionError, match="inconsistent_branch"):
        _authorize_head_against_baseline(
            head=current_b,
            branch="main",
            implement_base=current_b,
            work_id=WORK_ID,
            bound_work_id=WORK_ID,
            attempt_id="same",
            bound_attempt_id="same",
            attempt_baseline=current_b,
        )

    # Live execution: authenticate against actual controller bindings.
    live = _authenticate_current_repository_baseline()
    _assert_authenticated_lifecycle(live, expected_live)
    assert live["work_id"] == WORK_ID
    assert live["attempt_id"] != HISTORICAL_REVIEWED_ATTEMPT
    assert live["recorded_checkpoint"] != HISTORICAL_REVIEWED_CHECKPOINT

    # Fixture evidence: implementation path, constructed independently of live phase.
    implementation_fixture = _isolated_implementation_records(
        implement_base=current_b,
        plan_id=current_plan_id,
        attempt_id=current_attempt_id,
    )
    implemented = _authenticate_current_repository_baseline(implementation_fixture)
    assert implemented["state"] == "implementation"
    assert implemented["head"] == current_b == implemented["implement_base"]
    assert implemented["attempt_id"] == implemented["bound_attempt_id"] == current_attempt_id
    assert implemented["work_id"] == implemented["bound_work_id"] == WORK_ID
    assert implemented["recorded_checkpoint"] == ""
    assert implemented["attempt_baseline"] == current_b
    assert implemented["branch"] == EXPECTED_BRANCH

    # Fixture evidence: exact-checkpoint path, historical comparator tuple only.
    checkpoint_fixture = _isolated_checkpoint_records(
        implement_base=HISTORICAL_REVIEWED_B,
        plan_id=HISTORICAL_REVIEWED_PLAN,
        attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
        checkpoint_sha=HISTORICAL_REVIEWED_CHECKPOINT,
        checkpoint_parent=HISTORICAL_REVIEWED_B,
    )
    exact = _authenticate_current_repository_baseline(checkpoint_fixture)
    assert exact["state"] == "checkpoint"
    assert exact["head"] == HISTORICAL_REVIEWED_CHECKPOINT
    assert exact["attempt_id"] == exact["bound_attempt_id"] == HISTORICAL_REVIEWED_ATTEMPT
    assert exact["recorded_checkpoint"] == HISTORICAL_REVIEWED_CHECKPOINT
    assert exact["recorded_checkpoint_parent"] == HISTORICAL_REVIEWED_B
    assert exact["implement_base"] == HISTORICAL_REVIEWED_B
    assert exact["work_id"] == exact["bound_work_id"] == WORK_ID
    assert exact["attempt_baseline"] == HISTORICAL_REVIEWED_B
    assert exact["branch"] == EXPECTED_BRANCH

    _reject_ownership_mutations(implementation_fixture)
    _reject_ownership_mutations(checkpoint_fixture)
    _reject_baseline_binding(implementation_fixture, foreign_baseline=HISTORICAL_REVIEWED_B)
    _reject_baseline_binding(checkpoint_fixture, foreign_baseline=REVIEWED_PARENT_1094)

    wrong_checkpoint_parent = copy.deepcopy(checkpoint_fixture)
    wrong_checkpoint_parent["git_checkpoint_parent"] = REVIEWED_PARENT_1094
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authenticate_current_repository_baseline(wrong_checkpoint_parent)

    no_recorded_child = _isolated_implementation_records(
        implement_base=HISTORICAL_REVIEWED_B,
        plan_id=HISTORICAL_REVIEWED_PLAN,
        attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
    )
    _bound_attempt(no_recorded_child)["checkpoint_sha"] = None
    no_recorded_child["git_head"] = HISTORICAL_REVIEWED_CHECKPOINT
    no_recorded_child["git_head_parent"] = HISTORICAL_REVIEWED_B
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authenticate_current_repository_baseline(no_recorded_child)

    stale_old_b = _isolated_implementation_records(
        implement_base=HISTORICAL_REVIEWED_B,
        plan_id=HISTORICAL_REVIEWED_PLAN,
        attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
    )
    _bound_attempt(stale_old_b)["checkpoint_sha"] = REVIEWED_CHECKPOINT_1094
    stale_old_b["git_head"] = HISTORICAL_REVIEWED_CHECKPOINT
    stale_old_b["git_head_parent"] = HISTORICAL_REVIEWED_B
    stale_old_b["git_checkpoint_parent"] = REVIEWED_PARENT_1094
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authenticate_current_repository_baseline(stale_old_b)

    other_child = _isolated_checkpoint_records(
        implement_base=HISTORICAL_REVIEWED_B,
        plan_id=HISTORICAL_REVIEWED_PLAN,
        attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
        checkpoint_sha=HISTORICAL_REVIEWED_CHECKPOINT,
        checkpoint_parent=HISTORICAL_REVIEWED_B,
    )
    _bound_attempt(other_child)["phase"] = "running"
    other_child["git_head"] = current_b
    other_child["git_head_parent"] = HISTORICAL_REVIEWED_B
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authenticate_current_repository_baseline(other_child)
