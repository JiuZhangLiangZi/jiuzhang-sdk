"""Local dataset helpers for GBS examples and tests."""

from __future__ import annotations

from typing import Any

import numpy as np

from jiuzhang.local.gbs._validation import positive_int

__all__ = ["random_adjacency_matrix"]


def random_adjacency_matrix(
    modes: int,
    *,
    scale: float = 0.2,
    seed: int | None = None,
) -> Any:
    """Generate a symmetric zero-diagonal adjacency matrix.

    Args:
        modes: Number of graph modes. The returned matrix shape is
            ``(modes, modes)``.
        scale: Upper bound used to scale random edge weights before
            symmetrization.
        seed: Optional random seed for reproducible examples and tests.

    Returns:
        A NumPy adjacency matrix with zero diagonal and symmetric edge weights.
    """
    mode_count = positive_int(modes, name="modes")
    rng = np.random.default_rng(seed)
    raw = rng.random((mode_count, mode_count)) * float(scale)
    matrix = np.triu(raw, k=1)
    matrix = matrix + matrix.T
    np.fill_diagonal(matrix, 0.0)
    return matrix
