# Debater v1 Asian-growth benchmark — Step 12.1 / 12.1.1 / 12.1.2 prerequisite record

Label: **corpus-bound**. This is not a verified latest-market assessment and not an end-to-end Debater acceptance.

Step 12.1.1 corrects Fast Retailing date provenance and replaces Cursor “effective traces” with evidence classifications. Step 12.1.2 records the Cursor isolation and observation route from official docs plus installed help/binary strings, without setting `CURSOR_CONFIG_DIR`, writing configuration, or repeating a provider call. Completed discovery, both conversions, original filings, prepared representations, assets and coverage limitations are preserved. Fast Retailing publication date remains unknown; 2025-11-27 remains only the separately sourced financial-statement approval date.

Exact proposition (unapproved scope):

> Fast Retailing's acquisition of Lululemon would accelerate Lululemon's growth in Asia.

Treat the acquisition as hypothetical. Japan and Greater China must be assessed separately against continued independence. Outcome measure, market interpretation and any horizon remain **pending ordinary scope/proof-plan approval**. This step did not choose a measure, uplift, closing date, forecast, or store-count substitute.

## Outstanding (not performed)

The ordinary CLI research run, linked `argument.json` / `argument.md` pair, isolated withheld-source `--add`, unchanged resume/status, and semantic red-team checks are **outstanding**. No case, verdict, or end-to-end benchmark success is claimed. `python -m bav debate` does not exist (`bav/director/cli.py` has ingest/validate-source/reconcile/build/check/publish/list only).

## Baseline

| Binding | Value |
|---|---|
| Branch | `checkpoint/20260913-183303` |
| Step 12.1.2 `IMPLEMENT_BASE_SHA` / plan SHA / `implementation-baseline.json` head / HEAD / allocated `12.1.2` source | `d78b447706997eb7fe59ebaca16e44ed7dd185da` |
| Ancestry | B is HEAD; parent `ab16ca39042ee28c2981b854e043494d6b050a8e` is the Step 12.1.1 checkpoint / `reviewed_head` |
| Attempt | `9797ae0a14d34ccdbfbefe8c0cf5a218`, phase `running`, `plan_sha` = B, `checkpoint_sha` absent |
| Work / plan | `e35d5703ccc14627a150a29b9e900502` / `4c7098b778cd40889f51b9e5398b15b9` |
| Predecessor review | `12034e178bf88c94eddb8f24e944f9c97e35a383aab39b9570cf895cf193adc5` |
| `latest-implementation` leftover HEAD | `cdaeb1151cc1e7a60597ec7076d4fa6893b5ee4d` (ignored; `IMPLEMENT_BASE_SHA` populated) |
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

1. No `debate` CLI, case state, Planner/Reviewer, or argument export.
2. Lululemon 10-K strategy text is not recoverable from the authorized text-layer converter; OCR was not authorized.
3. Fast Retailing available source is a CFS, not a full strategy report; Note 6 Japan/PRC table was lost in Markdown.
4. Lululemon has no Greater China definition and no Japan revenue series; Fast Retailing Greater China ≠ PRC and is Fast Retailing/UNIQLO mix, not Lululemon.
5. No independently supplied filing Markdown.
6. Cursor historical effective configuration is **unknown**. Prospective isolation intent (`CURSOR_CONFIG_DIR` plus recorded startup cwd outside this checkout, `stream-json` plus filesystem capture) does not repair that gap and does not establish effective permissions. The consumed JSON envelope has no tool events and no loaded-config record. One independently observed write artifact exists; shell/read/web/MCP claims remain model-reported. `--workspace` alone cannot isolate project policy. Missing mechanisms remain loaded-configuration identity and a policy-denial event. This is not a verified human-only permission choice. Codex command events show a research-boundary violation; DNS failure is not policy denial. Company corpus must not be transmitted on these captured paths.
7. Source preparation succeeded for two PDFs; that is not Debater acceptance.
