# BAV Compiler — repository responsibility inventory

Step 10.1 design only. No runtime code was moved, deleted, or regenerated.
Every meaningful responsibility has exactly one disposition: Director, Extractor,
Modeler, Interpreter, Composer, Legacy, or Remove. Classification follows the
kind of decision. Configuration, tests, data and documentation inherit an
owner and are not additional active components. Do not create `remove/`.

Authenticated continuation baseline **B** = `2f292e955fa4e4d1828d795f472ae0ed15764cbf`
(Plan 10.1.2; HEAD). Independently authenticated from populated
`IMPLEMENT_BASE_SHA`. The reviewed 10.1.1 attempt used B
`312cb8aff118d427a73a3ad202693d2019d692bf` and checkpoint
`49a0a26c06675e24c898ff51bd471d1cec9419d3`; both are ancestors of this B
(`86ebdec` → `02d7fcd` Step 10.1 → `312cb8a` Plan 10.1.1 → `49a0a26` Step
10.1.1 → `2f292e9`). Mixed assessment source blobs
`core/model/reported_margin.py` and `core/model/revenue_driver.py` are
byte-identical at `312cb8a`, B and the working tree. Tracked historical
content is the Git tree at this continuation’s B. Loader and synthesis
decisions from 10.1.1 are retained. Current working-tree files were
inspected for local inputs, generated outputs and empty leftover dirs.

---

## 1. Baseline authentication

| Record | Value | Result |
|---|---|---|
| `.git/autocycle/resume-state` `IMPLEMENT_BASE_SHA` | `2f292e955fa4e4d1828d795f472ae0ed15764cbf` | Populated; used as B |
| `STATE_BRANCH` | `checkpoint/20260913-183303` | Matches `.git/HEAD` |
| `.git/refs/heads/checkpoint/20260913-183303` | `2f292e955fa4e4d1828d795f472ae0ed15764cbf` | HEAD == B |
| `.git/autocycle/implementation-baseline.json` `head` / `branch` | same SHA / same branch | Bound |
| `.git/autocycle/work-state.json` allocated `10.1.2` | `source` = B, `work_id` = `7951a38d066a440e8bfa19cd9dc5ecc7`, `status` = `opened` | Attempt bound |
| `IMPLEMENTATION.md` `AUTOCYCLE_PLAN` | `step_id` 10.1.2, same `work_id` | Bound |
| Ancestry | HEAD equals B; `312cb8a…` and `49a0a26…` are ancestors of HEAD | Fail-closed not required |
| Reviewed 10.1.1 B / checkpoint | `312cb8a…` / `49a0a26…` | Historical blob reference only; not this continuation’s B |
| `.git/autocycle/latest-implementation` | Still names `312cb8a…` | Ignored: `IMPLEMENT_BASE_SHA` is populated |

Fail-closed was not required. `latest-implementation` is leftover from the
reviewed 10.1.1 attempt and is not the implementation baseline.

---

## 2. Evidence classes

| Class | What | Continuity rule |
|---|---|---|
| Tracked at B | `implementation-baseline.json` file set: `bav/`, `core/`, `scripts/`, `automation/`, `skills/`, `docs/`, `example/` (5 files), `legacy/`, root planning/docs, config, `bav-pipeline-plugin.zip`. **No** `build/`, **no** current `benchmark/` or `release/` files, **no** PDFs | Git blobs at B are historical authority. Tracked moves compare destination bytes to `git show B:path` |
| Reproducible generated | `build/output/**`, example sidecars named in `.gitignore`, `__pycache__/`, `.pytest_cache/`, plugin zip via `scripts/build_plugin_zip.sh` | No historical preservation duty. Current correctness governs |
| Irreplaceable non-Git working inputs | `build/input/{lululemon,fast_retailing}/extracted/*.json` and `reconciled/*.json` (gitignored `/build/`). Local copies exist | Canonical destinations **are** those paths. Do not relocate until a surviving destination is verified |
| Irreplaceable source PDFs | Canonical destination: `build/input/<company>/source/`. **Absent** in the current working tree. **Not tracked at B**. `build/input/fast_retailing/source_manifest.json` still names obsolete `benchmark/fast_retailing/source/*.pdf` | Before any PDF appears and is moved or deleted, establish the canonical `source/` destination and verify bytes. Do not invent a backup tree. Historical Git (pre-B) may still hold `benchmark/*/source/` blobs; inspect with `git show` when needed |
| Protected planning | `TARGET.md`, `SESSION.md`, `IMPLEMENTATION.md` stay at repository root. `RESULT.md` stays at root as the implementation record | Cursor must not modify TARGET / SESSION / IMPLEMENTATION |

Empty leftover directories `benchmark/` and `release/` (`.DS_Store` only) are
not source evidence. `lululemon-live` and `coverage/` are absent.

---

## 3. Area coverage

Every top-level and `core/` area is classified below. Homogeneous files share
an entry. Mixed files have separate responsibility rows.

| Area | Section | Notes |
|---|---|---|
| Hidden / config | 4.1 | `.autocycle.toml`, `.gitignore`, `.cursor/`, `.claude-plugin/`, requirements |
| Public `bav` package | 4.2 | Preserve `python -m bav` |
| `core/__main__.py`, `current_build.py`, `build_status.py`, `project_companies.json` | 4.2, 10 | Director orchestration |
| `core/data/` | 4.3, 7 | Split Extractor contract vs Modeler payload |
| `core/ingestion/` | 7.3 | Extractor JSON contract I/O; Modeler admit/reconcile; no PDF extractor |
| `core/model/` | 4.4, 7.0, 7.1, 7.4 | Homogeneous Modeler plus exhaustive revenue-driver, synthesis and reported-margin assessment splits |
| `core/engine/` | 10 | Workbook construction = Modeler; registry policy = Director |
| `core/trainer/` | 10 | Invert: BAV build is Modeler; practice overlay is Legacy |
| `core/research/` | 5–9 | Mixed Driver split |
| `core/tests/` + fixtures | 4.5 | Inherited owners |
| `scripts/` | 4.6 | |
| `automation/` | 4.7 | Not cloud product infra |
| `skills/`, plugin zip | 4.8 | Legacy coverage pipeline |
| Docs / README / STYLE / DRIVER | 4.9, 11 | |
| `example/` | 4.10 | |
| Existing `legacy/` | 4.11 | Stay |
| Company inputs / outputs | 4.12 | |
| Obsolete / caches / stubs | 13 | Remove candidates |
| `director/`, `extractor/`, `modeler/`, `interpreter/`, `composer/` | absent at B | Create during later relocation steps |

Absent (do not invent): `pyproject.toml`, `setup.py`, `setup.cfg`, `package.json`,
`MANIFEST.in`, AWS/GCP/Terraform, `director/` at B (this inventory is the first
Director-docs file).

---

## 4. Responsibility inventory

Columns: current path or bounded range → canonical destination → callers →
disposition → reason → verification.

### 4.1 Configuration

| Current | Destination | Callers | Disposition | Reason | Verification |
|---|---|---|---|---|---|
| `.autocycle.toml` | stay root (Director policy) | Office Bridge | Director | Native Office capability, not analysis | capabilities probe |
| `.gitignore` | stay root | Git | Director | Generated vs source policy | `git check-ignore -v build/` |
| `.cursor/cli.json` | stay `.cursor/` | Cursor CLI | Director | Local agent policy | not imported by `bav` |
| `requirements-trainer.txt` | stay root | README, install | Director | Active runtime deps | `pip install -r` then `python -m bav` |
| `requirements-benchmark.txt` | with extract helper | `scripts/extract_benchmark_pdf_text.py` | Legacy | `pypdf` for obsolete text cache | that script only |
| `.claude-plugin/plugin.json` | `legacy/plugin/` or stay with skills | `scripts/build_plugin_zip.sh` | Legacy | Superseded coverage-skill product | zip rebuild |
| `.DS_Store` | delete in place | Finder | Remove | OS junk; already gitignored | no import |
| `__pycache__/`, `.pytest_cache/` | delete in place | CPython / pytest | Remove | Regenerable; already gitignored | reimport source |

### 4.2 Public package, CLI, company routing

Preserve public package name `bav` and company interfaces
`python -m bav {build,check,publish,list} Lululemon|FastRetailing`.

| Current | Destination | Callers | Disposition | Reason | Verification |
|---|---|---|---|---|---|
| `bav/__init__.py`, `bav/__main__.py` (`from core.__main__ import main`) | keep `bav/` at repo root | humans, tests | Director | Public identity; thin route | `python -m bav --help`; `test_build_cli.py` |
| `core/__init__.py` `__version__ = "0.1.0"` | stay as compatibility package; rewrite Trainer branding when copy is touched | imports | Director | Package identity | version string |
| `core/__main__.py` `main` / argparse | `director/cli.py`; `python -m core` remains an alias | `bav/__main__.py` | Director | Lifecycle coordination | `test_build_cli.py`, `test_filing_cli.py` |
| `cmd_build` company path | Director orchestration calling Modeler + Composer | `python -m bav build <Company>` | Director | Does not choose accounting | `test_current_build.py`; Lulu/FR build |
| `cmd_build` argparse / company path | `director/cli.py` `cmd_build` | CLI | Director | Route only | `test_build_cli.py` |
| `cmd_build` explicit JSON `-o` Trainer derive body | `legacy/trainer/derive.py` (existing `build_training_workbook` path) | compatibility users | Legacy | Dual-output body; not a second active architecture | `test_build_cli.py` |
| `cmd_check` / `cmd_publish` / `cmd_list` | Director routes | CLI | Director | Check diagnostic; publish Composer; list Modeler catalog | company check/publish/list |
| `cmd_validate_source` | Director route over Extractor contract + Modeler bind | CLI | Director | Orchestrates already-extracted JSON | `test_filing_cli.py` |
| `cmd_reconcile` | Director route; body Modeler | CLI | Director | Writes reconciled artifacts | `test_filing_reconciler.py` |
| `cmd_ingest` argparse / route | `director/cli.py` `cmd_ingest` | CLI | Director | Route only | ingest tests |
| `HKManualDocumentAdapter` | `legacy/ingestion/manual_hk.py` | `cmd_ingest` | Legacy | Transcribed HK ingest, not canonical company path | ingest tests |
| `core/current_build.py` `PROJECTS`, `resolve_company`, `build_company`, `check_company_output`, `prepare_company_input`, atomic exchange | `director/current_build.py` | CLI, `document.py`, tests | Director | “Company metadata selects evidence locations, never accounting behavior” | `test_current_build.py` |
| `core/project_companies.json` | `director/project_companies.json` | `current_build.PROJECTS` | Director | Names/slugs/aliases/fixture paths | resolve Lululemon/LULU/FastRetailing/9983 |
| `core/build_status.py` | `modeler/build_status.py` | `build_company` | Modeler | Mechanical family availability | `test_current_build.py` |

### 4.3 Data contracts

| Current | Destination | Callers | Disposition | Reason | Verification |
|---|---|---|---|---|---|
| `core/data/filing.py` (`ExtractedFiling`, `SourceRef`, `FilingMetadata`) | `extractor/data/filing.py` (contract only) | ingestion loaders | Extractor | Documentary extracted-filing schema. Engine does not produce it from PDF | `test_filing_json.py` |
| `core/data/interface.py` `DocumentManifest`, `DataSourceAdapter` | `extractor/data/interface.py` | `HKManualDocumentAdapter`, ingest | Extractor | Source-document handoff | ingest tests |
| `core/data/interface.py` `StandardizedFinancials`, `LineItem`, statements | `modeler/data/interface.py` | engine, model, CLI, research | Modeler | Model-facing payload. Director documents the handoff in `director/docs/`; it does not own the type | `standardized_from_payload(..., strict=True)` |
| `core/data/schema.py` `validate_standardized` | `director/data/schema.py` | exported only | Director | Unused completeness contract; keep, do not Remove, until out-of-tree use is known | grep remains export-only |
| `core/data/validators.py` statement checksums | `modeler/data/validators.py` | reconciler, build refuse | Modeler | Arithmetic identities on standardized statements | `test_validators.py` |
| `core/data/standardized_io.py` | `modeler/data/standardized_io.py` | `prepare_company_input`, CLI | Modeler | Model-only JSON; strips formulas | round-trip tests |
| `core/data/line_identity.py` | `modeler/data/line_identity.py` | merge/classify | Modeler | Line identity | `test_line_identity.py` |
| `core/data/issuer_fiscal.py` | `modeler/data/issuer_fiscal.py` | `prepare_company_input` | Modeler | Issuer FY labels; never from calendar year of period-end | `test_issuer_fiscal.py` |
| `core/data/historical_operating_kpis.py` | `modeler/data/historical_operating_kpis.py` | KPI/geo, IO | Modeler | Validated analytical contract | KPI tests |
| `core/data/historical_segments.py` | `modeler/data/historical_segments.py` | geo IO | Modeler | Validated analytical contract | geo tests |
| `core/data/historical_strategy.py` types, `load_strategy_disclosures`, `deserialize_historical_strategy`, `serialize_historical_strategy`, `validate_historical_strategy`, locators | `extractor/data/historical_strategy.py` | `prepare_company_input`, `standardized_io` | Extractor | Source-bound text+locator I/O and round-trip identity; not economic interpretation | `test_revenue_driver.py` |
| fixture `core/tests/fixtures/strategy/lululemon_management_disclosures.json` | stay fixture path until company-input promotion | `project_companies.json` | Extractor-shaped attributed evidence | Same | `test_revenue_driver.py` |

### 4.4 Homogeneous Modeler modules

These files perform reproducible calculations from the same inputs and explicit
assumptions. Destination: `modeler/` keeping the current basename unless a
later split is listed.

