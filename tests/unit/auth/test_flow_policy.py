"""Unit tests for auth flow policy resolution."""

from __future__ import annotations

from auth.oauth_clients import OAuthClientSelection


def test_resolve_auth_flow_plan_prefers_device_for_installed_stdio():
    from auth.flow_policy import resolve_auth_flow_plan

    oauth_client = OAuthClientSelection(
        client_key="local-default",
        client_id="client-id",
        client_secret="client-secret",
        source="default_client",
        selection_mode="default_first",
        client_type="installed",
    )

    plan = resolve_auth_flow_plan(
        requested_auth_mode="auto",
        transport_mode="stdio",
        user_google_email="user@example.com",
        oauth_client=oauth_client,
    )

    assert plan.selected_flow == "device"
    assert plan.transport_mode == "stdio"
    assert plan.selection_reason == "stdio auto prefers device flow for installed and local auth"


def test_resolve_auth_flow_plan_prefers_callback_for_mapped_web_stdio():
    from auth.flow_policy import resolve_auth_flow_plan

    oauth_client = OAuthClientSelection(
        client_key="work",
        client_id="client-id",
        client_secret="client-secret",
        source="account_map",
        selection_mode="mapped_only",
        client_type="web",
        redirect_uris=["http://localhost:9876/oauth2callback"],
    )

    plan = resolve_auth_flow_plan(
        requested_auth_mode="auto",
        transport_mode="stdio",
        user_google_email="user@example.com",
        oauth_client=oauth_client,
    )

    assert plan.selected_flow == "callback"
    assert plan.selection_reason == "mapped web stdio auth requires callback flow"


def test_resolve_auth_flow_plan_preserves_redirect_policy_inputs():
    from auth.flow_policy import resolve_auth_flow_plan

    oauth_client = OAuthClientSelection(
        client_key="work",
        client_id="client-id",
        client_secret="client-secret",
        source="account_map",
        selection_mode="mapped_only",
        client_type="web",
        redirect_uris=["http://localhost:9876/oauth2callback"],
    )

    plan = resolve_auth_flow_plan(
        requested_auth_mode="auto",
        transport_mode="stdio",
        user_google_email="user@example.com",
        oauth_client=oauth_client,
        preferred_redirect_ports=(9876,),
        allow_sequential_fallback=False,
        requires_explicit_redirect_uri=True,
    )

    assert plan.selected_flow == "callback"
    assert plan.allow_sequential_fallback is False
    assert plan.preferred_redirect_ports == (9876,)
    assert plan.requires_explicit_redirect_uri is True


def test_resolve_auth_flow_plan_honors_explicit_mode_before_auto_policy():
    from auth.flow_policy import resolve_auth_flow_plan

    oauth_client = OAuthClientSelection(
        client_key="work",
        client_id="client-id",
        client_secret="client-secret",
        source="account_map",
        selection_mode="mapped_only",
        client_type="web",
        redirect_uris=["http://localhost:9876/oauth2callback"],
    )

    plan = resolve_auth_flow_plan(
        requested_auth_mode="device",
        transport_mode="stdio",
        user_google_email="user@example.com",
        oauth_client=oauth_client,
    )

    assert plan.selected_flow == "device"
    assert plan.selection_reason == "explicit auth flow mode requested"


def test_resolve_auth_flow_plan_uses_callback_for_streamable_http():
    from auth.flow_policy import resolve_auth_flow_plan

    oauth_client = OAuthClientSelection(
        client_key="legacy-env",
        client_id="client-id",
        client_secret="client-secret",
        source="legacy_env",
        selection_mode="legacy",
        client_type="installed",
    )

    plan = resolve_auth_flow_plan(
        requested_auth_mode="auto",
        transport_mode="streamable-http",
        user_google_email="user@example.com",
        oauth_client=oauth_client,
    )

    assert plan.selected_flow == "callback"
    assert plan.selection_reason == "non-stdio transports require callback flow"


def test_resolve_auth_flow_plan_honors_client_flow_preference_before_transport_default():
    from auth.flow_policy import resolve_auth_flow_plan

    oauth_client = OAuthClientSelection(
        client_key="enterprise",
        client_id="client-id",
        client_secret="client-secret",
        source="domain_map",
        selection_mode="mapped_only",
        flow_preference="device",
        client_type="web",
        redirect_uris=["http://localhost:9876/oauth2callback"],
    )

    plan = resolve_auth_flow_plan(
        requested_auth_mode="auto",
        transport_mode="streamable-http",
        user_google_email="user@example.com",
        oauth_client=oauth_client,
    )

    assert plan.selected_flow == "device"
    assert plan.selection_reason == "oauth client flow_preference overrides auto mode"
