"""Pure auth flow planning rules."""

from __future__ import annotations

from auth.auth_plan import AuthFlow, ResolvedAuthPlan, TransportMode
from auth.oauth_clients import OAuthClientSelection

AUTH_FLOW_AUTO = "auto"
AUTH_FLOW_CALLBACK: AuthFlow = "callback"
AUTH_FLOW_DEVICE: AuthFlow = "device"


def resolve_auth_flow_plan(
    *,
    requested_auth_mode: str,
    transport_mode: TransportMode,
    user_google_email: str,
    oauth_client: OAuthClientSelection,
    preferred_redirect_ports: tuple[int, ...] = (),
    allow_sequential_fallback: bool = True,
    requires_explicit_redirect_uri: bool = False,
) -> ResolvedAuthPlan:
    """Resolve one typed auth plan without performing IO."""
    selected_flow: AuthFlow
    selection_reason: str

    if requested_auth_mode == AUTH_FLOW_CALLBACK:
        selected_flow = AUTH_FLOW_CALLBACK
        selection_reason = "explicit auth flow mode requested"
    elif requested_auth_mode == AUTH_FLOW_DEVICE:
        selected_flow = AUTH_FLOW_DEVICE
        selection_reason = "explicit auth flow mode requested"
    elif oauth_client.flow_preference == AUTH_FLOW_CALLBACK:
        selected_flow = AUTH_FLOW_CALLBACK
        selection_reason = "oauth client flow_preference overrides auto mode"
    elif oauth_client.flow_preference == AUTH_FLOW_DEVICE:
        selected_flow = AUTH_FLOW_DEVICE
        selection_reason = "oauth client flow_preference overrides auto mode"
    elif transport_mode != "stdio":
        selected_flow = AUTH_FLOW_CALLBACK
        selection_reason = "non-stdio transports require callback flow"
    elif oauth_client.client_type == "web" and oauth_client.source != "legacy_env":
        selected_flow = AUTH_FLOW_CALLBACK
        selection_reason = "mapped web stdio auth requires callback flow"
    else:
        selected_flow = AUTH_FLOW_DEVICE
        selection_reason = "stdio auto prefers device flow for installed and local auth"

    return ResolvedAuthPlan(
        user_google_email=user_google_email,
        transport_mode=transport_mode,
        selected_flow=selected_flow,
        oauth_client=oauth_client,
        selection_reason=selection_reason,
        preferred_redirect_ports=preferred_redirect_ports,
        allow_sequential_fallback=allow_sequential_fallback,
        requires_explicit_redirect_uri=requires_explicit_redirect_uri,
    )
