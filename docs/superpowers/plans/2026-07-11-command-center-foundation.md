# Command Center Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working command center foundation: FastAPI app, private dashboard, Supabase schema, job/audit records, Telegram approval primitives, Docker deployment, and read-only server health checks.

**Architecture:** Use a small Python FastAPI application with focused modules for config, database access, command registry, approvals, audit logging, Telegram messaging, and dashboard routes. The first version is intentionally safe: it can create jobs, log events, show status, and send approval requests, but it does not execute destructive actions yet.

**Tech Stack:** Python 3.12, FastAPI, Jinja2, asyncpg, httpx, pydantic-settings, pytest, Docker Compose, existing Supabase Postgres.

---

## Scope

This plan implements the foundation and read-only slice only.

Included:

- local app scaffold
- FastAPI health endpoint
- dashboard shell
- Supabase schema migration
- job/audit/approval repository
- Telegram approval message sender
- safe command registry
- read-only VPS health command
- Docker Compose deployment under `/DATA/docker/command-center`

Deferred to later plans:

- Gmail OAuth and Trash execution
- PC node SSH command execution
- document watcher rewiring
- OpenClaw repair/start integration
- Hermes install/connect
- VPS browser automation

## File Structure

Create these files:

- `pyproject.toml` - Python project metadata and dependencies.
- `README.md` - local setup, environment variables, test, and deploy notes.
- `.env.example` - documented non-secret environment template.
- `.gitignore` - ignore virtualenv, caches, local secrets.
- `src/command_center/__init__.py` - package marker.
- `src/command_center/main.py` - FastAPI app factory and route mounting.
- `src/command_center/config.py` - typed settings from environment.
- `src/command_center/db.py` - asyncpg pool lifecycle and helpers.
- `src/command_center/models.py` - dataclasses/enums for jobs, approvals, audit events.
- `src/command_center/repositories.py` - database queries for jobs, approvals, audit logs, integrations.
- `src/command_center/commands.py` - safe command registry and read-only command handlers.
- `src/command_center/approvals.py` - approval creation, expiry, and decision logic.
- `src/command_center/telegram.py` - Telegram Bot API client.
- `src/command_center/routes_api.py` - JSON API routes.
- `src/command_center/routes_dashboard.py` - dashboard HTML routes.
- `src/command_center/templates/base.html` - shared dashboard layout.
- `src/command_center/templates/index.html` - dashboard overview.
- `src/command_center/templates/jobs.html` - job list.
- `src/command_center/static/app.css` - minimal dashboard CSS.
- `migrations/001_command_center_schema.sql` - Supabase schema and tables.
- `tests/conftest.py` - test fixtures.
- `tests/test_config.py` - settings tests.
- `tests/test_commands.py` - command registry tests.
- `tests/test_approvals.py` - approval behavior tests.
- `tests/test_routes.py` - FastAPI route tests.
- `deploy/docker-compose.yml` - deployable service definition.
- `deploy/command-center.env.example` - deployment env template.
- `deploy/README.md` - VPS deployment steps.

## Task 1: Project Scaffold

**Files:**

- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/command_center/__init__.py`
- Create: `README.md`

- [ ] **Step 1: Create project metadata**

Write `pyproject.toml`:

```toml
[project]
name = "central-admin-openclaw"
version = "0.1.0"
description = "Private single-user automation command center for MABDC"
requires-python = ">=3.12"
dependencies = [
  "asyncpg>=0.30.0",
  "fastapi>=0.115.0",
  "httpx>=0.27.0",
  "jinja2>=3.1.4",
  "pydantic-settings>=2.6.0",
  "python-multipart>=0.0.12",
  "uvicorn[standard]>=0.32.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.0",
  "pytest-asyncio>=0.24.0",
  "ruff>=0.8.0",
  "httpx>=0.27.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 2: Create ignore rules**

Write `.gitignore`:

```gitignore
.env
.env.*
!.env.example
!deploy/command-center.env.example
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
*.pyc
dist/
build/
htmlcov/
.coverage
```

- [ ] **Step 3: Create environment template**

Write `.env.example`:

```dotenv
APP_NAME=MABDC Command Center
APP_ENV=local
APP_BASE_URL=http://127.0.0.1:8088
PRIVATE_ACCESS_NOTE=Use Tailscale or ZeroTier only

DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres

TELEGRAM_BOT_TOKEN=
TELEGRAM_APPROVAL_CHAT_ID=

COMMAND_CENTER_SECRET_DIR=/DATA/docker/command-center/secrets
```

- [ ] **Step 4: Create package marker**

Write `src/command_center/__init__.py`:

```python
"""MABDC private automation command center."""
```

- [ ] **Step 5: Create README**

Write `README.md`:

```markdown
# Central Admin OpenClaw

Private single-user automation command center for MABDC.

## Local setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
uvicorn command_center.main:app --app-dir src --reload --port 8088
```

## Safety model

Destructive actions require Telegram approval. The foundation build only includes read-only commands and approval primitives.

## Deployment target

The approved deployment path is `/DATA/docker/command-center` on the aaPanel VPS.
```

- [ ] **Step 6: Install dependencies locally**

Run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Expected: dependencies install without errors.

- [ ] **Step 7: Commit scaffold**

Run:

```bash
git add pyproject.toml .gitignore .env.example README.md src/command_center/__init__.py
git commit -m "chore: scaffold command center project"
```

Expected: commit succeeds.

## Task 2: Settings

**Files:**

- Create: `src/command_center/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write settings tests**

Write `tests/test_config.py`:

```python
from command_center.config import Settings


def test_settings_reads_required_database_url():
    settings = Settings(
        database_url="postgresql://user:pass@localhost:5432/postgres",
        telegram_bot_token="token",
        telegram_approval_chat_id="12345",
    )

    assert settings.database_url == "postgresql://user:pass@localhost:5432/postgres"
    assert settings.telegram_approval_chat_id == "12345"


def test_settings_defaults_to_local_environment():
    settings = Settings(database_url="postgresql://x:y@localhost/db")

    assert settings.app_name == "MABDC Command Center"
    assert settings.app_env == "local"
    assert settings.app_base_url == "http://127.0.0.1:8088"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
source .venv/bin/activate
pytest tests/test_config.py -v
```

Expected: FAIL because `command_center.config` does not exist.

- [ ] **Step 3: Implement settings**

Write `src/command_center/config.py`:

```python
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MABDC Command Center"
    app_env: str = "local"
    app_base_url: str = "http://127.0.0.1:8088"
    private_access_note: str = "Use Tailscale or ZeroTier only"

    database_url: str
    telegram_bot_token: str | None = None
    telegram_approval_chat_id: str | None = None
    command_center_secret_dir: str = Field(default="/DATA/docker/command-center/secrets")

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_approval_chat_id)


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
source .venv/bin/activate
pytest tests/test_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit settings**

Run:

```bash
git add src/command_center/config.py tests/test_config.py
git commit -m "feat: add typed settings"
```

Expected: commit succeeds.

## Task 3: Domain Models

**Files:**

- Create: `src/command_center/models.py`
- Test: `tests/test_approvals.py`

- [ ] **Step 1: Write model behavior tests**

Write `tests/test_approvals.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
source .venv/bin/activate
pytest tests/test_approvals.py -v
```

Expected: FAIL because `command_center.models` does not exist.

- [ ] **Step 3: Implement models**

Write `src/command_center/models.py`:

```python
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
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
source .venv/bin/activate
pytest tests/test_approvals.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit models**

Run:

```bash
git add src/command_center/models.py tests/test_approvals.py
git commit -m "feat: add command center domain models"
```

Expected: commit succeeds.

## Task 4: Supabase Schema Migration

**Files:**

- Create: `migrations/001_command_center_schema.sql`

- [ ] **Step 1: Write schema migration**

Write `migrations/001_command_center_schema.sql`:

```sql
create schema if not exists command_center;

create table if not exists command_center.jobs (
  id uuid primary key default gen_random_uuid(),
  command_name text not null,
  status text not null,
  requested_by text not null,
  payload jsonb not null default '{}'::jsonb,
  result jsonb,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists command_center.approvals (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references command_center.jobs(id) on delete cascade,
  status text not null,
  action_label text not null,
  requested_by text not null,
  decided_by text,
  expires_at timestamptz not null,
  decided_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists command_center.audit_logs (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  job_id uuid references command_center.jobs(id) on delete set null,
  approval_id uuid references command_center.approvals(id) on delete set null,
  actor text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists command_center.gmail_accounts (
  id uuid primary key default gen_random_uuid(),
  alias text not null unique,
  email text not null,
  secret_ref text not null,
  status text not null default 'connected',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists command_center.pc_nodes (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  zerotier_ip inet not null,
  ssh_port integer not null default 22,
  ssh_user text not null,
  status text not null default 'unknown',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists command_center.doc_events (
  id uuid primary key default gen_random_uuid(),
  event_name text not null,
  file_name text not null,
  nextcloud_user text not null,
  source_path text,
  email_status text,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists command_center.integrations (
  name text primary key,
  status text not null,
  details jsonb not null default '{}'::jsonb,
  checked_at timestamptz not null default now()
);

create index if not exists idx_command_center_jobs_created_at
  on command_center.jobs(created_at desc);

create index if not exists idx_command_center_approvals_job_id
  on command_center.approvals(job_id);

create index if not exists idx_command_center_audit_logs_created_at
  on command_center.audit_logs(created_at desc);
```

- [ ] **Step 2: Validate migration syntax locally**

Run:

```bash
test -s migrations/001_command_center_schema.sql
rg -n "command_center.jobs|command_center.approvals|command_center.audit_logs" migrations/001_command_center_schema.sql
```

Expected: file exists and table names are found.

- [ ] **Step 3: Commit migration**

Run:

```bash
git add migrations/001_command_center_schema.sql
git commit -m "feat: add command center database schema"
```

Expected: commit succeeds.

## Task 5: Database Layer

**Files:**

- Create: `src/command_center/db.py`
- Create: `src/command_center/repositories.py`

- [ ] **Step 1: Implement database pool helper**

Write `src/command_center/db.py`:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg


class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=5)

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        if self.pool is None:
            raise RuntimeError("Database pool is not connected")
        async with self.pool.acquire() as connection:
            yield connection
