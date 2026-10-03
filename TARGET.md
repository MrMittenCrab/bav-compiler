# TARGET.md

## Product target

Build **BAV Compiler**, a source-grounded Business Analysis and Valuation equity-research system, in repository/local root `bav-compiler`. Preserve the public Python package and CLI name `bav`. Do not rename the Git remote or unrelated infrastructure for branding.

The Excel workbook remains the core analytical and source-traceability product; canonical Markdown, figures and Word/PDF publications communicate validated analysis. The BAV workbook must not present itself as an answer key, exercise or Trainer. Its front page is a concise product and company-analysis summary.

The complete research system should enable an analyst to:

1. trace reported information into a research model;
2. understand three-statement relationships and accounting sign conventions;
3. make and defend material accounting, classification and normalization judgments;
4. construct and audit historical analytical schedules;
5. explain changes in profitability, capital intensity, financing, cash conversion and per-share economics;
6. convert historical analysis into explicit forecasts and valuation assumptions;
7. value the equity using BAV-consistent methods and appropriate cross-checks; and
8. communicate a concise, evidence-based investment conclusion.

Formula correctness is necessary but not sufficient. The product must support accounting judgment, economic interpretation, auditability, forecasting discipline, valuation and research communication.

Historical accounting analysis, normalization and reformulation, NOA, NOPAT, forecasting, valuation and investment interpretation remain long-term goals. A bounded Session need not complete every later stage.

Trainer is preserved where useful as Legacy functionality, not an active architectural component or the project identity. Existing optional `<Company>_BAV_Trainer.xlsx` derivation must not become a prerequisite for BAV build or publication. The retained training specifications below govern preserved behavior, not Trainer expansion.

## Debater v1 product direction

Implement the complete Session 12 handbook `bav-debater-asia-benchmark.md`, retained as the reconciled specification in `bav/director/docs/DEBATER.md`. It replaces `bav-debater-v1-revised.md`, `bav-debater-v1-implementation.md` and earlier Debater briefs. This is authorized feature development within the existing six components, not another architectural migration. Migration-only prohibitions below remain historical boundaries and do not prohibit this explicitly authorized feature.

A user submits a proposition through `python -m bav debate`. Debater develops one compact linked argument using the approved corpus, explicit assumptions, claim-attached research questions, supporting and challenging evidence, and a joint inference. It searches available evidence and supported Modeler outputs before requesting the most consequential missing material, accepts additions or availability notes, and resumes the same case. It may conclude that the examined record does not support the proposition.

Each assessed case produces `argument.json` and a deterministic `argument.md` from the same validated revision, including Incomplete and Unsupported outcomes. The Markdown begins with a short title and a fenced Unicode tree showing linked claims, their assessments, retained questions, answers or unresolved requests, and selected evidence references. Exact excerpts and usable numerical selections retain context, locators, definitions, lineage and limitations. Questions are evidence-layer organizers, not recursively nested claims. Up to two existing evidence selections may receive emphasis; this is not an acceptance quota.

The primary real benchmark preserves this exact submission:

> Fast Retailing's acquisition of Lululemon would accelerate Lululemon's growth in Asia.

Treat the acquisition as hypothetical. Assess Japan and Greater China separately, preserving issuer-specific market definitions and missing coverage. Neither China Mainland nor Rest of World substitutes for those focus markets, and focus-market findings do not establish every Asian market. Compare Lululemon's growth with realistic continued independence. Approve the outcome measure, market interpretation and any necessary horizon through the normal scope/proof-plan flow; do not invent uplift, closing dates or forecasts, replace growth with store count, weaken “would” to “might”, or require a favorable verdict. Acquisition valuation is not a necessary proof obligation for this growth-only proposition.

Develop the thin path through actual local sources and authorized runtime: inspect access first; prepare a small two-company corpus; execute the ordinary debate command; retrieve real strategy passages and relevant Modeler data; export the linked argument and decisive gaps; demonstrate `--add` and resumption; then run focused regressions. Keep benchmark-specific companies, manifests and examples in configuration or fixtures rather than reasoning code. The reference tree is an unresearched illustration, never company evidence or a mandatory five-branch template.

Extractor accepts supplied filing Markdown directly and prepares PDFs through the verified existing converter using a small application-controlled adapter. Preserve originals, assets, exact selected text, source identity and provenance. Reuse preparation by content and converter/profile hashes. Keep technical preparation failures distinct from searched-but-unanswered questions, and keep two representations of one filing distinct from independent corroboration. One-time bounded Developer-folder discovery does not authorize runtime scanning of other projects or personal directories.

Director owns noninteractive CLI routing, backend policy, approvals, durable state, budgets, dispatch and terminal formatting. Debater owns its schema and separate Planner/Reviewer contexts; Extractor owns preparation and retrieval; Modeler owns numerical selection and supported calculations; Inferer retains existing neutral assumptions; Composer supplies a pure Markdown renderer. No new top-level component, general reasoning framework, forecasting engine or report composer is authorized.

Prefer Cursor Agent CLI, with Codex CLI as an explicitly selected alternative behind one adapter contract. Verify installed behavior and enforce effective restrictions in a dedicated workspace before sending company material. Reasoning providers cannot execute arbitrary shell commands, write the project, use unrelated MCP tools or retrieve external material. Application-controlled conversion does not grant those powers. Do not silently change provider/model, install dependencies, create new billing or expand transmission permissions.

Persist one authoritative case state, serialized mutations, approval bindings, source/model snapshots, completed work and remaining allowances. Initial research limits are one active route, up to three candidate routes, four research batches, twelve backend calls, twenty tool dispatches and twenty minutes of active work; intake, retries and repairs count. Restart or provider switching does not reset them. Source preparation has separately recorded finite limits. Ask for at most two external evidence items at once, preferably one decisive gap.

Preserve all detailed CLI, approval, schema, safety, recovery, rendering, reader and acceptance requirements in the complete handbook. `--status` and `--list` are read-only and make no LLM calls; unchanged resume reuses saved work. Bare added filenames resolve only from Downloads; explicit paths retain ordinary meaning. Imported sources are untrusted data, never instructions or executable code. Missing evidence is not contradiction, user stipulation is not independent empirical proof, and schema validity does not certify semantic judgment.

