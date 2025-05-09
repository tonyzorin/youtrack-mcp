"""
MCP server implementation for YouTrack.
"""
import json
import logging
import os
import sys
import inspect
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union, AsyncGenerator

try:
    # Try importing from mcp_sdk (new package name)
    from mcp_sdk.server import ToolServerBase
except ImportError:
    # Fall back to mcp (old package name)
    from mcp.server.fastmcp import FastMCP as ToolServerBase

from youtrack_mcp.config import config

logger = logging.getLogger(__name__)


class YouTrackMCPServer:
    """MCP server for YouTrack integration."""
    
    def __init__(self, transport: Optional[str] = None):
        """
        Initialize the YouTrack MCP server.
        
        Args:
            transport: The transport to use ('http', 'stdio', or None to auto-detect)
        """
        # Auto-detect transport if not specified
        if transport is None:
            # Use STDIO when running in a pipe (for Claude integration)
            if not sys.stdin.isatty() or not sys.stdout.isatty():
                transport = 'stdio'
            else:
                transport = 'http'
        
        logger.info(f"Initializing YouTrack MCP server with {transport} transport")
        
        # Store the transport mode for later reference
        self.transport_mode = transport
        
        # Initialize server with ToolServerBase
        self.server = ToolServerBase(
            name=config.MCP_SERVER_NAME,
            instructions=config.MCP_SERVER_DESCRIPTION,
            transport=transport  # ToolServerBase expects 'transport' parameter
        )
        
        # Initialize tool registry
        self._tools: Dict[str, Callable] = {}
        
        # Keep track of registered tool names to prevent duplication
        self._registered_tools = set()
        
    def _generate_tool_schema(self, func: Callable, name: str, description: str, 
                        parameter_descriptions: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate a JSON schema for a tool based on its function signature.
        
        Args:
            func: The tool function
            name: The tool name
            description: Tool description
            parameter_descriptions: Descriptions for the parameters
            
        Returns:
            A JSON Schema object describing the tool
        """
        schema = {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # Get function signature to determine parameter properties
        sig = inspect.signature(func)
        
        for param_name, param in sig.parameters.items():
            # Skip self parameter for class methods
            if param_name == 'self':
                continue
                
            # Determine if parameter is required
            is_required = param.default == inspect.Parameter.empty
            
            # Get parameter type
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                param_type = Any  # Default to Any if not specified
                
            # Convert Python types to JSON Schema types
            schema_type = "string"  # Default to string
            
            # Handle common types
            if param_type in (int, float) or (hasattr(param_type, "__origin__") and param_type.__origin__ in (int, float)):
                schema_type = "number"
            elif param_type == bool or (hasattr(param_type, "__origin__") and param_type.__origin__ == bool):
                schema_type = "boolean"
            elif param_type in (dict, Dict) or (hasattr(param_type, "__origin__") and param_type.__origin__ in (dict, Dict)):
                schema_type = "object"
            elif param_type in (list, List) or (hasattr(param_type, "__origin__") and param_type.__origin__ in (list, List)):
                schema_type = "array"
                
            # Get description from parameter_descriptions or default
            param_description = parameter_descriptions.get(param_name, f"Parameter {param_name}")
            
            # Add parameter to schema
            schema["parameters"]["properties"][param_name] = {
                "type": schema_type,
                "description": param_description
            }
            
            # Add to required list if necessary
            if is_required:
                schema["parameters"]["required"].append(param_name)
        
        return schema
        
    def register_tool(self, name: str, func: Callable, description: str, 
                     parameter_descriptions: Optional[Dict[str, str]] = None,
                     should_stream: bool = True) -> None:
        """
        Register a tool with the MCP server.
        
        Args:
            name: The tool name
            func: The tool function
            description: Description of what the tool does
            parameter_descriptions: Optional descriptions for function parameters
            should_stream: Whether this tool should use streaming (when supported)
        """
        # Skip if tool already registered
        if name in self._registered_tools:
            logger.debug(f"Tool {name} already registered, skipping")
            return
            
        # Track that this tool has been registered
        self._registered_tools.add(name)
        
        # Use empty dict if parameter_descriptions is None
        if parameter_descriptions is None:
            parameter_descriptions = {}
        
        # Generate JSON Schema for the tool
        schema = self._generate_tool_schema(
            func=func,
            name=name,
            description=description,
            parameter_descriptions=parameter_descriptions
        )
        
        # Wrap function to handle errors and ensure proper MCP protocol format
        wrapped_func = self._wrap_tool_function(func, name, should_stream)
        
        self._tools[name] = wrapped_func
        
        # Get parameter information from function signature
        parameters = []
        required_parameters = []
        
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            is_required = param.default == inspect.Parameter.empty
            param_type = str(param.annotation).replace("<class '", "").replace("'>", "")
            if param_type == 'inspect._empty':
                param_type = 'Any'
                
            param_desc = parameter_descriptions.get(param_name, f"Parameter {param_name}")
            
            # Create a descriptive parameter entry
            param_info = {
                "name": param_name,
                "type": param_type,
                "required": is_required,
                "description": param_desc
            }
            
            parameters.append(param_info)
            if is_required:
                required_parameters.append(param_name)
        
        # Enhance description with parameter information
        enhanced_description = description
        if parameters:
            param_docs = "\n\nParameters:\n"
            for p in parameters:
                req_text = " (required)" if p["required"] else " (optional)"
                param_docs += f"- {p['name']}: {p['description']}{req_text}\n"
            enhanced_description += param_docs
            
        # Create example usage
        example_usage = f"\n\nExample usage:\n```\n{name}("
        example_params = []
        
        for p in parameters:
            if p["type"] == "str":
                example_params.append(f'{p["name"]}="example"')
            elif p["type"] == "int":
                example_params.append(f'{p["name"]}=10')
            elif p["type"] == "bool":
                example_params.append(f'{p["name"]}=True')
            elif p["type"] == "Optional[str]":
                continue  # Skip optional string params in example
            else:
                example_params.append(f'{p["name"]}=...')
                
        example_usage += ", ".join(example_params) + ")\n```"
        enhanced_description += example_usage
        
        # Store schema in the wrapped function for access later
        wrapped_func.tool_schema = schema
        
        # Register with MCP server with the enhanced description
        self.server.add_tool(
            name=name,
            description=enhanced_description,
            fn=wrapped_func
        )
        
        # Log at debug level instead of info to reduce noise
        logger.debug(f"Registered tool: {name} (streaming: {should_stream})")
        if required_parameters:
            logger.debug(f"  Required parameters: {', '.join(required_parameters)}")
    
    def _wrap_tool_function(self, func: Callable, name: str, should_stream: bool = True) -> Callable:
        """
        Wrap a tool function to handle errors and ensure proper MCP protocol format.
        
        Args:
            func: The original tool function
            name: The tool name
            should_stream: Whether this function should use streaming
            
        Returns:
            A wrapped function that handles errors and ensures proper output format
        """
        # Check if function is async
        is_async = inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func)
        
        async def async_wrapper(*args, **kwargs):
            """Async wrapper for tool functions."""
            try:
                logger.debug(f"Tool {name} called with args={args}, kwargs={kwargs}")
                
                # MCP-specific parameter handling
                # MCP often passes parameters as string in 'args' and 'kwargs' fields
                processed_args = []
                processed_kwargs = {}
                
                # Handle 'args' parameter (common in MCP calls)
                if 'args' in kwargs and not args:
                    args_value = kwargs.pop('args')
                    
                    # If args is a string containing multiple arguments
                    if isinstance(args_value, str):
                        # Try to parse as positional arguments
                        if args_value and not args_value.startswith('{'):
                            # Split by space but respect quoted strings
                            import shlex
                            try:
                                processed_args = shlex.split(args_value)
                            except Exception:
                                # If parsing fails, treat as a single argument
                                processed_args = [args_value]
                        # If it looks like JSON, try to parse it
                        elif args_value.startswith('{') and args_value.endswith('}'):
                            try:
                                args_dict = json.loads(args_value)
                                # If it's a dict, treat as kwargs
                                if isinstance(args_dict, dict):
                                    for k, v in args_dict.items():
                                        processed_kwargs[k] = v
                                else:
                                    # If not a dict, treat as a single arg
                                    processed_args = [args_value]
                            except json.JSONDecodeError:
                                # If parsing fails, treat as a single argument
                                processed_args = [args_value]
                        else:
                            # Default: treat as a single argument
                            processed_args = [args_value]
                    # If args is already a list or tuple
                    elif isinstance(args_value, (list, tuple)):
                        processed_args = list(args_value)
                    # Other types: pass as a single argument
                    else:
                        processed_args = [args_value]
                else:
                    # Use original args if no 'args' parameter
                    processed_args = list(args)
                
                # Handle 'kwargs' parameter (common in MCP calls)
                if 'kwargs' in kwargs:
                    kwargs_value = kwargs.pop('kwargs')
                    
                    # If kwargs is a string, try to parse as JSON
                    if isinstance(kwargs_value, str):
                        if kwargs_value.startswith('{') and kwargs_value.endswith('}'):
                            try:
                                kwargs_dict = json.loads(kwargs_value)
                                if isinstance(kwargs_dict, dict):
                                    for k, v in kwargs_dict.items():
                                        processed_kwargs[k] = v
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse kwargs as JSON: {kwargs_value}")
                        else:
                            # Try key=value format
                            parts = kwargs_value.split(',')
                            for part in parts:
                                if '=' in part:
                                    k, v = part.split('=', 1)
                                    processed_kwargs[k.strip()] = v.strip()
                    # If kwargs is already a dict
                    elif isinstance(kwargs_value, dict):
                        processed_kwargs.update(kwargs_value)
                
                # Add remaining kwargs
                processed_kwargs.update(kwargs)
                
                # Debug log the processed parameters
                logger.debug(f"Tool {name} processed parameters: args={processed_args}, kwargs={processed_kwargs}")
                
                # Get the signature of the target function
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if 'self' in param_names:
                    param_names.remove('self')
                
                # Special handling for specific tools
                if name in ('get_issue', 'add_comment', 'create_issue'):
                    # For these tools, we need to ensure the right parameter format
                    # YouTrack expects specific positional parameters
                    if name == 'get_issue' and not processed_kwargs.get('issue_id') and processed_args:
                        # If issue_id is missing but we have a positional arg, use it as issue_id
                        processed_kwargs['issue_id'] = processed_args[0]
                        processed_args = []
                    
                    elif name == 'add_comment':
                        # For add_comment, we need issue_id and text
                        if len(processed_args) >= 2:
                            processed_kwargs['issue_id'] = processed_args[0]
                            processed_kwargs['text'] = processed_args[1]
                            processed_args = []
                        elif len(processed_args) == 1 and not processed_kwargs.get('issue_id'):
                            processed_kwargs['issue_id'] = processed_args[0]
                            processed_args = []
                    
                    elif name == 'create_issue':
                        # For create_issue, we need project, summary, and optional description
                        if len(processed_args) >= 2:
                            processed_kwargs['project'] = processed_args[0]
                            processed_kwargs['summary'] = processed_args[1]
                            if len(processed_args) >= 3:
                                processed_kwargs['description'] = processed_args[2]
                            processed_args = []
                        elif len(processed_args) == 1 and not processed_kwargs.get('project'):
                            processed_kwargs['project'] = processed_args[0]
                            processed_args = []
                
                # Special handling for issue_create_issue
                if func.__name__ == 'create_issue' and hasattr(func, '__self__'):
                    # This is an instance method, so we need to handle the self parameter
                    instance = func.__self__
                    # Call the method directly on the instance
                    if inspect.iscoroutinefunction(func):
                        result = await func(**processed_kwargs)
                    else:
                        result = func(**processed_kwargs)
                    return result
                
                # Execute the function with the processed parameters
                if is_async:
                    result = await self._execute_func_async(func, processed_kwargs)
                else:
                    result = await self._execute_func(func, processed_kwargs)
                
                # Add tool name metadata to help with debugging
                if isinstance(result, dict):
                    result_with_meta = {
                        "tool": name,
                        "result": result
                    }
                    return result_with_meta
                
                # Return Tool: name, Result: value format for primitive results
                return f"Tool: {name}, Result: {result}"
            
            except Exception as e:
                logger.exception(f"Error executing tool {name}")
                
                # Format error response
                error_message = str(e)
                
                # Include more details for API errors
                if hasattr(e, 'response') and e.response:
                    try:
                        response_text = e.response.text
                        error_message += f"\nAPI Response: {response_text}"
                    except:
                        pass
                
                # Return formatted error
                return {
                    "status": "error",
                    "error": error_message
                }
        
        # For non-async functions, we need a wrapper to call the async wrapper
        def sync_wrapper(*args, **kwargs):
            """Sync wrapper that calls the async wrapper in an event loop."""
            try:
                # Use the existing event loop if available
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
            except RuntimeError as e:
                # Handle "event loop already running" error
                if "already running" in str(e):
                    # If we're in a running event loop, just run the async function directly
                    # nest_asyncio should handle this case, but add extra safety
                    try:
                        # Create a new event loop as a fallback option
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        return new_loop.run_until_complete(async_wrapper(*args, **kwargs))
                    finally:
                        new_loop.close()
                else:
                    # Re-raise other runtime errors
                    raise
        
        # Return the appropriate wrapper based on the transport mode
        if self.transport_mode == 'http':
            # For HTTP transport, always use the async wrapper
            return async_wrapper
        else:
            # For stdio transport, use sync wrapper for sync functions
            return sync_wrapper if not is_async else async_wrapper
    
    def _extract_real_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and validate actual kwargs from those provided by MCP framework.
        Handles type conversion and parameter name mappings.
        """
        real_kwargs = {}
        
        # Special case parameter name mappings to handle common variants
        param_mappings = {
            "project": "project_id",
            "name": "project_name",
            "user": "user_id",
            "issue": "issue_id"
        }
        
        # For MCP tools specifically, extract args as first positional parameter
        if 'args' in kwargs and isinstance(kwargs['args'], str) and kwargs['args']:
            logger.debug(f"Processing args parameter: {kwargs['args']}")
            try:
                # Try interpreting args as JSON if it looks like JSON
                if kwargs['args'].strip().startswith('{') and kwargs['args'].strip().endswith('}'):
                    # Clean up the string in case it has escaped quotes
                    cleaned_args = kwargs['args'].replace('\\\"', '"')
                    args_dict = json.loads(cleaned_args)
                    if isinstance(args_dict, dict):
                        # Merge the args dict into real_kwargs
                        for k, v in args_dict.items():
                            target_key = param_mappings.get(k, k)
                            real_kwargs[target_key] = v
                    else:
                        # Single value
                        real_kwargs['arg_value'] = args_dict
                else:
                    # Not JSON, use as-is for first positional parameter if not empty
                    if kwargs['args'].strip():
                        real_kwargs['arg_value'] = kwargs['args']
            except json.JSONDecodeError as e:
                # Not valid JSON, use as single parameter if not empty
                logger.warning(f"Failed to parse args as JSON: {kwargs['args']}. Error: {str(e)}")
                if kwargs['args'].strip():
                    real_kwargs['arg_value'] = kwargs['args']
        
        # Handle kwargs parameter specially - this is crucial for MCP tools
        if 'kwargs' in kwargs:
            if isinstance(kwargs['kwargs'], str):
                # Try to interpret as JSON if it's a string
                try:
                    # Clean up the string in case it has escaped quotes
                    cleaned_kwargs = kwargs['kwargs'].replace('\\\"', '"')
                    if cleaned_kwargs.strip().startswith('{') and cleaned_kwargs.strip().endswith('}'):
                        kwargs_dict = json.loads(cleaned_kwargs)
                        if isinstance(kwargs_dict, dict):
                            # Merge the kwargs dict into real_kwargs
                            for k, v in kwargs_dict.items():
                                target_key = param_mappings.get(k, k)
                                real_kwargs[target_key] = v
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse kwargs as JSON: {kwargs['kwargs']}. Error: {str(e)}")
            elif isinstance(kwargs['kwargs'], dict):
                # Direct dictionary - merge into real_kwargs
                for k, v in kwargs['kwargs'].items():
                    target_key = param_mappings.get(k, k)
                    real_kwargs[target_key] = v
            else:
                logger.warning(f"Received kwargs of unexpected type: {type(kwargs['kwargs'])}")
        
        # Now process any other parameters directly passed (not in args/kwargs)
        for key, value in kwargs.items():
            # Skip the 'args' and 'kwargs' container parameters that we've already processed
            if key not in ['args', 'kwargs']:
                # Apply parameter name mapping if applicable
                target_key = param_mappings.get(key, key)
                real_kwargs[target_key] = value
        
        # Special handling for create_issue since it's a common problem point
        # For create_issue, we want project_id to be project
        if 'func_name' in kwargs and kwargs['func_name'] == 'create_issue':
            if 'project_id' in real_kwargs and 'project' not in real_kwargs:
                real_kwargs['project'] = real_kwargs.pop('project_id')
            
            # Log parameters for debugging
            logger.info(f"Parameters for create_issue: {real_kwargs}")
        
        # Final pass for type conversion
        for param_name, param_value in list(real_kwargs.items()):
            # Only convert string values to avoid changing JSON objects/arrays
            if isinstance(param_value, str):
                # Convert boolean strings
                if param_value.lower() in ('true', 'false'):
                    real_kwargs[param_name] = param_value.lower() == 'true'
                # Convert integer strings
                elif param_value.isdigit():
                    real_kwargs[param_name] = int(param_value)
                # Convert float strings
                elif param_value.replace('.', '', 1).isdigit():
                    real_kwargs[param_name] = float(param_value)
        
        logger.debug(f"Extracted parameters: {real_kwargs}")
        return real_kwargs
    
    async def _execute_func_async(self, func: Callable, kwargs: Dict[str, Any]) -> Any:
        """
        Execute a function asynchronously, regardless of whether it's an async function or not.
        This universal executor handles both synchronous and asynchronous functions.
        
        Args:
            func: The function to execute
            kwargs: The keyword arguments to pass to the function
            
        Returns:
            The result of the function execution
        """
        try:
            # Check if this is a bound method wrapper (has the is_bound_method attribute)
            is_bound_method = getattr(func, "is_bound_method", False)
            
            # If this is a bound method wrapper created by create_bound_tool, 
            # call it directly with kwargs only
            if is_bound_method:
                logger.info(f"Calling bound method {func.__name__} with kwargs: {kwargs}")
                
                # Get the original function
                original_func = getattr(func, "original_func", func)
                
                # Execute based on whether it's async or not
                if inspect.iscoroutinefunction(original_func):
                    # It's an async function, await it
                    result = await func(**kwargs)
                else:
                    # It's a regular function, run it in an executor to not block
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, lambda: func(**kwargs)
                    )
                    
                return result
                
            # Handle standard parameter validation for non-bound methods
            sig = inspect.signature(func)
            parameters = list(sig.parameters.values())
            
            # Extract positional args from the parameter names
            positional_args = []
            actual_kwargs = {}
            missing_required_params = []
            
            # First, check which parameters are required
            required_params = []
            for param in parameters:
                if param.name == 'self':
                    continue
                    
                if param.default == inspect.Parameter.empty:
                    required_params.append(param.name)
            
            # Special handling for common tools
            if func.__name__ == 'search_with_custom_fields' and 'custom_fields' not in kwargs:
                # Add default empty custom_fields for search_with_custom_fields
                kwargs['custom_fields'] = '{}'
            elif func.__name__ == 'create_issue':
                # Ensure minimal parameters for create_issue
                if 'project' not in kwargs and 'project_id' in kwargs:
                    kwargs['project'] = kwargs['project_id']
                elif 'project' not in kwargs and 'project_key' in kwargs:
                    kwargs['project'] = kwargs['project_key']
                if 'summary' not in kwargs:
                    kwargs['summary'] = 'Issue created by MCP'
            
            # Now build the actual arguments to pass
            for param in parameters:
                # Skip self parameter for class methods
                if param.name == 'self':
                    continue
                
                # Check if this parameter should be a positional argument
                is_positional = param.default == inspect.Parameter.empty and param.kind in (
                    inspect.Parameter.POSITIONAL_ONLY, 
                    inspect.Parameter.POSITIONAL_OR_KEYWORD
                )
                
                if is_positional and param.name in kwargs:
                    positional_args.append(kwargs[param.name])
                elif param.name in kwargs:
                    actual_kwargs[param.name] = kwargs[param.name]
                elif is_positional:
                    # Track missing required parameters
                    missing_required_params.append(param.name)
                
                # Handle special case for first positional argument from arg_value
                if not positional_args and is_positional and 'arg_value' in kwargs:
                    positional_args.append(kwargs['arg_value'])
            
            # Special case for common parameters like project_id, query, etc.
            common_first_params = ['project_id', 'query', 'login', 'project_name', 'user_id', 'issue_id']
            for param_name in common_first_params:
                if not positional_args and param_name in kwargs:
                    positional_args.append(kwargs[param_name])
                    
            # For advanced_search and other query-based functions
            if 'query' in kwargs and not positional_args:
                positional_args.append(kwargs['query'])
            
            # Check if we're missing any required parameters
            if missing_required_params:
                # Debug log to help troubleshoot parameter issues
                params_str = ', '.join(missing_required_params)
                class_name = func.__self__.__class__.__name__ if hasattr(func, '__self__') else "Unknown"
                error_msg = f"{class_name}.{func.__name__}() missing {len(missing_required_params)} required positional argument(s): {params_str}"
                logger.warning(error_msg)
                
                # Try to recover by using defaults for common parameters
                if 'query' in missing_required_params and positional_args:
                    # We might already have query as first positional arg
                    missing_required_params.remove('query')
                
                if 'custom_fields' in missing_required_params:
                    # Add empty dict for custom_fields
                    actual_kwargs['custom_fields'] = {}
                    missing_required_params.remove('custom_fields')
                
                # For create_issue, add defaults for missing parameters
                if func.__name__ == 'create_issue':
                    if 'project' in missing_required_params and not positional_args:
                        # If we don't have a project, use a default or return error
                        return {"error": "Project is required for creating an issue", "status": "error"}
                    if 'summary' in missing_required_params:
                        actual_kwargs['summary'] = "Created by MCP Tool"
                        missing_required_params.remove('summary')
                
                # If we still have missing parameters, return an error
                if missing_required_params:
                    return {"error": error_msg, "status": "error"}
            
            # Log the actual call being made for debugging
            logger.debug(f"Calling {func.__name__} with args: {positional_args} and kwargs: {actual_kwargs}")
            
            # Execute the function - handle different types appropriately
            if inspect.iscoroutinefunction(func):
                # It's an async function, await it
                result = await func(*positional_args, **actual_kwargs)
            elif inspect.isasyncgenfunction(func):
                # It's an async generator, collect all items
                collected_results = []
                async for item in func(*positional_args, **actual_kwargs):
                    collected_results.append(item)
                result = collected_results
            else:
                # It's a regular function, run it in an executor to not block
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: func(*positional_args, **actual_kwargs)
                )
            
            # Handle async generator results that might have been returned
            if inspect.isasyncgen(result):
                collected_results = []
                async for item in result:
                    collected_results.append(item)
                return collected_results
                
            return result
        except Exception as e:
            logger.exception(f"Error executing function {func.__name__}")
            return {"status": "error", "error": str(e)}
    
    # Keep for backward compatibility but mark as deprecated
    async def _execute_func(self, func: Callable, kwargs: Dict[str, Any]) -> Any:
        """
        Execute function with given kwargs. 
        Deprecated: Use _execute_func_async instead.
        """
        return await self._execute_func_async(func, kwargs)
        
    def register_tools(self, tools: Dict[str, Dict[str, Any]]) -> None:
        """
        Register multiple tools at once.
        
        Args:
            tools: Dictionary mapping tool names to their configuration
        """
        # Log tool count
        logger.info(f"Found {len(tools)} tools to register")
        
        for name, config in tools.items():
            should_stream = config.get("streaming", True)
            self.register_tool(
                name=name,
                func=config["function"],
                description=config["description"],
                parameter_descriptions=config.get("parameter_descriptions"),
                should_stream=should_stream
            )
            
    def run(self) -> None:
        """Run the MCP server."""
        logger.info(f"Starting YouTrack MCP server ({config.MCP_SERVER_NAME}) with {self.transport_mode} transport")
        self.server.run()
            
    def register_loaded_tools(self, loaded_tools: Dict[str, Callable]) -> None:
        """
        Register tools that have been loaded by the loader.
        
        Args:
            loaded_tools: Dictionary mapping tool names to their functions
        """
        # Count duplicates for namespace resolution
        tool_counts = {}
        for name in loaded_tools:
            base_name = name
            if "_" in name:
                # For namespaced tools like "issues_get_issue", extract the base name
                base_name = name.split("_", 1)[1]
            tool_counts[base_name] = tool_counts.get(base_name, 0) + 1
        
        # Count of tools by streaming capability
        streaming_count = 0
        non_streaming_count = 0
        
        # Skip tools that are already registered
        new_tools = {}
        for name, func in loaded_tools.items():
            if name not in self._registered_tools:
                new_tools[name] = func
        
        # Log summary of tool registration plan
        logger.info(f"Registering {len(new_tools)} new tools out of {len(loaded_tools)} total tools")
        
        for name, func in new_tools.items():
            # Get function metadata
            description = func.__doc__ or f"Tool {name}"
            
            # For wrapped functions, try to get the original docstring
            if hasattr(func, "__wrapped__"):
                description = func.__wrapped__.__doc__ or description
            
            # Extract first line as description
            description = description.strip().split('\n')[0]
            
            # Determine if this tool should use streaming
            # For now, assume all tools except Issue tools can stream
            should_stream = not name.startswith("issues_") and not name in [
                "get_issue", "get_issue_raw", "search_issues", "create_issue", "add_comment"
            ]
            
            # Update counts
            if should_stream:
                streaming_count += 1
            else:
                non_streaming_count += 1
            
            # Register the tool with appropriate parameters
            self.register_tool(
                name=name,
                func=func,
                description=description,
                should_stream=should_stream
            )
        
        # Log summary at the end
        logger.info(f"Registered {len(new_tools)} new tools ({streaming_count} streaming, {non_streaming_count} non-streaming)")
    
    def stop(self) -> None:
        """Stop the MCP server."""
        logger.info("Stopping YouTrack MCP server")
        # Server automatically stops when run() completes 