"""Vercel serverless function handler for Flask API."""

import os
import sys

# Add server/src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server", "src"))

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import route blueprints
from routes.reports import reports_bp
from routes.requests import requests_bp


def create_app() -> Flask:
    """Application factory for Flask app."""
    application = Flask(__name__)

    application.config["JSON_SORT_KEYS"] = False

    # Enable CORS - same origin on Vercel, but allow dev/preview URLs
    CORS(
        application,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
    )

    # Register blueprints
    application.register_blueprint(reports_bp, url_prefix="/api")
    application.register_blueprint(requests_bp, url_prefix="/api")

    # Health check endpoint
    @application.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        from services.tableau import get_tableau_service

        service = get_tableau_service()
        return jsonify(
            {
                "status": "ok",
                "service": "tableau-report-tracker",
                "tableauConfigured": service.is_configured(),
            }
        )

    # Error handlers
    @application.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @application.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    return application


# Create the Flask app - Vercel will use this as WSGI application
app = create_app()
