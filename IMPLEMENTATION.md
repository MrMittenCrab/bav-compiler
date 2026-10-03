# Step 10.9.5 — Split normalization-candidate ownership
AUTOCYCLE_PLAN: {"finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "minor": 5, "objective": "Split normalization-candidate ownership", "plan_id": "97df6f3e6a8d433081dde0b05a4492d9", "predecessor_review_sha256": "83d4fdd1de80bbdbebf3700ff8733da78b2a931d74ca09dcc17cdaa4f3b4be3b", "step_id": "10.9.5", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

Decompose `core/ingestion/normalization_candidate_admission.py` by responsibility, completing the normalization-candidate ownership split while preserving the verified lifecycle authentication and production-loader repairs.

- Move provisional construction, analytical-series admission, mechanical adoption/treatment validation, line insertion and configuration construction to `modeler/ingestion/normalization_candidate_admission.py`. Retain admission persistence and recovered-evidence validation in Modeler, reusing `normalization_candidate_admission_io.py`.
- Place shared adoption, treatment and handoff contracts under Director using existing contract conventions. Keep calculation-specific result types with Modeler. Maintain one definition per type and preserve object identity through compatibility exports.
- Separate existing human interpretation and decision qualifications into `interpreter/normalization.py` where executable responsibility exists. Supplied grouping and treatment decisions remain supplied judgments; mechanical validation must not choose them or establish them as source facts. Do not invent an interpretation engine to populate this boundary.
- Move explicit handoff sequencing and save/load coordination to `director/ingestion/normalization_candidate_admission.py`, delegating calculations and persistence to Modeler. Preserve signatures, defaults, result fields, failure reasons and gate ordering.
- Leave the old module as a thin compatibility façade, including existing private exports where required. Update active callers to canonical owners; retain deliberate legacy-import coverage. Canonical implementations must not depend on the compatibility façade or Legacy.
- Update `director/docs/MIGRATION_INVENTORY.md` with actual responsibility destinations and remaining mixed-module scope. Replace the ownership test’s deferred-location assertion for normalization candidates with canonical ownership, import identity and dependency checks; retain the enrichment assertion appropriate to its unchanged state.

## Preservation

Preserve fingerprint recomputation and source file/hash, row, period, amount, currency, scale and locator bindings; adopted-status, required-decision, contradiction, membership, analytical identity/scope, treatment/configuration, tax and authorization gates. Preserve exact negative-face transformation, face/analytical agreement and once-only conversion.

Keep admission default-off and outside ordinary reconciliation. Reject blocked/provisional persistence; preserve the separate admission artifact, model-only standardized serialization, standardized-only loading and omission diagnostic. Preserve input immutability and repeated-admission rejection.

Independent authorization does not establish grouping as source fact. Preserve unresolved after-tax treatment, unresolved/unavailable locators and ambiguous-linkage rejection. Never infer printed pages from physical pages or sum overlapping comparative observations.

Preserve completed Modeler data and ingestion ownership, Director schema and orchestration ownership, Extractor documentary types/binding and historical-strategy contracts, issue ordering, compatibility façades and inventory mappings.

Preserve public `bav` commands, aliases, lazy loading, optional Trainer independence, dormant forecasting, accounting signs, fiscal distinctions, precision, reconciliations, provenance, residual qualifications and admission/comparison independence. Do not rewrite canonical source or extracted/reconciled inputs.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts/locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; margin prose requires independently selected margin evidence.

## Verification

- Resolve and authenticate implementation baseline B through populated `IMPLEMENT_BASE_SHA`, otherwise the normal implementation-baseline, bound-attempt and latest-implementation mechanisms. Preserve strict branch, work, attempt, baseline and exact-checkpoint bindings; fail closed. Read controller evidence only and keep fixtures isolated.
- Compare historical Git blobs at authenticated B with canonical destinations, checking provenance/path continuity and semantic preservation for split files. Retain the separately bound pre-relocation comparator `eb65dc63845b940162c48e39ae9af7598d2a3078`; historical tuples never authorize the live attempt.
- Retain isolated current-versus-B analytical and admission-gate comparisons. Adapt dependency materialization only as needed for canonical imports; preserve comparator independence and all assertions.
- Retain live lifecycle authentication, deterministic implementation/checkpoint fixtures and specific negative rejection cases. The reviewed authentication repair is complete; extend it only for a demonstrated migration regression.
- Exercise canonical entry points and compatibility imports, including fresh-process loading. Preserve rejection of reassigned/missing periods, false transformation metadata, provisional adoption, empty treatment, synthetic real-company acceptance and altered source hashes.
- Retain synthetic and independently authorized round trips with all 11 observations’ original periods, hashes, rows, locators, face amounts, exact transformation and analytical values.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_normalization_candidate_admission.py core/tests/test_data_ingestion_ownership.py core/tests/test_normalization.py core/tests/test_filing_json.py` and `git diff --check`. Do not skip, deselect, xfail or weaken gates.
- Append actual ownership splits, baseline bindings, measured verification and remaining defects to `RESULT.md`; preserve historical records. Distinguish this bounded split from parent Completion and Session acceptance.

## Remaining scope and constraints

Keep the unresolved enrichment-sidecar failure `test_ordinary_prepare_writes_resolution_and_keeps_revenue_per_store` visible and separate. This step does not repair it or establish a fully passing broader suite.

Broader classification/normalization interpretation splits, enrichment/Legacy decomposition, remaining ingestion orchestration, unrelated removals, test ownership migration and final repository-wide verification remain unfinished commitments. Do not add CLI expansion, a general provenance framework, algorithm/report redesign, Trainer expansion or second-phase features.

Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards and zero-byte research placeholders. Reuse verification only while dependencies remain applicable. Changed workbook formulas/dependencies or presentation retain SESSION’s native verification requirements through Office Bridge. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
