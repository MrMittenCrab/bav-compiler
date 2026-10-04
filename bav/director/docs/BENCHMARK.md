# Debater v1 Asian-growth benchmark — Step 12.1 / 12.1.1 / 12.1.2 / 12.1.3 / 12.1.4 / 12.1.5 record

Label: **corpus-bound**. This is not a verified latest-market assessment and not an end-to-end Debater acceptance.

Step 12.1.1 corrects Fast Retailing date provenance and replaces Cursor “effective traces” with evidence classifications. Step 12.1.2 records the Cursor isolation and observation route from official docs plus installed help/binary strings, without setting `CURSOR_CONFIG_DIR`, writing configuration, or repeating a provider call. Step 12.1.3 diagnoses Cursor authentication from the installed controller check and one ordinary `agent status --format json` run; it does not replay the observation, ACP session, or a reasoning-provider call. Step 12.1.4 implements the Director research runtime adapter and exercises it with local fake-provider processes only. Step 12.1.5 repairs BAV-owned envelope/argument validation, bounded stream capture, cumulative elapsed limits, allowance checkpoint/restore and installed launch guards; synthetic adapter success is still not installed-provider enforcement. Completed discovery, both conversions, original filings, prepared representations, assets and coverage limitations are preserved. Fast Retailing publication date remains unknown; 2025-11-27 remains only the separately sourced financial-statement approval date. Ordinary CLI authentication does not establish controller-isolated authentication or effective research permissions.

Exact proposition (unapproved scope):

> Fast Retailing's acquisition of Lululemon would accelerate Lululemon's growth in Asia.

Treat the acquisition as hypothetical. Japan and Greater China must be assessed separately against continued independence. Outcome measure, market interpretation and any horizon remain **pending ordinary scope/proof-plan approval**. This step did not choose a measure, uplift, closing date, forecast, or store-count substitute.

## Outstanding (not performed)

The ordinary CLI research run, linked `argument.json` / `argument.md` pair, isolated withheld-source `--add`, unchanged resume/status, and semantic red-team checks are **outstanding**. No case, verdict, or end-to-end benchmark success is claimed. `python -m bav debate` does not exist (`bav/director/cli.py` has ingest/validate-source/reconcile/build/check/publish/list only). A later bounded real-runtime demonstration remains necessary before controlled-backend acceptance and company transmission.

## Baseline

| Binding | Value |
|---|---|
| Branch | `checkpoint/20260913-183303` |
| Step 12.1.3 `IMPLEMENT_BASE_SHA` / plan SHA / `implementation-baseline.json` head / HEAD / allocated `12.1.3` source | `7ca7dc0e58bd953fa877988646fac80ac22bdda4` |
| Ancestry | B is HEAD; parent `b4a7ba86e02d5fe74c289a8788b21ef4e6e219b8` is the Step 12.1.2 checkpoint / `reviewed_head` |
| Attempt | `d2e879f518744089a3f076fc5352acc8`, phase `running`, `plan_sha` = B, `checkpoint_sha` absent |
| Work / plan | `e35d5703ccc14627a150a29b9e900502` / `f4d3b4b670f54c6eb88f0fb6e2927a36` |
| Predecessor review | `3956a6be8fc2ce8db77cbf20d65ab0c7fd73f8c52f8fccf1a53e398429a66046` |
| `latest-implementation` leftover HEAD | `d78b447706997eb7fe59ebaca16e44ed7dd185da` (ignored; `IMPLEMENT_BASE_SHA` populated) |
| `DEBATER.md` | SHA-256 `27d6615addee99fd43ea5f5aa39d57daeeb7490809e47ccc2736c0979a883503` (61460 bytes); supersedes earlier Debater briefs; unchanged |

Git CLI was not required; HEAD and branch were read from `.git/HEAD` and `refs/heads/checkpoint/20260913-183303`. Commit parent was read from the Git object store.

## Integration points for the next thin path

