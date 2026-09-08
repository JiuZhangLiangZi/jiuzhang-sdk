"""SDK 异常类层次。

所有 SDK 异常继承自 :class:`JiuzhangError`，并携带与统一返回结构对齐的字段：

* ``code``      — 错误码字符串（见 :mod:`jiuzhang.errors`）
* ``message``   — 人类可读的错误说明
* ``timestamp`` — 异常构造时刻的毫秒级时间戳
* ``details``   — 可选的附加上下文 dict

异常类层次是公开 API 的一部分。任何变更须遵守
:doc:`VERSIONING <../../VERSIONING>` 策略。
"""

from __future__ import annotations

import time
from typing import Any

from jiuzhang import errors

__all__ = [
    "InternalError",
    "InvalidParameterError",
    "JiuzhangError",
    "MachineBusyError",
    "MachineOfflineError",
    "PermissionDeniedError",
    "TimeoutError",
    "TokenExpiredError",
    "TokenInvalidError",
]


class JiuzhangError(Exception):
    """SDK 统一异常基类。

    所有 SDK 抛出的异常均继承自本类。集成方可通过 ``except JiuzhangError``
    捕获 SDK 的所有错误。

    Attributes:
        code: 错误码字符串（见 :mod:`jiuzhang.errors`）。
        message: 人类可读的错误说明。
        timestamp: 异常构造时刻的毫秒级 Unix 时间戳。
        details: 可选的附加上下文，例如 ``request_id``、``trace_id``。
    """

    #: 子类默认错误码；构造时若未显式传入则使用此值。
    default_code: str = errors.INTERNAL_ERROR

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        timestamp: int | None = None,
    ) -> None:
        """构造异常。

        Args:
            message: 人类可读的错误说明。
            code: 错误码字符串；若为 ``None`` 则使用子类的 ``default_code``。
            details: 可选的附加上下文 dict。
            timestamp: 毫秒级时间戳；若为 ``None`` 则使用当前时间。
        """
        super().__init__(message)
        self.code: str = code if code is not None else self.default_code
        self.message: str = message
        self.timestamp: int = timestamp if timestamp is not None else int(time.time() * 1000)
        self.details: dict[str, Any] = dict(details) if details else {}

    def to_result(self) -> dict[str, Any]:
        """将异常转换为统一返回结构。

        Returns:
            dict 含 ``code`` / ``message`` / ``timestamp`` / ``data`` 四个键，
            其中 ``data`` 为本异常的 ``details``（可能为空 dict）。
        """
        return {
            "code": self.code,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.details,
        }


class TokenInvalidError(JiuzhangError):
    """Token 格式非法或哈希校验未通过（不可重试）。"""

    default_code = errors.TOKEN_INVALID


class TokenExpiredError(JiuzhangError):
    """Token 已过期，需用户在控制台重置（不可重试）。"""

    default_code = errors.TOKEN_EXPIRED


class PermissionDeniedError(JiuzhangError):
    """权限不足（不可重试）。"""

    default_code = errors.PERMISSION_DENIED


class InvalidParameterError(JiuzhangError):
    """参数超出 limits 范围或类型不合法（不可重试）。"""

    default_code = errors.INVALID_PARAMETER


class MachineOfflineError(JiuzhangError):
    """真机离线或维护中（可重试，建议指数退避）。"""

    default_code = errors.MACHINE_OFFLINE


class MachineBusyError(JiuzhangError):
    """真机当前忙于其他任务（可重试，建议指数退避）。"""

    default_code = errors.MACHINE_BUSY


class TimeoutError(JiuzhangError):  # 故意覆盖内建：保持错误码命名一致
    """SDK 与控制计算机的通信超时（可重试，建议重建连接）。"""

    default_code = errors.TIMEOUT


class InternalError(JiuzhangError):
    """真机或控制计算机内部错误（可重试一次）。"""

    default_code = errors.INTERNAL_ERROR
