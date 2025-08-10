"""
SmartYAML utilities package
"""

# Import commonly used functions for backward compatibility
from .path_utils import resolve_path, is_safe_path, normalize_path
from .file_utils import read_file, get_file_hash, clear_file_cache, get_cache_stats
from .validation_utils import (
    validate_constructor_args, validate_filename, validate_environment_variable,
    validate_template_name, check_recursion_limit, get_env_var, is_truthy,
    validate_template_path, add_context_to_error
)
from .loader_utils import create_loader_context

__all__ = [
    'resolve_path', 'is_safe_path', 'normalize_path',
    'read_file', 'get_file_hash', 'clear_file_cache', 'get_cache_stats',
    'validate_constructor_args', 'validate_filename', 'validate_environment_variable',
    'validate_template_name', 'check_recursion_limit', 'get_env_var', 'is_truthy',
    'validate_template_path', 'add_context_to_error', 'create_loader_context'
]