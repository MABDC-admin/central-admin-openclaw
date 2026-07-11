# Command Center Design

Date: 2026-07-11
Owner: Dennis
Status: Approved for implementation planning

## Goal

Build a single-user private automation command center on the existing aaPanel VPS. The command center will provide both a private web dashboard and Telegram bot control for Gmail automation, VPS maintenance, PC-node control over ZeroTier, document watcher events, OpenClaw, Hermes, and future automation services.

The system must be safe by default. Destructive or sensitive actions require Telegram approval before execution.

## Deployment Target

Primary VPS:

- Hostname: `aapanel`
- Tailscale IP: `100.124.32.11`
- ZeroTier IP: `10.121.15.125`
- SSH: `root@100.124.32.11 -p 1988`
- OS: Ubuntu 22.04.5
- CPU: Ryzen 7 3700X, 16 threads
- RAM: 62 GB
- Root disk after cleanup: about 172 GB free
- Data disk: `/DATA`, about 2.3 TB free

Application location:

- `/DATA/docker/command-center`

The app will run as Docker Compose services:

- `command-center-api`
- `command-center-worker`
- `command-center-web`

## Architecture

The command center has two equal interfaces:

```text
Telegram Bot        Private Web Dashboard
     |                   |
     v                   v
       Command Center Backend
              |
      Jobs / approvals / logs
              |
   --------------------------------
   |       |        |       |      |
 Gmail  OpenClaw  Hermes  VPS    PC Nodes
 API    Gateway   Worker  Browser over ZeroTier
```

Telegram and the dashboard must use the same backend commands. There should not be separate business logic for each interface.

## Core Components

### Command Center Backend

Owns:

- command registry
- job creation and execution
- approval workflow
- audit logging
- integration status
- access to Supabase
- access to managed secrets

### Telegram Bot

Used for:

- normal commands
- alerts
- required approval buttons
- job status notifications

Dangerous actions are approved through Telegram.

### Private Web Dashboard

Used for:

- status overview
- logs and job history
- Gmail account management
- PC node registry
- document watcher events
- manual command execution
- integration health checks

The dashboard/API must be protected by private networking or strong access control.

## Data Store

Use the existing Supabase Postgres instance. Do not deploy a new database for v1.

Create a dedicated schema:

```text
command_center
```

Tables:

- `command_center.jobs`
- `command_center.approvals`
- `command_center.audit_logs`
- `command_center.gmail_accounts`
- `command_center.pc_nodes`
- `command_center.doc_events`
- `command_center.integrations`

Supabase stores:

- job status and history
- Telegram approval records
- Gmail account aliases and email addresses
- PC node names, ZeroTier IPs, SSH usernames, and SSH ports
- document watcher events
- audit logs
- integration status

Supabase does not store raw secrets in normal tables.

## Secrets

These values must not be hardcoded in source code or normal database rows:

- Gmail OAuth refresh tokens
- Telegram bot token
- OpenRouter API key
- SSH private keys
- mail API key

Use a VPS-managed secret store or encrypted vault. Supabase stores only a reference such as:

```text
gmail_accounts.secret_ref = "gmail_personal_oauth"
```

The existing document mail dispatcher currently has a hardcoded live mail API key. The implementation should move that key into managed secrets and rotate it if possible.

## Automation Modules

### Gmail Module

Uses the official Gmail API with one OAuth authorization per Gmail account.

V1 commands:

- add Gmail account
- list Gmail accounts
- reconnect Gmail account
- list labels
- dry-run cleanup by Gmail query
- move messages to Trash after Telegram approval
- show cleanup status

Default behavior:

- use `gmail.modify`
- move messages to Trash
- do not permanently delete messages by default

Permanent deletion is out of scope for v1 unless explicitly approved later.

### Document Watcher Module

Existing server assets:

- service: `doc-watcher.service`
- host watcher: `/opt/doc_watcher.sh`
- Nextcloud container: `nextcloud-app`
- dispatcher: `/var/www/html/custom_apps/send_doc_attachment.py`
- mail API: `api-mail.mabdc.com`

Current behavior:

- watches `/DATA/docker/nextcloud/app/data/`
- detects saved document files
- sends attachments automatically through the mail API

Command center behavior:

- ingest or log watcher events
- show document activity in the dashboard
- send Telegram alerts for document sends
- later route sensitive sends through Telegram approval
- move dispatcher secrets out of the script

Recommended folder behavior:

