# Step 10.12.1 — Compare representative company outputs against B

## Completion

Director owns CLI routing, company configuration and company build/check/publication orchestration, with mechanical build status owned by Modeler, while public interfaces and existing execution behavior remain preserved.

AUTOCYCLE_PLAN: {"evidence_routes": [{"commands": [["/opt/anaconda3/bin/python", "-m", "bav", "build", "Lululemon"], ["/opt/anaconda3/bin/python", "-m", "bav", "check", "Lululemon"], ["/opt/anaconda3/bin/python", "-m", "bav", "publish", "Lululemon"], ["/opt/anaconda3/bin/python", "-m", "bav", "build", "FastRetailing"], ["/opt/anaconda3/bin/python", "-m", "bav", "check", "FastRetailing"], ["/opt/anaconda3/bin/python", "-m", "bav", "publish", "FastRetailing"], ["/opt/anaconda3/bin/python", "-m", "pytest", "-q", "core/tests/test_current_build.py", "core/tests/test_publication.py"]], "fact": "Whether representative Lululemon and FastRetailing build/check/publication outputs preserve baseline B behavior under equivalent inputs."}], "finding_key": "Relocate CLI and company orchestration", "kind": "work", "minor": 1, "objective": "Compare representative company outputs against B", "plan_id": "38e6f227c15b488eb6a3c8d4ff3e1793", "predecessor_review_sha256": "3a5d8de4f33aede968617f319a6d2ef47c78aa518a0ab5b404adfc1be0d8a593", "step_id": "10.12.1", "work_id": "889f7a7b0342467caa4faf6315b52b88"}

## Bounded work

Resolve the representative comparison required by the parent plan. Retain completed relocation, compatibility façades, canonical callers and ownership documentation.

Unresolved fact: Whether representative Lululemon and FastRetailing build/check/publication outputs preserve baseline B behavior under equivalent inputs.

Criterion: IMPLEMENTATION.md explicitly requires comparison with B to verify existing execution behavior is preserved.

- Authenticate the execution baseline through populated `IMPLEMENT_BASE_SHA`, otherwise normal baseline and bound-attempt mechanisms. Verify branch, ancestry and checkpoint bindings; fail closed on missing authentication.
- Preserve the reviewed attempt’s authenticated comparator B, `2d272b7fdb4c0ab8bcabbcd50ef1efc357d181b3`, bound to attempt `1aeed994c57844349b2e9c09e53ab487` and checkpoint `d3629419e6120ce815841bf1a37f65f06c092152`. Distinguish this comparator from any new continuation baseline.
- Materialize B and the current candidate from Git into separate disposable directories. Inspect B’s historical blobs before using current canonical destinations. Keep the working repository, canonical outputs and controller evidence untouched.
- Supply identical copies of the existing canonical company inputs and referenced fixtures to both directories; record source paths and hashes. Verify their immutability afterward. Missing required inputs remain unresolved.
- Use the same Python installation, dependencies, fonts and environment for both executions. Run the six company commands above from each isolated repository root, recording exit codes, stdout, stderr and generated output locations.
- Compare actual B-generated and current-generated artifacts for both companies. Passing tests on both revisions and preserved source bytes do not substitute for this comparison.

## Output comparison

- Compare relative output inventories, supporting JSON, research Markdown, figure contents and zero-byte placeholders. Compare check diagnostics and exit behavior, accounting for only explicitly identified temporary-root differences.
- Compare XLSX ZIP member inventories and decompressed payloads, including workbook formulas, values, styles, relationships and embedded provenance. Inspect every differing member; distinguish archive timestamps and demonstrated volatile document metadata from analytical or presentation differences.
- Reuse `_word_member_diffs`, `_publication_diff` and `_pdf_documents_equal` from `core/tests/test_publication.py` for the two generated DOCX/PDF pairs. Record content, layout and metadata differences separately; do not broadly discard document properties or unexplained differences.
- Use existing check helpers and finite inspection commands without adding a verifier framework or AutoCycle infrastructure. Record the exact comparison invocations and results.
- Run the listed current-build and publication tests against the current candidate after generation. Retain applicable evidence for the completed 616-test run; rerun affected portions of the parent suite if a demonstrated defect requires a repair.
- Repair only a demonstrated relocation defect preventing this Completion, then repeat the affected paired comparison. Do not weaken, skip, deselect or xfail preserved gates.

## Preservation and recording

Preserve CLI contracts, aliases, patchable configuration, explicit JSON/Excel routes, optional Trainer behavior and ordinary execution’s independence from Legacy.

Preserve source immutability, strict standardized preparation, protected outputs, staged verification, sidecars, atomic replacement, failure rollback, provenance, analytical results, residual qualifications, dormant forecasting and research placeholders.

Retain normalization fingerprint, adoption, treatment, authorization, persistence, once-only conversion, isolated comparisons, lifecycle rejection coverage and all 11-observation round trips. Admission remains default-off and independent of ordinary reconciliation and comparison.

Apply SESSION’s Office Bridge requirements if workbook formulas/dependencies or presentation change. Reuse prior verification only while its dependencies remain applicable.

Run `git diff --check` and the corresponding diff check against the authenticated execution baseline. Append bindings, input hashes, output inventories, comparison results, measured checks and unresolved defects to `RESULT.md`; preserve historical records. Distinguish this Completion from unfinished Session migration.

Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
