"""Mock GBS data helpers.

This module only generates mock data for tests and demos. It is not a physical
GBS simulator.

本模块仅生成测试和演示用 Mock 数据，不代表真实 GBS 物理采样。
"""

from __future__ import annotations

from typing import Any, cast

import numpy as np

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.gbs.params import input_mode_count, output_mode_count

__all__ = ["generate_mock_result", "generate_mock_result_map_points", "generate_mock_samples"]


def generate_mock_samples(
    *,
    modes: int,
    shots: int,
    mean_photon_count: float = 10.0,
    seed: int | None = None,
) -> list[list[int]]:
    """Generate reproducible fake GBS-like samples for tests and demos."""
    if isinstance(modes, bool) or not isinstance(modes, int) or modes <= 0:
        raise InvalidParameterError("modes 必须为正整数")
    if isinstance(shots, bool) or not isinstance(shots, int) or shots <= 0:
        raise InvalidParameterError("shots 必须为正整数")
    if mean_photon_count < 0:
        raise InvalidParameterError("mean_photon_count 必须为非负数")

    rng = np.random.default_rng(seed)
    poisson_values = cast(Any, rng.poisson(mean_photon_count, size=shots))
    total_photons = [int(value) for value in poisson_values.tolist()]
    samples = np.zeros((shots, modes), dtype=np.int32)
    for index, total_count in enumerate(total_photons):
        if total_count > 0:
            selected = rng.integers(0, modes, size=total_count)
            np.add.at(samples[index], selected, 1)
    return [[int(value) for value in row] for row in samples.tolist()]


def generate_mock_result_map_points(
    *,
    point_count: int = 50,
    seed: int | None = None,
) -> dict[str, list[list[float]]]:
    """Generate fake distribution-curve points for resultMapPoints."""
    if isinstance(point_count, bool) or not isinstance(point_count, int) or point_count <= 0:
        raise InvalidParameterError("point_count 必须为正整数")
    rng = np.random.default_rng(seed)
    x_values = [float(index) for index in range(point_count)]
    random_values = cast(Any, rng.random(point_count))
    base_raw = [float(value) for value in random_values.tolist()]
    base_total = sum(base_raw)
    base = [value / base_total for value in base_raw]

    def curve(noise: float) -> list[list[float]]:
        raw_noise_values = cast(Any, rng.normal(0.0, noise, point_count))
        noise_values = [float(value) for value in raw_noise_values.tolist()]
        values = [
            max(value + noise_value, 0.0)
            for value, noise_value in zip(base, noise_values, strict=True)
        ]
        values_total = sum(values)
        if values_total == 0:
            values = base
            values_total = sum(values)
        values = [value / values_total for value in values]
        return [[float(x), float(y)] for x, y in zip(x_values, values, strict=True)]

    return {
        "experimental": curve(0.004),
        "ground_truth": [[float(x), float(y)] for x, y in zip(x_values, base, strict=True)],
        "squashed": curve(0.008),
        "thermal": curve(0.01),
        "distinguishable": curve(0.012),
    }


def generate_mock_result(
    *,
    task_id: str = "mock-task-1",
    quantum_computer_id: str = "PH_QC_04",
    mt: int = 300,
    pump_energy_nj: float = 3.3,
    squeezing_param: float = 1.3,
    sample_count: int = 1000,
    seed: int | None = None,
) -> dict[str, Any]:
    """Generate a JiuZhang cloud-style mock task result."""
    return {
        "code": 0,
        "message": "success",
        "timestamp": "2026-07-03T10:05:00Z",
        "data": {
            "task_id": task_id,
            "task_name": "Mock GBS experiment",
            "status": "SUCCESS",
            "created_at": "2026-07-03T10:00:00Z",
            "tianyan_response": {
                "taskId": task_id.replace("jz_tsk_", "ty_"),
                "taskStatus": 2,
                "quantum_computer_id": quantum_computer_id,
                "mtValue": mt,
                "pumpEnergyNj": pump_energy_nj,
                "squeezingParam": squeezing_param,
                "sampleCount": sample_count,
                "inputModeCount": input_mode_count(mt),
                "outputModeCount": output_mode_count(mt),
                "resultMapPoints": generate_mock_result_map_points(seed=seed),
                "failReason": None,
                "resultDownloadUrl": f"http://127.0.0.1:18081/mock-results/{task_id}.json",
            },
        },
    }
