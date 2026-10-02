# BAV Compiler — repository responsibility inventory

Step 10.1 design only. No runtime code was moved, deleted, or regenerated.
Every meaningful responsibility has exactly one disposition: Director, Extractor,
Modeler, Interpreter, Composer, Legacy, or Remove. Classification follows the
kind of decision. Configuration, tests, data and documentation inherit an
owner and are not additional active components. Do not create `remove/`.

Authenticated baseline **B** = `86ebdecb6c01a7153bbf6c90f5af16294753a3cd`.
Tracked historical content is the Git tree at B. Current working-tree files
were inspected for local inputs, generated outputs and empty leftover dirs.

---

## 1. Baseline authentication

| Record | Value | Result |
|---|---|---|
| `.git/autocycle/resume-state` `IMPLEMENT_BASE_SHA` | `86ebdecb6c01a7153bbf6c90f5af16294753a3cd` | Populated; used as B |
| `STATE_BRANCH` | `checkpoint/20260913-183303` | Matches `.git/HEAD` |
| `.git/refs/heads/checkpoint/20260913-183303` | `86ebdecb6c01a7153bbf6c90f5af16294753a3cd` | HEAD == B |
| `.git/autocycle/implementation-baseline.json` `head` / `branch` | same SHA / same branch | Bound |
| `.git/autocycle/work-state.json` allocated `10.1` | `source` = B, `work_id` = `7951a38d066a440e8bfa19cd9dc5ecc7`, `status` = `opened` | Attempt bound |
| `IMPLEMENTATION.md` `AUTOCYCLE_PLAN` | `step_id` 10.1, same `work_id` / `plan_id` | Bound |
| Ancestry | HEAD equals B | B is an ancestor of HEAD |
| `.git/autocycle/latest-implementation` | Points at `be5d9275…` and a `bav_trainer` log path | Ignored: `IMPLEMENT_BASE_SHA` is populated |

Fail-closed was not required. `latest-implementation` is leftover from another
repository path and is not the implementation baseline.

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
| `core/ingestion/` | 7 | Admission/reconcile = Modeler; no production extractor |
| `core/model/` | 4.4, 7 | Active historical Modeler; dormant forecast/RI stay Modeler |
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
| `cmd_build` explicit JSON `-o` | Director route; body still Legacy Trainer derive | compatibility users | Director + Legacy | Dual-output remains a CLI compatibility path | `test_build_cli.py` |
| `cmd_check` / `cmd_publish` / `cmd_list` | Director routes | CLI | Director | Check diagnostic; publish Composer; list Modeler catalog | company check/publish/list |
| `cmd_validate_source` | Director route over Extractor contract + Modeler bind | CLI | Director | Orchestrates already-extracted JSON | `test_filing_cli.py` |
| `cmd_reconcile` | Director route; body Modeler | CLI | Director | Writes reconciled artifacts | `test_filing_reconciler.py` |
| `cmd_ingest` + `HKManualDocumentAdapter` | Director route; adapter Legacy | CLI | Director + Legacy | Transcribed HK ingest, not canonical company path | `cmd_ingest` tests |
| `core/current_build.py` `PROJECTS`, `resolve_company`, `build_company`, `check_company_output`, `prepare_company_input`, atomic exchange | `director/current_build.py` | CLI, `document.py`, tests | Director | “Company metadata selects evidence locations, never accounting behavior” | `test_current_build.py` |
| `core/project_companies.json` | `director/project_companies.json` | `current_build.PROJECTS` | Director | Names/slugs/aliases/fixture paths | resolve Lululemon/LULU/FastRetailing/9983 |
| `core/build_status.py` | `modeler/build_status.py` | `build_company` | Modeler | Mechanical family availability | `test_current_build.py` |

### 4.3 Data contracts

