"""Tests for the reports API endpoints."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.app import create_app
from src.services.tableau import MockTableauService


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(testing=True)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""

    def test_health_returns_ok(self, client):
        """Health endpoint should return status ok."""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "tableau-report-tracker"
        assert "tableauConfigured" in data

    def test_health_returns_json(self, client):
        """Health endpoint should return JSON content type."""
        response = client.get("/api/health")
        assert response.content_type == "application/json"


class TestReportsEndpoint:
    """Tests for /api/reports endpoint."""

    def test_get_reports_returns_list(self, client):
        """Reports endpoint should return list of reports."""
        response = client.get("/api/reports")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "total" in data

    def test_get_reports_has_required_fields(self, client):
        """Each report should have required fields (camelCase)."""
        response = client.get("/api/reports")
        data = response.get_json()

        # Should have mock data since Tableau isn't configured
        assert len(data["data"]) > 0

        report = data["data"][0]
        # API uses camelCase to match frontend TypeScript types
        required_fields = [
            "id",
            "name",
            "projectName",
            "projectPath",
            "ownerName",
            "updatedAt",
            "webUrl",
            "viewCount",
        ]
        for field in required_fields:
            assert field in report, f"Missing field: {field}"

    def test_search_filters_by_name(self, client):
        """Search query should filter reports by name."""
        # Search for 'sales' should return matching reports
        response = client.get("/api/reports?q=sales")
        data = response.get_json()

        assert data["success"] is True
        assert data["filters"]["query"] == "sales"

        # All results should contain 'sales' (case-insensitive)
        for report in data["data"]:
            assert "sales" in report["name"].lower()

    def test_search_no_results(self, client):
        """Search with no matches should return empty list."""
        response = client.get("/api/reports?q=xyznonexistent")
        data = response.get_json()

        assert data["success"] is True
        assert data["data"] == []
        assert data["total"] == 0

    def test_filter_by_project(self, client):
        """Project filter should filter by project path."""
        response = client.get("/api/reports?project=Finance")
        data = response.get_json()

        assert data["success"] is True
        assert data["filters"]["project"] == "Finance"

        # All results should have project starting with 'Finance' (camelCase field)
        for report in data["data"]:
            assert report["projectPath"].startswith("Finance")


class TestReportByIdEndpoint:
    """Tests for /api/reports/<id> endpoint."""

    def test_get_report_by_valid_id(self, client):
        """Should return report when ID exists."""
        # Using mock data ID
        response = client.get("/api/reports/wb-001")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == "wb-001"
        assert data["data"]["name"] == "Sales Dashboard"

    def test_get_report_by_invalid_id(self, client):
        """Should return 404 when ID doesn't exist."""
        response = client.get("/api/reports/invalid-id-123")
        assert response.status_code == 404

        data = response.get_json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()


class TestProjectPathsEndpoint:
    """Tests for /api/reports/projects endpoint."""

    def test_get_project_paths(self, client):
        """Should return list of unique project paths."""
        response = client.get("/api/reports/projects")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

        # Should be sorted
        assert data["data"] == sorted(data["data"])


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_for_unknown_endpoint(self, client):
        """Should return 404 for unknown endpoints."""
        response = client.get("/api/unknown")
        assert response.status_code == 404

        data = response.get_json()
        assert data["success"] is False


class TestAPIContract:
    """
    Contract tests to ensure API response matches frontend TypeScript types.

    These fields must match: client/src/types/index.ts -> Report interface
    If this test fails, update BOTH the backend service AND frontend types.
    """

    # Expected fields from client/src/types/index.ts (camelCase)
    REPORT_FIELDS = {
        "id",
        "name",
        "description",
        "projectName",
        "projectPath",
        "ownerName",
        "ownerEmail",
        "createdAt",
        "updatedAt",
        "webUrl",
        "viewCount",
    }

    REPORT_VIEW_FIELDS = {"id", "name", "contentUrl"}

    def test_reports_list_matches_frontend_types(self, client):
        """API /reports response must match frontend Report type exactly."""
        response = client.get("/api/reports")
        report = response.get_json()["data"][0]

        # Check for exact field match (excluding 'views' which is optional in list)
        actual_fields = set(report.keys()) - {"views"}
        missing = self.REPORT_FIELDS - actual_fields
        extra = actual_fields - self.REPORT_FIELDS

        assert not missing, f"API missing fields expected by frontend: {missing}"
        assert not extra, f"API has extra fields not in frontend types: {extra}"

    def test_report_detail_matches_frontend_types(self, client):
        """API /reports/:id response must match frontend ReportDetailResponse."""
        response = client.get("/api/reports/wb-001")
        report = response.get_json()["data"]

        # Detail endpoint includes views
        actual_fields = set(report.keys()) - {"views"}
        missing = self.REPORT_FIELDS - actual_fields
        extra = actual_fields - self.REPORT_FIELDS

        assert not missing, f"API missing fields expected by frontend: {missing}"
        assert not extra, f"API has extra fields not in frontend types: {extra}"

        # Verify view structure if present
        if report.get("views"):
            view = report["views"][0]
            view_fields = set(view.keys())
            assert view_fields == self.REPORT_VIEW_FIELDS, (
                f"View fields mismatch. Expected: {self.REPORT_VIEW_FIELDS}, Got: {view_fields}"
            )

    def test_field_naming_convention(self, client):
        """All API fields must use camelCase to match frontend TypeScript types."""
        response = client.get("/api/reports")
        report = response.get_json()["data"][0]

        # All multi-word fields should be camelCase, not snake_case
        for field in report.keys():
            assert "_" not in field, (
                f"Field '{field}' uses snake_case. API must use camelCase to match frontend types."
            )


class TestMockTableauService:
    """Tests for MockTableauService directly."""

    def test_is_configured(self):
        """Mock service should always be configured."""
        service = MockTableauService()
        assert service.is_configured() is True

    def test_fetch_workbooks_returns_mock_data(self):
        """Should return mock workbooks."""
        service = MockTableauService()
        workbooks = service.fetch_workbooks()

        assert len(workbooks) == 5
        assert workbooks[0]["name"] == "Sales Dashboard"

    def test_fetch_workbooks_with_search(self):
        """Search should filter mock workbooks."""
        service = MockTableauService()
        workbooks = service.fetch_workbooks(search_query="HR")

        assert len(workbooks) == 1
        assert workbooks[0]["name"] == "HR Analytics"

    def test_get_workbook_by_id(self):
        """Should return correct workbook by ID."""
        service = MockTableauService()
        workbook = service.get_workbook_by_id("wb-002")

        assert workbook is not None
        assert workbook["name"] == "Marketing Metrics"

    def test_get_workbook_by_invalid_id(self):
        """Should return None for invalid ID."""
        service = MockTableauService()
        workbook = service.get_workbook_by_id("invalid")

        assert workbook is None

    def test_get_unique_project_paths(self):
        """Should return unique sorted project paths."""
        service = MockTableauService()
        paths = service.get_unique_project_paths()

        assert isinstance(paths, list)
        assert paths == sorted(paths)
        assert "Finance/Sales" in paths
        assert "Marketing" in paths
