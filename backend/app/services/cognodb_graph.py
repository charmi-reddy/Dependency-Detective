"""
CognoDB graph backend — official Neo4j Python driver over Bolt.

Every query executed here lives in ``services/cypher.py`` and is fully
parameterised ($parameters); no user input is ever interpolated into Cypher.
Transient and permanent driver failures surface as ``DatabaseUnavailable`` so
routes can answer 503 with a clean message instead of a stack trace.
"""

from __future__ import annotations

import time

from neo4j import GraphDatabase, exceptions as neo4j_exceptions

from . import cypher


class DatabaseUnavailable(Exception):
    """Raised when CognoDB cannot be reached or queried."""


_driver = None


def init(uri: str, username: str, password: str) -> None:
    global _driver
    _driver = GraphDatabase.driver(
        uri,
        auth=(username, password),
        max_connection_lifetime=300,
        connection_timeout=10,
    )


def close() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def verify() -> None:
    """Fail fast at startup if credentials/URI are wrong."""
    try:
        _driver.verify_connectivity()
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError, OSError) as exc:
        raise DatabaseUnavailable(f"Cannot connect to CognoDB: {exc}") from exc


def _run(query: str, **params):
    try:
        with _driver.session() as session:
            return session.run(query, params).data()
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError, OSError) as exc:
        raise DatabaseUnavailable(f"CognoDB query failed: {exc}") from exc


# --- Public query functions (mirror demo_graph.py) -----------------------------


def health() -> dict:
    start = time.perf_counter()
    _run(cypher.HEALTH_CHECK)
    latency_ms = round((time.perf_counter() - start) * 1000, 1)
    return {"status": "ok", "backend": "cognodb", "latency_ms": latency_ms}


def stats() -> dict:
    nodes = {row["type"]: row["count"] for row in _run(cypher.NODE_COUNT_BY_TYPE)}
    rels = {row["type"]: row["count"] for row in _run(cypher.REL_COUNT_BY_TYPE)}
    teams = _run(cypher.TEAM_COUNT)[0]["count"]
    return {"nodes": nodes, "relationships": rels, "teams": teams}


def search(q: str = "", type_label: str = "", limit: int = 25) -> list[dict]:
    return _run(cypher.SEARCH_COMPONENTS, q=q or "", typeLabel=type_label or "",
                limit=limit)


def get_component(node_id: str) -> dict | None:
    rows = _run(cypher.GET_COMPONENT, id=node_id)
    return rows[0] if rows else None


def direct_dependencies(node_id: str) -> list[dict]:
    return _run(cypher.DIRECT_DEPENDENCIES, id=node_id)


def direct_dependents(node_id: str) -> list[dict]:
    return _run(cypher.DIRECT_DEPENDENTS, id=node_id)


def impact(node_id: str) -> dict:
    """Multi-hop traversal (>=2 hops guaranteed by the data) — see IMPACT_ANALYSIS."""
    rows = _run(cypher.IMPACT_ANALYSIS, id=node_id)
    root = get_component(node_id)  # caller guarantees existence
    direct = [r for r in rows if r["depth"] == 1]
    indirect = [r for r in rows if r["depth"] > 1]
    max_depth = max((r["depth"] for r in rows), default=0)
    return {
        "root": root,
        "direct": direct,
        "indirect": indirect,
        "total": len(rows),
        "max_depth": max_depth,
    }


def shortest_path(from_id: str, to_id: str, max_paths: int = 6) -> dict:
    rows = _run(cypher.DEPENDENCY_PATHS, fromId=from_id, toId=to_id, maxPaths=max_paths)
    paths = [{"nodes": row["nodes"], "rels": row["rels"], "hops": len(row["rels"])}
             for row in rows]
    return {"found": bool(paths), "paths": paths,
            "hops": paths[0]["hops"] if paths else 0}


def criticality_counts(node_id: str) -> dict:
    rows = _run(cypher.CRITICALITY, id=node_id)
    return rows[0] if rows else {"direct": 0, "indirect": 0}


def leaderboard(limit: int = 10) -> list[dict]:
    return _run(cypher.CRITICALITY_LEADERBOARD, limit=limit)


def ids() -> set[str]:
    rows = _run(cypher.SEARCH_COMPONENTS, q="", typeLabel="", limit=1000)
    return {row["component"]["id"] for row in rows}
