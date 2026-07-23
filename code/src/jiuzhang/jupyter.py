"""Small Jupyter helpers for jiuzhang cloud notebooks."""

from __future__ import annotations

import html
import importlib
from typing import Any

from jiuzhang.cloud import CloudClient
from jiuzhang.gbs import GBSResult
from jiuzhang.settings import Settings

__all__ = ["display_gbs_result", "get_notebook_client", "show_environment"]


def get_notebook_client() -> CloudClient:
    """Create a CloudClient from notebook environment variables."""
    return CloudClient.from_env()


def show_environment() -> dict[str, str]:
    """Return masked notebook environment information."""
    settings = Settings.from_env()
    return {
        "base_url": settings.base_url,
        "api_key": settings.masked_api_key(),
        "project_id": settings.default_project_id or "",
        "quantum_computer_id": str(settings.default_quantum_computer_id),
        "request_timeout": str(settings.request_timeout),
        "poll_interval": str(settings.poll_interval),
    }


def display_gbs_result(result: GBSResult) -> dict[str, Any]:
    """Display a compact result summary in IPython, or return a dict fallback."""
    summary = {
        "task_id": result.task_id,
        "status": result.status_name,
        "task_name": result.task_name,
        "quantum_computer_id": result.quantum_computer_id,
        "mt": result.mt,
        "sample_count": result.sample_count,
        "download_url": result.download_url,
        "result_map_points": sorted(result.result_map_points.keys()),
    }
    try:
        display_module: Any = importlib.import_module("IPython.display")
    except ImportError:
        return summary

    rows = "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in summary.items()
    )
    html_class: Any = display_module.HTML
    display_func: Any = display_module.display
    display_func(
        html_class(f"<table><caption>GBS Task Result</caption><tbody>{rows}</tbody></table>")
    )
    return summary
