from __future__ import annotations

import importlib

from conftest import PROJECT_ROOT


def test_dashboard_imports_with_processed_data(monkeypatch) -> None:
    monkeypatch.setenv("DAVI_PROCESSED_DATA_DIR", "data/processed")
    app = importlib.import_module("app")

    assert app.DATA_DIR == PROJECT_ROOT / "data" / "processed"
    assert app.server is app.dash_app.server
    assert not app.df_student_profile.empty
    assert not app.df_student_result.empty
    assert not app.df_student_survey.empty


def test_health_endpoint_returns_ok(monkeypatch) -> None:
    monkeypatch.setenv("DAVI_PROCESSED_DATA_DIR", "data/processed")
    app = importlib.import_module("app")

    response = app.server.test_client().get("/healthz")

    assert response.status_code == 200
    assert response.data == b"ok"
