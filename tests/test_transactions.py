from tests.conftest import register_and_login


def _create_account(client, balance="10000.00"):
    resp = client.post(
        "/api/accounts",
        json={"name": "Main", "account_type": "bank", "opening_balance": balance, "currency": "PKR"},
    )
    return resp.json()["id"]


def _get_category_id(client, category_type="expense"):
    resp = client.get("/api/categories", params={"type": category_type})
    return resp.json()[0]["id"]


def test_create_expense_updates_balance(client):
    register_and_login(client)
    account_id = _create_account(client, "10000.00")
    cat_id = _get_category_id(client, "expense")

    resp = client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "1500.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-10",
            "description": "Dinner",
        },
    )
    assert resp.status_code == 201

    accounts = client.get("/api/accounts").json()
    assert accounts[0]["current_balance"] == "8500.00"


def test_create_income_updates_balance(client):
    register_and_login(client)
    account_id = _create_account(client, "10000.00")
    cat_id = _get_category_id(client, "income")

    client.post(
        "/api/transactions",
        json={
            "transaction_type": "income",
            "amount": "3000.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-10",
            "description": "Freelance payment",
        },
    )
    accounts = client.get("/api/accounts").json()
    assert accounts[0]["current_balance"] == "13000.00"


def test_reject_zero_amount(client):
    register_and_login(client)
    account_id = _create_account(client)
    resp = client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "0",
            "account_id": account_id,
            "transaction_date": "2026-08-10",
            "description": "Invalid",
        },
    )
    assert resp.status_code == 422


def test_edit_transaction_reverses_and_reapplies_balance(client):
    register_and_login(client)
    account_id = _create_account(client, "10000.00")
    cat_id = _get_category_id(client, "expense")

    created = client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "1000.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-10",
            "description": "Original",
        },
    ).json()

    # balance now 9000
    resp = client.put(
        f"/api/transactions/{created['id']}",
        json={
            "transaction_type": "expense",
            "amount": "2500.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-11",
            "description": "Edited",
        },
    )
    assert resp.status_code == 200

    accounts = client.get("/api/accounts").json()
    # 10000 - 2500 = 7500 (not 10000 - 1000 - 2500)
    assert accounts[0]["current_balance"] == "7500.00"


def test_delete_transaction_reverses_balance(client):
    register_and_login(client)
    account_id = _create_account(client, "10000.00")
    cat_id = _get_category_id(client, "expense")

    created = client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "1000.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-10",
            "description": "To delete",
        },
    ).json()

    resp = client.delete(f"/api/transactions/{created['id']}")
    assert resp.status_code == 204

    accounts = client.get("/api/accounts").json()
    assert accounts[0]["current_balance"] == "10000.00"


def test_search_transactions(client):
    register_and_login(client)
    account_id = _create_account(client)
    cat_id = _get_category_id(client, "expense")

    client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "500.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-10",
            "description": "Coffee shop visit",
        },
    )
    client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "200.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-11",
            "description": "Bus fare",
        },
    )

    resp = client.get("/api/transactions", params={"search": "Coffee"})
    body = resp.json()
    assert body["total"] == 1
    assert "Coffee" in body["items"][0]["description"]


def test_transaction_cross_user_isolation(client):
    register_and_login(client, email="owner@example.com")
    account_id = _create_account(client)
    cat_id = _get_category_id(client, "expense")
    txn = client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "100.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-10",
            "description": "Owner's transaction",
        },
    ).json()

    client.cookies.clear()
    register_and_login(client, email="intruder@example.com")
    resp = client.get(f"/api/transactions", params={"search": "Owner"})
    assert resp.json()["total"] == 0

    resp = client.delete(f"/api/transactions/{txn['id']}")
    assert resp.status_code == 404

    resp = client.put(
        f"/api/transactions/{txn['id']}",
        json={
            "transaction_type": "expense",
            "amount": "999.00",
            "account_id": account_id,
            "transaction_date": "2026-08-10",
            "description": "Hijacked",
        },
    )
    assert resp.status_code == 404