| Current | Destination | Callers | Disposition | Reason | Verification |
|---|---|---|---|---|---|
| `core/data/filing.py` (`ExtractedFiling`, `SourceRef`, `FilingMetadata`) | `extractor/data/filing.py` (contract only) | ingestion loaders | Extractor | Documentary extracted-filing schema. Engine does not produce it from PDF | `test_filing_json.py` |
| `core/data/interface.py` `DocumentManifest`, `DataSourceAdapter` | `extractor/data/interface.py` | `HKManualDocumentAdapter`, ingest | Extractor | Source-document handoff | ingest tests |
| `core/data/interface.py` `StandardizedFinancials`, `LineItem`, statements | `modeler/data/interface.py`; Director names the handoff | engine, model, CLI, research | Modeler (payload) / Director (interface authority) | Model-facing contract | `standardized_from_payload(..., strict=True)` |
| `core/data/schema.py` `validate_standardized` | Director contract check **or** Remove if still unused after move | exported only | Director (keep as unused contract) | Completeness of StandardizedFinancials; no production caller | grep remains export-only |
| `core/data/validators.py` statement checksums | `modeler/data/validators.py` | reconciler, build refuse | Modeler | Arithmetic identities on standardized statements | `test_validators.py` |
| `core/data/standardized_io.py` | `modeler/data/standardized_io.py` | `prepare_company_input`, CLI | Modeler | Model-only JSON; strips formulas | round-trip tests |
| `core/data/line_identity.py` | `modeler/data/line_identity.py` | merge/classify | Modeler | Line identity | `test_line_identity.py` |
| `core/data/issuer_fiscal.py` | `modeler/data/issuer_fiscal.py` | `prepare_company_input` | Modeler | Issuer FY labels; never from calendar year of period-end | `test_issuer_fiscal.py` |
| `core/data/historical_operating_kpis.py` / `historical_segments.py` | `modeler/data/` | KPI/geo, IO | Modeler | Validated analytical contracts | KPI/geo tests |
| `core/data/historical_strategy.py` + fixture `core/tests/fixtures/strategy/lululemon_management_disclosures.json` | disclosures stay company-input / Extractor-shaped; loader consumed by Modeler | `prepare_company_input` | Extractor (source-bound text+locator) | “Not an extraction or research framework”; pre-authored JSON | `test_revenue_driver.py` |

### 4.4 Homogeneous Modeler modules

These files perform reproducible calculations from the same inputs and explicit
assumptions. Destination: `modeler/` keeping the current basename unless a
later split is listed.

| Current files | Disposition | Callers | Verification |
|---|---|---|---|
| `classification.py`, `financial_math.py`, `line_resolver.py`, `period_axis.py`, `ratio_values.py`, `source_values.py`, `source_availability.py`, `historical_expected.py` | Modeler | engine, tests | matching `core/tests/test_*.py` |
| `normalization.py` series arithmetic; `normalized_per_share.py` | Modeler | builder, checker | `test_normalization.py`, `test_normalized_per_share.py` |
| `reported_margin.py`, `revenue_driver.py` (arithmetic/tests), `revenue_per_store.py`, `geographic_segment.py`, `operating_kpi.py`, `operating_kpi_relationships.py`, `management_kpi.py` | Modeler | research assemble, workbook | corresponding tests + `test_research_drivers.py` series |
| `earnings_quality.py`, `earnings_quality_change.py`, `working_capital.py`, `profitability_drivers.py`, `profitability_change.py`, `roe_attribution.py`, `per_share.py`, `per_share_attribution.py`, `inventory_analysis.py`, `cash_rollforward.py`, `capex.py`, `fixed_asset.py`, `lease_liability.py`, `lease_rou.py`, `lease_repayment.py`, `deferred_tax.py`, `goodwill_intangibles.py`, `acquisition_cash.py`, `share_repurchase.py`, `ownership_attribution.py` | Modeler | engine, benchmarks | matching tests; Lulu/FR benchmarks |
| `operating_forecast.py` | Modeler (dormant) | `test_operating_forecast.py` only | Do not activate |
| `ri_engine.py` | Modeler (dormant) | `ReferenceModelBuilder` only if `include_deferred_forecast` | `test_normal_v1_build_does_not_call_run_scenario` |

Mixed inside otherwise Modeler files:

| Current | Destination | Disposition | Reason |
|---|---|---|---|
| `judgment.py` `classification_judgment_cases` (case list from `decision.ambiguous`) | `modeler/judgment.py` | Modeler | Deterministic case selection |
| `judgment.py` `CLASSIFICATION_JUDGMENT_TEMPLATES` rationale / consequence / prompt | `interpreter/classification_judgment.py` | Interpreter | Meaning of alternatives |
| `normalization.py` treatment rationales | Interpreter text; Modeler keeps case IDs and series | Interpreter + Modeler | Same split |
| `revenue_strategy_synthesis.py` | see §7 | split | Mixed |

### 4.5 Tests (inherited owners)

Tests are not a sixth component. Destination = owner’s `tests/` after the
implementation move.

