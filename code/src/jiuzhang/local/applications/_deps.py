"""Private dependency loading for local application workflows."""

from __future__ import annotations

import warnings
from typing import Any

from jiuzhang.exceptions import InvalidParameterError


def optional_dependency(module_name: str) -> Any:
    """Import a local application dependency with a user-facing SDK error."""
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*")
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            return __import__(module_name, fromlist=["*"])
    except ImportError as exc:
        raise InvalidParameterError(
            "本地应用功能依赖缺失，请重新安装最新版：pip install --upgrade jiuzhang-sdk"
        ) from exc
