# Implement BAV Debater v1 — Asian-growth benchmark and filing evidence

This complete instruction replaces `bav-debater-v1-revised.md`, `bav-debater-v1-implementation.md`, and earlier Debater briefs. Implement it in the current BAV Compiler checkout. Develop the feature through the real benchmark below, including the narrow Extractor work it needs; do not combine superseded requirements with this file.

## 1. Product and deliverables

The user submits a proposition. Debater searches for one compact linked argument supporting it, using the approved corpus and explicit assumptions. It asks for the most consequential missing evidence, accepts additional files or availability notes, and resumes the same case. It can conclude that the record does not support the proposition.

Each case produces two principal files from the same validated revision:

- `argument.json` — the machine-readable argument tree, its research questions, selected evidence, underlying data, assumptions, and qualifications.
- `argument.md` — a deterministic, readable Markdown rendering of that same tree, including the questions underneath each linked claim and the evidence or unresolved requests attached to those questions.

Debater generates no `argument.txt`, report prose, graphs, chart specifications, slides, Word, or PDF publications. It supplies selected passages and data; a later Composer operation chooses and renders graphs or publications. Reading source PDFs, converting them to Markdown, and retaining original converter assets are explicitly in scope and are not publication generation. A fenced tree inside Markdown is required. New human-readable case artifacts use Markdown; machine records remain JSON, and original input formats remain unchanged.

This is feature implementation, not another architectural migration. Inspect the actual local checkout and project instructions first. Preserve `python -m bav`, the six-component architecture, existing company build/check/list/publish behavior, accepted financial inputs, neutral assumptions, and company outputs. Do not switch branches or discard unfinished work. Store the reconciled specification in the existing Director documentation area, normally `bav/director/docs/DEBATER.md`.

## 2. Primary benchmark and development order

Use this affirmative proposition as the main end-to-end benchmark:

> Fast Retailing's acquisition of Lululemon would accelerate Lululemon's growth in Asia.

Preserve that submitted wording. Treat the acquisition as hypothetical, not an announced or completed transaction. The benchmark is to implement grounded advocacy for this proposition, not a generic company summary or a neutral "whether" question. It is not a requirement that the final research verdict favor the acquisition.

Carry forward the user's research focus on **Japan and Greater China**, with separate coverage and support assessments. Do not substitute China Mainland for Greater China, use Rest of World as Japan, or treat evidence for one market as establishing the other. Record issuer-specific market definitions and missing coverage. Results for these focus markets do not establish every Asian market.

Make the comparison against realistic continued independence explicit. Growth concerns Lululemon's business, not the mechanical increase in Fast Retailing's consolidated revenue. Propose the relevant outcome measure, market interpretation, and any necessary horizon in the normal scope/proof-plan approval. Do not silently substitute store count for revenue growth, choose a numerical uplift, assume a closing date, or invent a three-year forecast. Initial source preparation and qualitative planning need not wait for parameters only required by later numerical work. Do not weaken "would" to "might" to obtain a favorable verdict; preserve uncertainty and conditionality honestly.

Develop one thin working path in this order:

1. Inspect the checkout, existing company source locations, PDF-to-Markdown tooling, and authorized runtime. Verify access before constructing a large framework.
2. Prepare a small source corpus for **both companies**, accepting existing filing Markdown directly and converting relevant PDFs only when needed.
3. Run the ordinary `debate` entry point on the proposition. Produce one linked argument with question-bearing branches and retrieve actual strategy passages and relevant Modeler data.
4. Export `argument.json` and the matching `argument.md` tree. If the record is insufficient, identify the most decisive missing evidence rather than filling the tree with invented answers.
5. Demonstrate an evidence addition and resumption through `--add`, then run the focused regression checks below.

The ordinary start command, once implemented, is:

```bash
python -m bav debate "Fast Retailing's acquisition of Lululemon would accelerate Lululemon's growth in Asia."
```

A supplied Markdown file uses the existing interface, with bare filenames resolved from Downloads:

```bash
python -m bav debate --case "Asian growth" \
  --add "lululemon-filing.md" \
  --add "fast-retailing-filing.md"
```

These filenames and the unique title fragment are examples, not assertions that such files or a case already exist. Print the actual title and commands. The benchmark context must be supplied or displayed through the normal scope/proof-plan flow, not inserted as hidden global defaults. Preserve intake clarification when needed; an intake-only response is not the completed research benchmark. A PDF is accepted through the same `--add` path and is prepared by Extractor; do not add a mandatory conversion wizard or a separate converter command users must remember.

Keep company names, source manifests, and this benchmark in configuration or fixtures, not special-case reasoning code. The reference tree later in this file illustrates the desired shape; the real tree and its answers must come from the accepted proposition and available evidence. Benchmark instructions, this discussion, synthetic examples, and previous generated arguments are not company evidence. Do not tune the test to pass only a positive verdict or an exact five-branch wording.

## 3. Filing Markdown and the minimum Extractor extension

### Find and reuse local sources

The user believes the company PDFs are under `~/Documents/Developer` and can also supply filing Markdown. Verify the locations on the user's machine; this instruction does not establish that any particular file exists.

Inspect registered `build/input/lululemon/` and `build/input/fast_retailing/` sources first. For initial benchmark setup only, perform bounded filename/metadata discovery for likely company PDF/Markdown filings under `~/Documents/Developer`, then inspect the relevant candidates to confirm issuer, document type, and period. Skip Git internals, environments, caches, credentials, generated research, and unrelated project content. Do not recursively ingest every PDF or follow symlinks outside the approved roots. When identity or edition is ambiguous, show candidates or request an exact path. Never move or delete the originals. This one-time discovery permission is not a permanent runtime permission to scan Developer.

Register a dated, fingerprinted benchmark source manifest so later runs use the same selected record. Preserve valid fiscal dates and source dates; filenames and file modification times alone do not establish publication dates. Do not assume the newest-looking file is the correct edition. Label the benchmark as corpus-bound, not a verified latest-market assessment. New filings create a new source snapshot rather than silently replacing the test corpus.

### Accept Markdown without unnecessary conversion

