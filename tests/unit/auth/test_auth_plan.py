"""Unit tests for typed auth plan contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from auth.oauth_clients import OAuthClientSelection


def test_resolved_auth_plan_is_frozen_and_keeps_redirect_state_outside_plan():
    from auth.auth_plan import ResolvedAuthPlan

    oauth_client = OAuthClientSelection(
        client_key="work",
        client_id="client-id",
        client_secret="client-secret",
        source="account_map",
        selection_mode="mapped_only",
        flow_preference="callback",
        redirect_uris=["http://localhost:9876/oauth2callback"],
        client_type="web",
    )

    plan = ResolvedAuthPlan(
        user_google_email="user@example.com",
        transport_mode="stdio",
        selected_flow="callback",
        oauth_client=oauth_client,
        selection_reason="mapped web stdio auth requires callback",
        preferred_redirect_ports=(9876,),
        allow_sequential_fallback=False,
        requires_explicit_redirect_uri=True,
    )

    assert plan.oauth_client is oauth_client
    assert plan.oauth_client.client_type == "web"
    assert not hasattr(plan, "client_type")
    assert not hasattr(plan, "redirect_uri")

    with pytest.raises(FrozenInstanceError):
        plan.selected_flow = "device"  # type: ignore[misc]
