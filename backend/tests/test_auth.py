"""
Unit tests for JWT User Authentication: /auth/signup, /auth/login, /auth/me.
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_signup_and_login():
    uid = str(uuid.uuid4())[:6]
    username = f"user_{uid}"
    email = f"user_{uid}@example.com"
    password = "SecurePassword123!"

    with TestClient(app) as test_client:
        # 1. Signup user
        signup_data = {
            "username": username,
            "email": email,
            "password": password,
        }
        resp = test_client.post("/auth/signup", json=signup_data)
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["username"] == username
        token = data["access_token"]

        # 2. Login user
        login_data = {
            "username_or_email": username,
            "password": password,
        }
        login_resp = test_client.post("/auth/login", json=login_data)
        assert login_resp.status_code == 200
        login_data_resp = login_resp.json()
        assert "access_token" in login_data_resp

        # 3. Access /auth/me with Bearer token
        headers = {"Authorization": f"Bearer {token}"}
        me_resp = test_client.get("/auth/me", headers=headers)
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["username"] == username
        assert me_data["email"] == email


def test_auth_unauthorized_access():
    with TestClient(app) as test_client:
        # Missing header -> 401/403
        resp = test_client.get("/auth/me")
        assert resp.status_code in (401, 403)

        # Invalid token -> 401
        resp_invalid = test_client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert resp_invalid.status_code == 401
