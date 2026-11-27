# Design-to-delivery implementation and verification

Implemented against the existing working tree; unrelated edits and creative projects retained. Shared Skills installed under `.agents/skills` with pre-update backups and verified source hashes.

## Requirements and evidence

| Requirement | Implementation | Verification |
|---|---|---|
| Full design reaches executable shots | Stable DESIGN codes; design_intent, timing, reaction, sound_cues, composition, lighting, graphics; complete scoped inputs | test_storyboard_contract_v2, test_creative_context, test_creator_context |
| Markdown, browser and CLI agree | Shared v2 contract and multiline parser; legacy action aliases; lossless qualified visual_basis; bound rename updates | test_storyboard_sync, test_documents, test_library, test_entries; browser save/reload/undo/redo; exported browser edit read by installed standalone context helper |
| Context uses current authored content | Complete current records and immediate neighbors; imported baselines and stale raw fields excluded | test_creative_context; task revision and new-child conflict tests |
| Asset decisions remain linked | Image prompt design/identity references; adopted asset owner dependencies | test_design_dependencies |
| Production preserves actual inputs | Full owned documents in execution workspace; immutable creative snapshots and media provenance; frozen coverage used on collection | test_production; test_entry_prepare; local fixture submission and browser historical-context display |
| Design reaches editing | DESIGN handoff requirements and shot links; design IDs on CUTs; cut-binding dependencies; front-end documents projected into managed OpenFilm workspace | test_editing and handoff.test.mjs with actual local OpenFilm initialization |
| Editing cannot silently use stale design | Managed-source semantic check; refresh when opened from director desk; authored manual changes preserved; managed source views read-only in OpenFilm | test_editing verifies source changes, refresh, unchanged film and preserved conflicting manual edits |
| Usable storyboard interface | Sequential reading; grouped multidimensional table; design text beside editable shot; contextual term controls; frozen production trace | Browser checks on isolated station/ticket fixture, source edit persists across reload and undo/redo; Vite build |
| Runtime and installed parity | 32 changed Skill files hash-match repository; current director service and plugin health verified | installed-manifest.json in local QA cache; live contract v2 and build ID; live OpenFilm plugin build |

## Executed checks

- Full director backend: 140 tests passed. Subsequent plugin-runtime and server checks: 12 passed.
- Shared document regressions: 12 passed; entry editor: 3 passed; context extraction: 1 passed; production entry: 4 passed.
- Main Skill self-test: 17; production self-test: 8; editing self-test passed.
- Frontend tests: stage controls/editing (8), contract connection (2); Vite production build passed.
- OpenFilm handoff test passed; tests also initialize a native local OpenFilm project and verify design metadata and stale-source detection.
- Local links in changed Markdown resolve.

Browser QA and local generated fixtures validate the data/workflow, not AI artistic quality. No paid model calls were used for this optimization. Current video projects were not rewritten. The old director service was restarted after the user explicitly confirmed their work was saved.

Local evidence and pre-install copies: `~/.short-drama/cache/design-throughline-qa-20261127/`. Existing build-size warnings remain unchanged.