A supplied, readable full filing in Markdown goes directly into the research corpus. Preserve the original file bytes, headings, tables, footnotes, and explicit caveats. Never rewrite or summarize the document as a substitute for source preparation. Identify incomplete excerpts, missing assets, and uncertain provenance; useful partial coverage need not block unrelated questions.

Associate a Markdown derivative with its original PDF only when document identity/version is established. Matching names alone are insufficient. A PDF and its Markdown are two representations of one source, not independent corroboration. Corrected or independently supplied Markdown keeps its own hash and attribution. Preserve both versions if they differ, and record which supports a selected passage. An unverified Markdown-to-PDF association may still be cited to the Markdown itself; it must not acquire invented PDF page references or official status from its filename.

### Reuse the existing converter through an adapter

The prior setup discussed `marker_single` in `~/.venvs/marker/bin/`, with Markdown output. Treat this as a discovery hint, not proof of a currently working installation. Inspect the actual executable or existing project wrapper, version, local help, dependencies, and configuration. Reuse the working command rather than reinstalling/upgrading it or building another PDF parser framework. Do not copy remembered flags without checking the installed version.

Place the small conversion adapter and source-preparation code under `bav/extractor/`. Director dispatches a typed preparation request; the LLM does not generate an executable command. Invoke an allowlisted executable with an argument list, explicit input/output paths, a finite timeout, and captured diagnostics. Do not alter the user's interactive shell, global environment, or coding-agent configuration.

Prefer text-layer conversion for readable PDFs. Do not force OCR, repeatedly reconvert unchanged files, or enable external LLM enrichment. OCR is a last resort for necessary unreadable content; request supplied Markdown or an explicit, bounded authorized fallback when needed. Check for missing models, large downloads, services, or new billing before running; do not silently install them. Missing converter access must not prevent the direct-Markdown path from working.

Process one selected PDF at a time initially. Retain any converter-produced metadata, page information, and original image assets needed to inspect the source, but do not synthesize descriptions of unreadable charts as facts. No visual research report or graph generation belongs to Debater. Conversion has a recorded finite time/resource allowance and no automatic repeat-on-resume loop; material extensions require approval. A failed conversion is a preparation failure, not evidence that management omitted a fact.

Validate output before indexing. Check expected page coverage when available, readable text, preserved heading/context, and consequential selected tables against their source. Missing pages, garbled characters, lost qualifiers, or shifted table columns remain explicit limitations. Do not demand perfect conversion of an entire report before using sound passages from other sections. Do not repair numbers or wording by LLM guesswork. Preserve exact selected text as observed in the accepted representation and record any PDF verification separately.

### Store data separately from implementation

Code belongs to Extractor; company filings and their derivatives remain input data. Prefer a dedicated research-only namespace within the existing company input area:

```text
bav/extractor/                         # preparation and retrieval code

build/input/<company>/research_sources/<document-id>/
    original.pdf or original.md        # retained original; not modified
    document.md                       # searchable, source-faithful representation
    manifest.json                     # identity, hashes, origin, conversion, limitations
    passages.json                     # section/line/page-located search records
    assets/                           # existing source/converter assets when needed

build/input/cases/<case-slug>/         # case state and case-specific evidence
build/output/cases/<case-slug>/
    argument.json
    argument.md
    data/
```

Adapt names to compatible existing contracts. Keep research manifests/chunks out of directories consumed as strict accounting-extraction JSON. Check the current financial loaders before adding these files; do not break `validate-source`, reconciliation, or ordinary company builds. Source preparation must never rewrite accepted standardized financial data. Cases reference shared company source snapshots instead of duplicating or reconverting each filing. Inputs from the user remain case-local when issuer/version cannot be safely assigned.

Key reuse to the original-content hash, converter/profile version, and prepared-content hash, not only a basename. Register the completed prepared bundle atomically. Reuse unchanged preparation across both questions and cases. Retain the actual original filename in metadata even if a safe managed filename is used.

### Make filing strategy text retrievable as evidence

Index bounded passages by heading, stable line/offset ranges, and verified page mappings where available. Preserve neighboring paragraphs, complete table headers, units, and relevant footnotes; do not split away a qualification from the claim it limits. Use Markdown line/section locators when page mapping is absent. Distinguish physical PDF pages from printed page labels, and do not derive an exact page map from a table of contents alone.

Debater's questions should retrieve from full strategy, business, regional-operation, management-discussion, outlook, and risk text—not only existing KPI JSON. Extractor returns exact excerpts and usable table selections, source locators, origin, context, and search coverage. It does not return an invented "management supports the acquisition" answer. An aspiration or guidance statement remains an attributed management view; it is not proof of future performance or capability transfer.

The required chain is:

```text
Original PDF → existing converter → filing Markdown
Supplied filing Markdown ────────────────┘
                                         ↓
                         Extractor's source-located corpus
                                         ↓
                    Debater claim → question → selected evidence
                                         ↓
                           argument.json + argument.md
```

For each decisive gap, search relevant available passages and Modeler outputs first. Do not ask the user to supply Markdown that can already be prepared through an authorized working adapter. Conversely, do not label information undisclosed when conversion or coverage failed. The source manifest and query record must make that distinction inspectable.

## 4. What the tree represents

There are three conceptual layers:

1. **Proposition** — the accepted claim and scope.
2. **Linked claims** — the premises that together provide one argumentative route to that proposition.
3. **Evidence layer** — candidate questions or evidence avenues, their answers, and selected supporting or challenging evidence.

Research questions organize the evidence layer. A question with an indented answer or source selection may occupy an extra visual line or indentation level, but it is not a new inferential claim layer. Do not turn every question into another recursively decomposed claim. Conversely, do not hide the questions in metadata that the Markdown tree never shows.

Layer-two claims are linked, not separate mini-arguments each claiming to prove the proposition. Store a concise joint inference explaining why they work together. Evidence beneath an individual claim may be convergent, jointly required, or mixed; preserve that relationship. Multiple observations are not automatically independent confirmations.

