# Issue #11: OAuth callback port not deterministic — Implementation Plan

**Issue:** OAuth callback port not deterministic when using `auth_clients.json` (raw `client_id`/`client_secret` format)  
**State:** OPEN  
**Author:** Harry-Coleman  
**Plan status:** READY FOR IMPLEMENTATION  
**Last updated:** 2026-03-13

---

## Original Problem

When using `auth_clients.json` with raw `client_id`/`client_secret` pairs (no `redirect_uris` array), the v1.0.8 multi-port fallback fix does not help because there are no registered ports to prefer. The callback server falls back to the random `9876-9899` range, causing OAuth to fail with a `redirect_uri_mismatch` error since Google requires every redirect URI to be pre-registered for Web application clients.

### Observed error

```
redirect_uri: http://localhost:9891/oauth2callback
Error: redirect_uri_mismatch
Request details: redirect_uri=http://localhost:9891/oauth2callback flowName=GeneralOAuthFlow
```

The port (`9891` in this case) varies between runs.

---

## Root Cause Analysis

The issue is a **client type mismatch**. The MCP server is a local process on the user's machine — textbook "Desktop application" (installed) in Google's OAuth taxonomy. The reporter created a "Web application" client instead, which requires exact redirect URI match including port.

Per Google's native app docs and RFC 8252 Section 7.3:
> "The authorization server MUST allow any port to be specified at the time of the request for loopback IP redirect URIs, to accommodate clients that obtain an available ephemeral port from the operating system at the time of the request."

**Desktop/installed clients**: Google accepts ANY localhost port. Port scanning (9876-9899) works.  
**Web application clients**: Every redirect URI including port must be pre-registered. Port scanning breaks.

### Bug chain for the reporter

1. User creates a **Web** client in GCP Console, registers one redirect URI
2. User hand-writes `auth_clients.json` with only `client_id` + `client_secret`
3. No `client_type` field -> `None` -> `None != "installed"` is `True` -> code treats it as web
4. No `redirect_uris` field -> no preferred ports -> sequential scan from 9876
5. Port 9876 may be occupied -> picks 9891 -> Google rejects with `redirect_uri_mismatch`

---

## Decision

**Support Desktop (installed) clients only.** Close support for Web application clients.

Rationale:
- An MCP server invoked via stdio is a native/desktop app by definition
- Google recommends Desktop client type for CLI/native tools
- Desktop clients make the port issue disappear entirely (any port works)
- The embedded credentials already use `"installed"` key (`auth/config.py:429`)
- No known enterprise policy blocks creation of Desktop OAuth clients

---

## Implementation Tasks

### Task 1: Default env-var config to `installed` key

**Status:** NOT STARTED  
**File:** `auth/google_auth.py`  
**Line:** 777

`load_client_secrets_from_env()` builds a config dict from `GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET` env vars. It currently wraps them under the `"web"` key. Change to `"installed"`.

```python
# BEFORE (line 777)
config = {"web": web_config}

# AFTER
config = {"installed": web_config}
```

**Verification:** Existing tests pass. Any test that checks the env-var config structure gets updated.

---

### Task 2: Default `create_oauth_flow()` config key to `installed`

**Status:** NOT STARTED  
**File:** `auth/google_auth.py`  
**Line:** 873

`create_oauth_flow()` builds the config dict for `google-auth-oauthlib`. The top-level key determines which redirect validation rules the Google library applies. Currently defaults to `"web"` when `client_type` is `None`.

```python
# BEFORE (line 873)
config_key = oauth_client.client_type or "web"

# AFTER
config_key = "installed"
```

Hardcoded to `"installed"` since we only support desktop clients. The `client_type` field on the selection object is no longer consulted here.

**Verification:** `create_oauth_flow()` always produces a config with `"installed"` top-level key regardless of input.

---

### Task 3: Remove preferred-ports extraction from callback challenge

**Status:** NOT STARTED  
**File:** `auth/google_auth.py`  
**Lines:** 180-197, 200-232

Two deletions:

1. **Delete `_extract_ports_from_redirect_uris()` function** (lines 180-197). No longer needed — desktop clients accept any port.

2. **Simplify `_start_callback_auth_challenge()`** (lines 213-228). Remove the web-specific branch that extracts preferred ports from `redirect_uris`. The function should call `resolve_oauth_redirect_uri_for_auth_flow()` without `preferred_ports`.