Debater emits no `argument.txt`, analytical report prose, graphs, chart specifications, slides, Word or PDF publications. Source PDF reading and conversion remain in scope. Later Composer publication is separate. Existing company build/check/list/publish behavior, accepted financial inputs, neutral assumptions, company outputs and STYLE.md remain protected.

The real benchmark must document actual sources, converter behavior, provider/model, passage locators, Modeler provenance, commands, status and coherent export paths in `bav/director/docs/BENCHMARK.md`. Demonstrate a staged addition of a withheld real source in an isolated case, full available sources for the final result, unchanged resume without reconversion or paid reasoning, and a differently worded or negated fixture. Mock-only runs, intake-only responses and unavailable integrations do not establish end-to-end acceptance. Record verified portions and exact blockers while continuing independent authorized work.

## Active component architecture

BAV Compiler has exactly six active components: Director, Extractor, Modeler, Inferer, Debater and Composer. `bav/` is the canonical active Python package, with component implementation under `bav/director/`, `bav/extractor/`, `bav/modeler/`, `bav/inferer/`, `bav/debater/` and `bav/composer/`.

All active BAV implementation belongs to exactly one component. Every meaningful responsibility has exactly one disposition: Director, Extractor, Modeler, Inferer, Debater, Composer, Legacy, Remove or Runtime-tooling. Classification follows responsibility and decision type, not current filenames, directories, classes or subsystems. Split mixed files across their substantive owners.

Do not retain active `core`, `common`, `shared` or `interpreter` implementation layers, or parallel active implementations in top-level component folders. Minimal `bav` package initialization and public entry wiring delegate to their component owner; they do not form another component.

### Director

Director owns architecture, orchestration, component boundaries, global configuration and policy, high-level component contracts, lifecycle and routing. It owns STYLE.md and other system-wide design/style specifications.

Director defines policy and controls execution. It is not a miscellaneous bucket. Extraction, quantitative calculations, neutral assumption formation, motivated research and publication implementation belong to their substantive components.

Director-owned high-level documentation lives under `bav/director/docs/`, including STYLE.md and the retained Driver specification. Move architectural and policy Markdown there when safe and update references. Determine AutoCycle root-path requirements before moving controller-facing documents; TARGET.md, SESSION.md, IMPLEMENTATION.md and RESULT.md remain at their required protected/controller-facing locations.

### Extractor

Extractor answers “What did the company publish?” It owns source-faithful acquisition and structuring of company evidence: filings, earnings-call materials, source Markdown, reported facts and KPIs, management commentary, management guidance, definitions and source provenance.

Management guidance is evidence, not authority. Accounting interpretation, normalization, model calculations, assumption formation, thesis construction and research prose do not belong to Extractor. Debater v1 authorizes the narrow filing-preparation, existing-converter adapter and contextual retrieval extension specified above; it does not authorize a replacement extraction framework or automatic accounting reconstruction.

### Modeler

Modeler owns the complete quantitative company model, historical and prospective: accounting classification and normalization, historical financial reconstruction, schedules, ratios and analytical series, identities, reconciliations, bridges and residuals, regressions and deterministic tests, forecasts, scenario calculations, sensitivities, DCF, comparables, valuation, workbook generation and BAV Excel construction.

Modeler owns calculation provenance and validity checks, including transformation and output provenance, consistency and measurement-boundary checks, and mechanical support for numerical claims. Raw source provenance originates in Extractor.

Forecast calculations belong to Modeler. It receives explicit assumptions and calculates their consequences without deciding whether those assumptions are neutral, bullish, bearish or otherwise desirable. Debater v1 may reuse supported calculations and narrow necessary adapters; ownership of prospective calculations does not authorize a new forecasting or valuation engine.

### Inferer

Inferer owns neutral/base assumption formation, assumption plausibility and neutral uncertainty.

It may use Extractor evidence, historical Modeler outputs, current model state, historical persistence, mean reversion, known business changes, management guidance, uncertainty and alternative plausible assumptions. Management guidance must not be copied mechanically into the base case.

Inferer distinguishes reported fact, management view, historical tendency, inferred assumption and uncertainty. It does not present management emphasis as established economic-driver status.

The intended future loop is Inferer → neutral assumptions → Modeler → calculated consequences → Inferer → revised assumptions. Debater v1 does not authorize a new Inferer engine.

### Debater

Debater owns motivated, position-conditioned research. Given a position, it asks: “What is the strongest defensible case for this position?”

Debater may directly use Extractor evidence, historical Modeler outputs, Modeler forecasts and valuation, and Inferer/base assumptions as a benchmark. It does not have to route through Inferer.

It may select evidence, construct thesis logic, request historical tests or sensitivities from Modeler, supply stance-conditioned assumptions to Modeler, construct counterarguments and rebuttals, and identify weaknesses in its own case.

Debater must not alter historical facts or Extractor evidence, overwrite canonical neutral/base assumptions, present stance-conditioned assumptions as neutral, invent evidence or promote unresolved claims to facts. Assumption sets retain explicit origin and stance.

Implement the bounded corpus-first workflow specified in Debater v1. Planner and Reviewer are functions within Debater, not additional components or an agent per question.

### Composer

Composer owns communication and publication: prose, report organization, headlines and transitions, chart/table presentation, captions and source notes, appendices, Markdown, Word/PDF, layout, style and rendering.

Composer may communicate neutral analysis or a Debater case. It does not originate assumptions or substantive analytical conclusions. Thesis logic, supporting-evidence selection, counterarguments and rebuttal substance belong to Debater; their wording and presentation belong to Composer.

Composer must not alter facts or Modeler outputs, invent evidence, manufacture causal certainty, turn unresolved judgments into established facts or create unsupported numerical conclusions.

For Debater v1, Composer supplies only a small deterministic Markdown-tree renderer with no LLM, Office, Pandoc, plotting or font dependency. Future publication remains a separate operation.

