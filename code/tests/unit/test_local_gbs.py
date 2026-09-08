from __future__ import annotations

import json

import numpy as np
import pytest

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.local.gbs import (
    GBSProgram,
    dumps_ir,
    hafnian,
    random_adjacency_matrix,
    sample_gbs,
    samples_to_distribution,
    to_blackbird,
    to_xir,
    torontonian,
)

pytest.importorskip("thewalrus")


def test_hafnian_and_torontonian_wrap_backend_values() -> None:
    adjacency = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert hafnian(adjacency) == pytest.approx(1.0)

    tor_matrix = np.array([[0.1, 0.02], [0.02, 0.1]])
    assert torontonian(tor_matrix) == pytest.approx(0.11138556118596776)


def test_random_adjacency_matrix_shape_and_symmetry() -> None:
    matrix = random_adjacency_matrix(6, seed=42)
    assert matrix.shape == (6, 6)
    np.testing.assert_allclose(matrix, matrix.T)
    np.testing.assert_allclose(np.diag(matrix), np.zeros(6))


def test_sample_gbs_returns_integer_samples() -> None:
    adjacency = random_adjacency_matrix(4, scale=0.15, seed=7)
    samples = sample_gbs(
        adjacency,
        shots=4,
        mean_photon_count=0.5,
        cutoff=3,
        max_photons=6,
        seed=123,
    )
    assert len(samples) == 4
    assert all(len(row) == 4 for row in samples)
    assert all(isinstance(value, int) and value >= 0 for row in samples for value in row)


def test_samples_to_distribution_normalizes_patterns() -> None:
    dist = samples_to_distribution([[0, 1], [0, 1], [1, 0]])
    assert dist == {(0, 1): pytest.approx(2 / 3), (1, 0): pytest.approx(1 / 3)}


def test_gbs_program_json_and_text_ir() -> None:
    program = GBSProgram(modes=2).squeezing([0.35, 0.2]).edge(0, 1, 0.5).measure_fock(shots=10)

    payload = json.loads(dumps_ir(program))
    assert payload["schema"] == "jiuzhang.local.gbs.v1"
    assert payload["modes"] == 2
    assert len(payload["operations"]) == 4

    blackbird_text = to_blackbird(program)
    assert "Sgate" in blackbird_text
    assert "MeasureFock" in blackbird_text

    xir_text = to_xir(program)
    assert "squeezing" in xir_text
    assert "measure_fock" in xir_text


def test_invalid_local_inputs_raise_sdk_errors() -> None:
    with pytest.raises(InvalidParameterError):
        hafnian([[1, 2, 3]])
    with pytest.raises(InvalidParameterError):
        sample_gbs([[0, 1], [1, 0]], shots=0)
    with pytest.raises(InvalidParameterError):
        GBSProgram(modes=2).edge(0, 0, 1.0)