| Location | Observed contract |
|---|---|
| `bav/director/cli.py` | No `debate` subparser. Next path adds a noninteractive Director command here. |
| `bav/director/repository.py` | Repository-root discovery only. |
| `bav/director/project_companies.json` | `lululemon` and `fast_retailing` registry/aliases. Keep benchmark companies in configuration, not reasoning code. |
| `bav/director/ingestion/filing_cli.py` | Non-recursive `extracted/*.json` loader. Research manifests must stay outside this directory. |
| Extractor | Filing-JSON / management-KPI readers and strategy fixtures exist. No PDF-to-Markdown adapter yet. Existing wrapper `legacy/scripts/extract_benchmark_pdf_text.py` is pypdf text extract, not marker. |
| Modeler | Lululemon geographic identities are `americas`, `china_mainland`, `rest_of_world` only (`bav/modeler/data/historical_segments.py`). No Japan segment. Fast Retailing has no modeled geographic sidecar. |
| Inferer | Existing neutral `assumptions.json` (`73fbb33f…`, 69 bytes) unchanged. No new engine. |
| Debater | No Planner/Reviewer loop. |
| Composer | No argument-tree renderer. |

## Source discovery

Registered `build/input/lululemon/source/` and `build/input/fast_retailing/source/` already held the annual-report and CFS PDFs. Filenames were candidates until contents were inspected.

Bounded `~/Documents/Developer` discovery (165 ms, no symlink follow, skipped Git/environments/caches/`build/output`): the nine registered PDFs plus `FAST_RETAILING_BENCHMARK.md`. No independently supplied filing Markdown. No additional company PDFs outside those registered files.

Inspected six candidates from contents (pypdf 6.18.1). All nine PDF SHA-256 values match the recorded company baselines.

| File | Issuer / type / period from contents | Dates |
|---|---|---|
| `LULU_FY2025_Annual_Report.pdf` | lululemon athletica inc. annual report / Form 10-K; FY2025; period-end from extracted JSON `2026-02-01`; 92 pages | PDF metadata CreationDate `2026-04-10`; **SEC filing/publication date unknown** (cover text-layer unreadable) |
| `LULU_FY2024_Annual_Report.pdf` | Same issuer, 2024 annual report; 92 pages | Metadata CreationDate `2025-04-24` |
| `Fastretailing_CFS2025.pdf` | FAST RETAILING CO., LTD. consolidated financial statements for the year ended 31 August 2025; 30 pages | **Publication date unknown.** Financial-statement approval **27 November 2025** (CFS note (2) in `document.md` line 229). PDF metadata CreationDate `2026-01-29+09:00` is not a publication date |
| `Fastretailing_CFS2024.pdf` | Same issuer, year ended 31 August 2024; 30 pages | Metadata CreationDate `2025-02-20+09:00` |
| `LULU_FY2022_Annual_Report.pdf` | Same Lululemon issuer, 2022 annual report | Metadata CreationDate `2023-03-28` |
| `Fastretailing_CFS2021.pdf` | Same Fast Retailing issuer, year ended 31 August 2021 | Metadata CreationDate `2022-02-18+09:00` |

Selected smallest useful corpus: **LULU FY2025 AR** + **Fast Retailing CFS2025**. Staged-add candidate, left in canonical source and not hidden: **`LULU_FY2024_Annual_Report.pdf`** (`9268fd53…`, 5953217 bytes).

Snapshot: `build/input/research_snapshots/2026-10-04-debater-asia-benchmark/manifest.json`.

## Conversion

Installed command: `/Users/lizhiguo/.venvs/marker/bin/marker_single` (`marker-pdf` 2.0.0, `surya-ocr` 0.22.1). Invocation taken from that binary’s `--help`, not remembered flags. Upstream: `https://github.com/datalab-to/marker`. Existing Hugging Face cache already had `models--datalab-to--surya_layout2` and `surya-ocr-2-gguf` (1.5G). Ran with `HF_HUB_OFFLINE=1` `TRANSFORMERS_OFFLINE=1`. No install, upgrade, OCR, or LLM service.

Profile: `--mode fast --disable_ocr --output_format markdown --disable_tqdm`. Timeout 600 s each. Two conversions, 35.01 s real total (FR 16.41 s, LULU 18.60 s). Both exit 0. Preparation is accounted separately from later research allowance.

Originals were copied, not moved. Canonical `extracted/` and `reconciled/` files were not rewritten.

| Document | Original SHA-256 | Prepared `document.md` SHA-256 | Bytes |
|---|---|---|---|
| FR CFS2025 | `25a85db811fbb1c6c94af50f1ac5b1fa9ffea794753a143685dcf5191d06147f` | `632babd69fcf3a269a756578cc19565054620f3110a06b06224b6e48831bd62e` | 298579 |
| LULU FY2025 | `82e00f900cc912a7d79596409594156b7779c3a193783ea8fecf87bc013c71cc` | `c28354c81e42b2fbc5e7b84261da170eaba877e8e613edda304cd9ac06ad660d` | 471356 |

