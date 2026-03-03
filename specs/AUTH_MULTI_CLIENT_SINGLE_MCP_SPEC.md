# Spec: Single-MCP Multi-Client Authentication

**Status:** In Implementation  
**Owner:** Codex  
**Plan Link:** `/Users/david.helmus/repos/ai-dev/_infra/gws-mcp-advanced/gws-mcp-advanced/agent-docs/roadmap/AUTH_STABILIZATION_PLAN.md`

## Problem
One MCP server must support multiple OAuth client configurations (enterprise + private tenants) with strict isolation and no cross-client fallback.

## Goals
1. Keep one MCP entry in client tools.
2. Route OAuth client by account/domain in-process.
3. Enforce hard-fail on mapping/domain mismatch.
4. Isolate credentials and session state by `(oauth_client, user_email)`.
5. Support headless-safe completion via `start_google_auth` + `complete_google_auth`.

## Configuration Model
Path: `WORKSPACE_MCP_CONFIG_DIR/auth_clients.json`

```json
{
  "version": 1,
  "selection_mode": "mapped_only",
  "default_client": null,
  "oauth_clients": {
    "work": {
      "client_id": "xxx.apps.googleusercontent.com",
      "client_secret": "yyy",
      "allowed_domains": ["hellofresh.com"],
      "flow_preference": "auto"
    }
  },
  "account_clients": {
    "alice@hellofresh.com": "work"
  },
  "domain_clients": {
    "hellofresh.com": "work"
  }
}
```

## Resolution Precedence
1. Internal/admin override (`override_client_key`).
2. `account_clients[user_email]`.
3. `domain_clients[email_domain]`.
4. `default_client` (only when `selection_mode != mapped_only`).
5. Legacy env fallback (`GOOGLE_OAUTH_CLIENT_ID/SECRET`) only when multi-client config is effectively unconfigured.

## Hard-Fail Rules
1. In `mapped_only`, missing mapping is an error once config is configured.
2. If mapped client profile is missing, fail.
3. If `allowed_domains` does not include target domain, fail.
4. Never fall back to another mapped client on mismatch.

## Storage / Session Model
1. Credentials: client-scoped path with legacy read-through migration.
2. OAuth states: persist `oauth_client_key`, `expected_user_email`, and `redirect_uri`.
3. Pending device flows: key by `(oauth_client_key, user_email)`.
4. Session mappings: persist optional MCP session -> `oauth_client_key`.

## Tool/API Contract
1. `start_google_auth(service_name, user_google_email)`:
   - resolves mapped client,
   - creates challenge state with client metadata,
   - returns actionable auth URL.
2. `complete_google_auth(service_name, user_google_email, callback_url?, authorization_code?, state?)`:
   - primary input: `callback_url`,
   - fallback input: `authorization_code + state`,
   - validates state and expected user/client binding,
   - exchanges token and persists credentials/session.
3. Setup/admin tools:
   - `setup_google_auth_clients()`
   - `import_google_auth_client(...)`

## Migration
1. Keep legacy env-only auth functional while auth client config is empty/unconfigured.
2. On client-scoped lookup miss, read legacy flat credential file and migrate into client-scoped storage.
3. Maintain legacy config-dir fallback already implemented (`gws-mcp-advanced` -> canonical path).

## Acceptance
1. Two mapped accounts on two different OAuth clients authenticate in one MCP process.
2. Work account cannot authenticate against private client (hard-fail).
3. Existing env-only deployments continue to authenticate without immediate config migration.
4. `complete_google_auth` succeeds in MCP-hosted lifecycle where browser callback race exists.
