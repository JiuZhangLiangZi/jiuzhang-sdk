"""PR-2：异常类 ``__init__`` 与 ``to_result`` 单元测试。

覆盖目标：

* :class:`~jiuzhang.exceptions.JiuzhangError` 的字段缺省行为
* 显式 ``code`` / ``details`` / ``timestamp`` 注入
* :meth:`~jiuzhang.exceptions.JiuzhangError.to_result` 返回的统一结构
* 8 个具体子类的 ``default_code`` 自洽
* ``details`` 入参的浅拷贝隔离（构造方修改入参不影响异常对象内部状态）
"""

from __future__ import annotations

import time

import pytest

from jiuzhang import errors
from jiuzhang.exceptions import (
    InternalError,
    InvalidParameterError,
    JiuzhangError,
    MachineBusyError,
    MachineOfflineError,
    PermissionDeniedError,
    TimeoutError,
    TokenExpiredError,
    TokenInvalidError,
)

# -----------------------------------------------------------------------------
# 基类构造与字段
# -----------------------------------------------------------------------------


class TestJiuzhangErrorInit:
    """JiuzhangError.__init__ 缺省 / 显式注入 / 边界场景。"""

    def test_default_code_falls_back_to_class_attribute(self) -> None:
        err = JiuzhangError("boom")
        assert err.code == JiuzhangError.default_code == errors.INTERNAL_ERROR

    def test_message_stored_verbatim(self) -> None:
        err = JiuzhangError("人类可读说明")
        assert err.message == "人类可读说明"
        assert str(err) == "人类可读说明"

    def test_timestamp_defaults_to_current_time_ms(self) -> None:
        before = int(time.time() * 1000)
        err = JiuzhangError("now")
        after = int(time.time() * 1000)
        assert before <= err.timestamp <= after

    def test_timestamp_can_be_pinned(self) -> None:
        err = JiuzhangError("pinned", timestamp=1762819200000)
        assert err.timestamp == 1762819200000

    def test_explicit_code_overrides_default(self) -> None:
        err = JiuzhangError("override", code=errors.TIMEOUT)
        assert err.code == errors.TIMEOUT

    def test_details_defaults_to_empty_dict(self) -> None:
        err = JiuzhangError("no details")
        assert err.details == {}

    def test_details_stored_as_copy(self) -> None:
        """构造方后续修改原 dict 不应影响异常内部 details。"""
        payload: dict[str, object] = {"trace_id": "abc123"}
        err = JiuzhangError("with details", details=payload)
        payload["trace_id"] = "MUTATED"
        assert err.details == {"trace_id": "abc123"}

    def test_falsy_details_normalised_to_empty(self) -> None:
        err = JiuzhangError("falsy", details=None)
        assert err.details == {}


# -----------------------------------------------------------------------------
# to_result
# -----------------------------------------------------------------------------


class TestToResult:
    """JiuzhangError.to_result 返回的统一结构。"""

    def test_returns_four_canonical_keys(self) -> None:
        err = JiuzhangError("ok")
        result = err.to_result()
        assert set(result.keys()) == {"code", "message", "timestamp", "data"}

    def test_fields_round_trip(self) -> None:
        err = JiuzhangError(
            "with everything",
            code=errors.MACHINE_BUSY,
            details={"queue_len": 3},
            timestamp=1762819200000,
        )
        result = err.to_result()
        assert result == {
            "code": errors.MACHINE_BUSY,
            "message": "with everything",
            "timestamp": 1762819200000,
            "data": {"queue_len": 3},
        }

    def test_data_field_is_details_dict(self) -> None:
        err = JiuzhangError("d", details={"x": 1, "y": [2, 3]})
        assert err.to_result()["data"] == {"x": 1, "y": [2, 3]}

    def test_data_defaults_to_empty_dict_when_no_details(self) -> None:
        err = JiuzhangError("no details")
        assert err.to_result()["data"] == {}


# -----------------------------------------------------------------------------
# 子类 default_code 自洽
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("exc_cls", "expected_code"),
    [
        (TokenInvalidError, errors.TOKEN_INVALID),
        (TokenExpiredError, errors.TOKEN_EXPIRED),
        (PermissionDeniedError, errors.PERMISSION_DENIED),
        (InvalidParameterError, errors.INVALID_PARAMETER),
        (MachineOfflineError, errors.MACHINE_OFFLINE),
        (MachineBusyError, errors.MACHINE_BUSY),
        (TimeoutError, errors.TIMEOUT),
        (InternalError, errors.INTERNAL_ERROR),
    ],
)
def test_subclass_default_code(exc_cls: type[JiuzhangError], expected_code: str) -> None:
    """每个具体子类的 default_code 等于其在 ERROR_CODE_TO_EXCEPTION 中的键。"""
    assert exc_cls.default_code == expected_code
    err = exc_cls("boom")
    assert err.code == expected_code
    assert err.to_result()["code"] == expected_code


@pytest.mark.parametrize(
    "exc_cls",
    [
        TokenInvalidError,
        TokenExpiredError,
        PermissionDeniedError,
        InvalidParameterError,
        MachineOfflineError,
        MachineBusyError,
        TimeoutError,
        InternalError,
    ],
)
def test_subclass_is_jiuzhang_error(exc_cls: type[JiuzhangError]) -> None:
    """所有子类可被 ``except JiuzhangError`` 捕获。"""
    with pytest.raises(JiuzhangError):
        raise exc_cls("subclass")


def test_error_code_to_exception_round_trip() -> None:
    """``errors.ERROR_CODE_TO_EXCEPTION[code](msg).code == code`` 闭环。"""
    for code, exc_cls in errors.ERROR_CODE_TO_EXCEPTION.items():
        instance = exc_cls("round-trip")
        assert instance.code == code
        assert instance.to_result()["code"] == code
