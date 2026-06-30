"""End-to-end smoke test: drive the real FastAPI app through a TestClient.

Sets harmless OPENAI/MONGO env before importing the app (the OpenAI client is
constructed at import). The TestClient runs without the lifespan context manager,
so no live OpenAI/Mongo connection is made.
"""
import os

import pytest

pytestmark = pytest.mark.e2e


def _client():
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    os.environ.setdefault("MONGO_HOST", "localhost")
    os.environ.setdefault("MONGO_PORT", "27017")
    from fastapi.testclient import TestClient
    from server import app
    return TestClient(app)


def test_openapi_schema_is_served():
    client = _client()
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/explanation" in response.json().get("paths", {})
