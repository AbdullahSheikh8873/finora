from tests.conftest import register_and_login


def test_transfer_moves_money_atomically(client):
    register_and_login(client)
    a = client.post(
        "/api/accounts",
        json={"name": "Checking", "account_type": "bank", "opening_balance": "10000.00", "currency": "PKR"},
    ).json()
    b = client.post(
        "/api/accounts",
        json={"name": "Savings", "account_type": "savings", "opening_balance": "2000.00", "currency": "PKR"},
    ).json()

    resp = client.post(
        "/api/transfers",
        json={
            "from_account_id": a["id"],
            "to_account_id": b["id"],
            "amount": "3000.00",
            "transfer_date": "2026-08-15",
            "description": "Move to savings",
        },
    )
    assert resp.status_code == 201

    accounts = {acc["name"]: acc for acc in client.get("/api/accounts").json()}
    assert accounts["Checking"]["current_balance"] == "7000.00"
    assert accounts["Savings"]["current_balance"] == "5000.00"


def test_transfer_same_account_rejected(client):
    register_and_login(client)
    a = client.post(
        "/api/accounts",
        json={"name": "Only", "account_type": "bank", "opening_balance": "1000.00", "currency": "PKR"},
    ).json()
    resp = client.post(
        "/api/transfers",
        json={
            "from_account_id": a["id"],
            "to_account_id": a["id"],
            "amount": "100.00",
            "transfer_date": "2026-08-15",
        },
    )
    assert resp.status_code == 400


def test_transfer_cross_user_account_rejected(client):
    register_and_login(client, email="victim@example.com")
    victim_account = client.post(
        "/api/accounts",
        json={"name": "Victim Bank", "account_type": "bank", "opening_balance": "5000.00", "currency": "PKR"},
    ).json()

    client.cookies.clear()
    register_and_login(client, email="attacker@example.com")
    attacker_account = client.post(
        "/api/accounts",
        json={"name": "Attacker Bank", "account_type": "bank", "opening_balance": "0", "currency": "PKR"},
    ).json()

    resp = client.post(
        "/api/transfers",
        json={
            "from_account_id": victim_account["id"],
            "to_account_id": attacker_account["id"],
            "amount": "5000.00",
            "transfer_date": "2026-08-15",
        },
    )
    assert resp.status_code == 404
