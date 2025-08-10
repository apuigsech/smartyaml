"""
SmartYAML utilities package
"""

from .file_utils import clear_file_cache, get_cache_stats, get_file_hash, read_file
from .loader_utils import create_loader_context

# Import commonly used functions for backward compatibility
from .path_utils import is_safe_path, normalize_path, resolve_path
from .validation_utils import (
    add_context_to_error,
    check_recursion_limit,
    get_env_var,
    is_truthy,
    validate_constructor_args,
    validate_environment_variable,
    validate_filename,
    validate_template_name,
    validate_template_path,
)

__all__ = [
    "resolve_path",
    "is_safe_path",
    "normalize_path",
    "read_file",
    "get_file_hash",
    "clear_file_cache",
    "get_cache_stats",
    "validate_constructor_args",
    "validate_filename",
    "validate_environment_variable",
    "validate_template_name",
    "check_recursion_limit",
    "get_env_var",
    "is_truthy",
    "validate_template_path",
    "add_context_to_error",
    "create_loader_context",
]