### Figures and handoffs

Modeler produces valid numerical series and calculations. Inferer forms neutral assumptions and evaluates their plausibility and uncertainty. Debater selects evidence and develops position-conditioned cases. Composer presents the supplied analytical state or case and controls exhibit form, labels, annotations, captions, source notes, ordering and visual emphasis.

A persuasive chart does not justify inventing an analytical relationship.

Extractor supplies evidence to Modeler, Inferer and Debater. Inferer supplies neutral assumptions to Modeler and may revise them after examining calculated consequences. Debater may request Modeler tests and calculations directly and supply explicitly separate stance-conditioned assumptions. Composer communicates neutral analysis or a Debater case under Director orchestration.

Interfaces remain thin and traceable. Do not create a large deterministic intermediate reasoning framework or ontology. The expressly authorized Debater v1 workflow does not authorize broader inference engines or prose systems.

### Interpreter and Driver decomposition

Interpreter must cease to exist as an active component. Do not rename it wholesale to Inferer. Inventory each Interpreter and Driver/research responsibility and split mixed files by decision type:

- Source-faithful facts, management statements, guidance and source provenance belong to Extractor.
- Historical and forecast calculations, scenario and valuation arithmetic, series, accounting identities, reconciliations, bridges, regressions, residuals, deterministic tests and mechanical claim validity belong to Modeler.
- Neutral/base assumption formation, assumption plausibility and neutral uncertainty belong to Inferer.
- Position-conditioned assumptions, thesis construction, supporting-evidence selection, counterarguments, rebuttals and case weaknesses belong to Debater.
- Research prose, headlines, report organization and publication presentation belong to Composer.
- System orchestration and global policy belong to Director.
- Obsolete functionality belongs to Legacy or Remove.

Split mixed deterministic prose into substantive decisions and wording/presentation. Preserve useful behavior and evidence qualifications without redesigning reports or assigning all former interpretation to one new component.

### Core dissolution

Core must cease to exist as an active implementation layer. Assign orchestration/policy to Director, source/provenance handling to Extractor, financial/model calculations to Modeler, neutral assumption logic to Inferer, argument/thesis logic to Debater and publication/rendering to Composer. Obsolete functionality belongs to Legacy or Remove.

Do not move all of Core into Director or create a replacement Core/Common/Shared layer. Update callers and remove obsolete active façades and duplicate implementations.

### Legacy and Remove

Keep `legacy/` at repository root. Legacy holds useful prior functionality outside the active architecture. Categories follow the actual inventory and may include Trainer, superseded workflows/interfaces, historical verification machinery, experiments or former research-generation architecture. Do not substantially or cosmetically refactor Legacy.

Active components must not depend on Legacy as a hidden implementation layer. Any implementation required by active behavior belongs under its correct active owner.

Remove material with no preservation value, including obsolete cloud infrastructure without a BAV Compiler role, dead duplicates, abandoned compatibility layers, inappropriate source-controlled generated/cache artifacts, temporary infrastructure and obsolete experiments. Do not create a `remove/` directory.

### Runtime workspace and root files

Keep `build/` at repository root as the runtime/generated workspace, not a component. Do not move it into Director. Preserve its canonical persistent upstream inputs and generated-output separation.

Outside `bav/`, retain only `legacy/`, `build/`, a minimal README.md and files genuinely required at repository root for packaging, Git, AutoCycle or other repository tooling. Keep `pyproject.toml` at root if required. Record why retained root files must remain there.

Inspect `requirements-trainer.txt` and other Trainer remnants by actual use. Move Trainer-only material to Legacy or remove it when unused; preserve active dependency declarations in appropriate required packaging/tooling files.

Do not move SESSION.md, TARGET.md, RESULT.md, IMPLEMENTATION.md or similar files without determining AutoCycle requirements. Architectural tidiness must not break controller operation or override protected-document ownership.

## Structural migration boundary

The Session 11 migration contract is retained below as historical scope and preservation guidance. Session 12 implements the explicitly authorized Debater feature; it does not repeat migration or certify historical work by instruction incorporation.

The migration inspects the complete repository and records responsibility ownership before code movement. It assigns every meaningful responsibility to one of the six components, Legacy, Remove or Runtime-tooling, paying particular attention to `bav/`, Core, Interpreter, top-level component folders, Driver/research, root Markdown and Trainer remnants.

Then split mixed files, move all active implementation into the six canonical `bav` packages, dismantle Interpreter and Core, and update imports, package exports, CLI routing, tests, documentation, build paths and publish paths. Preserve Build and Legacy at root.

Preserve useful existing BAV behavior and source evidence. Establish minimal component documentation where implementation is absent. Record the responsibility mapping, Interpreter split, Core split, root files intentionally retained and why, removed functionality, verification evidence and unresolved architectural ambiguities.

Migration completion requires no active Core or Interpreter, no duplicate old/new implementations, correct six-component ownership, explicit assumption origin and stance, neutral/base protection, Legacy independence, passing relevant regressions and representative Lululemon and Fast Retailing builds, checks and publications.

Migration alone did not authorize sophisticated Inferer or Debater engines, new forecast or valuation methods, new LLM workflows, Extractor or Composer redesign, unnecessary rewrites of working quantitative logic, Trainer expansion, replacement generic layers, a large reasoning ontology or cosmetic Legacy refactoring.

The retained historical and future product specifications below preserve existing behavior and longer-term intent. Session 12's separate authorization permits only the Debater v1 feature and its necessary narrow extensions; completing a Session never automatically authorizes another phase.

## Research output architecture

The canonical build architecture separates persistent upstream inputs from generated outputs:

- `build/input/<company>/source/`: original source filings.
- `build/input/<company>/extracted/`: filing-level ordinary financial and management KPI extraction.
- `build/input/<company>/reconciled/`: accepted company-level reconciled data and admission evidence.
- `build/input/<company>/research_sources/<document-id>/`: retained research originals, source-faithful Markdown, manifests, passage records and required original/converter assets.
- `build/input/cases/<case-slug>/`: durable case state, case-specific evidence, extracted selections and revisions.
- `build/output/<company>/`: generated workbook, research, figures, supporting build artifacts and published documents.
- `build/output/cases/<case-slug>/`: a coherent selected revision of `argument.json`, `argument.md` and portable selected `data/`.

