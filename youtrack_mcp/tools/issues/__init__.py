"""
YouTrack Issue Tools Package.

This package contains modular issue management tools broken down by functionality:
- basic_operations: Core CRUD operations
- custom_fields: Custom field management  
- dedicated_updates: Specialized update functions
- linking: Issue relationships
- diagnostics: Workflow analysis & help
- attachments: File & raw data operations
"""

# For now, we'll just have the base exports
# More will be added as we complete the refactoring

__all__ = [
    "DedicatedUpdates",
]

# Import the completed modules
try:
    from .dedicated_updates import DedicatedUpdates
except ImportError:
    # During development, modules might not be ready yet
    pass 