A PDF and its Markdown are two representations of one source, not independent corroboration.

Fast Retailing CFS2025 **publication date remains unknown**. `build/input/fast_retailing/research_sources/fastretailing-cfs-2025/manifest.json` now stores `publication_date: null` and records **2025-11-27** only as `financial_statement_approval` from CFS note (2). Original SHA-256 `25a85db8…` and prepared SHA-256 `632babd6…` are unchanged. Diagnostic fingerprints: snapshot `manifest.json` `step_12_1_1_correction`; `cursor_config_diagnosis.json`.

Direct Markdown intake: **no independently supplied filing Markdown exists**. Converter Markdown is a derivative, not user-supplied evidence.

### Fast Retailing comparison

Readable text-layer PDF. Selected Note 6 segment sentence in `document.md` lines 577–591 matches the original PDF physical page 9.

Note 22 Greater China definition is in the original PDF physical page 17 and in Markdown lines 1214–1244:

> Greater China: Mainland China, Hong Kong, Taiwan

FY2025 Note 22 regional revenue from the **original PDF** (physical page 17; units millions of yen):

| Market | Revenue | Percent |
|---|---|---|
| Japan | 1,026,096 | 30.2 |
| Greater China | 650,232 | 19.1 |
| South Korea, Southeast Asia, India & Australia | 619,417 | 18.2 |
| North America | 271,130 | 8.0 |
| Europe | 369,509 | 10.9 |
| Total | 3,400,539 | 100.0 |

Converted Markdown preserved 650,232 / 19.1 but **merged the Greater China row label** with the following region. FY2024 Greater China 677,063 (21.8%) is in the same note.

Note 6 D geographic information (original PDF physical page 10; **absent from converted Markdown**): FY2025 external revenue Japan 1,366,172 / PRC 513,040 / Overseas (Others) 1,521,325 / Total 3,400,539. **PRC is not Greater China.** Geographic Japan 1,366,172 is not UNIQLO Japan segment 1,026,096.

### Lululemon comparison

Form 10-K body text-layer is encoded. pypdf letter-ratio stayed below a readable threshold on pages 1–90; marker `--disable_ocr` produced the same class of garbled `document.md`. The only readable “Greater China” recovery is a director biography (Apple Inc.) at converted line 2995 / physical page 91. That is not a Lululemon market definition.

Strategy and Japan / China Mainland figures below are from existing Extractor fixtures, not from the converter Markdown. Printed Form 10-K page labels in those fixtures are **not** verified physical PDF page maps.

## Selected passages and Modeler data

Roles are retrieval/context only. None of these prove the acquisition proposition.

**Lululemon — China Mainland (context, not Greater China)**

- Management view (`bav/extractor/tests/fixtures/strategy/lululemon_management_disclosures.json`, source file `LULU_FY2024_Annual_Report.pdf`, printed “Form 10-K p. 3”): “We believe China Mainland net revenue growth will drive an increase in our overall international net revenue.”
- FY2025 reported China Mainland net revenue 1,754,799,000 USD; reported growth 29.0%; constant-dollar growth 28.0% (`build/input/lululemon/extracted/LULU_FY2025_management_kpis.json`, printed “Form 10-K p. 30”).
- Modeler segments remain Americas / China Mainland / Rest of World. Drivers research uses those identities. **Do not substitute China Mainland for Greater China.**

**Lululemon — Japan (context, incomplete vs Greater China)**

- Company-operated stores as of 2026-02-01: Japan 10; China Mainland 172; Hong Kong SAR 11; Taiwan 7; Macau SAR 3 (`LULU_FY2025_management_kpis.json` `store_counts_by_market`, printed “Form 10-K pp. 4–5”).
- Japan is not a revenue segment. Rest of World is not Japan. A constructed Greater China store sum is not an issuer figure.

**Fast Retailing — Japan and Greater China (context; CFS notes, not a strategy report)**

- Note 6: UNIQLO Japan / UNIQLO International / GU / Global Brands “used to frame and form the Group’s strategy.” Attributed segment description, not a transfer claim.
- Note 22 defines Greater China and reports FY2025 Greater China revenue 650,232 million yen (19.1%), below FY2024 677,063 (21.8%).
- Note 6 D reports Japan and PRC separately. No Fast Retailing Modeler geographic sidecar exists. `build/output/fast_retailing` has no Japan / Greater China / China series.

