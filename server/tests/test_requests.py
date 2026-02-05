"""Tests for the requests API endpoints and Trello service."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.app import create_app
from src.services.trello import MockTrelloService


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(testing=True)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestCreateRequestEndpoint:
    """Tests for POST /api/requests endpoint."""

    def get_valid_payload(self):
        """Return a valid request payload."""
        return {
            "report_id": "wb-001",
            "report_name": "Sales Dashboard",
            "title": "Fix the chart display issue",
            "description": "The bar chart is not rendering correctly when filtering by date range.",
            "request_type": "issue",
            "priority": "high",
            "requester_email": "user@company.com",
        }

    def test_create_request_success(self, client):
        """Should create a request successfully with valid data."""
        payload = self.get_valid_payload()
        response = client.post("/api/requests", json=payload)

        assert response.status_code == 201

        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert "id" in data["data"]
        assert "title" in data["data"]
        assert "trelloUrl" in data["data"]
        assert data["message"] == "Change request created successfully"

    def test_create_request_returns_json(self, client):
        """Create request should return JSON content type."""
        payload = self.get_valid_payload()
        response = client.post("/api/requests", json=payload)
        assert response.content_type == "application/json"

    def test_create_request_missing_body(self, client):
        """Should return 400 when request body is missing."""
        response = client.post("/api/requests", json=None)
        assert response.status_code == 400

        data = response.get_json()
        assert data["success"] is False
        assert "required" in data["error"].lower()

    def test_create_request_missing_required_fields(self, client):
        """Should return 400 when required fields are missing."""
        # Missing title and description
        payload = {
            "report_id": "wb-001",
            "report_name": "Sales Dashboard",
        }
        response = client.post("/api/requests", json=payload)
        assert response.status_code == 400

        data = response.get_json()
        assert data["success"] is False
        assert "missing" in data["error"].lower()

    def test_create_request_invalid_request_type(self, client):
        """Should return 400 for invalid request_type."""
        payload = self.get_valid_payload()
        payload["request_type"] = "invalid_type"

        response = client.post("/api/requests", json=payload)
        assert response.status_code == 400

        data = response.get_json()
        assert data["success"] is False
        assert "request_type" in data["error"].lower()

    def test_create_request_invalid_priority(self, client):
        """Should return 400 for invalid priority."""
        payload = self.get_valid_payload()
        payload["priority"] = "urgent"  # Not a valid priority

        response = client.post("/api/requests", json=payload)
        assert response.status_code == 400

        data = response.get_json()
        assert data["success"] is False
        assert "priority" in data["error"].lower()

    def test_create_request_title_too_short(self, client):
        """Should return 400 when title is too short."""
        payload = self.get_valid_payload()
        payload["title"] = "Fix"  # Less than 5 characters

        response = client.post("/api/requests", json=payload)
        assert response.status_code == 400

        data = response.get_json()
        assert data["success"] is False
        assert "title" in data["error"].lower()

    def test_create_request_description_too_short(self, client):
        """Should return 400 when description is too short."""
        payload = self.get_valid_payload()
        payload["description"] = "Short"  # Less than 10 characters

        response = client.post("/api/requests", json=payload)
        assert response.status_code == 400

        data = response.get_json()
        assert data["success"] is False
        assert "description" in data["error"].lower()

    def test_create_request_all_request_types(self, client):
        """Should accept all valid request types."""
        valid_types = ["issue", "enhancement", "other"]

        for request_type in valid_types:
            payload = self.get_valid_payload()
            payload["request_type"] = request_type

            response = client.post("/api/requests", json=payload)
            assert response.status_code == 201, f"Failed for type: {request_type}"

    def test_create_request_all_priorities(self, client):
        """Should accept all valid priorities."""
        valid_priorities = ["low", "medium", "high"]

        for priority in valid_priorities:
            payload = self.get_valid_payload()
            payload["priority"] = priority

            response = client.post("/api/requests", json=payload)
            assert response.status_code == 201, f"Failed for priority: {priority}"

    def test_create_request_trims_whitespace(self, client):
        """Should trim whitespace from title and description."""
        payload = self.get_valid_payload()
        payload["title"] = "  Padded title with spaces  "
        payload["description"] = "  This description has whitespace padding  "

        response = client.post("/api/requests", json=payload)
        assert response.status_code == 201


class TestGetRequestsEndpoint:
    """Tests for GET /api/requests endpoint."""

    def test_get_requests_requires_email(self, client):
        """Should return 400 when email query parameter is missing."""
        response = client.get("/api/requests")
        assert response.status_code == 400

        data = response.get_json()
        assert data["success"] is False
        assert "email" in data["error"].lower()

    def test_get_requests_validates_email_format(self, client):
        """Should return 400 for invalid email format."""
        response = client.get("/api/requests?email=invalid-email")
        assert response.status_code == 400

        data = response.get_json()
        assert data["success"] is False
        assert "email" in data["error"].lower()

    def test_get_requests_success(self, client):
        """Should return list of requests for valid email."""
        response = client.get("/api/requests?email=test@company.com")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "total" in data

    def test_get_requests_returns_json(self, client):
        """Get requests should return JSON content type."""
        response = client.get("/api/requests?email=test@company.com")
        assert response.content_type == "application/json"


class TestGetRequestDetailsEndpoint:
    """Tests for GET /api/requests/:id endpoint."""

    def test_get_request_details_not_found(self, client):
        """Should return 404 when request is not found."""
        response = client.get("/api/requests/nonexistent-id")
        assert response.status_code == 404

        data = response.get_json()
        assert data["success"] is False

    def test_get_request_details_returns_json(self, client):
        """Get request details should return JSON content type."""
        response = client.get("/api/requests/any-id")
        assert response.content_type == "application/json"


class TestMockTrelloService:
    """Tests for MockTrelloService directly."""

    def test_is_configured(self):
        """Mock service should always be configured."""
        service = MockTrelloService()
        assert service.is_configured() is True

    def test_create_change_request(self):
        """Should create a mock card with correct structure."""
        service = MockTrelloService()
        result = service.create_change_request(
            title="Test Request",
            description="Test description for the request",
            report_id="wb-001",
            report_name="Test Report",
            request_type="issue",
            priority="high",
            requester_email="test@company.com",
        )

        assert "id" in result
        assert "url" in result
        assert "name" in result
        assert result["name"] == "Test Request"
        assert "trello.com" in result["url"]

    def test_create_multiple_requests_unique_ids(self):
        """Each request should have a unique ID."""
        service = MockTrelloService()

        card1 = service.create_change_request(
            title="First Request",
            description="First description",
            report_id="wb-001",
            report_name="Report 1",
            request_type="issue",
            priority="low",
            requester_email="user1@company.com",
        )

        card2 = service.create_change_request(
            title="Second Request",
            description="Second description",
            report_id="wb-002",
            report_name="Report 2",
            request_type="enhancement",
            priority="medium",
            requester_email="user2@company.com",
        )

        assert card1["id"] != card2["id"]
        assert card1["url"] != card2["url"]

    def test_get_cards_by_requester(self):
        """Should return cards filtered by requester email."""
        service = MockTrelloService()

        # Create cards for different requesters
        service.create_change_request(
            title="Request 1",
            description="Description 1",
            report_id="wb-001",
            report_name="Report 1",
            request_type="issue",
            priority="high",
            requester_email="user1@company.com",
        )

        service.create_change_request(
            title="Request 2",
            description="Description 2",
            report_id="wb-002",
            report_name="Report 2",
            request_type="enhancement",
            priority="low",
            requester_email="user2@company.com",
        )

        # Get cards for user1
        user1_cards = service.get_cards_by_requester("user1@company.com")
        assert len(user1_cards) == 1
        assert user1_cards[0]["title"] == "Request 1"

        # Get cards for user2
        user2_cards = service.get_cards_by_requester("user2@company.com")
        assert len(user2_cards) == 1
        assert user2_cards[0]["title"] == "Request 2"

    def test_get_card_details(self):
        """Should return detailed card information."""
        service = MockTrelloService()

        card = service.create_change_request(
            title="Test Request",
            description="Test description",
            report_id="wb-001",
            report_name="Test Report",
            request_type="issue",
            priority="high",
            requester_email="test@company.com",
        )

        details = service.get_card_details(card["id"])
        assert details is not None
        assert details["title"] == "Test Request"
        assert "checklistItems" in details
        assert "checklistProgress" in details
        assert "status" in details

    def test_get_card_details_not_found(self):
        """Should return None for non-existent card."""
        service = MockTrelloService()
        details = service.get_card_details("nonexistent-id")
        assert details is None

    def test_ensure_workflow_lists_exist(self):
        """Should return mapping of all workflow lists."""
        service = MockTrelloService()
        lists = service.ensure_workflow_lists_exist()

        expected_lists = [
            "Change Request Queue",
            "Review and Planning",
            "In Progress",
            "Pending Review",
            "Completed",
            "On Hold",
        ]

        for list_name in expected_lists:
            assert list_name in lists, f"Missing list: {list_name}"


class TestAPIContract:
    """
    Contract tests to ensure API response matches frontend TypeScript types.

    These fields must match: client/src/types/index.ts -> CreateRequestResponse
    """

    CREATE_RESPONSE_FIELDS = {"id", "title", "trelloUrl"}

    def test_create_request_response_matches_frontend_types(self, client):
        """API response must match frontend CreateRequestResponse type."""
        payload = {
            "report_id": "wb-001",
            "report_name": "Sales Dashboard",
            "title": "Test request for contract test",
            "description": "This is a description for testing the API contract",
            "request_type": "issue",
            "priority": "medium",
            "requester_email": "test@company.com",
        }

        response = client.post("/api/requests", json=payload)
        assert response.status_code == 201

        data = response.get_json()["data"]

        actual_fields = set(data.keys())
        missing = self.CREATE_RESPONSE_FIELDS - actual_fields
        extra = actual_fields - self.CREATE_RESPONSE_FIELDS

        assert not missing, f"API missing fields expected by frontend: {missing}"
        assert not extra, f"API has extra fields not in frontend types: {extra}"

    def test_response_field_naming_convention(self, client):
        """Response fields should use camelCase to match TypeScript conventions."""
        payload = {
            "report_id": "wb-001",
            "report_name": "Sales Dashboard",
            "title": "Test request",
            "description": "Test description for naming test",
            "request_type": "issue",
            "priority": "low",
            "requester_email": "test@company.com",
        }

        response = client.post("/api/requests", json=payload)
        data = response.get_json()["data"]

        # trelloUrl should be camelCase (which it is)
        assert "trelloUrl" in data, "trelloUrl should use camelCase"
        assert "trello_url" not in data, "Should not have snake_case trello_url"
