"""Local GBS mathematical wrappers."""

from __future__ import annotations

from typing import Any

import numpy as np

from jiuzhang.local.gbs._backends.math_backend import backend
from jiuzhang.local.gbs._validation import square_matrix

__all__ = ["hafnian", "loop_hafnian", "threshold_probability", "torontonian"]


def _native_number(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    return value


def hafnian(
    matrix: Any,
    *,
    loop: bool = False,
    approx: bool = False,
    num_samples: int = 1000,
    method: str = "glynn",
) -> Any:
    """Compute the Hafnian of a square matrix.

    Args:
        matrix: Square matrix whose Hafnian is evaluated.
        loop: Whether to include loop contributions.
        approx: Whether to use the backend's approximate algorithm.
        num_samples: Number of samples used by the approximate algorithm.
        method: Backend algorithm name, such as ``"glynn"``.

    Returns:
        The Hafnian value returned by the local numerical backend.
    """
    arr = square_matrix(matrix)
    return _native_number(
        backend().hafnian(
            arr,
            loop=loop,
            approx=approx,
            num_samples=num_samples,
            method=method,
        )
    )


def loop_hafnian(
    matrix: Any,
    *,
    diagonal: Any | None = None,
    reps: Any | None = None,
    glynn: bool = True,
) -> Any:
    """Compute the loop Hafnian of a square matrix.

    Args:
        matrix: Square matrix whose loop Hafnian is evaluated.
        diagonal: Optional diagonal loop vector. When omitted, the backend uses
            the matrix diagonal.
        reps: Optional occupation-number repetitions for repeated modes.
        glynn: Whether to use the Glynn-form backend implementation.

    Returns:
        The loop Hafnian value returned by the local numerical backend.
    """
    arr = square_matrix(matrix)
    diag = None if diagonal is None else np.asarray(diagonal)
    return _native_number(backend().loop_hafnian(arr, D=diag, reps=reps, glynn=glynn))


def torontonian(matrix: Any, *, recursive: bool = True) -> Any:
    """Compute the Torontonian of a square matrix.

    Args:
        matrix: Square matrix whose Torontonian is evaluated.
        recursive: Whether to use the backend recursive implementation.

    Returns:
        The Torontonian value returned by the local numerical backend.
    """
    arr = square_matrix(matrix)
    return _native_number(backend().tor(arr, recursive=recursive))


def threshold_probability(
    mean: Any,
    covariance: Any,
    pattern: Any,
    *,
    hbar: float = 2.0,
    atol: float = 1e-10,
    rtol: float = 1e-10,
) -> Any:
    """Compute a threshold detection probability for a Gaussian state.

    Args:
        mean: Phase-space mean vector of the Gaussian state.
        covariance: Covariance matrix of the Gaussian state.
        pattern: Threshold detection pattern to evaluate.
        hbar: Backend convention for the commutation relation.
        atol: Absolute tolerance passed to the backend.
        rtol: Relative tolerance passed to the backend.

    Returns:
        Detection probability for the requested threshold pattern.
    """
    cov = square_matrix(covariance, name="covariance")
    mu = np.asarray(mean)
    det_pattern = np.asarray(pattern)
    return _native_number(
        backend().threshold_detection_prob(
            mu,
            cov,
            det_pattern,
            hbar=hbar,
            atol=atol,
            rtol=rtol,
        )
    )
