"""九章云平台 HTTP API 返回结构的轻量类型声明。"""

from __future__ import annotations

from typing import Any, TypedDict


class CloudResponse(TypedDict):
    """九章云平台统一响应。"""

    code: int
    message: str
    timestamp: str
    data: dict[str, Any] | None


class RuntimeEstimate(TypedDict, total=False):
    """复杂度估计响应核心字段。"""

    classical_cost_time_s: float
    classical_cost_time_us: int
    tianyan_response: dict[str, Any]
    neff: float
    estimatedChi: float
    plotData: dict[str, Any]


class TaskResult(TypedDict, total=False):
    """光量子优越性任务结果核心字段。"""

    taskId: str
    taskStatus: int
    mtValue: int
    sampleCount: int
    maxSamplePhotonCount: int
    sampleCostTime: float
    inputModeCount: int
    outputModeCount: int
    resultMapPoints: dict[str, Any]
