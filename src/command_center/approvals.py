from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from command_center.models import ApprovalStatus, AuditEventType, JobStatus


def approval_expiry(minutes: int = 10) -> datetime:
    return datetime.now(UTC) + timedelta(minutes=minutes)


def build_approval_text(action_label: str, target_label: str, expires_minutes: int = 10) -> str:
    return (
        "Approval required\n\n"
        f"Action: {action_label}\n"
        f"Target: {target_label}\n"
        f"Expires: {expires_minutes} minutes\n\n"
        "Choose Approve only if this is expected."
    )


class ApprovalRepository(Protocol):
    async def get_approval(self, approval_id: str): ...

    async def decide_approval(
        self,
        approval_id: str,
        status: ApprovalStatus,
        decided_by: str,
    ) -> None: ...

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: dict | None = None,
        error: str | None = None,
    ) -> None: ...

    async def write_audit_log(
        self,
        event_type: AuditEventType,
        actor: str,
        details: dict,
        job_id: str | None = None,
        approval_id: str | None = None,
    ) -> None: ...


class ApprovalDecisionError(ValueError):
    pass


@dataclass(frozen=True)
class ApprovalDecisionResult:
    ok: bool
    message: str
    approval_id: str
    job_id: str | None = None


class ApprovalService:
    def __init__(self, repository: ApprovalRepository) -> None:
        self.repository = repository

    async def decide(
        self,
        approval_id: str,
        decision: str,
        actor: str,
    ) -> ApprovalDecisionResult:
        if decision not in {"approve", "reject"}:
            raise ApprovalDecisionError(f"Unsupported approval decision: {decision}")

        approval = await self.repository.get_approval(approval_id)
        if approval is None:
            return ApprovalDecisionResult(
                ok=False,
                message="Approval not found.",
                approval_id=approval_id,
            )

        job_id = str(approval["job_id"])
        status = ApprovalStatus(str(approval["status"]))
        if status != ApprovalStatus.PENDING:
            return ApprovalDecisionResult(
                ok=False,
                message=f"Approval is already {status.value}.",
                approval_id=approval_id,
                job_id=job_id,
            )

        expires_at = approval["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if datetime.now(UTC) >= expires_at:
            await self.repository.decide_approval(approval_id, ApprovalStatus.EXPIRED, actor)
            await self.repository.update_job_status(job_id, JobStatus.EXPIRED)
            await self.repository.write_audit_log(
                AuditEventType.APPROVAL_EXPIRED,
                actor=actor,
                details={"action_label": approval["action_label"]},
                job_id=job_id,
                approval_id=approval_id,
            )
            return ApprovalDecisionResult(
                ok=False,
                message="Approval expired.",
                approval_id=approval_id,
                job_id=job_id,
            )

        if decision == "approve":
            await self.repository.decide_approval(approval_id, ApprovalStatus.APPROVED, actor)
            await self.repository.update_job_status(job_id, JobStatus.PENDING)
            await self.repository.write_audit_log(
                AuditEventType.APPROVAL_APPROVED,
                actor=actor,
                details={"action_label": approval["action_label"]},
                job_id=job_id,
                approval_id=approval_id,
            )
            return ApprovalDecisionResult(
                ok=True,
                message="Approved.",
                approval_id=approval_id,
                job_id=job_id,
            )

        await self.repository.decide_approval(approval_id, ApprovalStatus.REJECTED, actor)
        await self.repository.update_job_status(job_id, JobStatus.CANCELED)
        await self.repository.write_audit_log(
            AuditEventType.APPROVAL_REJECTED,
            actor=actor,
            details={"action_label": approval["action_label"]},
            job_id=job_id,
            approval_id=approval_id,
        )
        return ApprovalDecisionResult(
            ok=True,
            message="Rejected.",
            approval_id=approval_id,
            job_id=job_id,
        )
