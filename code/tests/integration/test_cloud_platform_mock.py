from __future__ import annotations

import importlib.util
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import ModuleType

import pytest

from jiuzhang import CloudClient, GBSParams, JiuzhangError, TokenManager


@pytest.fixture
def cloud_mock_url() -> str:
    module = _load_mock_module()
    state = module.MockState()
    server = ThreadingHTTPServer(("127.0.0.1", 0), module.build_handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/api/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.integration
def test_cloud_platform_mock_end_to_end(cloud_mock_url: str, sample_token_id: str) -> None:
    client = CloudClient(token_manager=TokenManager(sample_token_id))
    client.base_url = cloud_mock_url
    params = GBSParams(
        project_id="EXP-test",
        quantum_computer_id="PH_QC_04",
        mt=64,
        pump_energy_nj=2.0,
    )
    try:
        estimate = client.estimate_gbs(params)
        assert estimate["data"]["classical_cost_time_us"] == 24398

        request_id = "00000000-0000-4000-8000-000000000001"
        first = client.submit_gbs(params, request_id=request_id)
        second = client.submit_gbs(params, request_id=request_id)
        assert first["data"]["task_id"] == second["data"]["task_id"]

        raw_result = client.get_result(first["data"]["task_id"])
        assert raw_result["data"]["status"] == "SUCCESS"

        result = client.run_gbs(params, poll_interval=0.0)
        assert result.status_name == "SUCCESS"
        assert result.quantum_computer_id == "PH_QC_04"
        assert set(result.result_map_points) == {
            "experimental",
            "ground_truth",
            "squashed",
            "thermal",
            "distinguishable",
        }
    finally:
        client.close()


@pytest.mark.integration
def test_business_error_code_is_not_success(cloud_mock_url: str) -> None:
    client = CloudClient(
        token_manager=TokenManager("PQ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4"),
    )
    client.base_url = cloud_mock_url
    client._transport.token = None  # simulate a missing X-Jiuzhang-API-Key header
    try:
        with pytest.raises(JiuzhangError) as exc_info:
            client.estimate_runtime(
                quantum_computer_id="PH_QC_04",
                mt_value=64,
                pump_energy_nj=2.0,
            )
        assert exc_info.value.code == "1001"
    finally:
        client.close()


def _load_mock_module() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[3]
        / "local_test"
        / "mock_cloud_platform"
        / "mock_cloud_platform.py"
    )
    spec = importlib.util.spec_from_file_location("mock_cloud_platform", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load mock_cloud_platform.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["mock_cloud_platform"] = module
    spec.loader.exec_module(module)
    return module