| Group | Owner |
|---|---|
| `test_filing_json.py`, `test_filing_cli.py`, `test_management_kpi_{admission,enrichment,identity,reconciliation,history}.py`, `test_operating_kpi_facts.py`, `test_geographic_segment_facts.py`, `test_normalization_candidate_admission.py` | Extractor (bind) + Modeler (admit/reconcile) |
| `test_filing_reconciler.py`, `test_validators.py`, `test_issuer_fiscal.py`, `test_line_identity.py`, `test_line_resolver.py`, `test_classification.py`, `test_share_basis.py`, `test_historical_segment.py`, `test_source_availability.py`, `test_normalization.py`, `test_reported_margin.py` | Modeler |
| Analytical family `test_{earnings_quality*,working_capital,profitability_*,roe_attribution,per_share*,normalized_per_share,fixed_asset,lease_*,deferred_tax,goodwill_intangibles,capex,inventory_analysis,acquisition_cash,cash_rollforward,share_repurchase,ownership_attribution,operating_forecast}.py` | Modeler |
| `test_{operating_kpi_analysis,operating_kpi_relationships,operating_kpi_workbook,operating_kpi_management_history,management_kpi_analysis,revenue_per_store,revenue_driver,geographic_segment_analysis,geographic_segment_workbook}.py` | Modeler |
| `test_build_contract.py`, `test_reference_integrity.py`, `test_historical_v1_exit_gate.py`, `test_cross_company_robustness.py` | Modeler |
| `test_build_cli.py`, `test_current_build.py` | Director |
| `test_research_drivers.py` | split with §5 (Modeler / Interpreter / Composer) |
| `test_publication.py` | Composer |
| `test_learner_ready_presentation.py` | Composer + Director + Legacy (mixed file) |
| `test_trainer.py` | Legacy |
| `test_lululemon_benchmark.py`, `test_fast_retailing_benchmark.py` | Director (fixture policy) + Modeler |
| `test_cached_workbook_verifier.py`, `test_reference_workbook_audit.py` | Legacy |
| Fixtures `operating_kpis/lululemon_company_operated_stores.json` | Extractor-shaped fact handoff (referenced by `project_companies.json`) |
| Fixtures `ordinary_reconcile/lululemon/*` | Modeler protected reconcile snapshot |
| Fixtures `strategy/lululemon_management_disclosures.json` | Extractor-shaped attributed evidence |

### 4.6 Scripts

| Current | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `scripts/prepare_lululemon_operating_kpi_filings.py` | stay scripts or `extractor/` helper | Extractor | Copies extracts + appends authored store facts; does not write protected PDFs | `augment_extracted_filings` |
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
| `build/input/fast_retailing/source_manifest.json` | stay; rewrite paths to `build/input/fast_retailing/source/` when PDFs are restored | Extractor + Director | SHA ledger; currently names obsolete `benchmark/` paths | restore-then-bind |
| `build/output/<slug>/` workbook + supporting JSON | stay | Modeler | Reproducible analytical artifacts | `python -m bav build/check` |
| `build/output/<slug>/research/*.md`, `figures/`, `*.docx`, `*.pdf` | stay | Composer | Reproducible publication | `python -m bav publish`; Forecast/Valuation/Overview remain 0 bytes |

---

## 5. Mixed Driver splits

Keep existing types. Do not invent a reasoning schema. After the split,
`assemble_drivers_view` **stops** calling `select_driver_argument` (today
`drivers.py` L968). Interpreter runs as a separate call. Composer receives
`replace(view, selection=…)`.

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
| `_unique_assessments` L1023–1033 | same | assemble | Dedup assessments | appendix |
| `_latest_growth_index`, `_operating_profit_change`, `_series_at`, `margin_reconstruction_complete` L1493–1532 | same | headline, plots, tests | Mechanical reconstruction gate via `publication_reconstruction_allowed` | reconstruction tests ~L1025–1073 |

**B. Interpreter — not implemented as standalone functions in this file**

Judgment lives in `selection.py`. Drivers.py only consumes `view.selection`.
`_calendar_limitation` L445–458 is Interpreter judgment text over Modeler
calendar facts; wording is Composer. After split: Interpreter owns the
judgment; Composer owns the sentence.

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
| `_margin_reconstruction_complete` L706–723 | **delete**; call `drivers.margin_reconstruction_complete` | Duplicate | reconstruction tests |
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
| `_component_direction_phrase` L726–738 | Composer; merge with drivers duplicate | Wording | margin prose |
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

