"""
YouTrack Fields API client.
Provides functions to fetch available custom field values for projects.
"""

from typing import Any, Dict, List, Optional
import logging

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.projects import ProjectsClient

logger = logging.getLogger(__name__)


def get_project_fields(client: YouTrackClient, project_id: str) -> Dict[str, Any]:
    """
    Fetch available custom field definitions and their values for a project.

    Args:
        client: The YouTrack API client
        project_id: The project ID or short name

    Returns:
        Dictionary mapping field names to their metadata and allowed values
    """
    projects_client = ProjectsClient(client)
    return projects_client.get_all_custom_fields_schemas(project_id)
