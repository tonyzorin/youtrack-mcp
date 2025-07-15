"""
Comprehensive unit tests for YouTrack MCP wrappers.
"""
import pytest
import json
import logging
from unittest.mock import Mock, patch, MagicMock

from youtrack_mcp.mcp_wrappers import (
    sync_wrapper, process_parameters, normalize_parameter_names, create_bound_tool
)


class TestSyncWrapper:
    """Test cases for sync_wrapper function."""
    
    @pytest.mark.unit
    def test_sync_wrapper_basic_function(self):
        """Test sync_wrapper with a basic function."""
        def test_func(param1, param2="default"):
            return f"{param1}-{param2}"
        
        wrapped = sync_wrapper(test_func)
        
        # Test that wrapper preserves function metadata
        assert wrapped.__name__ == "test_func"
        assert hasattr(wrapped, 'is_bound_method')
        assert hasattr(wrapped, 'original_func')
        assert wrapped.original_func is test_func
    
    @pytest.mark.unit
    def test_sync_wrapper_calls_original_function(self):
        """Test that sync_wrapper calls the original function with processed parameters."""
        def test_func(name, value=42):
            return {"name": name, "value": value}
        
        wrapped = sync_wrapper(test_func)
        
        result = wrapped(name="test", value=100)
        assert result == {"name": "test", "value": 100}
    
    @pytest.mark.unit
    def test_sync_wrapper_handles_bound_method(self):
        """Test sync_wrapper with a bound method."""
        class TestClass:
            def test_method(self, param):
                return f"method-{param}"
        
        instance = TestClass()
        wrapped = sync_wrapper(instance.test_method)
        
        result = wrapped(param="value")
        assert result == "method-value"
        assert wrapped.is_bound_method is True
    
    @pytest.mark.unit
    def test_sync_wrapper_handles_exception(self):
        """Test that sync_wrapper handles exceptions properly."""
        def failing_func():
            raise ValueError("Test error")
        
        wrapped = sync_wrapper(failing_func)
        
        result = wrapped()
        
        # Should return JSON error response
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert error_data["status"] == "error"
        assert "Test error" in error_data["error"]
    
    @pytest.mark.unit
    def test_sync_wrapper_with_complex_parameters(self):
        """Test sync_wrapper with complex parameter processing."""
        def test_func(project, issue_id):
            return {"project": project, "issue_id": issue_id}
        
        wrapped = sync_wrapper(test_func)
        
        # Test with JSON args
        result = wrapped(args='{"project": "TEST", "issue_id": "123"}')
        assert result == {"project": "TEST", "issue_id": "123"}


