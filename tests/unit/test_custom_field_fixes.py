"""Test custom field update fixes."""

import pytest
from unittest.mock import Mock, patch
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.api.projects import ProjectsClient
from youtrack_mcp.api.client import YouTrackClient

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestCustomFieldUpdateFixes:
    """Test the fixes for custom field updates."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock YouTrack client."""
        return Mock(spec=YouTrackClient)

    @pytest.fixture
    def issues_client(self, mock_client):
        """Create an IssuesClient with mocked dependencies."""
        return IssuesClient(mock_client)

    @pytest.fixture
    def projects_client(self, mock_client):
        """Create a ProjectsClient with mocked dependencies."""
        return ProjectsClient(mock_client)

    def test_format_custom_field_value_with_id_state_field(self, issues_client):
        """Test formatting state field values with field ID."""
        result = issues_client._format_custom_field_value_with_id("state-field-id", "Open")
        
        expected = {
            "$type": "StateIssueCustomField",
            "id": "state-field-id",
            "value": {"name": "Open", "$type": "StateBundleElement"}
        }
        assert result == expected

    def test_format_custom_field_value_with_id_user_field(self, issues_client):
        """Test formatting user field values with field ID."""
        result = issues_client._format_custom_field_value_with_id("assignee-field-id", "john.doe")
        
        expected = {
            "$type": "SingleUserIssueCustomField",
            "id": "assignee-field-id",
            "value": {"login": "john.doe", "$type": "User"}
        }
        assert result == expected

    def test_format_custom_field_value_with_id_period_field(self, issues_client):
        """Test formatting period field values."""
        result = issues_client._format_custom_field_value_with_id("time-field-id", "PT2H30M")
        
        expected = {
            "$type": "SingleEnumIssueCustomField",
            "id": "time-field-id",
            "value": {"presentation": "PT2H30M", "$type": "PeriodValue"}
        }
        assert result == expected

    def test_format_custom_field_value_with_id_numeric_field(self, issues_client):
        """Test formatting numeric field values."""
        result = issues_client._format_custom_field_value_with_id("priority-field-id", 5)
        
        expected = {
            "$type": "SingleEnumIssueCustomField",
            "id": "priority-field-id",
            "value": {"name": "5", "$type": "EnumBundleElement"}
        }
        assert result == expected

    def test_format_custom_field_value_with_id_null_value(self, issues_client):
        """Test formatting null values."""
        result = issues_client._format_custom_field_value_with_id("any-field-id", None)
        
        expected = {
            "$type": "SingleEnumIssueCustomField",
            "id": "any-field-id",
            "value": None
        }
        assert result == expected

    def test_get_custom_field_id_success(self, issues_client, mock_client):
        """Test successfully getting field ID from project."""
        mock_client.get.return_value = [
            {
                "field": {
                    "id": "priority-field-id",
                    "name": "Priority"
                }
            },
            {
                "field": {
                    "id": "state-field-id", 
                    "name": "State"
                }
            }
        ]
        
        field_id = issues_client._get_custom_field_id("DEMO", "Priority")
        assert field_id == "priority-field-id"
        mock_client.get.assert_called_with("admin/projects/DEMO/customFields?fields=field(id,name,fieldType($type,valueType,id)),canBeEmpty,autoAttached")

    def test_get_custom_field_id_not_found(self, issues_client, mock_client):
        """Test field ID not found."""
        mock_client.get.return_value = [
            {
                "field": {
                    "id": "other-field-id",
                    "name": "Other Field"
                }
            }
        ]
        
        field_id = issues_client._get_custom_field_id("DEMO", "NonExistent")
        assert field_id is None

    def test_get_custom_field_id_api_error(self, issues_client, mock_client):
        """Test API error when getting field ID."""
        mock_client.get.side_effect = Exception("API Error")
        
        field_id = issues_client._get_custom_field_id("DEMO", "Priority")
        assert field_id is None

    def test_update_issue_custom_fields_uses_commands_api(
        self, issues_client, mock_client
    ):
        """Test that update_issue_custom_fields uses Commands API correctly."""
        # Mock the issue response for project extraction (when validate=True)  
        mock_client.get.return_value = {
            "id": "DEMO-123", 
            "project": {"id": "DEMO", "shortName": "DEMO"}
        }
        
        # Mock successful command execution
        mock_client.post.return_value = {"success": True}
        
        # Call the method with validation disabled (simpler test case)
        custom_fields = {"Priority": "High", "Assignee": "john.doe"}
        result = issues_client.update_issue_custom_fields("DEMO-123", custom_fields, validate=False)
        
        # Verify Commands API was called with correct format
        mock_client.post.assert_called_with(
            "commands", 
            data={
                "query": "Priority High Assignee john.doe",
                "issues": [{"idReadable": "DEMO-123"}]
            }
        )
        
        # Verify get_issue was called to return updated issue
        mock_client.get.assert_called()
        
        # Result should be the issue object
        assert hasattr(result, 'id') or isinstance(result, dict)

    def test_get_custom_field_schema_with_detailed_query(self, projects_client, mock_client):
        """Test enhanced schema retrieval with detailed field query."""
        mock_client.get.return_value = [
            {
                "field": {
                    "id": "priority-field-id",
                    "name": "Priority",
                    "fieldType": {
                        "$type": "EnumBundle",
                        "valueType": "enum",
                        "id": "enum-bundle-123"
                    },
                    "isMultiValue": False
                },
                "canBeEmpty": False,
                "autoAttached": True
            }
        ]
        
        with patch.object(projects_client, 'get_custom_field_allowed_values', return_value=[]):
            schema = projects_client.get_custom_field_schema("DEMO", "Priority")
        
        expected_schema = {
            "name": "Priority",
            "type": "enum",
            "bundle_type": "EnumBundle",
            "required": True,
            "multi_value": False,
            "auto_attach": True,
            "field_id": "priority-field-id",
            "bundle_id": "enum-bundle-123",
            "allowed_values": []
        }
        
        assert schema == expected_schema
        
        # Verify detailed query was used
        expected_query = "field(id,name,fieldType($type,valueType,id)),canBeEmpty,autoAttached"
        mock_client.get.assert_called_with(f"admin/projects/DEMO/customFields?fields={expected_query}")

    def test_get_custom_field_allowed_values_enum_bundle(self, projects_client, mock_client):
        """Test getting allowed values for enum bundle."""
        # Mock the field schema response
        mock_client.get.side_effect = [
            # First call - get field schema
            [
                {
                    "field": {
                        "id": "priority-field-id",
                        "name": "Priority",
                        "fieldType": {
                            "$type": "EnumBundle",
                            "valueType": "enum",
                            "id": "enum-bundle-123"
                        }
                    }
                }
            ],
            # Second call - get bundle values
            {
                "values": [
                    {
                        "id": "value-1",
                        "name": "High",
                        "description": "High priority",
                        "color": {"background": "#ff0000"}
                    },
                    {
                        "id": "value-2", 
                        "name": "Low",
                        "description": "Low priority",
                        "color": {"background": "#00ff00"}
                    }
                ]
            }
        ]
        
        values = projects_client.get_custom_field_allowed_values("DEMO", "Priority")
        
        expected_values = [
            {
                "name": "High",
                "description": "High priority", 
                "id": "value-1",
                "color": {"background": "#ff0000"}
            },
            {
                "name": "Low",
                "description": "Low priority",
                "id": "value-2", 
                "color": {"background": "#00ff00"}
            }
        ]
        
        assert values == expected_values
        
        # Verify the bundle API call
        assert mock_client.get.call_count == 2
        mock_client.get.assert_any_call("admin/customFieldSettings/bundles/enum/enum-bundle-123?fields=values(id,name,description,color)")

    def test_get_custom_field_allowed_values_state_bundle(self, projects_client, mock_client):
        """Test getting allowed values for state bundle."""
        # Mock the field schema response  
        mock_client.get.side_effect = [
            # First call - get field schema
            [
                {
                    "field": {
                        "id": "state-field-id",
                        "name": "State", 
                        "fieldType": {
                            "$type": "StateMachineBundle",
                            "valueType": "state",
                            "id": "state-bundle-456"
                        }
                    }
                }
            ],
            # Second call - get bundle values
            {
                "values": [
                    {
                        "id": "state-1",
                        "name": "Open",
                        "description": "Issue is open",
                        "isResolved": False,
                        "color": {"background": "#0000ff"}
                    },
                    {
                        "id": "state-2",
                        "name": "Closed", 
                        "description": "Issue is closed",
                        "isResolved": True,
                        "color": {"background": "#808080"}
                    }
                ]
            }
        ]
        
        values = projects_client.get_custom_field_allowed_values("DEMO", "State")
        
        expected_values = [
            {
                "name": "Open",
                "description": "Issue is open",
                "id": "state-1", 
                "resolved": False,
                "color": {"background": "#0000ff"}
            },
            {
                "name": "Closed",
                "description": "Issue is closed", 
                "id": "state-2",
                "resolved": True,
                "color": {"background": "#808080"}
            }
        ]
        
        assert values == expected_values

    def test_get_custom_field_allowed_values_user_bundle(self, projects_client, mock_client):
        """Test getting allowed values for user bundle."""
        # Mock the field schema response
        mock_client.get.side_effect = [
            # First call - get field schema
            [
                {
                    "field": {
                        "id": "assignee-field-id",
                        "name": "Assignee",
                        "fieldType": {
                            "$type": "UserBundle", 
                            "valueType": "user",
                            "id": "user-bundle-789"
                        }
                    }
                }
            ],
            # Second call - get users
            [
                {
                    "id": "user-1",
                    "login": "john.doe",
                    "name": "John Doe",
                    "email": "john.doe@example.com"
                },
                {
                    "id": "user-2", 
                    "login": "jane.smith",
                    "name": "Jane Smith",
                    "email": "jane.smith@example.com"
                }
            ]
        ]
        
        values = projects_client.get_custom_field_allowed_values("DEMO", "Assignee")
        
        expected_values = [
            {
                "name": "John Doe",
                "login": "john.doe",
                "id": "user-1",
                "email": "john.doe@example.com"
            },
            {
                "name": "Jane Smith", 
                "login": "jane.smith",
                "id": "user-2",
                "email": "jane.smith@example.com"
            }
        ]
        
        assert values == expected_values
        
        # Verify the users API call
        mock_client.get.assert_any_call("users?fields=id,login,name,email")

    def test_get_custom_field_allowed_values_field_not_found(self, projects_client, mock_client):
        """Test when custom field is not found."""
        mock_client.get.return_value = [
            {
                "field": {
                    "id": "other-field-id",
                    "name": "Other Field"
                }
            }
        ]
        
        values = projects_client.get_custom_field_allowed_values("DEMO", "NonExistent")
        assert values == []

    def test_get_custom_field_allowed_values_no_bundle_id(self, projects_client, mock_client):
        """Test when field has no bundle ID."""
        mock_client.get.return_value = [
            {
                "field": {
                    "id": "text-field-id",
                    "name": "Description",
                    "fieldType": {
                        "$type": "StringFieldType",
                        "valueType": "string"
                        # No bundle ID for string fields
                    }
                }
            }
        ]
        
        values = projects_client.get_custom_field_allowed_values("DEMO", "Description")
        assert values == []

    def test_get_custom_field_allowed_values_api_error(self, projects_client, mock_client):
        """Test API error handling."""
        mock_client.get.side_effect = Exception("API Error")
        
        values = projects_client.get_custom_field_allowed_values("DEMO", "Priority")
        assert values == [] 