**Handoff 1 (Modeler → Interpreter):** `DriversView` numeric fields + `attributions` + `comparable_sales` + `assessments`. Interpreter already reads them.

**Handoff 2 (Interpreter → Composer):** `ResearchSelection` on the same view. Composer already reads `principal_ids`, `secondary_ids`, `figure_ids`, `questions[].strongest_conclusion`, `unresolved_requirement`.

**Handoff 3 (Modeler → Composer):** same series for appendix tables and plot arrays. Composer must not recompute identities.

### `DriversView`

| Field | Owner |
|---|---|
| `company_name`, `currency`, `units`, `periods`, `labels` | Modeler |
| `display_name`, `period_ended` | Composer |
| All revenue/profit/margin/geo/cash/inventory/footprint series and residuals L548–621 | Modeler |
| `stores`, `revenue_growth`, `store_growth`, `revenue_per_store`, `comparable_sales`, `store_only_comparable_sales` | Modeler |
| `fifty_three_week_period`, `issuer_fiscal_name`, `amount_bridge_convention` | Modeler |
| `assessments` | Modeler |
| `relationship_findings` | Composer (pre-worded sentences) |
| `margin_explanation` | unused (`""` at assemble); do not invent a replacement |
| `attributions` | Modeler container of Extractor locators |
| `selection` | Interpreter + Composer per `ResearchSelection` fields |

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
| `magnitude` | Modeler numbers inside an Interpreter-chosen comparison |
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
| `main_body_table_reasons` | Composer; **never populated** |

---

## 7. Synthesis, validators, ingestion

### 7.1 `core/model/revenue_strategy_synthesis.py`

| Symbol | Destination | Disposition | Reason | Verification |
|---|---|---|---|---|
| `disclosure_locator` | Extractor-shaped helper consumed by Interpreter | Extractor | Formats `source_file; page_reference; section; period-end` | `test_revenue_driver.py` locators |
| `strategy_synthesis_applicable` | `modeler/` | Modeler | `return revenue_driver_applicable(financials)` | applicability tests |
| `compute_historical_strategy_synthesis` when it calls `compute_revenue_driver_analysis` and reads verdict / sample / finding / limitations | `modeler/` orchestrator | Modeler | Pulls admitted tests; does not invent values | `test_strategy_synthesis_connects_findings_without_claiming_outcomes` |
| `_verdict_inference`, `_lead`, `_qualification`, `_productivity_gap`, `_counterexample_notes`, `_featured_disclosure` | `interpreter/historical_strategy.py` | Interpreter | Verdict wording, featured-role choice, causal limits | no “achieved outcome”; no promoting deferred SPSF |
| `THEME_LABELS`, `THEME_SCHEDULES`, `_schedule_clause`, `_navigation`, `PROFESSIONAL_FALLBACK` | `composer/overview.py` | Composer | Sheet names, navigation, fallback opening | `test_learner_ready_presentation.py` |
| `StrategyFindingInterpretation` / `HistoricalStrategySynthesis` | split: Interpreter owns `inference`/`limits`; Composer owns `navigation`/`heading` | Interpreter + Composer | Mixed record | round-trip tests |

### 7.2 Validators and admission

| Current | Disposition | Reason | Verification |
|---|---|---|---|
| `core/data/validators.py` IS/BS/CF checksums | Modeler | Arithmetic on standardized statements | `test_validators.py` |
| `core/ingestion/filing_validator.py` `bind_source_file`, `source_row_identity` | Extractor | SHA-256 / portable `source_file` / page | `python -m bav validate-source` |
| `filing_validator.validate_operating_kpi_fact` path | Modeler | Admission identity, not provenance | KPI fact tests |
| `historical_operating_kpis` / `historical_segments` validators | Modeler | Fail-closed identity / bridge | matching tests |
| `management_kpi.py` admit/bind/classify | Modeler | Content-aware admission of already-extracted KPI JSON | `test_management_kpi_admission.py` |
| `management_kpi_identity.py`, `management_kpi_reconciliation.py`, `management_kpi_history.py` | Modeler | Identity, conflict, history derivation | matching tests |
| `operating_kpi.py` / `geographic_segment.py` selection | Modeler | Restated-vs-prior / Q4-2023 identity | fact tests |
| `normalization_candidate_admission.py` | Modeler (provisional) + Interpreter (human treatments); not default reconcile | Opt-in; human judgments are not facts | `test_normalization_candidate_admission.py` |
| `share_basis.py` | Modeler | Restatement-factor resolution | `test_share_basis.py` |