Keep one active candidate argument. Generate only the linked claims it needs, usually a handful rather than a fixed count. Reuse existing support. Develop questions selectively, normally one to three useful questions per claim; these are starting guidelines, not quotas. Retired routes stay in compact history, not as an expanding forest in the displayed tree. Retire irrelevant or redundant questions with a reason; do not erase a material unanswered question merely to make the current tree look supported.

Every necessary claim needs a defensible basis, but not a new research project. An existing fact, transparent calculation or inference, or reasonable explicit background assumption may suffice. A disputed assumption that does the work of the conclusion remains consequential. A question, a plausible phrase, and an unanswered evidence request are not evidence.

Mark up to two principal evidence selections for possible later one-slide communication. They may be data tables, data series, or source excerpts. Do not render them as charts or force two selections. This limit governs emphasis, not the total evidence retained or the acceptance of the argument.

## 5. Reference tree and Markdown behavior

### Reference outline from the design discussion

This preserves the requested example and its questions. It is an unresearched planning outline, not a finding about either company and not a fixed template. Its Greater China/store-only wording is narrower than the primary Asian-growth benchmark. Use the benchmark proposition and approved scope for the real run, not this older root as a substitute.

```text
MASTER CLAIM
Acquisition by Fast Retailing would supercharge
Lululemon's Greater China store expansion
│
├── 1. Lululemon has a real expansion constraint
│   ├── Store availability?
│   │   Need opening pipelines, delayed sites, and reasons for delay.
│   ├── Local operating know-how?
│   ├── Landlord relationships?
│   ├── Hiring/training?
│   └── Local digital/community execution?
│
├── 2. Fast Retailing possesses relevant capabilities
│   ├── Store network development?
│   ├── Local real-estate relationships?
│   │   Need relevant landlords, sites, and access arrangements.
│   ├── China operating organization?
│   ├── Supply chain/logistics?
│   └── Localization capability?
│
├── 3. Those capabilities are transferable
│   ├── Can Lululemon use them?
│   ├── Are formats and locations compatible?
│   │   Need matched locations, customer catchments, and store formats.
│   └── Would autonomy and brand positioning survive?
│
├── 4. Transfer changes measurable outcomes
│   ├── More openings per year?
│   │   Need acquisition versus realistic standalone opening schedules.
│   ├── Faster store ramp?
│   ├── Higher sales per store?
│   └── Better margins or returns?
│
└── 5. Net acquisition economics are positive
    ├── Synergy value?
    │   Need incremental cash flows relative to independence.
    ├── Integration cost?
    ├── Premium paid?
    └── Execution risk?
```

The reference's fifth branch appraises acquisition value, not store acceleration alone. In a live growth-only case, do not make it a necessary proof obligation or require valuation work; omit it from the selected linked argument or identify it separately as a related appraisal. Make it a required branch only for a proposition whose approved scope includes acquisition value. Do not silently enlarge the proposition to retain a template. Likewise, define material scope such as Greater China and the intended acceleration measure through intake, not by inventing favorable definitions after research.

The many questions in this reference are possible evidence avenues, not a requirement to investigate them all. A concrete active route should retain the applicable questions and prioritize the decisive ones.

### Required rendering

`argument.md` starts with a short title and the tree in a fenced `text` block, using Unicode tree connectors, spaces, and stable wrapping around 100 columns. It must be readable as raw Markdown and in an ordinary Markdown preview. No Mermaid, Graphviz, HTML-only widget, image, browser service, or special extension is required.

Within the tree, show each linked claim's assessment and its retained questions. Under each question show the available concise answer, selected evidence IDs or values, or the specific evidence still needed. For example, this is a shape illustration rather than a factual result:

```text
├── 1. Suitable-site access delays otherwise viable openings [Unresolved]
│   ├── Which openings were delayed by site access? [Needs evidence]
│   │   Need planned and actual dates, location, and recorded delay cause.
│   └── Could staffing instead explain those delays? [Searched]
│       No answer in the reviewed sources; no conclusion of absence.
```

After evidence arrives, preserve the question and attach its source-grounded answer. A short display such as `E1 — selected observations` must identify actual selected content, not just a document title. Longer excerpts or tables go in a compact evidence appendix below the tree, referenced by ID. Questions answered adversely remain visible when material. Assumptions and failure conditions must be visible next to the affected claim or in a short referenced section, not buried in logs.

Do not produce analytical report paragraphs. Short claim statements, answers, inference explanations, source excerpts, data tables, and qualifications are appropriate. Keep evidence labels and numeric tokens intact while wrapping. Choose a fence delimiter longer than any embedded delimiter in the displayed content so a source excerpt cannot break the preview. Generate this view from JSON without another LLM call. Never reconstruct the JSON by parsing the Markdown. Manual edits to generated Markdown do not change case authority; detect an edited export before replacement and preserve it rather than silently destroying the user's edits.

## 6. Corpus-first control loop

```text
Accept proposition and scope
        ↓
Inspect corpus and construct one linked argument
        ↓
Attach a small set of evidence questions to each claim
        ↓
Search the existing corpus and run supported calculations
        ↓
Review evidence, joint inference, and decisive gaps
        ↓
Export a draft, ask for evidence, or consider another route
```

Use two LLM roles, Planner and Reviewer, inside Debater. They are functions, not additional top-level components or a multi-agent society. Director runs and checkpoints the loop.

### Planner

Input is the accepted proposition, scope, source inventory, current evidence, permissions, user notes, and prior review. Output is one linked argument, its joint inference, explicit assumptions, and claim-attached research questions. Each question records what would answer it and why its answer could change the case. Questions must seek discriminating observations, not instruct retrieval to return only favorable examples.

Prefer a concrete mechanism over a list of attractive company characteristics. A cross-company argument must contain the relevant bridge, not concatenate two company summaries. Acquisition-driven improvement needs a realistic standalone comparison. A conditional scenario is admissible, but assuming the improvement and then calculating it is not evidence that the improvement will occur.

### Execute through the existing components

Use Extractor to search and extract from approved company materials and imported external files. Search the available source text, not only previously extracted KPI fields; the missing observation may already be in the corpus. Use Modeler for calculations and case-local scenarios supported by existing capabilities. Batch compatible questions and reuse unchanged results.

