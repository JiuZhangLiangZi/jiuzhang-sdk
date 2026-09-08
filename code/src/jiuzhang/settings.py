"""Environment-based settings for the jiuzhang SDK."""

from __future__ import annotations

import os
from dataclasses import dataclass

from jiuzhang.auth import TokenManager
from jiuzhang.exceptions import InvalidParameterError

__all__ = ["Settings"]


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from the notebook or process environment."""

    api_key: str
    base_url: str = "http://127.0.0.1:18081"
    default_project_id: str | None = None
    default_quantum_computer_id: str = "PH_QC_04"
    request_timeout: float = 30.0
    poll_interval: float = 0.5

    @classmethod
    def from_env(cls) -> Settings:
        """Load SDK settings from environment variables."""
        api_key = os.getenv("JIUZHANG_API_KEY", "").strip()
        base_url = os.getenv("JIUZHANG_BASE_URL", cls.base_url).strip()
        if not api_key:
            raise InvalidParameterError("environment variable JIUZHANG_API_KEY is required")

        return cls(
            api_key=api_key,
            base_url=base_url,
            default_project_id=os.getenv("JIUZHANG_PROJECT_ID", "").strip() or None,
            default_quantum_computer_id=os.getenv(
                "JIUZHANG_QUANTUM_COMPUTER_ID",
                "PH_QC_04",
            ).strip()
            or "PH_QC_04",
            request_timeout=_read_float_env("JIUZHANG_REQUEST_TIMEOUT", 30.0),
            poll_interval=_read_float_env("JIUZHANG_POLL_INTERVAL", 0.5),
        )

    def masked_api_key(self) -> str:
        """Return the API key with the middle portion hidden."""
        return TokenManager(self.api_key).masked_token


def _read_float_env(name: str, default: float) -> float:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise InvalidParameterError(f"environment variable {name} must be numeric") from exc
    if parsed <= 0:
        raise InvalidParameterError(f"environment variable {name} must be greater than 0")
    return parsed
