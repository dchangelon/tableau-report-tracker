"""Reports API routes for fetching Tableau workbooks."""

from flask import Blueprint, jsonify, request, current_app
from ..services.tableau import get_tableau_service

reports_bp = Blueprint("reports", __name__)


def _get_service():
    """Get Tableau service, using mock in testing mode."""
    force_mock = current_app.config.get("TESTING", False)
    return get_tableau_service(force_mock=force_mock)


@reports_bp.route("/reports", methods=["GET"])
def get_reports():
    """
    Fetch all reports/workbooks from Tableau.

    Query params:
        q: Search query to filter by name
        project: Project path to filter by

    Returns:
        JSON with data array and total count
    """
    try:
        search_query = request.args.get("q", "").strip() or None
        project_path = request.args.get("project", "").strip() or None

        service = _get_service()
        workbooks = service.fetch_workbooks(
            search_query=search_query, project_path=project_path
        )

        return jsonify(
            {
                "success": True,
                "data": workbooks,
                "total": len(workbooks),
                "filters": {
                    "query": search_query,
                    "project": project_path,
                },
            }
        )
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to fetch reports: {str(e)}"}), 500


@reports_bp.route("/reports/<report_id>", methods=["GET"])
def get_report(report_id: str):
    """
    Fetch a single report/workbook by ID.

    Args:
        report_id: The Tableau workbook ID

    Returns:
        JSON with report data
    """
    try:
        service = _get_service()
        workbook = service.get_workbook_by_id(report_id)

        if not workbook:
            return jsonify({"success": False, "error": "Report not found"}), 404

        return jsonify({"success": True, "data": workbook})
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to fetch report: {str(e)}"}), 500


@reports_bp.route("/reports/projects", methods=["GET"])
def get_project_paths():
    """
    Get unique project paths for filter dropdown.

    Returns:
        JSON with list of project paths
    """
    try:
        service = _get_service()
        paths = service.get_unique_project_paths()

        return jsonify({"success": True, "data": paths})
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to fetch projects: {str(e)}"}), 500
