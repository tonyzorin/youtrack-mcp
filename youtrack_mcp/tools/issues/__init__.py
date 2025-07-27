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
    "Diagnostics",
    "CustomFields",
    "BasicOperations",
    "Linking",
    "Attachments",
]

# Import the completed modules
try:
    from .dedicated_updates import DedicatedUpdates
    from .diagnostics import Diagnostics
    from .custom_fields import CustomFields
    from .basic_operations import BasicOperations
    from .linking import Linking
    from .attachments import Attachments
except ImportError:
    # During development, modules might not be ready yet
    pass 