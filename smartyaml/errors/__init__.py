"""
SmartYAML Error Handling System

Standardized error context building and exception management.
"""

from .context import ErrorContext, ErrorContextBuilder
from .helpers import (
    ErrorHelper,
    create_error_context,
    error_context,
    require_file_exists,
    require_list_length,
    require_type,
    with_error_context,
)

__all__ = [
    "ErrorContext",
    "ErrorContextBuilder",
    "ErrorHelper",
    "create_error_context",
    "require_type",
    "require_list_length",
    "require_file_exists",
    "error_context",
    "with_error_context",
]
