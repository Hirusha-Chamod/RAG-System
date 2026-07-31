"""
Phase 3 LangGraph Workflow unit tests (Chat, Retrieval, Fallback, Session Memory).
"""

from fastapi.testclient import TestClient
from app.main import app


def _get_auth_headers(client: TestClient, username: str = "workflow_user") -> dict:
    """Helper to register user and return Bearer auth headers."""
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


def test_chat_fallback_when_no_docs():
    """When no relevant docs exist, /chat triggers deterministic fallback (relevance_action='fallback')."""
    with TestClient(app) as client:
        headers = _get_auth_headers(client, "user_nodocs_3way")
        chat_req = {
            "message": "What is the secret passphrase for quantum core?",
            "session_id": "session_fallback_1",
            "model": "google/gemma-4-31b-it:free",
        }
        resp = client.post("/chat", json=chat_req, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["relevance_action"] == "fallback"
        assert "don't have any relevant documents" in data["answer"]


def test_retrieve_unauthenticated():
    """Unauthenticated /retrieve call returns 401/403."""
    with TestClient(app) as client:
        resp = client.post("/retrieve", json={"query": "test"})
        assert resp.status_code in (401, 403)


def test_retrieve_endpoint(tmp_path):
    """Ingest a document and verify /retrieve returns matching chunks for that user."""
    sample_text = (
        "Project Orion Architecture Document.\n\n"
        "Orion uses a decentralized quantum consensus algorithm operating on port 9090.\n"
        "All node communications are encrypted using AES-256-GCM."
    )
    doc_file = tmp_path / "orion.txt"
    doc_file.write_text(sample_text, encoding="utf-8")

    with TestClient(app) as client:
        headers = _get_auth_headers(client, "user_orion_3way")

        # Ingest document
        with open(doc_file, "rb") as f:
            ingest_resp = client.post(
                "/ingest",
                files=[("files", ("orion.txt", f, "text/plain"))],
                headers=headers,
            )
        assert ingest_resp.status_code == 200
        assert ingest_resp.json()["total_chunks"] > 0

        # Retrieve documents
        ret_resp = client.post(
            "/retrieve",
            json={"query": "quantum consensus algorithm port"},
            headers=headers,
        )
        assert ret_resp.status_code == 200
        data = ret_resp.json()
        assert len(data["results"]) > 0
        assert "orion.txt" in data["results"][0]["source"]


def test_invalid_model_rejection():
    """Requesting an un-whitelisted model returns 400 Bad Request."""
    with TestClient(app) as client:
        headers = _get_auth_headers(client, "user_model_test_3way")
        chat_req = {
            "message": "Hello",
            "session_id": "sess_1",
            "model": "invalid/paid-model-1000",
        }
        resp = client.post("/chat", json=chat_req, headers=headers)
        assert resp.status_code == 400
        assert "Invalid model" in resp.json()["detail"]