Research-source bundles remain outside strict accounting-extraction directories and never rewrite accepted standardized financial data. Shared preparation is reused across questions and cases; ambiguous issuer/version inputs remain case-local. Case inputs and shared research sources survive ordinary company rebuilds. Document backup implications where `build/input/` is Git-ignored.

All company directory names are lowercase, including `lululemon` and `fast_retailing`. Human-facing filenames may retain normal capitalization.

The completed Lululemon build contains:

- `build/output/lululemon/Lululemon_BAV.xlsx`
- `build/output/lululemon/research/Lululemon_Drivers.md`
- `build/output/lululemon/research/Lululemon_Forecast.md`
- `build/output/lululemon/research/Lululemon_Valuation.md`
- `build/output/lululemon/research/Lululemon_Overview.md`
- `build/output/lululemon/supporting/build_status.json`
- `build/output/lululemon/supporting/assumptions.json`
- `build/output/lululemon/supporting/component_map.json`
- `build/output/lululemon/supporting/rowmap.json`

Driver figures under `build/output/<company>/figures/drivers/` are optional and claim-driven. No particular chart or schedule is mandatory; retain a figure only when it communicates a selected analytical relationship more clearly than prose.

`python -m bav build Lululemon` reads the canonical Lululemon input and writes only under `build/output/lululemon/`. `python -m bav check Lululemon` checks that canonical output without requiring paths. `python -m bav publish Lululemon` renders canonical analysis and referenced figures into Word and PDF under `build/output/lululemon/`. These company-name interfaces generalize to supported companies. Build remains the primary product command; Check is diagnostic. Internal lookup may normalize company names to lowercase slugs.

Benchmark and release are uses of canonical outputs, represented through Git tracking, tags or release packaging, not separate company data architectures. After canonical paths and dependencies are verified, remove obsolete generated artifacts and duplicate legacy, benchmark and release company trees, including obsolete Trainer and Answer Key outputs. Preserve original filings and canonical upstream data. Compatibility copies or symlinks require an active supported interface; do not maintain alternate active build architectures. Runtime must not silently fall back to obsolete benchmark, release or other legacy company paths.

The Debater benchmark uses an explicitly recorded isolated case for staged evidence addition without deleting or hiding canonical company inputs. Preserve prior reviewed revisions and manually edited exports; no blanket legacy-artifact cleanup is authorized by Debater v1.

Root `README.md` minimally documents BAV Compiler, public use and its component and output architecture, linking detailed specifications. Director-owned `bav/director/docs/STYLE.md` is the single source of truth for human-facing BAV presentation and language conventions, applied to Markdown research, generated figures and rendered publications. Do not duplicate its specification in README or individual modules.

Director-owned `bav/director/docs/DRIVER.md` retains the company-agnostic historical Driver specification with ownership aligned to the component boundaries above. The existing publication hierarchy is headline conclusion, principal drivers, optional secondary signals, and an auditable appendix. Supplied analytical conclusions and available evidence inform communication; Composer owns publication ordering and emphasis without originating substantive conclusions. Company-specific applications remain labeled regression fixtures. The main body must stand alone while the appendix preserves the detailed analytical record.

The research module sequence is Drivers, Forecast, Valuation, Overview:

- Drivers: historical business, operating and financial analysis.
- Forecast: forward estimates and assumptions.
- Valuation: standalone valuation.
- Overview: cross-module synthesis.

These are output modules, not architectural components. Module names use one word unless a one-word name would be genuinely unclear. Preserve current Drivers behavior; Forecast, Valuation and Overview files remain zero-content placeholders, without headings, explanatory text, TODOs, templates or analysis. Debater case artifacts do not populate these company modules.

Research and figures must be reproducible from the same validated BAV inputs as the workbook. Preserve calculations, source references, reconciliations and validation controls; do not maintain a separate uncontrolled numerical dataset. Figures use Matplotlib and one centralized style implementation derived from STYLE.md.

Publication is downstream of analysis and must not duplicate analytical logic or maintain a second manually edited report. Use a standard maintainable Markdown-to-document toolchain where it meets actual rendering requirements. Word and PDF must be generated entirely from the CLI, without manual post-processing, and preserve headings, tables, equations, captions, source notes, meaningful structure and readable page layout. Resolve referenced canonical figures correctly; missing figures, broken references or conversion failures must fail clearly. Apply established styling and omit internal implementation/debug material from teammate-facing reports. Verify output readability and reproducibility.

Preserve the existing validated workbook. Debater v1 does not authorize a general workbook redesign or removal of audit evidence.

## Scope boundary

The analytical scope is **non-financial operating companies**. Banks, insurers, brokers, and other financial institutions require separate sector-specific accounting and valuation logic.

Hong Kong company input may remain manual. Automatic HKEX scraping is not required when annual reports, interim reports, results materials, Excel exports, Bloomberg exports, or Wind exports are supplied.

Analysis and exercises should follow materiality and the information actually supplied. Missing historical facts must not be invented.

BAV supplies source-grounded equity-research analysis and historical target-assessment evidence for the Lululemon M&A teamwork project. Identify historical growth and margin drivers, recurring versus episodic components, robust relationships and unresolved explanations. Session 12 additionally authorizes the explicit hypothetical Fast Retailing–Lululemon growth proposition through Debater v1, including a transfer mechanism and continued-independence comparison. This is not authorization for a deal recommendation, acquisition valuation, price target or new forecasting engine. Use supported case-local arithmetic only under the approved scope and explicit assumptions.

Preserve historical Driver publication for Lululemon and Fast Retailing through the shared company-agnostic path as regression cases. Neither company must reproduce the other's driver categories, figures or section count, and unavailable mechanisms do not justify fabricated data, forced external research acquisition or broad workbook changes. The previous publication-session sequence does not replace the current Endpoint and Priority.

## Source-data architecture