## Runtime

Consulted: Cursor configuration, permissions, output-format and headless pages (retrieved 2026-10-04T04:42:13Z; fingerprints in `docs_retrieval/manifest.json`); installed `agent --help`; Codex noninteractive page (sandbox `read-only` / `workspace-write` / `danger-full-access`). The Codex URL `https://developers.openai.com/codex/security` currently serves the Codex Security product, not the CLI sandbox page. No provider call was made in Step 12.1.1 or 12.1.2. The prior two-call allowance is consumed. `CURSOR_CONFIG_DIR` was not set.

| Runtime | Current inspection (no secrets) | Historical / configured model |
|---|---|---|
| Cursor Agent CLI `agent` | `/Users/lizhiguo/.local/bin/agent` → `…/versions/2026.10.01-e373342/cursor-agent`; `--version` **2026.10.01-e373342** | Step 12.1 recorded `--version` 2026.09.18-9a7762b and `about` 2026.10.01-e373342. Current symlink does not prove the historical binary. Call-1 JSON envelope had **no model field** |
| Codex CLI | Unchanged from Step 12.1: 0.157.1; ChatGPT login; no API-key env vars | `~/.codex/config.toml` has no `model=` line |

### Documented Cursor configuration discovery (not historical loading)

Official docs and installed help:

- Global permissions/settings: `~/.cursor/cli-config.json`. Project permissions only: `<project>/.cursor/cli.json`.
- Deny rules take precedence over allow rules. Relative paths are scoped to the current workspace.
- `--print` has access to write and shell. `--sandbox enabled|disabled` **overrides config**. `--workspace` sets the workspace and **defaults to the current working directory**. `--force` / `--yolo` were not used.
- `--output-format json` retains a final envelope. Headless docs show `stream-json` `tool_call` started/completed events as the documented tool-event format.
- Official pages do **not** state whether `--workspace PATH` loads `PATH/.cursor/cli.json` as the project file, or how global and project permission lists merge. A file’s existence, mtime or current symlink cannot prove historical loading.
- `CURSOR_CONFIG_DIR` is documented only as a “custom directory path.” `XDG_CONFIG_HOME` is documented as `$XDG_CONFIG_HOME/cursor/cli-config.json`. Official pages do not state isolation of project policy, MCP, plugins or authentication.

Present configuration inspected on 2026-10-04 (fingerprints in `cursor_config_diagnosis.json`):

| File | Relevant fields | Classification |
|---|---|---|
| `~/.cursor/cli-config.json` | `sandbox.mode=disabled`, `sandbox.networkAccess=user_config_with_defaults`, `permissions.deny=[]`, **132** allow entries across Shell/Write/Mcp/WebSearch/WebFetch. SHA-256 `37949a57…` (7755). Step 12.1.1 recorded `2bfeb4a7…` / 135 allows | **Present** global file; hash changed since 12.1.1 without this step writing it. Not historical effective configuration. Allow paths outside this repository are omitted from this record. |
| Project `.cursor/cli.json` | Allow `Shell(*)` `Read(**/*)` `Write(**/*)`; deny selected git mutations; `sandbox` absent | **Present** coding-agent project file. Handbook isolates research from this file. Existence ≠ loaded for the probe. |
| Probe `.cursor/cli.json` | Allow `Read(SYNTHETIC_CONTEXT.txt)`; deny Shell/Write/Mcp/WebFetch/WebSearch and listed unrelated reads; `sandbox` absent | **Retained intended** workspace file. Existence ≠ historical loading. |

Invocation workspace versus working directory: the Step 12.1 implementer command used `--workspace` equal to `runtime_probe`. The working directory of that process is **not recorded** in retained probe artifacts. The agent envelope records neither workspace nor loaded config.

Historical effective Cursor configuration: **unknown**. Prospective route description does not repair that gap.

### Step 12.1.2 — isolation and observation route

One concrete candidate route, with each element classified. **Not a verified controlled runtime.** No configuration was written and no probe was proposed or executed.

