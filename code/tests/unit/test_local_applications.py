from __future__ import annotations

import numpy as np
import pytest

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.local.applications import (
    dense_score,
    greedy_dense_subgraph,
    random_dense_search,
    sample_database_search,
    train_linear_graph_classifier,
)


def test_dense_subgraph_search_helpers_return_best_nodes() -> None:
    adjacency = np.array(
        [
            [0.0, 1.0, 1.0, 0.1],
            [1.0, 0.0, 1.0, 0.1],
            [1.0, 1.0, 0.0, 0.1],
            [0.1, 0.1, 0.1, 0.0],
        ]
    )

    greedy = greedy_dense_subgraph(adjacency, size=3)
    random_result = random_dense_search(adjacency, size=3, iterations=20, seed=7)
    sample_result = sample_database_search(
        adjacency,
        [[1, 1, 1, 0], [1, 0, 1, 1], [0, 1, 1, 1]],
        size=3,
        iterations=3,
        seed=7,
    )

    assert set(greedy.nodes.tolist()) == {0, 1, 2}
    assert dense_score(adjacency, greedy.nodes) == pytest.approx(6.0)
    assert random_result.best_score <= greedy.best_score
    assert sample_result.best_score == pytest.approx(6.0)


def test_sample_database_requires_matching_candidate_size() -> None:
    with pytest.raises(InvalidParameterError):
        sample_database_search(np.eye(3), [[1, 0, 0]], size=2)


def test_train_linear_graph_classifier_returns_plot_line() -> None:
    features = np.array([[1.0, 1.0], [1.1, 0.9], [-1.0, -1.0], [-1.2, -0.8]])
    labels = np.array([1, 1, 0, 0])

    result = train_linear_graph_classifier(features, labels)

    assert result.scaled_features.shape == (4, 2)
    assert result.labels.tolist() == [1, 1, 0, 0]
    assert len(result.line_x) == 2
    assert len(result.line_y) == 2
