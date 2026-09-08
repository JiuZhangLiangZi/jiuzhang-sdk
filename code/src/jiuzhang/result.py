"""统一返回结构工厂函数。

SDK 所有公开方法返回形如::

    {
        "code": "OK" | "<ERROR_CODE>",
        "message": str,
        "timestamp": int,   # 毫秒级 Unix 时间戳
        "data": dict,       # 业务数据（可能为空 dict）
    }

的字典。本模块提供 :func:`make_result` 工厂函数，确保结构在所有调用点保持一致。

键集合（``code`` / ``message`` / ``timestamp`` / ``data``）属于公开 API 的一部分，
任何变更须遵守 :doc:`VERSIONING <../../VERSIONING>` 策略。
"""

from __future__ import annotations

import time
from typing import Any

from jiuzhang import errors

__all__ = ["make_result"]


def make_result(
    code: str = errors.OK,
    message: str = "",
    data: dict[str, Any] | None = None,
    *,
    timestamp: int | None = None,
) -> dict[str, Any]:
    """构造统一返回结构 dict。

    Args:
        code: 错误码字符串，缺省为 :data:`jiuzhang.errors.OK`。
        message: 人类可读的说明。
        data: 业务数据 dict；若为 ``None`` 则填充为空 dict。调用方后续修改
            原 dict 不会影响返回结果（浅拷贝隔离）。
        timestamp: 毫秒级时间戳；若为 ``None`` 则使用当前时间。

    Returns:
        含 ``code`` / ``message`` / ``timestamp`` / ``data`` 四个键的 dict。

    Examples:
        >>> result = make_result(message="ok", data={"x": 1})
        >>> set(result.keys()) == {"code", "message", "timestamp", "data"}
        True
        >>> result["code"]
        'OK'
        >>> result["data"]
        {'x': 1}
    """
    return {
        "code": code,
        "message": message,
        "timestamp": timestamp if timestamp is not None else int(time.time() * 1000),
        "data": dict(data) if data else {},
    }
