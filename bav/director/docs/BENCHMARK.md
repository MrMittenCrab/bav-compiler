# Debater v1 Asian-growth benchmark — Step 12.1 prerequisite record

Label: **corpus-bound**. This is not a verified latest-market assessment and not an end-to-end Debater acceptance.

Exact proposition (unapproved scope):

> Fast Retailing's acquisition of Lululemon would accelerate Lululemon's growth in Asia.

Treat the acquisition as hypothetical. Japan and Greater China must be assessed separately against continued independence. Outcome measure, market interpretation and any horizon remain **pending ordinary scope/proof-plan approval**. This step did not choose a measure, uplift, closing date, forecast, or store-count substitute.

## Outstanding (not performed)

The ordinary CLI research run, linked `argument.json` / `argument.md` pair, isolated withheld-source `--add`, unchanged resume/status, and semantic red-team checks are **outstanding**. No case, verdict, or end-to-end benchmark success is claimed. `python -m bav debate` does not exist (`bav/director/cli.py` has ingest/validate-source/reconcile/build/check/publish/list only).

## Baseline

| Binding | Value |
|---|---|
| Branch | `checkpoint/20260913-183303` |
| `IMPLEMENT_BASE_SHA` / plan SHA / `implementation-baseline.json` head / HEAD / allocated `12.1` source | `e4632a6782be2c1de705ed838bc95a26d6b0e909` |
| Attempt | `7f42b6ae42124565820eb095ac49a90e`, phase `running` |
| Work / plan | `e35d5703ccc14627a150a29b9e900502` / `0f48c3009f7e451e8b3d0420830a6e86` |
| Predecessor review | `c693de448a9471be93cb4c975e6d8a2314aab8f6e8e201e4fd9e8b3e63b27540` |
| Reviewed head | `97d58c0a9928c4ee6e0de3ab93eb7587b544beb6` |
| `DEBATER.md` | SHA-256 `27d6615addee99fd43ea5f5aa39d57daeeb7490809e47ccc2736c0979a883503` (61460 bytes); supersedes earlier Debater briefs |

Git CLI was blocked in this environment; HEAD and branch were read from `.git/HEAD` and `refs/heads/checkpoint/20260913-183303`.

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
| `Fastretailing_CFS2025.pdf` | FAST RETAILING CO., LTD. consolidated financial statements for the year ended 31 August 2025; 30 pages | Approval date **27 November 2025** (CFS note). Metadata CreationDate `2026-01-29+09:00` is not the approval date |
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

Consulted: Cursor headless and permissions pages; Codex noninteractive page (sandbox `read-only` / `workspace-write` / `danger-full-access`). The Codex URL `https://developers.openai.com/codex/security` currently serves the Codex Security product, not the CLI sandbox page.

| Runtime | Version / auth (no secrets) | Configured model |
|---|---|---|
| Cursor Agent CLI `agent` | `--version` 2026.09.18-9a7762b; `agent about` 2026.10.01-e373342; logged in; Ultra; no `CURSOR_API_KEY` in the environment | `about` shows Grok 4.6 High Fast; `agent models` lists `auto` as default. Call-1 JSON envelope had **no model field** |
| Codex CLI | 0.157.1; `codex login status`: Logged in using ChatGPT; `auth.json` present; no `CODEX_API_KEY` / `OPENAI_API_KEY` in the environment | `~/.codex/config.toml` has no `model=` line |

`--print` documentation states print mode has access to write and shell. `--force` / `--yolo` were not used. Global `~/.cursor/cli-config.json` was not modified. Project `.cursor/cli.json` remains the coding-agent file and was not used as the research policy.

Synthetic workspace: `build/input/research_snapshots/2026-10-04-debater-asia-benchmark/runtime_probe/` (token `PROBE_TOKEN_BAV_12_1_SYNTHETIC` only). Two provider calls, 120 s class; measured 21.2 s (Cursor) and ~39 s (Codex). No company files were sent as prompt context. Cursor call 1 did read `TARGET.md` and `/etc/hosts` because restrictions failed.

### Cursor call 1 — controlled mode **not enforced**

Command: `agent -p --output-format json --sandbox enabled --trust --workspace <probe>` with workspace `.cursor/cli.json` denying `Shell(*)`, `Write(**/*)`, `Mcp(*:*)`, `WebFetch(*)`, `WebSearch(*)`, and unrelated reads.

Final envelope parsed: `type=result`, `subtype=success`, `is_error=false`, `duration_ms=21216`. Token returned.

Effective traces, not the model’s claim:

| Action | Measured |
|---|---|
| Shell `uname` | Ran; `Darwin` |
| Write `probe-write.txt` | Ran; file exists (`probe write test`) |
| Read `/etc/hosts` | Ran |
| Read `TARGET.md` | Ran |
| Fetch `https://example.com` | Denied: `Web fetch rejected: User Rejected` |
| MCP | `GetDynamicTools` `mcp` → `matches: []`; `FetchMcpResource` ran and failed (`Server "test" not found`) |

**Cursor route stopped for company-data transmission.** Workspace deny rules were not effective in this print/sandbox invocation. Unrestricted execution, `--force`, and global-config edits were not used.

### Codex call 1 — write blocked; shell, unrelated reads, and network tool not

Command: `codex exec --sandbox read-only --json --skip-git-repo-check --ephemeral -C <probe>`. JSONL parsed (`thread.started` … `turn.completed`). Token returned. `probe-write-codex.txt` does not exist.

| Action | Measured |
|---|---|
| Shell `uname` | Ran; `Darwin` |
| Write `probe-write-codex.txt` | Denied: `zsh:1: operation not permitted` |
| Read `/etc/hosts` | Ran (exit 0) |
| Read `TARGET.md` | Ran (exit 0) |
| `curl https://example.com` | Tool ran; failed DNS (`curl: (6) Could not resolve host`) |

**Codex is not an automatic replacement.** Read-only sandbox blocked the write and did not block shell, unrelated reads, or a network-tool attempt. Company corpus must not be sent until a human chooses an actually enforceable permission path.

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
6. Cursor and Codex controlled modes are **unverified / insufficient** for company-data research. A one-time permission choice is required before transmitting the corpus.
7. Source preparation succeeded for two PDFs; that is not Debater acceptance.