```python
# BEFORE (lines 213-228)
preferred_ports: list[int] = []
try:
    oauth_client = _resolve_oauth_client_selection(user_google_email, override_client_key)
    if oauth_client.client_type != "installed":
        preferred_ports = _extract_ports_from_redirect_uris(oauth_client.redirect_uris)
        if preferred_ports:
            logger.info(...)
except Exception as exc:
    logger.debug(...)

oauth_redirect_uri = resolve_oauth_redirect_uri_for_auth_flow(preferred_ports=preferred_ports or None)

# AFTER
oauth_redirect_uri = resolve_oauth_redirect_uri_for_auth_flow()
```

**Verification:** Callback challenge starts without port extraction. Port is whatever `find_available_port()` returns.

---

### Task 4: Remove `preferred_ports` from redirect resolver

**Status:** NOT STARTED  
**File:** `auth/google_auth.py`  
**Line:** 306

Remove `preferred_ports` parameter from `resolve_oauth_redirect_uri_for_auth_flow()`. Update the call to `start_oauth_callback_server()` accordingly.

```python
# BEFORE
def resolve_oauth_redirect_uri_for_auth_flow(preferred_ports: list[int] | None = None) -> str:
    ...
    success, error_msg, oauth_redirect_uri = start_oauth_callback_server(preferred_ports=preferred_ports)

# AFTER
def resolve_oauth_redirect_uri_for_auth_flow() -> str:
    ...
    success, error_msg, oauth_redirect_uri = start_oauth_callback_server()
```

**Verification:** No callers pass `preferred_ports` anymore. Function signature is clean.

---

### Task 5: Simplify callback server port selection

**Status:** NOT STARTED  
**File:** `auth/oauth_callback_server.py`  
**Lines:** 235-296

Remove `preferred_ports` parameter and the preferred-port scanning loop from `start_oauth_callback_server()`. The function goes straight to `find_available_port()`.

```python
# BEFORE
def start_oauth_callback_server(
    base_uri: str = "http://localhost",
    preferred_ports: list[int] | None = None,
) -> tuple[bool, str, str | None]:
    ...
    for candidate in preferred_ports or []:
        ...  # ~20 lines of preferred-port scanning
    if port is None:
        port = find_available_port()

# AFTER
def start_oauth_callback_server(
    base_uri: str = "http://localhost",
) -> tuple[bool, str, str | None]:
    ...
    port = find_available_port()
```

Also update the docstring to remove preferred-ports language. The module docstring (lines 1-12) should be updated to state that only Desktop/installed clients are supported.

**Verification:** Server starts on the first available port in 9876-9899. No preferred-port logic remains.

---

### Task 6: Reject web clients at import boundary

**Status:** NOT STARTED  
**File:** `auth/oauth_clients.py`  
**Lines:** 285-314

`_extract_google_client_credentials()` parses the Google OAuth JSON downloaded from GCP Console. When the top-level key is `"web"`, reject with a clear error instead of accepting.

```python
# BEFORE (lines 294-299)
client_type = "web"
payload = client_json.get("web") if isinstance(client_json, dict) else None
if payload is None and isinstance(client_json, dict):
    payload = client_json.get("installed")
    if payload is not None:
        client_type = "installed"

# AFTER
payload = None
if isinstance(client_json, dict):
    if "web" in client_json:
        raise AuthenticationError(
            "Web application OAuth clients are not supported. "
            "Create a Desktop application client in Google Cloud Console and download its JSON. "
            "See: https://developers.google.com/identity/protocols/oauth2/native-app"
        )
    payload = client_json.get("installed")
if payload is None and isinstance(client_json, dict):
    payload = client_json
if not isinstance(payload, dict):
    raise AuthenticationError("OAuth client JSON must include an 'installed' object")
client_type = "installed"
```

**Verification:** Importing a web client JSON file -> `AuthenticationError` with actionable message. Importing a desktop client JSON -> works as before.

---

### Task 7: Default missing `client_type` to `installed`

**Status:** NOT STARTED  
**File:** `auth/oauth_clients.py`  
**Lines:** 270-271

When resolving a client from `auth_clients.json`, if `client_type` is missing (hand-written config), default to `"installed"` instead of `None`.

```python
# BEFORE (lines 270-271)
client_type_raw = profile.get("client_type")
client_type = str(client_type_raw).strip() if isinstance(client_type_raw, str) else None

# AFTER
client_type_raw = profile.get("client_type")
client_type = str(client_type_raw).strip() if isinstance(client_type_raw, str) else "installed"
```

**Verification:** `OAuthClientSelection.client_type` is never `None` after resolution. Hand-written configs without `client_type` behave as desktop clients.

