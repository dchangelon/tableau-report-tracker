"""Trello API service for creating and managing change request cards."""

import os
import re
from typing import Optional
import requests
from functools import lru_cache

TRELLO_API_BASE = "https://api.trello.com/1"


class TrelloService:
    """Service for interacting with Trello API."""

    def __init__(self):
        """Initialize Trello service with credentials from environment."""
        self.api_key = os.getenv("TRELLO_API_KEY")
        self.token = os.getenv("TRELLO_TOKEN")
        self.board_name = os.getenv("TRELLO_BOARD_NAME", "The Report Report")
        self.list_name = os.getenv("TRELLO_LIST_NAME", "Change Request Queue")
        self._board_id: Optional[str] = None
        self._list_ids: dict[str, str] = {}
        self._label_ids: dict[str, str] = {}

    def is_configured(self) -> bool:
        """Check if Trello credentials are configured."""
        return bool(self.api_key and self.token)

    def _get_auth_params(self) -> dict:
        """Get authentication parameters for API requests."""
        if not self.is_configured():
            raise ValueError("Trello credentials not configured")
        return {"key": self.api_key, "token": self.token}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        timeout: int = 30,
    ) -> dict:
        """Make an authenticated request to Trello API."""
        url = f"{TRELLO_API_BASE}{endpoint}"
        all_params = {**self._get_auth_params(), **(params or {})}

        response = requests.request(
            method=method,
            url=url,
            params=all_params,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    def _get_board_id(self) -> str:
        """Get or create the board for change requests."""
        if self._board_id:
            return self._board_id

        # Try to find existing board
        boards = self._make_request("GET", "/members/me/boards", {"fields": "name"})
        for board in boards:
            if board["name"] == self.board_name:
                self._board_id = board["id"]
                return self._board_id

        # Create new board
        result = self._make_request(
            "POST",
            "/boards",
            {"name": self.board_name, "defaultLists": "false"},
        )
        self._board_id = result["id"]

        # Create default lists
        self._create_default_lists()
        self._create_default_labels()

        return self._board_id

    def _create_default_lists(self) -> None:
        """Create default lists for the board following the workflow progression."""
        board_id = self._board_id
        # Workflow: Change Request Queue --> Reviewing and Planning --> In Progress --> Pending Review --> Completed
        # Plus On Hold for paused requests
        lists_to_create = [
            "Change Request Queue",
            "Reviewing and Planning",
            "In Progress",
            "Pending Review",
            "Completed",
            "On Hold",
        ]

        for i, list_name in enumerate(lists_to_create):
            result = self._make_request(
                "POST",
                "/lists",
                {"name": list_name, "idBoard": board_id, "pos": i + 1},
            )
            self._list_ids[list_name.lower().replace(" ", "_")] = result["id"]

    def _create_default_labels(self) -> None:
        """Create default labels for request types and priorities."""
        board_id = self._board_id

        # Request type labels
        type_labels = {
            "issue": {"name": "Issue", "color": "red"},
            "enhancement": {"name": "Enhancement", "color": "green"},
            "other": {"name": "Other", "color": "purple"},
        }

        # Priority labels
        priority_labels = {
            "high": {"name": "High Priority", "color": "red"},
            "medium": {"name": "Medium Priority", "color": "yellow"},
            "low": {"name": "Low Priority", "color": "blue"},
        }

        for key, label in {**type_labels, **priority_labels}.items():
            result = self._make_request(
                "POST",
                "/labels",
                {"name": label["name"], "color": label["color"], "idBoard": board_id},
            )
            self._label_ids[key] = result["id"]

    def _get_list_id(self, list_name: str) -> str:
        """Get the ID of a list by name, creating if needed."""
        list_key = list_name.lower().replace(" ", "_")
        if list_key in self._list_ids:
            return self._list_ids[list_key]

        board_id = self._get_board_id()

        # Fetch lists from board
        lists = self._make_request("GET", f"/boards/{board_id}/lists", {"fields": "name"})
        for lst in lists:
            key = lst["name"].lower().replace(" ", "_")
            self._list_ids[key] = lst["id"]
            if key == list_key:
                return lst["id"]

        # Create list if not found
        result = self._make_request(
            "POST",
            "/lists",
            {"name": list_name, "idBoard": board_id},
        )
        self._list_ids[list_key] = result["id"]
        return result["id"]

    def _get_label_ids(self, request_type: str, priority: str) -> list[str]:
        """Get label IDs for a request type and priority."""
        if not self._label_ids:
            board_id = self._get_board_id()
            labels = self._make_request("GET", f"/boards/{board_id}/labels")
            for label in labels:
                name_lower = label["name"].lower().replace(" ", "_").replace("_priority", "")
                self._label_ids[name_lower] = label["id"]

        label_ids = []
        if request_type in self._label_ids:
            label_ids.append(self._label_ids[request_type])
        if priority in self._label_ids:
            label_ids.append(self._label_ids[priority])

        return label_ids

    def create_change_request(
        self,
        title: str,
        description: str,
        report_id: str,
        report_name: str,
        request_type: str,
        priority: str,
        requester_email: str,
    ) -> dict:
        """
        Create a Trello card for a change request.

        Args:
            title: The title of the request
            description: Detailed description of the change
            report_id: The Tableau report ID
            report_name: The name of the report
            request_type: Type of request (bug, enhancement, data_issue, other)
            priority: Priority level (low, medium, high)
            requester_email: Email of the person submitting the request

        Returns:
            Dictionary with card details including id and url
        """
        list_id = self._get_list_id(self.list_name)
        label_ids = self._get_label_ids(request_type, priority)

        # Build description with metadata (email stored for filtering)
        full_description = f"""## Request Details

{description}

---

**Requester:** {requester_email}
**Report:** {report_name}
**Report ID:** {report_id}
**Type:** {request_type.replace('_', ' ').title()}
**Priority:** {priority.title()}
"""

        params = {
            "idList": list_id,
            "name": title,
            "desc": full_description,
            "pos": "top",
        }

        if label_ids:
            params["idLabels"] = ",".join(label_ids)

        result = self._make_request("POST", "/cards", params)

        return {
            "id": result["id"],
            "url": result["shortUrl"],
            "name": result["name"],
        }

    def ensure_workflow_lists_exist(self) -> dict[str, str]:
        """
        Ensure all workflow lists exist on the board.

        Returns:
            Dictionary mapping list names to their IDs
        """
        board_id = self._get_board_id()
        required_lists = [
            "Change Request Queue",
            "Reviewing and Planning",
            "In Progress",
            "Pending Review",
            "Completed",
            "On Hold",
        ]

        # Fetch existing lists
        existing = self._make_request("GET", f"/boards/{board_id}/lists", {"fields": "name"})
        existing_names = {lst["name"]: lst["id"] for lst in existing}

        # Create any missing lists
        for i, list_name in enumerate(required_lists):
            if list_name not in existing_names:
                result = self._make_request(
                    "POST",
                    "/lists",
                    {"name": list_name, "idBoard": board_id, "pos": i + 1},
                )
                existing_names[list_name] = result["id"]

            # Cache the list ID
            list_key = list_name.lower().replace(" ", "_")
            self._list_ids[list_key] = existing_names[list_name]

        return existing_names

    def get_cards_by_requester(self, requester_email: str) -> list[dict]:
        """
        Fetch all cards from the board that were created by a specific requester.

        Args:
            requester_email: The email to filter cards by

        Returns:
            List of card dictionaries with status and progress info
        """
        board_id = self._get_board_id()

        # Ensure lists exist and get their mapping
        list_map = self.ensure_workflow_lists_exist()
        list_id_to_name = {v: k for k, v in list_map.items()}

        # Fetch all cards from the board
        cards = self._make_request(
            "GET",
            f"/boards/{board_id}/cards",
            {"fields": "id,name,desc,idList,shortUrl,dateLastActivity"},
        )

        # Filter cards by requester email in description
        user_cards = []
        for card in cards:
            desc = card.get("desc", "")
            # Check if this card belongs to the requester
            if f"**Requester:** {requester_email}" in desc:
                # Get checklist progress
                progress = self._get_card_progress(card["id"])

                # Determine status from list name
                list_id = card.get("idList", "")
                status = list_id_to_name.get(list_id, "Unknown")

                user_cards.append({
                    "id": card["id"],
                    "title": card["name"],
                    "status": status,
                    "trelloUrl": card.get("shortUrl", ""),
                    "updatedAt": card.get("dateLastActivity", ""),
                    "checklistProgress": progress,
                })

        return user_cards

    def get_card_details(self, card_id: str) -> dict:
        """
        Fetch detailed information about a single card including checklists.

        Args:
            card_id: The Trello card ID

        Returns:
            Dictionary with card details and checklist items
        """
        # Fetch card with all fields
        card = self._make_request(
            "GET",
            f"/cards/{card_id}",
            {"fields": "id,name,desc,idList,shortUrl,dateLastActivity"},
        )

        # Get list name for status
        board_id = self._get_board_id()
        list_map = self.ensure_workflow_lists_exist()
        list_id_to_name = {v: k for k, v in list_map.items()}
        status = list_id_to_name.get(card.get("idList", ""), "Unknown")

        # Fetch checklists for the card
        checklists = self._make_request("GET", f"/cards/{card_id}/checklists")

        # Parse checklist items
        checklist_items = []
        for checklist in checklists:
            for item in checklist.get("checkItems", []):
                checklist_items.append({
                    "id": item["id"],
                    "name": item["name"],
                    "completed": item["state"] == "complete",
                })

        # Calculate progress
        total = len(checklist_items)
        completed = sum(1 for item in checklist_items if item["completed"])
        progress = round((completed / total) * 100) if total > 0 else 0

        # Parse metadata from description
        desc = card.get("desc", "")
        metadata = self._parse_card_description(desc)

        return {
            "id": card["id"],
            "title": card["name"],
            "description": metadata.get("description", ""),
            "status": status,
            "trelloUrl": card.get("shortUrl", ""),
            "updatedAt": card.get("dateLastActivity", ""),
            "reportName": metadata.get("report_name", ""),
            "reportId": metadata.get("report_id", ""),
            "requestType": metadata.get("request_type", ""),
            "priority": metadata.get("priority", ""),
            "requesterEmail": metadata.get("requester_email", ""),
            "checklistProgress": progress,
            "checklistItems": checklist_items,
        }

    def _get_card_progress(self, card_id: str) -> int:
        """Get the checklist completion percentage for a card."""
        try:
            checklists = self._make_request("GET", f"/cards/{card_id}/checklists")
            total = 0
            completed = 0
            for checklist in checklists:
                for item in checklist.get("checkItems", []):
                    total += 1
                    if item["state"] == "complete":
                        completed += 1
            return round((completed / total) * 100) if total > 0 else 0
        except Exception:
            return 0

    def _parse_card_description(self, desc: str) -> dict:
        """Parse metadata from the card description."""
        result = {}

        # Extract the user description (before the ---)
        if "---" in desc:
            parts = desc.split("---", 1)
            # Remove "## Request Details" header
            user_desc = parts[0].replace("## Request Details", "").strip()
            result["description"] = user_desc
            metadata_section = parts[1] if len(parts) > 1 else ""
        else:
            result["description"] = desc
            metadata_section = ""

        # Parse metadata fields
        import re
        patterns = {
            "requester_email": r"\*\*Requester:\*\*\s*(.+)",
            "report_name": r"\*\*Report:\*\*\s*(.+)",
            "report_id": r"\*\*Report ID:\*\*\s*(.+)",
            "request_type": r"\*\*Type:\*\*\s*(.+)",
            "priority": r"\*\*Priority:\*\*\s*(.+)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, metadata_section)
            if match:
                result[key] = match.group(1).strip()

        return result


# Singleton instance
_trello_service: Optional[TrelloService] = None


def get_trello_service(force_mock: bool = False) -> TrelloService:
    """Get the Trello service instance."""
    global _trello_service

    if force_mock:
        return MockTrelloService()

    if _trello_service is None:
        _trello_service = TrelloService()

    return _trello_service


class MockTrelloService(TrelloService):
    """Mock Trello service for testing."""

    def __init__(self):
        """Initialize mock service."""
        super().__init__()
        self._mock_cards: list[dict] = []
        self._card_counter = 0

    def is_configured(self) -> bool:
        """Always configured in mock mode."""
        return True

    def create_change_request(
        self,
        title: str,
        description: str,
        report_id: str,
        report_name: str,
        request_type: str,
        priority: str,
        requester_email: str,
    ) -> dict:
        """Create a mock Trello card."""
        self._card_counter += 1
        card = {
            "id": f"mock-card-{self._card_counter}",
            "url": f"https://trello.com/c/mock{self._card_counter}",
            "name": title,
            "requester_email": requester_email,
            "report_id": report_id,
            "report_name": report_name,
            "request_type": request_type,
            "priority": priority,
            "description": description,
            "status": "Change Request Queue",
        }
        self._mock_cards.append(card)
        return card

    def ensure_workflow_lists_exist(self) -> dict[str, str]:
        """Return mock list mapping."""
        return {
            "Change Request Queue": "mock-list-1",
            "Reviewing and Planning": "mock-list-2",
            "In Progress": "mock-list-3",
            "Pending Review": "mock-list-4",
            "Completed": "mock-list-5",
            "On Hold": "mock-list-6",
        }

    def get_cards_by_requester(self, requester_email: str) -> list[dict]:
        """Return mock cards filtered by requester email."""
        return [
            {
                "id": card["id"],
                "title": card["name"],
                "status": card.get("status", "Change Request Queue"),
                "trelloUrl": card["url"],
                "updatedAt": "2026-01-27T12:00:00Z",
                "checklistProgress": 40,
            }
            for card in self._mock_cards
            if card.get("requester_email") == requester_email
        ]

    def get_card_details(self, card_id: str) -> dict:
        """Return mock card details."""
        for card in self._mock_cards:
            if card["id"] == card_id:
                return {
                    "id": card["id"],
                    "title": card["name"],
                    "description": card.get("description", ""),
                    "status": card.get("status", "Change Request Queue"),
                    "trelloUrl": card["url"],
                    "updatedAt": "2026-01-27T12:00:00Z",
                    "reportName": card.get("report_name", ""),
                    "reportId": card.get("report_id", ""),
                    "requestType": card.get("request_type", ""),
                    "priority": card.get("priority", ""),
                    "requesterEmail": card.get("requester_email", ""),
                    "checklistProgress": 40,
                    "checklistItems": [
                        {"id": "1", "name": "Request reviewed", "completed": True},
                        {"id": "2", "name": "Changes implemented", "completed": True},
                        {"id": "3", "name": "Testing completed", "completed": False},
                        {"id": "4", "name": "Deployed to production", "completed": False},
                        {"id": "5", "name": "Requester notified", "completed": False},
                    ],
                }
        return None
