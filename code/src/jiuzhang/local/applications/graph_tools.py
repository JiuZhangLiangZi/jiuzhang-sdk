"""Shared graph helpers for local application workflows."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.local.applications._deps import optional_dependency

__all__ = ["draw_graph", "graph_density", "to_networkx_graph"]


def to_networkx_graph(adjacency: Any) -> Any:
    """Convert an adjacency matrix to a NetworkX graph.

    Args:
        adjacency: Square graph adjacency matrix.

    Returns:
        A NetworkX graph object built from the adjacency matrix.
    """
    nx = optional_dependency("networkx")
    matrix = _adjacency_matrix(adjacency)
    return nx.Graph(matrix)


def graph_density(adjacency: Any, nodes: Any | None = None) -> float:
    """Compute graph density for a full graph or a selected subgraph.

    Args:
        adjacency: Square graph adjacency matrix.
        nodes: Optional node indices used to form a subgraph before computing
            density.

    Returns:
        Density value in ``[0, 1]``.
    """
    nx = optional_dependency("networkx")
    graph = to_networkx_graph(adjacency)
    if nodes is not None:
        graph = graph.subgraph([int(node) for node in nodes])
    return float(nx.density(graph))


def draw_graph(
    adjacency: Any,
    nodes: Any | None = None,
    *,
    title: str | None = None,
    ax: Any | None = None,
) -> Any:
    """Draw a graph with Matplotlib and NetworkX.

    Args:
        adjacency: Square graph adjacency matrix.
        nodes: Optional highlighted node indices.
        title: Optional chart title.
        ax: Optional Matplotlib axes object. When omitted, a new axes object is
            created.

    Returns:
        The Matplotlib axes object containing the graph.
    """
    nx = optional_dependency("networkx")
    plt = optional_dependency("matplotlib.pyplot")
    graph = to_networkx_graph(adjacency)
    axes = ax if ax is not None else plt.subplots(figsize=(6, 4))[1]
    selected = set() if nodes is None else {int(node) for node in nodes}
    colors = ["#4f7cff" if node in selected else "#b8c4d8" for node in graph.nodes]
    pos = nx.spring_layout(graph, seed=7)
    nx.draw_networkx(
        graph,
        pos=pos,
        ax=axes,
        node_color=colors,
        edge_color="#9aa8bd",
        with_labels=True,
        font_size=8,
        node_size=420,
    )
    axes.set_axis_off()
    if title is not None:
        axes.set_title(title)
    return axes


def _adjacency_matrix(adjacency: Any) -> npt.NDArray[np.float64]:
    arr = np.asarray(adjacency, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[0] != arr.shape[1]:
        raise InvalidParameterError("adjacency must be a non-empty square matrix")
    return arr
