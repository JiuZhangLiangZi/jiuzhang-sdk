"""Lightweight local analysis utilities for returned GBS data."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

import numpy as np

from jiuzhang.exceptions import InvalidParameterError

__all__ = [
    "click_count",
    "click_count_histogram",
    "collision_rate",
    "hellinger_distance",
    "js_divergence",
    "mode_occupancy",
    "normalize_distribution",
    "photon_count",
    "photon_count_histogram",
    "top_k_patterns",
    "total_variation_distance",
]


def photon_count(samples: Any) -> Any:
    """Return the total photon count of each sample."""
    return _samples_array(samples).sum(axis=1)


def photon_count_histogram(samples: Any) -> dict[int, int]:
    """Return a histogram of total photon counts."""
    counts = Counter(int(value) for value in photon_count(samples).tolist())
    return dict(sorted(counts.items()))


def click_count(samples: Any) -> Any:
    """Return the number of occupied modes in each sample."""
    return (_samples_array(samples) > 0).sum(axis=1)


def click_count_histogram(samples: Any) -> dict[int, int]:
    """Return a histogram of occupied-mode counts."""
    counts = Counter(int(value) for value in click_count(samples).tolist())
    return dict(sorted(counts.items()))


def mode_occupancy(samples: Any, *, normalize: bool = True) -> Any:
    """Return per-mode occupancy, optionally normalized by total photon count."""
    occupancy = _samples_array(samples).sum(axis=0).astype(np.float64)
    if not normalize:
        return occupancy
    total = float(occupancy.sum())
    if total == 0.0:
        return np.zeros_like(occupancy)
    return occupancy / total


def collision_rate(samples: Any) -> float:
    """Return the fraction of samples containing a multi-photon mode."""
    return float(np.mean(np.any(_samples_array(samples) > 1, axis=1)))


def top_k_patterns(samples: Any, k: int = 20) -> list[tuple[tuple[int, ...], int]]:
    """Return the k most common sample patterns."""
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise InvalidParameterError("k 必须为正整数")
    patterns = [tuple(int(value) for value in row) for row in _samples_array(samples).tolist()]
    return Counter(patterns).most_common(k)


def normalize_distribution(dist: Any) -> dict[Any, float]:
    """Normalize a dict or list distribution into a probability dictionary."""
    if isinstance(dist, dict):
        items = list(dist.items())
    elif isinstance(dist, list | tuple):
        items = list(enumerate(dist))
    else:
        raise InvalidParameterError("分布必须为 dict 或 list")
    if not items:
        raise InvalidParameterError("分布不能为空")

    values: dict[Any, float] = {}
    total = 0.0
    for key, value in items:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise InvalidParameterError("分布概率必须为非负数字")
        probability = float(value)
        if probability < 0:
            raise InvalidParameterError("分布概率不能为负数")
        values[key] = probability
        total += probability
    if total <= 0:
        raise InvalidParameterError("分布概率总和必须大于 0")
    return {key: value / total for key, value in values.items()}


def total_variation_distance(p: Any, q: Any) -> float:
    """Compute total variation distance between two distributions."""
    left, right = _aligned_distributions(p, q)
    return 0.5 * sum(abs(left[key] - right[key]) for key in left)


def hellinger_distance(p: Any, q: Any) -> float:
    """Compute Hellinger distance between two distributions."""
    left, right = _aligned_distributions(p, q)
    return math.sqrt(0.5 * sum((math.sqrt(left[key]) - math.sqrt(right[key])) ** 2 for key in left))


def js_divergence(p: Any, q: Any, eps: float = 1e-12) -> float:
    """Compute Jensen-Shannon divergence between two distributions."""
    if eps <= 0:
        raise InvalidParameterError("eps 必须大于 0")
    left, right = _aligned_distributions(p, q)
    total = 0.0
    for key in left:
        p_value = max(left[key], eps)
        q_value = max(right[key], eps)
        midpoint = 0.5 * (p_value + q_value)
        total += 0.5 * p_value * math.log(p_value / midpoint)
        total += 0.5 * q_value * math.log(q_value / midpoint)
    return total


def _samples_array(samples: Any) -> Any:
    raw = np.asarray(samples)
    if raw.ndim != 2 or raw.size == 0 or raw.shape[0] == 0 or raw.shape[1] == 0:
        raise InvalidParameterError("samples 必须是非空二维数组")
    if raw.dtype == np.bool_ or not np.issubdtype(raw.dtype, np.integer):
        raise InvalidParameterError("samples 元素必须为非负整数")
    arr = raw.astype(np.int64, copy=False)
    if np.any(arr < 0):
        raise InvalidParameterError("samples 元素必须为非负整数")
    return arr


def _aligned_distributions(p: Any, q: Any) -> tuple[dict[Any, float], dict[Any, float]]:
    left = normalize_distribution(p)
    right = normalize_distribution(q)
    keys = set(left) | set(right)
    return (
        {key: left.get(key, 0.0) for key in keys},
        {key: right.get(key, 0.0) for key in keys},
    )
