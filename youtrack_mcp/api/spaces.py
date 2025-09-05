"""
YouTrack Knowledge Base Spaces API client.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from youtrack_mcp.api.client import YouTrackClient


class Space(BaseModel):
    """Model for a YouTrack Knowledge Base Space."""

    id: str
    name: Optional[str] = None

    model_config = {
        "extra": "allow",
        "populate_by_name": True,
    }


class SpacesClient:
    """Client for interacting with YouTrack KB Spaces API."""

    def __init__(self, client: YouTrackClient):
        self.client = client

    def get_space(self, space_id: str, fields: Optional[str] = None) -> Space:
        """Get a single space by id."""
        fields_query = fields or "id,name"
        response = self.client.get(f"spaces/{space_id}?fields={fields_query}")
        return Space.model_validate(response)

    def list_spaces(
        self, fields: Optional[str] = None, top: int = 50, skip: int = 0
    ) -> List[Space]:
        """List spaces with pagination."""
        params: Dict[str, Any] = {
            "$top": top,
            "$skip": skip,
            "fields": fields or "id,name",
        }
        response = self.client.get("spaces", params=params)
        return [Space.model_validate(item) for item in response]