| Current files | Disposition | Callers | Verification |
|---|---|---|---|
| `classification.py`, `financial_math.py`, `line_resolver.py`, `period_axis.py`, `ratio_values.py`, `source_values.py`, `source_availability.py`, `historical_expected.py` | Modeler | engine, tests | matching `core/tests/test_*.py` |
| `normalization.py` series arithmetic; `normalized_per_share.py` | Modeler | builder, checker | `test_normalization.py`, `test_normalized_per_share.py` |
| `revenue_per_store.py`, `geographic_segment.py`, `operating_kpi.py`, `operating_kpi_relationships.py`, `management_kpi.py` | Modeler | research assemble, workbook | corresponding tests + `test_research_drivers.py` series |
| `earnings_quality.py`, `earnings_quality_change.py`, `working_capital.py`, `profitability_drivers.py`, `profitability_change.py`, `roe_attribution.py`, `per_share.py`, `per_share_attribution.py`, `inventory_analysis.py`, `cash_rollforward.py`, `capex.py`, `fixed_asset.py`, `lease_liability.py`, `lease_rou.py`, `lease_repayment.py`, `deferred_tax.py`, `goodwill_intangibles.py`, `acquisition_cash.py`, `share_repurchase.py`, `ownership_attribution.py` | Modeler | engine, benchmarks | matching tests; Lulu/FR benchmarks |
| `operating_forecast.py` | Modeler (dormant) | `test_operating_forecast.py` only | Do not activate |
| `ri_engine.py` | Modeler (dormant) | `ReferenceModelBuilder` only if `include_deferred_forecast` | `test_normal_v1_build_does_not_call_run_scenario` |

Mixed inside otherwise Modeler files:

| Current | Destination | Disposition | Reason |
|---|---|---|---|
| `judgment.py` `classification_judgment_cases` (case list from `decision.ambiguous`) | `modeler/judgment.py` | Modeler | Deterministic case selection |
| `judgment.py` `CLASSIFICATION_JUDGMENT_TEMPLATES` rationale / consequence / prompt | `interpreter/classification_judgment.py` | Interpreter | Meaning of alternatives |
| `normalization.py` case IDs, series, treatment selection | `modeler/normalization.py` | Modeler | Reproducible series | `test_normalization.py` |
| `normalization.py` treatment rationales | `interpreter/normalization.py` | Interpreter | Meaning of alternatives | same tests’ rationale assertions |
| `revenue_driver.py` | see §7.0 | split | Mixed; do not treat as homogeneous Modeler |
| `revenue_strategy_synthesis.py` | see §7.1 | split | Mixed |
| `reported_margin.py` | see §7.4 | split | Mixed; series/residuals stay Modeler; assessment judgments and wording do not |

### 4.5 Tests (inherited owners)

Tests are not a sixth component. Destination = owner’s `tests/` after the
implementation move.

| Group | Owner |
|---|---|
| `test_filing_json.py` parse / serialize / schema-reject cases | Extractor |
| `test_filing_cli.py` | Director (route) calling Extractor load + Modeler validate/admit |
| `test_management_kpi_admission.py` `load_extracted_json_object` / `classify_extracted_payload` / `load_extracted_filing` schema cases | Extractor |
| `test_management_kpi_admission.py` admit/bind cases | Modeler |
| `test_management_kpi_{enrichment,identity,reconciliation,history}.py` | Legacy enrich; Modeler identity/reconcile/history |
| `test_operating_kpi_facts.py`, `test_geographic_segment_facts.py` load/round-trip | Extractor load + Modeler admit |
| `test_normalization_candidate_admission.py` | Modeler (provisional) |
| `test_filing_reconciler.py`, `test_validators.py`, `test_issuer_fiscal.py`, `test_line_identity.py`, `test_line_resolver.py`, `test_classification.py`, `test_share_basis.py`, `test_historical_segment.py`, `test_source_availability.py`, `test_normalization.py` | Modeler |
| `test_reported_margin.py` series / signs / residuals / availability / catalog / workbook formulas | Modeler (`modeler/tests/test_reported_margin.py`) |
| `test_reported_margin.py` assessment kind/established, mix unestablished, episodic-versus-recurring, contradiction class | Interpreter (`interpreter/tests/test_reported_margin.py`) |
| `test_reported_margin.py` assessment sentences, formatted charges, contribution-schedule labels | Composer (`composer/tests/test_reported_margin.py`) |
| Analytical family `test_{earnings_quality*,working_capital,profitability_*,roe_attribution,per_share*,normalized_per_share,fixed_asset,lease_*,deferred_tax,goodwill_intangibles,capex,inventory_analysis,acquisition_cash,cash_rollforward,share_repurchase,ownership_attribution,operating_forecast}.py` | Modeler |
| `test_{operating_kpi_analysis,operating_kpi_relationships,operating_kpi_workbook,operating_kpi_management_history,management_kpi_analysis,revenue_per_store,geographic_segment_analysis,geographic_segment_workbook}.py` | Modeler |
| `test_revenue_driver.py` catalog/link/axis/reconstruction/numeric observations | Modeler (`modeler/tests/test_revenue_driver.py`) |
| `test_revenue_driver.py` verdict / limitation / deferred-SPSF / hypothesis-mechanism cases | Interpreter (`interpreter/tests/test_revenue_driver.py`) |
| `test_revenue_driver.py` finding/note/opening/fallback wording and sheet narrative | Composer (`composer/tests/test_revenue_driver.py`) |
| `test_lululemon_benchmark.py` / `test_fast_retailing_benchmark.py` `load_extracted_filing` setup | Extractor import; assertions stay Modeler |
| `test_build_contract.py`, `test_reference_integrity.py`, `test_historical_v1_exit_gate.py`, `test_cross_company_robustness.py` | Modeler |
| `test_build_cli.py`, `test_current_build.py` | Director |
| `test_research_drivers.py` | split with §5 (Modeler / Interpreter / Composer) |
| `test_publication.py` | Composer |
| `test_learner_ready_presentation.py` style / schedule wording / no-exercise-framing | Composer (`composer/tests/test_learner_ready_presentation.py`) |
| `test_learner_ready_presentation.py` `test_root_readme_is_practical_trainer_guide` | Director (`director/tests/test_readme.py`) |
| `test_learner_ready_presentation.py` committed Trainer/Answer Key pair cases | Legacy (`legacy/tests/test_learner_ready_presentation.py`) |
| `test_trainer.py` | Legacy |
| `test_lululemon_benchmark.py`, `test_fast_retailing_benchmark.py` fixture-policy assertions | Director |
| `test_lululemon_benchmark.py`, `test_fast_retailing_benchmark.py` numerical / schedule assertions | Modeler |
| `test_cached_workbook_verifier.py`, `test_reference_workbook_audit.py` | Legacy |
| Fixtures `operating_kpis/lululemon_company_operated_stores.json` | Extractor-shaped fact handoff (referenced by `project_companies.json`) |
| Fixtures `ordinary_reconcile/lululemon/*` | Modeler protected reconcile snapshot |
| Fixtures `strategy/lululemon_management_disclosures.json` | Extractor-shaped attributed evidence |

### 4.6 Scripts

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `scripts/prepare_lululemon_operating_kpi_filings.py` | `extractor/scripts/prepare_lululemon_operating_kpi_filings.py` | Extractor | Copies extracts + appends authored store facts; does not write protected PDFs | `augment_extracted_filings` |
| `scripts/build_lululemon_release.py`, `build_fast_retailing_release.py` | `legacy/scripts/` | Legacy | Retired Trainer/Answer Key release pair | not on `bav build` path |
| `scripts/audit_fast_retailing_benchmark.py`, `audit_reference_workbook.py` | `legacy/scripts/` | Legacy | Stage / GOOGL audit | matching tests |
| `scripts/extract_benchmark_pdf_text.py` | `legacy/scripts/` | Legacy | Regenerable PDF text cache | `requirements-benchmark.txt` |
| `scripts/build_plugin_zip.sh` | `legacy/` | Legacy | Packs superseded plugin | zip listing |
| `scripts/verify_cached_workbook.py`, `verify_lululemon_overview_presentation.py` | `legacy/verification/` | Legacy | Historical verifiers; SHA-bound | `test_cached_workbook_verifier.py`; native Office only when SHA matches |
| `scripts/build_fast_retailing_source_facts.py` | delete in place | Remove | File header: “OBSOLETE after Step 9M.1… do not use”. Writes absent `source_facts.json`. No `core/`/`bav/` import | `rg` self-only; `source_facts.json` absent |

### 4.7 Automation

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `automation/sentinel.py`, `bav_headless.py`, `build_dashboard.py`, `install.sh`, `com.bav.sentinel.plist`, `headless_settings.json`, `punchlist.md` | `legacy/automation/` | Legacy | EDGAR/news coverage vault; `coverage/` is absent. Not BAV Compiler orchestration | no `coverage/`; punchlist unverified |
| `automation/autocycle-fixes/*` | `legacy/autocycle-fixes/` | Legacy | Controller patches, not product | isolated tests vs installed autocycle |

Not cloud product infrastructure. Sentinel uses `urllib` and `osascript`.
No AWS/GCP/S3/Terraform.

### 4.8 Skills and plugin

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `skills/bav-pipeline/**`, `bav-update/**`, `bav-news/`, `bav-brief/**`, `bav-trainer/SKILL.md`, `EVALS_NOTE.md` | `legacy/skills/` | Legacy | Gemini/Claude coverage pipeline; unused by `python -m bav` | no import from `core/` / `bav/` |
| `skills/bav-pipeline/references/*.gs` and `legacy/Sample AppScript*.txt` | stay Legacy | Legacy | Google Sheets models, not GCP infra | no `bav` import |
| `bav-pipeline-plugin.zip` | stay one Legacy copy **or** delete because Git history + `build_plugin_zip.sh` regenerate it | Legacy (keep) | Rebuildable archive; not runtime | `unzip -l`; no import |

### 4.9 Documentation

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `TARGET.md`, `SESSION.md`, `IMPLEMENTATION.md` | stay root | Director (protected) | Controller-facing; do not move | Cursor read-only |
| `RESULT.md` | stay root | Director (record) | Implementation evidence log | append-only |
| `README.md` | stay root; update STYLE/DRIVER paths and BAV Compiler identity | Director | Operator + architecture | `test_learner_ready_presentation.py`, `test_research_drivers.py` |
| `STYLE.md` | `director/docs/STYLE.md` | Director | Single presentation authority | §11 |
| `DRIVER.md` | `director/docs/DRIVER.md` | Director | Company-agnostic Driver spec | §11 |
| `docs/build-contract.md` | `director/docs/build-contract.md` | Director | `BUILD_MODULES` policy | `test_build_contract.py` |
| `docs/FAST_RETAILING_BENCHMARK.md` | `director/docs/` after path rewrite | Director | Regression-case policy; stale `benchmark/` paths | `test_fast_retailing_benchmark.py` |
| `README-HK-TRAINER.md` | `legacy/docs/` | Legacy | Curriculum/Trainer guide | not imported |
| `docs/GOOGL_HISTORICAL_REFERENCE.md` | `legacy/docs/` | Legacy | Step 9 depth reference | audit script |
| `docs/native-excel-*.json` (7 files) | `legacy/verification/` | Legacy | Independent cell expectations bound to a **specific** `source_sha256` | native Office only if current workbook SHA matches; otherwise BLOCKED |
| `docs/excel-*-2026-09-20.md`, `docs/autocycle-resume-*.md`, `docs/superpowers/specs/*` | `legacy/docs/` | Legacy | Historical diagnosis / design | not imported |

### 4.10 Example

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `example/DEMO_HK_Standardized.json`, `DEMO_HK_Assumptions.json` | `legacy/example/` | Legacy | Synthetic HK curriculum | trainer tests |
| `example/DEMO_HK_Trainer.xlsx`, `DEMO_HK_Answer_Key.xlsx` | `legacy/example/` | Legacy | Committed Trainer pair | `test_learner_ready_presentation.py` |
| `example/GOOGL_Demo_Integrated_Financials.xlsx` | `legacy/example/` | Legacy | Structural reference, not a template | GOOGL doc SHA |
| gitignored `example/rowmap.json`, `*_component_map.json`, `*_assumptions.json` | delete leftover generate | Remove | Regenerable sidecars; already gitignored | not used by company build |

### 4.11 Existing legacy/

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `legacy/*.md` Gem instructions, `Sample AppScript*.txt`, `legacy/README.md` | stay `legacy/` | Legacy | Pre-skill Gemini/Sheets system | no `core` import |

### 4.12 Company inputs and generated outputs

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `build/input/<slug>/source/` (canonical; **empty now**) | stay | Extractor store | Irreplaceable filings when present | validate-source; SHA vs manifest / Git history |
| `build/input/<slug>/extracted/*.json` | stay | Extractor | Per-filing reported facts. Present locally; gitignored | company build; filing tests |
| `build/input/<slug>/reconciled/{standardized,provenance,conflicts}.json` (+ Lulu admission/page/supplemental) | stay | Modeler | Accepted company model + audit | `prepare_company_input`; `standardized_from_payload(strict=True)` |
| `build/input/*/BASELINE.md`, `GAPS.md`, `PROVENANCE.md` | stay as input notes or copy under `director/docs/` | Director | Fixture policy, not runtime | not imported by `bav` |
| `build/input/lululemon/evidence/prior-live/*` | `legacy/evidence/` or stay archive | Legacy | Relocated prior-live bytes; no live fallback | no `lululemon-live` path in `current_build` |
| `build/input/lululemon/evidence/ordinary-reconcile/*` | redundant with tracked fixtures | Legacy local copy | Tracked fixtures are the regression contract | fixture SHA tests |
| `build/input/lululemon/evidence/stale-benchmark-reconciled/` | delete empty dir | Remove | Empty | `ls` empty |
| `build/input/fast_retailing/evidence/_extract/*.txt` | delete after unused-script confirmation | Remove | Regenerable cache; not `prepare_company_input` | not read by build |
| `build/input/fast_retailing/source_manifest.json` | stay `build/input/fast_retailing/source_manifest.json` | Extractor | SHA ledger of source filings. Director later rewrites obsolete `benchmark/` paths as a path-policy edit; the file owner remains Extractor | restore-then-bind |
| `build/output/<slug>/` workbook + supporting JSON | stay | Modeler | Reproducible analytical artifacts | `python -m bav build/check` |
| `build/output/<slug>/research/*.md`, `figures/`, `*.docx`, `*.pdf` | stay | Composer | Reproducible publication | `python -m bav publish`; Forecast/Valuation/Overview remain 0 bytes |

