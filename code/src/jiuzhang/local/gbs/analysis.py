"""Local analysis helpers for GBS samples."""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np

from jiuzhang.exceptions import InvalidParameterError

__all__ = ["samples_to_distribution"]


def samples_to_distribution(samples: Any) -> dict[tuple[int, ...], float]:
    """Convert local samples into a normalized pattern distribution.

    Args:
        samples: Two-dimensional sample array. Rows are shots and columns are
            modes. Values must be non-negative integers.

    Returns:
        Mapping from sample pattern to observed probability.
    """
    arr = np.asarray(samples)
    if arr.ndim != 2 or arr.size == 0:
        raise InvalidParameterError("samples must be a non-empty 2D array")
    if arr.dtype == np.bool_ or not np.issubdtype(arr.dtype, np.integer):
        raise InvalidParameterError("samples must contain non-negative integers")
    if np.any(arr < 0):
        raise InvalidParameterError("samples must contain non-negative integers")
    counter = Counter(tuple(int(value) for value in row) for row in arr.tolist())
    total = float(sum(counter.values()))
    return {pattern: count / total for pattern, count in counter.items()}
