from __future__ import annotations

import builtins

import pytest

from jiuzhang import CloudClient, GBSParams, Settings
from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.gbs.mock import generate_mock_result
from jiuzhang.gbs.result import parse_gbs_result
from jiuzhang.jupyter import display_gbs_result, get_notebook_client, show_environment


@pytest.mark.integration
def test_settings_and_client_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JIUZHANG_API_KEY", "PQ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4")
    monkeypatch.setenv("JIUZHANG_BASE_URL", "http://127.0.0.1:18081")
    monkeypatch.setenv("JIUZHANG_PROJECT_ID", "EXP-test")
    monkeypatch.setenv("JIUZHANG_QUANTUM_COMPUTER_ID", "PH_QC_04")

    settings = Settings.from_env()
    assert settings.base_url == "http://127.0.0.1:18081"
    assert settings.default_project_id == "EXP-test"
    assert settings.default_quantum_computer_id == "PH_QC_04"

    client = CloudClient.from_env()
    notebook_client = get_notebook_client()
    try:
        assert client.base_url == settings.base_url
        assert notebook_client.base_url == settings.base_url
    finally:
        client.close()
        notebook_client.close()

    env = show_environment()
    assert env["api_key"] == "PQ-3f2c***a9c4"
    assert "3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4" not in str(env)


@pytest.mark.integration
def test_settings_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JIUZHANG_API_KEY", raising=False)
    monkeypatch.setenv("JIUZHANG_BASE_URL", "http://127.0.0.1:18081")

    with pytest.raises(InvalidParameterError):
        Settings.from_env()


@pytest.mark.integration
def test_display_result_falls_back_without_ipython(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name.startswith("IPython"):
            raise ImportError("blocked")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    result = parse_gbs_result(generate_mock_result())

    summary = display_gbs_result(result)

    assert summary["task_id"] == "mock-task-1"
    assert summary["status"] == "SUCCESS"


def test_gbs_params_import_for_notebook() -> None:
    params = GBSParams(project_id="EXP-test", mt=64, pump_energy_nj=2.0)
    assert params.mt == 64


@pytest.mark.integration
def test_cloud_client_default_base_url() -> None:
    client = CloudClient(token_manager=None)
    try:
        assert client.base_url == "http://127.0.0.1:18081"
    finally:
        client.close()