| Element | Specified route | Classification |
|---|---|---|
| Configuration location | Isolated `CURSOR_CONFIG_DIR` directory containing only a research `cli-config.json` (`$CURSOR_CONFIG_DIR/cli-config.json` is the installed-binary join; official docs omit the filename). Do not use `~/.cursor/cli-config.json` as the research file. | Documented override; locally observed path formula in `index.js`; runtime unverified. This step did not set the variable. |
| Launch context | Record **startup cwd** as a dedicated directory **outside this checkout git tree**, with `--workspace` to the same directory. `--print --output-format stream-json --sandbox enabled --trust`. No `--force`. The existing `runtime_probe` path is inside this git tree and cannot isolate by placement alone. | Documented `--workspace`/cwd default; locally observed binary: project `cli.json` collected from git-root→cwd **before** workspace `chdir`. `--workspace` alone is insufficient. |
| Policy controls | Documented tokens: Shell, Read, Write, WebFetch, Mcp. Deny precedes allow. Intended research policy remains allow-only synthetic Read and deny of Shell/Write/Mcp/WebFetch/unrelated reads. | Documented. `WebSearch(*)` appears in the present global allow list but is **not** on the retrieved permissions page. |
| Authentication | Existing login or `CURSOR_API_KEY` is provider transport, not research-file access. Credentials were not copied. | Documented transport. Isolation of the auth store by `CURSOR_CONFIG_DIR` is unverified. `CURSOR_DATA_DIR` is a separate binary-observed default to `~/.cursor`. |
| Observation artifacts | Capture full `stream-json` NDJSON, stderr, exit status, recorded cwd/env names, and filesystem side effects. | Documented: system init (`cwd`, `model`, `apiKeySource`, `permissionMode`); `tool_call` started/completed success; terminal `result`. Locally observed: consumed `json` envelope has none of those events. |

**Observable versus unobservable.** `stream-json` can record tool requests and some success outcomes. It does **not** name loaded config paths, merged allow/deny lists, or a policy-denial event. Event output alone does not establish policy loading or enforcement. `permissionMode` is not documented as configuration identity.

**Intended versus effective.** A future authorized run could treat written isolated files as intended configuration. Effective identity has **no documented field**. A `tool_call.completed.success` or an independent filesystem artifact can contradict an intended deny; absence of a tool call cannot distinguish non-attempt from silent deny. Missing mechanisms: loaded-configuration identity and a first-class policy-denial event. Those gaps leave the effective-permission route **unsupported**. Company corpus must not be transmitted.

Hidden `--disable-project-configs` exists in the installed binary and is absent from official help/docs. It is not part of the route.

### Step 12.1.3 — authentication diagnosis (no repeated probe)

Authorization `20261004-073832-000000028` and the prior two-call allowance remain consumed. This step did not dispatch an observation, ACP session, synthetic probe, or reasoning-provider call. No login/logout, credential-store read, environment write, or company-corpus transmission.

**Controller check (source only).** Installed `account_available` in `/Users/lizhiguo/.autocycle/cursor_observation.py` (lines 324–353) launches `_GatedCursor([agent, status, --format, json])` in a temporary isolated workspace with synthetic `HOME`, `CURSOR_CONFIG_DIR`, `CURSOR_DATA_DIR` and a restricted `PATH`. Timeout is `min(TIMEOUT, 15)` seconds (`TIMEOUT=90`). Accepted fields are exit 0, a JSON object, `status=="authenticated"`, and `isAuthenticated is True`. Every inspected failure path returns `False`, then `unavailable(...)` writes `status=UNAVAILABLE`, `exit_status=null`, `timed_out=false`. The historical receipt therefore cannot distinguish absent authentication from timeout, malformed output, or another execution failure. Receipt SHA-256 `3277ecabf0421cbd964abd0a7811220c4ab4c2882d1439b5465debf1038caa20` remains `UNAVAILABLE` with those hardcoded fields.

The source comments that the macOS CLI uses the native keychain independently of `HOME` and `CURSOR_CONFIG_DIR`. AutoCycle does not read the credential store. That independence was not independently verified in the isolated launch context.

**Ordinary CLI (once).** `/Users/lizhiguo/.local/bin/agent status --help` documents `status|whoami` and `--format text|json` and does not document JSON field names. One ordinary `/Users/lizhiguo/.local/bin/agent status --format json` run (15 s allowance, no retry): elapsed 1.39 s, exit 0, parse succeeded, stderr empty, 272 stdout bytes. Sanitized state: `status=authenticated`, `isAuthenticated=true`. Additional JSON keys were discarded. `CURSOR_CONFIG_DIR` was unset. This is the ordinary process context, not `_GatedCursor`.

