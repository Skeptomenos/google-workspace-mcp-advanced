"""Unit tests for redirect policy resolution."""

from __future__ import annotations

import pytest

from auth.oauth_clients import OAuthClientSelection
from core.errors import GoogleAuthenticationError


def test_resolve_redirect_policy_fails_for_mapped_client_missing_client_type():
    from auth.redirect_policy import resolve_redirect_policy

    oauth_client = OAuthClientSelection(
        client_key="work",
        client_id="client-id",
        client_secret="client-secret",
        source="account_map",
        selection_mode="mapped_only",
        redirect_uris=["http://localhost:9876/oauth2callback"],
        client_type=None,
    )

    with pytest.raises(GoogleAuthenticationError, match="client_type"):
        resolve_redirect_policy(oauth_client=oauth_client, transport_mode="stdio")


def test_resolve_redirect_policy_fails_for_mapped_web_client_missing_redirect_uris():
    from auth.redirect_policy import resolve_redirect_policy

    oauth_client = OAuthClientSelection(
        client_key="work",
        client_id="client-id",
        client_secret="client-secret",
        source="domain_map",
        selection_mode="mapped_only",
        redirect_uris=None,
        client_type="web",
    )

    with pytest.raises(GoogleAuthenticationError, match="redirect_uris"):
        resolve_redirect_policy(oauth_client=oauth_client, transport_mode="stdio")


def test_resolve_redirect_policy_disables_fallback_for_mapped_web_redirects():
    from auth.redirect_policy import resolve_redirect_policy

    oauth_client = OAuthClientSelection(
        client_key="work",
        client_id="client-id",
        client_secret="client-secret",
        source="script_map",
        selection_mode="mapped_only",
        redirect_uris=[
            "http://localhost:9876/oauth2callback",
            "http://localhost:9877/oauth2callback",
            "http://localhost:9876/oauth2callback",
        ],
        client_type="web",
    )

    policy = resolve_redirect_policy(oauth_client=oauth_client, transport_mode="stdio")

    assert policy.callback_allowed is True
    assert policy.preferred_redirect_ports == (9876, 9877)
    assert policy.allow_sequential_fallback is False
    assert policy.requires_explicit_redirect_uri is True


def test_resolve_redirect_policy_allows_fallback_for_installed_client():
    from auth.redirect_policy import resolve_redirect_policy

    oauth_client = OAuthClientSelection(
        client_key="local-default",
        client_id="client-id",
        client_secret="client-secret",
        source="default_client",
        selection_mode="default_first",
        redirect_uris=None,
        client_type="installed",
    )

    policy = resolve_redirect_policy(oauth_client=oauth_client, transport_mode="stdio")

    assert policy.callback_allowed is True
    assert policy.preferred_redirect_ports == ()
    assert policy.allow_sequential_fallback is True
    assert policy.requires_explicit_redirect_uri is False


def test_resolve_redirect_policy_allows_fallback_for_legacy_env_client():
    from auth.redirect_policy import resolve_redirect_policy

    oauth_client = OAuthClientSelection(
        client_key="legacy-env",
        client_id="client-id",
        client_secret="client-secret",
        source="legacy_env",
        selection_mode="legacy",
        redirect_uris=None,
        client_type=None,
    )

    policy = resolve_redirect_policy(oauth_client=oauth_client, transport_mode="stdio")

    assert policy.callback_allowed is True
    assert policy.preferred_redirect_ports == ()
    assert policy.allow_sequential_fallback is True
    assert policy.requires_explicit_redirect_uri is False


def test_resolve_redirect_policy_requires_explicit_redirect_uri_for_streamable_http():
    from auth.redirect_policy import resolve_redirect_policy

    oauth_client = OAuthClientSelection(
        client_key="legacy-env",
        client_id="client-id",
        client_secret="client-secret",
        source="legacy_env",
        selection_mode="legacy",
        redirect_uris=None,
        client_type="installed",
    )

    policy = resolve_redirect_policy(oauth_client=oauth_client, transport_mode="streamable-http")

    assert policy.callback_allowed is True
    assert policy.preferred_redirect_ports == ()
    assert policy.allow_sequential_fallback is False
    assert policy.requires_explicit_redirect_uri is True
