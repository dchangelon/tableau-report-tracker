"""Requests API routes for managing change requests via Trello."""

import re
from flask import Blueprint, jsonify, request, current_app
from ..services.trello import get_trello_service

requests_bp = Blueprint("requests", __name__)

# Valid values for request fields
VALID_REQUEST_TYPES = {"issue", "enhancement", "other"}
VALID_PRIORITIES = {"low", "medium", "high"}

# Simple email validation pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _get_service():
    """Get Trello service, using mock in testing mode."""
    force_mock = current_app.config.get("TESTING", False)
    return get_trello_service(force_mock=force_mock)


@requests_bp.route("/requests", methods=["GET"])
def get_requests():
    """
    Get all change requests for a specific requester.

    Query parameters:
        email: The requester's email address (required)

    Returns:
        JSON with list of requests including status and progress
    """
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

        service = _get_service()

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
        current_app.logger.error(f"Failed to fetch requests: {e}")
        return jsonify({"success": False, "error": "Failed to fetch requests"}), 500


@requests_bp.route("/requests/<card_id>", methods=["GET"])
def get_request_details(card_id: str):
    """
    Get detailed information about a single change request.

    Path parameters:
        card_id: The Trello card ID

    Returns:
        JSON with card details including checklist items
    """
    try:
        if not card_id:
            return jsonify({
                "success": False,
                "error": "Card ID is required"
            }), 400

        service = _get_service()

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
        current_app.logger.error(f"Failed to fetch request details: {e}")
        return jsonify({"success": False, "error": "Failed to fetch request details"}), 500


@requests_bp.route("/requests", methods=["POST"])
def create_request():
    """
    Create a new change request.

    Expected JSON body:
        {
            "report_id": "string",
            "report_name": "string",
            "title": "string",
            "description": "string",
            "request_type": "bug" | "enhancement" | "data_issue" | "other",
            "priority": "low" | "medium" | "high",
            "requester_email": "string"
        }

    Returns:
        JSON with created request details including Trello card URL
    """
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        # Validate required fields
        required_fields = ["report_id", "report_name", "title", "description", "request_type", "priority", "requester_email"]
        missing = [f for f in required_fields if not data.get(f)]

        if missing:
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing)}"
            }), 400

        # Validate email format
        if not EMAIL_PATTERN.match(data["requester_email"]):
            return jsonify({
                "success": False,
                "error": "Invalid email format"
            }), 400

        # Validate request_type
        if data["request_type"] not in VALID_REQUEST_TYPES:
            return jsonify({
                "success": False,
                "error": f"Invalid request_type. Must be one of: {', '.join(VALID_REQUEST_TYPES)}"
            }), 400

        # Validate priority
        if data["priority"] not in VALID_PRIORITIES:
            return jsonify({
                "success": False,
                "error": f"Invalid priority. Must be one of: {', '.join(VALID_PRIORITIES)}"
            }), 400

        # Validate title length
        if len(data["title"].strip()) < 5:
            return jsonify({
                "success": False,
                "error": "Title must be at least 5 characters"
            }), 400

        # Validate description length
        if len(data["description"].strip()) < 10:
            return jsonify({
                "success": False,
                "error": "Description must be at least 10 characters"
            }), 400

        service = _get_service()

        # Check if Trello is configured
        if not service.is_configured():
            return jsonify({
                "success": False,
                "error": "Trello is not configured. Please set TRELLO_API_KEY and TRELLO_TOKEN."
            }), 503

        # Create the Trello card
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
        current_app.logger.error(f"Failed to create request: {e}")
        return jsonify({"success": False, "error": "Failed to create change request"}), 500