---

## 5. Mixed Driver splits

Keep existing types. Do not invent a reasoning schema. After the split,
`assemble_drivers_view` **stops** calling `select_driver_argument` (today
`drivers.py` L968). Interpreter runs as a separate call. Composer receives
`replace(view, selection=…)`.

**Step 10.5 / 10.5.1 / 10.5.2 actual ownership.** The split is implemented. Shared
records live in `modeler/research/records.py` so Modeler imports do not pull
Interpreter or Composer. Numerical assembly is
`modeler/research/drivers_view.py` (no selection). CFO classification is
`modeler/research/cfo.py`. Geographic conditions are
`modeler/research/geo_conditions.py`. Mechanical eligibility is
`modeler/research/eligibility.py`. Interpreter judgments and economic gates are
`interpreter/selection.py`. Publication constants are
`composer/research/selection_roles.py`; role/order selection, claim wording,
shared component-direction phrasing and magnitude display formatting are
`composer/research/selection.py`. Driver Markdown, figures and publication
helpers are `composer/research/drivers.py`. Director
`director/research.py` obtains completed assessments, assembles the numeric
view, invokes Interpreter, invokes Composer selection, then
`replace(view, selection=…)`. Retained `core/research/drivers.py` and
`core/research/selection.py` are façades that delegate. Dead symbols
`FIGURE_NAMES`, `FIGURE_PLOTTERS` and `_calendar_limit_block` were removed.
Duplicate `_margin_reconstruction_complete` was deleted. Calendar applicability
remains `interpreter/selection.py::calendar_limitation_applies` and is carried
as `ResearchSelection.calendar_limited`. Composer formats the period, issuer
label and limitation text from that supplied judgment and does not re-decide
applicability. Revenue-per-store growth is completed during Modeler assembly as
`revenue_per_store_growth` using the existing adjacent-period, missing-value
and zero-denominator rules. Composer `_intensity_change` and `_growth_argument`
consume that series and do not recompute from levels. Margin reconstruction
validity is completed during Modeler assembly as `reconstruction_complete`
using `margin_reconstruction_complete` / `publication_reconstruction_allowed`.
Interpreter draws complete/partial conclusions from the supplied result.
Composer selection, claim wording, Markdown and figure source notes consume
the same supplied result and do not call `margin_reconstruction_complete`.
Missing completed selection, intensity growth or reconstruction results fail
closed.

### 5.1 `core/research/drivers.py`

**A. Modeler — numerical assembly, CFO classification, series, reconstruction, mechanical validity**

| Symbol / range | Destination | Callers | Reason | Verification |
|---|---|---|---|---|
| `_CFO_*`, `_normalize_cfo_concept`, `is_cfo_component`, `selected_cfo_concepts` L70–140, 264–337 | `modeler/research/cfo.py` | `_cash_series`; tests | Operating-CFO classification; `change_in_` alone does not establish operating classification | `test_research_drivers` FR/Lulu CFO (~L974–1019) |
| `_numeric`, `_attribution_amount`, `_attributions_from_financials`, `_geo_amount_changes`, `_mapped_numeric`, `_cash_series`, `_adjacent_numeric_changes` L203–396 | `modeler/research/drivers_view.py` | assemble | Series / remainder arithmetic | cash remainder / missing-CFO tests |
| `_label_for`, `_fifty_three_week_period`, `_issuer_fiscal_name`, `_fiscal_year_token`, `_date_text` L403–474 | same | assemble, tables, figures | Period facts; issuer FY not from calendar year | calendar regression |
| `ComparableSalesPoint`, `ManagementAttribution` L518–534 | same | assemble, selection | Observation / locator records, not driver admission | attribution strip test |
| `DriversView` numeric/identity/recon fields L538–622 except `selection` | same | select, render, plot | “Numbers for Markdown and figures; all from the same BAV compute path” | assemble + Lulu/FR builds |
| `assemble_drivers_view` L640–967 (**not** L968) | same | `publish_drivers`, tests | Assembly from existing compute path | `test_research_drivers`, `test_reported_margin` |
| `financial_drivers_applicable` L167–177 | same | assemble, `publish_company_research` | Applicability = verified revenue + operating-profit history | early return on publish |
| `_unique_assessments` L1023–1033 | same | assemble | First-name-wins concatenation; **not** a semantic producer | appendix order |
| `_latest_growth_index`, `_operating_profit_change`, `_series_at`, `margin_reconstruction_complete` L1493–1532 | same | assembly stores `reconstruction_complete`; tests | Mechanical reconstruction gate via `publication_reconstruction_allowed`; downstream consumes the stored series | reconstruction tests ~L1025–1073; `test_drivers_numeric` |

**B. Interpreter — not implemented as standalone functions in this file**

Judgment lives in `interpreter/selection.py`. Composer rendering consumes
`view.selection`, including `calendar_limited`. Interpreter owns calendar
applicability; Composer owns the limitation sentence and does not fall back to
period-axis inspection when the completed judgment is absent.

**C. Composer — wording, principal/secondary emphasis, report order, exhibit selection, plotting**

| Symbol / range | Destination | Callers | Reason | Verification |
|---|---|---|---|---|
| `RESERVED_MODULES`, `APPENDIX_HEADING`, `OBSOLETE_SECTIONS`, `WORKPAPER_FIELDS`, `SECONDARY_HEADING`, `PRINCIPAL_HEADING` L52–66, 155–156 | `composer/research/drivers.py` | `verify_research_artifacts`, tests | Heading/workpaper contract | `test_research_drivers` |
| `drivers_filename`, `placeholder_filenames`, `drivers_heading`, `expected_sections`, `is_principal_heading` L143–164 | same | publish, document | Filenames and heading grammar | placeholders remain 0 bytes |
| `SEGMENT_LABELS`, `POPULATION_LABELS` L187–200 | same | plots, compsales block | Display labels | geo/compsales tests |
| `_millions`, `_pct`, `_pp`, `_money`, `_display_*` L477–516, 1045–1144 | same | tables, plots, prose | Display rounding of already-computed values | Lulu/FR money strings |
| `DriversView.display_name`, `period_ended` | same | render | Publication name / date wording | `RenamedCo` test |
| `_KIND_LABELS`, `_FORBIDDEN_RESEARCH`, `_research_safe`, `_finding_sentence` L971–1042 | same | render | Wording hygiene | forbidden-vocab raise |
| Appendix / argument / headline / render L1036–2299 | same | `publish_drivers` | Report order: headline → numbered principals → `## Secondary signals` → Appendix | `verify_research_artifacts` |
| `plot_*`, `_style_axis`, `selected_figure_names`, `publish_drivers`, `write_placeholders` L2302–2584 | same | `publish_company_research` | Exhibit rendering; titles/source notes/colors | figure / publish tests |

**Remove (dead in this file)**

| Symbol | Justification |
|---|---|
| `FIGURE_NAMES`, `FIGURE_PLOTTERS` L180–186 | Defined only; runtime uses `_PLOT_BY_ID`. No other callers |
| `_calendar_limit_block` L461–465 | Unused wrapper; render calls `_calendar_limitation` |

### 5.2 `core/research/selection.py`

**A. Modeler**

| Symbol / range | Destination | Reason | Verification |
|---|---|---|---|
| `_present`, `_negative_change`, `_complete_sum`, `OFFSET_*`, `_revenue_offset_kind`, geo amount helpers, `GeographicClaimConditions`, `geographic_claim_conditions` L110–247 | `modeler/research/geo_conditions.py` | Observed numeric gates; missing ≠ zero | OFFSET / missing-region tests |
| `_latest_index`, `_label`, `_period_labels` L296–307 | same | Last-period index | see unresolved `_latest_growth_index` |
| `_margin_reconstruction_complete` L706–723 | **delete**; consume assembled `reconstruction_complete` | Duplicate computer removed; Composer does not recalculate | reconstruction / handoff tests |
| `_latest_change`; `_margin_is_material` L1097–1106 | `modeler/research/eligibility.py` | `change is not None and change != 0` is mechanical eligibility, not economic materiality | zero-margin demotion |

**B. Interpreter — materiality, mechanisms, strongest conclusions, uncertainty**

| Symbol / range | Destination | Reason | Verification |
|---|---|---|---|
| `CLAIM_*` L24–32 | `interpreter/selection.py` | Claim typology | selection tests |
| `ResearchClaim` / `ResearchQuestion` interpretive fields (§6) | stay as existing dataclasses | Compact question record | `test_research_drivers` |
| `geographic_strongest_conclusion`, `geographic_materiality_rationale` L250–284 | `interpreter/selection.py` | Strongest supported geo conclusion | named tests |
| `investigate_driver_questions` L310–320 | same | Candidate generation | all selection tests |
| Question-builder **judgment** insides of `_growth_questions`, `_geography_questions`, `_margin_questions`, `_cash_questions` | same | Mechanisms, alternatives, strongest, unresolved, status | footprint/geo/margin/cash tests |
| `select_driver_argument` **gates only** L1138–1139, 1109–1116, 1209, 1246 | same | `margin_material`, `geo_story`, `footprint_diverged`, `cash_visible` | principal_ids tests L191–195, 877–923 |
| Attribution **never** an independent principal L1170–1176 | same | Preserve attributed evidence; do not promote | attribution tests |

**C. Composer — wording, emphasis, ordering, exhibits**

| Symbol / range | Destination | Reason | Verification |
|---|---|---|---|
| `PUBLICATION_*`, `ROLE_*` L15–22 | `composer/research/selection_roles.py` | Publication roles | heading / role tests |
| `wording`, `publication`, `publication_reason`, `figure_purpose`, `figure_question` | Composer fields on existing types | Presentation | figure_ids tests |
| `geographic_figure_question` L287–293 | Composer | Exhibit question | imported in tests |
| `_component_direction_phrase` L726–738 | `composer/research/selection.py::component_direction_phrase` | Shared selection and Driver-prose wording; Interpreter no longer derives reconstruction from this phrase | margin prose |
| `select_driver_argument` **role/order/figure phase** L1141–1288 | Composer | Map Interpreter gates → principal/secondary/appendix + `figure_ids` | `expected_sections`; `selected_figure_names` |
| `SelectionDecision` | Composer (action) quoting Interpreter reason | Decision table | `_selection_block` |

**Concrete two-phase split of `select_driver_argument` (keep one function until the move):**

1. Interpreter: compute `margin_material`, `geo_story`, `footprint_diverged`, `cash_visible`; decide which IDs are economically carrying vs supporting vs auditable.
2. Composer: assign `ROLE_PRINCIPAL` / `ROLE_SECONDARY` / `ROLE_APPENDIX`, append `figure_ids`, write decision reasons, set `main_body_ids = principals + secondaries`. Order remains margin → geo → footprint → cash.

### 5.3 `style.py`, `document.py`, `publish.py`

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `core/research/style.py` entire module | `composer/research/style.py` | Composer | STYLE.md figure implementation; no analytical series | spacing/font tests |
| `core/research/document.py` entire module | `composer/research/document.py` | Composer | “Publication does not recalculate analysis” | `test_publication`; `python -m bav publish` |
| `core/research/publish.py` `verify_research_artifacts`, `publish_company_research` | `composer/research/publish.py` | Composer | Heading/figure/placeholder contract; apply-if-applicable | `check_company_output`; company build |
| `core/research/__init__.py` | Composer façade until split | Composer | Documents Markdown/figures output | package import |

---

## 6. Field ownership and smallest existing-data handoffs

No new types. Handoffs remain `DriversView` → `ResearchSelection` → Markdown/figures.

**Handoff 1 (Modeler → Interpreter):** `DriversView` numeric fields + `attributions` + `comparable_sales` + identity `kind`/`established` + reported-fact amounts/zeros + observed-movement direction tests + completed `revenue_per_store_growth` and `reconstruction_complete`. Interpreter does not reread Composer wording and does not recompute intensity growth or reconstruction validity.

**Handoff 2 (Interpreter → Composer):** `ResearchSelection` on the same view, plus assessment judgment fields (`kind`/`established` for descriptive, causal, reported-fact and unestablished branches; recurrence; contradiction class; unsupported-mix) and `calendar_limited`. Composer already reads `principal_ids`, `secondary_ids`, `figure_ids`, `questions[].strongest_conclusion`, `unresolved_requirement`. Composer formats `questions[].magnitude` from Interpreter-chosen comparisons and Modeler numbers.

**Handoff 3 (Modeler → Composer):** same series for appendix tables and plot arrays, including completed intensity growth and reconstruction validity. Composer must not recompute identities, intensity growth, reconstruction completeness or change `kind`/`established`.

### `DriversView`

| Field | Owner |
|---|---|
| `company_name`, `currency`, `units`, `periods`, `labels` | Modeler |
| `display_name`, `period_ended` | Composer |
| All revenue/profit/margin/geo/cash/inventory/footprint series and residuals L548–621 | Modeler |
| `stores`, `revenue_growth`, `store_growth`, `revenue_per_store`, `revenue_per_store_growth`, `comparable_sales`, `store_only_comparable_sales` | Modeler |
| `reconstruction_complete` | Modeler mechanical validity by period; Interpreter concludes; Composer publishes without recalculation |
| `fifty_three_week_period`, `issuer_fiscal_name` | Modeler |
| `amount_bridge_convention` | Composer rendered sentence; Modeler owns the formula only (`AMOUNT_BRIDGE_FORMULA`) |
| `assessments` | container only; see §7.0 / §7.4 field-and-branch maps. Assembly is not a producer |
| `relationship_findings` | Composer (`_finding_sentence` over assembled assessments; preserves `kind`/`established`) |
| `margin_explanation` | unused (`""` at assemble); do not invent a replacement |
| `attributions` | Modeler container of Extractor locators |
| `selection` | field owners in `ResearchSelection` below; not a second owner of the view |

