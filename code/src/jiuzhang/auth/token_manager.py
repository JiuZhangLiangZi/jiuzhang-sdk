"""TokenManager — API Key 本地格式校验与持有。

当前九章云平台 API Key 真实格式尚未冻结，SDK 暂接受 ``JZ-`` 或 ``PQ-``
前缀 + 32 位十六进制小写字符作为本地占位校验规则，例如::

    JZ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4
    PQ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4

本模块仅做客户端本地格式校验，**不产生任何网络请求**。后续云平台认证规则
确定后，应优先在本模块集中调整 API Key 格式校验与脱敏展示逻辑。
"""

from __future__ import annotations

import re
from typing import Any

from jiuzhang.exceptions import TokenInvalidError
from jiuzhang.result import make_result

__all__ = ["TokenManager"]

_TOKEN_PATTERN = re.compile(r"^((JZ|PQ)-[0-9a-f]{32}|jiuzhang_sk_[0-9a-f]{32})$")


class TokenManager:
    """持有 API Key 并提供本地格式校验。

    Attributes:
        token_id: 调用方传入的 API Key 字符串。

    Examples:
        >>> tm = TokenManager(token_id="PQ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4")
        >>> result = tm.validate_token()
        >>> result["code"]
        'OK'
    """

    def __init__(self, token_id: str) -> None:
        """构造 TokenManager。

        Args:
            token_id: API Key 字符串。本构造函数不做校验，校验在
                :meth:`validate_token` 中执行。
        """
        self.token_id: str = token_id

    @property
    def masked_token(self) -> str:
        """脱敏展示：保留前缀与末 4 位，中间用 ``***`` 替代。

        Examples:
            >>> TokenManager("PQ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4").masked_token
            'PQ-3f2c***a9c4'
        """
        if len(self.token_id) >= 10:
            return self.token_id[:7] + "***" + self.token_id[-4:]
        return "***"

    def validate_token(self) -> dict[str, Any]:
        """对持有的 API Key 做本地格式校验。

        校验规则：

        * 前缀暂定为 ``JZ-`` 或 ``PQ-``
        * 前缀后为 32 位十六进制小写字符
        * 总长度为 35 个字符

        Returns:
            统一返回结构 dict。校验通过时 ``code == "OK"``，
            ``data`` 含 ``tokenId``（脱敏）与 ``format``（``"VALID"``）。

        Raises:
            TokenInvalidError: 格式不符合规则。
        """
        if not _TOKEN_PATTERN.match(self.token_id):
            raise TokenInvalidError(
                "API Key 格式非法：期望 'JZ-' / 'PQ-' + 32 位十六进制小写，"
                "或 'jiuzhang_sk_' + 32 位十六进制小写，"
                f"实际为 {self.masked_token!r}",
                details={"token_masked": self.masked_token},
            )

        return make_result(
            message="token 校验通过",
            data={"tokenId": self.masked_token, "format": "VALID"},
        )
