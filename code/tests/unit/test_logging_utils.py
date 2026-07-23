"""``logging_utils.get_logger`` 单元测试。

覆盖目标：

* 命名空间归一（``None`` / ``""`` → 根 logger ``jiuzhang``）
* 子命名空间拼接（``"cloud.client"`` → ``jiuzhang.cloud.client``）
* 已带前缀的名不双重拼接（``"jiuzhang.foo"`` 仍为 ``jiuzhang.foo``）
* 根 logger 始终挂载 ``NullHandler``
* 重复调用不重复挂载 handler（幂等）
"""

from __future__ import annotations

import logging

from jiuzhang.logging_utils import get_logger


def test_default_returns_root_logger() -> None:
    logger = get_logger()
    assert logger.name == "jiuzhang"


def test_empty_string_returns_root_logger() -> None:
    logger = get_logger("")
    assert logger.name == "jiuzhang"


def test_subname_is_prefixed() -> None:
    logger = get_logger("cloud.client")
    assert logger.name == "jiuzhang.cloud.client"


def test_root_name_passed_explicitly_is_not_double_prefixed() -> None:
    logger = get_logger("jiuzhang")
    assert logger.name == "jiuzhang"


def test_already_prefixed_name_not_double_prefixed() -> None:
    logger = get_logger("jiuzhang.cloud.transport")
    assert logger.name == "jiuzhang.cloud.transport"


def test_root_has_null_handler_attached() -> None:
    """根 logger 上至少存在一个 NullHandler。"""
    get_logger()
    root = logging.getLogger("jiuzhang")
    assert any(isinstance(h, logging.NullHandler) for h in root.handlers)


def test_null_handler_attachment_is_idempotent() -> None:
    """多次调用 get_logger 不重复挂载 NullHandler。"""
    # 先清理掉所有现有 NullHandler，确保此处只看本测试的副作用
    root = logging.getLogger("jiuzhang")
    root.handlers = [h for h in root.handlers if not isinstance(h, logging.NullHandler)]
    get_logger()
    get_logger("a")
    get_logger("b.c")
    null_handlers = [h for h in root.handlers if isinstance(h, logging.NullHandler)]
    assert len(null_handlers) == 1


def test_returns_logging_logger_instance() -> None:
    logger = get_logger("cloud.client")
    assert isinstance(logger, logging.Logger)


def test_child_logger_propagates_to_root() -> None:
    """子 logger 默认 propagate=True，沿 parent 链最终可达 ``jiuzhang`` 根。"""
    child = get_logger("test.propagation")
    assert child.propagate is True
    # 沿 parent 链最终能到 jiuzhang 根（不依赖中间 PlaceHolder 是否已被物化）
    cursor: logging.Logger | None = child
    while cursor is not None and cursor.name != "jiuzhang":
        cursor = cursor.parent
    assert cursor is not None
    assert cursor.name == "jiuzhang"
