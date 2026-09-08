"""GBS task parameter validation and payload conversion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jiuzhang.exceptions import InvalidParameterError

__all__ = ["GBSParams", "input_mode_count", "output_mode_count", "validate_gbs_params"]


@dataclass(frozen=True)
class GBSParams:
    """Local GBS task configuration for the JiuZhang cloud platform."""

    project_id: str
    mt: int
    pump_energy_nj: float
    quantum_computer_id: str = "PH_QC_04"
    squeezing_param: float | None = None
    shots: int | None = None
    task_name: str = "GBS experiment"

    def validate(self) -> None:
        """Validate local GBS parameters before building a cloud payload."""
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise InvalidParameterError("project_id cannot be empty")
        if not isinstance(self.quantum_computer_id, str) or not self.quantum_computer_id.strip():
            raise InvalidParameterError("quantum_computer_id cannot be empty")
        if isinstance(self.mt, bool) or not isinstance(self.mt, int):
            raise InvalidParameterError("mt must be an integer")
        if not 1 <= self.mt <= 500:
            raise InvalidParameterError("mt must be in range 1..500")
        if isinstance(self.pump_energy_nj, bool) or not isinstance(
            self.pump_energy_nj, int | float
        ):
            raise InvalidParameterError("pump_energy_nj must be positive")
        if self.pump_energy_nj <= 0:
            raise InvalidParameterError("pump_energy_nj must be positive")
        if self.squeezing_param is not None:
            if isinstance(self.squeezing_param, bool) or not isinstance(
                self.squeezing_param, int | float
            ):
                raise InvalidParameterError("squeezing_param must be non-negative")
            if self.squeezing_param < 0:
                raise InvalidParameterError("squeezing_param must be non-negative")
        if self.shots is not None:
            if isinstance(self.shots, bool) or not isinstance(self.shots, int):
                raise InvalidParameterError("shots must be a positive integer")
            if self.shots <= 0:
                raise InvalidParameterError("shots must be a positive integer")
        if not isinstance(self.task_name, str) or not self.task_name.strip():
            raise InvalidParameterError("task_name cannot be empty")
        if len(self.task_name) > 200:
            raise InvalidParameterError("task_name cannot exceed 200 characters")

    def input_mode_count(self) -> int:
        """Return the input mode count derived from mt."""
        return input_mode_count(self.mt)

    def output_mode_count(self) -> int:
        """Return the output mode count derived from mt."""
        return output_mode_count(self.mt)

    def to_cloud_payload(self) -> dict[str, Any]:
        """Build the JiuZhang cloud platform task payload."""
        self.validate()
        payload: dict[str, Any] = {
            "project_id": self.project_id,
            "task_name": self.task_name,
            "quantum_computer_id": self.quantum_computer_id,
            "mt_value": self.mt,
            "pump_energy_nj": float(self.pump_energy_nj),
        }
        if self.squeezing_param is not None:
            payload["squeezing_param"] = float(self.squeezing_param)
        if self.shots is not None:
            payload["shots"] = self.shots
        return payload

    def to_tianyan_payload(self) -> dict[str, Any]:
        """Compatibility alias for older callers; prefer to_cloud_payload()."""
        return self.to_cloud_payload()

    def summary(self) -> dict[str, Any]:
        """Return a compact JSON-serializable parameter summary."""
        self.validate()
        return {
            "project_id": self.project_id,
            "quantum_computer_id": self.quantum_computer_id,
            "mt": self.mt,
            "pump_energy_nj": float(self.pump_energy_nj),
            "squeezing_param": self.squeezing_param,
            "shots": self.shots,
            "task_name": self.task_name,
            "input_mode_count": self.input_mode_count(),
            "output_mode_count": self.output_mode_count(),
        }


def input_mode_count(mt: int) -> int:
    """Compute the GBS input mode count."""
    if isinstance(mt, bool) or not isinstance(mt, int):
        raise InvalidParameterError("mt must be an integer")
    return 3 * mt


def output_mode_count(mt: int) -> int:
    """Compute the GBS output mode count."""
    if isinstance(mt, bool) or not isinstance(mt, int):
        raise InvalidParameterError("mt must be an integer")
    return 9 * (mt + 80)


def validate_gbs_params(params: GBSParams) -> None:
    """Validate a GBSParams instance."""
    params.validate()
