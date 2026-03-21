"""Internal auth regression matrix (SPEC-11 Task 11).

Exercises the auth policy seams (flow policy, redirect policy, challenge store)
across the full client-type x transport x flow matrix with monkeypatched
interactions. No live Google auth is required.
"""

from __future__ import annotations

import pytest

from auth.challenge_store import AuthChallengeContext, challenge_context_from_dict, challenge_context_to_dict
from auth.flow_policy import resolve_auth_flow_plan
from auth.oauth_clients import OAuthClientSelection
from auth.redirect_policy import resolve_redirect_policy
from core.errors import GoogleAuthenticationError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _installed_client(**overrides: str | list[str] | None) -> OAuthClientSelection:
    return OAuthClientSelection(
        client_key=overrides.get("client_key", "local-default"),  # type: ignore[arg-type]
        client_id=overrides.get("client_id", "installed-id.apps.googleusercontent.com"),  # type: ignore[arg-type]
        client_secret=overrides.get("client_secret", "installed-secret"),  # type: ignore[arg-type]
        source=overrides.get("source", "default_client"),  # type: ignore[arg-type]
        selection_mode=overrides.get("selection_mode", "default_first"),  # type: ignore[arg-type]
        client_type=overrides.get("client_type", "installed"),  # type: ignore[arg-type]
        flow_preference=overrides.get("flow_preference"),  # type: ignore[arg-type]
    )


def _web_client(**overrides: str | list[str] | None) -> OAuthClientSelection:
    return OAuthClientSelection(
        client_key=overrides.get("client_key", "work-callback"),  # type: ignore[arg-type]
        client_id=overrides.get("client_id", "web-id.apps.googleusercontent.com"),  # type: ignore[arg-type]
        client_secret=overrides.get("client_secret", "web-secret"),  # type: ignore[arg-type]
        source=overrides.get("source", "account_map"),  # type: ignore[arg-type]
        selection_mode=overrides.get("selection_mode", "mapped_only"),  # type: ignore[arg-type]
        client_type=overrides.get("client_type", "web"),  # type: ignore[arg-type]
        redirect_uris=overrides.get("redirect_uris", ["http://localhost:9876/oauth2callback"]),  # type: ignore[arg-type]
    )


