"""Tableau Server Client service for fetching workbooks and views."""

import json
import os
from pathlib import Path
from typing import Optional


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
        # Path relative to this file in api/services/
        config_path = Path(__file__).parent.parent / "config" / "exceptions.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {"excludedWorkbooks": [], "excludedFolders": [], "excludedFoldersExact": [], "excludedPaths": []}

    def _should_exclude(self, workbook_name: str, project_path: str) -> bool:
        """Check if workbook should be excluded based on exception list."""
        if workbook_name in self._exceptions.get("excludedWorkbooks", []):
            return True
        path_parts = project_path.split("/")
        for folder_pattern in self._exceptions.get("excludedFolders", []):
            for segment in path_parts:
                if folder_pattern in segment:
                    return True
        for folder_exact in self._exceptions.get("excludedFoldersExact", []):
            if folder_exact in path_parts:
                return True
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
            raise ValueError("Tableau credentials not configured. Check environment variables.")

        os.environ["NO_PROXY"] = "*"

        server = TSC.Server(self.server_url, use_server_version=True)
        auth = TSC.PersonalAccessTokenAuth(
            self.token_name, self.token_secret, self.site_name
        )
        return server, auth

    def fetch_workbooks(
        self, search_query: Optional[str] = None, project_path: Optional[str] = None
    ) -> list[dict]:
        """Fetch all workbooks from Tableau Server."""
        import tableauserverclient as TSC

        server, auth = self._get_connection()
        workbooks_data = []

        with server.auth.sign_in(auth):
            project_map = self._build_project_hierarchy(server)
            user_map = self._build_user_map(server)
            req_options = TSC.RequestOptions(pagesize=100)

            for workbook in TSC.Pager(server.workbooks, req_options):
                project_full_path = project_map.get(workbook.project_id, {}).get(
                    "full_path", "Unknown"
                )

                if search_query:
                    query = search_query.lower()
                    description = (workbook.description or "").lower()
                    if query not in workbook.name.lower() and query not in description:
                        continue

                if project_path:
                    if not project_full_path.startswith(project_path):
                        continue

                if self._should_exclude(workbook.name, project_full_path):
                    continue

                excluded_tags = self._exceptions.get("excludedTags", [])
                if excluded_tags and workbook.tags:
                    if workbook.tags & set(excluded_tags):
                        continue

                owner_info = user_map.get(workbook.owner_id, {})
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
            pass
        return user_map

    def _build_project_hierarchy(self, server) -> dict:
        """Build hierarchical project structure with full paths."""
        import tableauserverclient as TSC

        project_map = {}

        for project in TSC.Pager(server.projects):
            project_map[project.id] = {
                "name": project.name,
                "parent_id": project.parent_id,
                "full_path": None,
            }

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


def get_tableau_service(force_mock: bool = False):
    """Factory function to get appropriate Tableau service."""
    if force_mock:
        raise ValueError("Mock service not available in production")

    service = TableauService()
    if service.is_configured():
        return service
    else:
        raise ValueError("Tableau not configured. Set environment variables.")
