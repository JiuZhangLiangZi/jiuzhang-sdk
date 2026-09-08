from __future__ import annotations

import json

from jiuzhang import GBSResult, parse_gbs_result


def test_parse_direct_tianyan_result() -> None:
    result = parse_gbs_result(
        {
            "taskId": "70001",
            "taskStatus": 2,
            "resultMapPoints": {"experimental": [[0, 0.1]]},
        }
    )

    assert isinstance(result, GBSResult)
    assert result.task_id == "70001"
    assert result.is_success()
    assert result.experimental_distribution == [[0, 0.1]]


def test_parse_cloud_wrapped_result() -> None:
    result = parse_gbs_result(
        {
            "code": 0,
            "message": "success",
            "data": {
                "task_id": "jz_tsk_1",
                "project_id": "EXP-test",
                "quantum_computer_id": "PH_QC_04",
                "status": "SUCCESS",
                "task_name": "demo",
                "tianyan_response": {
                    "taskStatus": 2,
                    "resultMapPoints": {
                        "experimental": [[0, 0.1]],
                        "ground_truth": [[0, 0.11]],
                        "squashed": [[0, 0.12]],
                        "thermal": [[0, 0.09]],
                        "distinguishable": [[0, 0.08]],
                    },
                    "resultDownloadUrl": "http://example.test/result.json",
                },
            },
        }
    )

    assert result.task_id == "jz_tsk_1"
    assert result.project_id == "EXP-test"
    assert result.quantum_computer_id == "PH_QC_04"
    assert result.status_name == "SUCCESS"
    assert result.download_url == "http://example.test/result.json"
    assert result.ground_truth_distribution == [[0, 0.11]]


def test_status_mapping_and_to_dict_json_serializable() -> None:
    assert parse_gbs_result({"taskStatus": "SUCCESS"}).is_success()
    assert parse_gbs_result({"taskStatus": 3}).is_failed()
    assert parse_gbs_result({"taskStatus": "unexpected"}).status_name == "UNKNOWN"
    json.dumps(parse_gbs_result({}).to_dict())
