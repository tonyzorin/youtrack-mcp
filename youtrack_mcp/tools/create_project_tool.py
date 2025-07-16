"""
Standalone tool for creating YouTrack projects.
"""

import json
import logging
from typing import Optional

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.projects import ProjectsClient

logger = logging.getLogger(__name__)


def create_project_direct(
    name: str, short_name: str, lead_id: str, description: Optional[str] = None
) -> str:
    """
    Create a new YouTrack project with direct parameter handling.

    Args:
        name: The project name
        short_name: The project short name (used in issue IDs)
        lead_id: ID of the user who will be the project leader (required by YouTrack API)
        description: Optional project description

    Returns:
        JSON string with the created project information
    """
    try:
        client = YouTrackClient()
        projects_api = ProjectsClient(client)

        data = {"name": name, "shortName": short_name, "leader": {"id": lead_id}}

        if description:
            data["description"] = description

        logger.info(f"Creating project with direct tool: {data}")

        response = client.post("admin/projects", data=data)
        return json.dumps(response, indent=2)
    except Exception as e:
        logger.exception(f"Error creating project {name}")
        return json.dumps({"error": str(e)})
    finally:
        client.close()