### `ResearchClaim`

| Field | Owner |
|---|---|
| `identifier`, `claim_type` | Interpreter |
| `wording` | Composer |
| `measurement_role`, `evidence_refs`, `transformation`, `dependencies` | Modeler |
| `qualifiers` | Modeler when measurement; Interpreter when claim scope |
| `mechanism_support`, `counterevidence` | Interpreter |
| `status` | Modeler if `supported`/`unavailable`/`partial` from series; Interpreter if `blocked`/`unsupported`/`supported_as_attribution` |

### `ResearchQuestion`

| Field | Owner |
|---|---|
| `identifier`, `question` | Interpreter |
| `entity`, `population`, `periods`, `outcome` | Modeler (measurement scope) |
| `materiality_rationale`, `temporal_character`, `mechanisms`, `alternative`, `discriminating_evidence` | Interpreter |
| `magnitude` | Interpreter chooses the comparison and leaves the field unrendered; Composer formats Modeler numbers without changing meaning or precision |
| `claims` | mixed per `ResearchClaim` |
| `strongest_conclusion`, `unresolved_requirement`, `reopening_condition` | Interpreter |
| `publication`, `publication_reason`, `figure_purpose`, `figure_question`, `main_body_table_reason` | Composer (`main_body_table_reason` is never set) |
| `overlap` | Interpreter; unused by `select_driver_argument` |

### `ResearchSelection` / `SelectionDecision`

| Field | Owner |
|---|---|
| `questions` | mixed record; field owners above |
| `decisions` | Composer action + Interpreter reason text |
| `main_body_ids`, `principal_ids`, `secondary_ids`, `appendix_ids`, `figure_ids` | Composer, informed by Interpreter gates |
| `calendar_limited` | Interpreter judgment carried through Composer selection; Composer formats only |
| `main_body_table_reasons` | Composer; **never populated** |

---

## 7. Revenue-driver, synthesis, validators, ingestion

Thin existing-data handoffs only. No reasoning ontology. After the split,
Modeler must not import Interpreter or Composer; Interpreter must not import
Composer labels; Composer consumes Modeler numbers and Interpreter codes.

**Director sequence for existing callers** (`build_company`, research assemble,
Overview opening): Modeler compute → Interpreter interpret → Composer word →
consumer writes or renders. Keep one compatibility façade per mixed file only
until those callers are updated; the façade may not choose judgments.

### 7.0 `core/model/revenue_driver.py` (exhaustive)

Git blob at B and at reviewed-attempt `86ebdec…`: SHA-256
`ff46fc45f303a5fb883c01c2bd5520efe57a419b013b6d0a3ee4f117c828c4bb` (59157 bytes).

#### A. Modeler — observations, arithmetic, mechanical validity

Destination file: `modeler/revenue_driver.py`.

| Source symbol / field | Destination symbol | Reason | Consumers | Verification |
|---|---|---|---|---|
| `CALCULATION_KIND` | same | Calculation provenance | `RevenueDriverAnalysis.calculation_kind` | `test_revenue_driver` |
| `RevenueDriverPeriodObservation.period`, `.inputs`, `.consistent` | same | Aligned inputs and coincidence flags (`rev>0 and stores>0`). Not a verdict | workbook expand `_revenue_driver_expand_inputs`; research compsales points; Interpreter verdict | numeric tests |
| `GeographicRevenueReconstruction` all fields | same | Component sum, residuals, contributions | `assemble_drivers_view`; `_assess_revenue_test` identity | reconstruction tests |
| `FootprintIntensityIdentity` numeric fields | same | Stores × intensity identity and change split | assemble; identity assessment | footprint tests |
| `FootprintIntensityIdentity.convention` formula clause | `FOOTPRINT_IDENTITY_FORMULA` | Arithmetic convention only | assessment magnitude; sheet | identity tests |
| `RevenueDriverAnalysis.periods`, `.calculation_kind`, `.geographic_reconstruction`, `.footprint_identity` | same | Numeric analysis | workbook, research | `test_revenue_driver` |
| `RevenueDriverHypothesisTest.theme`, `.admitted_inputs`, `.periods_tested`, `.sample_size`, `.disclosures` (container) | same | Theme key, admitted series, sample | workbook sample row; Interpreter | theme tests |
| `revenue_driver_applicable` | same | `bool(data.disclosures)` gates optional series, not driver status | `_prepare_revenue_driver`; assemble; synthesis applicable | skip-without-disclosures |
| `_require_annual_axis`, `_numeric` | same | Axis / numeric coerce | builders | interim-axis test |
| `_disclosures_for` | same | Mechanical theme filter | builders | theme presence |
| `_compsales_adjacent_comparison_ineligible` | same | Adjacent compsales growth is None | Interpreter limitation code | ineligible tests |
| `_conflicting_qualifier_fields` (names only from `_QUALIFIER_FIELDS`) | `_QUALIFIER_FIELD_NAMES` | Which qualifier fields differ | deferred-disagreement detect | deferred-SPSF test |
| `_spsf_missing_periods` / unavailable-reason codes from `_spsf_evidence_limitations` | `_spsf_evidence_gaps` | Missing periods and `REASON_*` codes | Interpreter gap codes | SPSF limitation tests |
| `_deferred_disagreement_limitations` member selection | `_deferred_disagreements_for` | Filter `deferred_disagreements` by family | Interpreter | deferred-SPSF test |
| `_THEME_BUILDERS` numeric phase | `_store_expansion_observations`, `_comparable_sales_observations`, `_productivity_observations`, `_geographic_observations` | Build observation inputs/flags only; leave `.note` empty | Interpreter / Composer | each hypothesis-test builder |
| `_store_expansion_test` numeric body L544–650 | `_store_expansion_observations` | Applicability, relationship, RPS, coincidence, payload | workbook store rows | supported/mixed/contradicted/insufficient |
| `_comparable_sales_test` numeric body L714–799 | `_comparable_sales_observations` | Identities, percents, differences, `consistent` | research compsales points; workbook | compsales tests |
| `_productivity_test` numeric body L852–947 | `_productivity_observations` | SPSF growth availability, RPS rise/decline counts | Interpreter | SPSF tests |
| `_geographic_test` numeric body L1015–1141 | `_geographic_observations` | Contribution signs, extra False flag for mix | Interpreter | geographic mixed test |
| `compute_revenue_driver_analysis` L1192–1209, 1220–1228 numeric | same, numeric-only return | Axis, reconstructions, observation tests | Director sequence | missing-disclosures / axis |
| `_geographic_reconstruction`, `_footprint_intensity_identity` | same | Pure arithmetic | assemble; assessments | reconstruction tests |
| `_assess_revenue_test` identity residual branch L1376–1416 | `_identity_assessment` | **Only** `kind=KIND_IDENTITY` and residual-based `established` (`max_resid < 1e-4`). Not wording | `test.assessment` identity items | seven-part names; residual tests |
| `REASON_*` via management_kpi imports | stay Modeler admission codes | Mechanical unavailability | Composer labels | SPSF tests |

#### B. Interpreter — hypotheses, mechanisms, verdicts, causal qualifications

Destination file: `interpreter/revenue_driver.py`.

| Source symbol / field | Destination symbol | Reason | Consumers | Verification |
|---|---|---|---|---|
| `VERDICT_*`, `SUPPORTED_VERDICTS` | same | Verdict vocabulary | Composer display; tests | verdict tests |
| `HYPOTHESIS_*`, `MECHANISM_*` | same | Hypothesis and mechanism text already stored as judgment, not publication order | workbook “Analyst hypothesis” / “Economic mechanism” | hypothesis tests |
| Semantic codes for `SCOPE_NOTE` / limitation clauses | `QUAL_NOT_OUTCOME`, `QUAL_DESCRIPTIVE_DIFFERENCE`, `QUAL_RPS_NOT_PRODUCTIVITY`, `QUAL_POPS_DISTINCT`, `QUAL_GAPS_NOT_BRIDGED`, `QUAL_NOT_ORGANIC_FX` | Qualification kinds; not sentences | Composer wording | limitation tests |
| `FAILED_*` / `ADDITIONAL_*` as requirement ids | `REQ_STORE_GROWTH`, `REQ_COMPSALES`, `REQ_SPSF_GROWTH`, `REQ_GEOGRAPHIC`, `REQ_COMPSALES_HISTORY` | What evidence is missing | Composer phrases (preserve existing strings) | failed-requirement rows |
| `RevenueDriverHypothesisTest.hypothesis`, `.mechanism`, `.verdict`, `.failed_requirement`, `.additional_evidence` | same fields, Interpreter-produced | Judgment and requirement codes | workbook verdict/failed rows; synthesis | verdict tests |
| `RevenueDriverPeriodObservation.consistent` consumption | `_verdict_from_consistency` | Maps flags → verdict | each builder | mixed/contradicted |
| Structured counterexample | `observation.counterexample: bool` replacing `_is_counterexample_note` token scan | Interpreter must not parse Composer notes | `_finding_with_counterexamples`; synthesis | counterexample tests |
| `_objective_limitation` | `has_objective_role` + `QUAL_NOT_OUTCOME` | ROLE_OBJECTIVE is not an achieved outcome | Composer sentence | objective tests |
| `_store_expansion_test` verdict/qualification | `interpret_store_expansion` | Verdict, codes, counterexample flags | Composer `word_store_expansion` | store-expansion tests |
| `_comparable_sales_test` verdict/qualification | `interpret_comparable_sales` | same | Composer | compsales tests |
| `_productivity_test` verdict/qualification | `interpret_productivity` | same | Composer | SPSF tests |
| `_geographic_test` verdict/qualification | `interpret_geographic` | same; mix uses Modeler’s extra False flag | Composer | geographic mixed |
| `_assess_revenue_test` compsales / productivity / fallback L1417–1459 | `interpret_revenue_assessment` | Descriptive/causal `kind` and `established` only. Does **not** write identity `kind`/`established` | Composer wording | seven-part SPSF flags |

Do not have Interpreter import `_SEGMENT_LABELS`, `_format_ratio_pct`, or
`THEME_LABELS`.

#### C. Composer — publication wording

Destination file: `composer/revenue_driver.py`.

| Source symbol / field | Destination symbol | Reason | Consumers | Verification |
|---|---|---|---|---|
| `_SEGMENT_LABELS`, `_segment_label` | same | Display names | geographic notes | geo finding text |
| `_SPSF_REASON_LABELS`, `_FAMILY_DISAGREEMENT_LABELS` | same | Display labels for Modeler codes | limitation sentences | SPSF / deferred tests |
| `_QUALIFIER_FIELDS` labels | `_QUALIFIER_FIELD_LABELS` | Display only | deferred-disagreement prose | deferred-SPSF |
| `_format_ratio_pct`, `_format_pp` | same | Display rounding | observation notes | finding strings |
| `_finding_with_counterexamples` | same | Join base finding + counterexample notes | `test.finding` | “exceeded revenue growth” |
| `_format_deferred_disagreement` | same | Existing deferred sentence | `test.limitations` | deferred-SPSF test |
| `_compsales_population_limitations` wording | `word_compsales_population_limit` | Render distinct-population code | limitations | population tests |
| `_spsf_evidence_limitations` wording | `word_spsf_evidence_limits` | Render gap codes | limitations | SPSF limitation tests |
| `SCOPE_NOTE` rendered | same string | Preserve exact wording | `analysis.scope_note`; workbook A5 | `result.scope_note == SCOPE_NOTE` |
| `FOOTPRINT_IDENTITY_CONVENTION` rendered | same string = formula + Interpreter productivity qualification | Preserve exact wording | `footprint.convention`; assessments | identity tests |
| `RevenueDriverPeriodObservation.note` | same | Period interpretation sentences | workbook `_period_interpretations` | note assertions |
| `RevenueDriverHypothesisTest.finding`, rendered `.limitations`, `.identity_notes` | same | Publication sentences | workbook Finding/Limitations; synthesis `test.finding`; research | finding tests |
| Assessment text fields | same | `direction`, `magnitude`, `reconstruction`, `residual`, `stability`, `contradictions`, `disclosure_support`, `limitation` | `DriversView.relationship_findings` via `_finding_sentence` | seven-part |
| `word_store_expansion` / `word_comparable_sales` / `word_productivity` / `word_geographic` | new | Fill notes/finding/limitations from existing templates | builders’ current return | same tests |

#### `_store_expansion_test` executable split

1. Modeler `_store_expansion_observations`: applicability, `compute_operating_kpi_revenue_store_relationship`, optional RPS, per-period `inputs` + `consistent`.
2. Interpreter `interpret_store_expansion`: `_verdict_from_consistency`, `HYPOTHESIS_STORE_EXPANSION`, `MECHANISM_STORE_EXPANSION`, qualification codes, `REQ_STORE_GROWTH` when insufficient, `counterexample` on exceeded-growth / RPS-decline / store-up-revenue-down periods.
3. Composer `word_store_expansion`: existing note sentences, `finding` including `Verdict: …`, limitation sentences including `REVENUE_PER_STORE_SCOPE_NOTE`.

Same three-function pattern for `_comparable_sales_test`, `_productivity_test`,
`_geographic_test`. `_THEME_BUILDERS` becomes a Modeler observation map;
Interpreter/Composer maps stay beside it.

#### Result-field producers (one producer each)

