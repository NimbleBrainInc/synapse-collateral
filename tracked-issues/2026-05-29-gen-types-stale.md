## [TRACKED] gen-types.py is broken; ui/src/types.ts is stale
**Type**: bug | debt   **File**: scripts/gen-types.py, ui/src/types.ts   **Priority**: med
**Found during**: patch_source supervisor-trip fix (source_sha)

**Description**: `scripts/gen-types.py` imports models that no longer exist in
`src/mcp_collateral/models.py` (`ExportResult`, `PagePreview`, `PreviewResult`,
`SectionState`, `VariableDefinition`) and dies with ImportError, so it cannot
regenerate `ui/src/types.ts`. The committed `ui/src/types.ts` is consequently
out of sync with the Pydantic models — e.g. `WorkspaceState` in types.ts still
carries `source`, `sections`, `has_cache` (gone from the model) and lacks the
fields the model now has. The UI compiles only because it reads a subset.

**Suggested approach**: Reconcile the gen script's import list with the current
models, regenerate `types.ts`, and add a CI check (or pre-commit) that fails on
codegen drift. Until then, types.ts edits must be made by hand (as the
source_sha addition was).
