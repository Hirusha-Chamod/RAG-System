"""
Phase 2 Ingestion pipeline verification tests with JWT Bearer Authentication.
"""

from fastapi.testclient import TestClient
from app.main import app


def _get_auth_headers(client: TestClient, username: str = "ingest_user") -> dict:
    """Helper to register a user and return Auth headers."""
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


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_list_models():
    with TestClient(app) as client:
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert "google/gemma-4-31b-it:free" in data["models"]
        assert data["default_model"] == "google/gemma-4-31b-it:free"


def test_ingest_unauthenticated():
    """Unauthenticated call to /ingest returns 401/403."""
    with TestClient(app) as client:
        files = [("files", ("test.txt", b"some content", "text/plain"))]
        response = client.post("/ingest", files=files)
        assert response.status_code in (401, 403)


def test_ingest_unsupported_file():
    """Unsupported extension returns 200 OK with error status in per-file results."""
    with TestClient(app) as client:
        headers = _get_auth_headers(client, "ingest_user_1")
        files = [("files", ("test.invalid", b"some binary data", "application/octet-stream"))]
        response = client.post("/ingest", files=files, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["status"] == "error"
        assert "Unsupported file type" in data["results"][0]["error_message"]


def test_ingest_txt_file(tmp_path):
    """Ingest a text file with JWT authentication and verify parent/child chunks created."""
    sample_text = (
        "AI Nexus RAG Engine Document.\n\n"
        "This is the first paragraph detailing general system concepts and parent-child chunking.\n"
        "Vector databases like ChromaDB store child embeddings, while SQLite stores parent texts.\n\n"
        "This is the second paragraph covering FastAPI endpoints and OpenRouter LLM synthesis."
    )

    txt_file = tmp_path / "sample.txt"
    txt_file.write_text(sample_text, encoding="utf-8")

    with TestClient(app) as client:
        headers = _get_auth_headers(client, "ingest_user_2")
        with open(txt_file, "rb") as f:
            files = [("files", ("sample.txt", f, "text/plain"))]
            response = client.post("/ingest", files=files, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["status"] == "success"
        assert data["total_chunks"] > 0
        assert data["results"][0]["filename"] == "sample.txt"
