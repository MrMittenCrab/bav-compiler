# Step 10.9.1 — Relocate data contracts and ingestion responsibilities — normalization-candidate verification repair

AUTOCYCLE_PLAN: {"evidence_routes": [{"commands": [["/opt/anaconda3/bin/python", "-m", "pytest", "-q", "core/tests/test_normalization_candidate_admission.py"], ["/opt/anaconda3/bin/python", "-m", "pytest", "-q", "core/tests/test_data_ingestion_ownership.py", "core/tests/test_normalization.py", "core/tests/test_filing_json.py"]], "fact": "Normalization-candidate admission, rejection, standardized round-trip and provenance compatibility under the relocated canonical dependencies lacks completed behavioral verification."}], "finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "minor": 1, "objective": "Relocate data contracts and ingestion responsibilities — normalization-candidate verification repair", "plan_id": "ec5ab3a7c0864203ae074b8100804557", "predecessor_review_sha256": "405ddfe1feeed94af3212b7c533edee4ef84abcc762dfef030b65151254c3eef", "step_id": "10.9.1", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

Repair the normalization-candidate test fixtures and complete behavioral verification against authenticated B without repeating completed relocation.

- Authenticate the continuation baseline through populated `IMPLEMENT_BASE_SHA`, otherwise normal baseline, branch, ancestry and attempt/checkpoint bindings; fail closed if unavailable. Retain `eb65dc63845b940162c48e39ae9af7598d2a3078` as the authenticated pre-relocation comparison B for checkpoint `38f5774170c577aa10eb5f03c4cbe99ed7cff789`.
- Replace the historical `/tmp` qualification/prototype dependency in `core/tests/test_normalization_candidate_admission.py` with reproducible repository fixtures or deterministic pytest fixture construction. Use B Git blobs where available and verified canonical source/extracted evidence with normal path continuity otherwise.
- Derive observations from source rows, preserving identities, fiscal periods, values, currency, units, source hashes and physical/printed-page provenance. Keep expected analytical results independently specified; never generate expected results from the implementation under test. Mark synthetic adoption/treatment records explicitly as test authorization.
- Replace obsolete temporary-artifact hash assertions with checks of reproducible input binding and immutability. Missing historical temporary scripts and payloads require no reconstruction. Preserve every behavioral scenario previously prevented from executing; do not skip, deselect, xfail or weaken those checks.
- Exercise the same reproducible cases against B and current canonical dependencies in isolated processes. Use historical Git code directly and only necessary test import/path adaptations; keep B production code unchanged. Compare admission decisions, rejection gates/reasons, signed series, selector behavior, standardized export/reload and source/transformation provenance.
- Extend the existing test module where needed to assert provenance survives round-trip, including observation fingerprints, source hashes, locators, row identities and sign transformation. Preserve input immutability and rejection of repeated admission.
- Limit edits to this test module and directly necessary test fixtures/helpers. If verification demonstrates a production defect, record the concrete mismatch for Review rather than expanding into architectural changes.

## Verification

Normalization-candidate admission, rejection, standardized round-trip and provenance compatibility under the relocated canonical dependencies lacks completed behavioral verification.

Criterion: IMPLEMENTATION.md explicitly requires normalization-candidate compatibility and B-derived admission/rejection comparisons to establish preserved analytical behavior.

- Run both command lists in `evidence_routes`. All twenty formerly blocked cases must execute their checks successfully alongside the two previously passing tests.
- Cover absent/provisional/stale/contradictory adoption, missing or conflicting treatment, invalid source binding, missing periods, overlapping conflicts, unauthorized membership, cash-flow substitution, Studio/component exclusion, duplicate use, absent/repeated sign conversion and ambiguous selectors.
- Verify synthetic admission remains distinct from real-company acceptance, default admission remains disabled, recurring/non-recurring pretax consequences agree with B, and unresolved after-tax treatment remains unresolved.
- Reuse the reviewed ownership, relocation, affected-regression and company build/check/publish evidence only while its dependencies remain unchanged. Preserve outstanding B-derived comparisons; prior setup errors and filtered passes do not satisfy them.
- Run `git diff --check`; record checkpoint whitespace advisories separately without unrelated cleanup.
- Append exact commands, executed case counts, fixture derivation/bindings, B/current comparisons and remaining limitations to `RESULT.md`. Keep the separate enrichment-sidecar failure visible; do not claim the broader suite fully passes.

## Preserved relocation and constraints

Completed Modeler data ownership covers `interface`, `validators`, `standardized_io`, `line_identity`, `issuer_fiscal`, `historical_operating_kpis` and `historical_segments`; Director retains `data/schema`. Documentary types and historical-strategy contracts remain in Extractor.

Completed Modeler ingestion ownership covers `base`, `reconciler`, `filing_reconciler`, `filing_standardizer`, `management_kpi`, `management_kpi_identity`, `management_kpi_reconciliation`, `management_kpi_history`, `operating_kpi`, `geographic_segment`, `share_basis` and KPI validator admission. Director owns `filing_cli`, `note_handoff` and combined validation; Extractor retains documentary binding. Preserve issue ordering, façades, private exports, object identity and inventory mappings.

Preserve signatures, public commands, aliases, lazy loading, optional Trainer independence, dormant forecasting, accounting signs, fiscal distinctions, precision, reconciliations, source/transformation provenance, residual qualifications and admission/comparison independence. Do not rewrite canonical source or extracted/reconciled inputs.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts/locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; margin prose requires independently selected margin evidence.

Classification/normalization interpretation splits, normalization-candidate separation, enrichment/Legacy decomposition, remaining orchestration relocation, unrelated removals, test ownership migration and final repository-wide verification remain subsequent scope. Do not repair the enrichment-sidecar defect, redesign algorithms/reports, expand Trainer or implement second-phase features.

Preserve ownership/recovery safeguards, protected documents, unrelated dirty work and zero-byte research placeholders. SESSION native verification remains binding if formulas/dependencies or presentation change, through Office Bridge. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
