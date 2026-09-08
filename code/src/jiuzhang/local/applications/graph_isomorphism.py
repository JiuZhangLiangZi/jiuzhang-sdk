"""Local graph-isomorphism application helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.local.applications._deps import optional_dependency

__all__ = [
    "GraphClassificationResult",
    "event_feature_vector",
    "event_feature_vector_from_samples",
    "load_graph_samples",
    "load_mutag_graphs",
    "orbit_feature_vector_from_samples",
    "sample_to_event",
    "sample_to_orbit",
    "train_linear_graph_classifier",
]


@dataclass(frozen=True)
class GraphClassificationResult:
    """Linear graph-classification result."""

    scaled_features: npt.NDArray[np.float64]
    labels: npt.NDArray[np.int_]
    coef: npt.NDArray[np.float64]
    intercept: float
    line_x: list[float]
    line_y: list[float]


def load_mutag_graphs() -> list[npt.NDArray[np.float64]]:
    """Load four bundled MUTAG graph adjacency matrices.

    Returns:
        List of graph adjacency matrices used by the graph-isomorphism demo.
    """
    data = optional_dependency("strawberryfields.apps.data")
    return [
        np.asarray(data.Mutag0().adj, dtype=np.float64),
        np.asarray(data.Mutag1().adj, dtype=np.float64),
        np.asarray(data.Mutag2().adj, dtype=np.float64),
        np.asarray(data.Mutag3().adj, dtype=np.float64),
    ]


def load_graph_samples(paths: list[str]) -> list[npt.NDArray[np.int_]]:
    """Load graph sample databases from ``.npy`` files.

    Args:
        paths: Paths to sample files, one file per graph.

    Returns:
        List of two-dimensional integer sample arrays.
    """
    if not paths:
        raise InvalidParameterError("paths cannot be empty")
    return [_sample_array(np.load(path)) for path in paths]


def sample_to_orbit(sample: Any) -> list[int]:
    """Convert one sample to an orbit descriptor.

    Args:
        sample: One-dimensional photon-count sample.

    Returns:
        Orbit descriptor of the sample.
    """
    similarity = optional_dependency("strawberryfields.apps.similarity")
    return [int(value) for value in similarity.sample_to_orbit(sample)]


def sample_to_event(sample: Any, max_count: int) -> int:
    """Convert one sample to an event index.

    Args:
        sample: One-dimensional photon-count sample.
        max_count: Maximum photon count represented in the event space.

    Returns:
        Event index.
    """
    similarity = optional_dependency("strawberryfields.apps.similarity")
    return int(similarity.sample_to_event(sample, max_count))


def event_feature_vector_from_samples(
    samples: Any,
    events: list[int],
    max_count: int,
) -> npt.NDArray[np.float64]:
    """Compute event features from sampled graph data.

    Args:
        samples: Two-dimensional sample array.
        events: Event indices used as features.
        max_count: Maximum photon count represented in the event space.

    Returns:
        Feature vector for the requested event indices.
    """
    similarity = optional_dependency("strawberryfields.apps.similarity")
    return np.asarray(
        similarity.feature_vector_events_sampling(_sample_array(samples), events, max_count),
        dtype=np.float64,
    )


def orbit_feature_vector_from_samples(samples: Any, orbits: Any) -> npt.NDArray[np.float64]:
    """Compute orbit features from sampled graph data.

    Args:
        samples: Two-dimensional sample array.
        orbits: Orbit descriptors used as features.

    Returns:
        Feature vector for the requested orbits.
    """
    similarity = optional_dependency("strawberryfields.apps.similarity")
    return np.asarray(
        similarity.feature_vector_orbits_sampling(_sample_array(samples), orbits),
        dtype=np.float64,
    )


def event_feature_vector(
    adjacency: Any,
    events: list[int],
    max_count: int,
    *,
    samples: int | None = None,
    mean_photon_count: float = 5.5,
) -> npt.NDArray[np.float64]:
    """Compute event features directly from a graph adjacency matrix.

    Args:
        adjacency: Square graph adjacency matrix.
        events: Event indices used as features.
        max_count: Maximum photon count represented in the event space.
        samples: Optional number of generated samples used for estimation.
        mean_photon_count: Mean photon-count parameter used by the local
            calculation.

    Returns:
        Feature vector for the requested event indices.
    """
    nx = optional_dependency("networkx")
    similarity = optional_dependency("strawberryfields.apps.similarity")
    graph = nx.Graph(np.asarray(adjacency, dtype=np.float64))
    kwargs = {"n_mean": float(mean_photon_count)}
    if samples is not None:
        kwargs["samples"] = int(samples)
    return np.asarray(
        similarity.feature_vector_events(graph, events, max_count, **kwargs), dtype=np.float64
    )


def train_linear_graph_classifier(features: Any, labels: Any) -> GraphClassificationResult:
    """Train a local linear classifier on graph feature vectors.

    Args:
        features: Two-dimensional feature matrix.
        labels: One-dimensional integer class labels.

    Returns:
        Classifier parameters and a two-point separating line for plotting.
    """
    preprocessing = optional_dependency("sklearn.preprocessing")
    svm = optional_dependency("sklearn.svm")
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int_)
    if x.ndim != 2 or x.shape[0] == 0:
        raise InvalidParameterError("features must be a non-empty 2D array")
    if y.ndim != 1 or y.shape[0] != x.shape[0]:
        raise InvalidParameterError("labels must be a 1D array matching features")
    scaled = preprocessing.StandardScaler().fit_transform(x)
    classifier = svm.LinearSVC(random_state=7, dual="auto")
    classifier.fit(scaled, y)
    coef = np.asarray(classifier.coef_[0], dtype=np.float64)
    intercept = float(classifier.intercept_[0])
    line_x = [-1.5, 1.5]
    if coef.shape[0] >= 2 and abs(coef[1]) > 1e-12:
        slope = -coef[0] / coef[1]
        bias = -intercept / coef[1]
        line_y = [float(slope * value + bias) for value in line_x]
    else:
        line_y = [0.0, 0.0]
    return GraphClassificationResult(
        scaled_features=np.asarray(scaled, dtype=np.float64),
        labels=y,
        coef=coef,
        intercept=intercept,
        line_x=line_x,
        line_y=line_y,
    )


def _sample_array(samples: Any) -> npt.NDArray[np.int_]:
    arr = np.asarray(samples, dtype=np.int_)
    if arr.ndim != 2 or arr.size == 0:
        raise InvalidParameterError("samples must be a non-empty 2D array")
    return arr