Start with small local search/indexing facilities and existing readers. Do not introduce a general crawler or vector-database service. Relevant headings, lexical retrieval, table lookup, and bounded semantic assessment are sufficient initial mechanisms. A search hit is a candidate, not accepted evidence. Retain surrounding context and a record of sources actually checked. Search for contrary observations too. One search miss must not become a statement that the company never disclosed something.

Discover runtime sources through the existing company registry and canonical paths, including registered research-source Markdown, company source/extracted/reconciled inputs, and validated Modeler workbooks or sidecars. The bounded Developer-folder discovery in section 3 is a one-time benchmark setup task, not runtime authority to scan other projects. Do not scan `.git`, credentials, unrelated repositories, or all of Downloads. Previously generated research and Debater arguments are not independent evidence; follow their references to the underlying record.

If a required file cannot be parsed, distinguish that technical coverage gap from a searched source with no answer. Missing Modeler or Extractor functionality is a capability gap, not permission to fabricate data or implement a new financial engine. Add only narrow adapters or calculations needed for the agreed first version during implementation. The runtime research agent cannot write or install a missing tool; it returns a specific capability gap.

### Review and prioritize

Reviewer receives the original proposition, candidate argument, actual selected source content with context, Modeler methods/results, known counterevidence, and search coverage—not just Planner's persuasive summary. It checks reference integrity, support for each premise, and the joint inference separately. A criticism must name a concrete gap, incompatible definition, counterexample, or discriminating question.

Prioritize the unresolved question whose realistically obtainable answer could most improve judgment of the whole argument, considering the route's other gaps and acquisition effort. Use a brief qualitative value-of-information rationale, not invented probabilities. Favorability is not value of information. Prefer one decisive user request; allow two when useful, especially when one source could resolve both. Many candidate questions do not imply many active requests.

Before asking the user, use available corpus evidence and supported calculations. The request must state the affected question, minimum useful data, geography/period or other necessary scope, what was already checked, and why it matters. Keep the terminal terse; retain search detail in the case record.

After `--add`, validate the new material, connect it to the relevant question, and reassess the claims and joint inference. An irrelevant or incomplete file must not close a request automatically. One source may answer several questions. Reuse the evidence by reference without counting it as independent confirmation.

When the user says evidence is unavailable, preserve that statement as availability information, not proof the premise is false. Defer the route if needed and consider a different linked argument supporting the unchanged proposition. Do not delete an indispensable premise while keeping the original conclusion. Remember failed routes and unavailable requests so unchanged resumes do not repeat them.

Stop when the selected argument is adequate for the intended use and further work would mainly add detail; when an essential gap requires user input; or when the examined record does not sustain a viable route. Do not claim global optimality or exhaustive rejection of every imaginable argument.

## 7. CLI and case identity

Keep the command noninteractive. Every invocation works within its allowance, saves, prints its result or next action, and exits. No chat shell, wizard, TUI, dashboard, or waiting process.

| Operation | Command |
|---|---|
| Submit | `python -m bav debate "PROPOSITION"` |
| Submit with a file | `python -m bav debate "PROPOSITION" --add "catalog.csv"` |
| Find cases | `python -m bav debate --list` |
| Resume | `python -m bav debate --case "readable title or unique fragment"` |
| Inspect without research | `python -m bav debate --case "China expansion" --status` |
| Add and resume | `python -m bav debate --case "China expansion" --add "pipeline.csv"` |
| Add context | `python -m bav debate --case "China expansion" --note "The pipeline covers China Mainland only."` |
| Report unavailable evidence | `python -m bav debate --case "China expansion" --note "I cannot obtain the opening-delay records. Try another route."` |
| Approve the displayed pending item | `python -m bav debate --case "China expansion" --approve` |
| Exclude proposed meanings and approve | `python -m bav debate --case "product fit" --exclude 2,3 --approve` |
| Select a backend | `python -m bav debate --case "China expansion" --backend codex` |

Building the strongest defensible argument is implicit. Do not require a stance parameter, an evidence checklist, or “build the strongest case” in the proposition.

Assign a stable descriptive title identifying the proposition, not the current strategy. Exact title matching takes precedence over case-insensitive unique-fragment matching. On multiple matches, list full titles and exit without acting. On no match, print the list command. Do not guess or default to the most recent case. An internal ID and safe directory slug are allowed but not the user-facing reference.

Conservatively match repeated accepted propositions to existing cases. Preserve negation, entities, periods, geography, comparison, and strength. Never merge different claims through speculative semantic similarity. Resolve title collisions with meaningful scope text. Do not change titles after replacing a research route.

For `--add`, a bare filename resolves only to `~/Downloads`. Explicit absolute paths and paths such as `./catalog.csv` retain their ordinary meaning. Do not search all Downloads or other personal directories. Copy originals into managed storage, do not move or modify them. Same content is idempotent; changed content under the same name is a new version. Accept repeatable `--add` and optional `--note` together.

`--note` is complementary instruction, source context, or an evidence-availability response. It cannot replace the proposition or declare a disputed premise independently verified. Reject a materially changed proposition and request resubmission, leaving the case unchanged. If a note's target is unclear, ask which outstanding question it concerns before changing availability. No new unavailable-evidence flag is needed.

Validate the invocation and intended case before committing mutations. `--status` and `--list` are read-only and make no LLM calls. A bare resume of an unchanged waiting or current case returns saved work; it does not restart research. Reject conflicting options rather than guessing.

## 8. Intake and approvals

Distinguish meaning selection from proof planning.

- Clear propositions proceed without artificial meaning decomposition. Historical, comparative, causal, and conditional claims are allowed; they need not be discrete future events.
- Several workable meanings produce a numbered scope proposal. Confirm all or exclude meanings before substantial research. A pending proposal can have a saved title without a research status.
- Materially unclear submissions get a terse resubmission request and create no case. Do not use `--note` to repair a rejected proposition.

