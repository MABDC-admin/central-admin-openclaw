import asyncio
from dataclasses import dataclass
from typing import Any

from command_center.approvals import approval_expiry, build_approval_text
from command_center.commands import CommandRegistry
from command_center.models import AuditEventType, JobStatus


@dataclass(frozen=True)
class JobSubmissionResult:
    job_id: str
    status: JobStatus
    approval_id: str | None = None


class JobSubmissionService:
    def __init__(
        self,
        repository,
        registry: CommandRegistry,
        telegram_client=None,
    ) -> None:
        self.repository = repository
        self.registry = registry
        self.telegram_client = telegram_client

    async def submit(
        self,
        command_name: str,
        requested_by: str,
        payload: dict[str, Any] | None = None,
    ) -> JobSubmissionResult:
        payload = payload or {}
        command = self.registry.get(command_name)
        if not command.dangerous:
            job_id = await self.repository.create_job(
                command_name,
                requested_by,
                payload,
                JobStatus.PENDING,
            )
            await self.repository.write_audit_log(
                AuditEventType.JOB_CREATED,
                actor=requested_by,
                details={"command_name": command_name},
                job_id=job_id,
            )
            return JobSubmissionResult(job_id=job_id, status=JobStatus.PENDING)

        job_id = await self.repository.create_job(
            command_name,
            requested_by,
            payload,
            JobStatus.WAITING_APPROVAL,
        )
        approval_id = await self.repository.create_approval(
            job_id,
            action_label=command_name,
            requested_by=requested_by,
            expires_at=approval_expiry(),
        )
        await self.repository.write_audit_log(
            AuditEventType.APPROVAL_REQUESTED,
            actor=requested_by,
            details={"command_name": command_name},
            job_id=job_id,
            approval_id=approval_id,
        )
        if self.telegram_client:
            await self.telegram_client.send_approval_request(
                build_approval_text(command_name, requested_by),
                approval_id,
            )
        return JobSubmissionResult(
            job_id=job_id,
            status=JobStatus.WAITING_APPROVAL,
            approval_id=approval_id,
        )


class JobRunner:
    def __init__(self, repository, registry: CommandRegistry) -> None:
        self.repository = repository
        self.registry = registry

    async def run_once(self) -> bool:
        job = await self.repository.claim_next_pending_job()
        if job is None:
            return False

        job_id = str(job["id"])
        command_name = str(job["command_name"])
        actor = str(job["requested_by"])
        payload = dict(job["payload"] or {})
        await self.repository.write_audit_log(
            AuditEventType.JOB_STARTED,
            actor="worker",
            details={"command_name": command_name},
            job_id=job_id,
        )
        try:
            command = self.registry.get(command_name)
            result = command.handler(payload)
        except Exception as exc:
            await self.repository.update_job_status(
                job_id,
                JobStatus.FAILED,
                error=str(exc),
            )
            await self.repository.write_audit_log(
                AuditEventType.JOB_FAILED,
                actor="worker",
                details={"command_name": command_name, "error": str(exc), "requested_by": actor},
                job_id=job_id,
            )
            return True

        await self.repository.update_job_status(
            job_id,
            JobStatus.SUCCEEDED,
            result=result,
        )
        await self.repository.write_audit_log(
            AuditEventType.JOB_SUCCEEDED,
            actor="worker",
            details={"command_name": command_name, "requested_by": actor},
            job_id=job_id,
        )
        return True

    async def run_forever(self, idle_sleep_seconds: float = 5.0) -> None:
        while True:
            ran = await self.run_once()
            if not ran:
                await asyncio.sleep(idle_sleep_seconds)
