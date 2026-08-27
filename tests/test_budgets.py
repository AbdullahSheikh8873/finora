from tests.conftest import register_and_login


def _account(client):
    return client.post(
        "/api/accounts",
        json={"name": "Main", "account_type": "bank", "opening_balance": "50000.00", "currency": "PKR"},
    ).json()["id"]


def _category(client, name="Food"):
    cats = client.get("/api/categories", params={"type": "expense"}).json()
    return next(c["id"] for c in cats if c["name"] == name)


def test_create_budget_and_track_usage(client):
    register_and_login(client)
    account_id = _account(client)
    cat_id = _category(client)

    resp = client.post(
        "/api/budgets", json={"category_id": cat_id, "amount": "10000.00", "month": 8, "year": 2026}
    )
    assert resp.status_code == 201

    client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "3200.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-05",
            "description": "Weekly groceries",
        },
    )

    budgets = client.get("/api/budgets", params={"month": 8, "year": 2026}).json()
    assert len(budgets) == 1
    assert budgets[0]["spent"] == "3200.00"
    assert budgets[0]["remaining"] == "6800.00"
    assert budgets[0]["status"] == "safe"


def test_budget_status_thresholds(client):
    register_and_login(client)
    account_id = _account(client)
    cat_id = _category(client)

    client.post(
        "/api/budgets", json={"category_id": cat_id, "amount": "1000.00", "month": 8, "year": 2026}
    )
    client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "750.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-05",
            "description": "Big grocery run",
        },
    )
    budgets = client.get("/api/budgets", params={"month": 8, "year": 2026}).json()
    assert budgets[0]["status"] == "warning"

    client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "200.00",
            "account_id": account_id,
            "category_id": cat_id,
            "transaction_date": "2026-08-06",
            "description": "More groceries",
        },
    )
    budgets = client.get("/api/budgets", params={"month": 8, "year": 2026}).json()
    assert budgets[0]["status"] == "critical"


def test_duplicate_budget_rejected(client):
    register_and_login(client)
    _account(client)
    cat_id = _category(client)
    client.post(
        "/api/budgets", json={"category_id": cat_id, "amount": "1000.00", "month": 8, "year": 2026}
    )
    resp = client.post(
        "/api/budgets", json={"category_id": cat_id, "amount": "2000.00", "month": 8, "year": 2026}
    )
    assert resp.status_code == 400


def test_delete_budget(client):
    register_and_login(client)
    _account(client)
    cat_id = _category(client)
    created = client.post(
        "/api/budgets", json={"category_id": cat_id, "amount": "1000.00", "month": 8, "year": 2026}
    ).json()
    resp = client.delete(f"/api/budgets/{created['id']}")
    assert resp.status_code == 204
    budgets = client.get("/api/budgets", params={"month": 8, "year": 2026}).json()
    assert len(budgets) == 0
