"""
Backend-resolution layer.

Selects the CognoDB backend or the embedded demo backend based on
configuration, then re-exports the query surface the routes consume. Also
houses the criticality scoring — deliberately simple and graph-derived:

    share  = total_affected / (all_components - 1)   # fraction of the system
    HIGH   if share >= 15%   # one failure endangers >= 15% of all components
    MEDIUM if share >= 10%
    LOW    otherwise

(Thresholds calibrated so the seeded system yields a clear spread — a handful
of HIGH shared databases/infra, frequent MEDIUM single-owner services, and a
long LOW tail of leaf components.)

Both numbers come straight from graph traversal, nothing is hand-assigned.
"""

from __future__ import annotations

import logging

from . import cognodb_graph, demo_graph
from .cognodb_graph import DatabaseUnavailable  # re-exported for routes

log = logging.getLogger(__name__)

_active = None
_mode = "demo"
_startup_error: str | None = None

HIGH_THRESHOLD = 0.15
MEDIUM_THRESHOLD = 0.10


def init_app(config: dict) -> None:
    global _active, _mode, _startup_error
    requested = config.get("GRAPH_BACKEND", "auto")
    uri = config.get("COGNODB_URI", "")
    user = config.get("COGNODB_USERNAME", "cognodb")
    password = config.get("COGNODB_PASSWORD", "")

    use_demo = requested == "demo" or (requested == "auto" and not uri)

    if use_demo:
        _active = demo_graph
        _mode = "demo"
        _startup_error = None
        log.info("Graph backend: embedded demo dataset (set COGNODB_URI for CognoDB)")
        return

    cognodb_graph.init(uri, user, password)
    _active = cognodb_graph
    _mode = "cognodb"
    try:
        cognodb_graph.verify()
        _startup_error = None
        log.info("Graph backend: CognoDB at %s", uri)
    except DatabaseUnavailable as exc:
        # Stay in cognodb mode: /health reports the outage and queries answer
        # 503 gracefully instead of the app refusing to boot.
        _startup_error = str(exc)
        log.warning("CognoDB unreachable at startup: %s", exc)


def mode() -> str:
    return _mode


# --- Query surface ------------------------------------------------------------


def health() -> dict:
    status = _active.health()
    status["mode"] = _mode
    if _startup_error:
        status["startup_warning"] = _startup_error
    return status


def stats() -> dict:
    return _active.stats()


def search(q: str = "", type_label: str = "", limit: int = 25) -> list[dict]:
    return _active.search(q=q, type_label=type_label, limit=limit)


def get_component(node_id: str) -> dict | None:
    return _active.get_component(node_id)


def dependencies_bundle(node_id: str) -> dict:
    return {
        "component": _active.get_component(node_id),
        "dependencies": _active.direct_dependencies(node_id),
        "dependents": _active.direct_dependents(node_id),
    }


def impact(node_id: str) -> dict:
    return _active.impact(node_id)


def shortest_path(from_id: str, to_id: str) -> dict:
    result = _active.shortest_path(from_id, to_id)
    result["from"] = _active.get_component(from_id)
    result["to"] = _active.get_component(to_id)
    return result


def _criticality_tier(total: int, components_total: int) -> dict:
    share = total / max(components_total - 1, 1)
    if share >= HIGH_THRESHOLD:
        tier = "HIGH"
    elif share >= MEDIUM_THRESHOLD:
        tier = "MEDIUM"
    else:
        tier = "LOW"
    return {"tier": tier, "share": round(share, 3)}


def criticality(node_id: str) -> dict:
    counts = _active.criticality_counts(node_id)
    total = counts["direct"] + counts["indirect"]
    components_total = len(_active.ids())
    scored = _criticality_tier(total, components_total)
    return {
        **counts,
        "total": total,
        **scored,
        "thresholds": {"high": HIGH_THRESHOLD, "medium": MEDIUM_THRESHOLD},
    }


def leaderboard(limit: int = 10) -> list[dict]:
    rows = _active.leaderboard(limit)
    components_total = len(_active.ids())
    for row in rows:
        row.update(_criticality_tier(row["reach"], components_total))
    return rows
