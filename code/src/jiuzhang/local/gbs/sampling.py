"""Local GBS sampling wrappers."""

from __future__ import annotations

from typing import Any, Literal

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.local.gbs._backends.math_backend import samples_backend
from jiuzhang.local.gbs._validation import non_negative_float, positive_int, square_matrix

__all__ = ["sample_gbs"]


def sample_gbs(
    adjacency: Any,
    *,
    shots: int = 10,
    mean_photon_count: float = 1.0,
    detector: Literal["pnr", "threshold"] = "pnr",
    cutoff: int = 5,
    max_photons: int = 30,
    seed: int | None = None,
    parallel: bool = False,
) -> list[list[int]]:
    """Generate local GBS samples from an adjacency matrix.

    Args:
        adjacency: Symmetric graph adjacency matrix. Its shape determines the
            number of optical modes in the local sampling problem.
        shots: Number of samples to generate.
        mean_photon_count: Target mean photon number used when converting the
            graph into a Gaussian state.
        detector: Measurement model. ``"pnr"`` returns photon-number-resolving
            samples; ``"threshold"`` returns click/no-click threshold samples.
        cutoff: Photon-number cutoff per mode for ``"pnr"`` sampling.
        max_photons: Upper bound for the total photon count accepted by the
            sampler.
        seed: Optional random seed for reproducible local examples.
        parallel: Whether to enable the backend sampler's parallel execution.

    Returns:
        A list of samples. Each sample is a list of non-negative integers with
        length equal to the number of modes.
    """
    matrix = square_matrix(adjacency, name="adjacency")
    shot_count = positive_int(shots, name="shots")
    cutoff_value = positive_int(cutoff, name="cutoff")
    max_photon_count = positive_int(max_photons, name="max_photons")
    n_mean = non_negative_float(mean_photon_count, name="mean_photon_count")
    if detector not in {"pnr", "threshold"}:
        raise InvalidParameterError("detector must be 'pnr' or 'threshold'")

    samples = samples_backend()
    if seed is not None:
        samples.seed(seed)

    if detector == "threshold":
        raw = samples.torontonian_sample_graph(
            matrix,
            n_mean=n_mean,
            samples=shot_count,
            cutoff=1,
            max_photons=max_photon_count,
            parallel=parallel,
        )
    else:
        raw = samples.hafnian_sample_graph(
            matrix,
            n_mean=n_mean,
            samples=shot_count,
            cutoff=cutoff_value,
            max_photons=max_photon_count,
            parallel=parallel,
        )
    return [[int(value) for value in row] for row in raw.tolist()]
