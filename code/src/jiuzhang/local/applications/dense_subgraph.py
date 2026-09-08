"""Local dense-subgraph application helpers."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np
import numpy.typing as npt

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.local.applications._deps import optional_dependency

__all__ = [
    "DenseSearchResult",
    "dense_score",
    "greedy_dense_subgraph",
    "load_planted_dense_graph",
    "load_sample_database",
    "random_dense_search",
    "sample_database_search",
    "simulated_annealing_dense_search",
]


@dataclass(frozen=True)
class DenseSearchResult:
    """Dense-subgraph search result."""

    scores: npt.NDArray[np.float64]
    nodes: npt.NDArray[np.int_]
    best_score: float


def load_planted_dense_graph() -> npt.NDArray[np.float64]:
    """Load the bundled planted dense-subgraph adjacency matrix.

    Returns:
        A weighted adjacency matrix for the dense-subgraph demo.
    """
    data = optional_dependency("strawberryfields.apps.data")
    return np.asarray(data.Planted().adj, dtype=np.float64)


def load_sample_database(path: str) -> npt.NDArray[np.int_]:
    """Load a local sample database from a ``.npy`` file.

    Args:
        path: Path to a NumPy ``.npy`` file containing sample rows.

    Returns:
        Two-dimensional integer sample array.
    """
    samples = np.asarray(np.load(path), dtype=np.int_)
    if samples.ndim != 2 or samples.size == 0:
        raise InvalidParameterError("sample database must be a non-empty 2D array")
    return samples


def dense_score(adjacency: Any, nodes: Any) -> float:
    """Compute the total edge weight inside a selected node set.

    Args:
        adjacency: Square graph adjacency matrix.
        nodes: Node indices used to form the candidate subgraph.

    Returns:
        Absolute sum of the selected adjacency submatrix.
    """
    matrix = _matrix(adjacency)
    selected = _nodes(nodes, matrix.shape[0])
    return float(abs(np.sum(matrix[np.ix_(selected, selected)])))


def greedy_dense_subgraph(adjacency: Any, *, size: int) -> DenseSearchResult:
    """Find a dense subgraph with greedy node deletion.

    Args:
        adjacency: Square graph adjacency matrix.
        size: Number of nodes retained in the returned subgraph.

    Returns:
        Search result containing the selected nodes and best score trace.
    """
    matrix = _matrix(adjacency)
    target_size = _positive_int(size, name="size")
    if target_size > matrix.shape[0]:
        raise InvalidParameterError("size cannot exceed the graph node count")

    index = np.arange(matrix.shape[0], dtype=np.int_)
    best_score = dense_score(matrix, index)
    while len(index) > target_size:
        candidates = np.array(list(combinations(range(len(index)), len(index) - 1)))
        scores = np.array([dense_score(matrix, index[candidate]) for candidate in candidates])
        best = int(scores.argmax())
        index = index[candidates[best]]
        best_score = float(scores[best])
    return DenseSearchResult(
        scores=np.asarray([best_score], dtype=np.float64),
        nodes=index.astype(np.int_),
        best_score=best_score,
    )


def random_dense_search(
    adjacency: Any,
    *,
    size: int,
    iterations: int = 1000,
    seed: int | None = None,
) -> DenseSearchResult:
    """Search dense subgraphs by uniform random candidates.

    Args:
        adjacency: Square graph adjacency matrix.
        size: Number of nodes in each candidate subgraph.
        iterations: Number of random candidates evaluated.
        seed: Optional random seed for reproducibility.

    Returns:
        Search result containing best-score trace and selected nodes.
    """
    matrix = _matrix(adjacency)
    target_size = _positive_int(size, name="size")
    total = _positive_int(iterations, name="iterations")
    rng = np.random.default_rng(seed)
    best_nodes = np.zeros(target_size, dtype=np.int_)
    best_score = 0.0
    scores = np.zeros(total, dtype=np.float64)
    nodes = np.arange(matrix.shape[0], dtype=np.int_)
    for index in range(total):
        candidate = rng.choice(nodes, target_size, replace=False)
        score = dense_score(matrix, candidate)
        if score > best_score:
            best_score = score
            best_nodes = np.asarray(candidate, dtype=np.int_)
        scores[index] = best_score
    return DenseSearchResult(scores=scores, nodes=best_nodes, best_score=best_score)


def sample_database_search(
    adjacency: Any,
    samples: Any,
    *,
    size: int,
    iterations: int = 1000,
    seed: int | None = None,
) -> DenseSearchResult:
    """Search dense subgraphs from a local sample database.

    Args:
        adjacency: Square graph adjacency matrix.
        samples: Two-dimensional samples. Non-zero entries are treated as
            selected nodes.
        size: Required selected node count after thresholding samples.
        iterations: Number of candidate samples evaluated.
        seed: Optional random seed for reproducibility.

    Returns:
        Search result containing best-score trace and selected nodes.
    """
    matrix = _matrix(adjacency)
    database = _binary_database(samples, size=size)
    total = min(_positive_int(iterations, name="iterations"), len(database))
    rng = np.random.default_rng(seed)
    selected_rows = rng.choice(np.arange(len(database)), size=total, replace=False)
    best_nodes = np.zeros(size, dtype=np.int_)
    best_score = 0.0
    scores = np.zeros(total, dtype=np.float64)
    for index, row_index in enumerate(selected_rows):
        candidate = np.nonzero(database[int(row_index)])[0].astype(np.int_)
        score = dense_score(matrix, candidate)
        if score > best_score:
            best_score = score
            best_nodes = candidate
        scores[index] = best_score
    return DenseSearchResult(scores=scores, nodes=best_nodes, best_score=best_score)


def simulated_annealing_dense_search(
    adjacency: Any,
    *,
    size: int,
    iterations: int = 1000,
    change_count: int | None = None,
    temperature: float = 0.1,
    cooling_ratio: float = 0.995,
    seed: int | None = None,
) -> DenseSearchResult:
    """Search dense subgraphs with simulated annealing.

    Args:
        adjacency: Square graph adjacency matrix.
        size: Number of selected nodes.
        iterations: Number of annealing steps.
        change_count: Maximum number of nodes replaced in one step. Defaults to
            ``size``.
        temperature: Initial acceptance temperature.
        cooling_ratio: Multiplicative temperature decay per iteration.
        seed: Optional random seed for reproducibility.

    Returns:
        Search result containing best-score trace and selected nodes.
    """
    matrix = _matrix(adjacency)
    target_size = _positive_int(size, name="size")
    total = _positive_int(iterations, name="iterations")
    changes = (
        target_size if change_count is None else _positive_int(change_count, name="change_count")
    )
    rng = np.random.default_rng(seed)
    all_nodes = np.arange(matrix.shape[0], dtype=np.int_)
    current = rng.choice(all_nodes, target_size, replace=False)
    current_score = dense_score(matrix, current)
    best_score = current_score
    best_nodes = current.copy()
    scores = np.zeros(total, dtype=np.float64)
    temp = float(temperature)
    for index in range(total):
        replace_count = int(rng.integers(1, min(changes, target_size) + 1))
        keep_count = target_size - replace_count
        kept = (
            rng.choice(current, keep_count, replace=False)
            if keep_count > 0
            else np.array([], dtype=np.int_)
        )
        pool = np.setdiff1d(all_nodes, kept, assume_unique=False)
        candidate = np.concatenate([kept, rng.choice(pool, replace_count, replace=False)])
        score = dense_score(matrix, candidate)
        if score > current_score or rng.random() < np.exp(
            (score - current_score) / max(temp, 1e-12)
        ):
            current = candidate
            current_score = score
            if score > best_score:
                best_score = score
                best_nodes = candidate.copy()
        temp *= float(cooling_ratio)
        scores[index] = best_score
    return DenseSearchResult(scores=scores, nodes=best_nodes.astype(np.int_), best_score=best_score)


def _matrix(adjacency: Any) -> npt.NDArray[np.float64]:
    matrix = np.asarray(adjacency, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[0] != matrix.shape[1]:
        raise InvalidParameterError("adjacency must be a non-empty square matrix")
    return matrix


def _nodes(nodes: Any, node_count: int) -> npt.NDArray[np.int_]:
    selected = np.asarray(nodes, dtype=np.int_)
    if selected.ndim != 1 or selected.size == 0:
        raise InvalidParameterError("nodes must be a non-empty 1D array")
    if np.any(selected < 0) or np.any(selected >= node_count):
        raise InvalidParameterError("nodes contain out-of-range indices")
    return selected


def _binary_database(samples: Any, *, size: int) -> npt.NDArray[np.int_]:
    arr = np.asarray(samples)
    if arr.ndim != 2 or arr.size == 0:
        raise InvalidParameterError("samples must be a non-empty 2D array")
    binary = (arr > 0).astype(np.int_)
    selected = np.asarray(binary[np.sum(binary, axis=1) == size], dtype=np.int_)
    if selected.size == 0:
        raise InvalidParameterError("samples do not contain candidates with the requested size")
    return selected


def _positive_int(value: Any, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InvalidParameterError(f"{name} must be a positive integer")
    return value
