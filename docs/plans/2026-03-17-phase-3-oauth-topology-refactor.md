# Phase 3 OAuth Topology Refactor

**Status:** Deferred follow-up  
**Priority:** Medium  
**Last updated:** 2026-03-17  
**Depends on:** `SPEC-11.md`, `v1.0.10`, green auth regression matrix  
**Related docs:** `docs/plans/2026-03-12-deterministic-oauth-callback-reliability.md`, `SPEC-11.md`, `agent-docs/roadmap/AUTH_STABILIZATION_PLAN.md`

## Why this exists

Phase 1 and Phase 2 solved the active auth reliability problem and extracted the key policy/state seams.
Current auth behavior is stable and released, but one structural knot remains: stdio/local auth and
provider/HTTP auth still share too much orchestration inside `auth/google_auth.py`.

This document is the dedicated follow-up plan for that remaining refactor work. It is intentionally
separate from `SPEC-11.md` so the Issue #11 fix can stay closed while future structural work remains
well scoped.

## Current baseline

- Released baseline: `v1.0.10`
- Phase 1 and Phase 2 are implemented and verified
- Auth behavior is protected by `tests/integration/auth/test_auth_matrix.py`
- This refactor is deferred until auth topology work is explicitly pulled forward

## Goals

1. Separate stdio/local auth orchestration from provider/HTTP auth orchestration.
2. Remove remaining error-driven steady-state fallback and ambiguous re-resolution branches.
3. Reduce `auth/google_auth.py` to a thin compatibility facade.
4. Make supported auth topologies explicit in code, tests, and docs.

## Non-goals

1. Adding new user-facing auth tools or flags.
2. Reopening Phase 1 or Phase 2 bug-fix behavior.
3. Broad tool-surface changes outside auth orchestration.
4. Shipping this work opportunistically while auth is already stable.

## Entry criteria

Start this phase only when all of the following are true:

1. The current auth matrix is green on the starting branch.
2. There are no unresolved auth regressions from Phase 1 or Phase 2.
3. Full repo verification is green before refactor work starts.
4. The work is explicitly pulled forward as a product/maintenance priority.

## Task 13: Split stdio and provider/HTTP orchestration

**Files:**
- Create: `auth/stdio_auth.py`
- Create: `auth/http_auth.py`
- Modify: `auth/google_auth.py`
- Modify: `core/server.py`
- Modify: `auth/service_decorator.py`
- Modify: `auth/external_oauth_provider.py`
- Create: `tests/integration/auth/test_topology_boundaries.py`

**Implementation:**
- Move stdio-oriented auth challenge start/completion, local callback use, and manual completion
  handling into `auth/stdio_auth.py`.
- Move provider/HTTP orchestration into `auth/http_auth.py` and make it the only place that bridges
  to provider-specific behavior.
- Keep `auth/google_auth.py` as a compatibility facade during the transition, but make it delegate
  immediately instead of owning the full decision tree.
- Add integration coverage proving:
  - stdio auth can complete manually without provider configuration
  - provider/HTTP auth does not start the local callback server as an implicit fallback

**Verification:**

```bash
uv run pytest tests/integration/auth/test_topology_boundaries.py -v
```

**Definition of done:**
- The top-level auth architecture reflects two explicit topologies instead of one giant conditional
  tree.

## Task 14: Remove error-driven fallback and ambiguous runtime branches

**Files:**
- Modify: `auth/flow_policy.py`
- Modify: `auth/google_auth.py`
- Modify: `auth/oauth_clients.py`
- Modify: `tests/unit/auth/test_flow_policy.py`
- Modify: `tests/integration/auth/test_auth_matrix.py`

**Implementation:**
- Remove any remaining steady-state logic that treats provider errors such as `invalid_client` as a
  normal way to decide auth flow.
- Make `auto` mean deterministic capability-based selection only.
- Remove ambiguous runtime branches that re-resolve client/redirect context after a challenge is
  already persisted.
- Preserve explicit upgrade or repair messages where old behavior is no longer supported.

**Verification:**

```bash
uv run pytest tests/unit/auth/test_flow_policy.py tests/integration/auth/test_auth_matrix.py -v
```

**Definition of done:**
- Auth flow selection is deterministic before any request is sent to Google.

## Task 15: Shrink `auth/google_auth.py` and delete dead compatibility branches

**Files:**
- Modify: `auth/google_auth.py`
- Modify: `auth/ARCHITECTURE.md`
- Modify: `docs/setup/AUTHENTICATION_MODEL.md`
- Modify: `docs/RELEASE_NOTES.md`

**Implementation:**
- Remove dead helpers and compatibility branches that become unnecessary after Tasks 13 and 14.
- Update docs so the supported boundaries are explicit:
  - stdio auth
  - provider/HTTP auth
  - multi-client mode
  - legacy compatibility mode
- Document any remaining migration path for operators still using legacy layouts.

**Verification:**

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

**Definition of done:**
- `auth/google_auth.py` is a thin facade rather than the main policy engine.

## Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Cross-topology regression while moving orchestration | High | Add topology-boundary integration tests before moving branches |
| Refactor expands beyond auth orchestration | Medium | Keep the phase limited to topology separation and dead-branch cleanup |
| New code reintroduces flow ambiguity | High | Make `flow_policy.py` and the auth matrix the blocking verification source |
| Review becomes too large | Medium | Split delivery into 2-3 PR slices with passing tests after each slice |

## Suggested PR slices

1. Topology split (`auth/stdio_auth.py`, `auth/http_auth.py`, boundary tests)
2. Deterministic flow cleanup (remove error-driven fallback and ambiguous re-resolution)
3. Facade/doc cleanup (`auth/google_auth.py` shrink + documentation reconciliation)

## Exit criteria

1. `auth/google_auth.py` is a thin facade rather than the main policy engine.
2. The auth topology is explicit in code, tests, and docs.
3. Remaining compatibility behavior is deliberate, narrow, and documented.
4. Full repo verification passes after the final slice.
