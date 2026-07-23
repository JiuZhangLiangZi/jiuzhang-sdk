"""Cloud API client for the JiuZhang SDK."""

from __future__ import annotations

import time
import uuid
from typing import Any

from jiuzhang.auth import TokenManager
from jiuzhang.cloud.transport import HttpTransport
from jiuzhang.exceptions import InvalidParameterError, TimeoutError
from jiuzhang.settings import Settings


class CloudClient:
    """HTTP client for the JiuZhang cloud platform."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:18081",
        *,
        api_key: str | None = None,
        token_manager: TokenManager | None = None,
        timeout: float = 30.0,
        transport: HttpTransport | None = None,
    ) -> None:
        """Create a CloudClient."""
        if api_key is not None and token_manager is not None:
            raise InvalidParameterError("api_key and token_manager are mutually exclusive")
        self._base_url = base_url
        self.token_manager = token_manager or (
            TokenManager(api_key) if api_key is not None else None
        )
        token = self.token_manager.token_id if self.token_manager is not None else None
        self._transport = transport or HttpTransport(base_url, token=token, timeout=timeout)

    @property
    def base_url(self) -> str:
        """Return the configured cloud API base URL."""
        return self._base_url

    @base_url.setter
    def base_url(self, value: str) -> None:
        """Set the cloud API base URL and update the transport."""
        self._base_url = value
        if hasattr(self, "_transport") and self._transport is not None:
            self._transport.base_url = value.rstrip("/") + "/"

    @classmethod
    def from_settings(cls, settings: Settings) -> CloudClient:
        """Create a client from Settings."""
        return cls(
            base_url=settings.base_url,
            token_manager=TokenManager(settings.api_key),
            timeout=settings.request_timeout,
        )

    @classmethod
    def from_env(cls) -> CloudClient:
        """Create a client from environment variables."""
        return cls.from_settings(Settings.from_env())

    def close(self) -> None:
        """Close the underlying HTTP transport."""
        self._transport.close()

    def estimate_runtime(
        self,
        *,
        quantum_computer_id: str,
        mt_value: int,
        pump_energy_nj: float,
    ) -> dict[str, Any]:
        """Estimate runtime before submitting a task."""
        self._validate_common(mt_value, pump_energy_nj)
        return self._transport.post(
            "/estimate",
            json=self._build_common_payload(
                mt_value=mt_value,
                pump_energy_nj=pump_energy_nj,
                quantum_computer_id=quantum_computer_id,
            ),
        )

    def submit_task(
        self,
        *,
        project_id: str,
        task_name: str,
        quantum_computer_id: str,
        mt_value: int,
        pump_energy_nj: float,
        squeezing_param: float | None = None,
        classical_cost_time: int | float | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Submit a cloud GBS task and return the cloud task id."""
        if not isinstance(project_id, str) or not project_id.strip():
            raise InvalidParameterError("project_id cannot be empty")
        if not isinstance(task_name, str) or not task_name.strip():
            raise InvalidParameterError("task_name cannot be empty")
        if len(task_name) > 200:
            raise InvalidParameterError("task_name cannot exceed 200 characters")
        self._validate_common(mt_value, pump_energy_nj)
        payload: dict[str, Any] = self._build_common_payload(
            mt_value=mt_value,
            pump_energy_nj=pump_energy_nj,
            quantum_computer_id=quantum_computer_id,
        )
        payload.update(
            {
                "project_id": project_id,
                "task_name": task_name,
            }
        )
        if squeezing_param is not None:
            payload["squeezing_param"] = squeezing_param
        if classical_cost_time is not None:
            payload["classical_cost_time"] = int(classical_cost_time)
        headers = {"X-Request-Id": request_id or str(uuid.uuid4())}
        return self._transport.post("/tasks/submit", json=payload, headers=headers)

    def get_result(self, task_id: int | str) -> dict[str, Any]:
        """Query a cloud task result."""
        task_id_text = str(task_id).strip()
        if not task_id_text:
            raise InvalidParameterError("task_id cannot be empty")
        return self._transport.get(f"/tasks/{task_id_text}")

    def run_experiment(
        self,
        *,
        project_id: str,
        task_name: str,
        quantum_computer_id: str,
        mt_value: int,
        pump_energy_nj: float,
        squeezing_param: float | None = None,
        poll_interval: float = 0.5,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Estimate, submit, and poll a cloud task."""
        estimate = self.estimate_runtime(
            quantum_computer_id=quantum_computer_id,
            mt_value=mt_value,
            pump_energy_nj=pump_energy_nj,
        )
        classical_cost_time = self._extract_classical_cost_time_us(estimate)
        task = self.submit_task(
            project_id=project_id,
            task_name=task_name,
            quantum_computer_id=quantum_computer_id,
            mt_value=mt_value,
            pump_energy_nj=pump_energy_nj,
            squeezing_param=squeezing_param,
            classical_cost_time=classical_cost_time,
        )
        task_id = self._extract_task_id(task)
        deadline = time.monotonic() + timeout
        last_result: dict[str, Any] | None = None
        while time.monotonic() <= deadline:
            last_result = self.get_result(task_id)
            status = self._extract_task_status(last_result)
            if status in (2, "2", "SUCCESS", "success", "SUCCEEDED", "succeeded"):
                return {"estimate": estimate, "task": task, "result": last_result}
            if status in (3, "3", "FAILED", "failed"):
                return {"estimate": estimate, "task": task, "result": last_result}
            time.sleep(poll_interval)
        raise TimeoutError(
            "cloud task polling timed out",
            details={"task_id": task_id, "last_result": last_result or {}},
        )

    def estimate_gbs(self, params: Any) -> dict[str, Any]:
        """Estimate runtime using a GBSParams instance."""
        params.validate()
        return self.estimate_runtime(
            quantum_computer_id=params.quantum_computer_id,
            mt_value=params.mt,
            pump_energy_nj=params.pump_energy_nj,
        )

    def submit_gbs(self, params: Any, *, request_id: str | None = None) -> dict[str, Any]:
        """Submit a GBS task using a GBSParams instance."""
        params.validate()
        return self.submit_task(
            project_id=params.project_id,
            task_name=params.task_name,
            quantum_computer_id=params.quantum_computer_id,
            mt_value=params.mt,
            pump_energy_nj=params.pump_energy_nj,
            squeezing_param=params.squeezing_param,
            request_id=request_id,
        )

    def run_gbs(
        self,
        params: Any,
        *,
        poll_interval: float = 0.5,
        timeout: float = 30.0,
    ) -> Any:
        """Run a GBS task and return a parsed GBSResult."""
        from jiuzhang.gbs.result import parse_gbs_result

        params.validate()
        raw = self.run_experiment(
            project_id=params.project_id,
            task_name=params.task_name,
            quantum_computer_id=params.quantum_computer_id,
            mt_value=params.mt,
            pump_energy_nj=params.pump_energy_nj,
            squeezing_param=params.squeezing_param,
            poll_interval=poll_interval,
            timeout=timeout,
        )
        return parse_gbs_result(raw["result"])

    @staticmethod
    def _validate_common(mt_value: int, pump_energy_nj: float) -> None:
        if isinstance(mt_value, bool) or not isinstance(mt_value, int):
            raise InvalidParameterError("mt_value must be an integer")
        if not 1 <= mt_value <= 500:
            raise InvalidParameterError("mt_value must be in range 1..500")
        if isinstance(pump_energy_nj, bool) or not isinstance(pump_energy_nj, int | float):
            raise InvalidParameterError("pump_energy_nj must be positive")
        if pump_energy_nj <= 0:
            raise InvalidParameterError("pump_energy_nj must be positive")

    @staticmethod
    def _build_common_payload(
        *,
        mt_value: int,
        pump_energy_nj: float,
        quantum_computer_id: str,
    ) -> dict[str, Any]:
        if not isinstance(quantum_computer_id, str) or not quantum_computer_id.strip():
            raise InvalidParameterError("quantum_computer_id cannot be empty")
        return {
            "quantum_computer_id": quantum_computer_id,
            "mt_value": mt_value,
            "pump_energy_nj": pump_energy_nj,
        }

    @staticmethod
    def _extract_task_id(task: dict[str, Any]) -> int | str:
        data = task.get("data")
        if isinstance(data, dict) and "task_id" in data:
            value = data["task_id"]
            if isinstance(value, int | str):
                return value
        if isinstance(data, dict) and "taskId" in data:
            value = data["taskId"]
            if isinstance(value, int | str):
                return value
        if "task_id" in task:
            value = task["task_id"]
            if isinstance(value, int | str):
                return value
        if "taskId" in task:
            value = task["taskId"]
            if isinstance(value, int | str):
                return value
        raise InvalidParameterError("task response is missing task_id", details={"task": task})

    @staticmethod
    def _extract_task_status(result: dict[str, Any]) -> int | str | None:
        data = result.get("data")
        if isinstance(data, dict):
            value = data.get("status")
            if isinstance(value, int | str):
                return value
            tianyan_response = data.get("tianyan_response")
            if isinstance(tianyan_response, dict):
                value = tianyan_response.get("taskStatus")
                if isinstance(value, int | str):
                    return value
            value = data.get("taskStatus")
            if isinstance(value, int | str):
                return value
        value = result.get("taskStatus")
        if isinstance(value, int | str):
            return value
        return None

    @staticmethod
    def _extract_classical_cost_time_us(estimate: dict[str, Any]) -> int | None:
        data = estimate.get("data")
        if isinstance(data, dict):
            value = data.get("classical_cost_time_us")
            if isinstance(value, int | float):
                return int(value)
            seconds = data.get("classical_cost_time_s")
            if isinstance(seconds, int | float):
                return int(seconds * 1_000_000)
        value = estimate.get("classicalCostTime")
        if isinstance(value, int | float):
            return int(value * 1_000_000)
        return None
