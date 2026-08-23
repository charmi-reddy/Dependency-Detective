"""
REST API for Dependency Detective.

Contract:
  * success → the payload itself (object or list)
  * failure → {"error": {"code": <machine code>, "message": <human text>}}
              with a meaningful HTTP status (400 / 404 / 503)

All graph access goes through ``services.graph_service``; Cypher lives in
``services/cypher.py`` and is parameterised end-to-end.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services import graph_service
from ..services.graph_service import DatabaseUnavailable

api = Blueprint("api", __name__, url_prefix="/api")

VALID_TYPES = {"Service", "Database", "API", "Library", "Infrastructure"}
MAX_LIMIT = 100


# --- helpers -------------------------------------------------------------------


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def not_found(component_id: str) -> ApiError:
    return ApiError(404, "not_found", f"Component '{component_id}' not found.")


def must_exist(component_id: str) -> dict:
    record = graph_service.get_component(component_id)
    if record is None:
        raise not_found(component_id)
    return record


def parse_limit(raw: str | None, default: int) -> int:
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ApiError(400, "bad_request", "limit must be an integer.")
    if not 1 <= value <= MAX_LIMIT:
        raise ApiError(400, "bad_request", f"limit must be between 1 and {MAX_LIMIT}.")
    return value


@api.errorhandler(ApiError)
def _api_error(err: ApiError):
    return jsonify({"error": {"code": err.code, "message": err.message}}), err.status


@api.errorhandler(DatabaseUnavailable)
def _db_error(err: DatabaseUnavailable):
    return jsonify({"error": {
        "code": "database_unavailable",
        "message": "Unable to connect to the dependency database. Please try again.",
        "detail": str(err),
    }}), 503


# --- routes ---------------------------------------------------------------------


@api.get("/health")
def health():
    try:
        return jsonify(graph_service.health())
    except DatabaseUnavailable as exc:
        return jsonify({"status": "unavailable", "mode": graph_service.mode(),
                        "error": str(exc)}), 503


@api.get("/stats")
def stats():
    return jsonify(graph_service.stats())


@api.get("/components")
def components():
    q = request.args.get("q", "").strip()
    type_label = request.args.get("type", "").strip()
    if type_label and type_label not in VALID_TYPES:
        raise ApiError(400, "bad_request",
                       f"type must be one of {sorted(VALID_TYPES)}.")
    limit = parse_limit(request.args.get("limit"), default=25)
    return jsonify(graph_service.search(q=q, type_label=type_label, limit=limit))


@api.get("/components/<component_id>")
def component(component_id: str):
    return jsonify(must_exist(component_id))


@api.get("/components/<component_id>/dependencies")
def component_dependencies(component_id: str):
    must_exist(component_id)
    return jsonify(graph_service.dependencies_bundle(component_id))


@api.get("/components/<component_id>/impact")
def component_impact(component_id: str):
    must_exist(component_id)
    return jsonify(graph_service.impact(component_id))


@api.get("/components/<component_id>/criticality")
def component_criticality(component_id: str):
    record = must_exist(component_id)
    score = graph_service.criticality(component_id)
    return jsonify({"component": record, **score})


@api.get("/criticality")
def criticality_leaderboard():
    limit = parse_limit(request.args.get("limit"), default=8)
    return jsonify(graph_service.leaderboard(limit))


@api.get("/path")
def dependency_path():
    from_id = request.args.get("from", "").strip()
    to_id = request.args.get("to", "").strip()
    if not from_id or not to_id:
        raise ApiError(400, "bad_request",
                       "Both 'from' and 'to' query parameters are required.")
    if from_id == to_id:
        raise ApiError(400, "bad_request", "'from' and 'to' must be different components.")
    must_exist(from_id)
    must_exist(to_id)
    return jsonify(graph_service.shortest_path(from_id, to_id))
