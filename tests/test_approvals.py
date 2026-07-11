from datetime import UTC, datetime, timedelta

from command_center.models import ApprovalStatus, ApprovalTicket, JobStatus


def test_approval_ticket_detects_expiry():
    ticket = ApprovalTicket(
        id="approval_1",
        job_id="job_1",
        status=ApprovalStatus.PENDING,
        action_label="Trash 10 Gmail messages",
        requested_by="telegram",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    assert ticket.is_expired(datetime.now(UTC)) is True


def test_approval_ticket_pending_not_expired():
    ticket = ApprovalTicket(
        id="approval_1",
        job_id="job_1",
        status=ApprovalStatus.PENDING,
        action_label="Run VPS health check",
        requested_by="dashboard",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )

    assert ticket.is_expired(datetime.now(UTC)) is False


def test_job_status_values_are_stable():
    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.SUCCEEDED.value == "succeeded"
