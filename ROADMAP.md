# Product Roadmap

## Metadata
- Last Updated (UTC): 2026-03-02T22:35:00Z
- Canonical Execution Plan: `agent-docs/roadmap/PLAN.md`
- Canonical Manual Matrix: `agent-docs/testing/OPENCODE_MCP_MANUAL_TESTING.md`

## Current State

### Completed Roadmap Closures (Wave 3)
1. `RM-01` Code-block rendering parity: complete.
   - Evidence: OpenCode `OP-68` PASS.
2. `RM-02` Table reliability: complete.
   - Evidence: multi-table and preceding-content integration regressions plus manual extended-matrix PASS.
3. `RM-03` Task-list trailing bullet regression: complete.
   - Evidence: OpenCode `OP-67` PASS.
4. `RM-04` Markdown image rendering regression: complete.
   - Evidence: OpenCode `OP-69` PASS (visual confirmation).
   - Note: `inspect_doc_structure` does not surface inline image objects reliably for this scenario; visual verification is authoritative for image presence.

### Deferred Platform Item (Non-Blocking)
1. Programmable Search Engine (`search_custom`) enablement.
   - Status: Deferred by product decision.
   - Scope: `GOOGLE_PSE_API_KEY` + `GOOGLE_PSE_ENGINE_ID`.
   - Reason: web-search coverage currently provided by other MCPs.
   - Revisit trigger: when unified web-search routing through this MCP becomes a product requirement.

## Next Roadmap Focus
1. Rename and migration hardening (`DIST-05`):
   - Complete canonical naming cleanup in runtime defaults/docs/tests
   - Keep legacy config directory compatibility with explicit migration guidance
2. Smart-chip extension stream (`RM-05`..`RM-07`):
   - Native checklist bullets
   - Mention-to-chip mapping
   - Add-ons-backed third-party chips feasibility

## Closure Notes
1. Markdown formatting is no longer an active roadmap risk area.
2. Historical design exploration for markdown parsing is preserved in commit history and specs; this roadmap now tracks only forward-looking work.
