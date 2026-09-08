from __future__ import annotations

from typing import Any

import pytest

from jiuzhang import CloudClient, InvalidParameterError, TokenManager


class FakeTransport:
    def __init__(self) -> None:
        self.posts: list[tuple[str, dict[str, Any]]] = []
        self.gets: list[str] = []

    def post(
        self,
        path: str,
        json: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        self.posts.append((path, json))
        if path == "/estimate":
            return {"code": 0, "message": "success", "data": {"classical_cost_time_us": 12500}}
        return {"code": 0, "message": "success", "data": {"task_id": "jz_tsk_70001"}}

    def get(self, path: str) -> dict[str, Any]:
        self.gets.append(path)
        return {
            "code": 0,
            "message": "success",
            "data": {
                "task_id": "jz_tsk_70001",
                "status": "SUCCESS",
                "tianyan_response": {"taskId": "70001", "taskStatus": 2},
            },
        }

    def close(self) -> None:
        pass


def test_cloud_client_calls_cloud_paths(sample_token_id: str) -> None:
    transport = FakeTransport()
    client = CloudClient(
        token_manager=TokenManager(sample_token_id),
        transport=transport,  # type: ignore[arg-type]
    )

    estimate = client.estimate_runtime(
        quantum_computer_id="PH_QC_04",
        mt_value=243,
        pump_energy_nj=6.5,
    )
    task = client.submit_task(
        project_id="EXP-test",
        task_name="光量子优越性实验",
        quantum_computer_id="PH_QC_04",
        mt_value=243,
        pump_energy_nj=6.5,
        squeezing_param=1.8,
        classical_cost_time=estimate["data"]["classical_cost_time_us"],
    )
    result = client.get_result(task["data"]["task_id"])

    assert transport.posts[0][0] == "/estimate"
    assert transport.posts[0][1]["quantum_computer_id"] == "PH_QC_04"
    assert "device_id" not in transport.posts[0][1]
    assert transport.posts[1][0] == "/tasks/submit"
    assert transport.posts[1][1]["project_id"] == "EXP-test"
    assert transport.posts[1][1]["task_name"] == "光量子优越性实验"
    assert transport.gets == ["/tasks/jz_tsk_70001"]
    assert result["data"]["status"] == "SUCCESS"


def test_run_experiment_returns_combined_payload(sample_token_id: str) -> None:
    transport = FakeTransport()
    client = CloudClient(
        token_manager=TokenManager(sample_token_id),
        transport=transport,  # type: ignore[arg-type]
    )

    payload = client.run_experiment(
        project_id="EXP-test",
        task_name="demo",
        quantum_computer_id="PH_QC_04",
        mt_value=81,
        pump_energy_nj=6.0,
        poll_interval=0.0,
    )

    assert payload["task"]["data"]["task_id"] == "jz_tsk_70001"
    assert payload["result"]["data"]["status"] == "SUCCESS"


def test_cloud_client_validates_parameters() -> None:
    client = CloudClient(transport=FakeTransport())  # type: ignore[arg-type]

    with pytest.raises(InvalidParameterError):
        client.estimate_runtime(
            quantum_computer_id="PH_QC_04",
            mt_value=0,
            pump_energy_nj=6.5,
        )


def test_gbs_helpers_return_parsed_result(sample_token_id: str) -> None:
    from jiuzhang import GBSParams

    transport = FakeTransport()
    client = CloudClient(
        token_manager=TokenManager(sample_token_id),
        transport=transport,  # type: ignore[arg-type]
    )

    result = client.run_gbs(
        GBSParams(
            project_id="EXP-test",
            quantum_computer_id="PH_QC_04",
            mt=81,
            pump_energy_nj=6.0,
        ),
        poll_interval=0.0,
    )

    assert result.task_id == "jz_tsk_70001"
    assert result.status_name == "SUCCESS"
