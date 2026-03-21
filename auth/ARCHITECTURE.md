# Auth Module Architecture

## Current State (Phase 2 complete)

### Module Overview

The auth module handles OAuth 2.0/2.1 authentication for Google Workspace APIs.
It supports both single-user and multi-user modes with MCP session binding.
Auth policy decisions are owned by small, pure, typed modules extracted in Phase 2.

### File Structure

```
auth/
├── __init__.py                 # Public API exports
├── interfaces.py               # Abstract base classes
├── auth_plan.py                # Typed auth decision contracts (ResolvedAuthPlan)
├── flow_policy.py              # Pure flow-selection rules (resolve_auth_flow_plan)
├── redirect_policy.py          # Pure redirect rules (resolve_redirect_policy)
├── challenge_store.py          # Typed challenge context facade (AuthChallengeContext)
├── google_auth.py              # Core OAuth flow and credential management
├── config.py                   # OAuth configuration and mode detection
├── oauth_clients.py            # Multi-client registry and resolver
├── oauth21_session_store.py    # Session management with persistence
├── credential_store.py         # File-based credential storage
├── service_decorator.py        # @require_google_service decorator
├── scopes.py                   # OAuth scope definitions
├── diagnostics.py              # Auth debugging utilities
├── security_io.py              # Secure file I/O helpers
├── middleware/
│   ├── auth_info.py            # Auth info extraction middleware
│   └── session.py              # MCP session binding middleware
├── oauth_callback_server.py    # Local OAuth callback server
├── oauth_responses.py          # OAuth response formatting
└── external_oauth_provider.py  # External OAuth provider support
```

### Phase 2 Policy Modules

These pure modules own auth policy decisions. They perform no IO and are independently testable.

| Module | Owns | Key Function |
|---|---|---|
| `auth_plan.py` | Typed contracts: `TransportMode`, `AuthFlow`, `ResolvedAuthPlan` | Dataclass definitions only |
| `flow_policy.py` | Flow selection: device vs callback, explicit override, flow_preference | `resolve_auth_flow_plan(...)` |
| `redirect_policy.py` | Redirect rules: port extraction, fallback policy, explicit redirect requirement | `resolve_redirect_policy(...)` |
| `challenge_store.py` | Challenge persistence facade: `AuthChallengeContext`, dict roundtrip | `challenge_context_from_dict(...)` |

**Composition point:** `google_auth.py:_resolve_auth_plan()` composes redirect policy + flow policy
into a single `ResolvedAuthPlan`. Callers consume the plan object instead of scattered conditionals.

### File Dependencies

```
google_auth.py
├── auth_plan.py (ResolvedAuthPlan, TransportMode)
├── flow_policy.py (resolve_auth_flow_plan)
├── redirect_policy.py (resolve_redirect_policy)
├── challenge_store.py (challenge_context_from_dict) [in handle_auth_callback]
├── config.py (get_transport_mode, is_stateless_mode, ...)
├── credential_store.py (get_credential_store)
├── diagnostics.py (log_resolved_auth_decision)
├── oauth_clients.py (resolve_oauth_client_for_user, OAuthClientSelection)
├── oauth21_session_store.py (get_oauth21_session_store)
├── scopes.py (SCOPES, get_current_scopes)
└── core/context.py (get_fastmcp_session_id)

core/server.py
├── challenge_store.py (challenge_context_from_dict) [in _get_persisted_redirect_uri_for_state]
├── google_auth.py (handle_auth_callback, initiate_auth_challenge, ...)
└── oauth21_session_store.py (get_oauth21_session_store)

service_decorator.py
├── google_auth.py (get_authenticated_google_service)
├── oauth21_session_store.py
├── scopes.py
└── core/context.py

oauth_callback_server.py
├── redirect_policy.py (build_local_redirect_uri, build_allowed_local_redirect_uris)
├── google_auth.py (check_client_secrets, handle_auth_callback)
└── scopes.py
```

### Data Stores

