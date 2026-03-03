# Authentication Pattern Review: `gogcli` vs `google-workspace-mcp-advanced`

- Status: `REVIEW_COMPLETE`
- Last Updated (UTC): `2026-03-03T08:20:06Z`
- Scope: single MCP server supporting private + enterprise tenants with different OAuth clients/auth patterns

## Why This Review Exists

You want one MCP server entry (not two separate MCP configs) that can authenticate and operate across:
1. private Google Workspace/Google account contexts, and
2. enterprise Google Workspace contexts with stricter OAuth allow/deny rules.

This document captures what currently works, what does not, what `gogcli` already solves, and what we can adopt.

## External Reference Reviewed (`gogcli`)

Primary sources:
1. [gogcli README](https://github.com/steipete/gogcli)
2. [gogcli auth clients doc](https://raw.githubusercontent.com/steipete/gogcli/main/docs/auth-clients.md)

Notable capabilities (from repository docs/README):
1. Multiple OAuth clients are first-class (`--client <name>` / `GOG_CLIENT`).
2. Tokens are isolated per `(client, email)` bucket.
3. Client selection supports precedence rules:
   1. explicit client override,
   2. account-to-client mapping,
   3. domain-to-client mapping,
   4. domain-based credential filename fallback,
   5. default client.
4. Headless-safe auth flows exist:
   1. manual flow (`--manual`) where user pastes redirect URL back,
   2. split remote flow (`--remote --step 1/2`) with persisted state and explicit callback URL handoff.
5. Service account auth can coexist and take precedence where configured.

## Current MCP Reality (Codebase Truth)

Current design in this repo:
1. OAuth client is process-global and loaded from env (`GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET`), not per account.
   - See `auth/google_auth.py` and `auth/config.py`.
2. Credentials are stored per email in local files, but auth challenge generation still uses global client env.
3. `auto + stdio` currently prefers device flow and can fail with Web OAuth clients (`invalid_client`) until fallback logic lands (AUTH-R2).
4. Session binding protects against cross-user misuse, but binding currently does not include a client dimension.

Implication:
1. One running MCP process cannot currently choose between two different OAuth client IDs/secrets dynamically by account/domain.

## What Works Today

With one MCP process:
1. Multi-account works if all accounts can authenticate against the same OAuth client project.
2. Credential/session reuse and refresh behavior works for previously authorized accounts (subject to token validity and scope checks).
3. Callback mode works in stdio (`WORKSPACE_MCP_AUTH_FLOW=callback`) as interim reliability path for Web clients.

## What Does Not Work Today

1. One MCP process with two different OAuth client JSONs selected automatically by tenant/domain.
2. Per-account/per-domain auth-client routing during auth challenge.
3. Mixed auth patterns per account (for example one account on callback-only client profile and another on device-capable profile) under a single shared global client config.

## Can We Learn from `gogcli`?

Yes. The core transferable idea is:
1. separate **account identity** from **OAuth client identity**,
2. make client selection deterministic and explicit,
3. isolate token/session state by `(client, account)`.

## Recommended MCP Design (Single Server, Multi-Tenant)

### 1) Add OAuth Client Registry

Store named OAuth clients in config dir, for example:
1. `<config>/oauth-clients/default.json`
2. `<config>/oauth-clients/work.json`
3. `<config>/oauth-clients/private.json`

Each file contains client metadata:
1. `client_id`
2. `client_secret`
3. optional policy hints (`allowed_domains`, `flow_preference`)

### 2) Add Client Selection Rules (gog-style precedence)

When a tool call needs auth for `user_google_email`, resolve client in this order:
1. explicit tool/server override (future parameter or env override),
2. account-to-client map (`account_clients`),
3. domain-to-client map (`client_domains`),
4. default client.

### 3) Partition Credential Storage by Client

Replace flat per-email token path with client-aware storage:
1. option A: `<config>/credentials/<client>/<email>.json`
2. option B: `<config>/credentials/<client>__<email>.json`

This prevents enterprise/private token mixing and refresh confusion.

### 4) Bind Sessions to `(client, account)`

Extend OAuth session mapping and security checks to include client key:
1. binding tuple = `(mcp_session_id -> client_name + user_email)`,
2. reject requests that try to resolve credentials for a different client than bound.

### 5) Add Headless-Friendly Manual Completion API

Adopt `gogcli`-like split flow for MCP-hosted environments:
1. `start_google_auth` returns URL + state and persists pending challenge,
2. `complete_google_auth` accepts full callback URL (or code/state), validates persisted state, exchanges token.

This avoids relying exclusively on a live localhost callback server inside tool-call timing windows.

### 6) Keep Device/Callback Fallback in Auto Mode

For `auto` mode:
1. try device flow,
2. if provider returns `invalid_client` (Web app client), fallback to callback/manual completion,
3. emit deterministic guidance to the LLM/user.

## Expected Enterprise Impact

This design addresses enterprise constraints:
1. enterprise users blocked from external OAuth clients can map to enterprise-owned client profile,
2. private users can map to private client profile in same MCP instance,
3. no need for two separate MCP server entries in client config.

## Risks / Tradeoffs

1. Migration complexity from current flat credential layout.
2. Additional test matrix:
   1. per-client credential isolation,
   2. per-client refresh,
   3. session binding enforcement with client dimension,
   4. mixed flow modes per client profile.
3. Backward compatibility: existing env-only setup must continue to work as legacy default client.

## Implementation Readiness Verdict

Verdict: `READY_FOR_SPEC`.

## Validated vs Unvalidated

Validated (code/doc truth):
1. Current MCP auth client selection is process-global and env-driven.
2. Current storage/session model is not client-aware.
3. `gogcli` publicly documents first-class multi-client routing and per-client token isolation patterns.
4. Policy decision is now locked for target implementation: `selection_mode=mapped_only`, hard-fail on domain/client mismatch, and no cross-client fallback.
5. Setup flow decision is now locked: auto-bootstrap `auth_clients.json` skeleton plus explicit OAuth client import path for secrets.
6. Additional policy decisions are locked: explicit client override is internal/admin-only, and `complete_google_auth` uses hybrid input (`callback_url` primary, optional `code/state` fallback).

Unvalidated assumptions requiring explicit spec decisions:
1. Exact migration strategy for existing flat credential files and rollback semantics.

Required before coding:
1. Define config schema for `oauth-clients`, `account_clients`, `client_domains`.
2. Define migration behavior for existing credentials and sessions.
3. Define MCP tool contract changes (`start_google_auth` / `complete_google_auth`).

## Suggested Next Work Item

Create `specs/AUTH_MULTI_CLIENT_SINGLE_MCP_SPEC.md` with:
1. data model,
2. storage layout,
3. selection algorithm,
4. API/tool contract changes,
5. migration and rollback plan,
6. acceptance test matrix.