| Field | Producer | Workbook | Research | Tests |
|---|---|---|---|---|
| `observation.inputs` / `.consistent` / `.period` | Modeler | expand + formula links | compsales points | numeric |
| `observation.note` | Composer | period interpretation row | unused | finding/note |
| `test.verdict` | Interpreter | verdict row (Composer displays `replace('_',' ')`) | unused | verdict |
| `test.hypothesis` / `.mechanism` | Interpreter | hypothesis/mechanism rows | unused | hypothesis |
| `test.finding` / `.limitations` / `.identity_notes` | Composer | Finding / Limitations / Identity note | synthesis copies finding | finding |
| `test.failed_requirement` / `.additional_evidence` | Interpreter codes; Composer existing phrases | failed / additional rows | unused | failed-requirement |
| `analysis.geographic_reconstruction` / `.footprint_identity` | Modeler | reconstruction block | assemble series | reconstruction |
| `analysis.scope_note` | Composer | A5 | unused | `== SCOPE_NOTE` |
| `test.assessment` container | not a producer | unused as a blob | `_finding_sentence` | see branch map |
| `test.assessment` identity `kind` / residual `established` | Modeler | unused | `_finding_sentence` copies flags | geo/footprint residual `< 1e-4` |
| `test.assessment` descriptive/causal `kind` / `established` | Interpreter | unused | same | SPSF / compsales / fallback |
| `test.assessment` wording fields | Composer; must copy `kind`/`established` unchanged | unused | relationship_findings | seven-part names |
| `analysis.assessments` | concatenation of non-None `test.assessment` then `margins.assessments`; **not** a producer | unused | assemble `_unique_assessments` | order: `_THEME_BUILDERS` then §7.4 append order |
| `test.disclosures` | Extractor-shaped records already on financials | management-statement rows | unused | locator tests |

#### `_assess_revenue_test` branch producers (one kind/established producer each)

Precedence is the current if-chain. Later branches do not rewrite an earlier
return. Composer fills text after the branch owner sets `kind`/`established`.

| Branch (current guard) | `kind` | `established` | Wording | Destination symbols |
|---|---|---|---|---|
| `THEME_GEOGRAPHIC_GROWTH` and `geo is not None` L1376–1395 | Modeler `KIND_IDENTITY` | Modeler `max_resid is not None and max_resid < 1e-4` | Composer; `contradictions` uses Interpreter `counterexample` then existing finding text or `"none required"` | `_identity_assessment` / `word_identity_assessment` |
| `THEME_STORE_EXPANSION` and `footprint is not None` L1396–1416 | Modeler `KIND_IDENTITY` | Modeler same residual rule on `reconstruction_residual` | Composer; same counterexample rule | `_identity_assessment` / `word_identity_assessment` |
| `THEME_COMPARABLE_SALES` L1417–1430 | Interpreter `KIND_OBSERVED` if any `consistent is not None` else `KIND_UNESTABLISHED` | Interpreter `bool(known) and verdict != VERDICT_INSUFFICIENT` | Composer | `interpret_revenue_assessment` / `word_revenue_assessment` |
| `THEME_PRODUCTIVITY` L1431–1444 | Interpreter `KIND_UNESTABLISHED` if insufficient else `KIND_OBSERVED` | Interpreter `verdict != VERDICT_INSUFFICIENT` | Composer | same |
| Fallback L1445–1459 (geo without reconstruction, store without footprint, or other) | Interpreter `KIND_CAUSAL` if contradicted else observed/unestablished from `known` / insufficient | Interpreter `verdict == VERDICT_SUPPORTED` | Composer | same |

`RevenueDriverHypothesisTest.assessment` is the container for that branch
result. It is not itself a producer.

**Imports after the move:** `modeler/revenue_driver.py` keeps relationship /
KPI / geo / period_axis / `MarginRelationshipAssessment` type imports. It
must not import Interpreter or Composer. `interpreter/revenue_driver.py`
imports Modeler observation types, identity residuals, and verdict/KIND
constants only — not Composer labels or formatters.
`composer/revenue_driver.py` imports Interpreter codes + Modeler numbers;
it copies `kind`/`established` and does not compute series.
`core.engine.reference_model` numeric expand imports Modeler only.
`core.research.drivers` assemble imports Modeler observations and already-
filled assessment records; `_finding_sentence` / `_KIND_LABELS` /
`_assessment_block` import Composer. `core.trainer.workbook._add_bav_opening`
does not import this module.

Director sequences existing callers: Modeler compute → Interpreter
`interpret_revenue_assessment` (descriptive/causal branches only) → Composer
word → `assemble_drivers_view` concatenates. Keep one compatibility façade
until those callers are updated; the façade may not choose judgments.

Preservation: existing `test_revenue_driver.py` strings, verdicts, residuals,
and workbook link formulas stay. Composer keeps current sentences. Identity
`kind`/`established` stay residual-owned.

### 7.1 `core/model/revenue_strategy_synthesis.py`

Git blob at B and at `86ebdec…`: SHA-256
`f9006d0f6faceb643cc949e948c304e8f3316ff3725e338b78d4684de071f16c` (14784 bytes).

#### A. Modeler

| Source | Destination | Reason | Verification |
|---|---|---|---|
| `strategy_synthesis_applicable` | `modeler/revenue_driver.py` (next to `revenue_driver_applicable`) | `return revenue_driver_applicable(financials)` | applicability |
| Optional `compute_revenue_driver_analysis` fetch | caller supplies `RevenueDriverAnalysis` | Composer/opening must not run tests as a hidden side effect after the move | `test_strategy_synthesis_connects_findings_without_claiming_outcomes` |

#### B. Interpreter — `interpreter/historical_strategy.py`

| Source | Destination symbol | Reason | Verification |
|---|---|---|---|
| `_ROLE_PRIORITY`, `_featured_disclosure` | same | Which disclosure role to feature | featured-statement tests |
| `_management_statement` selection | `select_featured_disclosures` | Evidence selection | synthesis tests |
| `_qualification` | `qualification_codes(test)` | Semantic codes, not sentences | no “achieved outcome” |
| `_verdict_inference` **branch only** | `select_verdict_inference(test) -> {supported,mixed,contradicted,insufficient}` | Judgment selection. Must not read `THEME_LABELS` | verdict-without-outcome |
| `_counterexample_notes` | `selected_counterexample_ids` using `observation.counterexample` | Stop scanning Composer tokens | counterexample tests |
| `_has_deferred_spsf` | `has_deferred_spsf` on Interpreter limitations / Modeler disagreements | Stop parsing “Deferred …” prose | deferred-SPSF link-without-promotion |
| `_productivity_gap` judgment | `productivity_gap_kind` | Insufficient vs other; do not promote deferred SPSF | same |
| `UNTESTED_INITIATIVES`, `WHAT_HISTORY_ESTABLISHES`, `DEFERRED_SPSF_LINK` as codes | `LIMIT_UNTESTED`, `LIMIT_HISTORY`, `LIMIT_DEFERRED_SPSF` | Causal limits | synthesis limits |
| `StrategyFindingInterpretation.theme`, semantic `inference` | Interpreter fields | Theme + selected inference | synthesis |
| `HistoricalStrategySynthesis` semantic `limits` / `productivity_gap` / `untested` | Interpreter fields | Qualification payload | opening “Evidence limits” |

#### C. Composer — `composer/overview.py`

| Source | Destination symbol | Reason | Verification |
|---|---|---|---|
| `THEME_LABELS` | same | Display labels | `_verdict_inference` / `_lead` wording |
| `THEME_SCHEDULES`, `_schedule_clause`, `_navigation` | same | Sheet names and “See ….” | `REVENUE_DRIVER_SHEET_NAME in store_row.finding` |
| `_join_labels` | same | Plural join | lead sentences |
| `_format_statement`, `disclosure_locator` consumption | `format_management_statement` | Wording of Extractor locator + text | locator tests |
| `_verdict_inference` templates, lowercasing, `observation`/`s` | `word_verdict_inference` | Presentation only | no Composer labels in Interpreter |
| `_lead` templates, capitalize, is/are | `word_lead` | Opening prose | opening tests |
| `_productivity_gap` sentences | `word_productivity_gap` | Render Interpreter kind | deferred-SPSF |
| `PROFESSIONAL_FALLBACK` | same | Opening when synthesis is inapplicable | `test_opening_without_strategy_stays_professional_fallback` |
| `StrategyFindingInterpretation.heading`, `.management_statement`, `.finding` (finding + schedule clause), `.supporting_schedules`, rendered `.inference`, rendered `.counterexample` | Composer fields | Publication record | synthesis tests |
| `HistoricalStrategySynthesis.lead`, `.navigation`, rendered limits/gap/untested | Composer fields | Overview opening | `_add_bav_opening` |
| `compute_historical_strategy_synthesis` | `composer/overview.py` same name | Composer wording: require completed analysis and `HistoricalStrategyJudgment`; do not interpret or compute analysis | `test_strategy_synthesis_*` |
| `_interpretations` | `compose_interpretations` | Assemble Composer fields from Interpreter + Modeler tests | same |

`disclosure_locator` stays Extractor-shaped:
`extractor/data/historical_strategy.py` `disclosure_locator` (same format
`source_file; page_reference; section; period-end`). Composer formats; it does
not invent locators.

**Overview opening** (`core/trainer/workbook.py` `_add_bav_opening`): after
Trainer inversion this function is Composer `composer/workbook_opening.py`
`_add_bav_opening`. It consumes `lead`, rendered limits/gap/untested,
`navigation`, and `PROFESSIONAL_FALLBACK`. Layout/hyperlinks are Composer.
Company/period identity lines are Modeler facts displayed by Composer.

#### Result-field producers

| Field | Producer | Opening | Tests |
|---|---|---|---|
| `synthesis.lead` | Composer from Interpreter verdict groups | “Historical reading” | no “Historical finding”; no outcome claim |
| `synthesis.limits` / `.productivity_gap` / `.untested` | Interpreter codes; Composer existing sentences | “Evidence limits” | limits without promoting SPSF |
| `synthesis.navigation` | Composer | schedule hyperlinks | sheet names exist |
| `row.inference` | Interpreter selection; Composer `word_verdict_inference` | unused (opening uses lead) | no Composer labels inside Interpreter |
| `row.finding` | Composer (`test.finding` + schedule clause) | unused | `analysis.tests[0].finding in store_row.finding` |
| `row.heading` / `.supporting_schedules` | Composer | unused | THEME_LABELS |
| `PROFESSIONAL_FALLBACK` | Composer | fallback opening | fallback test |

**Imports:** Interpreter historical_strategy imports Modeler test records and
verdict codes only — never `THEME_LABELS`. Composer overview imports
`THEME_LABELS`, Interpreter codes, Extractor `disclosure_locator`, and
catalog sheet-name constants; it does not invoke Interpreter. Director
`complete_historical_strategy_synthesis` obtains analysis when needed, invokes
`interpret_historical_strategy`, and passes the completed judgment to Composer.
`_add_bav_opening` imports Composer only.

### 7.2 Validators and admission

| Current | Disposition | Reason | Verification |
|---|---|---|---|
| `core/data/validators.py` IS/BS/CF checksums | Modeler | Arithmetic on standardized statements | `test_validators.py` |
| `core/ingestion/filing_validator.py` `bind_source_file`, `source_row_identity` | Extractor | SHA-256 / portable `source_file` / page | `python -m bav validate-source` |
| `filing_validator.validate_operating_kpi_fact` path | Modeler | Admission identity, not provenance | KPI fact tests |
| `historical_operating_kpis` / `historical_segments` validators | Modeler | Fail-closed identity / bridge | matching tests |
| `management_kpi.py` `classify_extracted_payload`, `_annual_schema_complete`, `_management_schema_complete` | Extractor `extractor/data/extracted_kind.py` | Schema kind of already-extracted JSON; not admission | `test_management_kpi_admission.py` classify cases |
| `management_kpi.py` `load_management_kpi_document`, `parse_management_kpi_document` | Extractor `extractor/data/management_kpi_json.py` | Source-faithful parse of management-KPI JSON | admission tests’ parse setup |
| `management_kpi.py` admit/bind | Modeler `modeler/ingestion/management_kpi.py` | Content-aware admission of already-parsed KPI documents | `test_management_kpi_admission.py` admit |
| `management_kpi_identity.py`, `management_kpi_reconciliation.py`, `management_kpi_history.py` | Modeler | Identity, conflict, history derivation | matching tests |
| `operating_kpi.py` / `geographic_segment.py` selection | Modeler | Restated-vs-prior / Q4-2023 identity | fact tests |
| `normalization_candidate_admission.py` case/series admission | Modeler `modeler/ingestion/normalization_candidate_admission.py` | Opt-in; not default reconcile | `test_normalization_candidate_admission.py` |
| `normalization_candidate_admission.py` human treatment judgments | Interpreter `interpreter/normalization.py` | Human treatments are not facts | same tests |
| `share_basis.py` | Modeler | Restatement-factor resolution | `test_share_basis.py` |

### 7.3 Ingestion I/O — `load_extracted_filing` owner

**Disposition: Extractor.** Exact destination
`extractor/data/filing_json.py` keeping the current symbol names.

This is source-faithful schema I/O of already-extracted JSON. It is not PDF
extraction, not admission, not reconciliation, and not Director orchestration.
Existing loading does not authorize building a new extractor.

Git blob at B and at `86ebdec…`: SHA-256
`46bc9271922965c3141a5161eceeb15c5485f5dd3ee2f5ca9b5ec55724d93562` (12851 bytes).