| Store | Type | Location | Survives Restart |
|-------|------|----------|------------------|
| LocalDirectoryCredentialStore | File | `~/.config/google-workspace-mcp-advanced/credentials/{email}.json` (legacy fallback: `~/.config/gws-mcp-advanced/credentials/{email}.json`) | Yes |
| OAuth21SessionStore._sessions | Memory | N/A | No |
| OAuth21SessionStore._mcp_session_mapping | Memory + Disk | `sessions.json` | Yes (v0.2.0+) |
| OAuth21SessionStore._session_auth_binding | Memory + Disk | `sessions.json` | Yes (v0.2.0+) |
| OAuth21SessionStore.oauth_states | Disk | `oauth_states.json` | Yes |

### Key Components

#### LocalDirectoryCredentialStore
- Persists OAuth tokens to disk as JSON files
- One file per user: `{email}.json`
- Stores: access_token, refresh_token, scopes, expiry, token_uri

#### OAuth21SessionStore
- Manages in-memory sessions with disk persistence for recovery
- Binds MCP sessions to Google user accounts
- Supports single-user auto-recovery mode

#### GoogleAuth (google_auth.py)
- Handles OAuth flow initiation and callback
- Token refresh with automatic retry
- Credential validation and scope checking
- Composes `resolve_redirect_policy()` + `resolve_auth_flow_plan()` via `_resolve_auth_plan()`

#### ServiceDecorator (@require_google_service)
- Injects authenticated Google API service into tool functions
- Handles token refresh and re-authentication prompts
- Maps service names to required scopes

### Authentication Flow

```
1. Tool invoked with user_google_email
   │
2. @require_google_service decorator
   │
3. Check OAuth21SessionStore for MCP session binding
   │
   ├─ Found → Get credentials from session
   │
   └─ Not found → Check LocalDirectoryCredentialStore
      │
      ├─ Found → Validate and refresh if needed
      │          Bind to MCP session
      │
      └─ Not found → Single-user mode?
         │
         ├─ Yes + 1 user exists → Auto-bind
         │
         └─ No → Resolve auth plan and return challenge
```

### Auth Policy Resolution (Phase 2)

```
_resolve_auth_plan(user_google_email)
   │
   ├─ resolve OAuth client selection
   │
   ├─ resolve_redirect_policy(oauth_client, transport_mode)
   │   → ResolvedRedirectPolicy (ports, fallback, explicit redirect required)
   │
   └─ resolve_auth_flow_plan(mode, transport, client, redirect_policy...)
       → ResolvedAuthPlan (flow, reason, redirect ports, fallback, explicit flag)
```

### Auth Topology Support Matrix

| Transport | Primary Client Type | Auth Flow (auto) | Sequential Callback Fallback |
|---|---|---|---|
| `stdio` | `installed` | device | Allowed |
| `stdio` | `web` (mapped) | callback | Disabled (registered ports only) |
| `stdio` | legacy env | device | Allowed |
| `streamable-http` | any | callback | Disabled (explicit redirect URI required) |

### Resolved Issues (v0.2.0+)

- **RC-1**: Session mappings now persist to `sessions.json`
- **RC-5**: Single-user auto-recovery implemented

### Interfaces (v0.4.0)

Abstract base classes in `auth/interfaces.py`:
- `BaseCredentialStore`: Contract for credential storage
- `BaseSessionStore`: Contract for session management
- `BaseAuthProvider`: Contract for OAuth providers

These enable dependency injection via `core/container.py`.

## Target State (Phase 5+)

See `specs/03_architecture_and_consolidation.md` for the target structure:

```
auth/
├── config.py                   # MERGE: oauth_config.py + google_oauth_config.py
├── scopes.py                   # KEEP
├── decorators.py               # RENAME: service_decorator.py
├── interfaces.py               # KEEP
├── credentials/
│   ├── store.py                # KEEP: credential_store.py
│   ├── session.py              # EXTRACT: from oauth21_session_store.py
│   └── types.py                # MERGE: oauth_types.py
├── providers/
│   ├── google.py               # EXTRACT: from google_auth.py
│   └── external.py             # RENAME: external_oauth_provider.py
├── middleware/
│   ├── auth_info.py            # RENAME: auth_info_middleware.py
│   └── session.py              # RENAME: mcp_session_middleware.py
└── server/
    └── callback.py             # RENAME: oauth_callback_server.py
```
