"""PR-3：``result.make_result`` 单元测试。

覆盖目标：

* 默认参数（``code = OK`` / 空 message / 空 data / 当前时间 timestamp）
* 显式参数覆盖
* ``data`` 浅拷贝隔离（与 ``JiuzhangError.details`` 行为对齐）
* 返回 dict 的键集合与公开 API 契约一致
"""

from __future__ import annotations

import time

from jiuzhang import errors
from jiuzhang.result import make_result


def test_returns_four_canonical_keys() -> None:
    """返回 dict 含 code / message / timestamp / data 四个键。"""
    result = make_result()
    assert set(result.keys()) == {"code", "message", "timestamp", "data"}


def test_default_code_is_ok() -> None:
    assert make_result()["code"] == errors.OK


def test_default_message_is_empty_string() -> None:
    assert make_result()["message"] == ""


def test_default_data_is_empty_dict() -> None:
    assert make_result()["data"] == {}


def test_timestamp_defaults_to_current_time_ms() -> None:
    before = int(time.time() * 1000)
    result = make_result()
    after = int(time.time() * 1000)
    assert before <= result["timestamp"] <= after


def test_explicit_code_message_data() -> None:
    result = make_result(code=errors.MACHINE_BUSY, message="忙", data={"queue_len": 7})
    assert result["code"] == errors.MACHINE_BUSY
    assert result["message"] == "忙"
    assert result["data"] == {"queue_len": 7}


def test_explicit_timestamp_respected() -> None:
    result = make_result(timestamp=1762819200000)
    assert result["timestamp"] == 1762819200000


def test_data_shallow_copy_isolation() -> None:
    """调用方修改原 dict 不应影响返回结果。"""
    payload: dict[str, object] = {"trace_id": "abc"}
    result = make_result(data=payload)
    payload["trace_id"] = "MUTATED"
    assert result["data"] == {"trace_id": "abc"}


def test_none_data_normalised_to_empty_dict() -> None:
    assert make_result(data=None)["data"] == {}


def test_empty_data_normalised_to_empty_dict() -> None:
    assert make_result(data={})["data"] == {}
