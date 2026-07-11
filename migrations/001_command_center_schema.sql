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
