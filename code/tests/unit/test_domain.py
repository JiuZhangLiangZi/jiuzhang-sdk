"""TokenManager 单元测试。"""

from __future__ import annotations

import pytest

from jiuzhang import TokenManager
from jiuzhang.exceptions import TokenInvalidError


class TestTokenManagerValidate:
    """TokenManager.validate_token 行为。"""

    def test_valid_pq_api_key_returns_ok(self) -> None:
        tm = TokenManager(token_id="PQ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4")
        result = tm.validate_token()
        assert result["code"] == "OK"
        assert result["data"]["format"] == "VALID"
        assert "PQ-" in result["data"]["tokenId"]

    def test_valid_jz_api_key_returns_ok(self) -> None:
        tm = TokenManager(token_id="JZ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4")
        assert tm.validate_token()["code"] == "OK"

    def test_valid_jiuzhang_sk_api_key_returns_ok(self) -> None:
        tm = TokenManager(token_id="jiuzhang_sk_3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4")
        assert tm.validate_token()["code"] == "OK"

    def test_missing_prefix_raises(self) -> None:
        tm = TokenManager(token_id="XX-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4")
        with pytest.raises(TokenInvalidError, match="格式非法"):
            tm.validate_token()

    def test_too_short_raises(self) -> None:
        tm = TokenManager(token_id="JZ-abc")
        with pytest.raises(TokenInvalidError):
            tm.validate_token()

    def test_uppercase_hex_raises(self) -> None:
        tm = TokenManager(token_id="JZ-3F2C2A3B0F7A4A2AB1CDB0B7D2F1A9C4")
        with pytest.raises(TokenInvalidError):
            tm.validate_token()

    def test_non_hex_chars_raises(self) -> None:
        tm = TokenManager(token_id="JZ-zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
        with pytest.raises(TokenInvalidError):
            tm.validate_token()

    def test_empty_string_raises(self) -> None:
        tm = TokenManager(token_id="")
        with pytest.raises(TokenInvalidError):
            tm.validate_token()


class TestTokenManagerMasked:
    """TokenManager.masked_token 行为。"""

    def test_masked_token_format(self) -> None:
        tm = TokenManager(token_id="PQ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4")
        assert tm.masked_token == "PQ-3f2c***a9c4"

    def test_short_token_masked(self) -> None:
        tm = TokenManager(token_id="short")
        assert tm.masked_token == "***"
