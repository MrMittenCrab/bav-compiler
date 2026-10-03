# Step 10.9.4 — Bind baseline authentication to the actual controller attempt
AUTOCYCLE_PLAN: {"finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "objective": "Bind baseline authentication to the actual controller attempt", "plan_id": "ab9f733870294d859da0cf0481edebcf", "predecessor_review_sha256": "279e8aedba489f630f86d4f4b097bb3f0174ac149d93cf263f9172f355e97b28", "step_id": "10.9.4", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

Finish the current attempt’s baseline authentication repair in `core/tests/test_normalization_candidate_admission.py`. Preserve the completed production loader repairs in `modeler/ingestion/normalization_candidate_admission_io.py`.

- Resolve B from populated `IMPLEMENT_BASE_SHA` in `.git/autocycle/resume-state`; otherwise use authenticated implementation-baseline, bound attempt and latest-implementation records. A SHA’s presence alone does not authenticate it. Fail closed when required ownership or baseline evidence is unavailable or inconsistent.
- Read the actual branch’s work and implementation attempt from existing controller records. Bind work identity, attempt identity, attempt plan/baseline SHA and checkpoint SHA to the repository state. Remove the caller’s use of identical hardcoded `WORK_ID` values as proof of ownership and supply actual attempt identities.
- Require nonempty, matching work and attempt bindings before authorizing either implementation-at-B or checkpoint execution. `HEAD == B` must not bypass ownership validation.
- Authorize checkpoint execution only when HEAD equals the checkpoint recorded for that same work and attempt, the attempt’s baseline equals B, and Git confirms the required branch and parent/ancestry relationship.
- Remove the direct-child fallback. Reject an unrecorded direct child of B even when the recorded checkpoint is absent or belongs to another baseline. A stale admitted review cannot substitute for the current attempt’s checkpoint binding.
- Keep historical reviewed checkpoints and comparators separate from current authorization. The reviewed attempt `afa6820bb22e4c8da5b7fcc1a3a3c26b` binds checkpoint `fe04b6ceaec34f825e6c56c2351508ed7fc79078` to B `418f7dc23a52c925d88f9a76ab32cfc33b70e204`; do not hardcode this tuple as authorization for future attempts.
- Use controller evidence read-only. Do not edit `.git/autocycle`, substitute HEAD as B, fabricate missing bindings or introduce recovery infrastructure.

## Verification

- Cover valid bound implementation-at-B and exact recorded checkpoint states.
- Reject absent and mismatched work IDs, attempt IDs, baseline bindings, checkpoint bindings and branches. Exercise missing identities on either side, including at `HEAD == B`.
- Reproduce both direct-child bypasses: no recorded checkpoint, and a recorded checkpoint belonging to old B. Also reject a different child of the correct B when an exact checkpoint is recorded.
- Exercise `_authenticate_current_repository_baseline` through its record-reading and caller path using isolated fixtures derived from existing controller record shapes; helper-only tests are insufficient. Mutate actual observed ownership independently from expected ownership without modifying controller files.
- Retain isolated current-versus-B execution from historical Git blobs and analytical/admission-gate assertions. Preserve separately bound historical comparators, including pre-relocation `eb65dc63845b940162c48e39ae9af7598d2a3078`; allow only intended validation/persistence differences.
- Preserve fresh-process production-loader rejection of reassigned or missing periods, false transformation metadata, provisional adoption, empty treatment, synthetic real-company acceptance and altered source hashes.
- Retain synthetic and independently authorized round trips with all 11 observations’ original periods, hashes, rows, locators, face amounts, exact transformation and analytical values; retain input immutability and repeated-admission rejection.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_normalization_candidate_admission.py`.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_data_ingestion_ownership.py core/tests/test_normalization.py core/tests/test_filing_json.py` and `git diff --check`. Do not skip, deselect, xfail or weaken existing gates.
- Append measured results, actual binding sources and rejection evidence to `RESULT.md`. Preserve historical records; distinguish this repair from parent Completion and Session acceptance.

## Preserved behavior and remaining scope

Preserve fingerprint recomputation and source file/hash, row, period, amount, currency, scale and locator bindings; adopted-status, required-decision, contradiction, membership, analytical identity/scope, treatment/configuration, tax and authorization gates. Preserve exact negative-face transformation, face/analytical agreement and once-only conversion.

Preserve independent authorization’s grouping qualifications, unresolved after-tax treatment, unresolved/unavailable locators and ambiguous-linkage rejection. Never infer printed pages from physical pages or sum overlapping comparative observations. Keep admission default-off, reject blocked/provisional persistence, and retain the separate admission artifact, model-only standardized serialization, standardized-only loading and omission diagnostic.

Preserve completed Modeler data ownership of `interface`, `validators`, `standardized_io`, `line_identity`, `issuer_fiscal`, `historical_operating_kpis` and `historical_segments`; Director retains `data/schema`. Documentary types and historical-strategy contracts remain in Extractor.

Preserve completed Modeler ingestion ownership of `base`, `reconciler`, `filing_reconciler`, `filing_standardizer`, `management_kpi`, `management_kpi_identity`, `management_kpi_reconciliation`, `management_kpi_history`, `operating_kpi`, `geographic_segment`, `share_basis` and KPI validator admission. Director owns `filing_cli`, `note_handoff` and combined validation; Extractor retains documentary binding. Preserve issue ordering, façades, private exports, object identity and inventory mappings.

Preserve public `bav` commands, aliases, lazy loading, optional Trainer independence, dormant forecasting, accounting signs, fiscal distinctions, precision, reconciliations, provenance, residual qualifications and admission/comparison independence. Do not rewrite canonical source or extracted/reconciled inputs.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts/locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; margin prose requires independently selected margin evidence.

Classification/normalization interpretation splits, broader normalization-candidate separation, enrichment/Legacy decomposition, remaining orchestration relocation, unrelated removals, test ownership migration and final repository-wide verification remain subsequent scope. Keep the separate enrichment-sidecar defect visible. Do not add CLI expansion, a general provenance framework, algorithm/report redesign, Trainer expansion or second-phase features.

Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards and zero-byte research placeholders. Reuse verification only while dependencies remain applicable. SESSION native verification remains binding for changed formulas/dependencies or presentation, through Office Bridge. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
