# Legacy — retained prior functionality

This tree holds useful prior functionality outside the active BAV Compiler
architecture. Ordinary company `python -m bav {build,check,publish}` and
canonical filing validate/reconcile do not import this package.

Retained compatibility entry points used by public behavior:

- `legacy/ingestion/` — transcribed HK JSON and Excel/Bloomberg/Wind adapters,
  still reachable through `core.ingestion.manual_hk` / `core.ingestion.excel_import`
  and the `ingest` / explicit Excel-input `-o` build commands.
- `legacy/trainer/` — optional Trainer derive, blanking, scoring and chrome,
  still reachable through `core.trainer` façades and explicit `--workbook` check
  or JSON `-o` derive.

Those compatibility modules are not the active company execution path.

## Step 10.13 destinations

| Category | Current location | Retained entry points |
|---|---|---|
| Coverage automation | `legacy/automation/` | `legacy/automation/sentinel.py`, `bav_headless.py`, `install.sh` (do not install from ordinary BAV work) |
| Controller patches | `legacy/autocycle-fixes/` | Isolated tests vs installed AutoCycle; patches are historical assets and are not applied here |
| Skills and fixtures | `legacy/skills/` | Not imported by `python -m bav` |
| Plugin metadata | `legacy/plugin/plugin.json` | Input to `legacy/build_plugin_zip.sh` |
| Plugin archive | `legacy/bav-pipeline-plugin.zip` | Retained existing archive; packaged members stay `.claude-plugin/`, `skills/`, `README.md` |
| Plugin packager | `legacy/build_plugin_zip.sh` | Optional output path; default `legacy/bav-pipeline-plugin.zip` |
| Retired release / audit / PDF-cache scripts | `legacy/scripts/` | `python legacy/scripts/{build_lululemon_release,build_fast_retailing_release,audit_fast_retailing_benchmark,audit_reference_workbook,extract_benchmark_pdf_text}.py` |
| Benchmark PDF helper deps | `legacy/scripts/requirements-benchmark.txt` | Alongside `extract_benchmark_pdf_text.py` |
| Historical verifiers and SHA-bound Excel refs | `legacy/verification/` | `legacy/verification/verify_cached_workbook.py`, `verify_lululemon_overview_presentation.py`, `native-excel-*.json` |
| Trainer guide, GOOGL reference, diagnosis / resume notes, superpowers specs | `legacy/docs/` | `legacy/docs/README-HK-TRAINER.md`, `legacy/docs/GOOGL_HISTORICAL_REFERENCE.md`, `legacy/docs/superpowers/specs/` |
| HK / GOOGL example assets | `legacy/example/` | `DEMO_HK_*.json`, `DEMO_HK_Trainer.xlsx`, `DEMO_HK_Answer_Key.xlsx`, `GOOGL_Demo_Integrated_Financials.xlsx` |

Historical RESULT records keep the commands that were run at the time. Current
instructions use the destinations above.

`scripts/build_fast_retailing_source_facts.py` remains at its old path as a
later Remove item. Canonical `build/input/`, `build/output/` and leftover
gitignored `example/` sidecars stay where they are.

## Original custom-GPT system (Gemini Gems)

Before this repository was a Claude Code skill, it was four instruction sets run by hand as **Gemini Gems** — the custom-GPT pattern, anchored on Google's ecosystem:

- **Gemini Gems** held the personas (paste an instruction file into a Gem — or an OpenAI custom GPT — and it becomes that specialist);
- **NotebookLM** provided grounding: upload the 10-Ks, analyst reports, and transcripts, and the Strategist's report cites real filings instead of model memory;
- **Google Sheets + Apps Script** was the modeling surface: the Analyst and Modeler Gems emit `.gs` scripts that build the workbook tabs programmatically, formula-linked end to end.

## The files

| File | Role |
|---|---|
| `1. The Strategist Gem Instructions.md` | Strategy report with quantified factors and the Bull/Base/Bear scenario framework — the model's input, never its output |
| `2. The Assembler Gem Instructions.md` | 10-K filings → clean IS/BS/CF tabs: superset schema, restatement priority (newest filing wins), sign conventions, checksums |
| `3. The Analyst Gem Instructions.md` | Generates the Apps Script that builds Condensed Financials (operating vs. financial classification) and ALT DuPont — no hardcoded values, every cell traces to a source tab |
| `4. The Modeler (Multi Scenario) Gem Instructions.md` | Three-scenario residual income model: customizes only `getScenarioConfigs()` in the reference script; writes differentiated Professor's Notes |
| `4Alt. The Modeler Gem Instructions.md` | Single-scenario variant of the Modeler |
| `Sample AppScript for Condensed and Dupont*.txt` | Reference Apps Script implementations for the Analyst's output |

The authoritative reference `.gs` scripts the Modeler customizes (`Reference_Parameterized_Model.gs`, `MultiScenario_Parameterized_Model.gs`) live in `skills/bav-pipeline/references/` — they remain the definition of the Google Sheets model-tab layout. This coverage pipeline is Legacy; ordinary BAV company execution does not use it.

## The manual workflow

1. Ground NotebookLM with the company's filings; run **Strategist** → strategy report.
2. Give **Assembler** the 10-K PDFs → paste its output structure into Sheets (or run its build steps).
3. Run **Analyst** → paste the generated Apps Script into Extensions → Apps Script → run → Condensed + DuPont tabs appear.
4. Give **Modeler** the strategy report + workbook → it returns `getScenarioConfigs()` → paste into the reference script → run → three model tabs + scenario summary.

Each handoff is manual; each output is a one-shot artifact. The Claude Code skill
in `legacy/skills/` automated that workflow historically. See the root
[README](../README.md) for the current BAV Compiler architecture.
