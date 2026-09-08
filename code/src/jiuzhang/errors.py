"""SDK 错误码字符串常量与错误码 → 异常类映射。

错误码集合是公开 API 的一部分，任何新增/删除/重命名都属于
breaking change，须遵守 :doc:`VERSIONING <../../VERSIONING>` 策略。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from jiuzhang.exceptions import JiuzhangError

__all__ = [
    "ERROR_CODE_TO_EXCEPTION",
    "INTERNAL_ERROR",
    "INVALID_PARAMETER",
    "MACHINE_BUSY",
    "MACHINE_OFFLINE",
    "OK",
    "PERMISSION_DENIED",
    "TIMEOUT",
    "TOKEN_EXPIRED",
    "TOKEN_INVALID",
]

# -----------------------------------------------------------------------------
# 错误码字符串常量（统一返回结构中 ``code`` 字段的合法取值）
# -----------------------------------------------------------------------------

OK: Final[str] = "OK"
TOKEN_INVALID: Final[str] = "TOKEN_INVALID"
TOKEN_EXPIRED: Final[str] = "TOKEN_EXPIRED"
PERMISSION_DENIED: Final[str] = "PERMISSION_DENIED"
INVALID_PARAMETER: Final[str] = "INVALID_PARAMETER"
MACHINE_OFFLINE: Final[str] = "MACHINE_OFFLINE"
MACHINE_BUSY: Final[str] = "MACHINE_BUSY"
TIMEOUT: Final[str] = "TIMEOUT"
INTERNAL_ERROR: Final[str] = "INTERNAL_ERROR"


#: 错误码字符串到异常类的映射，供协议层 ``ERROR`` 消息映射到 Python 异常使用。
#:
#: 本字典在模块加载时为空，由 :mod:`jiuzhang` 顶层 ``__init__`` 在所有
#: 异常类导入完成后调用 :func:`_populate_error_code_to_exception` 填充。
#: 这样安排是为了打破 ``errors.py`` 与 ``exceptions.py`` 之间的循环依赖。
ERROR_CODE_TO_EXCEPTION: dict[str, type[JiuzhangError]] = {}


def _populate_error_code_to_exception() -> None:
    """在 SDK 加载完成后填充 :data:`ERROR_CODE_TO_EXCEPTION`。

    本函数由 :mod:`jiuzhang.__init__` 在所有异常类导入后调用一次；
    重复调用是幂等的（先清空再填充）。
    """
    from jiuzhang.exceptions import (
        InternalError,
        InvalidParameterError,
        MachineBusyError,
        MachineOfflineError,
        PermissionDeniedError,
        TokenExpiredError,
        TokenInvalidError,
    )
    from jiuzhang.exceptions import (
        TimeoutError as JiuzhangTimeoutError,
    )

    ERROR_CODE_TO_EXCEPTION.clear()
    ERROR_CODE_TO_EXCEPTION.update(
        {
            TOKEN_INVALID: TokenInvalidError,
            TOKEN_EXPIRED: TokenExpiredError,
            PERMISSION_DENIED: PermissionDeniedError,
            INVALID_PARAMETER: InvalidParameterError,
            MACHINE_OFFLINE: MachineOfflineError,
            MACHINE_BUSY: MachineBusyError,
            TIMEOUT: JiuzhangTimeoutError,
            INTERNAL_ERROR: InternalError,
        }
    )