Keep the approved scope explicit. Do not substitute UNIQLO for Fast Retailing, China Mainland for Greater China, revenue for profit, or growth for acquisition value. If several retained meanings cannot be supported by one coherent linked argument, request narrower propositions rather than invent a link.

For substantive causal/strategic cases, inspect the source inventory and show a compact linked proof plan for approval. Simple facts and arithmetic comparisons need no extra approval. An initial plan can authorize limited fallback strategies. Routine questions and calculations within an approved route proceed automatically; a materially different mechanism, source-access permission, provider data-sharing boundary, or budget extension needs a new bounded approval.

`--approve` applies only to the single unchanged pending item previously displayed for that case. Bind it to the saved plan revision, actions, relevant input snapshots, provider boundary, and allowance. Recheck these at execution. If changed, do not execute; display the changed plan and require a subsequent approval. Repeating approval of the same consumed item must not repeat its actions. Keep only one pending item and serialize case mutations.

`--exclude` applies only to displayed meaning choices, never to necessary proof obligations or counterevidence. Permit `--exclude ... --approve` for that one atomic selection. Reject approval combined with files, notes, or backend changes; process those first. User approval permits research, not a premise's truth or a weakened standard.

## 9. Terminal contract

A deterministic formatter prints only populated `Case:`, `Status:`, and `Next:` fields in that order. Use one indentation level for continuation lines, no nested labels, and no unnecessary words. A colon is allowed only on a line starting with one of those three labels. Do not corrupt a literal URL or filename to comply; put a necessary colon-containing literal on a labeled line or reference a Markdown artifact containing it. The restriction applies to ordinary terminal messages, not JSON syntax, Markdown trees, or source quotations.

Do not stream raw provider messages, nested progress headings, or reasoning transcripts. Before assessment, a lone Case line is enough. The only case research statuses are:

| Status | Meaning |
|---|---|
| `Draft` | A reviewed, usable linked argument and evidence package exists. |
| `Incomplete` | An essential unresolved dependency prevents that argument. |
| `Unsupported` | Substantive assessment has not sustained a viable route in the examined record. |

Omit Status before an assessment exists. “Needs evidence” belongs under Next, not in a fourth case status. Internal question states do not expand this vocabulary. Budget limits, approval, interruption, provider configuration, and technical errors are next actions, not evidentiary verdicts. Missing evidence is not contradiction. Retain a previous status only if it remains valid for the current inputs.

Examples are hypothetical interface outputs:

```text
Next: Resubmit with the acquirer and intended beneficiary.
```

```text
Case: Lululemon–Fast Retailing product fit
Next: Confirm meanings
      1  Complementary product categories.
      2  Distinct price tiers.
      3  Complementary customer segments.
      python -m bav debate --case "product fit" --approve
```

```text
Case: Lululemon China expansion
Status: Incomplete
Next: Needs evidence — opening delays and causes in the target markets.
      Tests whether suitable-site access limits expansion.
      python -m bav debate --case "China expansion" --add "pipeline.csv"
```

```text
Case: Lululemon China expansion
Status: Draft
Next: open "build/output/cases/lululemon-china-expansion/argument.md"
```

```text
Case: Lululemon China expansion
Status: Unsupported
Next: Review the failed route in argument.md.
      Available evidence attributes the delays to a different constraint.
```

```text
Case: Lululemon China expansion
Next: Backend timed out. Resume saved work.
      python -m bav debate --case "China expansion"
```

Zero exit status means a command successfully handled and saved a result or ordinary wait, not that the proposition is supported. Use nonzero for invalid input and genuine execution failure. Preserve checkpoints on interruption. Keep a small structured internal result envelope rather than infer state from terminal prose.

## 10. JSON and data contract

Maintain one authoritative versioned case state; export one selected argument into `argument.json`. Markdown is its generated view, never a second editable authority. Include the accepted scope, status or null, case/revision identity, and the source/model snapshot on which the assessment depends.

Implement and ship a small versioned schema or equivalent validator with these relationships, plus an example JSON/Markdown pair exercising them. Additional operational metadata may be stored outside the export. A machine consumer must not need to infer claim/question associations from display order alone.

| Object | Required meaning |
|---|---|
| Proposition | Original submission, accepted wording/meanings, scope, and relevant success criterion or comparison. |
| Argument | One title, `linked` relation, short joint inference, and ordered linked claims. No recursively nested claim children. |
| Claim | Stable ID, statement, assessment, concise support rationale, assumptions, relevant failure conditions, and an ordered `questions` list. |
| Question | Stable ID, the inquiry, a concise answer or null, evidence links, remaining gap, search coverage, availability, and a qualitative priority reason. |
| Evidence link | Evidence ID, supports/challenges/context role, and why the selection bears on the question and claim. |
| Evidence | Exact selected text or structured data, source references/locators, context, definitions, lineage, and relevant limitations. |
| Source | Publisher/origin, original name, date or unknown date, content fingerprint, entity/market, and retained source location. |
| Primary evidence | Up to two emphasis references to existing evidence items or data selections. No chart type, axis, color, layout, or rendering specification. |
| Qualifications | Material limitations or conditional conclusions, linked to affected claims. |

Questions must be structurally nested under their claim, not only held in a flat request list. An outstanding request references that same question object by ID, rather than copying a second independently mutable version of it. A shared evidence registry prevents duplicated observations. A question can have several supporting and challenging links. Do not count questions, documents, and evidence items interchangeably.

Keep two distinct concepts. Claim assessment concerns support, with `supported`, `assumed`, `unresolved`, or `contradicted` and a short explanation for mixed cases. Question coverage/availability records whether it was searched and whether material is present, requested, inaccessible, or unavailable. An answered question can undermine a claim; unavailable evidence cannot automatically mark it contradicted. These internal values are not terminal case statuses.

Selected numerical data must be usable without scraping Markdown or revisiting an inaccessible laptop workbook. Inline small datasets; put large selections in relative `data/*.json` files with fingerprints. Include ordered column definitions and typed values, units/scales/currency, actual versus forecast/scenario identity, periods, entity/market, missing-value treatment, and source pointers per observation or clearly defined common source range. Preserve `0` versus `null`, percent versus fraction, and percentage points versus percentages. Record calculation methods and input/assumption references for derived values. Keep raw numerical values separate from display strings and do not round away material distinctions.