The analytical accounting engine does not interpret arbitrary PDFs directly. Debater research may read source-faithful filing Markdown prepared by Extractor's verified existing-converter adapter; this is separate from accounting extraction.

`build/input/<company>/` contains all persistent upstream data needed to reproduce the BAV output. For Lululemon, `source/` holds original filings; `extracted/` holds ordinary financial and management KPI filing JSON, such as `LULU_FY2022.json` and `LULU_FY2022_management_kpis.json`; `reconciled/` holds `standardized.json`, `provenance.json`, `conflicts.json` and `management_kpi_admission.json`.

`build/input/lululemon/reconciled/standardized.json` remains the canonical company model consumed by the BAV build. Integrate useful existing upstream evidence into this architecture without retaining duplicate identical files or a separate `lululemon-live` tree. Use the same structure for `fast_retailing`.

Preserve issuer fiscal-year labels and actual period-end dates as distinct information at the canonical data/presentation boundary. Workbook presentation, Markdown and figures use the same issuer fiscal-year mapping; never derive issuer fiscal year from the calendar year of the period-end date.

For filing-based accounting workflows, the canonical upstream handoff is **source-grounded filing JSON**. Each filing is extracted independently and preserves reported labels, statement sections, periods, currency/unit scale, values, and page-level provenance.

LLM-assisted extraction is permitted upstream, but extraction must remain separate from accounting judgment and analytical modeling. Extractor records what the filing says; Modeler owns reproducible classification, normalization, reconciliation and analysis under explicit assumptions. Inferer owns neutral/base assumption formation; Debater owns position-conditioned assumptions and case construction.

The preserved filing workflow is:

source documents → one extracted JSON per filing → deterministic validation → deterministic cross-filing reconciliation → `StandardizedFinancials` → complete BAV reference model → professional BAV workbook

Optional Legacy Trainer derivation may consume the completed model; active BAV generation must not depend on Legacy.

Canonical Markdown research and reusable figures consume the same validated analytical outputs, with traceability to the workbook and source evidence.

Debater additionally consumes supplied filing Markdown or source PDFs converted to Markdown, through Extractor's source-located corpus. Preserve headings, tables, footnotes, context and exact selected passages. Use section/line locators when page mappings are unavailable. Hash and attribute representations separately, and do not count a PDF and its derivative as independent corroboration. Prepared research text does not replace the validated financial handoff.

Cross-filing differences, restatements, and source conflicts must be recorded rather than silently overwritten. Later audited presentations may take deterministic precedence, but the superseded observations remain in provenance.

`StandardizedFinancials` remains the model-facing contract. Source paths, page references, extraction evidence, conflicts, and discarded observations remain separate audit artifacts.

PDF/LLM accounting extraction may later be automated through an external model/API, but the BAV accounting engine must remain provider-independent and consume validated structured data rather than model responses directly. Debater's authorized local PDF-to-Markdown preparation neither requires nor authorizes that later accounting automation.

## Curriculum progression

This is retained Legacy Trainer intent, not active Debater development.

The learner should progress through three levels.

### Level 1 — Guided model construction

The system supplies source financials, accounting classifications, market facts, and setup judgments. The learner reconstructs formulas, links, reformulation schedules, ratios, bridges, and analytical calculations.

### Level 2 — Analyst judgment

The system still supplies source facts, but selected classification, normalization, and accounting-treatment decisions become explicit exercises. The learner chooses and defends treatments and reconciles the resulting model.

### Level 3 — Research application

The learner receives company filings/source extracts and must build the historical analytical model, identify accounting distortions, interpret performance drivers, forecast the business, value the company, and produce a concise investment-oriented conclusion.

The intended progression is:

supplied judgment → guided judgment → independent accounting analysis → historical research diagnostics → driver-based forecasting → valuation → investment interpretation

Ambiguous accounting treatments should be taught as alternatives with consequences rather than as one universally correct answer.

## Historical Step 9 — retained product stage

The historical-v1 model-construction foundation is release-gated and usable for learning now. Historical Step 9 describes retained analytical scope; it is distinct from Session/work numbering.

Preserve existing historical capabilities under their correct component owners:

- multi-period source links and reformulated statements;
- NOPAT, NOWC, NOLA, NOA, Net Debt, and reformulated Equity;
- historical growth, margins, effective tax, financing metrics, RNOA, Spread, FLEV, ROE, and DuPont;
- guided Accounting Judgment for supported classification alternatives;
- guided recurring/non-recurring earnings normalization;
- cash-conversion and accrual diagnostics and trends;
- working-capital diagnostics and driver decomposition;
- RNOA margin/turnover and change attribution;
- ROE operating/financing attribution;
- historical diluted per-share analysis when actual diluted weighted-average share history is supplied;
- normalized diluted EPS when both share history and normalization cases are supplied;
- workbook-wide Check;
- completed reference-model formulas and Notes with a matched Trainer;
- cross-company synthetic robustness tests.

Broader forecasting, valuation, scenario engines and investment conclusions remain deferred. The explicitly authorized Debater v1 case workflow may reuse supported Modeler calculations without activating those deferred product stages.

## Reference workbook for historical convergence

`example/GOOGL_Demo_Integrated_Financials.xlsx` is the project’s **reference workbook for structural coherence and analytical completeness**.

Use it to study:

- how source statements, reformulation, DuPont, earnings-quality analysis, and downstream analytical schedules fit together;
- how an integrated analyst workbook organizes historical information without fragmenting the model;
- which historically useful analytical sections are still missing from the BAV;
- how information density and dependency flow can be improved.

It is **not** a literal template.

Do not automatically copy:

- its decorative styling;
- its populated calculations into Trainer practice cells;
- pipeline/automation features;
- quarterly, forecasting, scenario, valuation, or market-monitoring features merely because they exist there;
- any source facts not explicitly supplied for the company.

A feature from the GOOGL workbook should enter the BAV only when it is historically relevant, analytically useful and supported by explicit source facts. Trainer derivation should preserve the relevant semantic mapping and Check behavior.

The BAV should converge toward the reference workbook’s integration and analytical depth. The Trainer retains its learning mechanics as a derivative.

