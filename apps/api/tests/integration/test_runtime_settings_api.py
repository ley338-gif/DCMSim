from app.core.config import settings
from app.main import app
from fastapi.testclient import TestClient


def test_runtime_settings_show_effective_values_without_sensitive_configuration(monkeypatch):
    monkeypatch.setattr(settings, "connect_timeout", 7.5)
    monkeypatch.setattr(settings, "association_timeout", 12)
    monkeypatch.setattr(settings, "dimse_timeout", 30)
    monkeypatch.setattr(settings, "log_level", "warning")
    monkeypatch.setattr(settings, "database_url", "sqlite:////private/patients.db")

    with TestClient(app) as client:
        response = client.get("/api/settings/runtime")

    assert response.status_code == 200
    assert response.json() == {
        "connect_timeout": 7.5,
        "association_timeout": 12,
        "dimse_timeout": 30,
        "log_level": "WARNING",
    }
    assert "patients.db" not in response.text


def test_runtime_settings_reports_log_level_fallback(monkeypatch):
    monkeypatch.setattr(settings, "log_level", "not-a-level")
    with TestClient(app) as client:
        response = client.get("/api/settings/runtime")
    assert response.json()["log_level"] == "INFO"