For passages, retain the exact selected wording and locator plus enough nearby context to preserve qualifications. Label generated paraphrases as paraphrases. Do not require the source to be numeric; management commentary or a product description can be legitimate attributed evidence.

References in the output bundle use relative paths, safe IDs, or an unambiguous source locator plus retained selected content and source fingerprint. Copy necessary data selections into the bundle; do not rely solely on an absolute workbook path. Do not redistribute entire licensed source documents merely to make an export portable. Shared raw sources remain in input storage.

Validate IDs, resolved evidence/data references, supported schema versions, finite numbers, rectangular tables, typed missing values, prohibited recursive claim children, and noncircular lineage. Validate semantic scope/measurement compatibility separately. Never derive root confidence by averaging premise labels or multiplying invented probabilities.

Export after meaningful user-visible stops, including Incomplete and Unsupported, so the user can inspect the tree and gaps before a draft exists. A pending scope with no argument yet need not have argument files. Interrupted or failed execution preserves the last valid snapshot and explicitly identifies stale research instead of relabeling it as current.

Write each output bundle into a staged revision, validate both representations and data paths, then publish them together using existing atomic-generation conventions or a small revision-pointer mechanism. Do not expose `argument.md` from one revision alongside `argument.json` from another. A failed export preserves the previous coherent pair. Regenerating Markdown from the same JSON should give the same tree, order, statuses, IDs, assumptions, and values.

## 11. Ownership and evidence boundaries

| Owner | Work in this task |
|---|---|
| Director | CLI, policies, backend adapters, approvals, budgets, persistence, dispatch, terminal formatting. |
| Extractor | File import, existing-command PDF-to-Markdown adapter, filing preparation/indexing, corpus search, context, provenance, coverage. |
| Modeler | Numerical selection/comparison, supported scenario arithmetic, calculation provenance. |
| Inferer | Existing neutral assumptions when relevant; no new Inferer engine. |
| Debater | Argument schema, Planner/Reviewer, question generation, evidence mapping, priority and readiness judgments. |
| Composer | A small pure Markdown-tree renderer; later graphs/prose are outside this task. |

The Markdown renderer must not invoke an LLM, Office, Pandoc, a plotting library, font discovery, or the full company publication pipeline. Reuse or isolate a pure formatting function; avoid eager imports that make Debater depend on unrelated publication tools. Existing `STYLE.md` remains the policy authority; a plain fenced tree uses the viewer's monospace display and introduces no bundled fonts.

Required initial readers cover supplied filing Markdown/plain text, CSV, JSON, PDFs prepared through the reused converter, and existing BAV XLSX/sidecars. Retain original file extensions. The narrow filing-preparation implementation in section 3 is required; a stub that asks for Markdown despite an available authorized converter is insufficient. PDF-to-Markdown preparation is not automatic accounting reconstruction. Scans, complex tables that cannot be reliably read, and broken files produce specific coverage limitations; do not silently claim an empty source was fully searched. Do not add mandatory OCR or a new paid extraction service.

For BAV workbooks prefer validated semantic outputs/sidecars. Use read-only workbook access with sheet/cell locators when needed. Do not run macros or change/recalculate originals; absent or stale formula values require a supported calculation path or an explicit gap. Preserve fiscal dates and geographic definitions. Product styles are not size/color variants; catalog counts are not sales mix; regular and sale prices need separate fields.

Approved inputs are the permitted record, not a declaration that every sentence is true. Distinguish reported observations, management views, external samples, conditional model outputs, user assertions, and user stipulations. Preserve discrepancies and attributable source authority without re-auditing every filing. A stipulated premise can support a conditional argument, not an unconditional empirical conclusion it assumes.

Preserve material contrary evidence and common source lineage. Keep consequential period/peer/definition changes visible to Reviewer. A scenario cannot prove its input assumption, multiple presentations of the same fact are not independent evidence, and favorable results from incompatible scenarios cannot be merged.

Treat imported material as untrusted data, including an added Markdown file. It cannot become an instruction, authorize tools, execute formulas/code, change scope, or disclose credentials. Escape Markdown/HTML/control sequences in generated previews without changing stored quoted content. Never execute LLM-generated shell or Python; validated application functions perform tool work.

Version one is corpus-first and works without automatic online acquisition. Use configured approved connectors only if present and authorized. Do not add a crawler, buy data, bypass access controls, contact people, or propose “approve and fetch” when no such capability exists. A missing external source normally leads to an actionable file request.

## 12. Runtime and bounded search

Use Cursor Agent CLI as the preferred runtime and Codex CLI as an explicitly selectable alternative behind one adapter contract. AutoCycle implements and tests this feature; ordinary Debater research must not invoke AutoCycle, edit code, create Git commits, or use its Office/access/checkpoint machinery. Director owns the research loop independently of provider chat history.

AutoCycle → Cursor/Codex implements and tests repository code. BAV Director/Debater → Cursor/Codex performs product research. Shared installed executables and borrowed architectural ideas do not confer shared runtime dependencies. BAV owns configuration, prompts, session/case state, workspace, permissions, budgets, evidence capture, and lifecycle. Debater must not import from `~/.autocycle`, invoke AutoCycle, or depend on its provider engine, stages, controller lifecycle, instruction database, evidence routes, locks, work-state, observation machinery, policy, budgets, logs, or backend configuration. Cursor remains preferred. Codex remains a separately selectable alternative behind the BAV contract and is unimplemented until demonstrated. Do not silently switch backend or model. Historical Controller permission probes are neither acceptance nor prerequisites.

Inspect installed versions, authentication, supported models, output envelopes, and effective permissions. Do not assume print/headless mode makes an agent read-only or that JSON output validates its research content. Use documented noninteractive execution, check exit/error indicators, parse the final payload, and validate it. Failed provider execution must not be converted into a plausible research result.

Planner and Reviewer use separate contexts through the configured backend, with compact case snapshots and selected source material. A separate review context is not guaranteed independent judgment. Do not create an additional agent per question. Provider output proposes structured requests; BAV validates and executes them.