```

- [ ] **Step 2: Implement repositories**

Write `src/command_center/repositories.py`:

```python
from datetime import datetime
from typing import Any

from command_center.db import Database
from command_center.models import ApprovalStatus, AuditEventType, JobStatus


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
                payload,
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
                result,
                error,
            )

    async def list_recent_jobs(self, limit: int = 25) -> list[dict[str, Any]]:
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                select id::text, command_name, status, requested_by, payload, result, error, created_at
                from command_center.jobs
                order by created_at desc
                limit $1
                """,
                limit,
            )
        return [dict(row) for row in rows]

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
                details,
                job_id,
                approval_id,
            )
```

- [ ] **Step 3: Run lint**

Run:

```bash
source .venv/bin/activate
ruff check src/command_center/db.py src/command_center/repositories.py
```

Expected: PASS.

- [ ] **Step 4: Commit database layer**

Run:

```bash
git add src/command_center/db.py src/command_center/repositories.py
git commit -m "feat: add database repository layer"
```

Expected: commit succeeds.

## Task 6: Command Registry

**Files:**

- Create: `src/command_center/commands.py`
- Test: `tests/test_commands.py`

- [ ] **Step 1: Write command tests**

Write `tests/test_commands.py`:

```python
import pytest

from command_center.commands import CommandRegistry, run_vps_health_check


def test_registry_contains_safe_health_command():
    registry = CommandRegistry.default()

    command = registry.get("vps.health")

    assert command.name == "vps.health"
    assert command.dangerous is False


def test_registry_rejects_unknown_command():
    registry = CommandRegistry.default()

    with pytest.raises(KeyError):
        registry.get("missing.command")


def test_vps_health_check_returns_safe_summary():
    result = run_vps_health_check()

    assert result["ok"] is True
    assert "hostname" in result
    assert "disk_root" in result
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
source .venv/bin/activate
pytest tests/test_commands.py -v
```

Expected: FAIL because `command_center.commands` does not exist.

- [ ] **Step 3: Implement command registry**

Write `src/command_center/commands.py`:

```python
import os
import shutil
import socket
from dataclasses import dataclass
from typing import Any, Callable

from command_center.models import CommandDefinition

CommandHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class RegisteredCommand:
    definition: CommandDefinition
    handler: CommandHandler

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def dangerous(self) -> bool:
        return self.definition.dangerous


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, RegisteredCommand] = {}

    def register(self, definition: CommandDefinition, handler: CommandHandler) -> None:
        self._commands[definition.name] = RegisteredCommand(definition=definition, handler=handler)

    def get(self, name: str) -> RegisteredCommand:
        if name not in self._commands:
            raise KeyError(f"Unknown command: {name}")
        return self._commands[name]

    def list_commands(self) -> list[CommandDefinition]:
        return [registered.definition for registered in self._commands.values()]

    @classmethod
    def default(cls) -> "CommandRegistry":
        registry = cls()
        registry.register(
            CommandDefinition(
                name="vps.health",
                description="Read-only VPS health summary",
                dangerous=False,
            ),
            lambda payload: run_vps_health_check(),
        )
        return registry


def run_vps_health_check() -> dict[str, Any]:
    total, used, free = shutil.disk_usage("/")
    load_avg = os.getloadavg()

    return {
        "ok": True,
        "hostname": socket.gethostname(),
        "disk_root": {
            "total_gb": round(total / 1024 / 1024 / 1024, 2),
            "used_gb": round(used / 1024 / 1024 / 1024, 2),
            "free_gb": round(free / 1024 / 1024 / 1024, 2),
        },
        "load_average": {
            "one_minute": load_avg[0],
            "five_minutes": load_avg[1],
            "fifteen_minutes": load_avg[2],
        },
    }
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
source .venv/bin/activate
pytest tests/test_commands.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit command registry**

Run:

```bash
git add src/command_center/commands.py tests/test_commands.py
git commit -m "feat: add safe command registry"
```

Expected: commit succeeds.

## Task 7: Approval Service and Telegram Client

**Files:**

- Create: `src/command_center/approvals.py`
- Create: `src/command_center/telegram.py`
- Modify: `tests/test_approvals.py`

- [ ] **Step 1: Extend approval tests**

Append to `tests/test_approvals.py`:

```python
from command_center.approvals import build_approval_text


def test_build_approval_text_contains_target_and_expiry():
    text = build_approval_text(
        action_label="Trash 10 Gmail messages",
        target_label="gmail:personal",
        expires_minutes=10,
    )

    assert "Trash 10 Gmail messages" in text
    assert "gmail:personal" in text
    assert "10 minutes" in text
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
source .venv/bin/activate
pytest tests/test_approvals.py -v
```

Expected: FAIL because `build_approval_text` does not exist.

- [ ] **Step 3: Implement approval helpers**

Write `src/command_center/approvals.py`:

```python
from datetime import UTC, datetime, timedelta


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
```

- [ ] **Step 4: Implement Telegram client**

Write `src/command_center/telegram.py`:

```python
from typing import Any

import httpx


class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_approval_request(
        self,
        text: str,
        approval_id: str,
    ) -> dict[str, Any]:
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "Approve", "callback_data": f"approve:{approval_id}"},
                        {"text": "Reject", "callback_data": f"reject:{approval_id}"},
                    ]
                ]
            },
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{self.base_url}/sendMessage", json=payload)
            response.raise_for_status()
            return response.json()
```

- [ ] **Step 5: Run tests and lint**

Run:

```bash
source .venv/bin/activate
pytest tests/test_approvals.py -v
ruff check src/command_center/approvals.py src/command_center/telegram.py
```

Expected: PASS.

- [ ] **Step 6: Commit approvals**

Run:

```bash
git add src/command_center/approvals.py src/command_center/telegram.py tests/test_approvals.py
git commit -m "feat: add telegram approval primitives"
```

Expected: commit succeeds.

## Task 8: FastAPI App and API Routes

**Files:**

- Create: `src/command_center/main.py`
- Create: `src/command_center/routes_api.py`
- Test: `tests/test_routes.py`

- [ ] **Step 1: Write route tests**

Write `tests/test_routes.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
source .venv/bin/activate
pytest tests/test_routes.py -v
```

Expected: FAIL because app routes do not exist.

- [ ] **Step 3: Implement API routes**

Write `src/command_center/routes_api.py`:

```python
from fastapi import APIRouter

from command_center.commands import CommandRegistry

router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@router.get("/commands")
async def list_commands() -> dict[str, list[dict[str, object]]]:
    registry = CommandRegistry.default()
    commands = [
        {
            "name": command.name,
            "description": command.description,
            "dangerous": command.dangerous,
        }
        for command in registry.list_commands()
    ]
    return {"commands": commands}
```

- [ ] **Step 4: Implement app factory**

Write `src/command_center/main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from command_center.config import get_settings
from command_center.routes_api import router as api_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router)
    app.mount("/static", StaticFiles(directory="src/command_center/static"), name="static")
    return app


app = create_app()
```

- [ ] **Step 5: Create static directory**

Run:

```bash
mkdir -p src/command_center/static
touch src/command_center/static/app.css
```

Expected: static path exists so app startup succeeds.

- [ ] **Step 6: Run tests and verify pass**

Run:

```bash
source .venv/bin/activate
pytest tests/test_routes.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit API app**

Run:

```bash
git add src/command_center/main.py src/command_center/routes_api.py src/command_center/static/app.css tests/test_routes.py
git commit -m "feat: add FastAPI health and command routes"
```

Expected: commit succeeds.

## Task 9: Dashboard Routes

**Files:**

- Create: `src/command_center/routes_dashboard.py`
- Create: `src/command_center/templates/base.html`
- Create: `src/command_center/templates/index.html`
- Create: `src/command_center/templates/jobs.html`
- Modify: `src/command_center/main.py`
- Modify: `src/command_center/static/app.css`
- Modify: `tests/test_routes.py`

- [ ] **Step 1: Extend route tests**

Append to `tests/test_routes.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
source .venv/bin/activate
pytest tests/test_routes.py -v
```

Expected: FAIL because dashboard routes do not exist.

- [ ] **Step 3: Implement dashboard routes**

Write `src/command_center/routes_dashboard.py`:

```python
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from command_center.commands import CommandRegistry
from command_center.config import get_settings

router = APIRouter()
templates = Jinja2Templates(directory="src/command_center/templates")


@router.get("/")
async def dashboard_home(request: Request):
    settings = get_settings()
    registry = CommandRegistry.default()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "app_name": settings.app_name,
            "private_access_note": settings.private_access_note,
            "commands": registry.list_commands(),
        },
    )


@router.get("/jobs")
async def jobs_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "jobs.html",
        {
            "app_name": settings.app_name,
            "jobs": [],
        },
    )
```

- [ ] **Step 4: Mount dashboard routes**

Modify `src/command_center/main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from command_center.config import get_settings
from command_center.routes_api import router as api_router
from command_center.routes_dashboard import router as dashboard_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router)
    app.include_router(dashboard_router)
    app.mount("/static", StaticFiles(directory="src/command_center/static"), name="static")
    return app


app = create_app()
```

- [ ] **Step 5: Add templates**

Write `src/command_center/templates/base.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ app_name }}</title>
    <link rel="stylesheet" href="/static/app.css">
  </head>
  <body>
    <header class="topbar">
      <div>
        <h1>{{ app_name }}</h1>
        <p>{{ private_access_note | default("Private access only") }}</p>
      </div>
      <nav>
        <a href="/">Overview</a>
        <a href="/jobs">Jobs</a>
      </nav>
    </header>
    <main>
      {% block content %}{% endblock %}
    </main>
  </body>
</html>
```

Write `src/command_center/templates/index.html`:

```html
{% extends "base.html" %}
{% block content %}
<section class="panel">
  <h2>Command Registry</h2>
  <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Description</th>
        <th>Approval</th>
      </tr>
    </thead>
    <tbody>
      {% for command in commands %}
      <tr>
        <td><code>{{ command.name }}</code></td>
        <td>{{ command.description }}</td>
        <td>{{ "Required" if command.dangerous else "Not required" }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</section>
{% endblock %}
```

Write `src/command_center/templates/jobs.html`:

```html
{% extends "base.html" %}
{% block content %}
<section class="panel">
  <h2>Recent Jobs</h2>
  {% if jobs %}
  <table>
    <thead>
      <tr>
        <th>Command</th>
        <th>Status</th>
        <th>Requested By</th>
      </tr>
    </thead>
    <tbody>
      {% for job in jobs %}
      <tr>
        <td>{{ job.command_name }}</td>
        <td>{{ job.status }}</td>
        <td>{{ job.requested_by }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No jobs recorded yet.</p>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 6: Add dashboard CSS**

Write `src/command_center/static/app.css`:

```css
:root {
  color-scheme: light;
  font-family: Arial, sans-serif;
  background: #f5f7f9;
  color: #17202a;
}

body {
  margin: 0;
}

.topbar {
  align-items: center;
  background: #1f2933;
  color: #ffffff;
  display: flex;
  justify-content: space-between;
  padding: 16px 24px;
}

.topbar h1 {
  font-size: 20px;
  margin: 0 0 4px;
}

.topbar p {
  color: #cbd5df;
  margin: 0;
}

.topbar a {
  color: #ffffff;
  margin-left: 16px;
  text-decoration: none;
}

main {
  padding: 24px;
}

.panel {
  background: #ffffff;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 18px;
}

table {
  border-collapse: collapse;
  width: 100%;
}

th,
td {
  border-bottom: 1px solid #e4e7eb;
  padding: 10px;
  text-align: left;
}
```

- [ ] **Step 7: Run tests and verify pass**

Run:

```bash
source .venv/bin/activate
pytest tests/test_routes.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit dashboard**

Run:

```bash
git add src/command_center/main.py src/command_center/routes_dashboard.py src/command_center/templates src/command_center/static/app.css tests/test_routes.py
git commit -m "feat: add private dashboard shell"
```

Expected: commit succeeds.

## Task 10: Docker Deployment Files

**Files:**

- Create: `deploy/docker-compose.yml`
- Create: `deploy/command-center.env.example`
- Create: `deploy/README.md`

- [ ] **Step 1: Add deployment env example**

Write `deploy/command-center.env.example`:

```dotenv
APP_NAME=MABDC Command Center
APP_ENV=production
APP_BASE_URL=https://command.mabdc.com
PRIVATE_ACCESS_NOTE=Private access over Tailscale or ZeroTier only

DATABASE_URL=postgresql://postgres:CHANGE_ME@supabase-db:5432/postgres

TELEGRAM_BOT_TOKEN=CHANGE_ME
TELEGRAM_APPROVAL_CHAT_ID=CHANGE_ME

COMMAND_CENTER_SECRET_DIR=/run/secrets/command-center
```

- [ ] **Step 2: Add Docker Compose**

Write `deploy/docker-compose.yml`:

```yaml
services:
  command-center-api:
    build:
      context: ..
      dockerfile: deploy/runtime.Dockerfile
    env_file:
      - ./command-center.env
    ports:
      - "127.0.0.1:18088:8088"
    restart: unless-stopped
    command: ["uvicorn", "command_center.main:app", "--host", "0.0.0.0", "--port", "8088"]

  command-center-worker:
    build:
      context: ..
      dockerfile: deploy/runtime.Dockerfile
    env_file:
      - ./command-center.env
    restart: unless-stopped
    command: ["python", "-m", "command_center.worker"]
```

- [ ] **Step 3: Add runtime Dockerfile**

Create `deploy/runtime.Dockerfile`:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --no-cache-dir .

EXPOSE 8088
```

- [ ] **Step 4: Add worker process**

Create `src/command_center/worker.py`:

```python
import time


def main() -> None:
    while True:
        time.sleep(30)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Add deployment README**

Write `deploy/README.md`:

```markdown
# VPS Deployment

Deploy path:

```bash
/DATA/docker/command-center
```

Initial deployment:

```bash
mkdir -p /DATA/docker/command-center
cp -r deploy src pyproject.toml README.md /DATA/docker/command-center/
cd /DATA/docker/command-center/deploy
cp command-center.env.example command-center.env
```

Edit `command-center.env` with real private values, then:

```bash
docker compose up -d --build
curl -fsS http://127.0.0.1:18088/api/health
```

Expected response:

```json
{"ok":true}
```
```

- [ ] **Step 6: Build Docker image locally**

Run:

```bash
docker compose -f deploy/docker-compose.yml build
```

Expected: build succeeds.

- [ ] **Step 7: Commit deployment files**

Run:

```bash
git add deploy src/command_center/worker.py
git commit -m "feat: add docker deployment files"
```

Expected: commit succeeds.

## Task 11: Full Verification and Push

**Files:**

- Modify only files needed to fix test, lint, or build failures.

- [ ] **Step 1: Run full test suite**

Run:

```bash
source .venv/bin/activate
pytest -v
```

Expected: PASS.

- [ ] **Step 2: Run lint**

Run:

```bash
source .venv/bin/activate
ruff check src tests
```

Expected: PASS.

- [ ] **Step 3: Run app locally**

Run:

```bash
source .venv/bin/activate
uvicorn command_center.main:app --app-dir src --host 127.0.0.1 --port 8088
```

Expected: server starts and logs a line showing it is listening on `http://127.0.0.1:8088`.

- [ ] **Step 4: Check health endpoint**

In another terminal:

```bash
curl -fsS http://127.0.0.1:8088/api/health
```

Expected:

```json
{"ok":true}
```

- [ ] **Step 5: Check dashboard**

Open:

```text
http://127.0.0.1:8088/
```

Expected: dashboard shows `MABDC Command Center` and command `vps.health`.

- [ ] **Step 6: Push branch**

Run:

```bash
git status --short
git push
```

Expected: working tree clean and remote `origin/main` updated.

## Self-Review

Spec coverage:

- Foundation app: Task 1, Task 8, Task 9, Task 10.
- Existing Supabase schema: Task 4, Task 5.
- Telegram approval primitives: Task 7.
- Read-only VPS status: Task 6.
- Dashboard and shared command registry: Task 6, Task 8, Task 9.
- Secrets not hardcoded: Task 2 and deploy env templates define secret inputs, implementation keeps secret values outside committed files.
- Destructive actions requiring approval: represented in models and approval primitives; execution is deferred until later plans.

Intentional gaps for later plans:

- Gmail OAuth and cleanup execution.
- PC-node SSH execution.
- Document watcher dispatcher rewiring.
- OpenClaw restart/repair integration.
- Hermes installation.
- Browser automation.

Placeholder scan:

- No unfinished marker text or unspecified implementation steps are present.
- Deferred items are explicitly out of this foundation scope.

Type consistency:

- `JobStatus`, `ApprovalStatus`, and `AuditEventType` are defined before repository usage.
- `CommandRegistry.default()` is used consistently by routes and tests.
- `Settings` fields match `.env.example` and deployment env names.
