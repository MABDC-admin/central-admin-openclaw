from datetime import UTC, datetime, timedelta

import pytest

from command_center.approvals import ApprovalDecisionError, ApprovalService
from command_center.models import ApprovalStatus, AuditEventType, JobStatus


class FakeRepository:
    def __init__(self, approval: dict | None):
        self.approval = approval
        self.approval_updates = []
        self.job_updates = []
        self.audit_logs = []

    async def get_approval(self, approval_id: str):
        if self.approval and self.approval["id"] == approval_id:
            return self.approval
        return None

    async def decide_approval(self, approval_id, status, decided_by):
        self.approval_updates.append((approval_id, status, decided_by))
        self.approval["status"] = status.value

    async def update_job_status(self, job_id, status, result=None, error=None):
        self.job_updates.append((job_id, status, result, error))

    async def write_audit_log(self, event_type, actor, details, job_id=None, approval_id=None):
        self.audit_logs.append((event_type, actor, details, job_id, approval_id))


def pending_approval(expires_at=None):
    return {
        "id": "approval-1",
        "job_id": "job-1",
        "status": ApprovalStatus.PENDING.value,
        "action_label": "Trash 10 Gmail messages",
        "requested_by": "telegram",
        "expires_at": expires_at or datetime.now(UTC) + timedelta(minutes=5),
    }


@pytest.mark.asyncio
async def test_approve_pending_approval_marks_job_pending():
    repo = FakeRepository(pending_approval())
    service = ApprovalService(repo)

    result = await service.decide("approval-1", "approve", "telegram:123")

    assert result.ok is True
    assert repo.approval_updates == [
        ("approval-1", ApprovalStatus.APPROVED, "telegram:123"),
    ]
    assert repo.job_updates == [("job-1", JobStatus.PENDING, None, None)]
    assert repo.audit_logs[0][0] == AuditEventType.APPROVAL_APPROVED


@pytest.mark.asyncio
async def test_reject_pending_approval_cancels_job():
    repo = FakeRepository(pending_approval())
    service = ApprovalService(repo)

    result = await service.decide("approval-1", "reject", "telegram:123")

    assert result.ok is True
    assert repo.approval_updates == [
        ("approval-1", ApprovalStatus.REJECTED, "telegram:123"),
    ]
    assert repo.job_updates == [("job-1", JobStatus.CANCELED, None, None)]
    assert repo.audit_logs[0][0] == AuditEventType.APPROVAL_REJECTED


@pytest.mark.asyncio
async def test_missing_approval_returns_error():
    repo = FakeRepository(None)
    service = ApprovalService(repo)

    result = await service.decide("missing", "approve", "telegram:123")

    assert result.ok is False
    assert result.message == "Approval not found."


@pytest.mark.asyncio
async def test_already_decided_approval_returns_error():
    approval = pending_approval()
    approval["status"] = ApprovalStatus.APPROVED.value
    repo = FakeRepository(approval)
    service = ApprovalService(repo)

    result = await service.decide("approval-1", "approve", "telegram:123")

    assert result.ok is False
    assert result.message == "Approval is already approved."


@pytest.mark.asyncio
async def test_expired_approval_expires_job():
    expired = datetime.now(UTC) - timedelta(seconds=1)
    repo = FakeRepository(pending_approval(expires_at=expired))
    service = ApprovalService(repo)

    result = await service.decide("approval-1", "approve", "telegram:123")

    assert result.ok is False
    assert result.message == "Approval expired."
    assert repo.approval_updates == [
        ("approval-1", ApprovalStatus.EXPIRED, "telegram:123"),
    ]
    assert repo.job_updates == [("job-1", JobStatus.EXPIRED, None, None)]
    assert repo.audit_logs[0][0] == AuditEventType.APPROVAL_EXPIRED


@pytest.mark.asyncio
async def test_unknown_decision_raises_error():
    repo = FakeRepository(pending_approval())
    service = ApprovalService(repo)

    with pytest.raises(ApprovalDecisionError):
        await service.decide("approval-1", "maybe", "telegram:123")
