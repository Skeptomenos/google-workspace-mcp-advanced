from urllib.parse import parse_qs, urlparse

from auth.google_auth import create_oauth_flow
from auth.oauth_clients import OAuthClientSelection


def _oauth_client() -> OAuthClientSelection:
    return OAuthClientSelection(
        client_key="test-client",
        client_id="dummy-client.apps.googleusercontent.com",
        client_secret="dummy-secret",
        source="test",
        selection_mode="mapped_only",
    )


def test_create_oauth_flow_autogenerates_pkce_verifier_for_auth_url():
    flow = create_oauth_flow(
        scopes=["openid"],
        redirect_uri="http://localhost:9876/oauth2callback",
        state="state-1",
        oauth_client=_oauth_client(),
    )

    auth_url, returned_state = flow.authorization_url(access_type="offline", prompt="consent")
    query = parse_qs(urlparse(auth_url).query)

    assert returned_state == "state-1"
    assert query["state"] == ["state-1"]
    assert "code_challenge" in query
    assert query["code_challenge_method"] == ["S256"]
    assert flow.code_verifier
