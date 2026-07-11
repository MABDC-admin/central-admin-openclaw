from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class JobStatus(StrEnum):
    PENDING = "pending"
    WAITING_APPROVAL = "waiting_approval"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    EXPIRED = "expired"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    USED = "used"


class AuditEventType(StrEnum):
    JOB_CREATED = "job_created"
    JOB_STARTED = "job_started"
    JOB_SUCCEEDED = "job_succeeded"
    JOB_FAILED = "job_failed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_EXPIRED = "approval_expired"


@dataclass(frozen=True)
class CommandDefinition:
    name: str
    description: str
    dangerous: bool


@dataclass(frozen=True)
class JobRecord:
    id: str
    command_name: str
    status: JobStatus
    requested_by: str
    payload: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class ApprovalTicket:
    id: str
    job_id: str
    status: ApprovalStatus
    action_label: str
    requested_by: str
    expires_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return self.status == ApprovalStatus.PENDING and now >= self.expires_at
