"""Validation helpers for local GBS wrappers."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from jiuzhang.exceptions import InvalidParameterError


def optional_dependency(module_name: str) -> Any:
    """Import an optional local backend dependency with a user-facing error."""
    try:
        return __import__(module_name, fromlist=["*"])
    except ImportError as exc:
        raise InvalidParameterError(
            "本地 GBS 功能依赖缺失，请重新安装最新版：pip install --upgrade jiuzhang-sdk"
        ) from exc


def square_matrix(value: Any, *, name: str = "matrix") -> npt.NDArray[Any]:
    """Convert input to a non-empty square numpy matrix."""
    arr = np.asarray(value)
    if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[0] != arr.shape[1]:
        raise InvalidParameterError(f"{name} must be a non-empty square matrix")
    if arr.dtype == np.bool_ or not np.issubdtype(arr.dtype, np.number):
        raise InvalidParameterError(f"{name} must contain numeric values")
    return arr


def positive_int(value: Any, *, name: str) -> int:
    """Validate a positive integer."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InvalidParameterError(f"{name} must be a positive integer")
    return value


def non_negative_float(value: Any, *, name: str) -> float:
    """Validate a non-negative numeric value."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidParameterError(f"{name} must be non-negative")
    result = float(value)
    if result < 0:
        raise InvalidParameterError(f"{name} must be non-negative")
    return result
