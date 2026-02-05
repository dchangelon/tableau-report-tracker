"""Flask application entry point."""

import argparse
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from .routes.reports import reports_bp
from .routes.requests import requests_bp


def create_app(testing: bool = False) -> Flask:
    """
    Application factory for creating Flask app.

    Args:
        testing: If True, use testing configuration

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Configuration
    app.config["TESTING"] = testing
    app.config["JSON_SORT_KEYS"] = False

    # Enable CORS for frontend
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",  # Vite dev server
                    "http://localhost:3000",  # Alternative dev port
                    "https://*.vercel.app",   # Vercel preview deployments
                ],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    # Register blueprints
    app.register_blueprint(reports_bp, url_prefix="/api")
    app.register_blueprint(requests_bp, url_prefix="/api")

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint for monitoring."""
        from .services.tableau import TableauService

        tableau_service = TableauService()

        return jsonify(
            {
                "status": "ok",
                "service": "tableau-report-tracker",
                "tableauConfigured": tableau_service.is_configured(),
            }
        )

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({"success": False, "error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle uncaught exceptions."""
        app.logger.error(f"Unhandled exception: {error}")
        return jsonify({"success": False, "error": "An unexpected error occurred"}), 500

    return app


# For running directly with `python src/app.py`
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tableau Report Tracker API Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    app = create_app()
    app.run(host="0.0.0.0", port=args.port, debug=args.debug)
