"""Ordinary debate intake and approval. Zero provider launches."""

from __future__ import annotations

import argparse
import json
import threading
from pathlib import Path

import pytest

from bav.debater.intake import load_intake_fixtures
from bav.director.cli import main
from bav.director.debate import command as debate_command
from bav.director.debate.command import execute_debate
from bav.director.debate.store import canonical_json, locked_case
from bav.extractor.research.paths import sha256_text
from bav.director.debate.terminal import format_terminal
from bav.extractor.research.contracts import InventoryRecord, SnapshotInventory

BENCHMARK = (
    "Fast Retailing's acquisition of Lululemon would accelerate Lululemon's growth in Asia."
)
PRODUCT_FIT = "Lululemon and Fast Retailing have product fit."
def _inventory(*, fingerprint: str = "fp-test") -> SnapshotInventory:
    lulu = InventoryRecord(
        document_id="lulu-fy2025-annual-report",
        company_slug="lululemon",
        case_local=False,
        original_filename="LULU_FY2025_Annual_Report.pdf",
        original_sha256="82" * 32,
        prepared_sha256="c2" * 32,
        converter_profile_id="fixture",
        representation="converted_markdown",
        publication_date_status="unknown",
        issuer_status="assigned",
        limitations=("garbled_text",),
        bundle_dir=Path("."),
    )
    fr = InventoryRecord(
        document_id="fastretailing-cfs-2025",
        company_slug="fast_retailing",
        case_local=False,
        original_filename="Fastretailing_CFS2025.pdf",
        original_sha256="25" * 32,
        prepared_sha256="63" * 32,
        converter_profile_id="fixture",
        representation="converted_markdown",
        publication_date_status="unknown",
        issuer_status="assigned",
        limitations=("cfs_only", "missing_note_6d_table"),
        bundle_dir=Path("."),
    )
    return SnapshotInventory(
        snapshot_id="2026-10-04-debater-asia-benchmark",
        snapshot_fingerprint=fingerprint,
        records=(lulu, fr),
        coverage_gaps=(
            "lulu-fy2025-annual-report:garbled_text",
            "fastretailing-cfs-2025:cfs_only",
            "fastretailing-cfs-2025:missing_note_6d_table",
        ),
    )


def _args(**values):
    defaults = {
        "proposition": None,
        "case": None,
        "list": False,
        "status": False,
        "approve": False,
        "exclude": None,
        "add": None,
        "note": None,
        "backend": None,
    }
    defaults.update(values)
    return argparse.Namespace(**defaults)


def _run(tmp_path, **values):
    return execute_debate(
        _args(**values),
        cases_dir=tmp_path,
        inventory=_inventory(),
        fixtures=load_intake_fixtures(),
    )


