"""基于 httpx 的九章云平台 HTTP 传输层。"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from jiuzhang.exceptions import (
    InternalError,
    InvalidParameterError,
    JiuzhangError,
    PermissionDeniedError,
    TimeoutError,
)


class HttpTransport:
    """封装九章云平台 HTTP JSON 调用。"""

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        """构造 HTTP 传输层。

        Args:
            base_url: 九章云平台根地址，例如 ``http://127.0.0.1:18081``。
            token: 可选 API Key，传输层会写入认证 header。
            timeout: 请求超时时间，单位秒。
            client: 测试注入用 httpx.Client。
        """
        self.base_url = base_url.rstrip("/") + "/"
        self.token = token
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        """关闭底层 HTTP client。"""
        if self._owns_client:
            self._client.close()

    def get(self, path: str) -> dict[str, Any]:
        """发送 GET JSON 请求。"""
        return self._request("GET", path)

    def post(
        self,
        path: str,
        json: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """发送 POST JSON 请求。"""
        return self._request("POST", path, json=json, extra_headers=headers)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = urljoin(self.base_url, path.lstrip("/"))
        headers = self._headers()
        if extra_headers:
            headers.update(extra_headers)
        try:
            response = self._client.request(method, url, json=json, headers=headers)
        except httpx.TimeoutException as exc:
            raise TimeoutError("平台 HTTP 请求超时", details={"url": url}) from exc
        except httpx.HTTPError as exc:
            raise InternalError(
                "平台 HTTP 请求失败", details={"url": url, "error": str(exc)}
            ) from exc

        if response.status_code in (401, 403):
            raise PermissionDeniedError(
                "平台认证失败或权限不足",
                details={"url": url, "status_code": response.status_code},
            )
        if response.status_code >= 400:
            raise InternalError(
                "平台 HTTP 返回错误状态码",
                details={"url": url, "status_code": response.status_code, "body": response.text},
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise InternalError("平台 HTTP 返回非 JSON 响应", details={"url": url}) from exc
        if not isinstance(payload, dict):
            raise InternalError("平台 HTTP JSON 响应必须为对象", details={"url": url})
        self._raise_for_business_error(payload, url=url)
        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.token:
            headers["X-Jiuzhang-API-Key"] = self.token
        return headers

    @staticmethod
    def _raise_for_business_error(payload: dict[str, Any], *, url: str) -> None:
        code = payload.get("code")
        if code in (None, 0, "0"):
            return
        message = payload.get("message") or payload.get("msg") or "九章云平台业务错误"
        details = {
            "url": url,
            "code": code,
            "data": payload.get("data"),
            "details": payload.get("details"),
        }
        exc_cls: type[JiuzhangError]
        if code in (1001, "1001"):
            exc_cls = PermissionDeniedError
        elif code in (1002, "1002", 2001, "2001"):
            exc_cls = InvalidParameterError
        elif code in (3001, "3001"):
            exc_cls = TimeoutError
        else:
            exc_cls = InternalError
        raise exc_cls(str(message), code=str(code), details=details)
