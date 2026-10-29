from fastapi.testclient import TestClient

from kangaroo.app import app
from kangaroo.routes.auth import require_user
from kangaroo.settings import settings


def test_settings_dump_masks_secrets(monkeypatch):
    monkeypatch.setitem(
        app.dependency_overrides, require_user, lambda: {"email": "admin@example.com"}
    )
    client = TestClient(app)

    response = client.get("/api/v1/settings/")

    body = response.json()
    assert response.status_code == 200
    assert body["env"] == settings.env
    assert body["session_secret_key"] == "**********"
    assert body["oidc_client_secret"] == "**********"
    assert settings.oidc_client_secret.get_secret_value() not in response.text