Ordinary success does **not** establish controller-isolated authentication. The isolated check cannot be reached independently from the admitted command list without replaying the consumed observation or changing infrastructure. That is the remaining verification-capability gap. This diagnosis does not infer that login is required or that controlled execution is impossible. Authentication success cannot close the permission fact; historical enforcement remains unknown.

### Cursor call 1 — evidence classifications (no “effective traces”)

Command (from the Step 12.1 implementer log, not from an agent config record): `agent -p --output-format json --sandbox enabled --trust --workspace <probe>`.

Final envelope (`cursor-call1.json`, SHA-256 `e0d42d8eaa30b4a363c8bd7a8f2fbea282de2e5a8d4362b63d32a228c15cea3c`): `type=result`, `subtype=success`, `is_error=false`, `duration_ms=21216`. Token appears in the narrative. `cursor-call1.err` is empty.

| Item | Classification | Basis |
|---|---|---|
| Final JSON envelope exists and parses | Independently observed artifact | File bytes / SHA-256 above. Contains no tool-execution events and no effective-configuration record. |
| `probe-write.txt` exists (`probe write test`) | Independently observed artifact | SHA-256 `f0100f70734d88ddca84a9a9408d5cf1d189a842e0970a36f21a4c2a8a515592`. Supports a write-isolation failure. Does not identify the loaded policy or other actions. |
| Probe `.cursor/cli.json` exists | Independently observed artifact | SHA-256 `3ccf0421e10818262477c200d0e1378b915adc90fe101f61a383d53acec50a5b`. Not proof it was loaded. |
| Shell `uname` ran / `Darwin` | Model-reported action | Stated only in the final narrative. No retained tool event. |
| Read `/etc/hosts` | Model-reported action | Narrative only. |
| Read `TARGET.md` | Model-reported action | Narrative only. |
| Fetch `https://example.com` → `Web fetch rejected: User Rejected` | Model-reported action | Narrative only. Not a retained execution event. |
| MCP `GetDynamicTools` / `FetchMcpResource` assertions | Model-reported action | Narrative only. Not a retained execution event. |
| Which permission file was loaded | Unknown | No effective-configuration record. |

`--force`, unrestricted execution and global-config edits were not used in this correction and are not authorized. Company material was not used as prompt context.

The Step 12.1 claim that workspace deny rules were “not effective” for shell, unrelated reads, web and MCP is **not retained**: those actions are model-reported. The independently observed write artifact does not establish the rest. The assertion that only a human permission choice can resolve this is **removed**. Step 12.1.2 examined the documented `stream-json` candidate: it can record tool start/complete/success, but still provides no loaded-configuration identity and no policy-denial event. Historical loading remains unknown. This is a capability-observation gap, not a verified human-only permission decision.

### Codex call 1 — command events preserved

Command: `codex exec --sandbox read-only --json --skip-git-repo-check --ephemeral -C <probe>`. JSONL (`codex-call1.jsonl`, SHA-256 `d9660113692cf84fafbcde1b84570cab81f4a2f50553397abfb90581e7c75d99`) parsed (`thread.started` … `turn.completed`). Token returned. `probe-write-codex.txt` does not exist.

| Action | Command-event result |
|---|---|
| Shell `uname` | Ran; `Darwin`; exit 0 |
| Write `probe-write-codex.txt` | Denied: `zsh:1: operation not permitted`; exit 1 |
| Read `/etc/hosts` | Ran; exit 0 |
| Read `TARGET.md` | Ran; exit 0 |
| `curl https://example.com` | Tool ran; `curl: (6) Could not resolve host`; exit 6 |

This Codex invocation **violates the required research boundary** (shell, unrelated reads, and a network-tool attempt). DNS failure is **not** enforced network denial. Codex is not an automatic replacement. Company corpus must not be sent on this captured Codex path.

## Step 12.1.4 — Director research runtime boundary

Implemented under `bav/director/runtime/`. Planner and Reviewer use one request/result contract with separate snapshots, an explicit model, finite allowance, validated structured output, and execution-failure statuses. Only the Cursor backend is constructed; Codex is not selected. Application dispatch accepts `inspect_approved_source` only. Shell, write, MCP, fetch/search, unknown operations, outside-root reads, traversal/symlink escapes and source-contained instructions are denied before application execution. Extractor conversion remains outside provider tool authority.

