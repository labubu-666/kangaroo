from sqlalchemy import func, select

from kangaroo.app import app
from kangaroo.repositories.tables import RecentHistoryRow
from kangaroo.routes.auth import require_user

OTHER_USER = {"email": "other@example.com"}
BASE = "/api-internal/v1/recent-history"


def visit(client, item_id, title=None, parent=None, type="work-item"):
    response = client.post(
        f"{BASE}/",
        json={
            "type": type,
            "item_id": item_id,
            "title": title or f"Item {item_id}",
            "parent": parent,
            "to": "/work-items/$id",
            "params": {"id": item_id},
        },
    )
    assert response.status_code == 204


def test_recent_history_requires_login(client, logged_out):
    assert client.get(BASE).status_code == 401


def test_visit_then_list(client):
    visit(client, "w1", title="Write docs", parent="Website")
    response = client.get(BASE)
    assert response.status_code == 200
    assert response.json() == [
        {
            "type": "work-item",
            "item_id": "w1",
            "title": "Write docs",
            "parent": "Website",
            "to": "/work-items/$id",
            "params": {"id": "w1"},
            "search": {},
            "modified_at": response.json()[0]["modified_at"],
        }
    ]


def test_repeat_visit_moves_item_to_top_without_duplicating(client):
    visit(client, "a", title="A")
    visit(client, "b", title="B")
    visit(client, "a", title="A renamed")
    items = client.get(BASE).json()
    assert [item["item_id"] for item in items] == ["a", "b"]
    assert items[0]["title"] == "A renamed"


def test_same_id_different_type_is_separate(client):
    visit(client, "1", type="project")
    visit(client, "1", type="function")
    assert len(client.get(BASE).json()) == 2


def test_list_shows_at_most_ten_newest(client):
    for index in range(12):
        visit(client, f"w{index}")
    items = client.get(BASE).json()
    assert len(items) == 10
    assert items[0]["item_id"] == "w11"


def test_list_truncates_storage_to_one_hundred(client, session):
    for index in range(105):
        visit(client, f"w{index}")
    client.get(BASE)
    count = session.scalar(select(func.count()).select_from(RecentHistoryRow))
    assert count == 100


def test_search_matches_title_and_parent_beyond_first_ten(client):
    visit(client, "old", title="Quarterly report")
    for index in range(12):
        visit(client, f"w{index}", title=f"Task {index}", parent="Website")
    assert [i["item_id"] for i in client.get(BASE).json()].count("old") == 0
    found = client.get(BASE, params={"search": "quarterly"}).json()
    assert [item["item_id"] for item in found] == ["old"]
    by_parent = client.get(BASE, params={"search": "website"}).json()
    assert len(by_parent) == 10


def test_search_treats_like_wildcards_literally(client):
    visit(client, "a", title="100% done")
    visit(client, "b", title="other")
    found = client.get(BASE, params={"search": "%"}).json()
    assert [item["item_id"] for item in found] == ["a"]


def test_remove_one_entry(client):
    visit(client, "a")
    visit(client, "b")
    response = client.delete(f"{BASE}/work-item/a")
    assert response.status_code == 204
    assert [i["item_id"] for i in client.get(BASE).json()] == ["b"]


def test_clear_removes_all_entries(client):
    visit(client, "a")
    visit(client, "b")
    assert client.delete(BASE).status_code == 204
    assert client.get(BASE).json() == []


def test_history_is_per_user(client, monkeypatch):
    visit(client, "mine")
    monkeypatch.setitem(app.dependency_overrides, require_user, lambda: OTHER_USER)
    assert client.get(BASE).json() == []
    visit(client, "theirs")
    monkeypatch.setitem(
        app.dependency_overrides,
        require_user,
        lambda: {"email": "test@example.com"},
    )
    assert [i["item_id"] for i in client.get(BASE).json()] == ["mine"]


def test_invalid_type_is_rejected(client):
    response = client.post(
        f"{BASE}/",
        json={
            "type": "nope",
            "item_id": "x",
            "title": "x",
            "to": "/x",
            "params": {},
        },
    )
    assert response.status_code == 422


def test_calendar_visit_is_recorded_without_params(client):
    response = client.post(
        f"{BASE}/",
        json={
            "type": "calendar",
            "item_id": "all",
            "title": "Calendar",
            "to": "/calendar",
            "params": {},
        },
    )
    assert response.status_code == 204
    assert [item["type"] for item in client.get(BASE).json()] == ["calendar"]


def test_project_tab_keeps_its_search_and_tabs_are_separate(client):
    for tab in ["backlog", "calendar"]:
        response = client.post(
            f"{BASE}/",
            json={
                "type": "project-tab",
                "item_id": f"p1:{tab}",
                "title": tab.title(),
                "parent": "Media",
                "to": "/projects/$id",
                "params": {"id": "p1"},
                "search": {"tab": tab},
            },
        )
        assert response.status_code == 204
    items = client.get(BASE).json()
    assert [(i["title"], i["search"]) for i in items] == [
        ("Calendar", {"tab": "calendar"}),
        ("Backlog", {"tab": "backlog"}),
    ]


def test_revisiting_a_project_tab_moves_it_to_top(client):
    for tab in ["backlog", "calendar", "backlog"]:
        client.post(
            f"{BASE}/",
            json={
                "type": "project-tab",
                "item_id": f"p1:{tab}",
                "title": tab.title(),
                "parent": "Media",
                "to": "/projects/$id",
                "params": {"id": "p1"},
                "search": {"tab": tab},
            },
        )
    assert [i["title"] for i in client.get(BASE).json()] == ["Backlog", "Calendar"]
