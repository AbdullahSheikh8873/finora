from tests.conftest import register_and_login


def test_register_success(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Ayesha Khan",
            "email": "ayesha@example.com",
            "password": "SecurePass1",
            "confirm_password": "SecurePass1",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "ayesha@example.com"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_rejected(client):
    register_and_login(client, email="dupe@example.com")
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Another User",
            "email": "dupe@example.com",
            "password": "SecurePass1",
            "confirm_password": "SecurePass1",
        },
    )
    assert resp.status_code == 400


def test_register_password_mismatch_rejected(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Mismatch User",
            "email": "mismatch@example.com",
            "password": "SecurePass1",
            "confirm_password": "DifferentPass1",
        },
    )
    assert resp.status_code == 400


def test_register_weak_password_rejected(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Weak User",
            "email": "weak@example.com",
            "password": "weak",
            "confirm_password": "weak",
        },
    )
    assert resp.status_code == 422


def test_login_success(client):
    register_and_login(client, email="login@example.com", password="SecurePass1")
    resp = client.post(
        "/api/auth/login", json={"email": "login@example.com", "password": "SecurePass1"}
    )
    assert resp.status_code == 200
    assert "finora_access_token" in resp.cookies


def test_login_wrong_password(client):
    register_and_login(client, email="wrong@example.com", password="SecurePass1")
    resp = client.post(
        "/api/auth/login", json={"email": "wrong@example.com", "password": "WrongPass1"}
    )
    assert resp.status_code == 401


def test_protected_route_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout_clears_session(client):
    register_and_login(client, email="logout@example.com")
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200

    client.post("/api/auth/logout")
    client.cookies.clear()
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_change_password(client):
    register_and_login(client, email="changepw@example.com", password="SecurePass1")
    resp = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "SecurePass1",
            "new_password": "NewSecurePass2",
            "confirm_new_password": "NewSecurePass2",
        },
    )
    assert resp.status_code == 200

    client.cookies.clear()
    resp = client.post(
        "/api/auth/login", json={"email": "changepw@example.com", "password": "NewSecurePass2"}
    )
    assert resp.status_code == 200
