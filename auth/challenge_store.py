"""Typed facade for OAuth challenge state persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthChallengeContext:
    """Typed representation of one pending OAuth challenge.

    This facade replaces the raw-dict pattern used by OAuth21SessionStore
    for challenge state metadata. All fields that were previously accessed
    via ``state_info.get("key")`` are now typed attributes.
    """

    state: str
    user_google_email: str | None
    oauth_client_key: str | None
    redirect_uri: str
    code_verifier: str | None
    session_id: str | None


def challenge_context_to_dict(ctx: AuthChallengeContext) -> dict[str, Any]:
    """Serialize an AuthChallengeContext to the raw dict format used by the session store."""
    return {
        "state": ctx.state,
        "session_id": ctx.session_id,
        "oauth_client_key": ctx.oauth_client_key,
        "expected_user_email": ctx.user_google_email,
        "code_verifier": ctx.code_verifier,
        "redirect_uri": ctx.redirect_uri,
    }


def challenge_context_from_dict(raw: dict[str, Any]) -> AuthChallengeContext:
    """Deserialize a raw dict from the session store into an AuthChallengeContext.

    Accepts both ``user_google_email`` and the legacy ``expected_user_email``
    key, preferring ``user_google_email`` when both are present.

    Raises:
        KeyError: If required fields (``state``, ``redirect_uri``) are missing.
        ValueError: If required fields are empty/None.
    """
    state = raw.get("state")
    if not state:
        raise ValueError("OAuth challenge state dict is missing required 'state' field")

    redirect_uri = raw.get("redirect_uri")
    if not redirect_uri:
        raise ValueError("OAuth challenge state dict is missing required 'redirect_uri' field")

    user_google_email = raw.get("user_google_email") or raw.get("expected_user_email")

    return AuthChallengeContext(
        state=str(state),
        user_google_email=str(user_google_email) if user_google_email else None,
        oauth_client_key=raw.get("oauth_client_key"),
        redirect_uri=str(redirect_uri),
        code_verifier=raw.get("code_verifier"),
        session_id=raw.get("session_id"),
    )
