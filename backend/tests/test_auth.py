"""
Unit tests for JWT User Authentication: /auth/signup, /auth/login, /auth/me.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_signup_and_login():
    with TestClient(app) as test_client:
        # 1. Signup user
        signup_data = {
            "username": "testuser_auth",
            "email": "testuser@example.com",
            "password": "SecurePassword123!",
        }
        resp = test_client.post("/auth/signup", json=signup_data)
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["username"] == "testuser_auth"
        token = data["access_token"]

        # 2. Login user
        login_data = {
            "username_or_email": "testuser_auth",
            "password": "SecurePassword123!",
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
        assert me_data["username"] == "testuser_auth"
        assert me_data["email"] == "testuser@example.com"


def test_auth_unauthorized_access():
    with TestClient(app) as test_client:
        # Missing header -> 401
        resp = test_client.get("/auth/me")
        assert resp.status_code == 403 or resp.status_code == 401

        # Invalid token -> 401
        resp_invalid = test_client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert resp_invalid.status_code == 401
