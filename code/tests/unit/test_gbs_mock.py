from __future__ import annotations

from jiuzhang import parse_gbs_result
from jiuzhang.gbs.mock import (
    generate_mock_result,
    generate_mock_result_map_points,
    generate_mock_samples,
)


def test_mock_samples_are_reproducible_and_shaped() -> None:
    left = generate_mock_samples(modes=5, shots=3, seed=42)
    right = generate_mock_samples(modes=5, shots=3, seed=42)

    assert left == right
    assert len(left) == 3
    assert len(left[0]) == 5


def test_mock_result_can_be_parsed() -> None:
    result = parse_gbs_result(generate_mock_result(task_id="jz_tsk_mock_1", seed=7))

    assert result.task_id == "jz_tsk_mock_1"
    assert result.status_name == "SUCCESS"
    assert result.experimental_distribution is not None


def test_result_map_points_contains_expected_keys() -> None:
    points = generate_mock_result_map_points(seed=1)

    assert set(points) == {
        "experimental",
        "ground_truth",
        "squashed",
        "thermal",
        "distinguishable",
    }
