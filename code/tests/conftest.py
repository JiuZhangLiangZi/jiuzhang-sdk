"""pytest 共享配置与 fixtures。"""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_token_id() -> str:
    """提供一个格式合法的示例 API Key，供单元测试复用。"""
    return "PQ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4"
