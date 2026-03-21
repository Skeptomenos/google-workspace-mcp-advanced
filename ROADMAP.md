# Product Roadmap

## Metadata
- Last Updated (UTC): 2026-03-17T09:20:00Z
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

### Deferred Auth Follow-up (Non-Blocking)
1. Phase 3 OAuth Topology Refactor.
   - Status: Deferred by product priority; current auth behavior is stable through `v1.0.10`.
   - Scope: separate stdio/local auth from provider/HTTP auth, remove remaining steady-state
     error-driven fallback, and shrink `auth/google_auth.py` into a thin facade.
   - Canonical plan: `docs/plans/2026-03-17-phase-3-oauth-topology-refactor.md`
   - Revisit trigger: when auth topology work is explicitly pulled forward.

## Next Roadmap Focus
1. Smart-chip extension stream (Wave 8):
   - `RM-05`: done (`checklist_mode` with `unicode` default and `native` opt-in)
   - `RM-06`: done (`mention_mode` with `text` default and `person_chip` opt-in)
   - `RM-07`: deferred (Add-ons-backed third-party smart chips remain out of scope under current no-external/third-party dependency policy)
2. Deferred Apps Script follow-up:
    - `APPS-07`: cross-project execution UX hardening (non-blocking, pull-forward only)
3. Autonomous verification operations:
    - Wave 4 cleanup/cadence automation is in place (`scripts/mcp_live_cleanup.py` + `.github/workflows/live-mcp-cadence.yml`)
4. Auth stabilization closeout:
   - `SPEC-11` Phase 1/2 is complete and released.
   - Remaining auth work is the deferred Phase 3 refactor only.

## Closure Notes
1. Markdown formatting is no longer an active roadmap risk area.
2. Historical design exploration for markdown parsing is preserved in commit history and specs; this roadmap now tracks only forward-looking work.