---

### Task 8: Add/update tests

**Status:** NOT STARTED  
**Files:** `tests/unit/auth/`

| Test | Assertion |
|------|-----------|
| Import web client JSON -> rejection | `_extract_google_client_credentials({"web": {...}})` raises `AuthenticationError` with "not supported" |
| Import desktop client JSON -> success | `_extract_google_client_credentials({"installed": {...}})` returns `client_type="installed"` |
| Hand-written config without `client_type` -> defaults to installed | `resolve_oauth_client(...)` returns `client_type="installed"` |
| `create_oauth_flow()` uses `"installed"` key | Config dict passed to `Flow.from_client_config` has `"installed"` top-level key |
| `start_oauth_callback_server()` has no `preferred_ports` param | Signature check or call without the kwarg succeeds |
| `load_client_secrets_from_env()` uses `"installed"` key | Returned dict has `"installed"` top-level key, not `"web"` |

Update any existing tests that create `OAuthClientSelection(client_type="web", ...)` — those paths are now dead.

**Verification:** `uv run pytest tests/unit/auth/ -v` — all pass.

---

### Task 9: Update documentation

**Status:** NOT STARTED

| File | Change |
|------|--------|
| `docs/setup/MULTI_CLIENT_AUTH_SETUP.md` | Add note: "Only Desktop application (installed) OAuth clients are supported." Remove any references to web client config. |
| `docs/setup/AUTHENTICATION_MODEL.md` | Add troubleshooting entry: `redirect_uri_mismatch` -> "Verify your OAuth client was created as **Desktop application** in Google Cloud Console, not Web application." |
| `docs/setup/MCP_CLIENT_SETUP_GUIDE.md` | Add: "When creating your OAuth client in Google Cloud Console, select **Desktop application**." |
| `docs/setup/CLAUDE_CODE_MCP_SETUP.md` | One line: create a Desktop application client. |
| `docs/setup/OPENCODE_MCP_SETUP.md` | One line: create a Desktop application client. |
| `docs/setup/CURSOR_MCP_SETUP.md` | One line: create a Desktop application client. |
| `docs/setup/GEMINI_CLI_MCP_SETUP.md` | One line: create a Desktop application client. |
| `docs/RELEASE_NOTES.md` | Document: desktop-only policy, web clients rejected at import, issue #11 closed. |
| `README.md` | Align any OAuth client type references to Desktop. |

**Verification:** Read each file after editing. Grep for "web application" or `"web"` in setup docs to ensure none remain.

---

### Task 10: Full verification protocol

**Status:** NOT STARTED

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

All three must pass clean before the fix is considered done.

---

## Execution Order

Tasks 1-5 are the code changes (can be done in one pass).  
Task 6-7 are the validation/rejection changes (same pass).  
Task 8 is tests (immediately after code changes).  
Task 9 is docs (after tests pass).  
Task 10 is final gate.

---

## Files Changed Summary

| File | Type | Changes |
|------|------|---------|
| `auth/google_auth.py` | Modify | Tasks 1-4: env-var default, flow config key, delete `_extract_ports_from_redirect_uris`, simplify callback challenge, remove `preferred_ports` plumbing |
| `auth/oauth_callback_server.py` | Modify | Task 5: remove `preferred_ports` param and scanning loop |
| `auth/oauth_clients.py` | Modify | Tasks 6-7: reject web clients at import, default missing `client_type` to `"installed"` |
| `tests/unit/auth/test_*.py` | Modify/Add | Task 8: new tests + update existing |
| `docs/setup/*.md` | Modify | Task 9: desktop-only guidance |
| `docs/RELEASE_NOTES.md` | Modify | Task 9: release note |
| `README.md` | Modify | Task 9: align to desktop |

**Net code delta:** ~-39 lines (net deletion — removing web-specific logic).

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Users with existing working web client setups break on upgrade | Medium | Clear error message at import tells them to create Desktop client. Release note documents the change. |
| Existing `auth_clients.json` with `client_type: "web"` already persisted | Low | Rejection is at import time (Task 6). Existing persisted configs still have `client_type` in the JSON but `create_oauth_flow()` now hardcodes `"installed"` (Task 2), so they work but get desktop behavior. |
| Enterprise users who believe they cannot create Desktop clients | Low | Desktop clients are available in all GCP projects. No known policy blocks them. |

---

## Log

| Date | Entry |
|------|-------|
| 2026-03-13 | Created implementation plan. Decision: desktop-only. 10 tasks defined. |