Use an explicitly configured supported model and record the actual model and runtime version. Reuse authorized subscriptions. Do not silently choose a new paid service, claim unlimited usage, switch provider/model after a failure, or transmit private corpus content under unapproved permissions. `--backend cursor|codex` changes subsequent calls only after the applicable data-sharing policy is satisfied and is saved with the case. Switching does not restart the argument or reset its budget.

Keep the provider in a dedicated workspace with only the context it needs. Enforce effective tool permissions rather than relying on a prompt. No arbitrary agent shell execution, project writes, unrelated MCP tools, or agent-initiated external retrieval. Application-controlled invocation of the verified conversion executable by Extractor is permitted and does not grant shell access to the reasoning agent. Provider transport and authentication are necessary runtime operations, distinct from permission to browse or read additional user data. Isolate BAV runtime configuration from coding-agent project instructions. A source file named `AGENTS.md` remains evidence, not runtime policy.

Test this boundary early with a small synthetic provider probe before building the rest of the loop. If the installed CLI cannot support the required controlled mode, report the specific blocker and available safe choice. Do not solve it with `--force`, unrestricted execution, a rewritten global agent configuration, or a newly billed backend. No new sandbox platform is required merely to keep the chosen CLI at any cost.

Finite initial allowances are one active route, up to three candidate routes, four research batches, twelve backend calls, twenty tool dispatches, and twenty minutes of active work. Count intake, retries, and repair calls within those limits. These are tunable engineering defaults, not evidentiary thresholds. Ask for at most two external evidence items at once and prefer one decisive gap. Reuse completed work; do not fill every allowance.

Process restart and provider switch do not reset allowances. User waiting time does not consume active time. Source preparation also has recorded, bounded limits; perform reusable initial corpus preparation before the benchmark research allowance where possible, and state that accounting explicitly. New evidence continues within the remaining applicable allowance; a specific extension requires approval when exhausted. Technical failures and allowance exhaustion belong under Next, not automatically under Unsupported.

## 13. Durable state and continuation

Use simple local storage and existing repository conventions.

```text
build/input/cases/<safe-case-slug>/
    case.json
    sources/
    extracted/
    revisions/

build/output/cases/<safe-case-slug>/
    argument.json
    argument.md
    data/
```

Durable state includes the original/accepted proposition, current route, claim/question IDs, search coverage, source and model fingerprints, completed results, review disposition, unresolved requests, unavailable routes, pending approval, backend configuration references, and remaining allowance. Store concise decisions and reasons, not private chain-of-thought. Operational history is not the argument shown to Composer.

Use per-case writer serialization and atomic saves. Make Imports idempotent, validate all paths, and preserve filenames in metadata rather than constructing unsafe paths from LLM titles. Save successful stage results and reuse them after interruption. Terminate only child processes owned by this invocation. Do not delete unknown locks or kill unrelated Excel, Word, Cursor, or Codex processes.

New evidence, source corrections, or a changed model snapshot must invalidate affected claim assessments and downstream readiness. A failed import alone does not invalidate an unchanged draft. Keep source/argument versions distinguishable and record which reviewed snapshot each export represents. If recomputation is interrupted, identify the previous package as stale when warranted.

Case input storage and shared research-source Markdown are not disposable build output and must survive ordinary company rebuilds. Document backup implications where `build/input/` is Git-ignored. Register new research-source bundles without rewriting or replacing existing canonical company sources, models, research, or neutral assumptions. Scenario inputs are case-local copies. Do not promise exactly-once paid calls across uncertain crash outcomes; checkpoint known results and diagnose uncertain outcomes instead of blindly repeating them.

If earlier Debater code already writes text trees or charts, change only this feature's future outputs and documented references. Preserve prior reviewed revisions and manually edited files. Do not mass-rename source files, delete legacy artifacts, or leave old exports appearing current after a format change.

## 14. Acceptance and red-team checks

Implement a thin end-to-end path before adding convenience. Reuse existing tests and small labeled fixtures. Mock providers for deterministic behavior tests, then perform a bounded authorized real-backend demonstration. Do not claim a functioning research agent from a canned answer or a mock-only run.

| Test | Required result |
|---|---|
| Markdown opening | An ordinary Markdown preview clearly shows the full claim → linked claims → questions/selected evidence structure without plugins. |
| JSON/Markdown parity | Same revision, ordering, question text, evidence links, assumptions, gaps, and values; Markdown can be regenerated deterministically. |
| Questions visible | Questions under each linked claim are shown before and after evidence arrives, not silently dropped when unresolved. |
| Corpus-first retrieval | Relevant filing Markdown or Modeler data answer questions without asking the user to re-upload or manually re-extract them. |
| PDF/Markdown intake | A supplied filing Markdown bypasses conversion; a PDF uses the verified adapter. Both reach the same source-located retrieval interface. |
| Source identity | PDF and Markdown versions of one filing are not counted as separate confirmation; unsupported page mappings, issuer identities, and dates remain unknown. |
| Preparation failure | Missing executable, unreadable pages, and failed conversion are coverage/capability issues, not negative company evidence. Useful available Markdown remains usable. |
| Preparation reuse | Same source/profile is prepared once; a changed source/version invalidates affected research without modifying the original or accepted financial inputs. |
| Decisive request | The most consequential remaining gap is requested with scope and purpose; a less useful readily available fact does not displace it. |
| Import and resume | Relevant added material updates the same question and argument; duplicate, irrelevant, incomplete, or unreadable files do not falsely resolve it. |
| Evidence unavailable | A note can defer one route and lead to another; absence is not falsity and an indispensable premise is not quietly removed. |
| Linked inference | Well-supported company descriptions without a transfer/counterfactual bridge do not yield Draft for the acquisition claim. |
| Selectivity | A usable case can have few evidence selections and reasonable assumptions; a two-selection count cannot force acceptance. |
| Data portability | JSON contains or resolves the selected data and methods after the bundle is copied, without an absolute machine-specific workbook path. |
| No publication creep | Debate emits no graphs, chart specifications, report paragraphs, `.txt` argument, Word, or PDF and starts without Office/plotting/font tools. |
| Intake and reference | Unclear propositions create no case; ambiguous meanings require approval; title collisions and fragments never select the wrong case. |
| Approval | Changed, stale, duplicate, or concurrently modified plans cannot execute under a previous approval; exclusions concern meanings only. |
| Evidence integrity | Contrary evidence, qualifiers, duplicates/common origins, scenario assumptions, unit/period/geography mismatches remain reviewable. |
| Safety | Added files cannot alter instructions, run code, grant tools, or cause unapproved reads/transmission; provider restrictions are exercised, not merely asserted. |
| Recovery | Interrupted export never publishes a mixed JSON/Markdown pair; stale drafts, edited exports, locks, failed backends, and budgets are handled without data loss. |
| Terminal | Only populated Case/Status/Next fields; colons only on their lines; three one-word research statuses; no provider chatter. |
| Regression | Existing company commands, accepted financial data, and neutral assumptions retain their behavior. |