class TestProcessParameters:
    """Test cases for process_parameters function."""
    
    @pytest.mark.unit
    def test_process_parameters_no_special_params(self):
        """Test parameter processing without special 'args' or 'kwargs' parameters."""
        args = ("test1", "test2")
        kwargs = {"param1": "value1", "param2": "value2"}
        
        processed_args, processed_kwargs = process_parameters("test_func", args, kwargs)
        
        assert processed_args == ("test1", "test2")
        assert processed_kwargs == {"param1": "value1", "param2": "value2"}
    
    @pytest.mark.unit
    def test_process_parameters_with_json_args(self):
        """Test parameter processing with JSON args parameter."""
        args = ()
        kwargs = {"args": '{"project": "TEST", "issue_id": "123"}'}
        
        processed_args, processed_kwargs = process_parameters("test_func", args, kwargs)
        
        assert processed_args == ()
        assert processed_kwargs["project"] == "TEST"
        assert processed_kwargs["issue_id"] == "123"
        assert "args" not in processed_kwargs
    
    @pytest.mark.unit
    def test_process_parameters_with_non_json_args(self):
        """Test parameter processing with non-JSON args parameter."""
        args = ()
        kwargs = {"args": "simple_value"}
        
        processed_args, processed_kwargs = process_parameters("test_func", args, kwargs)
        
        assert processed_args == ("simple_value",)
        assert "args" not in processed_kwargs
    
    @pytest.mark.unit
    def test_process_parameters_with_empty_args(self):
        """Test parameter processing with empty args parameter."""
        args = ()
        kwargs = {"args": ""}
        
        processed_args, processed_kwargs = process_parameters("test_func", args, kwargs)
        
        assert processed_args == ()
        assert "args" not in processed_kwargs
    
    @pytest.mark.unit
    def test_process_parameters_with_invalid_json_args(self):
        """Test parameter processing with invalid JSON in args."""
        args = ()
        kwargs = {"args": '{"invalid": json}'}  # Looks like JSON but is invalid
        
        with patch('youtrack_mcp.mcp_wrappers.logger') as mock_logger:
            processed_args, processed_kwargs = process_parameters("test_func", args, kwargs)
        
        # Should fall back to using as string argument
        assert processed_args == ('{"invalid": json}',)
        assert "args" not in processed_kwargs
        # Check that warning was called with correct message
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Failed to parse args as JSON" in call_args
    
    @pytest.mark.unit
    def test_process_parameters_with_json_kwargs(self):
        """Test parameter processing with JSON kwargs parameter."""
        args = ()
        kwargs = {"kwargs": '{"param1": "value1", "param2": "value2"}'}
        
        processed_args, processed_kwargs = process_parameters("test_func", args, kwargs)
        
        assert processed_args == ()
        assert processed_kwargs["param1"] == "value1"
        assert processed_kwargs["param2"] == "value2"
        assert "kwargs" not in processed_kwargs
    
    @pytest.mark.unit
    def test_process_parameters_with_dict_kwargs(self):
        """Test parameter processing with dictionary kwargs parameter."""
        args = ()
        kwargs = {"kwargs": {"param1": "value1", "param2": "value2"}}
        
        processed_args, processed_kwargs = process_parameters("test_func", args, kwargs)
        
        assert processed_args == ()
        assert processed_kwargs["param1"] == "value1"
        assert processed_kwargs["param2"] == "value2"
        assert "kwargs" not in processed_kwargs
    
    @pytest.mark.unit
    def test_process_parameters_with_invalid_json_kwargs(self):
        """Test parameter processing with invalid JSON in kwargs."""
        args = ()
        kwargs = {"kwargs": '{"invalid": json'}
        
        with patch('youtrack_mcp.mcp_wrappers.logger') as mock_logger:
            processed_args, processed_kwargs = process_parameters("test_func", args, kwargs)
        
        assert processed_args == ()
        assert "kwargs" not in processed_kwargs
        mock_logger.warning.assert_called()
    
    @pytest.mark.unit
    def test_process_parameters_with_non_json_string_kwargs(self):
        """Test parameter processing with non-JSON string kwargs."""
        args = ()
        kwargs = {"kwargs": "simple_string"}
        
        with patch('youtrack_mcp.mcp_wrappers.logger') as mock_logger:
            processed_args, processed_kwargs = process_parameters("test_func", args, kwargs)
        
        assert processed_args == ()
        assert "kwargs" not in processed_kwargs
        mock_logger.warning.assert_called()
    
    @pytest.mark.unit
    def test_process_parameters_normalization_called(self):
        """Test that parameter normalization is called."""
        args = ()
        kwargs = {"project_id": "TEST"}
        
        with patch('youtrack_mcp.mcp_wrappers.normalize_parameter_names') as mock_normalize:
            mock_normalize.return_value = {"project": "TEST"}
            
            processed_args, processed_kwargs = process_parameters("create_issue", args, kwargs)
            
            mock_normalize.assert_called_once_with("create_issue", {"project_id": "TEST"})
            assert processed_kwargs == {"project": "TEST"}