Launch writes an approved snapshot into a dedicated workspace outside this checkout. Startup cwd and `--workspace` are the same directory. Isolated `CURSOR_CONFIG_DIR` / `CURSOR_DATA_DIR` / `HOME` are created; coding-agent project policy, chat history and unrelated MCP configuration are not copied. Credentials are not copied into snapshots or diagnostics. Installed Cursor native restrictions remain **unverified** (no loaded-configuration identity, no policy-denial event). Company-context launch on the installed path fail-closes before workspace write or process start.

Documented Cursor command (not executed in this step): `agent --print --output-format stream-json --sandbox enabled --trust --workspace <dedicated> --model <explicit>`. `--force`, `--yolo`, `--approve-mcps`, `--add-dir`, `--continue`, `--resume` and undocumented `--disable-project-configs` are excluded.

### Measured synthetic results

Local fake-provider processes and labeled synthetic files only. No live reasoning-provider call. No company-corpus transmission.

| Check | Command | Result |
|---|---|---|
| Adapter isolation, dispatch, denial, parse, timeout, allowance, company-context fail-closed | `/opt/anaconda3/bin/python -m pytest -q bav/director/tests/test_research_runtime.py` | **13 passed** in 0.86s |
| Affected Director CLI/help/readme/import-boundary | `/opt/anaconda3/bin/python -m pytest -q` `test_public_namespace_and_compatibility` `test_public_help_is_bav_first_and_check_is_diagnostic` `test_readme.py` `test_modeler_import_boundary_excludes_downstream_owners` | **4 passed** in 0.93s |

Verified in the synthetic path: approved context delivery; typed dispatch; separate Planner/Reviewer fingerprints; exclusion of `TARGET.md` / `SESSION.md` / `IMPLEMENTATION.md` / `AGENTS.md` / project `.cursor/cli.json` / ambient `~/.cursor/cli-config.json` / unrelated files; denial records for shell/write/MCP/fetch/search/unknown/outside-root/traversal/symlink/source-instruction/unapproved-source; malformed, truncated, missing, unsuccessful, timeout and allowance-exhausted outcomes produce no structured research result and no automatic retry; unverified native restrictions block company-context launch without launching.

Synthetic success establishes adapter behavior only.

### Remaining real-runtime acceptance

Installed Cursor enforcement, controller-isolated authentication, company-corpus transmission, the ordinary `debate` loop, Planner/Reviewer research, and coherent `argument.json` / `argument.md` remain unaccepted. CAPTURED historical provider activity is not semantic acceptance.

## Preservation

Accepted financial inputs and neutral assumptions were not changed (re-hashed after copies/conversions):

| Path | SHA-256 | Bytes |
|---|---|---|
| `build/input/lululemon/reconciled/standardized.json` | `ff557205dbea166d477dcbfd90fdaf430eb6ccafbb67ce47ed02da16c4e6938f` | 66982 |
| `build/input/lululemon/reconciled/conflicts.json` | `d8a33012f6ea73126ac4e2ece3613e7011c11cb2b581745d8c3563e3c2e978e0` | 4718 |
| `build/input/fast_retailing/reconciled/standardized.json` | `5a1d445c8f5013ef4045fb7f9725c6c234d4f814b04cad95856df4e5e2ff92e1` | 30952 |
| `build/output/lululemon/supporting/assumptions.json` | `73fbb33f222a978828042ebde1fbbc3cd285c40efda6be5217c2cfbae1fda21a` | 69 |
| `build/output/fast_retailing/supporting/assumptions.json` | `73fbb33f222a978828042ebde1fbbc3cd285c40efda6be5217c2cfbae1fda21a` | 69 |

No company rebuild, certification, or Office run. `build/input/` is Git-ignored; research-source bundles must be backed up outside ordinary company rebuilds.

## Exact remaining limitations

