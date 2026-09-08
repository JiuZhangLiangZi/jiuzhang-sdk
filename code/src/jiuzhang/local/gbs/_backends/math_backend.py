"""Private adapter for local GBS math backends."""

from __future__ import annotations

from typing import Any

from jiuzhang.local.gbs._validation import optional_dependency


def backend() -> Any:
    """Return the optional math backend module."""
    return optional_dependency("thewalrus")


def samples_backend() -> Any:
    """Return the optional sampling backend module."""
    return optional_dependency("thewalrus.samples")