class TestNormalizeParameterNames:
    """Test cases for normalize_parameter_names function."""
    
    @pytest.mark.unit
    def test_normalize_project_tools_parameters(self):
        """Test parameter normalization for project tools methods."""
        kwargs = {"project": "TEST"}
        
        result = normalize_parameter_names("get_project", kwargs)
        
        assert result == {"project_id": "TEST"}
        assert "project" not in result
    
    @pytest.mark.unit
    def test_normalize_issue_tools_project_parameter(self):
        """Test parameter normalization for issue tools project parameter."""
        kwargs = {"project_id": "TEST"}
        
        result = normalize_parameter_names("create_issue", kwargs)
        
        assert result == {"project": "TEST"}
        assert "project_id" not in result
    
    @pytest.mark.unit
    def test_normalize_issue_tools_project_key_parameter(self):
        """Test parameter normalization for issue tools project_key parameter."""
        kwargs = {"project_key": "TEST"}
        
        result = normalize_parameter_names("create_issue", kwargs)
        
        assert result == {"project": "TEST"}
        assert "project_key" not in result
    
    @pytest.mark.unit
    def test_normalize_issue_tools_issue_key_parameter(self):
        """Test parameter normalization for issue tools issue_key parameter."""
        kwargs = {"issue_key": "TEST-123"}
        
        result = normalize_parameter_names("get_issue", kwargs)
        
        assert result == {"issue_id": "TEST-123"}
        assert "issue_key" not in result
    
    @pytest.mark.unit
    def test_normalize_user_parameters(self):
        """Test parameter normalization for user-related parameters."""
        kwargs = {"user_id": "user123", "user_login": "john.doe"}
        
        result = normalize_parameter_names("get_user", kwargs)
        
        assert result == {"user": "user123", "login": "john.doe"}
        assert "user_id" not in result
        assert "user_login" not in result
    
    @pytest.mark.unit
    def test_normalize_custom_field_parameters(self):
        """Test parameter normalization for custom field parameters."""
        kwargs = {"custom_field_id": "field123"}
        
        result = normalize_parameter_names("get_custom_field", kwargs)
        
        assert result == {"field_id": "field123"}
        assert "custom_field_id" not in result
    
    @pytest.mark.unit
    def test_normalize_no_changes_needed(self):
        """Test parameter normalization when no changes are needed."""
        kwargs = {"summary": "Test issue", "description": "Test description"}
        
        result = normalize_parameter_names("create_issue", kwargs)
        
        assert result == {"summary": "Test issue", "description": "Test description"}
    
    @pytest.mark.unit
    def test_normalize_preserves_existing_preferred_names(self):
        """Test that normalization doesn't override existing preferred parameter names."""
        # If both project_id and project exist, keep both (no conversion happens)
        kwargs = {"project_id": "OLD", "project": "NEW"}
        
        result = normalize_parameter_names("create_issue", kwargs)
        
        # Should keep both since project already exists (no conversion)
        assert result == {"project": "NEW", "project_id": "OLD"}
    
    @pytest.mark.unit
    def test_normalize_logs_important_functions(self):
        """Test that normalization logs for important functions."""
        kwargs = {"project_id": "TEST"}
        
        with patch('youtrack_mcp.mcp_wrappers.logger') as mock_logger:
            result = normalize_parameter_names("create_issue", kwargs)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "create_issue normalized parameters" in call_args
    
    @pytest.mark.unit
    def test_normalize_multiple_mappings(self):
        """Test parameter normalization with multiple mappings."""
        kwargs = {
            "project_id": "TEST",
            "issue_key": "TEST-123", 
            "user_id": "user123",
            "custom_field_id": "field456"
        }
        
        result = normalize_parameter_names("create_issue", kwargs)
        
        expected = {
            "project": "TEST",
            "issue_id": "TEST-123",
            "user": "user123", 
            "field_id": "field456"
        }
        assert result == expected


class TestCreateBoundTool:
    """Test cases for create_bound_tool function."""
    
    @pytest.mark.unit
    def test_create_bound_tool_basic(self):
        """Test creating a bound tool from an instance method."""
        class TestClass:
            def test_method(self, param):
                return f"bound-{param}"
        
        instance = TestClass()
        bound_tool = create_bound_tool(instance, "test_method")
        
        # Test that bound tool has proper attributes
        assert hasattr(bound_tool, 'is_bound_method')
        assert hasattr(bound_tool, 'original_func')
        assert hasattr(bound_tool, 'instance')
        assert bound_tool.is_bound_method is True
        assert bound_tool.instance is instance
        assert bound_tool.__name__ == "test_method"
    
    @pytest.mark.unit
    def test_create_bound_tool_calls_method(self):
        """Test that bound tool calls the original method correctly."""
        class TestClass:
            def test_method(self, name, value=42):
                return {"name": name, "value": value, "class": "TestClass"}
        
        instance = TestClass()
        bound_tool = create_bound_tool(instance, "test_method")
        
        result = bound_tool(name="test", value=100)
        assert result == {"name": "test", "value": 100, "class": "TestClass"}
    
    @pytest.mark.unit
    def test_create_bound_tool_parameter_processing(self):
        """Test that bound tool processes parameters correctly."""
        class TestClass:
            def test_method(self, project, issue_id):
                return {"project": project, "issue_id": issue_id}
        
        instance = TestClass()
        bound_tool = create_bound_tool(instance, "test_method")
        
        # Test with processed parameters
        result = bound_tool(args='{"project": "TEST", "issue_id": "123"}')
        assert result == {"project": "TEST", "issue_id": "123"}
    
    @pytest.mark.unit
    def test_create_bound_tool_handles_exception(self):
        """Test that bound tool handles exceptions properly."""
        class TestClass:
            def failing_method(self):
                raise RuntimeError("Method error")
        
        instance = TestClass()
        bound_tool = create_bound_tool(instance, "failing_method")
        
        result = bound_tool()
        
        # Should return JSON error response
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert error_data["status"] == "error"
        assert "Method error" in error_data["error"]
    
    @pytest.mark.unit
    def test_create_bound_tool_preserves_method_binding(self):
        """Test that bound tool preserves method binding correctly."""
        class TestClass:
            def __init__(self, name):
                self.name = name
            
            def get_name(self):
                return self.name
        
        instance = TestClass("test_instance")
        bound_tool = create_bound_tool(instance, "get_name")
        
        result = bound_tool()
        assert result == "test_instance"
    
    @pytest.mark.unit
    def test_create_bound_tool_with_parameter_normalization(self):
        """Test bound tool with parameter normalization for different tool types."""
        class ProjectClass:
            def get_project(self, project_id):
                return {"project_id": project_id}
        
        class IssueClass:
            def create_issue(self, project):
                return {"project": project}
        
        # Test project tool (project -> project_id)
        project_instance = ProjectClass()
        project_tool = create_bound_tool(project_instance, "get_project")
        result = project_tool(project="TEST")  # Should normalize to project_id
        assert result == {"project_id": "TEST"}
        
        # Test issue tool (project_id -> project)
        issue_instance = IssueClass()
        issue_tool = create_bound_tool(issue_instance, "create_issue")
        result = issue_tool(project_id="TEST")  # Should normalize to project
        assert result == {"project": "TEST"}