### Required real benchmark demonstration

Use the exact proposition in section 2, the ordinary CLI, and real local filing sources—not a hard-coded answer. Record the source manifest, actual backend/model, selected passage locators, model-data provenance, commands, resulting status, and `argument.json`/`argument.md` paths in a short `BENCHMARK.md` under the normal Director documentation/verification location. Document inaccessible inputs without exposing unrelated private paths or credentials.

Demonstrate these behaviors:

1. At least one relevant source from each company is registered and searched. Verify a strategy passage from each is retrievable with context. Evidence need not support the proposition to pass retrieval; report whether it supports, challenges, or merely supplies context.
2. Test direct Markdown intake and at least one real PDF-to-Markdown conversion through the actual installed command when the dependency and PDF exist. Compare a selected passage and any consequential selected table to the original representation. Do not simulate the live converter and report it as integration success.
3. Produce a compact linked argument with retained research questions, sourced answers/data, explicit assumptions, and the most decisive genuine gap. Reflect Japan and Greater China separately; do not require identical claims or data availability in both.
4. In an isolated benchmark case with a recorded partial initial corpus, add an existing withheld real source through `--add` and resume. Confirm the new source is evaluated against the affected questions; it need not cause Draft or reverse a verdict. Label the staged withholding in the benchmark report and do not delete or hide canonical company inputs. Use full available sources for the final benchmark result.
5. Repeat an unchanged resume/status read and verify that it does not reconvert the sources or rerun paid reasoning. Add a small differently worded or negated proposition fixture to check that the implementation has not memorized the acquisition example.

Report the supported outcome, including Incomplete when that is correct. A technically working feature may finish this benchmark without proving the acquisition thesis. Conversely, missing source files or unavailable converter/provider capability do not count as a passed end-to-end benchmark. Record verified portions and the exact blocker, ask for the missing file or decision, and stop the affected route without endless retries. Continue independent implementation work that does not require that dependency. Synthetic data are allowed only in clearly marked tests, never in the real company corpus.

Run focused tests during development, then concretely affected regressions. Do not repeatedly rebuild all workbooks, rerun full certification, or launch native Office for a tree/CLI change. Do not weaken existing required checks; record pre-existing failures separately. If a provider is unavailable, mark that integration unverified rather than claiming both backends passed.

## 15. Decisions the implementation agent must not guess

| Boundary | Required behavior |
|---|---|
| Missing model/authentication or incompatible provider permissions | Report the actual one-time choice or blocker; never enable unrestricted execution or an unapproved paid alternative. |
| Missing source, unreadable document, or ambiguous catalog coverage | Inspect the approved local corpus and converter first; preserve unresolved gaps and ask for specific material/context, not invented data. |
| Converter flags, source edition, missing runtime models, or new extraction services | Verify installed tooling and document identity; reuse an approved working command, request a missing capability decision, and never silently upgrade/install or transmit sources elsewhere. |
| Materially different proposition, market, horizon, or beneficiary | Require resubmission or the specified scope approval; never weaken or expand the claim silently. |
| New source access, provider transmission boundary, or cost allowance | Present a finite approval request. Mere approval of the argument does not grant it. |
| Unknown user changes, legacy state, or lock ownership | Preserve the work and report the conflict; do not reset, stash, overwrite, or clear it blindly. |

Routine schema, function, and test organization belongs to the implementer. Do not ask the user to make every technical choice, and do not invent features to avoid a genuine missing capability.

The brief closes the main design ambiguities: questions are visible evidence-layer organizers; Markdown and JSON are one representation in two formats; missing evidence differs from contradiction; principal selections are data rather than charts; and material obligations cannot be pruned to manufacture support. Semantic judgment remains fallible and must be demonstrated against the adversarial fixtures, not certified by schema validation alone.

## 16. Handoff and exclusions

Deliver the implemented commands, one-time provider/converter setup only where required, the primary Asian-growth benchmark `argument.json`/`argument.md` pair and selected data, the source/conversion manifest, `BENCHMARK.md` evidence, and truthful remaining limitations. State which company source files were found and which still need to be supplied. Human-readable setup, examples, and diagnostics use Markdown. No added text-file argument output.

Do not modify AutoCycle, bypass its state/verification controls, rename BAV, revive Interpreter/Core, add a chat interface, database service, theorem prover, general crawler, recursive reasoning ontology, graph renderer, new forecasting engine, or report composer. Future Composer publication is a separate task.

Inspect installed tool help and current official documentation rather than assuming remembered flags:

- Existing PDF-to-Markdown tooling — inspect the local wrapper and `marker_single --help`; upstream reference `https://github.com/datalab-to/marker` (version-dependent options).
- Cursor headless mode — `https://cursor.com/docs/cli/headless`
- Cursor permissions — `https://cursor.com/docs/cli/reference/permissions`
- Codex noninteractive mode — `https://developers.openai.com/codex/noninteractive`
- Codex security — `https://developers.openai.com/codex/security`

These pages concern runtime integration, not a guarantee of factual or logical correctness. The acceptance criteria above concern the product behavior agreed with the user.
