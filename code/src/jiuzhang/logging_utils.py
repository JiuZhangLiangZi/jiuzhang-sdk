"""SDK 日志工具。

SDK 内部统一通过 :func:`get_logger` 获取 logger，命名空间始终以 ``jiuzhang.``
开头。根 logger ``jiuzhang`` 上挂载一个 :class:`logging.NullHandler`，避免在
调用方未配置日志时产生 "No handlers could be found for logger" 警告。

调用方可通过标准 :mod:`logging` 配置 ``jiuzhang`` 命名空间来接管日志，例如::

    import logging
    logging.getLogger("jiuzhang").setLevel(logging.DEBUG)
    logging.getLogger("jiuzhang").addHandler(logging.StreamHandler())
"""

from __future__ import annotations

import logging

__all__ = ["get_logger"]

_ROOT_NAME = "jiuzhang"


def _ensure_root_null_handler() -> None:
    """确保 ``jiuzhang`` 根 logger 上挂载一个 :class:`logging.NullHandler`。

    幂等：若已存在 ``NullHandler`` 则不重复添加。
    """
    root_logger = logging.getLogger(_ROOT_NAME)
    if not any(isinstance(h, logging.NullHandler) for h in root_logger.handlers):
        root_logger.addHandler(logging.NullHandler())


def get_logger(name: str | None = None) -> logging.Logger:
    """获取 ``jiuzhang.*`` 命名空间下的 logger。

    Args:
        name: 子命名空间名称（如 ``"cloud.client"``）。若为 ``None``
            或空串则返回根 logger ``jiuzhang``。允许传入已带 ``jiuzhang.``
            前缀的完整名（如直接用模块的 ``__name__``）；本函数会自动归一化，
            不会产生 ``jiuzhang.jiuzhang.*`` 这种嵌套命名。

    Returns:
        配置了 :class:`logging.NullHandler` 的 logger 实例。

    Examples:
        >>> logger = get_logger("cloud.client")
        >>> logger.name
        'jiuzhang.cloud.client'
        >>> root = get_logger()
        >>> root.name
        'jiuzhang'
    """
    _ensure_root_null_handler()
    if not name:
        return logging.getLogger(_ROOT_NAME)
    if name == _ROOT_NAME or name.startswith(f"{_ROOT_NAME}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{_ROOT_NAME}.{name}")