| Source symbol | Destination | Disposition | Reason | Callers | Verification |
|---|---|---|---|---|---|
| `_required_nonempty_str`, `_optional_str`, `_required_positive_int`, `_parse_date` | `extractor/data/filing_json.py` | Extractor | Schema scalars | `load_extracted_filing` | `test_filing_json.py` rejects |
| `_parse_source` | same | Extractor | `SourceRef` page/statement/note/label | statement/supplemental rows | page-required tests |
| `_parse_values`, `_parse_statement_row` | same | Extractor | Statement rows and presentation roles | load | round-trip |
| `_parse_supplemental` | same | Extractor | Note/share facts; parse-time `reject_non_string_reported_label` is contract shape, not admission | load | KPI label tests |
| `load_extracted_filing` | same | Extractor | Parse one ExtractedFiling v1.0 file; does not open PDFs | `filing_cli.load_and_validate_extracted_dir`; tests listed below | `test_filing_json.py` |
| `load_extracted_json_object` | same | Extractor | Raw object load, no schema dispatch | `filing_cli` before classify; `test_management_kpi_admission.py` | classify-then-load |
| `extracted_filing_to_payload` | same | Extractor | Serialize the published contract | round-trip tests | payload == JSON |
| `core/data/filing.py` types | `extractor/data/filing.py` | Extractor | Published contract | loaders | same tests |
| `is_operating_kpi_fact_type`, `reject_non_string_reported_label` used at parse | `extractor/data/operating_kpi_contract.py` | Extractor | Parse-time type/label shape. Modeler admission keeps its own identity checks and may import the same type-set | `_parse_supplemental` | operating-KPI fact tests |

**Not this loader**

| Symbol | Owner | Why |
|---|---|---|
| `classify_extracted_payload` | Extractor `extractor/data/extracted_kind.py` | Schema kind; used after raw load |
| `validate_extracted_filing` / `bind_source_file` | Extractor `extractor/data/filing_validator.py` | Provenance bind |
| `validate_operating_kpi_fact` | Modeler | Admission identity |
| `issuer_fiscal_years_from_extracted` | Modeler `modeler/data/issuer_fiscal.py` | Own `json.loads` for FY mapping; does not call `load_extracted_filing` |
| `prepare_company_input` | Director → Modeler `standardized_from_payload` | Company build reads `reconciled/standardized.json`, not this loader |
| `filing_cli.list_extracted_json_files`, `load_and_validate_extracted_dir` | Director `director/ingestion/filing_cli.py` | Lists files and sequences Extractor load + Modeler admit |
| `cmd_validate_source` / `cmd_reconcile` | Director | CLI routes |

**Production callers of `load_extracted_filing`:** only
`core/ingestion/filing_cli.py` L66 (Director validate/reconcile path).

**Test callers:** `test_filing_json.py`, `test_management_kpi_admission.py`,
`test_operating_kpi_facts.py`, `test_geographic_segment_facts.py`,
`test_geographic_segment_analysis.py`, `test_geographic_segment_workbook.py`,
`test_lululemon_benchmark.py`, `test_fast_retailing_benchmark.py`.

**Import changes:** `from extractor.data.filing_json import load_extracted_filing,
load_extracted_json_object, extracted_filing_to_payload`. Director
`filing_cli` imports Extractor loaders + `classify_extracted_payload`. Modeler
reconcile/standardize consume `ExtractedFiling` instances; they do not parse
JSON. Company `python -m bav build` does not gain an Extractor dependency
through this loader.

Remaining ingestion rows:

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `filing_cli.py` | `director/ingestion/filing_cli.py` | Director | Workflow over extracted dir | `test_filing_cli.py` |
| `filing_reconciler.py` `reconcile_filings` | `modeler/ingestion/filing_reconciler.py` | Modeler | Cross-filing selection | `test_filing_reconciler.py` |
| `reconciliation_provenance_payload` `source_file` / `source_sha256` / `pdf_page` | Extractor fields on the payload | Extractor | Raw source provenance | committed `provenance.json` |
| `reconciliation_provenance_payload` `selection_rule` / rank | Modeler fields on the same payload | Modeler | Analytical selection provenance | committed `provenance.json` |
| `filing_standardizer.py` | `modeler/ingestion/filing_standardizer.py` | Modeler | Emit model-only `StandardizedFinancials` | Lulu/FR reconcile |
| `note_handoff.py` | `director/ingestion/note_handoff.py` | Director | Appends already-authored note facts | prepare script |
| `excel_import.py`, `manual_hk.py` | `legacy/ingestion/` | Legacy | Transcribed Excel/JSON adapters | ingest / demo tests |
| `future_adapters.py` `HKEXAdapter`, `SECAdapter`, `SGXAdapter` | delete in place | Remove | `NotImplementedError`; TARGET forbids HKEX scrape; no production import | `rg` definition + `README-HK-TRAINER.md` mention only |
| `base.py` / `reconciler.py` | `modeler/ingestion/` | Modeler | Shared checksum reconcile | build refuse-on-fail |
| `management_kpi_enrichment.py` `inspect_source_pdf`, `enrich_management_working_copies` | `legacy/ingestion/management_kpi_enrichment.py` | Legacy | Working-copy PDF page bind; not Extractor product; company build does not call enrich | `test_management_kpi_enrichment.py` |

Raw source provenance belongs to Extractor. Analytical transformations and
calculation provenance belong to Modeler.

### 7.4 `core/model/reported_margin.py` (exhaustive)

Git blob at B, at reviewed 10.1.1 B `312cb8a…`, and the working tree: SHA-256
`94bb8a1c23e4ad5523716fac7fd355c7ff6fda3f778dce283a450afd4bf4eec4`
(44917 bytes). Do not classify this file as homogeneous Modeler.

Shared existing contract (no new type): `MarginRelationshipAssessment` and
the `KIND_*` string constants stay on `modeler/reported_margin.py`. Director
documents the field-and-branch producers; Director does not own the type.
Interpreter and Composer import the type and constants. `KIND_ATTRIBUTED_EXPLANATION`
is unused by current assemblers; it remains Interpreter claim vocabulary
with Composer `_KIND_LABELS` display `"management explanation"`.

After the split, Modeler must not import Interpreter or Composer; Interpreter
must not import Composer labels or formatters.

#### A. Modeler — series, signs, contributions, residuals, availability, mechanical validity

Destination file: `modeler/reported_margin.py`.

| Source symbol / field | Destination symbol | Reason | Consumers | Verification |
|---|---|---|---|---|
| `GROSS_PROFIT_CONCEPT` … `OTHER_OPERATING_CONCEPTS` | same | Concept keys | resolvers, workbook | resolution tests |
| `EXPENSE_PRESENTATION_POSITIVE` / `_SIGNED` | same | Convention codes | `expense_presentation_factor` | signed-SG&A tests |
| `RATIO_RECONSTRUCTION_TOLERANCE` `1e-8`, `AMOUNT_RECONSTRUCTION_TOLERANCE` `1e-4`, `PUBLICATION_RATIO_TOLERANCE` `5e-5`, `PUBLICATION_AMOUNT_TOLERANCE` `1.0` | same | Mechanical claim gates | `residual_blocks_reconstruction_claim`; identity `established` | residual / publication tests |
| `KIND_IDENTITY`, `KIND_REPORTED_FACT`, `KIND_OBSERVED`, `KIND_CAUSAL`, `KIND_UNESTABLISHED`, `KIND_ATTRIBUTED_EXPLANATION` | same constants on this file | Shared vocabulary; **producers** are the branch maps below | Interpreter / Composer | kind assertions |
| `AMOUNT_BRIDGE_CONVENTION` formula clause | `AMOUNT_BRIDGE_FORMULA` | `ΔGP = GM_prior × ΔRevenue + Revenue_prior × ΔGM + ΔRevenue × ΔGM` only | GP-bridge residual; sheet math | Lulu GP residual `< 1e-6` |
| `ReportedMarginAvailability` / `ReportedMarginSources` | same | Unique IS resolution flags and LineItems | compute; workbook provenance | availability / source-fidelity |
| `ReportedMarginSeries` numeric fields L119–160 | same | Levels, changes, signed contributions, residuals | assemble; `historical_expected`; `reference_model`; checker | `test_reported_margin` series |
| `ReportedMarginSeries.amount_bridge_convention` | Composer field on the same record | Rendered sentence, not the formula | `_amount_bridge_block` | convention text |
| `ReportedMarginSeries.assessments` | container only | Not a producer | assemble; `analysis.assessments` concat | see branch map |
| `MarginRelationshipAssessment` dataclass | same (shared contract) | Existing seven-part record | revenue + margin + research | type import |
| `_resolve_unique_is`, `reported_margin_availability`, `resolve_reported_margin_sources` | same | Unique explicit IS lines; no label fallback | compute; workbook | concept / renamed-label |
| `_revenue_ready` and `*_applicable` | same | Family presence from unique sources | compute; assemble gate | independent-family omissions |
| `expense_presentation_factor`, `analytical_expense`, `expense_presentation_factor_for_sources` | same | Majority nonzero sign; keep opposite-sign reversals; do not `abs()` source values | compute; `reference_model` | positive vs signed; FR SG&A |
| `residual_blocks_reconstruction_claim`, `publication_reconstruction_allowed` | same | Unknown/material residual blocks an exact claim | identity `established`; `selection.publication_reconstruction_allowed` | residual / reconstruction tests |
| `_difference_or_na`, `_adjacent_changes`, `_adjacent_amount_changes`, `_adjacent_optional_changes` | same | Missing ≠ zero; opening period None | compute | zeros / missing |
| `_sum_optional`, `_reconstruct_operating_profit` | same | GP − SG&A − optional impairment − optional other | compute | Lulu residual 0 |
| `_signed_ratio_contributions`, `_sum_contributions`, `_pair_residual`, `_numeric_ratio` | same | Expense contributions negated; omitted parts stay omitted | compute; latest-movement tests | sign / missing / zero |
| `compute_reported_margin_series` numeric body L382–655, 680–718 | same, numeric-only return | Series and residuals only; do not call interpret/word | Director sequence; assemble; workbook | series tests |
| Identity residual facts for assessments | `_margin_identity_validity`, `_margin_contribution_validity`, `_gross_profit_bridge_validity` | `max_resid` and `residual_blocks_reconstruction_claim` | Interpreter/Composer consume flags | Lulu contribution `established` |
| Disclosed charge observations | `_impairment_charge_observations` | Periods with `amount > 0`, disclosed zeros, line presence | Interpreter recurrence; Composer magnitude | Lulu FY2023 407913 / later 0 |
| Latest-movement numeric tests | `_latest_adjacent_movement` | Latest index with defined OM pair; `om_move`; signed `gm_move`/`sga_move`/`imp_move`/`other_move`; `om_move < 0`; `gm_move * om_move < 0`; both-negative conjunction | Interpreter contradiction class; Composer pp | oppose-aggregate test |

#### B. Interpreter — causal limits, recurrence, interpretive support

Destination file: `interpreter/reported_margin.py`.

| Source symbol / field | Destination symbol | Reason | Consumers | Verification |
|---|---|---|---|---|
| Mix/cost/leverage support decision L976–997 | `interpret_unsupported_mix` | Always emitted. `kind=KIND_UNESTABLISHED`, `established=False`. Causal limit: face-of-statement components do not isolate mix/markdowns/freight/costs/occupancy/leverage | Composer `word_unsupported_mix` | FR/Lulu `unestablished_inference` and mix name |
| Impairment recurrence L970 | `interpret_disclosed_charges` | `stability` judgment: episodic, not a recurring operating burden. `kind=KIND_REPORTED_FACT` (claim typology). Does **not** own amounts or zeros | Composer charge sentences | no current wording assertion (gap) |
| Latest-movement contradiction class L1057–1073 | `interpret_latest_movement` | Class only: both GM and SG&A reduced OM; component direction differs from reported OM; or none required. `kind=KIND_OBSERVED` | Composer contradiction sentences | `test_component_direction_can_oppose_aggregate_margin` |
| Identity branches | none beyond consuming Modeler validity | No causal or recurrence judgment | Composer identity sentences | Lulu identity `established` is Modeler |

Do not have Interpreter import `_format_*`, contribution-schedule labels,
or `AMOUNT_BRIDGE_CONVENTION` prose.

#### C. Composer — labels, sentences, numeric formatting, rendered qualifications

Destination file: `composer/reported_margin.py`.

| Source symbol / field | Destination symbol | Reason | Consumers | Verification |
|---|---|---|---|---|
| `AMOUNT_BRIDGE_CONVENTION` rendered | same string | Preserve exact wording | `ReportedMarginSeries.amount_bridge_convention`; GP-bridge `magnitude`; `_amount_bridge_block` fallback | convention paragraph |
| Identity / contribution / GP-bridge text fields | `word_margin_identity`, `word_margin_contributions`, `word_gross_profit_bridge` | `name`, `direction`, `magnitude`, `reconstruction`, formatted `residual`, `stability`, `contradictions`, `disclosure_support`, `limitation`. Copy Modeler `kind`/`established` | research appendix; `_finding_sentence` | Lulu contribution name + `established` |
| Charge sentences | `word_disclosed_charges` | `"{period.isoformat()} {amount:,.0f}"` join or `"disclosed zeros only"`; residual/zero prose; copy Interpreter `kind` and Modeler disclosure-`established` | same | no current format assertion (gap) |
| Mix sentences | `word_unsupported_mix` | Preserve `mix_limit` wording; copy Interpreter flags | same | mix name + not established |
| Latest-movement sentences | `word_latest_movement` | `"operating margin fell"` / `"rose"`; `{om_move * 100:+.2f} pp`; component pp parts; contradiction sentences from Interpreter class | same | oppose-aggregate substring |
| Workbook contribution labels | stay with `reference_model` / catalog (Modeler sheet construction uses these strings) | `"Δ gross margin contribution"` and signed SG&A/impairment/other labels are existing sheet text | ALT DuPont | `test_rendered_component_contribution_schedule` |

#### `_assess_margin_relationships` branch producers

Append order is the current if-chain. Collection order after revenue
assessments is this order. Composer words each branch after its
`kind`/`established` owner.

