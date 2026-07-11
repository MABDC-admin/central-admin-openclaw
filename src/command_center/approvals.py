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
