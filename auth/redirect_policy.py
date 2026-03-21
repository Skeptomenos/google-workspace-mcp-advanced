"""Pure redirect policy rules for auth flows."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from auth.auth_plan import TransportMode
from auth.oauth_clients import OAuthClientSelection
from core.errors import GoogleAuthenticationError


@dataclass(frozen=True)
class ResolvedRedirectPolicy:
    """Resolved redirect behavior for one auth attempt."""

    callback_allowed: bool
    preferred_redirect_ports: tuple[int, ...]
    allow_sequential_fallback: bool
    requires_explicit_redirect_uri: bool


def build_local_redirect_uri(base_uri: str, port: int) -> str:
    """Build one localhost callback URI from base URI and port."""
    return f"{base_uri}:{port}/oauth2callback"


def build_allowed_local_redirect_uris(
    base_uri: str,
    preferred_ports: tuple[int, ...] | list[int] | None,
) -> list[str] | None:
    """Build allowed local redirect URIs from preferred ports."""
    if not preferred_ports:
        return None
    return [build_local_redirect_uri(base_uri, port) for port in preferred_ports]


def extract_localhost_ports_from_redirect_uris(redirect_uris: list[str] | None) -> tuple[int, ...]:
    """Extract unique localhost ports from registered redirect URIs in declaration order."""
    ports: list[int] = []
    for uri in redirect_uris or []:
        try:
            parsed = urlparse(uri)
        except Exception:
            continue

        if parsed.hostname in {"localhost", "127.0.0.1"} and parsed.port and parsed.port not in ports:
            ports.append(parsed.port)

    return tuple(ports)


def resolve_redirect_policy(
    *,
    oauth_client: OAuthClientSelection,
    transport_mode: TransportMode,
) -> ResolvedRedirectPolicy:
    """Resolve redirect requirements for one auth attempt without performing IO."""
    if transport_mode != "stdio":
        return ResolvedRedirectPolicy(
            callback_allowed=True,
            preferred_redirect_ports=(),
            allow_sequential_fallback=False,
            requires_explicit_redirect_uri=True,
        )

    if oauth_client.source == "legacy_env":
        return ResolvedRedirectPolicy(
            callback_allowed=True,
            preferred_redirect_ports=(),
            allow_sequential_fallback=True,
            requires_explicit_redirect_uri=False,
        )

    client_type = (oauth_client.client_type or "").strip().lower() or None
    if not client_type:
        raise GoogleAuthenticationError(
            f"OAuth client '{oauth_client.client_key}' is missing client_type in auth_clients.json. "
            "Re-import the original Google OAuth client JSON with import_google_auth_client or add "
            "client_type explicitly."
        )

    if client_type == "installed":
        return ResolvedRedirectPolicy(
            callback_allowed=True,
            preferred_redirect_ports=(),
            allow_sequential_fallback=True,
            requires_explicit_redirect_uri=False,
        )

    if client_type != "web":
        raise GoogleAuthenticationError(
            f"OAuth client '{oauth_client.client_key}' has unsupported client_type '{oauth_client.client_type}'. "
            "Use 'installed' or 'web', or re-import the original Google OAuth client JSON."
        )

    if not oauth_client.redirect_uris:
        raise GoogleAuthenticationError(
            f"OAuth client '{oauth_client.client_key}' is missing redirect_uris in auth_clients.json. "
            "Add redirect_uris or re-import the original Google OAuth client JSON with "
            "import_google_auth_client."
        )

    preferred_redirect_ports = extract_localhost_ports_from_redirect_uris(oauth_client.redirect_uris)
    if not preferred_redirect_ports:
        raise GoogleAuthenticationError(
            f"OAuth client '{oauth_client.client_key}' does not declare any localhost redirect_uris for local "
            "callback auth. Add localhost redirect_uris or re-import the original Google OAuth client JSON."
        )

    return ResolvedRedirectPolicy(
        callback_allowed=True,
        preferred_redirect_ports=preferred_redirect_ports,
        allow_sequential_fallback=False,
        requires_explicit_redirect_uri=True,
    )
