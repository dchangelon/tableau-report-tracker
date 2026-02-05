"""Trello API service for creating and managing change request cards."""

import os
import re
from typing import Optional
import requests

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

        boards = self._make_request("GET", "/members/me/boards", {"fields": "name"})
        for board in boards:
            if board["name"] == self.board_name:
                self._board_id = board["id"]
                return self._board_id

        result = self._make_request(
            "POST",
            "/boards",
            {"name": self.board_name, "defaultLists": "false"},
        )
        self._board_id = result["id"]
        self._create_default_lists()
        self._create_default_labels()
        return self._board_id

    def _create_default_lists(self) -> None:
        """Create default lists for the board."""
        board_id = self._board_id
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

        type_labels = {
            "issue": {"name": "Issue", "color": "red"},
            "enhancement": {"name": "Enhancement", "color": "green"},
            "other": {"name": "Other", "color": "purple"},
        }

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
        lists = self._make_request("GET", f"/boards/{board_id}/lists", {"fields": "name"})
        for lst in lists:
            key = lst["name"].lower().replace(" ", "_")
            self._list_ids[key] = lst["id"]
            if key == list_key:
                return lst["id"]

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
        """Create a Trello card for a change request."""
        list_id = self._get_list_id(self.list_name)
        label_ids = self._get_label_ids(request_type, priority)

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
        self._add_workflow_checklist(result["id"])

        return {
            "id": result["id"],
            "url": result["shortUrl"],
            "name": result["name"],
        }

    def _add_workflow_checklist(self, card_id: str) -> None:
        """Add a standard workflow checklist to a card."""
        checklist = self._make_request(
            "POST",
            "/checklists",
            {"idCard": card_id, "name": "Workflow"},
        )

        items = [
            "Request reviewed",
            "Changes implemented",
            "Testing completed",
            "Deployed to production",
            "Requester notified",
        ]

        for item in items:
            self._make_request(
                "POST",
                f"/checklists/{checklist['id']}/checkItems",
                {"name": item},
            )

    def ensure_workflow_lists_exist(self) -> dict[str, str]:
        """Ensure all workflow lists exist on the board."""
        board_id = self._get_board_id()
        required_lists = [
            "Change Request Queue",
            "Reviewing and Planning",
            "In Progress",
            "Pending Review",
            "Completed",
            "On Hold",
        ]

        existing = self._make_request("GET", f"/boards/{board_id}/lists", {"fields": "name"})
        existing_names = {lst["name"]: lst["id"] for lst in existing}

        for i, list_name in enumerate(required_lists):
            if list_name not in existing_names:
                result = self._make_request(
                    "POST",
                    "/lists",
                    {"name": list_name, "idBoard": board_id, "pos": i + 1},
                )
                existing_names[list_name] = result["id"]

            list_key = list_name.lower().replace(" ", "_")
            self._list_ids[list_key] = existing_names[list_name]

        return existing_names

    def get_cards_by_requester(self, requester_email: str) -> list[dict]:
        """Fetch all cards from the board that were created by a specific requester."""
        board_id = self._get_board_id()
        list_map = self.ensure_workflow_lists_exist()
        list_id_to_name = {v: k for k, v in list_map.items()}

        cards = self._make_request(
            "GET",
            f"/boards/{board_id}/cards",
            {"fields": "id,name,desc,idList,shortUrl,dateLastActivity"},
        )

        user_cards = []
        for card in cards:
            desc = card.get("desc", "")
            if f"**Requester:** {requester_email}" in desc:
                progress = self._get_card_progress(card["id"])
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
        """Fetch detailed information about a single card including checklists."""
        card = self._make_request(
            "GET",
            f"/cards/{card_id}",
            {"fields": "id,name,desc,idList,shortUrl,dateLastActivity"},
        )

        board_id = self._get_board_id()
        list_map = self.ensure_workflow_lists_exist()
        list_id_to_name = {v: k for k, v in list_map.items()}
        status = list_id_to_name.get(card.get("idList", ""), "Unknown")

        checklists = self._make_request("GET", f"/cards/{card_id}/checklists")

        checklist_items = []
        for checklist in checklists:
            for item in checklist.get("checkItems", []):
                checklist_items.append({
                    "id": item["id"],
                    "name": item["name"],
                    "completed": item["state"] == "complete",
                })

        total = len(checklist_items)
        completed = sum(1 for item in checklist_items if item["completed"])
        progress = round((completed / total) * 100) if total > 0 else 0

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

        if "---" in desc:
            parts = desc.split("---", 1)
            user_desc = parts[0].replace("## Request Details", "").strip()
            result["description"] = user_desc
            metadata_section = parts[1] if len(parts) > 1 else ""
        else:
            result["description"] = desc
            metadata_section = ""

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


_trello_service: Optional[TrelloService] = None


def get_trello_service(force_mock: bool = False) -> TrelloService:
    """Get the Trello service instance."""
    global _trello_service

    if force_mock:
        raise ValueError("Mock service not available in production")

    if _trello_service is None:
        _trello_service = TrelloService()

    return _trello_service
