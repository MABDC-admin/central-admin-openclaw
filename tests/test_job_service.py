from command_center.commands import CommandRegistry
from command_center.job_service import JobRunner, JobSubmissionService
from command_center.models import AuditEventType, CommandDefinition, JobStatus


class FakeRepository:
    def __init__(self):
        self.jobs = {}
        self.created = []
        self.updated = []
        self.audit_logs = []
        self.approvals = []
        self.next_job_id = 1

    async def create_job(self, command_name, requested_by, payload, status=JobStatus.PENDING):
        job_id = f"job-{self.next_job_id}"
        self.next_job_id += 1
        self.jobs[job_id] = {
            "id": job_id,
            "command_name": command_name,
            "requested_by": requested_by,
            "payload": payload,
            "status": status.value,
        }
        self.created.append((command_name, requested_by, payload, status))
        return job_id

    async def create_approval(self, job_id, action_label, requested_by, expires_at):
        self.approvals.append((job_id, action_label, requested_by, expires_at))
        return "approval-1"

    async def update_job_status(self, job_id, status, result=None, error=None):
        self.jobs[job_id]["status"] = status.value
        self.updated.append((job_id, status, result, error))

    async def claim_next_pending_job(self):
        for job in self.jobs.values():
            if job["status"] == JobStatus.PENDING.value:
                job["status"] = JobStatus.RUNNING.value
                return dict(job)
        return None

    async def write_audit_log(self, event_type, actor, details, job_id=None, approval_id=None):
        self.audit_logs.append((event_type, actor, details, job_id, approval_id))


class FakeTelegramClient:
    def __init__(self):
        self.approvals = []

    async def send_approval_request(self, text, approval_id):
        self.approvals.append((text, approval_id))
        return {"ok": True}


def registry_with_safe_and_dangerous():
    registry = CommandRegistry()
    registry.register(
        CommandDefinition("safe.echo", "Echo", False),
        lambda payload: {"echo": payload["value"]},
    )
    registry.register(
        CommandDefinition("danger.poweroff", "Power off", True),
        lambda payload: {"never": "runs"},
    )
    return registry


async def test_submit_safe_command_creates_pending_job():
    repository = FakeRepository()
    service = JobSubmissionService(repository, registry_with_safe_and_dangerous())

    result = await service.submit("safe.echo", "dashboard", {"value": "ok"})

    assert result.job_id == "job-1"
    assert result.status == JobStatus.PENDING
    assert repository.created == [
        ("safe.echo", "dashboard", {"value": "ok"}, JobStatus.PENDING)
    ]
    assert repository.audit_logs[0][0] == AuditEventType.JOB_CREATED


async def test_submit_dangerous_command_requests_telegram_approval():
    repository = FakeRepository()
    telegram_client = FakeTelegramClient()
    service = JobSubmissionService(
        repository,
        registry_with_safe_and_dangerous(),
        telegram_client=telegram_client,
    )

    result = await service.submit("danger.poweroff", "dashboard", {})

    assert result.status == JobStatus.WAITING_APPROVAL
    assert result.approval_id == "approval-1"
    assert repository.approvals[0][0] == "job-1"
    assert telegram_client.approvals == [
        (
            "Approval required\n\n"
            "Action: danger.poweroff\n"
            "Target: dashboard\n"
            "Expires: 10 minutes\n\n"
            "Choose Approve only if this is expected.",
            "approval-1",
        )
    ]


async def test_job_runner_executes_pending_safe_job():
    repository = FakeRepository()
    await repository.create_job("safe.echo", "dashboard", {"value": "ok"})
    runner = JobRunner(repository, registry_with_safe_and_dangerous())

    ran = await runner.run_once()

    assert ran is True
    assert repository.updated[-1] == (
        "job-1",
        JobStatus.SUCCEEDED,
        {"echo": "ok"},
        None,
    )
    assert repository.audit_logs[-1][0] == AuditEventType.JOB_SUCCEEDED


async def test_job_runner_marks_unknown_command_failed():
    repository = FakeRepository()
    await repository.create_job("missing.command", "dashboard", {})
    runner = JobRunner(repository, registry_with_safe_and_dangerous())

    ran = await runner.run_once()

    assert ran is True
    assert repository.updated[-1][1] == JobStatus.FAILED
    assert "Unknown command" in repository.updated[-1][3]
