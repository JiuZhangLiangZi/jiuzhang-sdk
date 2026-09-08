"""Optional dependency loading for local MNIST workflows."""

from __future__ import annotations

from typing import Any

from jiuzhang.exceptions import InvalidParameterError


def optional_dependency(module_name: str, package_name: str | None = None) -> Any:
    """Import an optional dependency with a user-facing SDK error."""
    try:
        return __import__(module_name, fromlist=["*"])
    except ImportError as exc:
        package = package_name or module_name
        raise InvalidParameterError(
            f"本地 MNIST 识别功能依赖缺失，请安装最新版依赖：pip install --upgrade {package}"
        ) from exc
