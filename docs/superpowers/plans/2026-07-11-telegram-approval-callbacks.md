# Telegram Approval Callbacks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real Telegram approval callback handling with persisted approval decisions and job status updates.

**Architecture:** Extend the existing FastAPI app with a Telegram webhook endpoint that accepts callback queries, parses `approve:<id>` and `reject:<id>`, updates Supabase approval/job records through the repository layer, and answers Telegram callbacks. Keep execution safe: approval decisions are recorded, but no destructive command runs in this slice.

**Tech Stack:** FastAPI, asyncpg, httpx, pytest, existing command center schema.

---

## Scope

Included:

- Approval lookup and decision repository methods.
- Approval service for approve/reject/expire behavior.
- Telegram webhook route for callback queries.
- Tests using fake repository/client objects.
- Dashboard/API visibility for recent jobs remains unchanged except repository support.

Deferred:

- Running destructive actions after approval.
- Telegram webhook registration with Telegram API.
- Gmail/PC-node action execution.

## Tasks

### Task 1: Repository Decision Methods

**Files:**

- Modify: `src/command_center/repositories.py`

Steps:

- [ ] Add `get_approval(approval_id: str) -> dict[str, Any] | None`.
- [ ] Add `decide_approval(approval_id: str, status: ApprovalStatus, decided_by: str) -> None`.
- [ ] Add `get_job(job_id: str) -> dict[str, Any] | None`.
- [ ] Add audit writes from the service layer, not directly inside these methods.

### Task 2: Approval Service

**Files:**

- Modify: `src/command_center/approvals.py`
- Test: `tests/test_approval_service.py`

Steps:

- [ ] Add tests for approve, reject, missing approval, already-decided approval, and expired approval.
- [ ] Add `ApprovalDecisionResult` dataclass.
- [ ] Add `ApprovalService.decide(approval_id, decision, actor)`.
- [ ] Approved decisions set approval to `approved` and job to `pending`.
- [ ] Rejected decisions set approval to `rejected` and job to `canceled`.
- [ ] Expired approvals set approval to `expired` and job to `expired`.
- [ ] Write audit events for approved/rejected/expired outcomes.

### Task 3: Telegram Callback Route

**Files:**

- Modify: `src/command_center/telegram.py`
- Modify: `src/command_center/routes_api.py`
- Modify: `src/command_center/main.py`
- Test: `tests/test_telegram_routes.py`

Steps:

- [ ] Add `TelegramClient.answer_callback_query(callback_query_id, text)`.
- [ ] Add `POST /api/telegram/webhook`.
- [ ] Parse callback data in the form `approve:<approval_id>` or `reject:<approval_id>`.
- [ ] Return `{"ok": true}` for valid Telegram webhook payloads.
- [ ] Reject unknown callback formats with `{"ok": false}` but HTTP 200 so Telegram does not retry forever.
- [ ] Use app state dependencies for repository/service/client so tests can inject fakes.

### Task 4: Verify and Deploy

**Files:**

- Modify only files needed to fix verification failures.

Steps:

- [ ] Run `pytest -v -s`.
- [ ] Run `ruff check src tests`.
- [ ] Build Docker image with `docker compose -f deploy/docker-compose.yml build`.
- [ ] Commit changes.
- [ ] Push branch/main.
- [ ] Copy updated app to `/DATA/docker/command-center/app`.
- [ ] Restart `docker compose up -d --build`.
- [ ] Verify `http://100.124.32.11:18088/api/health`.

## Self-Review

- This plan does not execute Gmail deletion or PC commands.
- Approval callbacks are persisted and auditable.
- Telegram callback route avoids retry storms by returning HTTP 200 for malformed callback data.
