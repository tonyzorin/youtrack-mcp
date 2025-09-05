"""
YouTrack Knowledge Base Article MCP tools.
"""

import logging
from typing import Any, Dict, Optional

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.articles import ArticlesClient
from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class ArticlesTools:
    """Article-related MCP tools."""

    def __init__(self):
        self.client = YouTrackClient()
        self.articles_api = ArticlesClient(self.client)

    def close(self) -> None:
        if hasattr(self.client, "close"):
            self.client.close()

    @sync_wrapper
    def get_article(
        self,
        article_id: str,
        fields: str = "id,summary,content,updated,space(id,name)",
    ) -> str:
        """Get a single article by id."""
        try:
            if not article_id:
                return format_json_response({"error": "Article ID is required"})
            article = self.articles_api.get_article(article_id, fields)
            return format_json_response(
                article.model_dump() if hasattr(article, "model_dump") else article
            )
        except Exception as e:
            logger.exception(f"Error getting article {article_id}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def list_articles(
        self,
        space_id: Optional[str] = None,
        query: Optional[str] = None,
        fields: str = "id,summary,updated,space(id,name)",
        top: int = 20,
        skip: int = 0,
    ) -> str:
        """List articles with optional filters."""
        try:
            articles = self.articles_api.list_articles(
                space_id=space_id,
                query=query,
                fields=fields,
                top=top,
                skip=skip,
            )
            result = [
                a.model_dump() if hasattr(a, "model_dump") else a for a in articles
            ]
            return format_json_response(result)
        except Exception as e:
            logger.exception("Error listing articles")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def search_articles(
        self,
        query: str,
        fields: str = "id,summary,updated,space(id,name)",
        top: int = 20,
        skip: int = 0,
    ) -> str:
        """Search articles by query."""
        try:
            if not query:
                return format_json_response({"error": "Query is required"})
            articles = self.articles_api.search_articles(
                query=query, fields=fields, top=top, skip=skip
            )
            result = [
                a.model_dump() if hasattr(a, "model_dump") else a for a in articles
            ]
            return format_json_response(result)
        except Exception as e:
            logger.exception("Error searching articles")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def search_articles_filtered(
        self,
        space_id: Optional[str] = None,
        author: Optional[str] = None,
        tag: Optional[str] = None,
        status: Optional[str] = None,
        updated_since: Optional[str] = None,
        sort: Optional[str] = None,
        query: Optional[str] = None,
        fields: str = "id,summary,updated,space(id,name)",
        top: int = 20,
        skip: int = 0,
    ) -> str:
        """Search articles with filters (space, author, tag, status, updatedSince, sort)."""
        try:
            articles = self.articles_api.search_articles_filtered(
                space_id=space_id,
                author=author,
                tag=tag,
                status=status,
                updated_since=updated_since,
                sort=sort,
                query=query,
                fields=fields,
                top=top,
                skip=skip,
            )
            result = [
                a.model_dump() if hasattr(a, "model_dump") else a for a in articles
            ]
            return format_json_response(result)
        except Exception as e:
            logger.exception("Error searching filtered articles")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def create_article(
        self,
        space_id: str,
        summary: str,
        content: str,
        parent_article_id: Optional[str] = None,
        status: Optional[str] = None,
        fields: str = "id,summary,content,updated,space(id,name)",
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a Knowledge Base article."""
        try:
            if not space_id:
                return format_json_response({"error": "space_id is required"})
            if not summary:
                return format_json_response({"error": "summary is required"})
            if not content:
                return format_json_response({"error": "content is required"})
            article = self.articles_api.create_article(
                space_id=space_id,
                summary=summary,
                content=content,
                parent_article_id=parent_article_id,
                status=status,
                fields=fields,
                extra=extra,
            )
            return format_json_response(
                article.model_dump() if hasattr(article, "model_dump") else article
            )
        except Exception as e:
            logger.exception("Error creating article")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def update_article(
        self,
        article_id: str,
        summary: Optional[str] = None,
        content: Optional[str] = None,
        space_id: Optional[str] = None,
        parent_article_id: Optional[str] = None,
        status: Optional[str] = None,
        fields: str = "id,summary,content,updated,space(id,name)",
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Update a Knowledge Base article."""
        try:
            if not article_id:
                return format_json_response({"error": "article_id is required"})
            article = self.articles_api.update_article(
                article_id=article_id,
                summary=summary,
                content=content,
                space_id=space_id,
                parent_article_id=parent_article_id,
                status=status,
                fields=fields,
                extra=extra,
            )
            return format_json_response(
                article.model_dump() if hasattr(article, "model_dump") else article
            )
        except Exception as e:
            logger.exception("Error updating article")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def set_article_status(self, article_id: str, status: str) -> str:
        """Set article status, e.g., 'draft' or 'published'."""
        try:
            if not article_id:
                return format_json_response({"error": "article_id is required"})
            if not status:
                return format_json_response({"error": "status is required"})
            article = self.articles_api.set_article_status(article_id, status)
            return format_json_response(
                article.model_dump() if hasattr(article, "model_dump") else article
            )
        except Exception as e:
            logger.exception("Error setting article status")
            return format_json_response({"error": str(e)})

    # === Comments ===
    @sync_wrapper
    def list_article_comments(
        self,
        article_id: str,
        fields: str = "id,text,updated,author(login,name)",
        top: int = 50,
        skip: int = 0,
    ) -> str:
        try:
            if not article_id:
                return format_json_response({"error": "article_id is required"})
            comments = self.articles_api.list_article_comments(
                article_id=article_id, fields=fields, top=top, skip=skip
            )
            result = [c.model_dump() if hasattr(c, "model_dump") else c for c in comments]
            return format_json_response(result)
        except Exception as e:
            logger.exception("Error listing article comments")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def add_article_comment(
        self, article_id: str, text: str, fields: str = "id,text,updated,author(login,name)"
    ) -> str:
        try:
            if not article_id:
                return format_json_response({"error": "article_id is required"})
            if not text:
                return format_json_response({"error": "text is required"})
            comment = self.articles_api.add_article_comment(
                article_id=article_id, text=text, fields=fields
            )
            return format_json_response(
                comment.model_dump() if hasattr(comment, "model_dump") else comment
            )
        except Exception as e:
            logger.exception("Error adding article comment")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def update_article_comment(
        self,
        article_id: str,
        comment_id: str,
        text: str,
        fields: str = "id,text,updated,author(login,name)",
    ) -> str:
        try:
            if not article_id:
                return format_json_response({"error": "article_id is required"})
            if not comment_id:
                return format_json_response({"error": "comment_id is required"})
            if not text:
                return format_json_response({"error": "text is required"})
            comment = self.articles_api.update_article_comment(
                article_id=article_id, comment_id=comment_id, text=text, fields=fields
            )
            return format_json_response(
                comment.model_dump() if hasattr(comment, "model_dump") else comment
            )
        except Exception as e:
            logger.exception("Error updating article comment")
            return format_json_response({"error": str(e)})

    # === Attachments ===
    @sync_wrapper
    def list_article_attachments(
        self,
        article_id: str,
        fields: str = "id,name,mimeType,size",
        top: int = 50,
        skip: int = 0,
    ) -> str:
        try:
            if not article_id:
                return format_json_response({"error": "article_id is required"})
            attachments = self.articles_api.list_article_attachments(
                article_id=article_id, fields=fields, top=top, skip=skip
            )
            result = [a.model_dump() if hasattr(a, "model_dump") else a for a in attachments]
            return format_json_response(result)
        except Exception as e:
            logger.exception("Error listing article attachments")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def upload_article_attachment(
        self,
        article_id: str,
        filename: str,
        file_bytes_b64: str,
        mime_type: str = "application/octet-stream",
        fields: str = "id,name,mimeType,size",
    ) -> str:
        """
        Upload an attachment to an article. Expects base64-encoded bytes.
        """
        import base64

        try:
            if not article_id:
                return format_json_response({"error": "article_id is required"})
            if not filename:
                return format_json_response({"error": "filename is required"})
            if not file_bytes_b64:
                return format_json_response({"error": "file_bytes_b64 is required"})
            file_bytes = base64.b64decode(file_bytes_b64)
            attachment = self.articles_api.upload_article_attachment(
                article_id=article_id,
                filename=filename,
                file_bytes=file_bytes,
                mime_type=mime_type,
                fields=fields,
            )
            return format_json_response(
                attachment.model_dump() if hasattr(attachment, "model_dump") else attachment
            )
        except Exception as e:
            logger.exception("Error uploading article attachment")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def download_article_attachment(
        self, article_id: str, attachment_id: str, return_base64: bool = True
    ) -> str:
        """
        Download an attachment. By default returns base64-encoded content.
        """
        import base64

        try:
            if not article_id:
                return format_json_response({"error": "article_id is required"})
            if not attachment_id:
                return format_json_response({"error": "attachment_id is required"})
            data = self.articles_api.download_article_attachment(
                article_id=article_id, attachment_id=attachment_id
            )
            if return_base64:
                return format_json_response({"content_base64": base64.b64encode(data).decode("ascii")})
            return format_json_response({"content": data.decode("utf-8", errors="replace")})
        except Exception as e:
            logger.exception("Error downloading article attachment")
            return format_json_response({"error": str(e)})
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        return {
            "get_article": {
                "description": 'Get a Knowledge Base article by id. Example: get_article(article_id="1-23")',
                "parameter_descriptions": {
                    "article_id": "Internal article id like '1-23'",
                    "fields": "Fields to include (default: id,summary,content,updated,space(id,name))",
                },
            },
            "list_articles": {
                "description": 'List Knowledge Base articles with optional filters. Example: list_articles(space_id="0-1", query="status: published", top=20)',
                "parameter_descriptions": {
                    "space_id": "Optional space id to filter",
                    "query": "Optional search query",
                    "fields": "Fields to include (default: id,summary,updated,space(id,name))",
                    "top": "Max results (default: 20)",
                    "skip": "Offset for pagination (default: 0)",
                },
            },
            "search_articles": {
                "description": 'Search Knowledge Base articles by query. Example: search_articles(query="onboarding")',
                "parameter_descriptions": {
                    "query": "Search query",
                    "fields": "Fields to include (default: id,summary,updated,space(id,name))",
                    "top": "Max results (default: 20)",
                    "skip": "Offset for pagination (default: 0)",
                },
            },
            "search_articles_filtered": {
                "description": 'Search Knowledge Base articles with filters (space, author, tag, status, updatedSince, sort). Example: search_articles_filtered(space_id="0-1", status="published", updated_since="2025-01-01")',
                "parameter_descriptions": {
                    "space_id": "Optional space id to filter",
                    "author": "Optional author id/login",
                    "tag": "Optional tag/label",
                    "status": "Optional status (e.g., draft, published)",
                    "updated_since": "ISO8601 or millis; filters updated from this timestamp",
                    "sort": "Sort expression, e.g., 'updated desc'",
                    "query": "Free text to append",
                    "fields": "Fields to include (default: id,summary,updated,space(id,name))",
                    "top": "Max results (default: 20)",
                    "skip": "Offset for pagination (default: 0)",
                },
            },
            "create_article": {
                "description": "Create a Knowledge Base article.",
                "parameter_descriptions": {
                    "space_id": "Space id (e.g., '0-1')",
                    "summary": "Article title/summary",
                    "content": "Article content (text/HTML/Markdown depending on instance)",
                    "parent_article_id": "Optional parent article id",
                    "status": "Optional status (e.g., draft, published)",
                    "fields": "Fields to include in response",
                    "extra": "Optional map of extra properties",
                },
            },
            "update_article": {
                "description": "Update a Knowledge Base article (send only fields to change).",
                "parameter_descriptions": {
                    "article_id": "Target article id",
                    "summary": "New summary",
                    "content": "New content",
                    "space_id": "Move to space id",
                    "parent_article_id": "Set/move parent article id",
                    "status": "Set status (draft/published)",
                    "fields": "Fields to include in response",
                    "extra": "Optional map of extra properties",
                },
            },
            "set_article_status": {
                "description": "Set article status (e.g., draft, published).",
                "parameter_descriptions": {
                    "article_id": "Target article id",
                    "status": "New status value",
                },
            },
            "list_article_comments": {
                "description": "List comments for an article.",
                "parameter_descriptions": {
                    "article_id": "Target article id",
                    "fields": "Fields to include",
                    "top": "Max results",
                    "skip": "Offset",
                },
            },
            "add_article_comment": {
                "description": "Add a comment to an article.",
                "parameter_descriptions": {
                    "article_id": "Target article id",
                    "text": "Comment text",
                    "fields": "Fields to include",
                },
            },
            "update_article_comment": {
                "description": "Update an article comment.",
                "parameter_descriptions": {
                    "article_id": "Target article id",
                    "comment_id": "Comment id",
                    "text": "Updated text",
                    "fields": "Fields to include",
                },
            },
            "list_article_attachments": {
                "description": "List attachments for an article.",
                "parameter_descriptions": {
                    "article_id": "Target article id",
                    "fields": "Fields to include",
                    "top": "Max results",
                    "skip": "Offset",
                },
            },
            "upload_article_attachment": {
                "description": "Upload an attachment (base64) to an article.",
                "parameter_descriptions": {
                    "article_id": "Target article id",
                    "filename": "Filename to store",
                    "file_bytes_b64": "Base64 file content",
                    "mime_type": "Optional MIME type",
                    "fields": "Fields to include",
                },
            },
            "download_article_attachment": {
                "description": "Download an attachment; returns base64 by default.",
                "parameter_descriptions": {
                    "article_id": "Target article id",
                    "attachment_id": "Attachment id",
                    "return_base64": "If true, returns content_base64; else utf-8 string",
                },
            },
        }
