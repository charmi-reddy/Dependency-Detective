"""Application factory for the Dependency Detective API."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from .config import Config
from .routes.api import api
from .services import graph_service

# Built React app (npm run build). If present, Flask serves the whole product
# from one origin — which is exactly how the single-service deploy works.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    graph_service.init_app(app.config)

    app.register_blueprint(api)

    if FRONTEND_DIST.is_dir():

        @app.get("/")
        def spa_index():
            return send_from_directory(FRONTEND_DIST, "index.html")

        @app.get("/<path:path>")
        def spa_assets(path: str):
            if path.startswith("api/"):
                return jsonify({"error": {"code": "not_found",
                                          "message": "Resource not found."}}), 404
            candidate = FRONTEND_DIST / path
            if candidate.is_file():
                return send_from_directory(FRONTEND_DIST, path)
            return send_from_directory(FRONTEND_DIST, "index.html")
    else:

        @app.get("/")
        def index():
            return jsonify({
                "service": "Dependency Detective API",
                "graph_backend": graph_service.mode(),
                "docs": "/api/health for liveness; see README.md for endpoints",
            })

    @app.errorhandler(404)
    def four_oh_four(_):
        return jsonify({"error": {"code": "not_found",
                                  "message": "Resource not found."}}), 404

    @app.errorhandler(500)
    def five_hundred(_):
        return jsonify({"error": {"code": "internal_error",
                                  "message": "Something went wrong. Please try again."}}), 500

    return app