| Branch (current guard) | `kind` | `established` | Other judgment | Wording | Destination symbols |
|---|---|---|---|---|---|
| Component identity L864–897 (`reconstructed_om`, `om_residual`, `sga_disclosed`) | Modeler `KIND_IDENTITY` | Modeler `max_resid is not None` and not `residual_blocks_reconstruction_claim(..., kind="ratio")` | none | Composer | `_margin_identity_validity` / `word_margin_identity` |
| Component contributions L898–927 (`contribution_sum`, `contribution_resid`) | Modeler `KIND_IDENTITY` | Modeler same ratio residual rule | none | Composer | `_margin_contribution_validity` / `word_margin_contributions` |
| Gross-profit bridge L928–949 (`gp_change_residual is not None`) | Modeler `KIND_IDENTITY` | Modeler `max_gp is not None` and not `residual_blocks_reconstruction_claim(..., kind="amount")` | none | Composer | `_gross_profit_bridge_validity` / `word_gross_profit_bridge` |
| Disclosed charges L950–975 (`impairment_disclosed` and amounts) | Interpreter `KIND_REPORTED_FACT` | Modeler True from disclosed line + amounts tuple (actual decision is observation presence, not recurrence) | Interpreter episodic-versus-recurring | Composer formats amounts/zeros separately from recurrence | `_impairment_charge_observations` / `interpret_disclosed_charges` / `word_disclosed_charges` |
| Unsupported mix/cost/leverage L976–997 (always) | Interpreter `KIND_UNESTABLISHED` | Interpreter `False` | Interpreter causal limit | Composer `mix_limit` | `interpret_unsupported_mix` / `word_unsupported_mix` |
| Latest adjacent movement L999–1080 (OM, `sga_ratio`, GM, latest defined pair) | Interpreter `KIND_OBSERVED` | Modeler True from latest defined OM pair (actual decision is pair availability, not the contradiction class) | Interpreter contradiction class; Modeler owns the numerical direction tests | Composer direction phrase and `+.2f` pp | `_latest_adjacent_movement` / `interpret_latest_movement` / `word_latest_movement` |

Numerical direction tests (`om_move < 0`, `gm_move * om_move < 0`, both
contributions negative) are Modeler. Their English expression and the
causal reading of those signs are not.

#### Result-field producers (containers are not producers)

| Field | Producer |
|---|---|
| `ReportedMarginSeries` numeric fields | Modeler |
| `ReportedMarginSeries.amount_bridge_convention` | Composer |
| `ReportedMarginSeries.assessments` | concatenation of the six branches above; **not** a producer |
| `RevenueDriverHypothesisTest.assessment` | the `_assess_revenue_test` branch that returned it; **not** a producer |
| `RevenueDriverAnalysis.assessments` | `tuple(test.assessment for test in assessed if assessment)` then `+ margins.assessments`; **not** a producer |
| `DriversView.assessments` | `_unique_assessments(analysis_assessments + margin_assessments)`; **not** a producer |
| `DriversView.relationship_findings` | Composer `_finding_sentence` |

**Branch precedence and concatenation.** `_THEME_BUILDERS` order is store
expansion, comparable sales, productivity, geographic growth. Margin
branches then append in the table order above. `assemble_drivers_view`
concatenates `analysis.assessments + margins.assessments`. When analysis
ran, it already includes `margins.assessments`, so the second copy is a
duplicate. `_unique_assessments` keeps the first `name` and drops later
duplicates. Revenue names and margin names do not collide. Preserve this
first-name-wins order; do not re-sort.

#### Handoffs, callers, destination imports

Director sequences existing callers (`build_company`, `assemble_drivers_view`,
`publish_drivers`, Overview opening, workbook):

1. Modeler `compute_reported_margin_series` (numeric) and
   `compute_revenue_driver_analysis` observations + identity
   `kind`/`established`.
2. Interpreter `interpret_margin_relationships` and descriptive/causal
   `interpret_revenue_assessment`.
3. Composer `word_margin_relationships` / `word_revenue_assessment`
   (preserve `kind`/`established`).
4. `assemble_drivers_view` concatenates existing records; it does not
   interpret or word.
5. `select_driver_argument` does not read assessments (appendix-only).
6. Composer `_assessment_block` / `_finding_sentence` / `_KIND_LABELS` /
   `_amount_bridge_block`.

Workbook consumers (`reference_model._prepare_reported_margin`,
`historical_expected.reported_margin_expected_series`,
`trainer.checker` live formulas, `component_catalog` families) use series
and specs only. They must import Modeler `reported_margin` and must not
import Interpreter or Composer assessment helpers.

| After-move import | Allowed dependencies |
|---|---|
| `modeler/reported_margin.py` | `line_resolver`, `ratio_values`, `source_values`, `data.interface` |
| `interpreter/reported_margin.py` | Modeler series, KIND constants, residual helpers |
| `composer/reported_margin.py` | Modeler numbers + Interpreter codes; no series math |
| `modeler/revenue_driver.py` | Modeler margin series/type; not Interpreter/Composer |
| `composer/research/drivers.py` | filled assessment records + `_KIND_LABELS` |
| Compatibility façade in current files | sequences the three phases; may not choose judgments |

#### Preservation checks (existing coverage → future split)

| Check | Owner after split | Existing coverage | Gap |
|---|---|---|---|
| Residual thresholds 1e-8 / 1e-4 / publication 5e-5 and 1.0 | Modeler | `test_reported_margin` Lulu residuals 0 / `< 1e-12`; FR residual blocks publication; `residual_blocks_reconstruction_claim` | no assertion that identity `established` uses those exact limits |
| Revenue identity `established` iff `max_resid < 1e-4` | Modeler | geo/footprint residuals `== 0` or `< 1e-6` in seven-part | seven-part does **not** assert identity `kind`/`established` |
| Missing ≠ zero; opening None; omitted line None | Modeler | `test_component_contributions_sign_missing_zero_and_residual`; zeros/undefined | none for those series facts |
| Signed contributions (expense negated) | Modeler | sign tests; FR analytical SG&A | none |
| Fiscal alignment / canonical axis | Modeler | Lulu/FR period lists; `test_revenue_driver` interim-axis reject | none |
| Provenance / source signs unchanged | Modeler | source-fidelity; FR source SG&A negative, series positive | none |
| Identity `kind` + contribution `established` | Modeler | Lulu kinds contain `identity`; contribution name `established` | GP-bridge assessment unasserted |
| Mix `kind=unestablished_inference`, `established=False` | Interpreter | Lulu/FR any-unestablished and mix name | `mix_limit` sentence unasserted |
| Latest-movement contradiction wording | Interpreter class + Composer sentence | oppose-aggregate substring | class enum not separately tested |
| Impairment episodic judgment | Interpreter | none | coverage gap |
| Charge amount formatting / disclosed zeros | Composer | none | coverage gap |
| Assessment order / first-name-wins dedup | assemble pass-through | none | coverage gap |
| `_finding_sentence` / `_KIND_LABELS` / appendix table | Composer | `test_research_drivers` does not read `view.assessments` or `relationship_findings` | coverage gap |
| Current rendered assessment sentences | Composer | only the oppose-aggregate substring and mix/identity names | do not invent new wording checks; preserve current strings when tests exist |
| Workbook contribution labels | Composer/sheet text already asserted | `test_rendered_component_contribution_schedule` | none |
| Seven-part names + SPSF flags | revenue §7.0 | `test_lululemon_revenue_reconstruction_and_seven_part_validation` | identity flags and finding-sentence format unasserted |

Do not invent completed checks for the gaps. Later executing steps reuse
these existing tests after the split.

---

## 8. Figures versus relationships versus presentation

| Surface | Valid numerical series (Modeler) | Economically meaningful relationship (Interpreter) | Publication form (Composer) |
|---|---|---|---|
| `drivers.py` plotters | bar heights from assembled series | not decided in plotters | titles, labels, 53-week annotation, source notes, `style.series_color` |
| `style.py` | none | none | fonts, grayscale, spacing, `savefig` |
| `document.py` | none (reads Markdown/PNG) | none | Word/PDF layout, captions |
| `publish.py` | none | none | apply-if-applicable, verify headings/figures |
| `figure_ids` | — | Interpreter may ask a figure question | Composer decides whether a PNG is emitted |
| Drivers assessment appendix | Modeler residuals and identity `established`; Interpreter descriptive/causal/`reported_fact` kinds and support | same field-and-branch map as §7.0 / §7.4 | `_KIND_LABELS`, `_finding_sentence`, table form |

A persuasive chart does not invent an analytical relationship.

---

## 9. Management-emphasis admission

**Admission path (existing objects only)**

1. Extractor-origin rows on `StandardizedFinancials.historical_strategy` (`ROLE_ATTRIBUTION`).
2. Modeler `_attributions_from_financials` copies `ROLE_ATTRIBUTION` only (`drivers.py` L226–237).
3. `revenue_driver_applicable` is `bool(data.disclosures)`. Disclosure presence gates compsales / footprint identity / geo reconstruction **series**, not geo/store/margin **levels**.
4. Interpreter `_margin_questions` builds `management_margin_attribution` when `latest_attr` is nonempty.
5. Composer `_margin_argument` may insert attributed prose beside a margin finding.
6. Composer `_attribution_block` publishes the locator table when `view.attributions` is nonempty.

**Step 10.5:** investigation no longer sets `PUBLICATION_MAIN` for attribution
or comparable-sales presence. Attribution remains `supported_as_attribution`
with locators and qualifiers; the appendix table is retained regardless of
principal selection. Attributed margin prose appears only beside an
independently selected margin finding. Comparable-sales observations stay
auditable in the appendix.

**Rule that treated emphasis as more than attributed evidence (removed in 10.5; evidence kept)**

```868:935:core/research/selection.py
    if latest_attr:
        ...
                publication=PUBLICATION_MAIN,
```

Condition: any latest-period attribution. A quantified `approximate_amount`
only changes the materiality sentence, not an independent Interpreter test
that the theme is an economic driver.

**Related MAIN-on-presence (compsales)**

```467:551:core/research/selection.py
    if compsales:
        ...
                publication=PUBLICATION_MAIN,
```

`select_driver_argument` already demotes compsales to appendix (L1233–1240).
Investigation should stop setting `PUBLICATION_MAIN` for presence alone.

**What does not promote emphasis to driver status**

```1170:1176:core/research/selection.py
    if attribution and attribution.publication == PUBLICATION_MAIN and margin:
        appendix.append(attribution)
        ...
                "Preserved with the accounting-margin finding; not an independent principal driver.",
```

Principals are only: non-zero margin change; geo operating story; footprint
divergence if not geo; cash if nothing else is principal.

**Removal while retaining attributed evidence**

- Stop setting `publication=PUBLICATION_MAIN` for attribution presence.
- Keep the `ResearchClaim` (`CLAIM_ATTRIBUTION`, locators, qualifiers
  `not independently verified` / `outside the accounting bridge`,
  `status="supported_as_attribution"`).
- Keep `_attribution_block` and attributed prose only beside an independently
  selected margin finding.
- Keep `ROLE_ATTRIBUTION` assembly and source locators.
- Do not use disclosure presence as a silent principal-driver gate.

---

## 10. Engine, workbook, Trainer inversion

Reusable workbook/model/check machinery is Modeler. Trainer practice overlay
is Legacy. Active code must not depend on Legacy as a hidden implementation
layer.

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `core/engine/build_contract.py` `BUILD_MODULES` policy table | `director/build_contract.py` | Director | `forecast` is `deferred` | `test_build_contract.py` |
| `core/engine/build_contract.py` prepare/writer registration | `modeler/engine/build_contract.py` | Modeler | Executes Director policy | `test_build_contract.py` |
| `component_catalog.py` | `modeler/engine/component_catalog.py` | Modeler | Semantic families / coordinates | `test_reference_integrity.py` |
| `semantic_map.py` | `modeler/engine/semantic_map.py` | Modeler | Coordinate map | `test_reference_integrity.py` |
| `map_embed.py` | `modeler/engine/map_embed.py` | Modeler | Embed sidecar | `verify_staged` |
| `reference_model.py` `ReferenceModelBuilder.build` | `modeler/workbook.py` | Modeler | Workbook construction | Lulu/FR benchmarks |
| `include_deferred_forecast` / `run_scenario` | stay gated default off | Modeler (dormant) | Do not activate | `test_historical_v1_exit_gate.py` |
| `reference_model` lazy imports of `trainer.check_context` | `modeler/check_context.py` | Modeler | Live formulas and source-payload embed are BAV machinery | live-formula tests |
| `core/trainer/workbook.py` `build_bav_workbook` | `modeler/build_bav.py` | Modeler | “professional BAV. Does not derive a Trainer.” Mis-housed | `test_current_build.py` |
| `TrainingWorkbookGenerator.finalize_bav` | `modeler/build_bav.py` `finalize_bav` | Modeler | Workbook finalize without opening prose | `verify_staged` |
| `_add_bav_opening` | `composer/workbook_opening.py` `_add_bav_opening` | Composer | Overview prose, navigation, fallback; consumes §7.1 fields | `verify_staged` Overview; opening tests |
| `core/trainer/semantic_io.py` `load_semantic_map`, sidecars | `modeler/semantic_io.py` | Modeler | Sidecar I/O is BAV | `verify_staged` |
| `derive_trainer_workbook`, practice blanking, `checker.py` `check_workbook` | `legacy/trainer/` | Legacy | Practice overlay and scoring | `test_trainer.py`; optional check if Trainer exists |

**Current (wrong) direction — active → Trainer**

- `core/__main__.py` L27–29 imports `check_workbook`, `semantic_io`, `build_training_workbook`
- `core/current_build.py` L278 imports `build_bav_workbook`
- `core/engine/reference_model.py` lazy-imports `trainer.check_context`

**Required inversion**

1. Move `build_bav_workbook`, semantic-map I/O, live formulas, and BAV check-context embed into Modeler.
2. Leave in Legacy only derive/blank/score/chrome.
3. `build_company` / `cmd_build` call Modeler only.
4. `cmd_check` may optionally import Legacy if a Trainer file exists.
5. Tests that need a Trainer call Legacy after Modeler build.
6. Keep research free of `core.trainer` imports.

