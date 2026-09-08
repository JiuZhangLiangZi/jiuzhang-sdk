"""JiuZhang local GBS program model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.local.gbs._validation import positive_int

__all__ = ["GBSProgram", "Operation"]


@dataclass(frozen=True)
class Operation:
    """A local GBS program operation.

    Args:
        name: Operation name stored in the local IR.
        params: Operation parameters, such as squeezing strength or shot count.
        modes: Mode indices touched by the operation.
    """

    name: str
    params: dict[str, Any] = field(default_factory=dict)
    modes: tuple[int, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable operation."""
        return {"name": self.name, "params": dict(self.params), "modes": list(self.modes)}


@dataclass(frozen=True)
class GBSProgram:
    """A local GBS program that can be serialized into IR.

    Args:
        modes: Number of optical modes represented by the program.
        operations: Immutable operation sequence.
        name: Program name stored in JSON IR.
    """

    modes: int
    operations: tuple[Operation, ...] = field(default_factory=tuple)
    name: str = "gbs_program"

    def __post_init__(self) -> None:
        """Validate the immutable program after construction."""
        positive_int(self.modes, name="modes")
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidParameterError("name cannot be empty")

    def squeezing(self, values: Any) -> GBSProgram:
        """Add per-mode squeezing operations.

        Args:
            values: Iterable of squeezing strengths. Its length must equal
                ``modes``.

        Returns:
            A new ``GBSProgram`` containing the appended squeezing operations.
        """
        items = list(values)
        if len(items) != self.modes:
            raise InvalidParameterError("squeezing values length must equal modes")
        program = self
        for mode, value in enumerate(items):
            program = program._append(
                Operation("squeezing", {"r": float(value), "phi": 0.0}, (mode,))
            )
        return program

    def edge(self, mode_a: int, mode_b: int, weight: float) -> GBSProgram:
        """Add an undirected weighted graph edge.

        Args:
            mode_a: First mode index.
            mode_b: Second mode index. It must be different from ``mode_a``.
            weight: Edge weight used by the local GBS graph representation.

        Returns:
            A new ``GBSProgram`` containing the appended edge operation.
        """
        self._validate_mode(mode_a)
        self._validate_mode(mode_b)
        if mode_a == mode_b:
            raise InvalidParameterError("edge modes must be different")
        return self._append(
            Operation("edge", {"weight": float(weight)}, (int(mode_a), int(mode_b)))
        )

    def measure_fock(self, *, shots: int = 1000) -> GBSProgram:
        """Add a photon-number-resolving measurement.

        Args:
            shots: Number of measurement samples requested by the program.

        Returns:
            A new ``GBSProgram`` containing the measurement operation.
        """
        return self._append(
            Operation(
                "measure_fock",
                {"shots": positive_int(shots, name="shots")},
                tuple(range(self.modes)),
            )
        )

    def measure_threshold(self, *, shots: int = 1000) -> GBSProgram:
        """Add a threshold measurement.

        Args:
            shots: Number of measurement samples requested by the program.

        Returns:
            A new ``GBSProgram`` containing the measurement operation.
        """
        return self._append(
            Operation(
                "measure_threshold",
                {"shots": positive_int(shots, name="shots")},
                tuple(range(self.modes)),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable local IR dictionary.

        Returns:
            Dictionary containing schema, program name, mode count, and ordered
            operations.
        """
        return {
            "schema": "jiuzhang.local.gbs.v1",
            "name": self.name,
            "modes": self.modes,
            "operations": [operation.to_dict() for operation in self.operations],
        }

    def _append(self, operation: Operation) -> GBSProgram:
        return GBSProgram(
            modes=self.modes,
            operations=(*self.operations, operation),
            name=self.name,
        )

    def _validate_mode(self, mode: int) -> None:
        if isinstance(mode, bool) or not isinstance(mode, int) or not 0 <= mode < self.modes:
            raise InvalidParameterError("mode index is out of range")