### 7.3 Ingestion I/O

| Current | Disposition | Reason | Verification |
|---|---|---|---|
| `filing_json.py` `load_extracted_filing` | Director/Modeler loader of Extractor output | Parses extracted JSON; does not open PDFs | `test_filing_json.py` |
| `filing_cli.py` | Director | Workflow over extracted dir | `test_filing_cli.py` |
| `filing_reconciler.py` `reconcile_filings` | Modeler | Cross-filing selection | `test_filing_reconciler.py` |
| `reconciliation_provenance_payload` | Extractor (`source_file`, `source_sha256`, `pdf_page`) + Modeler (`selection_rule`, rank) | Split raw vs analytical provenance | committed `provenance.json` |
| `filing_standardizer.py` | Modeler | Emit model-only `StandardizedFinancials` | Lulu/FR reconcile |
| `note_handoff.py` | Director staging helper | Appends already-authored note facts | prepare script |
| `excel_import.py`, `manual_hk.py` | Legacy | Transcribed Excel/JSON adapters | ingest / demo tests |
| `future_adapters.py` `HKEXAdapter`, `SECAdapter`, `SGXAdapter` | Remove | `NotImplementedError`; TARGET forbids HKEX scrape; no production import | `rg` definition + `README-HK-TRAINER.md` mention only |
| `base.py` / `reconciler.py` | Modeler | Shared checksum reconcile | build refuse-on-fail |
| `management_kpi_enrichment.py` `inspect_source_pdf`, `enrich_management_working_copies` | Legacy binder; **not** Extractor product | Opens PDFs to bind pages / optional traced SPSF; refuses to write protected `extracted/`; company build does not call enrich | `test_management_kpi_enrichment.py` |

Raw source provenance belongs to Extractor. Analytical transformations and
calculation provenance belong to Modeler.

---

## 8. Figures versus relationships versus presentation

| Surface | Valid numerical series (Modeler) | Economically meaningful relationship (Interpreter) | Publication form (Composer) |
|---|---|---|---|
| `drivers.py` plotters | bar heights from assembled series | not decided in plotters | titles, labels, 53-week annotation, source notes, `style.series_color` |
| `style.py` | none | none | fonts, grayscale, spacing, `savefig` |
| `document.py` | none (reads Markdown/PNG) | none | Word/PDF layout, captions |
| `publish.py` | none | none | apply-if-applicable, verify headings/figures |
| `figure_ids` | — | Interpreter may ask a figure question | Composer decides whether a PNG is emitted |

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

**Rule that treats emphasis as more than attributed evidence (remove this promotion; keep evidence)**

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
| `core/engine/build_contract.py` `BUILD_MODULES` | `director/build_contract.py` policy + Modeler prepare/writers | Director + Modeler | `forecast` is `deferred` | `test_build_contract.py` |
| `component_catalog.py`, `semantic_map.py`, `map_embed.py` | `modeler/` | Modeler | Semantic families / coordinates | `test_reference_integrity.py` |
| `reference_model.py` `ReferenceModelBuilder.build` | `modeler/workbook.py` | Modeler | Workbook construction | Lulu/FR benchmarks |
| `include_deferred_forecast` / `run_scenario` | stay gated default off | Modeler (dormant) | Do not activate | `test_historical_v1_exit_gate.py` |
| `reference_model` lazy imports of `trainer.check_context` | `modeler/check_context.py` | Modeler | Live formulas and source-payload embed are BAV machinery | live-formula tests |
| `core/trainer/workbook.py` `build_bav_workbook` | `modeler/build_bav.py` | Modeler | “professional BAV. Does not derive a Trainer.” Mis-housed | `test_current_build.py` |
| `TrainingWorkbookGenerator.finalize_bav` / `_add_bav_opening` | Modeler finalize + Composer Overview | Modeler + Composer | Opening is publication inside the workbook | `verify_staged` Overview |
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

## 12. Extractor boundary (documentation only)

No production source-faithful statement extractor exists. The engine consumes
already-extracted JSON (`load_extracted_filing` → `extracted/` +
`reconciled/standardized.json`). Closest PDF-touching code is
`inspect_source_pdf` / `enrich_management_working_copies`, which bind pages on
working-copy KPI JSON and refuse to write protected `extracted/`. That is not
a reason to build Extractor.

