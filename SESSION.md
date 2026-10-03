# BAV Compiler — Six-component Architectural Migration

Session: 11

## Endpoint

Complete and verify the ownership and filesystem migration so all active BAV implementation belongs to exactly one of `bav/director/`, `bav/extractor/`, `bav/modeler/`, `bav/inferer/`, `bav/debater/` and `bav/composer/`, preserving useful existing behavior and public `bav` interfaces.

Session acceptance requires:

- A complete responsibility inventory precedes movement and assigns every meaningful responsibility to one canonical component, Legacy, Remove or Runtime-tooling; mixed files are split by decision type.
- No active Core, Interpreter, replacement generic layer or duplicate top-level implementation remains. Interpreter is decomposed rather than renamed wholesale; Core is distributed rather than moved wholesale into Director.
- Director owns governance/orchestration and system-wide specifications; Extractor owns source-faithful evidence/provenance; Modeler owns the complete historical/prospective quantitative model; Inferer owns neutral/base assumptions; Debater owns stance-conditioned assumptions and case construction; Composer owns communication/publication without originating assumptions or substantive conclusions.
- Management guidance remains evidence, not authority or a mechanically copied base case. Reported facts, management views, historical tendencies, inferred assumptions and uncertainty remain distinguishable. Assumption origin and stance are explicit; Debater cannot silently overwrite canonical neutral/base assumptions and may use Extractor/Modeler directly.
- `build/` and `legacy/` remain at root. Only minimal README and genuinely required packaging/Git/AutoCycle/tooling files otherwise remain outside `bav/`; root retention is justified and AutoCycle document locations remain functional. Trainer remnants receive explicit dispositions.
- Active components do not depend on Legacy as a hidden implementation layer. Imports, exports, CLI routing, tests, documentation, resource paths and build/publish paths match canonical ownership.
- Relevant tests and representative Lululemon/Fast Retailing builds, checks and publications pass; useful optional Trainer behavior survives. RESULT.md records mapping, splits, intentional root retention, removals, verification and unresolved ambiguities.
- Stop after verified structural migration. Do not build sophisticated Inferer/Debater engines, new methods or LLM workflows, redesign Extractor/Composer, unnecessarily rewrite quantitative logic or cosmetically refactor Legacy.

## Priority

1. Inspect the complete repository and inventory responsibilities before movement, especially Interpreter, Core, Driver/research, current `bav`, top-level components, root Markdown and Trainer remnants.
2. Execute inventory-led splits and relocation into the six canonical packages; update references, preserve useful behavior, establish minimal missing boundaries and remove justified obsolete material.
3. Verify ownership, assumption separation, Legacy independence, representative behavior and relevant regressions; resolve migration defects and record evidence.

Preserve canonical source evidence, accounting signs, fiscal distinctions, precision, reconciliations, provenance, admission/comparison independence, residual qualifications, fail-closed controls, default-off normalization admission and zero-byte research placeholders. Deferred accounting and future product obligations remain deferred, not completed.

Use authenticated implementation baseline B and historical Git blobs, then canonical destinations, provenance continuity and current verification. Git preserves tracked history; protect irreplaceable non-Git evidence through verified canonical continuity before removal. Preserve normal ownership, recovery, protected-document and unrelated-dirty-work safeguards.

Reuse verification only where dependencies remain applicable. Changed workbook formulas/dependencies require native recalculation and independent saved-cache verification; changed presentation requires readability inspection. Native Office work uses Office Bridge and existing access controls. Never claim later verification proves an earlier gate ran.

Instruction incorporation is not acceptance; DONE requires this Session Endpoint and current plan acceptance.
