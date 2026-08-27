from tests.conftest import register_and_login


def test_create_account(client):
    register_and_login(client)
    resp = client.post(
        "/api/accounts",
        json={"name": "Cash Wallet", "account_type": "cash", "opening_balance": "5000.00", "currency": "PKR"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["current_balance"] == "5000.00"
    assert body["opening_balance"] == "5000.00"


def test_list_accounts_only_own(client):
    register_and_login(client, email="a@example.com")
    client.post(
        "/api/accounts",
        json={"name": "A's Account", "account_type": "bank", "opening_balance": "0", "currency": "PKR"},
    )
    client.cookies.clear()

    register_and_login(client, email="b@example.com")
    resp = client.get("/api/accounts")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_archive_account(client):
    register_and_login(client)
    create = client.post(
        "/api/accounts",
        json={"name": "Old Wallet", "account_type": "wallet", "opening_balance": "0", "currency": "PKR"},
    )
    account_id = create.json()["id"]
    resp = client.post(f"/api/accounts/{account_id}/archive")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_update_account(client):
    register_and_login(client)
    create = client.post(
        "/api/accounts",
        json={"name": "Old Name", "account_type": "bank", "opening_balance": "0", "currency": "PKR"},
    )
    account_id = create.json()["id"]
    resp = client.put(
        f"/api/accounts/{account_id}",
        json={"name": "New Name", "account_type": "savings", "currency": "USD"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["account_type"] == "savings"
