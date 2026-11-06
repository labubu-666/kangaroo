import hashlib

from kangaroo.app import app
from kangaroo.routes.auth import require_user


def test_current_user_returns_username_email_and_gravatar(client, monkeypatch):
    monkeypatch.setitem(
        app.dependency_overrides,
        require_user,
        lambda: {"email": "  Test.User@Example.com ", "name": "test-user"},
    )

    response = client.get("/api/v1/user")

    digest = hashlib.sha256(b"test.user@example.com").hexdigest()
    assert response.status_code == 200
    assert response.json() == {
        "username": "test-user",
        "email": "  Test.User@Example.com ",
        "avatar_url": f"https://gravatar.com/avatar/{digest}?d=identicon&s=64",
    }


def test_current_user_prefers_preferred_username(client, monkeypatch):
    monkeypatch.setitem(
        app.dependency_overrides,
        require_user,
        lambda: {
            "email": "test.user@example.com",
            "name": "Ken",
            "preferred_username": "kenny",
        },
    )

    response = client.get("/api/v1/user")

    assert response.json()["username"] == "kenny"


def test_current_user_requires_login(logged_out, client):
    response = client.get("/api/v1/user")

    assert response.status_code == 401
