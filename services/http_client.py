"""
HTTP client implementations for remote service access.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

from services.base_service import get_service_url


class HTTPClient:
    """Base HTTP client with common request methods."""

    @staticmethod
    def _get_base_url() -> str:
        """Get base URL or raise error if not in remote mode."""
        url = get_service_url()
        if not url:
            raise RuntimeError("SERVICE_URL environment variable not set")
        return url.rstrip("/")

    @staticmethod
    def _handle_response(
        response: httpx.Response,
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Handle HTTP response and return (data, error)."""
        if response.status_code >= 400:
            try:
                error_detail = response.json().get("detail", response.text)
            except Exception:
                error_detail = response.text
            return None, error_detail

        try:
            return response.json(), None
        except Exception:
            return None, "Invalid JSON response"

    @staticmethod
    def get(
        endpoint: str, params: Optional[Dict] = None
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Make GET request."""
        base_url = HTTPClient._get_base_url()
        url = f"{base_url}{endpoint}"

        try:
            response = httpx.get(url, params=params or {}, timeout=30.0)
            return HTTPClient._handle_response(response)
        except httpx.RequestError as e:
            return None, f"Request failed: {str(e)}"

    @staticmethod
    def post(endpoint: str, json: Dict) -> Tuple[Optional[Any], Optional[str]]:
        """Make POST request."""
        base_url = HTTPClient._get_base_url()
        url = f"{base_url}{endpoint}"

        try:
            response = httpx.post(url, json=json, timeout=30.0)
            return HTTPClient._handle_response(response)
        except httpx.RequestError as e:
            return None, f"Request failed: {str(e)}"

    @staticmethod
    def patch(endpoint: str, json: Dict) -> Tuple[Optional[Any], Optional[str]]:
        """Make PATCH request."""
        base_url = HTTPClient._get_base_url()
        url = f"{base_url}{endpoint}"

        try:
            response = httpx.patch(url, json=json, timeout=30.0)
            return HTTPClient._handle_response(response)
        except httpx.RequestError as e:
            return None, f"Request failed: {str(e)}"


class RemoteObject:
    """Base class for objects returned from HTTP API."""

    def __init__(self, data: Dict):
        self._data = data
        for key, value in data.items():
            # Convert datetime strings to datetime objects
            if isinstance(value, str) and "T" in value:
                try:
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            setattr(self, key, value)


class ContactHTTP:
    """HTTP client for Contact operations."""

    @staticmethod
    def add_contact(
        first_name: str, last_name: str
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Add a contact via HTTP."""
        data, error = HTTPClient.post(
            "/contacts", {"first_name": first_name, "last_name": last_name}
        )
        if error:
            return None, error
        return RemoteObject(data), None

    @staticmethod
    def list_contacts() -> List[Any]:
        """List all contacts via HTTP."""
        data, error = HTTPClient.get("/contacts")
        if error:
            return []
        return [RemoteObject(item) for item in data]

    @staticmethod
    def get_top_contacts(limit: int = 10) -> List[Tuple[Any, int]]:
        """Get top contacts via HTTP."""
        data, error = HTTPClient.get("/contacts/top", {"limit": limit})
        if error:
            return []
        return [(RemoteObject(item), item["note_count"]) for item in data]

    @staticmethod
    def bulk_add_contacts(names: List[str]) -> Tuple[List[str], List[str]]:
        """Bulk add contacts via HTTP."""
        data, error = HTTPClient.post("/contacts/bulk", names)
        if error:
            return [], []
        return data.get("added", []), data.get("skipped", [])

    @staticmethod
    def search_contacts(query: str) -> List[Any]:
        """Search contacts via HTTP."""
        data, error = HTTPClient.get("/contacts/search", {"query": query})
        if error:
            return []
        return [RemoteObject(item) for item in data]

    @staticmethod
    def get_contact_with_notes(
        contact_id: int, note_limit: int = 10
    ) -> Optional[Tuple[Any, List[Any]]]:
        """Get contact with notes via HTTP."""
        # This would require a new API endpoint
        # For now, return None to fall back to direct mode
        return None


class TaskHTTP:
    """HTTP client for Task operations."""

    @staticmethod
    def add_task(
        title: str,
        due_date: datetime,
        importance: int,
        description: Optional[str] = None,
        contact_ids: Optional[List[int]] = None,
        organization_ids: Optional[List[int]] = None,
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Add a task via HTTP."""
        data, error = HTTPClient.post(
            "/tasks",
            {
                "title": title,
                "due_date": due_date.isoformat(),
                "importance": importance,
                "description": description,
                "contact_ids": contact_ids,
                "organization_ids": organization_ids,
            },
        )
        if error:
            return None, error
        return RemoteObject(data), None

    @staticmethod
    def list_tasks(
        limit: int = 20,
        show_completed: bool = False,
        contact_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> List[Any]:
        """List tasks via HTTP."""
        params = {
            "limit": limit,
            "show_completed": show_completed,
        }
        if contact_id:
            params["contact_id"] = contact_id
        if organization_id:
            params["organization_id"] = organization_id

        data, error = HTTPClient.get("/tasks", params)
        if error:
            return []

        # Convert nested objects
        result = []
        for item in data:
            task = RemoteObject(item)
            task.contacts = [RemoteObject(c) for c in item.get("contacts", [])]
            task.organizations = [
                RemoteObject(o) for o in item.get("organizations", [])
            ]
            result.append(task)
        return result

    @staticmethod
    def get_urgent_tasks(days: int = 7, sort_by: str = "urgency") -> List[Any]:
        """Get urgent tasks via HTTP."""
        data, error = HTTPClient.get(
            "/tasks/urgent", {"days": days, "sort_by": sort_by}
        )
        if error:
            return []

        result = []
        for item in data:
            task = RemoteObject(item)
            task.contacts = [RemoteObject(c) for c in item.get("contacts", [])]
            task.organizations = [
                RemoteObject(o) for o in item.get("organizations", [])
            ]
            result.append(task)
        return result

    @staticmethod
    def get_task(task_id: int) -> Optional[Any]:
        """Get a task via HTTP."""
        data, error = HTTPClient.get(f"/tasks/{task_id}")
        if error:
            return None
        task = RemoteObject(data)
        task.contacts = [RemoteObject(c) for c in data.get("contacts", [])]
        task.organizations = [RemoteObject(o) for o in data.get("organizations", [])]
        return task

    @staticmethod
    def complete_task(task_id: int) -> Tuple[Optional[Any], Optional[str]]:
        """Complete a task via HTTP."""
        data, error = HTTPClient.post(f"/tasks/{task_id}/complete", {})
        if error:
            return None, error
        return RemoteObject(data), None

    @staticmethod
    def uncomplete_task(task_id: int) -> Tuple[Optional[Any], Optional[str]]:
        """Uncomplete a task via HTTP."""
        data, error = HTTPClient.post(f"/tasks/{task_id}/uncomplete", {})
        if error:
            return None, error
        return RemoteObject(data), None

    @staticmethod
    def tag_task(
        task_id: int,
        add_contact_ids: Optional[List[int]] = None,
        add_org_ids: Optional[List[int]] = None,
        remove_contact_ids: Optional[List[int]] = None,
        remove_org_ids: Optional[List[int]] = None,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Tag a task via HTTP."""
        payload = {}
        if add_contact_ids:
            payload["add_contact_ids"] = add_contact_ids
        if add_org_ids:
            payload["add_organization_ids"] = add_org_ids
        if remove_contact_ids:
            payload["remove_contact_ids"] = remove_contact_ids
        if remove_org_ids:
            payload["remove_organization_ids"] = remove_org_ids

        return HTTPClient.patch(f"/tasks/{task_id}/tags", payload)


class NoteHTTP:
    """HTTP client for Note operations."""

    @staticmethod
    def add_note(
        title: str,
        content: str,
        contact_ids: Optional[List[int]] = None,
        organization_ids: Optional[List[int]] = None,
        task_ids: Optional[List[int]] = None,
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Add a note via HTTP."""
        data, error = HTTPClient.post(
            "/notes",
            {
                "title": title,
                "content": content,
                "contact_ids": contact_ids,
                "organization_ids": organization_ids,
                "task_ids": task_ids,
            },
        )
        if error:
            return None, error

        note = RemoteObject(data)
        note.contacts = [RemoteObject(c) for c in data.get("contacts", [])]
        note.organizations = [RemoteObject(o) for o in data.get("organizations", [])]
        note.tasks = [RemoteObject(t) for t in data.get("tasks", [])]
        return note, None

    @staticmethod
    def list_notes(
        limit: int = 20,
        contact_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> Tuple[Optional[List[Any]], Optional[str]]:
        """List notes via HTTP."""
        params = {"limit": limit}
        if contact_id:
            params["contact_id"] = contact_id
        if organization_id:
            params["organization_id"] = organization_id

        data, error = HTTPClient.get("/notes", params)
        if error:
            return None, error

        result = []
        for item in data:
            note = RemoteObject(item)
            note.contacts = [RemoteObject(c) for c in item.get("contacts", [])]
            note.organizations = [
                RemoteObject(o) for o in item.get("organizations", [])
            ]
            note.tasks = [RemoteObject(t) for t in item.get("tasks", [])]
            result.append(note)
        return result, None

    @staticmethod
    def get_note(note_id: int) -> Optional[Any]:
        """Get a note via HTTP."""
        data, error = HTTPClient.get(f"/notes/{note_id}")
        if error:
            return None

        note = RemoteObject(data)
        note.contacts = [RemoteObject(c) for c in data.get("contacts", [])]
        note.organizations = [RemoteObject(o) for o in data.get("organizations", [])]
        note.tasks = [RemoteObject(t) for t in data.get("tasks", [])]
        return note

    @staticmethod
    def tag_note(
        note_id: int,
        add_contact_ids: Optional[List[int]] = None,
        remove_contact_ids: Optional[List[int]] = None,
        add_org_ids: Optional[List[int]] = None,
        remove_org_ids: Optional[List[int]] = None,
        add_task_ids: Optional[List[int]] = None,
        remove_task_ids: Optional[List[int]] = None,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Tag a note via HTTP."""
        payload = {}
        if add_contact_ids:
            payload["add_contact_ids"] = add_contact_ids
        if remove_contact_ids:
            payload["remove_contact_ids"] = remove_contact_ids
        if add_org_ids:
            payload["add_organization_ids"] = add_org_ids
        if remove_org_ids:
            payload["remove_organization_ids"] = remove_org_ids
        if add_task_ids:
            payload["add_task_ids"] = add_task_ids
        if remove_task_ids:
            payload["remove_task_ids"] = remove_task_ids

        return HTTPClient.patch(f"/notes/{note_id}/tags", payload)


class OrganizationHTTP:
    """HTTP client for Organization operations."""

    @staticmethod
    def add_organization(name: str) -> Tuple[Optional[Any], Optional[str]]:
        """Add an organization via HTTP."""
        data, error = HTTPClient.post("/organizations", {"name": name})
        if error:
            return None, error
        return RemoteObject(data), None

    @staticmethod
    def list_organizations() -> List[Any]:
        """List organizations via HTTP."""
        data, error = HTTPClient.get("/organizations")
        if error:
            return []
        return [RemoteObject(item) for item in data]

    @staticmethod
    def get_top_organizations(limit: int = 10) -> List[Tuple[Any, int]]:
        """Get top organizations via HTTP."""
        data, error = HTTPClient.get("/organizations/top", {"limit": limit})
        if error:
            return []
        return [(RemoteObject(item), item["note_count"]) for item in data]