## Historical accounting competence to cover

Step 9 should continue toward coverage of these topics where material and supported by supplied facts:

- three-statement linkage and accounting sign conventions;
- operating versus financing classification;
- recurring versus transitory / non-recurring items;
- earnings normalization;
- accruals, cash conversion, and quality of earnings;
- working-capital behavior;
- revenue growth and margin analysis;
- capex, depreciation, asset intensity, and turnover;
- leases;
- stock-based compensation and dilution;
- goodwill, acquired intangibles, and acquisitions;
- deferred taxes and unusual tax rates;
- minority / non-controlling interests;
- historical share counts and per-share bridges;
- segment economics where disclosed;
- accounting consistency checks and detection of suspicious or internally inconsistent results;
- operating/financing reformulation under the BAV framework;
- RNOA, after-tax cost of debt, Spread, FLEV, ROE decomposition, and related profitability diagnostics.

The product should not require every topic for every company. Optional modules should be gated by materiality and source availability.

## Interpretation is part of the product

Major schedules should explain what changed economically and why it matters, as well as how a number is calculated.

The historical decomposition is the primary analytical object. Preserve this analytical sequence while assigning calculations and deterministic validity to Modeler, neutral assumptions and uncertainty to Inferer, position-conditioned case construction to Debater and expression to Composer:

reported outcome → decomposition → measurable components / admitted KPIs → historical contribution analysis → reconstruction of actual results → residuals and contradictions → source and management-disclosure check → interpretation

For each material outcome, answer: what happened, what moved it mathematically, and what explains those arithmetic movements? State the relationship or formula, calculate across available historical periods, compare implied changes with reported changes, and expose unexplained components. Prefer a few economically meaningful, source-supported decompositions over weak ratio catalogues.

Revenue analysis retains the existing supported driver calculations using admitted geography/segment, footprint, comparable-sales, channel or other operational evidence where available. Quantify geographic contributions and test footprint versus intensity relationships without inventing missing components. Company-wide revenue per store is a historical intensity proxy, not pure store productivity when digital or other channels contribute. Preserve channel, currency, calendar and definition distinctions.

Margin analysis explicitly follows the three-question structure. State historical revenue, gross profit, gross margin, SG&A burden, other material operating items, operating profit and operating margin. Where disclosed, use:

Operating margin = Gross margin − SG&A / Revenue − impairment or asset-related charges / Revenue − other reported operating items / Revenue.

Bridge changes with consistent signs and denominators in percentage points or basis points. Reconcile levels and changes to reported operating margin and show any residual. Do not hide disclosed components in an aggregate operating burden or invent undisclosed subcomponents.

After establishing the arithmetic, trace explanations such as mix, markdowns, freight, input costs, occupancy, geographic mix and leverage/deleverage to source evidence. Preserve management explanations as attributed statements; measure causal contributions only where disclosures support the calculation. Management emphasis does not itself establish a driver. Preserve these source controls when adding the narrow Debater filing-retrieval path.

For each non-trivial proposed driver relationship, historical validation tests direction, magnitude, reconstruction, residual, stability across periods, contradictions and the disclosure check. Use compact bridges or tables. Validation tests the decomposition against observed history; it is not a separate predictive model. Do not add statistically elaborate models unsupported by the historical sample.

Clearly distinguish accounting identity, reported historical fact, management explanation or strategy, observed historical relationship, economically plausible causal hypothesis and inference not established by evidence. An accounting identity or correlation alone does not establish a causal driver. Reconsider unsupported explanations or state that evidence is insufficient.

Use this history to identify informative versus weak relationships, recurring versus episodic movements, accounting growth versus underlying operating improvement, and sourced claims versus inference. Methods generalize across companies; benchmark issuers do not justify issuer-specific analytical rules. Debater v1 does not authorize expansion of the ordinary company analysis modules.

Other interpretation questions include:

- Was a decline in RNOA caused by lower operating margins or greater NOA intensity?
- Did earnings growth come from operating improvement, leverage, acquisitions, tax effects, or dilution?
- Is cash conversion consistent with reported profitability?
- Does a working-capital movement reflect growth, deterioration, seasonality, or accounting treatment?
- Is an apparent improvement in ROE operating or financing-driven?

The workbook need not grade free-form essays. Preserved diagnostics do not justify a new deterministic reasoning framework or research-writing evaluation layer.

## Historical learner experience

1. Supply historical company source documents or already-extracted filing JSON.
2. Convert each filing into source-grounded structured facts, then validate and reconcile those facts into model-facing historical input.
3. Build the complete historical BAV analysis from accepted facts and setup judgments.
4. Produce `<Company>_BAV.xlsx` as the default professional deliverable.
5. Optionally derive `<Company>_BAV_Trainer.xlsx` from the same completed model.
6. In the Trainer, source data and supplied facts remain populated. The learner fills selected yellow historical formula cells and guided judgment-response cells.
7. Run **Check** when desired: blank cells remain yellow, correct cells become green and incorrect cells become red.
8. Consult the matching BAV for correct formulas and concise analytical Notes. The BAV uses ordinary white/no-fill cells and contains no yellow fill/highlight or exercise framing.

The BAV is the authoritative formula-and-Note reference. Check validates only; it does not reveal answers. The BAV must remain professionally presented rather than adopting learning instructions.

## What stays populated

The Trainer should not make the learner re-enter literal data that the system already knows. Keep populated:

- historical source-statement numbers;
- historical share-count data and market facts when supplied;
- labels, dates, units, and workbook setup;
- system-controlled source links or checks intentionally outside the current practice surface;
- supplied setup/judgment facts until the relevant judgment exercise explicitly makes them learner-controlled.

The default test is: **does reconstructing this cell teach historical model logic or only data entry?**

## Hard requirements for the historical product

