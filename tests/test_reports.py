from decimal import Decimal

from tests.conftest import register_and_login


def test_dashboard_zero_income_no_division_error(client):
    register_and_login(client)
    client.post(
        "/api/accounts",
        json={"name": "Main", "account_type": "bank", "opening_balance": "1000.00", "currency": "PKR"},
    )
    resp = client.get("/api/reports/dashboard")
    assert resp.status_code == 200
    assert resp.json()["summary"]["savings_rate"] == 0.0


def test_dashboard_reflects_real_transactions(client):
    register_and_login(client)
    account_id = client.post(
        "/api/accounts",
        json={"name": "Main", "account_type": "bank", "opening_balance": "0", "currency": "PKR"},
    ).json()["id"]

    income_cat = client.get("/api/categories", params={"type": "income"}).json()[0]["id"]
    expense_cat = client.get("/api/categories", params={"type": "expense"}).json()[0]["id"]

    import datetime

    today = datetime.date.today().isoformat()

    client.post(
        "/api/transactions",
        json={
            "transaction_type": "income",
            "amount": "10000.00",
            "account_id": account_id,
            "category_id": income_cat,
            "transaction_date": today,
            "description": "Salary",
        },
    )
    client.post(
        "/api/transactions",
        json={
            "transaction_type": "expense",
            "amount": "4000.00",
            "account_id": account_id,
            "category_id": expense_cat,
            "transaction_date": today,
            "description": "Rent",
        },
    )

    resp = client.get("/api/reports/dashboard")
    summary = resp.json()["summary"]
    assert summary["income"] == 10000.0
    assert summary["expenses"] == 4000.0
    assert summary["net_savings"] == 6000.0
    assert summary["savings_rate"] == 60.0
