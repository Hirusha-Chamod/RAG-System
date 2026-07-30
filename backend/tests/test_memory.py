"""
Unit tests for Long-Term User Memory endpoints: GET /memory, POST /memory, DELETE /memory.
"""

from fastapi.testclient import TestClient
from app.main import app


def _get_auth_headers(client: TestClient, username: str = "memory_test_user") -> dict:
    """Helper to register a test user and return Bearer auth headers."""
    signup_data = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "Password123!",
    }
    resp = client.post("/auth/signup", json=signup_data)
    if resp.status_code == 201:
        token = resp.json()["access_token"]
    else:
        login_resp = client.post(
            "/auth/login",
            json={"username_or_email": username, "password": "Password123!"},
        )
        token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_memory_crud_operations():
    """Test full CRUD cycle for long-term user memory."""
    with TestClient(app) as client:
        headers = _get_auth_headers(client, "mem_crud_user")

        # 1. GET /memory (Initially empty)
        resp = client.get("/memory", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()["memories"]) == 0

        # 2. POST /memory (Set preference)
        save_data = {"key": "preferred_style", "value": "concise bullet points"}
        post_resp = client.post("/memory", json=save_data, headers=headers)
        assert post_resp.status_code == 201
        assert post_resp.json()["status"] == "success"

        # 3. GET /memory (Verify entry exists)
        get_resp = client.get("/memory", headers=headers)
        assert get_resp.status_code == 200
        memories = get_resp.json()["memories"]
        assert len(memories) == 1
        assert memories[0]["key"] == "preferred_style"

        # 4. DELETE /memory?key=preferred_style (Delete single key)
        del_resp = client.delete("/memory?key=preferred_style", headers=headers)
        assert del_resp.status_code == 200

        # 5. GET /memory (Verify empty again)
        final_get = client.get("/memory", headers=headers)
        assert final_get.status_code == 200
        assert len(final_get.json()["memories"]) == 0


def test_memory_unauthenticated_blocking():
    """Unauthenticated call to /memory endpoints returns 401/403."""
    with TestClient(app) as client:
        assert client.get("/memory").status_code in (401, 403)
        assert client.post("/memory", json={"key": "k", "value": "v"}).status_code in (401, 403)
        assert client.delete("/memory").status_code in (401, 403)
