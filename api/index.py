"""Vercel serverless function handler for Flask API."""

import os
import re
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import local services
from .services.tableau import TableauService, get_tableau_service
from .services.trello import TrelloService, get_trello_service

# Valid values for request fields
VALID_REQUEST_TYPES = {"issue", "enhancement", "other"}
VALID_PRIORITIES = {"low", "medium", "high"}
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def create_app() -> Flask:
    """Application factory for Flask app."""
    application = Flask(__name__)
    application.config["JSON_SORT_KEYS"] = False

    CORS(
        application,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
    )

    # Health check endpoint
    @application.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        try:
            service = TableauService()
            return jsonify({
                "status": "ok",
                "service": "tableau-report-tracker",
                "tableauConfigured": service.is_configured(),
            })
        except Exception as e:
            return jsonify({
                "status": "ok",
                "service": "tableau-report-tracker",
                "tableauConfigured": False,
                "error": str(e),
            })

    # Reports endpoints
    @application.route("/api/reports", methods=["GET"])
    def get_reports():
        """Fetch all reports/workbooks from Tableau."""
        try:
            search_query = request.args.get("q", "").strip() or None
            project_path = request.args.get("project", "").strip() or None

            service = get_tableau_service()
            workbooks = service.fetch_workbooks(
                search_query=search_query, project_path=project_path
            )

            return jsonify({
                "success": True,
                "data": workbooks,
                "total": len(workbooks),
                "filters": {
                    "query": search_query,
                    "project": project_path,
                },
            })
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to fetch reports: {str(e)}"}), 500

    @application.route("/api/reports/<report_id>", methods=["GET"])
    def get_report(report_id: str):
        """Fetch a single report/workbook by ID."""
        try:
            service = get_tableau_service()
            workbook = service.get_workbook_by_id(report_id)

            if not workbook:
                return jsonify({"success": False, "error": "Report not found"}), 404

            return jsonify({"success": True, "data": workbook})
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to fetch report: {str(e)}"}), 500

    @application.route("/api/reports/projects", methods=["GET"])
    def get_project_paths():
        """Get unique project paths for filter dropdown."""
        try:
            service = get_tableau_service()
            paths = service.get_unique_project_paths()
            return jsonify({"success": True, "data": paths})
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to fetch projects: {str(e)}"}), 500

    # Requests endpoints
    @application.route("/api/requests", methods=["GET"])
    def get_requests():
        """Get all change requests for a specific requester."""
        try:
            email = request.args.get("email")

            if not email:
                return jsonify({
                    "success": False,
                    "error": "Email query parameter is required"
                }), 400

            if not EMAIL_PATTERN.match(email):
                return jsonify({
                    "success": False,
                    "error": "Invalid email format"
                }), 400

            service = get_trello_service()

            if not service.is_configured():
                return jsonify({
                    "success": False,
                    "error": "Trello is not configured"
                }), 503

            cards = service.get_cards_by_requester(email)

            return jsonify({
                "success": True,
                "data": cards,
                "total": len(cards),
            })

        except Exception as e:
            return jsonify({"success": False, "error": "Failed to fetch requests"}), 500

    @application.route("/api/requests/<card_id>", methods=["GET"])
    def get_request_details(card_id: str):
        """Get detailed information about a single change request."""
        try:
            if not card_id:
                return jsonify({
                    "success": False,
                    "error": "Card ID is required"
                }), 400

            service = get_trello_service()

            if not service.is_configured():
                return jsonify({
                    "success": False,
                    "error": "Trello is not configured"
                }), 503

            card = service.get_card_details(card_id)

            if not card:
                return jsonify({
                    "success": False,
                    "error": "Request not found"
                }), 404

            return jsonify({
                "success": True,
                "data": card,
            })

        except Exception as e:
            return jsonify({"success": False, "error": "Failed to fetch request details"}), 500

    @application.route("/api/requests", methods=["POST"])
    def create_request():
        """Create a new change request."""
        try:
            data = request.get_json(silent=True)

            if not data:
                return jsonify({"success": False, "error": "Request body is required"}), 400

            required_fields = ["report_id", "report_name", "title", "description", "request_type", "priority", "requester_email"]
            missing = [f for f in required_fields if not data.get(f)]

            if missing:
                return jsonify({
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing)}"
                }), 400

            if not EMAIL_PATTERN.match(data["requester_email"]):
                return jsonify({
                    "success": False,
                    "error": "Invalid email format"
                }), 400

            if data["request_type"] not in VALID_REQUEST_TYPES:
                return jsonify({
                    "success": False,
                    "error": f"Invalid request_type. Must be one of: {', '.join(VALID_REQUEST_TYPES)}"
                }), 400

            if data["priority"] not in VALID_PRIORITIES:
                return jsonify({
                    "success": False,
                    "error": f"Invalid priority. Must be one of: {', '.join(VALID_PRIORITIES)}"
                }), 400

            if len(data["title"].strip()) < 5:
                return jsonify({
                    "success": False,
                    "error": "Title must be at least 5 characters"
                }), 400

            if len(data["description"].strip()) < 10:
                return jsonify({
                    "success": False,
                    "error": "Description must be at least 10 characters"
                }), 400

            service = get_trello_service()

            if not service.is_configured():
                return jsonify({
                    "success": False,
                    "error": "Trello is not configured. Please set TRELLO_API_KEY and TRELLO_TOKEN."
                }), 503

            card = service.create_change_request(
                title=data["title"].strip(),
                description=data["description"].strip(),
                report_id=data["report_id"],
                report_name=data["report_name"],
                request_type=data["request_type"],
                priority=data["priority"],
                requester_email=data["requester_email"].strip(),
            )

            return jsonify({
                "success": True,
                "data": {
                    "id": card["id"],
                    "title": card["name"],
                    "trelloUrl": card["url"],
                },
                "message": "Change request created successfully"
            }), 201

        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "error": "Failed to create change request"}), 500

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
