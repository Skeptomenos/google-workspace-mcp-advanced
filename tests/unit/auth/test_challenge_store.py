"""Unit tests for typed challenge context facade."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest


def test_auth_challenge_context_is_frozen():
    from auth.challenge_store import AuthChallengeContext

    ctx = AuthChallengeContext(
        state="test-state-abc",
        user_google_email="alice@example.com",
        oauth_client_key="work-callback",
        redirect_uri="http://localhost:9876/oauth2callback",
        code_verifier="pkce-verifier-123",
        session_id="session-abc",
    )

    assert ctx.state == "test-state-abc"
    assert ctx.user_google_email == "alice@example.com"
    assert ctx.oauth_client_key == "work-callback"
    assert ctx.redirect_uri == "http://localhost:9876/oauth2callback"
    assert ctx.code_verifier == "pkce-verifier-123"
    assert ctx.session_id == "session-abc"

    with pytest.raises(FrozenInstanceError):
        ctx.state = "mutated"  # type: ignore[misc]


def test_auth_challenge_context_allows_optional_fields():
    from auth.challenge_store import AuthChallengeContext

    ctx = AuthChallengeContext(
        state="minimal-state",
        user_google_email="bob@example.com",
        oauth_client_key=None,
        redirect_uri="http://localhost:9876/oauth2callback",
        code_verifier=None,
        session_id=None,
    )

    assert ctx.oauth_client_key is None
    assert ctx.code_verifier is None
    assert ctx.session_id is None


def test_auth_challenge_context_roundtrips_through_dict():
    from auth.challenge_store import AuthChallengeContext, challenge_context_from_dict, challenge_context_to_dict

    original = AuthChallengeContext(
        state="roundtrip-state",
        user_google_email="alice@example.com",
        oauth_client_key="work",
        redirect_uri="http://localhost:9876/oauth2callback",
        code_verifier="verifier-xyz",
        session_id="sess-123",
    )

    raw = challenge_context_to_dict(original)
    assert isinstance(raw, dict)
    assert raw["state"] == "roundtrip-state"
    assert raw["redirect_uri"] == "http://localhost:9876/oauth2callback"

    restored = challenge_context_from_dict(raw)
    assert restored.state == original.state
    assert restored.user_google_email == original.user_google_email
    assert restored.oauth_client_key == original.oauth_client_key
    assert restored.redirect_uri == original.redirect_uri
    assert restored.code_verifier == original.code_verifier
    assert restored.session_id == original.session_id


def test_challenge_context_from_dict_handles_missing_optional_fields():
    from auth.challenge_store import challenge_context_from_dict

    raw = {
        "state": "sparse-state",
        "user_google_email": "bob@example.com",
        "redirect_uri": "http://localhost:9876/oauth2callback",
    }

    ctx = challenge_context_from_dict(raw)

    assert ctx.state == "sparse-state"
    assert ctx.user_google_email == "bob@example.com"
    assert ctx.oauth_client_key is None
    assert ctx.redirect_uri == "http://localhost:9876/oauth2callback"
    assert ctx.code_verifier is None
    assert ctx.session_id is None


def test_challenge_context_from_dict_uses_expected_user_email_fallback():
    """Legacy store uses 'expected_user_email'; facade must accept both keys."""
    from auth.challenge_store import challenge_context_from_dict

    raw = {
        "state": "legacy-state",
        "expected_user_email": "legacy@example.com",
        "redirect_uri": "http://localhost:9876/oauth2callback",
    }

    ctx = challenge_context_from_dict(raw)
    assert ctx.user_google_email == "legacy@example.com"


def test_challenge_context_from_dict_prefers_user_google_email_over_expected():
    from auth.challenge_store import challenge_context_from_dict

    raw = {
        "state": "dual-key-state",
        "user_google_email": "preferred@example.com",
        "expected_user_email": "fallback@example.com",
        "redirect_uri": "http://localhost:9876/oauth2callback",
    }

    ctx = challenge_context_from_dict(raw)
    assert ctx.user_google_email == "preferred@example.com"


def test_challenge_context_from_dict_requires_state():
    from auth.challenge_store import challenge_context_from_dict

    with pytest.raises((KeyError, ValueError)):
        challenge_context_from_dict({"redirect_uri": "http://localhost:9876/oauth2callback"})


def test_challenge_context_from_dict_requires_redirect_uri():
    from auth.challenge_store import challenge_context_from_dict

    with pytest.raises((KeyError, ValueError)):
        challenge_context_from_dict({"state": "no-redirect"})