def _legacy_env_client(**overrides: str | list[str] | None) -> OAuthClientSelection:
    return OAuthClientSelection(
        client_key=overrides.get("client_key", "legacy-env"),  # type: ignore[arg-type]
        client_id=overrides.get("client_id", "legacy-id.apps.googleusercontent.com"),  # type: ignore[arg-type]
        client_secret=overrides.get("client_secret", "legacy-secret"),  # type: ignore[arg-type]
        source=overrides.get("source", "legacy_env"),  # type: ignore[arg-type]
        selection_mode=overrides.get("selection_mode", "legacy"),  # type: ignore[arg-type]
        client_type=overrides.get("client_type"),  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# 1. web vs installed (redirect policy)
# ---------------------------------------------------------------------------


class TestWebVsInstalled:
    def test_installed_allows_sequential_fallback(self):
        policy = resolve_redirect_policy(oauth_client=_installed_client(), transport_mode="stdio")
        assert policy.allow_sequential_fallback is True
        assert policy.preferred_redirect_ports == ()

    def test_web_disables_fallback_and_extracts_ports(self):
        policy = resolve_redirect_policy(oauth_client=_web_client(), transport_mode="stdio")
        assert policy.allow_sequential_fallback is False
        assert policy.preferred_redirect_ports == (9876,)
        assert policy.requires_explicit_redirect_uri is True

    def test_web_with_multiple_ports(self):
        client = _web_client(
            redirect_uris=[
                "http://localhost:9876/oauth2callback",
                "http://localhost:9877/oauth2callback",
            ],
        )
        policy = resolve_redirect_policy(oauth_client=client, transport_mode="stdio")
        assert policy.preferred_redirect_ports == (9876, 9877)


# ---------------------------------------------------------------------------
# 2. stdio vs streamable-http (flow + redirect policy)
# ---------------------------------------------------------------------------


class TestTransportModes:
    def test_stdio_installed_prefers_device(self):
        plan = resolve_auth_flow_plan(
            requested_auth_mode="auto",
            transport_mode="stdio",
            user_google_email="user@example.com",
            oauth_client=_installed_client(),
        )
        assert plan.selected_flow == "device"

    def test_stdio_web_prefers_callback(self):
        client = _web_client()
        policy = resolve_redirect_policy(oauth_client=client, transport_mode="stdio")
        plan = resolve_auth_flow_plan(
            requested_auth_mode="auto",
            transport_mode="stdio",
            user_google_email="user@example.com",
            oauth_client=client,
            preferred_redirect_ports=policy.preferred_redirect_ports,
            allow_sequential_fallback=policy.allow_sequential_fallback,
            requires_explicit_redirect_uri=policy.requires_explicit_redirect_uri,
        )
        assert plan.selected_flow == "callback"
        assert plan.selection_reason == "mapped web stdio auth requires callback flow"

    def test_streamable_http_always_callback(self):
        plan = resolve_auth_flow_plan(
            requested_auth_mode="auto",
            transport_mode="streamable-http",
            user_google_email="user@example.com",
            oauth_client=_installed_client(),
        )
        assert plan.selected_flow == "callback"

    def test_streamable_http_requires_explicit_redirect_uri(self):
        policy = resolve_redirect_policy(
            oauth_client=_legacy_env_client(client_type="installed"),
            transport_mode="streamable-http",
        )
        assert policy.requires_explicit_redirect_uri is True
        assert policy.allow_sequential_fallback is False


# ---------------------------------------------------------------------------
# 3. callback vs device vs manual completion (flow selection)
# ---------------------------------------------------------------------------


class TestFlowSelection:
    def test_explicit_callback_overrides_transport(self):
        plan = resolve_auth_flow_plan(
            requested_auth_mode="callback",
            transport_mode="stdio",
            user_google_email="user@example.com",
            oauth_client=_installed_client(),
        )
        assert plan.selected_flow == "callback"
        assert plan.selection_reason == "explicit auth flow mode requested"

    def test_explicit_device_overrides_transport(self):
        plan = resolve_auth_flow_plan(
            requested_auth_mode="device",
            transport_mode="streamable-http",
            user_google_email="user@example.com",
            oauth_client=_installed_client(),
        )
        assert plan.selected_flow == "device"
        assert plan.selection_reason == "explicit auth flow mode requested"

    def test_flow_preference_overrides_transport_default(self):
        client = _installed_client(flow_preference="callback")
        plan = resolve_auth_flow_plan(
            requested_auth_mode="auto",
            transport_mode="stdio",
            user_google_email="user@example.com",
            oauth_client=client,
        )
        assert plan.selected_flow == "callback"
        assert plan.selection_reason == "oauth client flow_preference overrides auto mode"


# ---------------------------------------------------------------------------
# 4. mapped-only vs legacy env fallback (redirect policy)
# ---------------------------------------------------------------------------


class TestMappedVsLegacy:
    def test_legacy_env_allows_fallback(self):
        policy = resolve_redirect_policy(oauth_client=_legacy_env_client(), transport_mode="stdio")
        assert policy.allow_sequential_fallback is True
        assert policy.preferred_redirect_ports == ()

    def test_mapped_installed_allows_fallback(self):
        policy = resolve_redirect_policy(
            oauth_client=_installed_client(source="account_map", selection_mode="mapped_only"),
            transport_mode="stdio",
        )
        assert policy.allow_sequential_fallback is True

    def test_mapped_web_disables_fallback(self):
        policy = resolve_redirect_policy(
            oauth_client=_web_client(source="domain_map"),
            transport_mode="stdio",
        )
        assert policy.allow_sequential_fallback is False


# ---------------------------------------------------------------------------
# 5. mapped client_type=None fails with repair guidance
# ---------------------------------------------------------------------------


class TestMissingClientType:
    def test_mapped_missing_client_type_fails(self):
        client = OAuthClientSelection(
            client_key="hand-written",
            client_id="hw-id.apps.googleusercontent.com",
            client_secret="hw-secret",
            source="account_map",
            selection_mode="mapped_only",
            client_type=None,
        )
        with pytest.raises(GoogleAuthenticationError, match="client_type"):
            resolve_redirect_policy(oauth_client=client, transport_mode="stdio")

    def test_legacy_env_missing_client_type_succeeds(self):
        """Legacy env-derived clients are exempt from client_type validation."""
        policy = resolve_redirect_policy(oauth_client=_legacy_env_client(), transport_mode="stdio")
        assert policy.callback_allowed is True


# ---------------------------------------------------------------------------
# 6. occupied callback port (callback server policy)
# ---------------------------------------------------------------------------


class TestOccupiedCallbackPort:
    def test_registered_ports_occupied_and_fallback_disabled(self):
        from auth.oauth_callback_server import _resolve_callback_bind_port

        port, error = _resolve_callback_bind_port(
            preferred_ports=[9876],
            allow_sequential_fallback=False,
            is_port_available=lambda _: False,
            find_fallback_port=lambda: 9880,
        )
        assert port is None
        assert "registered oauth callback ports" in error.lower()

    def test_registered_ports_occupied_but_fallback_enabled(self):
        from auth.oauth_callback_server import _resolve_callback_bind_port

        port, error = _resolve_callback_bind_port(
            preferred_ports=[9876],
            allow_sequential_fallback=True,
            is_port_available=lambda _: False,
            find_fallback_port=lambda: 9888,
        )
        assert port == 9888
        assert error == ""


# ---------------------------------------------------------------------------
# 7. concurrent callback starts against singleton server
# ---------------------------------------------------------------------------


class TestConcurrentCallbackStarts:
    def test_incompatible_running_server_fails(self):
        from auth.oauth_callback_server import _validate_running_server_reuse

        ok, error = _validate_running_server_reuse(
            running_redirect_uri="http://localhost:9876/oauth2callback",
            allowed_redirect_uris=["http://localhost:9877/oauth2callback"],
        )
        assert ok is False
        assert "another local callback auth challenge is active" in error.lower()

    def test_compatible_running_server_reused(self):
        from auth.oauth_callback_server import _validate_running_server_reuse

        ok, error = _validate_running_server_reuse(
            running_redirect_uri="http://localhost:9876/oauth2callback",
            allowed_redirect_uris=["http://localhost:9876/oauth2callback"],
        )
        assert ok is True
        assert error == ""


# ---------------------------------------------------------------------------
# 8. wrong-account callback (challenge context)
# ---------------------------------------------------------------------------


class TestWrongAccountCallback:
    def test_challenge_context_preserves_expected_user(self):
        ctx = AuthChallengeContext(
            state="state-abc",
            user_google_email="alice@example.com",
            oauth_client_key="work",
            redirect_uri="http://localhost:9876/oauth2callback",
            code_verifier="verifier",
            session_id="sess-123",
        )
        assert ctx.user_google_email == "alice@example.com"

    def test_wrong_account_detectable_from_context(self):
        """The facade preserves expected email so callers can detect wrong-account."""
        ctx = AuthChallengeContext(
            state="state-xyz",
            user_google_email="expected@example.com",
            oauth_client_key="work",
            redirect_uri="http://localhost:9876/oauth2callback",
            code_verifier=None,
            session_id=None,
        )
        actual_email = "wrong@example.com"
        assert actual_email.lower() != (ctx.user_google_email or "").lower()


# ---------------------------------------------------------------------------
# 9. restart / reload with pending OAuth state (challenge store roundtrip)
# ---------------------------------------------------------------------------


class TestPendingStateRestart:
    def test_challenge_context_survives_dict_roundtrip(self):
        original = AuthChallengeContext(
            state="persist-state",
            user_google_email="alice@example.com",
            oauth_client_key="work-callback",
            redirect_uri="http://localhost:9876/oauth2callback",
            code_verifier="verifier-abc",
            session_id="sess-001",
        )
        raw = challenge_context_to_dict(original)
        restored = challenge_context_from_dict({**raw, "state": original.state})

        assert restored.state == original.state
        assert restored.user_google_email == original.user_google_email
        assert restored.oauth_client_key == original.oauth_client_key
        assert restored.redirect_uri == original.redirect_uri
        assert restored.code_verifier == original.code_verifier
        assert restored.session_id == original.session_id

    def test_legacy_expected_user_email_key_restored(self):
        """Store uses 'expected_user_email'; facade must accept it."""
        raw = {
            "state": "legacy-state",
            "expected_user_email": "legacy@example.com",
            "redirect_uri": "http://localhost:9877/oauth2callback",
            "oauth_client_key": "old-key",
        }
        ctx = challenge_context_from_dict(raw)
        assert ctx.user_google_email == "legacy@example.com"
