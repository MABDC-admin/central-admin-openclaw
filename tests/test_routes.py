from fastapi.testclient import TestClient

from command_center.main import create_app


def test_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_commands_endpoint_lists_vps_health():
    client = TestClient(create_app())

    response = client.get("/api/commands")

    assert response.status_code == 200
    names = [item["name"] for item in response.json()["commands"]]
    assert "vps.health" in names
