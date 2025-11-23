from fastapi.testclient import TestClient

from backend.api.main import app


def test_get_problems_returns_data():
    with TestClient(app) as client:
        resp = client.get("/api/problems")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 50
        sample = data[0]
        for key in ["id", "statement", "choices", "grade", "year"]:
            assert key in sample


def test_get_tags_returns_whitelist():
    with TestClient(app) as client:
        resp = client.get("/api/tags")
        assert resp.status_code == 200
        data = resp.json()
        assert "tags" in data
        tags = data["tags"]
        assert isinstance(tags, dict)
        assert "Number Theory" in tags