@pytest.fixture(autouse=True)
def _forbid_provider(monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("provider must not launch during intake")

    monkeypatch.setattr("bav.director.runtime.adapter.ResearchRuntime.invoke", boom)
    monkeypatch.setattr("bav.director.runtime.verification.run_verification", boom)
    debate_command.PROVIDER_LAUNCHES.update(invoke=0, verify=0, company_transmission=0)


def _assert_terminal(envelope):
    text = format_terminal(envelope)
    assert envelope.provider_launched is False
    assert envelope.company_transmitted is False
    for line in text.splitlines():
        if ":" in line:
            assert line.startswith("Case:") or line.startswith("Status:") or line.startswith("Next:")
    assert "Status:" not in text
    return text


def test_benchmark_submit_displays_proof_plan(tmp_path):
    envelope = _run(tmp_path, proposition=BENCHMARK)
    text = _assert_terminal(envelope)
    assert envelope.exit_code == 0
    assert envelope.case_title == (
        "Fast Retailing acquisition would accelerate Lululemon growth in Asia"
    )
    assert envelope.pending_kind == "proof_plan"
    assert "Confirm proof plan" in text
    assert "Hypothetical acquisition" in text
    assert BENCHMARK in text
    assert "Japan and Greater China" in text
    assert "continued independence" in text
    assert "Store count is not the measure" in text
    assert "uplift, closing date, forecast, horizon" in text
    assert "acquisition valuation" in text
    assert "would, not might" in text
    assert "Two company descriptions are not a linked argument" in text
    assert "lulu-fy2025-annual-report" in text
    assert "fastretailing-cfs-2025" in text
    assert "garbled_text" in text or "garbled text" in text
    payload = json.loads((tmp_path / envelope.case_slug / "case.json").read_text())
    assert payload["status"] is None
    assert payload["proposition"]["original"] == BENCHMARK
    assert payload["allowance"]["backend_calls"] == 12


def test_unclear_proposition_creates_no_case(tmp_path):
    envelope = _run(tmp_path, proposition="growth")
    assert envelope.exit_code == 0
    assert envelope.case_slug is None
    assert "Resubmit" in envelope.next_lines[0]
    assert list(tmp_path.glob("*/case.json")) == []


def test_ambiguous_meanings_then_exclude_and_plan(tmp_path):
    first = _run(tmp_path, proposition=PRODUCT_FIT)
    assert first.pending_kind == "meanings"
    assert "Confirm meanings" in first.next_lines[0]
    all_meanings = _run(tmp_path, case="product fit", approve=True)
    assert "narrower propositions" in all_meanings.next_lines[0]
    assert all_meanings.pending_kind is None
    second = _run(tmp_path, proposition="Lululemon reported ten stores in Japan.")
    assert second.pending_kind is None
    assert "Installed launch is closed" in second.next_lines[0]
    other = tmp_path / "other"
    other.mkdir()
    fresh = execute_debate(
        _args(proposition=PRODUCT_FIT),
        cases_dir=other,
        inventory=_inventory(),
        fixtures=load_intake_fixtures(),
    )
    excluded = execute_debate(
        _args(case="product fit", approve=True, exclude="2,3"),
        cases_dir=other,
        inventory=_inventory(),
        fixtures=load_intake_fixtures(),
    )
    assert excluded.pending_kind == "proof_plan"
    assert "Confirm proof plan" in excluded.next_lines[0]
    approved = execute_debate(
        _args(case="product fit", approve=True),
        cases_dir=other,
        inventory=_inventory(),
        fixtures=load_intake_fixtures(),
    )
    assert approved.kind == "plan_approved"
    assert approved.pending_kind is None
    assert "Approved scope and plan are saved locally" in "\n".join(approved.next_lines)
    payload = json.loads((other / approved.case_slug / "case.json").read_text())
    assert payload["approved_plan"]["plan_id"] == "product-fit"
    assert payload["pending"] is None


def test_negated_and_reworded_propositions_are_separate_cases(tmp_path):
    baseline = _run(tmp_path, proposition=BENCHMARK)
    negated = _run(
        tmp_path,
        proposition=(
            "Fast Retailing's acquisition of Lululemon would not accelerate "
            "Lululemon's growth in Asia."
        ),
    )
    reworded = _run(
        tmp_path,
        proposition=(
            "An acquisition of Lululemon by Fast Retailing would speed "
            "Lululemon's Asian expansion."
        ),
    )
    slugs = {
        baseline.case_slug,
        negated.case_slug,
        reworded.case_slug,
    }
    assert len(slugs) == 3
    listing = _run(tmp_path, list=True)
    assert len(listing.next_lines) == 4


def test_title_collision_and_ambiguous_fragment(tmp_path):
    left = "X" * 90 + " would grow now."
    right = "X" * 90 + " would shrink later."
    first = _run(tmp_path, proposition=left)
    second = _run(tmp_path, proposition=right)
    assert first.case_title != second.case_title
    assert "alt wording" in second.case_title
    fragment = _run(tmp_path, case="XXX")
    assert fragment.kind == "ambiguous_case"
    assert fragment.mutated is False
    missing = _run(tmp_path, case="no-such-case")
    assert "python -m bav debate --list" in missing.next_lines[0]


def test_conflicting_and_unimplemented_options_leave_authority(tmp_path):
    created = _run(tmp_path, proposition=BENCHMARK)
    before = (tmp_path / created.case_slug / "case.json").read_text()
    conflict = _run(tmp_path, case=created.case_title, approve=True, backend="cursor")
    assert conflict.exit_code == 1
    added = _run(tmp_path, case=created.case_title, add=["file.md"])
    assert added.exit_code == 1
    note = _run(tmp_path, case=created.case_title, note="unavailable")
    assert note.exit_code == 1
    exclude = _run(tmp_path, case=created.case_title, exclude="1")
    assert exclude.exit_code == 1
    listed = _run(tmp_path, list=True, proposition=BENCHMARK)
    assert listed.exit_code == 1
    assert (tmp_path / created.case_slug / "case.json").read_text() == before


def test_invalid_exclude_on_proof_plan_does_not_mutate(tmp_path):
    created = _run(tmp_path, proposition=BENCHMARK)
    before = (tmp_path / created.case_slug / "case.json").read_text()
    result = _run(tmp_path, case="growth in Asia", approve=True, exclude="1")
    assert result.exit_code == 1
    assert "displayed meanings" in result.next_lines[0]
    assert (tmp_path / created.case_slug / "case.json").read_text() == before


def test_approve_then_resume_and_status_reuse_saved_state(tmp_path):
    submitted = _run(tmp_path, proposition=BENCHMARK)
    first_path = tmp_path / submitted.case_slug / "case.json"
    pending_rev = json.loads(first_path.read_text())["pending"]["revision"]
    approved = _run(tmp_path, case="growth in Asia", approve=True)
    assert approved.kind == "plan_approved"
    assert "Installed launch is closed" in approved.next_lines[0]
    payload = json.loads(first_path.read_text())
    assert payload["approved_scope"]["growth_measure"]
    assert payload["pending"] is None
    assert pending_rev not in (payload.get("pending") or {})
    resume = _run(tmp_path, case="growth in Asia")
    status = _run(tmp_path, case="growth in Asia", status=True)
    assert resume.next_lines == approved.next_lines
    assert status.next_lines == approved.next_lines
    assert resume.mutated is False
    assert status.mutated is False
    assert resume.details["authority"] == sha256_text(canonical_json(payload))
    leftover = json.loads(first_path.read_text())
    assert leftover["allowance"]["backend_calls"] == 12
    consumed = _run(tmp_path, case="growth in Asia", approve=True)
    assert consumed.exit_code == 1
    assert json.loads(first_path.read_text())["approved_plan"]["revision"] == payload["approved_plan"]["revision"]


def test_changed_binding_requires_subsequent_approval(tmp_path):
    submitted = _run(tmp_path, proposition=BENCHMARK)
    path = tmp_path / submitted.case_slug / "case.json"
    payload = json.loads(path.read_text())
    authority = canonical_json(payload)
    payload["pending"]["input_fingerprint"] = "tampered"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    changed = _run(tmp_path, case="growth in Asia", approve=True)
    assert changed.kind == "approval_rebound"
    assert "subsequent approval" in changed.next_lines[0]
    updated = json.loads(path.read_text())
    assert updated["pending"]["consumed"] is False
    assert canonical_json(updated) != authority
    approved = _run(tmp_path, case="growth in Asia", approve=True)
    assert approved.kind == "plan_approved"


def test_concurrent_lock_and_interrupted_tmp_leave_authority(tmp_path):
    submitted = _run(tmp_path, proposition=BENCHMARK)
    directory = tmp_path / submitted.case_slug
    before = (directory / "case.json").read_bytes()
    (directory / "case.json.leftover.tmp").write_text("{", encoding="utf-8")
    held = threading.Event()
    release = threading.Event()

    def holder():
        with locked_case(directory, nonblocking=False):
            held.set()
            release.wait(2)

    thread = threading.Thread(target=holder)
    thread.start()
    assert held.wait(2)
    locked = _run(tmp_path, case="growth in Asia", approve=True)
    release.set()
    thread.join()
    assert locked.exit_code == 1
    assert (directory / "case.json").read_bytes() == before
    resume = _run(tmp_path, case="growth in Asia", status=True)
    assert resume.exit_code == 0
    assert resume.mutated is False


def test_backend_change_is_rejected_without_resetting_budget(tmp_path):
    submitted = _run(tmp_path, proposition=BENCHMARK)
    path = tmp_path / submitted.case_slug / "case.json"
    before = json.loads(path.read_text())
    result = _run(tmp_path, case="growth in Asia", backend="codex")
    assert result.exit_code == 1
    after = json.loads(path.read_text())
    assert after["allowance"] == before["allowance"]
    assert after["backend"]["backend"] == "cursor"
    assert after == before


def test_repeated_submit_resumes_same_case(tmp_path):
    first = _run(tmp_path, proposition=BENCHMARK)
    second = _run(tmp_path, proposition=BENCHMARK)
    assert second.mutated is False
    assert second.case_slug == first.case_slug
    assert len(list(tmp_path.glob("*/case.json"))) == 1


def test_cli_wiring_uses_injected_cases(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(debate_command, "cases_root", lambda **_kwargs: tmp_path)
    monkeypatch.setattr(
        debate_command,
        "_load_inventory",
        lambda _fixtures: _inventory(),
    )
    assert main([
        "debate",
        BENCHMARK,
    ]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Case: ")
    assert "Next: Confirm proof plan" in out
    assert "Status:" not in out
    assert main(["debate", "--case", "growth in Asia", "--status"]) == 0
    assert main(["debate", "--list"]) == 0


def test_live_corpus_inventory_binds_benchmark_plan(tmp_path):
    from bav.director.research_corpus import inventory_approved_snapshot

    inventory = inventory_approved_snapshot()
    assert {record.document_id for record in inventory.records} >= {
        "lulu-fy2025-annual-report",
        "fastretailing-cfs-2025",
    }
    envelope = execute_debate(
        _args(proposition=BENCHMARK),
        cases_dir=tmp_path,
        inventory=inventory,
        fixtures=load_intake_fixtures(),
    )
    text = _assert_terminal(envelope)
    assert inventory.snapshot_id == "2026-10-04-debater-asia-benchmark"
    assert inventory.snapshot_fingerprint
    payload = json.loads((tmp_path / envelope.case_slug / "case.json").read_text())
    assert payload["corpus"]["snapshot_fingerprint"] == inventory.snapshot_fingerprint
    assert "Japan and Greater China" in text
    assert envelope.provider_launched is False