- **Historical reference-model first.** The professional BAV contains the complete working historical model; Trainer formulas derive from it.
- **No invented historical inputs.** Historical ratios, KPIs and per-share metrics use supplied historical facts only. Synthetic fixtures are not production evidence.
- **Source-grounded structured handoff.** Filing-based LLM extraction produces one auditable JSON artifact per source filing before BAV standardization; source conflicts/restatements are preserved in audit artifacts.
- **Professional default deliverable.** Ordinary company builds produce `<Company>_BAV.xlsx`. Successful builds and intermediate Session progress do not require Trainer generation.
- **Secondary Trainer.** Preserve optional derivation of `<Company>_BAV_Trainer.xlsx` from the completed model. Do not add unnecessary CLI commands solely for this distinction.
- **Formula-construction focus.** Practice should teach model logic, not transcription.
- **Trainer contains no active answers or hints.** Active formula-practice cells start blank yellow with no Note/comment.
- **BAV contains formulas and analytical Notes, with no yellow.** Cells corresponding to Trainer practice contain correct formulas and concise non-empty Notes, using ordinary white/no-fill formatting.
- **Workbook-wide Check.** One Check validates every active historical practice cell.
- **Check is non-disclosing.** Aggregate counts are allowed; answers/formulas/hints are not printed or inserted.
- **Shared analytical structure.** BAV and Trainer retain corresponding analytical identities and schedules. Opening presentation and learning instructions may differ according to product purpose.
- **Restrained presentation.** Preserve Aptos Narrow 11, black text and ordinary white cells for the existing analytical surface. Bright yellow denotes only Trainer practice; green/red denote functional Check feedback. Avoid decorative borders and fills. Professional opening and analytical presentation should materially improve understanding. STYLE.md governs research presentation; Session 4 does not require restyling the preserved analytical workbook.
- **Semantic component mapping.** Practice formulas resolve by semantic identity rather than fragile static coordinates.
- **Professional workbook preserved.** Trainer derivation removes only selected learning cells and adds training presentation; it must not mutate the BAV. Source facts and non-practice calculations remain populated.
- **Standardized identity survives round trips.** Identity-bearing fields such as `LineItem.concept` survive supported standardized-data export/reload.
- **Historical accounting logic is authoritative.** Reformulation and DuPont math remain aligned with BAV methodology.
- **Non-financial-company scope.** Do not imply the same reformulation is universal for financial institutions.
- **Forecast isolation.** Normal Step 9 builds must not execute dormant forecasting or valuation code.

## Step 9 roadmap before forecasting

The historical roadmap retains:

1. historical reformulation and DuPont foundation;
2. multi-period completion;
3. accounting judgment and normalization;
4. earnings-quality, cash-conversion, working-capital, profitability, financing, and per-share diagnostics;
5. cross-company robustness;
6. professional BAV presentation, derivative Trainer and practical documentation;
7. **GOOGL historical reference audit:** compare the historical model with `GOOGL_Demo_Integrated_Financials.xlsx` and classify historical gaps;
8. **historical convergence:** implement the highest-value missing historical analytical modules supported by explicit data, including where appropriate capex/depreciation/asset intensity, leases, SBC/dilution, goodwill/acquisitions, deferred tax, NCI, segment economics, and consistency checks;
9. **unseen-company / real-company historical validation:** validate the complete source-document → filing-JSON → reconciliation → `StandardizedFinancials` handoff and prove the professional model and derivative Trainer work beyond synthetic fixtures and the illustrative demo;
10. only after historical Step 9 is coherent and usable, reintroduce driver-based forecasting;
11. only after forecasting is separately verified, add valuation, scenarios, and investment conclusions.

SESSION.md specifies the current Endpoint and Priority within this destination. Full normalization, NOA and NOPAT completion need not precede historical driver-and-strategy analysis unless directly necessary for it. The separately authorized Debater v1 workflow need not await completion of unrelated historical roadmap items.

Do not jump from the release-gated historical-v1 baseline directly into forecasting merely because the baseline is technically complete.

## Autonomous progression policy

The current authorized feature direction is Debater v1. Historical product-stage numbers below are retained roadmap references, not authorization to add unrelated features or a substitute for Session/work numbering.

Autonomous planning must advance the current Session Endpoint under its Priority. Preserve useful existing capabilities and defer unrelated historical feature expansion.

### Current analytical focus gate

Endpoint and Priority belong in SESSION.md.

Preserve accepted Geographic Analysis, Operating KPIs and Normalization Judgment / Earnings Normalization work. Unfinished normalization and broader accounting work remain open long-term obligations; do not represent deferral as completion.

Preserve already accepted accounting, ingestion, geographic, KPI, normalization, provenance, workbook and regression work within the six-component architecture.

Historical Net Debt / Debt-Like Items Bridge, Complete NOPAT / RNOA and new forecasting remain deferred. Debater v1 authorizes the specified hypothetical acquisition-growth case, including its buyer-specific transfer and independence comparison, without authorizing a deal recommendation or acquisition valuation.

### Step 9 exit gate

Step 9 is complete when all of the following are true:

- the GOOOGL historical reference audit has no unresolved high-value historical gap;
- historically material modules supported by available source facts are implemented, tested, or explicitly deferred with a documented reason;
- the source-document → filing JSON → reconciliation → `StandardizedFinancials` → reference-model → professional BAV → derivative Trainer path has been demonstrated on real-company data;
- optional historical modules fail closed when required evidence is missing or contradictory;
- historical analytical schedules, learner practice surfaces, Check behavior, provenance, and workbook generation pass their required regression and benchmark tests;
- no known historical defect or missing module materially limits analysis of an unfamiliar non-financial company.

Once this gate is satisfied, subsequent authorized planning should advance toward Step 10 rather than inventing additional historical polish. It must still respect an explicit Session boundary; completing a Session does not automatically start another.

A completed roadmap item should not be reopened unless a later regression, benchmark, or new source-supported requirement exposes a concrete defect.

### Step 10 — Driver-based forecasting

Build forecasting only after Step 9 passes its exit gate and the active Session permits forecasting.

The forecasting system should:

