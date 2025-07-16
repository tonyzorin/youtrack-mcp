"""
YouTrack Issues API client.
"""

from typing import Any, Dict, List, Optional
import json
import logging

from pydantic import BaseModel, Field

from youtrack_mcp.api.client import YouTrackClient, YouTrackAPIError

logger = logging.getLogger(__name__)


class Issue(BaseModel):
    """Model for a YouTrack issue."""

    id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    created: Optional[int] = None
    updated: Optional[int] = None
    project: Optional[Dict[str, Any]] = Field(default_factory=dict)
    reporter: Optional[Dict[str, Any]] = None
    assignee: Optional[Dict[str, Any]] = None
    custom_fields: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    model_config = {
        "extra": "allow",  # Allow extra fields from the API
        "populate_by_name": True,  # Allow population by field name (helps with aliases)
        "validate_assignment": False,  # Less strict validation for attribute assignment
        "protected_namespaces": (),  # Don't protect any namespaces
    }

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        """Override model_validate to handle various input formats."""
        try:
            # Try standard validation
            return super().model_validate(obj, *args, **kwargs)
        except Exception as e:
            # Fall back to more permissive validation
            if isinstance(obj, dict):
                # Ensure ID is present
                if "id" not in obj and obj.get("$type") == "Issue":
                    # Try to find an ID from other fields or generate placeholder
                    obj["id"] = obj.get(
                        "idReadable", str(obj.get("created", "unknown-id"))
                    )

                # Create issue with minimal validated data
                return cls(
                    id=obj.get("id", "unknown"),
                    summary=obj.get("summary", "No summary"),
                    description=obj.get("description", ""),
                    created=obj.get("created"),
                    updated=obj.get("updated"),
                    project=obj.get("project", {}),
                    reporter=obj.get("reporter"),
                    assignee=obj.get("assignee"),
                    custom_fields=obj.get("customFields", []),
                )

            # If obj isn't even a dict, raise the original error
            raise