`verify_staged(..., trainer=None)` already honors “build does not require
Trainer”. Explicit `-o` JSON still derives a Trainer; that dual path is a
Director CLI compatibility decision, not a new feature.

---

## 11. Director ownership, STYLE.md, DRIVER.md

Director owns architecture, component boundaries, orchestration, project
configuration, global policies, high-level Markdown specifications, interfaces,
handoff contracts and lifecycle coordination. Shared analytical implementation
belongs to the substantive component.

Designated destinations:

- `director/docs/STYLE.md` ← current root `STYLE.md`
- `director/docs/DRIVER.md` ← current root `DRIVER.md`
- `director/docs/MIGRATION_INVENTORY.md` ← this file (created this step)

Protected locations (do not move): `TARGET.md`, `SESSION.md`,
`IMPLEMENTATION.md`. `RESULT.md` stays at root.

### Reference updates required when STYLE/DRIVER move

| Reference | Change |
|---|---|
| `core/tests/test_research_drivers.py` L86 `ROOT / "STYLE.md"` | `ROOT / "director/docs/STYLE.md"` |
| `core/tests/test_research_drivers.py` L967 `ROOT / "DRIVER.md"` | `ROOT / "director/docs/DRIVER.md"` |
| `core/tests/test_research_drivers.py` L110 `assert "STYLE.md" in` README | accept `director/docs/STYLE.md` |
| `README.md` L50, 54, 72 “root `STYLE.md`” | `director/docs/STYLE.md` |
| `core/research/style.py` docstring “root STYLE.md” | Director path |
| `DRIVER.md` L5, 29, 115, 117, 175, 204, 209 bare `STYLE.md` | `director/docs/STYLE.md` after both move |

Do not rewrite historical SHA tables in `RESULT.md`. TARGET / SESSION /
IMPLEMENTATION already name the destinations and must not be edited by Cursor.

`README.md` is still titled “BAV — Hong Kong Edition” and
`test_learner_ready_presentation.py` asserts that heading. Updating the
product face to BAV Compiler must change the test in the same step.

---

## 12. Extractor boundary

Existing Extractor implementation is JSON-contract I/O only. There is still
no production PDF/statement extractor. Do not implement extraction, scrapers,
or `future_adapters`.

Owned Extractor destinations (existing code, moved later):

- `extractor/data/filing.py` — `ExtractedFiling` contract
- `extractor/data/filing_json.py` — `load_extracted_filing`, parse helpers,
  `load_extracted_json_object`, `extracted_filing_to_payload`
- `extractor/data/extracted_kind.py` — `classify_extracted_payload`
- `extractor/data/management_kpi_json.py` — parse/load management-KPI documents
- `extractor/data/filing_validator.py` — `bind_source_file`, `source_row_identity`
- `extractor/data/operating_kpi_contract.py` — parse-time fact-type / label shape
- `extractor/data/historical_strategy.py` — `disclosure_locator` + disclosure types
- `extractor/README.md` — documentation-only PDF boundary

Company `python -m bav build` reads `reconciled/standardized.json` through
Modeler `standardized_from_payload`. It does not call `load_extracted_filing`.
`validate-source` / `reconcile` Director routes call Extractor loaders.

Closest PDF-touching code remains Legacy
`inspect_source_pdf` / `enrich_management_working_copies`. That is not a
reason to build a new Extractor.

Create later with the Extractor move:

```
extractor/README.md
  BAV consumes ExtractedFiling JSON and bound source PDFs.
  This repository does not extract statements from PDF.
  Upstream LLM/human extraction is permitted; the published contract is
  filing.py plus filing_json loaders. Do not add scrapers here.
```

---

## 13. Legacy categories and Remove candidates

Actual Legacy categories (from this inventory, not a preset list):

1. Trainer practice overlay and Check scoring
2. HK manual ingest / demo workbooks
3. Coverage-skill pipeline (skills, sentinel, plugin zip, Apps Script)
4. Retired release/benchmark builders and GOOGL/FR audit scripts
5. Historical Office verifiers and SHA-bound native-excel JSON
6. Historical diagnosis / resume / superpowers design notes
7. Existing `legacy/` Gem instructions
8. PDF page-bind enrichment (working-copy binder)
9. Prior-live / ordinary-reconcile local evidence copies

Active implementation required by BAV build/publish must move out of Trainer
into Modeler/Composer before Legacy is isolated.

### Remove (delete in place; never create `remove/`)

| Item | Absence-of-use / no-preservation-value |
|---|---|
| `scripts/build_fast_retailing_source_facts.py` | Obsolete header; unused; writes absent `source_facts.json` |
| `core/ingestion/future_adapters.py` stubs | No production import; TARGET forbids building them |
| `FIGURE_NAMES`, `FIGURE_PLOTTERS`, `_calendar_limit_block` | Dead symbols |
| Empty `benchmark/`, `release/` dirs (`.DS_Store` only) | Trees already relocated; Git history keeps old blobs. Runtime has no fallback |
| `build/input/lululemon/evidence/stale-benchmark-reconciled/` | Empty |
| `build/input/fast_retailing/evidence/_extract/*.txt` | Regenerable cache; not a build input |
| gitignored example sidecars | Regenerable |
| `__pycache__/`, `.pytest_cache/`, `.DS_Store` | Regenerable / OS junk |

Do not delete Git history. Do not delete local extracted/reconciled JSON.
Do not delete source PDFs if they are later restored until
`build/input/<company>/source/` holds verified bytes.

`validate_standardized` is unused but is a Director contract, not Remove,
until out-of-tree use is known.

Plugin zip: keep one Legacy copy. Deleting it is optional only because
`build_plugin_zip.sh` + Git history regenerate it; default is keep.

---

## 14. Ordered movement / split sequence

Subsequent reviewed steps execute this order. This step does not execute it.

1. Create visible roots `director/`, `extractor/`, `modeler/`, `interpreter/`, `composer/`; keep `legacy/`. Add `extractor/README.md`. Move Extractor contract + `filing_json` loaders + `classify_extracted_payload` + management-KPI parse + provenance bind per §7.3 / §12.
2. Move `STYLE.md` and `DRIVER.md` to `director/docs/` and apply §11 reference updates, including README identity if that step touches README. Protected planning docs stay.
3. Split `revenue_driver.py`, `revenue_strategy_synthesis.py` and `reported_margin.py` per §7.0–7.1 and §7.4 (observations / identity validity / verdicts / wording). Then split `drivers.py` / `selection.py` per §5. Apply the management-emphasis removal in §9. Deduplicate reconstruction helpers. Assessment concatenation stays first-name-wins; façades may not choose judgments.
4. Move remaining Modeler calculation modules, data payload, ingestion reconcile/standardize, engine workbook, `build_bav_workbook`, semantic I/O, check-context embed.
5. Move Interpreter judgment functions and classification/normalization rationales / strategy inference.
6. Move Composer `style.py`, `document.py`, `publish.py`, Drivers prose/plots, Overview opening/navigation.
7. Move Director CLI / `current_build` / `project_companies.json` / build-contract policy. Keep `python -m bav` and company name interfaces. Director `build_company` sequences Modeler → Interpreter → Composer before workbook write.
8. Relocate Legacy (Trainer remainder, skills, automation, retired scripts, HK demo, historical docs/verifiers).
9. Delete Remove items in place. Update imports, CLI routes, package docstrings, tests, README, `docs/FAST_RETAILING_BENCHMARK.md` stale paths, `source_manifest.json` if PDFs are restored.
10. Verify §15. Stop. No second-phase features.

### Affected surfaces (must be updated in the executing steps)

| Surface | Change |
|---|---|
| Imports | `core.research.*` → component packages; `core.trainer.workbook.build_bav_workbook` → Modeler; research stays free of Legacy |
| CLI routes | Same public commands; bodies follow new owners |
| Package metadata | `core/__init__.py` / `bav/__init__.py` branding → BAV Compiler; no `pyproject.toml` exists |
| Build/publish | `build/input/<slug>/` and `build/output/<slug>/` stay canonical |
| Tests | Path updates for STYLE/DRIVER; split `test_research_drivers.py` with the modules |
| Docs | README, DRIVER↔STYLE links, FR benchmark paths |

Preserve public `bav` and canonical company input/output interfaces.

---

## 15. Verification routes (for later executing steps)

This inventory step does not rebuild, publish, or run native Office.

**Existing pytest (apply after moves):**

- `core/tests/test_research_drivers.py` — Drivers split, CFO, reconstruction, headings, STYLE/DRIVER paths
- `core/tests/test_publication.py`, `test_current_build.py`, `test_build_cli.py`, `test_build_contract.py`
- `core/tests/test_reported_margin.py`, `test_revenue_driver.py` — after the §7.0 / §7.4 split, keep residual, missing-versus-zero, sign, fiscal, provenance, kind/flag and current wording assertions; do not treat collection assembly as a second producer
- Filing / KPI / geo admission and reconcile suites
- Analytical family suites listed in §4.5
- `test_lululemon_benchmark.py`, `test_fast_retailing_benchmark.py`
- `test_trainer.py`, `test_learner_ready_presentation.py` for optional Trainer

**Representative company paths**

```text
python -m bav build Lululemon
python -m bav check Lululemon
python -m bav publish Lululemon
python -m bav build FastRetailing
python -m bav check FastRetailing
python -m bav publish FastRetailing
```

Local snapshot now: both companies have nonempty `*_Drivers.md`, zero-byte
Forecast/Valuation/Overview, Word/PDF, workbook, supporting JSON. **No Trainer
under `build/output/`**. Optional Trainer remains
`python -m bav build <json> -o …` and `check` only if a Trainer file exists.

**Native Office is change-dependent.** Do not treat historical receipts as
current proof.

- Recalc + saved-cache is required when workbook **formulas/dependencies** change.
- Readability inspection is required when **presentation** changes.
- `docs/native-excel-*.json` `source_sha256` is bound to a specific generation.
  Mismatch → BLOCKED. Later verify does not prove an earlier gate.
- `.autocycle.toml` opts into `excel` and `word`. Use Office Bridge helpers
  only in the executing steps that change those surfaces.

Preserve analytical signs, fiscal labels, source links, qualifications,
residuals, fail-closed controls, zero-byte research placeholders and useful
existing behavior.

Inventory completion does **not** establish migration acceptance.

---

## 16. Remaining behavior defects (not ownership gaps)

Ownership and destinations that previously blocked execution are decided in
§7.0, §7.1, §7.3, §7.4, §10 and §12. The items below are unrelated runtime or
product-behavior defects. They must not be treated as unfinished ownership.
Do not expand this inventory correction into runtime repairs.

1. **`_latest_index` vs `_latest_growth_index`.** Selection uses the last period; prose/plots use the last period with non-None `revenue_growth`. Same view can qualify and narrate different years if trailing growth is missing. Both keep their §5 destinations; later repair is not this design.
2. **`_margin_is_material` is a non-zero test.** Named as materiality; classified as Modeler eligibility. Interpreter economic materiality is not separately implemented.
3. **Attribution without a margin question** (`select_driver_argument` L1179–1186) records `action=attribution.publication` but does not add the id to principal/secondary/appendix. `_attribution_block` still prints if `view.attributions` is set.
4. **Disclosure-gated reconstructions.** No `historical_strategy` disclosures ⇒ footprint/geo reconstruction series are None, while store/geo levels still assemble. That is current Modeler gating via `revenue_driver_applicable`, not a principal-driver gate. Changing the gate is a later behavior decision.
5. **`overlap` and `main_body_table_reason(s)` unused.** Combining footprint+compsales and margin+attribution is hard-coded.
6. **`DriversView.margin_explanation` always `""`.** Dead field; do not invent a replacement.
7. **`relationship_findings` / `assessments` do not affect `select_driver_argument`.** Appendix-only. No new schema.
8. **`validate_standardized` unused.** Keep as Director contract pending out-of-tree confirmation.
9. **`cmd_build -o` still derives a Trainer** while company builds do not. Compatibility vs single-output remains a Director CLI policy; owners are split in §4.2.
10. **`_append_traced_spsf_occurrences`** can write KPI rows from PDF regexes into working copies. Off the canonical `extracted/` / `build` path. Legacy binder, not a reason to build Extractor.
11. **Three “validator” names.** `schema.validate_standardized` = Director unused contract; `data.validators` = Modeler checksums; `filing_validator.bind_source_file` = Extractor; `validate_operating_kpi_fact` = Modeler admission. Shared name only.
12. **Source PDFs are absent locally and not tracked at B.** Canonical destination is `build/input/<company>/source/`. `source_manifest.json` still cites `benchmark/fast_retailing/source/`. Restore-and-bind is later work; do not invent PDFs.
13. **`README.md` “BAV — Hong Kong Edition”** is asserted by `test_root_readme_is_practical_trainer_guide`. Product-face rename must update that Director test together.
14. **`latest-implementation` leftover** names `312cb8a…`. Ignored because `IMPLEMENT_BASE_SHA` is populated.

Resolved in this correction (no longer ownership blockers):

- `revenue_driver.py` is not homogeneous Modeler; §7.0 assigns every symbol.
- `_verdict_inference` judgment vs `THEME_LABELS` / templates is split in §7.1.
- `load_extracted_filing` is Extractor `extractor/data/filing_json.py`.
- `_add_bav_opening` is Composer; finalize is Modeler.
- Shared CLI/test/manifest/build-contract labels are split to one owner each.
- `reported_margin.py` is not homogeneous Modeler; §7.4 assigns every symbol
  and every `_assess_margin_relationships` branch.
- Revenue identity `kind`/`established` are Modeler residual products;
  descriptive/causal `kind`/`established` are Interpreter. Composer wording
  copies those fields. Blanket ownership of `test.assessment`,
  `analysis.assessments`, `ReportedMarginSeries.assessments` and
  `DriversView.assessments` is replaced by the field-and-branch maps.

These behavior items do not block beginning migration.
