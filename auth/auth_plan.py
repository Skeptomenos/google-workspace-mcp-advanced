"""Typed auth decision contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from auth.oauth_clients import OAuthClientSelection

TransportMode = Literal["stdio", "streamable-http"]
AuthFlow = Literal["device", "callback"]


@dataclass(frozen=True)
class ResolvedAuthPlan:
    """Resolved auth policy decision for one challenge."""

    user_google_email: str
    transport_mode: TransportMode
    selected_flow: AuthFlow
    oauth_client: OAuthClientSelection | None
    selection_reason: str
    preferred_redirect_ports: tuple[int, ...]
    allow_sequential_fallback: bool
    requires_explicit_redirect_uri: bool
