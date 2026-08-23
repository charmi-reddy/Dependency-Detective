"""
In-memory graph backend used when no CognoDB instance is configured.

It loads the canonical dataset from ``database.seed_data`` into a NetworkX
MultiDiGraph and implements exactly the same query functions as
``cognodb_graph.py`` (same signatures, same response shapes), so the rest of
the application — routes, frontend, tests — cannot tell the difference.

The point of this backend is offline development and CI tests. Production
queries run as the parameterised Cypher found in ``services/cypher.py``;
each function's docstring names the equivalent Cypher constant.
"""

from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx

# Make the repository's top-level ``database`` package importable regardless of
# the current working directory (backend/ differs from repo root).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from database import seed_data  # noqa: E402

_G = None


def _graph() -> nx.MultiDiGraph:
    global _G
    if _G is None:
        g = nx.MultiDiGraph()
        for node_id, label in seed_data.LABELS.items():
            props = dict(seed_data.ALL_PROPERTIES[node_id])
            props["id"] = node_id
            g.add_node(node_id, labels=(label), **props)
        for src, rtype, dst in seed_data.RELATIONSHIPS:
            # key=rtype keeps READS_FROM/WRITES_TO parallel edges distinct.
            g.add_edge(src, dst, key=rtype, type=rtype)
        _G = g
    return _G


def _summary(node_id: str) -> dict:
    node = _graph().nodes[node_id]
    return {"id": node_id, "name": node.get("name", node_id), "type": node.get("labels")}


def _component(node_id: str) -> dict:
    """Node properties only — matches CognoDB's ``n{.*}`` serialisation exactly."""
    return {k: v for k, v in _graph().nodes[node_id].items() if k != "labels"}


def health() -> dict:
    g = _graph()
    return {"status": "ok", "backend": "demo", "nodes": g.number_of_nodes(),
            "relationships": g.number_of_edges()}


def stats() -> dict:
    g = _graph()
    nodes: dict[str, int] = {}
    for _, data in g.nodes(data=True):
        label = data.get("labels")
        nodes[label] = nodes.get(label, 0) + 1
    rels: dict[str, int] = {}
    for _, _, data in g.edges(data=True):
        t = data["type"]
        rels[t] = rels.get(t, 0) + 1
    return {
        "nodes": dict(sorted(nodes.items(), key=lambda kv: -kv[1])),
        "relationships": dict(sorted(rels.items(), key=lambda kv: -kv[1])),
        "teams": nodes.get("Team", 0),
    }


def search(q: str = "", type_label: str = "", limit: int = 25) -> list[dict]:
    g = _graph()
    out = []
    for node_id, data in g.nodes(data=True):
        if data.get("labels") == "Team":
            continue
        if type_label and data.get("labels") != type_label:
            continue
        if q and q.lower() not in data.get("name", "").lower():
            continue
        out.append({"component": _component(node_id), "type": data.get("labels")})
    out.sort(key=lambda r: r["component"]["name"])
    return out[:limit]


def get_component(node_id: str) -> dict | None:
    g = _graph()
    if node_id not in g:
        return None
    owner = None
    for _, dst, data in g.out_edges(node_id, data=True):
        if data["type"] == "OWNED_BY":
            owner = g.nodes[dst].get("name")
    return {"component": _component(node_id), "type": g.nodes[node_id].get("labels"),
            "owner": owner}


def direct_dependencies(node_id: str) -> list[dict]:
    g = _graph()
    rows = []
    for _, dst, data in g.out_edges(node_id, data=True):
        if data["type"] == "OWNED_BY":
            continue
        rows.append({"rel": data["type"], "component": _component(dst),
                     "type": g.nodes[dst].get("labels")})
    rows.sort(key=lambda r: (r["rel"], r["component"]["name"]))
    return rows


def direct_dependents(node_id: str) -> list[dict]:
    g = _graph()
    rows = []
    for src, _, data in g.in_edges(node_id, data=True):
        rows.append({"rel": data["type"], "component": _component(src),
                     "type": g.nodes[src].get("labels")})
    rows.sort(key=lambda r: r["component"]["name"])
    return rows


