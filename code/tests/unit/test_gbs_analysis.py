from __future__ import annotations

import numpy as np
import pytest

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.gbs.analysis import (
    click_count,
    click_count_histogram,
    collision_rate,
    hellinger_distance,
    js_divergence,
    mode_occupancy,
    photon_count,
    photon_count_histogram,
    top_k_patterns,
    total_variation_distance,
)

SAMPLES = [[0, 1, 0, 2], [1, 0, 0, 1], [0, 1, 0, 2]]


def test_sample_statistics() -> None:
    np.testing.assert_array_equal(photon_count(SAMPLES), np.array([3, 2, 3]))
    assert photon_count_histogram(SAMPLES) == {2: 1, 3: 2}
    np.testing.assert_array_equal(click_count(SAMPLES), np.array([2, 2, 2]))
    assert click_count_histogram(SAMPLES) == {2: 3}
    assert collision_rate(SAMPLES) == pytest.approx(2 / 3)
    assert top_k_patterns(SAMPLES, k=1) == [((0, 1, 0, 2), 2)]


def test_mode_occupancy() -> None:
    np.testing.assert_array_equal(mode_occupancy(SAMPLES, normalize=False), np.array([1, 2, 0, 5]))
    np.testing.assert_allclose(mode_occupancy(SAMPLES), np.array([1 / 8, 2 / 8, 0, 5 / 8]))


def test_distribution_distances() -> None:
    p = {"0010": 0.1, "0100": 0.2, "1000": 0.7}
    q = {"0010": 0.2, "0100": 0.2, "1000": 0.6}

    assert total_variation_distance(p, p) == pytest.approx(0.0)
    assert hellinger_distance(p, p) == pytest.approx(0.0)
    assert js_divergence(p, p) == pytest.approx(0.0)
    assert total_variation_distance(p, q) == pytest.approx(0.1)


@pytest.mark.parametrize("samples", [[], [[1, -1]], [[1.2, 0.0]], [1, 2, 3]])
def test_invalid_samples_raise(samples: object) -> None:
    with pytest.raises(InvalidParameterError):
        photon_count(samples)