- normal outgoing folder: auto-send
- approval folder: require Telegram approval
- private or finance folders: block unless manually approved

### PC Node Module

PC nodes are legitimate office machines managed by the user as IT.

V1 control method:

- Windows OpenSSH Server
- ZeroTier private IP
- SSH user and port per node

Commands:

- register node
- list nodes
- ping/test SSH
- run approved SSH command
- collect output summary and exit status

No admin-bypass behavior is allowed. Admin actions must use authorized accounts, keys, and approved commands.

Long-term improvement:

- add a small node agent service on each PC to enforce allowed actions locally

### VPS Module

Commands:

- health check
- disk usage
- memory usage
- Docker status
- service status
- approved service restart
- approved maintenance command

### OpenClaw Module

Existing OpenClaw path:

- `/www/wwwroot/claw.mabdc.com`

Current finding:

- Docker Compose config exists
- Nginx config exists
- OpenClaw containers are stopped
- local gateway port `18789` was not listening during inspection

V1 behavior:

- show status
- start/stop/restart after approval if needed
- route selected jobs after OpenClaw is repaired and running

### Hermes Module

Hermes is not currently installed on the VPS.

V1 behavior:

- leave integration point ready
- install/connect in a later phase
- route long-running or repeated tasks to Hermes after setup

### Browser Module

Browser automation runs only on the VPS in v1.

Do not run browser automation on PC nodes in v1.

## Approval Rules

Dangerous actions always require Telegram approval:

- Gmail trash/delete
- send email with attachment
- run PC SSH command
- install or update packages
- restart services
- edit or delete files
- start browser automation with account access

Safe actions can run without approval:

- status checks
- dry runs
- list Gmail labels/accounts
- list PC nodes
- show logs
- show disk/RAM/Docker status

Approval flow:

```text
Command requested
        |
        v
Backend creates preview
        |
        v
Telegram sends Approve / Reject
        |
        v
Approved action runs once
        |
        v
Result saved to Supabase audit log
```

Approvals must:

- show the target account, node, or service
- show the action summary
- expire after a short time
- be single-use
- write an audit record for approve, reject, expire, and execute outcomes

## Networking

Preferred access:

- Tailscale or ZeroTier private access
- no public dashboard unless protected

Suggested private URL:

```text
https://command.mabdc.com
```

Only expose this if protected by one of:

- Tailscale-only access
- ZeroTier-only access
- Authelia or OAuth2 proxy
- strict IP allowlist

PC node SSH uses ZeroTier IPs.

Supabase should be accessed by the command center through local or private networking, not public DB ports.

## Rollout Plan

### Phase 1: Foundation

- create command center app
- connect to existing Supabase
- create `command_center` schema and tables
- add Telegram bot approval flow
- add dashboard private access
- add audit logs

### Phase 2: Read-Only Integrations

- Gmail dry-run only
- Supabase status
- VPS health checks
- Docker/service status
- PC node ping/SSH test only
- document watcher event logging only
- OpenClaw status only

### Phase 3: Approved Actions

- Gmail move-to-Trash after Telegram approval
- PC SSH commands after Telegram approval
- VPS service restart after Telegram approval
- document email send approval for sensitive folders

### Phase 4: Agent Integrations

- repair/restart OpenClaw
- install/connect Hermes
- route selected jobs to agents
- add VPS-only browser automation

## Test Requirements

Required tests and checks:

- Gmail cleanup dry-run does not delete mail
- Gmail Trash requires approval
- rejected approval cancels job
- expired approval cannot run
- PC SSH command logs target and output summary
- document watcher logs save event
- secrets do not appear in logs
- dashboard and Telegram show the same job status
- destructive commands create audit records
- command center can connect to existing Supabase

## Operational Notes

- Keep the root disk above 100 GB free before adding large images.
- Use Docker Compose under `/DATA/docker/command-center`.
- Do not mix command center code into Nextcloud or OpenClaw.
- Keep OpenClaw and Hermes as integrations/workers, not the primary database or approval authority.
- Use root SSH only for bootstrap; daily services should run under container users or a dedicated service user.
- Review public Supabase port exposure later, especially database pooler ports.

## Out of Scope for V1

- multi-user roles
- permanent Gmail deletion
- PC browser automation
- full agent mesh where OpenClaw and Hermes both act as equal controllers
- admin-bypass behavior
- public unauthenticated dashboard access
- storing raw secrets in normal Supabase tables
