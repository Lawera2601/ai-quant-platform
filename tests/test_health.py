from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_response_contract():
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok"},
    }
