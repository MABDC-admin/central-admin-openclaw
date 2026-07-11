import json
from datetime import datetime
from typing import Any

from command_center.db import Database
from command_center.models import ApprovalStatus, AuditEventType, JobStatus


def _json_dumps(value: dict[str, Any] | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value)


def _json_loads(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def _decode_json_fields(row: dict[str, Any]) -> dict[str, Any]:
    for field in ("payload", "result", "details"):
        if field in row and row[field] is not None:
            row[field] = _json_loads(row[field])
    return row


class CommandCenterRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create_job(
        self,
        command_name: str,
        requested_by: str,
        payload: dict[str, Any],
        status: JobStatus = JobStatus.PENDING,
    ) -> str:
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                insert into command_center.jobs (command_name, status, requested_by, payload)
                values ($1, $2, $3, $4::jsonb)
                returning id::text
                """,
                command_name,
                status.value,
                requested_by,
                _json_dumps(payload),
            )
        return str(row["id"])

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                update command_center.jobs
                set status = $2, result = $3::jsonb, error = $4, updated_at = now()
                where id = $1::uuid
                """,
                job_id,
                status.value,
                _json_dumps(result),
                error,
            )

    async def list_recent_jobs(self, limit: int = 25) -> list[dict[str, Any]]:
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                select
                  id::text, command_name, status, requested_by,
                  payload, result, error, created_at
                from command_center.jobs
                order by created_at desc
                limit $1
                """,
                limit,
            )
        return [_decode_json_fields(dict(row)) for row in rows]

    async def claim_next_pending_job(self) -> dict[str, Any] | None:
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                update command_center.jobs
                set status = $1, updated_at = now()
                where id = (
                  select id
                  from command_center.jobs
                  where status = $2
                  order by created_at
                  for update skip locked
                  limit 1
                )
                returning
                  id::text, command_name, status, requested_by,
                  payload, result, error, created_at, updated_at
                """,
                JobStatus.RUNNING.value,
                JobStatus.PENDING.value,
            )
        return _decode_json_fields(dict(row)) if row else None

    async def create_approval(
        self,
        job_id: str,
        action_label: str,
        requested_by: str,
        expires_at: datetime,
    ) -> str:
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                insert into command_center.approvals
                  (job_id, status, action_label, requested_by, expires_at)
                values ($1::uuid, $2, $3, $4, $5)
                returning id::text
                """,
                job_id,
                ApprovalStatus.PENDING.value,
                action_label,
                requested_by,
                expires_at,
            )
        return str(row["id"])

    async def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                select
                  id::text, job_id::text, status, action_label,
                  requested_by, expires_at, decided_by, decided_at, created_at
                from command_center.approvals
                where id = $1::uuid
                """,
                approval_id,
            )
        return _decode_json_fields(dict(row)) if row else None

    async def decide_approval(
        self,
        approval_id: str,
        status: ApprovalStatus,
        decided_by: str,
    ) -> None:
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                update command_center.approvals
                set status = $2, decided_by = $3, decided_at = now()
                where id = $1::uuid
                """,
                approval_id,
                status.value,
                decided_by,
            )

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                select
                  id::text, command_name, status, requested_by,
                  payload, result, error, created_at, updated_at
                from command_center.jobs
                where id = $1::uuid
                """,
                job_id,
            )
        return _decode_json_fields(dict(row)) if row else None

    async def write_audit_log(
        self,
        event_type: AuditEventType,
        actor: str,
        details: dict[str, Any],
        job_id: str | None = None,
        approval_id: str | None = None,
    ) -> None:
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                insert into command_center.audit_logs
                  (event_type, actor, details, job_id, approval_id)
                values ($1, $2, $3::jsonb, $4::uuid, $5::uuid)
                """,
                event_type.value,
                actor,
                _json_dumps(details),
                job_id,
                approval_id,
            )