**This migration specifies a documentation-only boundary. Do not implement
extraction, scrapers, or `future_adapters`.**

Create later (not this step):

```
extractor/README.md
  BAV consumes ExtractedFiling JSON and bound source PDFs.
  This repository does not extract statements from PDF.
  Upstream LLM/human extraction is permitted; the published contract is
  filing.py. Do not add scrapers here.
```

Optional later move: `filing.py` types into `extractor/data/` as the published
contract. Loaders stay Director/Modeler consumers.

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

1. Create visible roots `director/`, `extractor/`, `modeler/`, `interpreter/`, `composer/`; keep `legacy/`. Add documentation-only `extractor/README.md`.
2. Move `STYLE.md` and `DRIVER.md` to `director/docs/` and apply §11 reference updates, including README identity if that step touches README. Protected planning docs stay.
3. Split `drivers.py` / `selection.py` in place (or during the move) per §5: assembly without `select_driver_argument`; Interpreter gates; Composer roles/render/plots. Apply the management-emphasis removal in §9. Deduplicate reconstruction helpers.
4. Move Modeler calculation modules, data payload, ingestion reconcile/standardize, engine workbook, `build_bav_workbook`, semantic I/O, check-context embed.
5. Move Interpreter judgment functions and classification/normalization rationales / strategy inference.
6. Move Composer `style.py`, `document.py`, `publish.py`, Drivers prose/plots, Overview navigation.
7. Move Director CLI / `current_build` / `project_companies.json` / build-contract policy. Keep `python -m bav` and company name interfaces.
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
- `core/tests/test_reported_margin.py`, `test_revenue_driver.py`
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

## 16. Unresolved issues (not disguised as completed classification)

1. **`_latest_index` vs `_latest_growth_index`.** Selection uses the last period; prose/plots use the last period with non-None `revenue_growth`. Same view can qualify and narrate different years if trailing growth is missing. Split keeps both; later repair is not this design.
2. **`_margin_is_material` is a non-zero test.** Named as materiality; classified here as Modeler eligibility. Interpreter economic materiality is not separately implemented.
3. **Attribution without a margin question** (`select_driver_argument` L1179–1186) records `action=attribution.publication` but does not add the id to principal/secondary/appendix. `_attribution_block` still prints if `view.attributions` is set.
4. **Disclosure-gated reconstructions.** No `historical_strategy` disclosures ⇒ footprint/geo reconstruction series are None, while store/geo levels still assemble. Optional revenue-driver module vs “emphasis gates audit series” is unresolved. It is not currently a principal-driver gate.
5. **`overlap` and `main_body_table_reason(s)` unused.** Combining footprint+compsales and margin+attribution is hard-coded.
6. **`DriversView.margin_explanation` always `""`.** Dead field; do not invent a replacement.
7. **`relationship_findings` / `assessments` do not affect `select_driver_argument`.** Appendix-only. No new schema.
8. **`validate_standardized` unused.** Keep as Director contract pending out-of-tree confirmation.
9. **`cmd_build -o` still derives a Trainer** while company builds do not. Compatibility vs single-output is a Director CLI decision.
10. **`_append_traced_spsf_occurrences`** can write KPI rows from PDF regexes into working copies. Off the canonical `extracted/` / `build` path. Legacy binder, not a reason to build Extractor.
11. **Overview synthesis lives in `trainer/workbook.py`.** After Trainer inversion, Composer vs Modeler for `_add_bav_opening` layout vs Interpreter lead text follows §7.1.
12. **Three “validator” layers** (`schema.validate_standardized`, `data.validators`, `filing_validator`) share a name and have different owners (Director / Modeler / Extractor+Modeler).
13. **Source PDFs are absent locally and not tracked at B.** Canonical destination is `build/input/<company>/source/`. `source_manifest.json` still cites `benchmark/fast_retailing/source/`. Restore-and-bind is later work; do not invent PDFs.
14. **`README.md` “BAV — Hong Kong Edition”** is asserted by `test_learner_ready_presentation.py`. Product-face rename must update that test together.
15. **`latest-implementation` leftover** from `bav_trainer` is not an ambiguity of product ownership; it is ignored because `IMPLEMENT_BASE_SHA` is populated.

These items do not block beginning migration. They must not be treated as
finished classification where they remain open.