class IssuesClient:
    """Client for interacting with YouTrack Issues API."""

    def __init__(self, client: YouTrackClient):
        """
        Initialize the Issues API client.

        Args:
            client: The YouTrack API client
        """
        self.client = client

    def get_issue(self, issue_id: str) -> Issue:
        """
        Get an issue by ID.

        Args:
            issue_id: The issue ID or readable ID (e.g., PROJECT-123)

        Returns:
            The issue data
        """
        try:
            # Get issue data
            response = self.client.get(f"issues/{issue_id}")

            # If the response doesn't have all needed fields, fetch more details
            if (
                isinstance(response, dict)
                and response.get("$type") == "Issue"
                and "summary" not in response
            ):
                # Get additional fields we need including attachments
                fields = "summary,description,created,updated,project,reporter,assignee,customFields,attachments(id,name,url,mimeType,size)"
                try:
                    detailed_response = self.client.get(
                        f"issues/{issue_id}?fields={fields}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to get detailed issue data: {e}")
                    detailed_response = response
            else:
                detailed_response = response

            # Ensure the ID field is present
            if (
                isinstance(detailed_response, dict)
                and "id" not in detailed_response
                and detailed_response.get("$type") == "Issue"
            ):
                detailed_response["id"] = issue_id

            try:
                # Try to validate the model
                return Issue.model_validate(detailed_response)
            except Exception as validation_error:
                # If validation fails, create a more flexible issue object
                logger.warning(
                    f"Issue validation error: {validation_error}. Creating issue with minimal data."
                )

                if isinstance(detailed_response, dict):
                    # Extract key fields if possible
                    summary = detailed_response.get("summary", "Unknown summary")
                    description = detailed_response.get("description", "")

                    # Create a basic issue with the available data
                    issue = Issue(id=issue_id, summary=summary, description=description)

                    # Add any other fields that might be useful
                    for field in [
                        "created",
                        "updated",
                        "project",
                        "reporter",
                        "assignee",
                        "attachments",
                    ]:
                        if field in detailed_response:
                            setattr(issue, field, detailed_response[field])

                    return issue
                else:
                    # If response is not even a dict, create a minimal issue
                    return Issue(id=issue_id, summary=f"Issue {issue_id}")

        except Exception as e:
            # Log the full error with traceback
            logger.exception(f"Error retrieving issue {issue_id}")
            # Create minimal issue to avoid breaking calls
            return Issue(id=issue_id, summary=f"Error: {str(e)[:100]}...")

    def create_issue(
        self,
        project_id: str,
        summary: str,
        description: Optional[str] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> Issue:
        """
        Create a new issue.

        Args:
            project_id: The ID of the project
            summary: The issue summary
            description: The issue description
            additional_fields: Additional fields to set on the issue

        Returns:
            The created issue data
        """
        # Make sure we have valid input data
        if not project_id:
            raise ValueError("Project ID is required")
        if not summary:
            raise ValueError("Summary is required")

        # Format request data according to YouTrack API requirements
        # Note: YouTrack API requires a specific format for some fields
        data = {"project": {"id": project_id}, "summary": summary}

        if description:
            data["description"] = description

        if additional_fields:
            data.update(additional_fields)

        try:
            # For debugging
            logger.info(f"Creating issue with data: {json.dumps(data)}")

            # Post directly with the json parameter to ensure correct format
            url = "issues"
            response = self.client.session.post(
                f"{self.client.base_url}/{url}",
                json=data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

            # Handle the response
            if response.status_code >= 400:
                error_msg = f"Error creating issue: {response.status_code}"
                try:
                    error_content = response.json()
                    error_msg += f" - {json.dumps(error_content)}"
                except:
                    error_msg += f" - {response.text}"

                logger.error(error_msg)
                raise YouTrackAPIError(error_msg, response.status_code, response)

            # Process successful response
            try:
                result = response.json()
                return Issue.model_validate(result)
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")
                # Return raw response if we can't parse it
                return Issue(
                    id=str(response.status_code), summary="Created successfully"
                )

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Error creating issue: {str(e)}, Data: {data}"
            )
            raise

    def update_issue(
        self,
        issue_id: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> Issue:
        """
        Update an existing issue.

        Args:
            issue_id: The issue ID or readable ID
            summary: The new issue summary
            description: The new issue description
            additional_fields: Additional fields to update

        Returns:
            The updated issue data
        """
        data = {}

        if summary is not None:
            data["summary"] = summary

        if description is not None:
            data["description"] = description

        if additional_fields:
            data.update(additional_fields)

        if not data:
            # Nothing to update
            return self.get_issue(issue_id)

        response = self.client.post(f"issues/{issue_id}", data=data)
        return Issue.model_validate(response)

    def search_issues(self, query: str, limit: int = 10) -> List[Issue]:
        """
        Search for issues using YouTrack query language.

        Args:
            query: The search query
            limit: Maximum number of issues to return

        Returns:
            List of matching issues
        """
        # Request additional fields to ensure we get summary
        fields = "id,summary,description,created,updated,project,reporter,assignee,customFields"
        params = {"query": query, "$top": limit, "fields": fields}
        response = self.client.get("issues", params=params)

        issues = []
        if isinstance(response, list):
            for issue_data in response:
                try:
                    issues.append(Issue.model_validate(issue_data))
                except Exception as e:
                    logger.warning(f"Error validating issue: {e}")
                    # Create a basic issue with id
                    issue_id = issue_data.get(
                        "id", str(issue_data.get("created", "unknown"))
                    )
                    issues.append(
                        Issue(
                            id=issue_id,
                            summary=issue_data.get("summary", f"Issue {issue_id}"),
                        )
                    )

        return issues

    def add_comment(self, issue_id: str, text: str) -> Dict[str, Any]:
        """
        Add a comment to an issue.

        Args:
            issue_id: The issue ID or readable ID
            text: The comment text

        Returns:
            The created comment data
        """
        data = {"text": text}
        return self.client.post(f"issues/{issue_id}/comments", data=data)

        
    def get_comments(self, issue_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all comments for an issue.
        
        Args:
            issue_id: The issue ID or readable ID
            limit: Maximum number of comments to return (default: 100)
            
        Returns:
            List of comments for the issue
        """
        # Request with fields to include author and other relevant information
        fields = "id,text,created,updated,author(id,login,name)"
        params = {"$top": limit, "fields": fields}
        return self.client.get(f"issues/{issue_id}/comments", params=params) 

    def get_attachment_content(self, issue_id: str, attachment_id: str) -> bytes:
        """
        Get the content of an attachment with file size validation.

        Args:
            issue_id: The issue ID or readable ID
            attachment_id: The attachment ID

        Returns:
            The attachment content as bytes

        Raises:
            ValueError: If attachment not found or file too large
            YouTrackAPIError: If API request fails
        """
        # First, get the attachment metadata to get the URL and size
        issue_response = self.client.get(
            f"issues/{issue_id}?fields=attachments(id,url,size,name,mimeType)"
        )

        # Find the attachment with the matching ID
        attachment_info = None
        if "attachments" in issue_response:
            for attachment in issue_response["attachments"]:
                if attachment.get("id") == attachment_id:
                    attachment_info = attachment
                    break

        if not attachment_info:
            raise ValueError(
                f"Attachment {attachment_id} not found in issue {issue_id}"
            )

        # Check file size limit for base64 encoding
        # Base64 encoding increases size by ~33%, so for 1MB base64 limit, max original size is ~750KB
        MAX_ORIGINAL_SIZE = 750 * 1024  # 750KB original file
        MAX_BASE64_SIZE = (
            1024 * 1024
        )  # 1MB after base64 encoding (Claude Desktop limit)

        file_size = attachment_info.get("size", 0)
        filename = attachment_info.get("name", attachment_id)
        mime_type = attachment_info.get("mimeType", "unknown")

        if file_size > MAX_ORIGINAL_SIZE:
            # Calculate what the base64 size would be
            estimated_base64_size = int(file_size * 1.33)
            raise ValueError(
                f"Attachment '{filename}' ({mime_type}) is too large "
                f"({file_size:,} bytes → ~{estimated_base64_size:,} bytes after base64 encoding). "
                f"Maximum allowed: {MAX_ORIGINAL_SIZE:,} bytes original (~{MAX_BASE64_SIZE:,} bytes base64)."
            )

        attachment_url = attachment_info.get("url")
        if not attachment_url:
            raise ValueError(f"No download URL found for attachment {attachment_id}")

        # The URL in the attachment data is relative to the base URL
        if attachment_url.startswith("/"):
            attachment_url = attachment_url[1:]  # Remove leading slash

        # Construct the full URL
        base_url = self.client.base_url
        if base_url.endswith("/api"):
            base_url = base_url[:-4]  # Remove '/api' suffix

        full_url = f"{base_url}/{attachment_url}"

        # Make the request to get the attachment content
        from youtrack_mcp.api.client import YouTrackAPIError

        response = self.client.session.get(full_url)

        # Check for errors
        if response.status_code >= 400:
            error_msg = f"Error getting attachment content: {response.status_code}"
            raise YouTrackAPIError(error_msg, response.status_code, response)

        # Double-check the actual content size
        content_length = len(response.content)
        if content_length > MAX_ORIGINAL_SIZE:
            estimated_base64_size = int(content_length * 1.33)
            raise ValueError(
                f"Downloaded content size ({content_length:,} bytes → ~{estimated_base64_size:,} bytes base64) "
                f"exceeds maximum allowed size ({MAX_ORIGINAL_SIZE:,} bytes original). "
                f"The file may have been modified since metadata was fetched."
            )

        # Return the binary content
        return response.content