class TestIntegrationScenarios:
    """Integration test scenarios for MCP wrappers."""
    
    @pytest.mark.unit
    def test_full_workflow_project_tool(self):
        """Test full workflow for a project tool."""
        class ProjectTools:
            def get_project(self, project_id):
                return {"id": project_id, "name": f"Project {project_id}"}
        
        instance = ProjectTools()
        
        # Test sync_wrapper
        wrapped_method = sync_wrapper(instance.get_project)
        result = wrapped_method(project="TEST")
        assert result == {"id": "TEST", "name": "Project TEST"}
        
        # Test create_bound_tool
        bound_tool = create_bound_tool(instance, "get_project")
        result = bound_tool(project="TEST")
        assert result == {"id": "TEST", "name": "Project TEST"}
    
    @pytest.mark.unit
    def test_full_workflow_issue_tool(self):
        """Test full workflow for an issue tool."""
        class IssueTools:
            def create_issue(self, project, summary):
                return {"project": project, "summary": summary, "id": f"{project}-1"}
        
        instance = IssueTools()
        
        # Test with JSON args
        bound_tool = create_bound_tool(instance, "create_issue")
        result = bound_tool(args='{"project_id": "TEST", "summary": "New issue"}')
        
        # project_id should be normalized to project
        assert result == {"project": "TEST", "summary": "New issue", "id": "TEST-1"}
    
    @pytest.mark.unit  
    def test_complex_parameter_scenarios(self):
        """Test complex parameter processing scenarios."""
        class ComplexTools:
            def complex_method(self, project_id, user, field_id):
                return {
                    "project_id": project_id,
                    "user": user,
                    "field_id": field_id
                }
        
        instance = ComplexTools()
        bound_tool = create_bound_tool(instance, "complex_method")
        
        # Test with mixed parameter names that need normalization
        result = bound_tool(
            project_id="TEST",        # Stays as project_id (not an issue tool method)
            user_id="user456",        # -> user (general mapping)
            custom_field_id="field789" # -> field_id (general mapping)
        )
        
        # For non-specific tool methods, only general normalizations apply
        # issue_key normalization only happens for issue tool methods
        expected = {
            "project_id": "TEST",     # project_id stays as is since not in specific lists
            "user": "user456",        # user_id -> user (general mapping)
            "field_id": "field789"    # custom_field_id -> field_id (general mapping)
        }
        assert result == expected 

    @pytest.mark.unit
    def test_json_parsing_error_in_kwargs(self):
        """Test handling of invalid JSON in kwargs parameter."""
        class TestTools:
            def test_method(self, project="default"):
                return {"project": project}
        
        instance = TestTools()
        bound_tool = create_bound_tool(instance, "test_method")
        
        # Test invalid JSON in kwargs - should trigger line 129-130
        with patch('youtrack_mcp.mcp_wrappers.logger') as mock_logger:
            result = bound_tool(kwargs='{"invalid": json}')  # Invalid JSON syntax
            
            # Should log warning about JSON parsing failure
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Failed to parse kwargs as JSON" in warning_call
            
            # Should use default parameter since kwargs parsing failed
            assert result == {"project": "default"}

    @pytest.mark.unit
    def test_non_json_kwargs_string_warning(self):
        """Test warning for non-JSON string in kwargs parameter."""
        class TestTools:
            def test_method(self, project="default"):
                return {"project": project}
        
        instance = TestTools()
        bound_tool = create_bound_tool(instance, "test_method")
        
        # Test non-JSON string in kwargs - should trigger warning after line 130
        with patch('youtrack_mcp.mcp_wrappers.logger') as mock_logger:
            result = bound_tool(kwargs='not json at all')
            
            # Should log warning about non-JSON string
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Received kwargs as non-JSON string" in warning_call
            
            # Should use default parameter since kwargs was not processed
            assert result == {"project": "default"} 