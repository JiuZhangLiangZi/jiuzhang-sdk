from __future__ import annotations

import httpx
import pytest

from jiuzhang.cloud import HttpTransport
from jiuzhang.exceptions import InternalError, PermissionDeniedError


def test_http_transport_injects_api_key_header() -> None:
    captured_headers: httpx.Headers | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_headers
        captured_headers = request.headers
        return httpx.Response(200, json={"ok": True})

    transport = HttpTransport(
        "http://mock.local",
        token="PQ-3f2c2a3b0f7a4a2ab1cdb0b7d2f1a9c4",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert transport.get("/hello") == {"ok": True}
    assert captured_headers is not None
    assert captured_headers["x-jiuzhang-api-key"].startswith("PQ-")
    assert "authorization" not in captured_headers


def test_http_transport_maps_auth_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"code": 403})

    transport = HttpTransport(
        "http://mock.local",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(PermissionDeniedError):
        transport.get("/secure")


def test_http_transport_rejects_non_object_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[1, 2, 3])

    transport = HttpTransport(
        "http://mock.local",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(InternalError):
        transport.get("/bad")


def test_http_transport_maps_business_error_code() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"code": 1001, "message": "认证失败", "data": None})

    transport = HttpTransport(
        "http://mock.local",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(PermissionDeniedError) as exc_info:
        transport.get("/secure")
    assert exc_info.value.code == "1001"
