"""
MCP wrapper functions for YouTrack tools.

This module provides wrapper functions that properly handle parameter formatting
for YouTrack MCP tools to ensure they work correctly with various parameter formats.
"""

import json
import logging
import inspect
from functools import wraps, partial
from typing import Any, Callable, Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)

def sync_wrapper(func: Callable) -> Callable:
    """
    Wrapper for synchronous functions to ensure proper parameter handling.
    
    This wrapper properly extracts parameters from various formats that might be
    passed by MCP tools, including:
    - Named parameters (issue_id="ABC-123")
    - Args string as JSON or raw value
    - Kwargs dictionary or string
    
    Args:
        func: The original function to wrap
        
    Returns:
        Wrapped function that handles parameter extraction
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Log the original parameters for debugging
        logger.debug(f"Original parameters for {func.__name__}: args={args}, kwargs={kwargs}")
        
        # Process the parameters to get the correct format
        processed_args, processed_kwargs = process_parameters(func.__name__, args, kwargs)
        
        # Get the original bound instance if this is a method
        instance = getattr(func, '__self__', None)
        
        # Log the processed parameters for debugging
        logger.debug(f"Calling {func.__name__} with processed args: {processed_args}, kwargs: {processed_kwargs}")
        
        # Call the original function with the processed parameters
        try:
            if instance:
                # For bound methods, we need to ensure the instance is used
                return func(**processed_kwargs)
            else:
                return func(*processed_args, **processed_kwargs)
        except Exception as e:
            logger.exception(f"Error calling {func.__name__}: {str(e)}")
            return json.dumps({
                "error": f"Error calling {func.__name__}: {str(e)}",
                "status": "error"
            })
    
    # Store whether this is a bound method for later reference
    wrapper.is_bound_method = hasattr(func, '__self__')
    wrapper.original_func = func
    
    return wrapper

def process_parameters(func_name: str, args: Tuple, kwargs: Dict[str, Any]) -> Tuple[Tuple, Dict[str, Any]]:
    """
    Process parameters for YouTrack MCP tool functions.
    
    This function handles various parameter formats that might be passed by MCP tools:
    - Direct arguments (user passes issue_id="ABC-123")
    - Args string containing JSON or raw value
    - Kwargs dictionary or string
    
    Args:
        func_name: Name of the function being called
        args: Original positional arguments
        kwargs: Original keyword arguments
        
    Returns:
        Tuple containing processed (args, kwargs)
    """
    processed_args = list(args)
    processed_kwargs = kwargs.copy()
    
    # Handle 'args' parameter specially
    if 'args' in processed_kwargs:
        args_value = processed_kwargs.pop('args')
        logger.debug(f"Processing 'args' parameter: {args_value}")
        
        # Process args_value based on its type
        if isinstance(args_value, str):
            # Try to parse as JSON if it looks like JSON
            if args_value.strip().startswith('{') and args_value.strip().endswith('}'):
                try:
                    args_dict = json.loads(args_value)
                    if isinstance(args_dict, dict):
                        # Add each key-value pair to kwargs
                        for k, v in args_dict.items():
                            processed_kwargs[k] = v
                    else:
                        # Use as first positional argument
                        processed_args.insert(0, args_dict)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse args as JSON: {args_value}. Error: {str(e)}")
                    # Not valid JSON, use as first positional argument only if not empty
                    if args_value.strip():
                        processed_args.insert(0, args_value)
            else:
                # Not JSON-like, use as first positional argument only if not empty
                if args_value.strip():
                    processed_args.insert(0, args_value)
    
    # Handle 'kwargs' parameter specially
    if 'kwargs' in processed_kwargs:
        kwargs_value = processed_kwargs.pop('kwargs')
        logger.debug(f"Processing 'kwargs' parameter: {kwargs_value}")
        
        # Process kwargs_value based on its type
        if isinstance(kwargs_value, str):
            # Try to parse as JSON if it looks like JSON
            if kwargs_value.strip().startswith('{') and kwargs_value.strip().endswith('}'):
                try:
                    kwargs_dict = json.loads(kwargs_value)
                    if isinstance(kwargs_dict, dict):
                        # Add each key-value pair to kwargs
                        for k, v in kwargs_dict.items():
                            processed_kwargs[k] = v
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse kwargs as JSON: {kwargs_value}. Error: {str(e)}")
            elif kwargs_value:
                logger.warning(f"Received kwargs as non-JSON string: {kwargs_value}")
        elif isinstance(kwargs_value, dict):
            # Add each key-value pair to kwargs
            for k, v in kwargs_value.items():
                processed_kwargs[k] = v
    
    # Handle parameter name normalization for all tool functions
    normalized_kwargs = normalize_parameter_names(func_name, processed_kwargs)
    
    return tuple(processed_args), normalized_kwargs

def normalize_parameter_names(func_name: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize parameter names based on common naming conventions and specific tool needs.
    
    Args:
        func_name: Name of the function being called
        kwargs: Original keyword arguments
        
    Returns:
        Dictionary with normalized parameter names
    """
    # Copy kwargs to avoid modifying during iteration
    normalized = kwargs.copy()
    
    # Tool-specific parameter mappings
    # For ProjectTools methods, we want to keep project_id as project_id
    project_tools_methods = [
        'get_project', 'get_project_issues', 'get_custom_fields', 'update_project'
    ]
    
    issue_tools_methods = [
        'create_issue', 'issue_create_issue', 'get_issue', 'add_comment', 'get_issue_raw'
    ]
    
    # Apply mappings based on the function being called
    if func_name in project_tools_methods:
        # For project tools, ensure project is named project_id
        if 'project' in normalized and 'project_id' not in normalized:
            normalized['project_id'] = normalized.pop('project')
    
    elif func_name in issue_tools_methods:
        # For issue tools, ensure project_id is mapped to project
        if 'project_id' in normalized and 'project' not in normalized:
            normalized['project'] = normalized.pop('project_id')
        
        # Also handle project_key for issue tools
        if 'project_key' in normalized and 'project' not in normalized:
            normalized['project'] = normalized.pop('project_key')
        
        # Handle issue_key for issue tools
        if 'issue_key' in normalized and 'issue_id' not in normalized:
            normalized['issue_id'] = normalized.pop('issue_key')
    
    # User tools mappings
    if 'user_id' in normalized and 'user' not in normalized:
        normalized['user'] = normalized.pop('user_id')
    
    if 'user_login' in normalized and 'login' not in normalized:
        normalized['login'] = normalized.pop('user_login')
    
    # Custom field mapping
    if 'custom_field_id' in normalized and 'field_id' not in normalized:
        normalized['field_id'] = normalized.pop('custom_field_id')
    
    # Log the normalized parameters for key functions
    if func_name in project_tools_methods or func_name in issue_tools_methods:
        logger.info(f"{func_name} normalized parameters: {normalized}")
    
    return normalized

def create_bound_tool(instance: Any, method_name: str) -> Callable:
    """
    Create a properly bound tool function from a class instance and method name.
    
    Args:
        instance: The class instance containing the method
        method_name: The name of the method to bind
        
    Returns:
        A properly bound function that can be used as an MCP tool
    """
    # Get the method from the instance
    method = getattr(instance, method_name)
    
    # Create a function that maintains the binding
    @wraps(method)
    def bound_wrapper(*args, **kwargs):
        # Process the parameters to get the correct format
        processed_args, processed_kwargs = process_parameters(method_name, args, kwargs)
        
        # Call the method with the processed parameters
        try:
            return method(**processed_kwargs)
        except Exception as e:
            logger.exception(f"Error calling {method_name}: {str(e)}")
            return json.dumps({
                "error": f"Error calling {method_name}: {str(e)}",
                "status": "error"
            })
    
    # Mark this as a bound method
    bound_wrapper.is_bound_method = True
    bound_wrapper.original_func = method
    bound_wrapper.instance = instance
    
    return bound_wrapper 