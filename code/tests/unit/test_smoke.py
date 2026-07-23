"""冒烟测试：验证包能正确安装、导入，公开 API 完整。"""

from __future__ import annotations

import re

import jiuzhang


def test_package_importable() -> None:
    """SDK 包可被 import。"""
    assert jiuzhang is not None


def test_version_format() -> None:
    """``__version__`` 符合 PEP 440 alpha / rc / 正式版形式。"""
    assert hasattr(jiuzhang, "__version__")
    assert isinstance(jiuzhang.__version__, str)
    assert re.match(r"^\d+\.\d+\.\d+(a\d+|rc\d+)?$", jiuzhang.__version__)


def test_version_pinned_for_current_release() -> None:
    """当前预发布版本号锁定为 ``0.1.0a30``。"""
    assert jiuzhang.__version__ == "0.1.0a30"


def test_public_api_all_importable() -> None:
    """``__all__`` 中列出的所有符号可成功从 ``jiuzhang`` 顶层导入。"""
    for name in jiuzhang.__all__:
        assert hasattr(jiuzhang, name), f"jiuzhang.__all__ 声明了 {name!r} 但实际未导出"


def test_public_api_minimum_set() -> None:
    """平台型 HTTP 主线公开 API 必须在 ``__all__`` 中。"""
    required = {
        "CloudClient",
        "GBSParams",
        "GBSResult",
        "HttpTransport",
        "TokenManager",
        "JiuzhangError",
        "parse_gbs_result",
    }
    missing = required - set(jiuzhang.__all__)
    assert not missing, f"公开 API 缺失核心符号：{missing}"


def test_removed_direct_machine_api_not_exported() -> None:
    """真机直连旧 API 不再从顶层导出。"""
    removed = {"Photo" + "nicMachine", "Gaussian" + "BosonSampler"}
    assert removed.isdisjoint(jiuzhang.__all__)


def test_exception_hierarchy() -> None:
    """所有具体异常子类都继承自 ``JiuzhangError``。"""
    from jiuzhang import (
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

    subclasses = [
        TokenInvalidError,
        TokenExpiredError,
        PermissionDeniedError,
        InvalidParameterError,
        MachineOfflineError,
        MachineBusyError,
        TimeoutError,
        InternalError,
    ]
    for cls in subclasses:
        assert issubclass(cls, JiuzhangError), f"{cls.__name__} 应继承自 JiuzhangError"


def test_error_codes_stable() -> None:
    """错误码字符串常量值与文档承诺一致。"""
    from jiuzhang import errors

    assert errors.OK == "OK"
    assert errors.TOKEN_INVALID == "TOKEN_INVALID"
    assert errors.TOKEN_EXPIRED == "TOKEN_EXPIRED"
    assert errors.PERMISSION_DENIED == "PERMISSION_DENIED"
    assert errors.INVALID_PARAMETER == "INVALID_PARAMETER"
    assert errors.MACHINE_OFFLINE == "MACHINE_OFFLINE"
    assert errors.MACHINE_BUSY == "MACHINE_BUSY"
    assert errors.TIMEOUT == "TIMEOUT"
    assert errors.INTERNAL_ERROR == "INTERNAL_ERROR"


def test_error_code_to_exception_mapping_complete() -> None:
    """``ERROR_CODE_TO_EXCEPTION`` 映射覆盖所有非 OK 错误码。"""
    from jiuzhang import errors
    from jiuzhang.exceptions import JiuzhangError

    expected_codes = {
        errors.TOKEN_INVALID,
        errors.TOKEN_EXPIRED,
        errors.PERMISSION_DENIED,
        errors.INVALID_PARAMETER,
        errors.MACHINE_OFFLINE,
        errors.MACHINE_BUSY,
        errors.TIMEOUT,
        errors.INTERNAL_ERROR,
    }
    assert set(errors.ERROR_CODE_TO_EXCEPTION.keys()) == expected_codes
    for exc_cls in errors.ERROR_CODE_TO_EXCEPTION.values():
        assert issubclass(exc_cls, JiuzhangError)


def test_exception_default_code_alignment() -> None:
    """每个异常子类的 ``default_code`` 与映射表保持自洽。"""
    from jiuzhang import errors

    for code, exc_cls in errors.ERROR_CODE_TO_EXCEPTION.items():
        assert (
            exc_cls.default_code == code
        ), f"{exc_cls.__name__}.default_code({exc_cls.default_code!r}) 与映射键 {code!r} 不一致"


def test_token_manager_constructs_without_network(sample_token_id: str) -> None:
    """``TokenManager`` 构造不发起网络请求，仅缓存 token。"""
    from jiuzhang import TokenManager

    tm = TokenManager(token_id=sample_token_id)
    assert tm.token_id == sample_token_id