def _dep_only_view(g: nx.MultiDiGraph) -> nx.DiGraph:
    """Dependency-only simple digraph (drops OWNED_BY and parallel edges)."""
    keep = [(u, v) for u, v, d in g.edges(data=True) if d["type"] in seed_data.DEPENDENCY_TYPES]
    view = nx.DiGraph()
    view.add_nodes_from(g.nodes)
    view.add_edges_from(keep)
    return view


def impact(node_id: str) -> dict:
    """Equivalent Cypher: ``IMPACT_ANALYSIS`` (multi-hop, 1..6)."""
    g = _graph()
    simple = _dep_only_view(g)
    affected_nodes = nx.ancestors(simple, node_id)  # nodes with a path TO root
    entries = []
    for other in affected_nodes:
        chain_ids = nx.shortest_path(simple, other, node_id)
        depth = len(chain_ids) - 1
        rels = []
        for u, v in zip(chain_ids, chain_ids[1:]):
            # Deterministic pick among parallel edges (e.g. READS_FROM vs WRITES_TO).
            types = sorted(d["type"] for d in g.get_edge_data(u, v).values()
                           if d["type"] in seed_data.DEPENDENCY_TYPES)
            rels.append(types[0])
        entries.append({
            "component": _component(other),
            "type": g.nodes[other].get("labels"),
            "depth": depth,
            "chain_nodes": [_summary(cid) for cid in chain_ids],
            "chain_rels": rels,
        })
    entries.sort(key=lambda e: (e["depth"], e["component"]["name"]))
    return {
        "root": {"component": _component(node_id), "type": g.nodes[node_id].get("labels")},
        "direct": [e for e in entries if e["depth"] == 1],
        "indirect": [e for e in entries if e["depth"] > 1],
        "total": len(entries),
        "max_depth": seed_data_max_depth(entries),
    }


def seed_data_max_depth(entries: list[dict]) -> int:
    return max((e["depth"] for e in entries), default=0)


def shortest_path(from_id: str, to_id: str, max_paths: int = 6) -> dict:
    """Equivalent Cypher: ``DEPENDENCY_PATHS`` (all chains <= 8 hops, shortest first)."""
    g = _graph()
    simple = _dep_only_view(g)
    try:
        chains = sorted(nx.all_simple_paths(simple, from_id, to_id, cutoff=8), key=len)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        chains = []
    paths = []
    for chain_ids in chains[:max_paths]:
        rels = []
        for u, v in zip(chain_ids, chain_ids[1:]):
            types = sorted(d["type"] for d in g.get_edge_data(u, v).values()
                           if d["type"] in seed_data.DEPENDENCY_TYPES)
            rels.append(types[0])
        paths.append({"nodes": [_summary(cid) for cid in chain_ids],
                      "rels": rels, "hops": len(rels)})
    return {"found": bool(paths), "paths": paths,
            "hops": paths[0]["hops"] if paths else 0}


def criticality_counts(node_id: str) -> dict:
    """Equivalent Cypher: ``CRITICALITY``."""
    g = _graph()
    simple = _dep_only_view(g)
    direct = sum(1 for u in simple.predecessors(node_id) if g.nodes[u].get("labels") != "Team")
    indirect = 0
    for other in nx.ancestors(simple, node_id):
        if other == node_id:
            continue
        if nx.shortest_path_length(simple, other, node_id) >= 2:
            indirect += 1
    return {"direct": direct, "indirect": indirect}


def leaderboard(limit: int = 10) -> list[dict]:
    """Equivalent Cypher: ``CRITICALITY_LEADERBOARD``."""
    g = _graph()
    simple = _dep_only_view(g)
    rows = []
    for node_id, data in g.nodes(data=True):
        if data.get("labels") == "Team":
            continue
        reach = len(nx.ancestors(simple, node_id))
        rows.append({"component": _component(node_id), "type": data.get("labels"),
                     "reach": reach})
    rows.sort(key=lambda r: (-r["reach"], r["component"]["name"]))
    return rows[:limit]


def ids() -> set[str]:
    return set(_graph().nodes)
