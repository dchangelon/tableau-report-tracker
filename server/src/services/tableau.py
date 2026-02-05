"""Tableau Server Client service for fetching workbooks and views."""

import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class TableauService:
    """Service for interacting with Tableau Server."""

    def __init__(self):
        """Initialize Tableau connection settings."""
        self.server_url = os.getenv("TABLEAU_SERVER_URL")
        self.site_name = os.getenv("TABLEAU_SITE_NAME", "")
        self.token_name = os.getenv("TABLEAU_TOKEN_NAME")
        self.token_secret = os.getenv("TABLEAU_TOKEN_SECRET")
        self._server = None
        self._auth = None
        self._exceptions = self._load_exceptions()

    def _load_exceptions(self) -> dict:
        """Load exception configuration from config file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "exceptions.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {"excludedWorkbooks": [], "excludedFolders": [], "excludedFoldersExact": [], "excludedPaths": []}

    def _should_exclude(self, workbook_name: str, project_path: str) -> bool:
        """Check if workbook should be excluded based on exception list."""
        # Check workbook name (exact match)
        if workbook_name in self._exceptions.get("excludedWorkbooks", []):
            return True
        # Check if any path segment contains excluded folder pattern (substring match)
        path_parts = project_path.split("/")
        for folder_pattern in self._exceptions.get("excludedFolders", []):
            for segment in path_parts:
                if folder_pattern in segment:
                    return True
        # Check if any path segment exactly matches excluded folder (exact match)
        for folder_exact in self._exceptions.get("excludedFoldersExact", []):
            if folder_exact in path_parts:
                return True
        # Check full path prefix match
        for excluded_path in self._exceptions.get("excludedPaths", []):
            if project_path.startswith(excluded_path):
                return True
        return False

    def is_configured(self) -> bool:
        """Check if Tableau credentials are configured."""
        return all([self.server_url, self.token_name, self.token_secret])

    def _get_connection(self):
        """Create Tableau Server connection objects."""
        import tableauserverclient as TSC

        if not self.is_configured():
            raise ValueError("Tableau credentials not configured. Check .env file.")

        # Bypass any system proxy settings that might interfere
        os.environ["NO_PROXY"] = "*"

        server = TSC.Server(self.server_url, use_server_version=True)
        auth = TSC.PersonalAccessTokenAuth(
            self.token_name, self.token_secret, self.site_name
        )
        return server, auth

    def fetch_workbooks(
        self, search_query: Optional[str] = None, project_path: Optional[str] = None
    ) -> list[dict]:
        """
        Fetch all workbooks from Tableau Server.

        Args:
            search_query: Optional text to filter workbooks by name
            project_path: Optional project path to filter by

        Returns:
            List of workbook dictionaries (views not included for performance)
        """
        import tableauserverclient as TSC

        server, auth = self._get_connection()
        workbooks_data = []

        with server.auth.sign_in(auth):
            # Build project hierarchy for full paths
            project_map = self._build_project_hierarchy(server)

            # Build user map for owner names
            user_map = self._build_user_map(server)

            # Fetch workbooks with pagination
            req_options = TSC.RequestOptions(pagesize=100)

            for workbook in TSC.Pager(server.workbooks, req_options):
                # Get project full path
                project_full_path = project_map.get(workbook.project_id, {}).get(
                    "full_path", "Unknown"
                )

                # Apply filters
                if search_query:
                    if search_query.lower() not in workbook.name.lower():
                        continue

                if project_path:
                    if not project_full_path.startswith(project_path):
                        continue

                # Apply exception list filter
                if self._should_exclude(workbook.name, project_full_path):
                    continue

                # Get owner info from user map
                owner_info = user_map.get(workbook.owner_id, {})

                # Get project name from the map
                project_info = project_map.get(workbook.project_id, {})
                project_name = project_info.get("name", "Unknown")

                workbooks_data.append(
                    {
                        "id": workbook.id,
                        "name": workbook.name,
                        "description": workbook.description or "",
                        "projectName": project_name,
                        "projectPath": project_full_path,
                        "ownerName": owner_info.get("name", workbook.owner_id or ""),
                        "ownerEmail": owner_info.get("email", ""),
                        "createdAt": (
                            workbook.created_at.isoformat()
                            if hasattr(workbook, "created_at") and workbook.created_at
                            else None
                        ),
                        "updatedAt": (
                            workbook.updated_at.isoformat()
                            if workbook.updated_at
                            else None
                        ),
                        "webUrl": workbook.webpage_url or "",
                        "viewCount": 0,
                    }
                )

        return workbooks_data

    def _build_user_map(self, server) -> dict:
        """Build map of user IDs to user info."""
        import tableauserverclient as TSC

        user_map = {}
        try:
            for user in TSC.Pager(server.users):
                user_map[user.id] = {
                    "name": user.name or user.fullname or "",
                    "email": getattr(user, "email", "") or "",
                }
        except Exception:
            # If we can't fetch users, return empty map
            pass
        return user_map

    def _build_project_hierarchy(self, server) -> dict:
        """Build hierarchical project structure with full paths."""
        import tableauserverclient as TSC

        project_map = {}

        # Fetch all projects
        for project in TSC.Pager(server.projects):
            project_map[project.id] = {
                "name": project.name,
                "parent_id": project.parent_id,
                "full_path": None,
            }

        # Compute full paths recursively
        def get_full_path(project_id: str) -> str:
            if project_id not in project_map:
                return "Unknown"

            proj = project_map[project_id]
            if proj["full_path"]:
                return proj["full_path"]

            if proj["parent_id"] and proj["parent_id"] in project_map:
                parent_path = get_full_path(proj["parent_id"])
                proj["full_path"] = f"{parent_path}/{proj['name']}"
            else:
                proj["full_path"] = proj["name"]

            return proj["full_path"]

        # Compute all paths
        for project_id in project_map:
            get_full_path(project_id)

        return project_map

    def get_workbook_by_id(self, workbook_id: str) -> Optional[dict]:
        """Fetch a single workbook by ID with full details including views."""
        import tableauserverclient as TSC

        server, auth = self._get_connection()

        with server.auth.sign_in(auth):
            try:
                workbook = server.workbooks.get_by_id(workbook_id)
                server.workbooks.populate_views(workbook)

                project_map = self._build_project_hierarchy(server)
                user_map = self._build_user_map(server)

                project_full_path = project_map.get(workbook.project_id, {}).get(
                    "full_path", "Unknown"
                )
                owner_info = user_map.get(workbook.owner_id, {})

                project_info = project_map.get(workbook.project_id, {})
                project_name = project_info.get("name", "Unknown")

                return {
                    "id": workbook.id,
                    "name": workbook.name,
                    "description": workbook.description or "",
                    "projectName": project_name,
                    "projectPath": project_full_path,
                    "ownerName": owner_info.get("name", workbook.owner_id or ""),
                    "ownerEmail": owner_info.get("email", ""),
                    "createdAt": (
                        workbook.created_at.isoformat()
                        if hasattr(workbook, "created_at") and workbook.created_at
                        else None
                    ),
                    "updatedAt": (
                        workbook.updated_at.isoformat() if workbook.updated_at else None
                    ),
                    "webUrl": workbook.webpage_url or "",
                    "viewCount": len(workbook.views) if workbook.views else 0,
                    "views": [
                        {"id": v.id, "name": v.name, "contentUrl": v.content_url}
                        for v in (workbook.views or [])
                    ],
                }
            except Exception:
                return None

    def get_unique_project_paths(self) -> list[str]:
        """Get list of unique project paths for filtering."""
        import tableauserverclient as TSC

        server, auth = self._get_connection()

        with server.auth.sign_in(auth):
            project_map = self._build_project_hierarchy(server)
            paths = sorted(set(p["full_path"] for p in project_map.values() if p["full_path"]))
            return paths


# Mock service for development without Tableau credentials
class MockTableauService:
    """Mock Tableau service for development/testing."""

    def __init__(self):
        """Initialize with exception list."""
        self._exceptions = self._load_exceptions()

    def _load_exceptions(self) -> dict:
        """Load exception configuration from config file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "exceptions.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {"excludedWorkbooks": [], "excludedFolders": [], "excludedFoldersExact": [], "excludedPaths": []}

    def _should_exclude(self, workbook_name: str, project_path: str) -> bool:
        """Check if workbook should be excluded based on exception list."""
        # Check workbook name (exact match)
        if workbook_name in self._exceptions.get("excludedWorkbooks", []):
            return True
        # Check if any path segment contains excluded folder pattern (substring match)
        path_parts = project_path.split("/")
        for folder_pattern in self._exceptions.get("excludedFolders", []):
            for segment in path_parts:
                if folder_pattern in segment:
                    return True
        # Check if any path segment exactly matches excluded folder (exact match)
        for folder_exact in self._exceptions.get("excludedFoldersExact", []):
            if folder_exact in path_parts:
                return True
        # Check full path prefix match
        for excluded_path in self._exceptions.get("excludedPaths", []):
            if project_path.startswith(excluded_path):
                return True
        return False

    MOCK_WORKBOOKS = [
        {
            "id": "wb-001",
            "name": "Sales Dashboard",
            "description": "Analyze revenue by region, track monthly sales trends, and identify top-performing products.",
            "projectName": "Sales",
            "projectPath": "Finance/Sales",
            "ownerName": "Jane Analyst",
            "ownerEmail": "analyst@company.com",
            "createdAt": "2024-01-01T08:00:00Z",
            "updatedAt": "2024-01-15T10:30:00Z",
            "webUrl": "https://tableau.example.com/views/SalesDashboard",
            "viewCount": 2,
            "views": [
                {"id": "v-001", "name": "Overview", "contentUrl": "/views/SalesDashboard/Overview"},
                {"id": "v-002", "name": "Regional", "contentUrl": "/views/SalesDashboard/Regional"},
            ],
        },
        {
            "id": "wb-002",
            "name": "Marketing Metrics",
            "description": "Track campaign performance, lead generation, and conversion rates across marketing channels.",
            "projectName": "Marketing",
            "projectPath": "Marketing",
            "ownerName": "John Marketer",
            "ownerEmail": "marketer@company.com",
            "createdAt": "2024-01-02T09:00:00Z",
            "updatedAt": "2024-01-14T14:20:00Z",
            "webUrl": "https://tableau.example.com/views/MarketingMetrics",
            "viewCount": 1,
            "views": [
                {"id": "v-003", "name": "Campaigns", "contentUrl": "/views/MarketingMetrics/Campaigns"},
            ],
        },
        {
            "id": "wb-003",
            "name": "HR Analytics",
            "description": "Monitor headcount, track employee turnover rates, and analyze workforce demographics.",
            "projectName": "Reports",
            "projectPath": "HR/Reports",
            "ownerName": "Sarah HR",
            "ownerEmail": "hr@company.com",
            "createdAt": "2024-01-03T10:00:00Z",
            "updatedAt": "2024-01-13T09:00:00Z",
            "webUrl": "https://tableau.example.com/views/HRAnalytics",
            "viewCount": 2,
            "views": [
                {"id": "v-004", "name": "Headcount", "contentUrl": "/views/HRAnalytics/Headcount"},
                {"id": "v-005", "name": "Turnover", "contentUrl": "/views/HRAnalytics/Turnover"},
            ],
        },
        {
            "id": "wb-004",
            "name": "Quarterly Revenue Report",
            "description": "Summarizes quarterly revenue performance with year-over-year comparisons and growth metrics.",
            "projectName": "Sales",
            "projectPath": "Finance/Sales",
            "ownerName": "Jane Analyst",
            "ownerEmail": "analyst@company.com",
            "createdAt": "2024-01-04T11:00:00Z",
            "updatedAt": "2024-01-12T16:45:00Z",
            "webUrl": "https://tableau.example.com/views/QuarterlyRevenue",
            "viewCount": 1,
            "views": [
                {"id": "v-006", "name": "Q4 Summary", "contentUrl": "/views/QuarterlyRevenue/Q4Summary"},
            ],
        },
        {
            "id": "wb-005",
            "name": "Customer Satisfaction Scores",
            "description": "Track NPS scores, analyze customer feedback trends, and identify areas for service improvement.",
            "projectName": "Customer Success",
            "projectPath": "Customer Success",
            "ownerName": "Mike Support",
            "ownerEmail": "cs@company.com",
            "createdAt": "2024-01-05T12:00:00Z",
            "updatedAt": "2024-01-11T11:15:00Z",
            "webUrl": "https://tableau.example.com/views/CSAT",
            "viewCount": 2,
            "views": [
                {"id": "v-007", "name": "NPS Trends", "contentUrl": "/views/CSAT/NPSTrends"},
                {"id": "v-008", "name": "By Region", "contentUrl": "/views/CSAT/ByRegion"},
            ],
        },
    ]

    def is_configured(self) -> bool:
        """Mock is always 'configured'."""
        return True

    def fetch_workbooks(
        self, search_query: Optional[str] = None, project_path: Optional[str] = None
    ) -> list[dict]:
        """Return mock workbooks with optional filtering."""
        results = self.MOCK_WORKBOOKS.copy()

        # Apply exception list filter
        results = [
            w for w in results
            if not self._should_exclude(w["name"], w["projectPath"])
        ]

        if search_query:
            query_lower = search_query.lower()
            results = [w for w in results if query_lower in w["name"].lower()]

        if project_path:
            results = [w for w in results if w["projectPath"].startswith(project_path)]

        return results

    def get_workbook_by_id(self, workbook_id: str) -> Optional[dict]:
        """Return mock workbook by ID."""
        for wb in self.MOCK_WORKBOOKS:
            if wb["id"] == workbook_id:
                return wb
        return None

    def get_unique_project_paths(self) -> list[str]:
        """Get unique project paths from mock data."""
        paths = sorted(set(w["projectPath"] for w in self.MOCK_WORKBOOKS))
        return paths


def get_tableau_service(force_mock: bool = False):
    """
    Factory function to get appropriate Tableau service.

    Args:
        force_mock: If True, always return MockTableauService (useful for testing)

    Returns:
        TableauService or MockTableauService
    """
    if force_mock:
        return MockTableauService()

    service = TableauService()
    if service.is_configured():
        return service
    else:
        print("WARNING: Tableau not configured, using mock data")
        return MockTableauService()
