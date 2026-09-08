from __future__ import annotations

import pytest

from jiuzhang import GBSParams, InvalidParameterError, input_mode_count, output_mode_count


def test_valid_params_payload_and_summary() -> None:
    params = GBSParams(
        project_id="EXP-test",
        quantum_computer_id="PH_QC_04",
        mt=300,
        pump_energy_nj=3.3,
        squeezing_param=1.3,
        shots=1000,
        task_name="demo",
    )

    params.validate()
    assert params.input_mode_count() == 900
    assert params.output_mode_count() == 3420
    assert params.to_cloud_payload() == {
        "project_id": "EXP-test",
        "task_name": "demo",
        "quantum_computer_id": "PH_QC_04",
        "mt_value": 300,
        "pump_energy_nj": 3.3,
        "squeezing_param": 1.3,
        "shots": 1000,
    }
    assert params.summary()["output_mode_count"] == 3420


@pytest.mark.parametrize(
    "kwargs",
    [
        {"project_id": ""},
        {"quantum_computer_id": ""},
        {"mt": 0},
        {"mt": 501},
        {"pump_energy_nj": 0},
        {"squeezing_param": -0.1},
        {"shots": 0},
        {"task_name": ""},
    ],
)
def test_invalid_params_raise(kwargs: dict[str, object]) -> None:
    values: dict[str, object] = {
        "project_id": "EXP-test",
        "quantum_computer_id": "PH_QC_04",
        "mt": 64,
        "pump_energy_nj": 2.0,
        "squeezing_param": 0.35,
        "task_name": "demo",
    }
    values.update(kwargs)
    with pytest.raises(InvalidParameterError):
        GBSParams(**values).validate()  # type: ignore[arg-type]


def test_mode_count_helpers() -> None:
    assert input_mode_count(300) == 900
    assert output_mode_count(300) == 3420
