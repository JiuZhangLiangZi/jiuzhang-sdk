"""GBS cloud result parsing helpers."""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Any

__all__ = ["GBSResult", "parse_gbs_result"]


@dataclass(frozen=True)
class GBSResult:
    """Parsed representation of a JiuZhang cloud GBS task result."""

    task_id: str | None
    status: int | str | None
    task_name: str | None = None
    project_id: str | None = None
    quantum_computer_id: str | None = None
    mt: int | None = None
    pump_energy_nj: float | str | None = None
    squeezing_param: float | str | None = None
    sample_count: int | None = None
    result_map_points: dict[str, Any] = field(default_factory=dict)
    download_url: str | None = None
    fail_reason: str | None = None
    created_at: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def status_name(self) -> str:
        """Return a normalized status name."""
        mapping = {
            0: "PENDING",
            "0": "PENDING",
            1: "RUNNING",
            "1": "RUNNING",
            2: "SUCCESS",
            "2": "SUCCESS",
            3: "FAILED",
            "3": "FAILED",
            "SUCCESS": "SUCCESS",
            "SUCCEEDED": "SUCCESS",
            "FAILED": "FAILED",
            "RUNNING": "RUNNING",
            "INIT": "INIT",
            "SUBMITTED": "SUBMITTED",
            "PENDING": "PENDING",
        }
        key = self.status.upper() if isinstance(self.status, str) else self.status
        return mapping.get(key, "UNKNOWN")

    def is_success(self) -> bool:
        """Whether the task reached a successful terminal state."""
        return self.status_name == "SUCCESS"

    def is_failed(self) -> bool:
        """Whether the task reached a failed terminal state."""
        return self.status_name == "FAILED"

    @property
    def experimental_distribution(self) -> Any:
        """Experimental distribution points."""
        return self.result_map_points.get("experimental")

    @property
    def ground_truth_distribution(self) -> Any:
        """Ground-truth distribution points."""
        return self.result_map_points.get("ground_truth")

    @property
    def squashed_distribution(self) -> Any:
        """Squashed-model distribution points."""
        return self.result_map_points.get("squashed")

    @property
    def thermal_distribution(self) -> Any:
        """Thermal-model distribution points."""
        return self.result_map_points.get("thermal")

    @property
    def distinguishable_distribution(self) -> Any:
        """Distinguishable-particle distribution points."""
        return self.result_map_points.get("distinguishable")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "status_name": self.status_name,
            "task_name": self.task_name,
            "project_id": self.project_id,
            "quantum_computer_id": self.quantum_computer_id,
            "mt": self.mt,
            "pump_energy_nj": self.pump_energy_nj,
            "squeezing_param": self.squeezing_param,
            "sample_count": self.sample_count,
            "result_map_points": dict(self.result_map_points),
            "download_url": self.download_url,
            "fail_reason": self.fail_reason,
            "created_at": self.created_at,
            "raw": dict(self.raw),
        }

    def _repr_html_(self) -> str:
        """Render a compact notebook-friendly HTML summary."""
        rows = {
            "task_id": self.task_id,
            "status": self.status_name,
            "task_name": self.task_name,
            "project_id": self.project_id,
            "quantum_computer_id": self.quantum_computer_id,
            "mt": self.mt,
            "sample_count": self.sample_count,
            "download_url": self.download_url,
            "result_map_points": ", ".join(sorted(self.result_map_points.keys())),
        }
        body = "".join(
            "<tr>"
            f"<th>{html.escape(str(key))}</th>"
            f"<td>{html.escape('' if value is None else str(value))}</td>"
            "</tr>"
            for key, value in rows.items()
        )
        return f"<table><caption>GBS Task Result</caption><tbody>{body}</tbody></table>"


def parse_gbs_result(raw: dict[str, Any]) -> GBSResult:
    """Parse direct, Tianyan-style, or JiuZhang cloud wrapped result payloads."""
    data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
    if not isinstance(data, dict):
        data = {}
    tianyan = data.get("tianyan_response")
    tianyan_data = tianyan if isinstance(tianyan, dict) else data

    result_map_points = tianyan_data.get("resultMapPoints")
    if not isinstance(result_map_points, dict):
        result_map_points = {}

    return GBSResult(
        task_id=_as_text(data.get("task_id") or tianyan_data.get("taskId")),
        status=data.get("status") or tianyan_data.get("taskStatus"),
        task_name=_as_text(data.get("task_name") or tianyan_data.get("taskName")),
        project_id=_as_text(data.get("project_id")),
        quantum_computer_id=_as_text(
            data.get("quantum_computer_id") or tianyan_data.get("quantum_computer_id")
        ),
        mt=_as_int(data.get("mt_value") or tianyan_data.get("mtValue")),
        pump_energy_nj=data.get("pump_energy_nj") or tianyan_data.get("pumpEnergyNj"),
        squeezing_param=data.get("squeezing_param") or tianyan_data.get("squeezingParam"),
        sample_count=_as_int(data.get("sample_count") or tianyan_data.get("sampleCount")),
        result_map_points=result_map_points,
        download_url=_as_text(data.get("download_url") or tianyan_data.get("resultDownloadUrl")),
        fail_reason=_as_text(data.get("fail_reason") or tianyan_data.get("failReason")),
        created_at=_as_text(data.get("created_at")),
        raw=raw,
    )


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None
