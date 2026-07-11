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
