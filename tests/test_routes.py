from fastapi.testclient import TestClient

from command_center.main import create_app
from command_center.models import JobStatus


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


class FakeJobSubmissionService:
    def __init__(self):
        self.calls = []

    async def submit(self, command_name, requested_by, payload):
        self.calls.append((command_name, requested_by, payload))
        return type(
            "Result",
            (),
            {
                "job_id": "job-1",
                "status": JobStatus.PENDING,
                "approval_id": None,
            },
        )()


def test_submit_job_endpoint_creates_job():
    app = create_app()
    fake_service = FakeJobSubmissionService()
    app.state.job_submission_service = fake_service
    client = TestClient(app)

    response = client.post(
        "/api/jobs",
        json={"command_name": "vps.health", "requested_by": "dashboard", "payload": {}},
    )

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-1",
        "status": "pending",
        "approval_id": None,
    }
    assert fake_service.calls == [("vps.health", "dashboard", {})]


def test_dashboard_run_button_submits_job():
    app = create_app()
    fake_service = FakeJobSubmissionService()
    app.state.job_submission_service = fake_service
    client = TestClient(app, follow_redirects=False)

    response = client.post("/jobs", data={"command_name": "vps.health"})

    assert response.status_code == 303
    assert response.headers["location"] == "/jobs"
    assert fake_service.calls == [("vps.health", "dashboard", {})]
