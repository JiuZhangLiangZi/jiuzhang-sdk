"""Local molecular-docking application helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from jiuzhang.local.applications._deps import optional_dependency

__all__ = [
    "DockingGraph",
    "clique_search",
    "clique_shrink",
    "is_clique",
    "load_phat_graph",
    "load_tace_as_graph",
    "postselect_subgraphs",
    "subgraph_density_summary",
]


@dataclass(frozen=True)
class DockingGraph:
    """Graph data used by local molecular-docking demos."""

    name: str
    adjacency: npt.NDArray[np.float64]
    _backend_data: Any


def load_tace_as_graph() -> DockingGraph:
    """Load the bundled TACE-AS molecular-docking graph.

    Returns:
        Docking graph with adjacency matrix and private sample source.
    """
    data = optional_dependency("strawberryfields.apps.data")
    raw = data.TaceAs()
    return DockingGraph(
        name="TACE-AS", adjacency=np.asarray(raw.adj, dtype=np.float64), _backend_data=raw
    )


def load_phat_graph() -> DockingGraph:
    """Load the bundled PHat graph for clique-search comparison.

    Returns:
        Docking graph with adjacency matrix and private sample source.
    """
    data = optional_dependency("strawberryfields.apps.data")
    raw = data.PHat()
    return DockingGraph(
        name="PHat", adjacency=np.asarray(raw.adj, dtype=np.float64), _backend_data=raw
    )


def postselect_subgraphs(
    dataset: DockingGraph, min_photons: int, max_photons: int
) -> list[list[int]]:
    """Post-select local samples and convert them into graph node lists.

    Args:
        dataset: Docking graph returned by ``load_tace_as_graph`` or
            ``load_phat_graph``.
        min_photons: Minimum total photon count retained.
        max_photons: Maximum total photon count retained.

    Returns:
        Candidate subgraphs represented as node-index lists.
    """
    nx = optional_dependency("networkx")
    sample = optional_dependency("strawberryfields.apps.sample")
    graph = nx.Graph(dataset.adjacency)
    postselected = sample.postselect(dataset._backend_data, min_photons, max_photons)
    return [list(map(int, nodes)) for nodes in sample.to_subgraphs(postselected, graph)]


def subgraph_density_summary(
    adjacency: Any,
    subgraphs: list[list[int]],
    *,
    seed: int | None = None,
) -> dict[str, float]:
    """Compare sampled subgraph density with uniform random subgraphs.

    Args:
        adjacency: Square graph adjacency matrix.
        subgraphs: Candidate subgraphs represented as node-index lists.
        seed: Optional random seed for reproducible uniform baselines.

    Returns:
        Mean sampled density and mean uniform density.
    """
    nx = optional_dependency("networkx")
    rng = np.random.default_rng(seed)
    graph = nx.Graph(np.asarray(adjacency, dtype=np.float64))
    node_count = len(graph.nodes)
    sampled_density = []
    uniform_density = []
    for nodes in subgraphs:
        size = len(nodes)
        uniform = list(rng.choice(np.arange(node_count), size, replace=False))
        sampled_density.append(float(nx.density(graph.subgraph(nodes))))
        uniform_density.append(float(nx.density(graph.subgraph(uniform))))
    return {
        "sampled_mean_density": float(np.mean(sampled_density)),
        "uniform_mean_density": float(np.mean(uniform_density)),
    }


def clique_shrink(adjacency: Any, nodes: list[int]) -> list[int]:
    """Shrink a candidate subgraph into a clique.

    Args:
        adjacency: Square graph adjacency matrix.
        nodes: Candidate node indices.

    Returns:
        Node list after greedy clique shrinking.
    """
    nx = optional_dependency("networkx")
    clique = optional_dependency("strawberryfields.apps.clique")
    return list(map(int, clique.shrink(nodes, nx.Graph(np.asarray(adjacency, dtype=np.float64)))))


def clique_search(adjacency: Any, nodes: list[int], iterations: int = 10) -> list[int]:
    """Expand a clique candidate with local search.

    Args:
        adjacency: Square graph adjacency matrix.
        nodes: Starting clique node indices.
        iterations: Number of local-search iterations.

    Returns:
        Node list after local clique search.
    """
    nx = optional_dependency("networkx")
    clique = optional_dependency("strawberryfields.apps.clique")
    return list(
        map(
            int, clique.search(nodes, nx.Graph(np.asarray(adjacency, dtype=np.float64)), iterations)
        )
    )


def is_clique(adjacency: Any, nodes: list[int]) -> bool:
    """Check whether selected nodes form a clique.

    Args:
        adjacency: Square graph adjacency matrix.
        nodes: Candidate node indices.

    Returns:
        ``True`` when the selected subgraph is a clique.
    """
    nx = optional_dependency("networkx")
    clique = optional_dependency("strawberryfields.apps.clique")
    graph = nx.Graph(np.asarray(adjacency, dtype=np.float64))
    return bool(clique.is_clique(graph.subgraph(nodes)))
