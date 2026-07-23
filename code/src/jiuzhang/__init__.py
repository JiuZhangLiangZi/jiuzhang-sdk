"""jiuzhang — 九章光量子云接入 Python SDK。

公开 API 由本模块的 ``__all__`` 锁定。未在其中列出的符号视为内部实现，
任何版本均可能变更。集成方应通过::

    from jiuzhang import CloudClient, TokenManager

的方式引用，避免直接 import 子模块的私有路径。
"""

from __future__ import annotations

from jiuzhang.auth import TokenManager
from jiuzhang.cloud import CloudClient, HttpTransport
from jiuzhang.errors import _populate_error_code_to_exception
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
from jiuzhang.gbs import GBSParams, GBSResult, input_mode_count, output_mode_count, parse_gbs_result
from jiuzhang.settings import Settings
from jiuzhang.version import __version__

# 在所有异常类完成导入后填充错误码 → 异常类映射，打破 errors.py 与
# exceptions.py 之间的循环依赖。
_populate_error_code_to_exception()
del _populate_error_code_to_exception

__all__ = [
    "CloudClient",
    "GBSParams",
    "GBSResult",
    "HttpTransport",
    "InternalError",
    "InvalidParameterError",
    "JiuzhangError",
    "MachineBusyError",
    "MachineOfflineError",
    "PermissionDeniedError",
    "Settings",
    "TimeoutError",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenManager",
    "__version__",
    "input_mode_count",
    "output_mode_count",
    "parse_gbs_result",
]