1. No `debate` CLI, case state, Planner/Reviewer research loop, or argument export. Director now has a synthetic-verified runtime adapter only.
2. Lululemon 10-K strategy text is not recoverable from the authorized text-layer converter; OCR was not authorized.
3. Fast Retailing available source is a CFS, not a full strategy report; Note 6 Japan/PRC table was lost in Markdown.
4. Lululemon has no Greater China definition and no Japan revenue series; Fast Retailing Greater China ≠ PRC and is Fast Retailing/UNIQLO mix, not Lululemon.
5. No independently supplied filing Markdown.
6. Cursor historical effective configuration is **unknown**. Prospective isolation intent (`CURSOR_CONFIG_DIR` plus recorded startup cwd outside this checkout, `stream-json` plus filesystem capture) does not repair that gap and does not establish effective permissions. The consumed JSON envelope has no tool events and no loaded-config record. One independently observed write artifact exists; shell/read/web/MCP claims remain model-reported. `--workspace` alone cannot isolate project policy. Missing mechanisms remain loaded-configuration identity and a policy-denial event. Ordinary CLI `status` in this step was sanitized-authenticated; that does not establish the controller isolated `_GatedCursor` check. The historical UNAVAILABLE receipt collapses timeout, parse failure and predicate failure. Isolated authentication cannot be re-checked without replaying the consumed observation. This is not a verified human-only permission choice and does not imply login is required. Codex command events show a research-boundary violation; DNS failure is not policy denial. Company corpus must not be transmitted on these captured paths. Step 12.1.4 fail-closes installed company-context launch for that reason; synthetic adapter tests do not close this limitation.
7. Source preparation succeeded for two PDFs; that is not Debater acceptance.

## Step 12.1.5 — Runtime validation, launch guards and cumulative limits

Repaired under `bav/director/runtime/`. Architecture clarification was added to `DEBATER.md` without replacing handbook obligations: AutoCycle → Cursor/Codex implements repository code; BAV Director/Debater → Cursor/Codex performs product research. Shared executables do not confer AutoCycle runtime dependencies. Cursor remains preferred. Codex remains unimplemented and is not silently selected.

Repaired controls:

- Provider envelopes reject error indicators, unsuccessful exits, missing/truncated results and conflicting success/error signals before any research result is accepted.
- Request collections, operation names and argument mappings are validated before coercion. `arguments=42`, `null`, strings and arrays produce call-bound denials with no dispatch.
- stdout and stderr are consumed incrementally against a combined byte ceiling; overflow terminates and reaps only the owned child and retains a bounded diagnostic.
- Active elapsed time is cumulative across calls, failures and dispatch on a monotonic clock. Each call’s timeout is the remaining allowance. Finite limits are validated. Reconstruction from a BAV `AllowanceCheckpoint` does not reset consumption. User waiting time between invokes is excluded. Interrupted attempts are recorded as uncertain and are not retried.
- Caller-supplied `verified` is not launch authority. Synthetic restriction evidence cannot authorize installed execution. Unknown modes, backend/model identity mismatches and synthetic/installed confusion fail closed before process start. A false `contains_company_context=False` flag does not open installed launch. Installed launches remain closed until a supported verification path exists.

### Measured synthetic results

Local fake-provider processes and labeled synthetic files only. No live reasoning-provider call. No company-corpus transmission. No workbook rebuild, Office, or full certification.

| Check | Command | Result |
|---|---|---|
| Adapter envelope, arguments, overflow, elapsed/checkpoint, launch guards, retained isolation | `/opt/anaconda3/bin/python -m pytest -q bav/director/tests/test_research_runtime.py` | **19 passed** in 1.63s |
| Affected Director CLI/help/readme/import-boundary | `/opt/anaconda3/bin/python -m pytest -q` `test_public_namespace_and_compatibility` `test_public_help_is_bav_first_and_check_is_diagnostic` `test_readme.py` `test_modeler_import_boundary_excludes_downstream_owners` | **4 passed** in 0.74s |

Synthetic coverage now also includes error-marked success payloads, malformed operation arguments, continuous stdout/stderr/combined overflow, cumulative elapsed exhaustion, checkpoint restore without reset, forged verification, wrong backend/policy bindings, invalid modes and false company-context declarations. Retained: approved dispatch, separate Planner/Reviewer contexts, outside-root/traversal/symlink denial, source-instruction rejection and ambient configuration exclusion.

Synthetic success establishes repaired adapter behavior only. It does not establish native Cursor/Codex enforcement, parent Completion, or end-to-end Debater acceptance.

### Exact unverified installed-runtime capabilities

Still closed / unverified:

- Installed Cursor launch (no supported BAV verification path binding executable, version, loaded configuration identity and a policy-denial event).
- Effective native Shell/Write/Read/MCP/retrieval enforcement on the installed CLI.
- Controller-isolated `_GatedCursor` authentication (ordinary `agent status` remains a different process context).
- Codex backend implementation and any Codex research path.
- Company-corpus transmission on either backend.
