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


def test_dashboard_home_renders():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "MABDC Command Center" in response.text


def test_jobs_page_renders():
    client = TestClient(create_app())

    response = client.get("/jobs")

    assert response.status_code == 200
    assert "Recent Jobs" in response.text
