"""
Dedicated cross-user data isolation tests -- the single most important
security property of this application.
"""
from tests.conftest import register_and_login


def test_account_not_accessible_by_other_user(client):
    register_and_login(client, email="alice@example.com")
    account = client.post(
        "/api/accounts",
        json={"name": "Alice's Bank", "account_type": "bank", "opening_balance": "1000.00", "currency": "PKR"},
    ).json()

    client.cookies.clear()
    register_and_login(client, email="bob@example.com")
    resp = client.get(f"/api/accounts/{account['id']}")
    assert resp.status_code == 404

    resp = client.put(
        f"/api/accounts/{account['id']}",
        json={"name": "Hijacked", "account_type": "bank", "currency": "PKR"},
    )
    assert resp.status_code == 404

    resp = client.post(f"/api/accounts/{account['id']}/archive")
    assert resp.status_code == 404


def test_budget_not_accessible_by_other_user(client):
    register_and_login(client, email="alice2@example.com")
    client.post(
        "/api/accounts",
        json={"name": "Alice", "account_type": "bank", "opening_balance": "1000", "currency": "PKR"},
    )
    cat_id = client.get("/api/categories", params={"type": "expense"}).json()[0]["id"]
    budget = client.post(
        "/api/budgets", json={"category_id": cat_id, "amount": "500.00", "month": 8, "year": 2026}
    ).json()

    client.cookies.clear()
    register_and_login(client, email="bob2@example.com")
    resp = client.delete(f"/api/budgets/{budget['id']}")
    assert resp.status_code == 404


def test_notifications_not_accessible_by_other_user(client):
    register_and_login(client, email="alice3@example.com")
    client.post(
        "/api/accounts",
        json={"name": "Alice", "account_type": "bank", "opening_balance": "0", "currency": "PKR"},
    )
    notifications = client.get("/api/notifications").json()
    assert len(notifications) >= 1
    notif_id = notifications[0]["id"]

    client.cookies.clear()
    register_and_login(client, email="bob3@example.com")
    resp = client.post(f"/api/notifications/{notif_id}/read")
    assert resp.status_code == 404

    # Bob has no notifications of his own yet -- and definitely can't see Alice's.
    resp = client.get("/api/notifications")
    assert resp.json() == []

    client.post(
        "/api/accounts",
        json={"name": "Bob", "account_type": "bank", "opening_balance": "0", "currency": "PKR"},
    )
    resp = client.get("/api/notifications")
    assert len(resp.json()) == 1  # only bob's own "account created" notification


def test_dashboard_data_is_per_user(client):
    register_and_login(client, email="alice4@example.com")
    account = client.post(
        "/api/accounts",
        json={"name": "Alice", "account_type": "bank", "opening_balance": "50000", "currency": "PKR"},
    ).json()
    client.cookies.clear()

    register_and_login(client, email="bob4@example.com")
    resp = client.get("/api/reports/dashboard")
    assert resp.json()["summary"]["total_balance"] == 0.0