- begin from the verified historical analytical model;
- forecast explicit operating drivers rather than extrapolating outputs mechanically;
- link revenue, margins, working capital, capex, depreciation, taxes, financing, and share-count assumptions to the relevant historical diagnostics;
- distinguish supplied assumptions, learner assumptions, and calculated outputs;
- preserve accounting identities and historical/forecast continuity;
- make key assumptions auditable and suitable for learner practice;
- support a coherent base case before introducing alternative scenarios.

Step 10 is complete when an unfamiliar supported company can move from verified historical analysis to an internally coherent, driver-based forecast with tested formulas, assumptions, and accounting links.

### Step 11 — Valuation and scenarios

Only after Step 10 is verified, add valuation and scenario analysis.

The valuation system should:

- consume the verified historical and forecast model rather than duplicate it;
- implement BAV-consistent valuation methods and appropriate cross-checks;
- make cost-of-capital, terminal-value, and other material valuation assumptions explicit;
- support disciplined Bear / Base / Bull scenarios by changing economically meaningful drivers;
- expose major sensitivities without creating arbitrary scenario complexity;
- reconcile valuation outputs to per-share equity value and relevant market inputs.

Step 11 is complete when valuation is internally reconciled, scenario differences can be traced to explicit assumptions, and major sensitivities are visible and testable.

### Step 12 — Investment interpretation

Only after historical analysis, forecasting, and valuation are verified, build the final research interpretation layer. This long-term stage is distinct from Session 12's expressly authorized corpus-first Debater feature.

The analyst, and subsequently the learner, should be able to:

- identify the principal historical and forecast value drivers;
- distinguish operating improvement from financing, accounting, tax, acquisition, and dilution effects;
- state the assumptions on which valuation depends;
- identify material risks and variant views;
- connect scenario and sensitivity results to the investment thesis;
- produce a concise, evidence-based investment conclusion.

Inferer owns neutral/base assumption formation, Debater owns position-conditioned assumptions and case construction, Modeler calculates consequences, and Composer communicates supplied analysis and conclusions. Beyond Debater v1's specified workflow, future reasoning and prose systems remain deferred; this roadmap does not mandate a deterministic reasoning ontology.

### Autonomous planning rule

Use the existing AutoCycle Completion and Review control loop.

Within the active Session, choose the smallest direct work that materially advances its Endpoint, governed by its Priority. Prefer meaningful end-to-end product capability and reuse of adequate working subsystems.

Defer infrastructure refinement, hypothetical edge-case hardening, cosmetic work and abstractions that are unnecessary for the Endpoint.

The long-term stage order remains Step 9 → Step 10 → Step 11 → Step 12. Advance those stages only when their exit conditions are supported by evidence and the active Session permits that scope. The explicit Debater v1 authorization is a bounded feature direction, not certification or activation of the deferred forecasting and valuation stages.

`DONE` requires the Session Endpoint and current plan acceptance, not merely publication or consumption of instructions. Never start a new Session automatically.

## Forecast / valuation boundary

Forecasting, residual-income valuation, DCF/cross-check valuation, terminal value, Bear/Base/Bull scenarios, and forward valuation multiples remain deferred during the current Step 9 stage.

Historical relationships must not become forward assumptions in a historical-only Session. Later forecasting requires both the Step 9 exit gate and a Session permitting that work.

Debater v1 may use existing supported Modeler capabilities and narrow necessary calculations with explicit case-local assumptions and provenance. It must report a capability gap rather than build a new financial engine. A scenario does not establish the truth of its assumptions, and case calculations must not activate dormant forecasting in ordinary company builds.

The repository may retain dormant forecast/valuation scaffolding with an explicit inventory disposition, but normal historical builds must not execute it or depend on forecast outputs. Retention alone does not authorize implementation.

Deferred tabs may remain hidden placeholders: `Model_Bear`, `Model_Base`, `Model_Bull`, `Scenario_Summary`.

They must remain excluded from the active semantic practice surface and Check until a future forecasting stage explicitly activates them.

## Definition of done for the current historical baseline

The BAV-first historical baseline is complete when supported historical data for a non-financial company produces a professional BAV and permits derivation of a matching Trainer in which:

- the historical model is internally coherent;
- source facts remain populated;
- the default deliverable is the professional BAV without required Trainer generation;
- active Trainer formula cells are blank yellow;
- matching BAV cells contain correct formulas and analytical Notes and are ordinary white/no-fill;
- the BAV contains no yellow fill/highlight or exercise framing;
- Check validates the full active Trainer surface without disclosing answers;
- optional modules appear only when their required historical facts are supplied;
- normal generation does not run forecasting/valuation code;
- the BAV is usable as professional historical analysis and the derivative Trainer is usable for learning.

This baseline being complete does **not** freeze Step 9. Historical depth, reference-workbook convergence, accounting-analysis breadth, and real-company validation can continue within authorized Sessions before forecasting begins.

## End-state definition of done

The broader BAV research system succeeds when an unfamiliar supported non-financial company can be analyzed through a professional, auditable research workbook, canonical Markdown modules, reusable figures and shareable Word/PDF publications that enable the analyst to:

- construct and audit the historical accounting model;
- make defensible material accounting/reformulation judgments;
- identify and explain material earnings-quality and accounting issues;
- diagnose historical economic drivers;
- build explicit forecasts linked to those drivers;
- value the equity using BAV-consistent methods and appropriate cross-checks;
- explain key sensitivities, risks, and variant assumptions; and
- communicate a concise, evidence-based investment conclusion.

Debater additionally supports inspectable, source-grounded proposition cases with linked claims, visible research questions, reusable selected evidence, explicit assumptions and qualifications, and durable evidence addition and resumption. A defensible Incomplete or Unsupported case is a legitimate research outcome; it does not excuse missing technical acceptance evidence.

The secondary Trainer should enable an accounting novice to progress toward solving such an unseen-company research case with materially less scaffolding.

## Planning ownership

This file records stable product intent. Target changes require explicit human instruction. ChatGPT owns planning publication; Cursor must never modify `TARGET.md`, `SESSION.md` or `IMPLEMENTATION.md`.

SESSION.md holds the current Endpoint and Priority. IMPLEMENTATION.md holds current bounded execution guidance. RESULT.md records implementation completion and measured verification.
