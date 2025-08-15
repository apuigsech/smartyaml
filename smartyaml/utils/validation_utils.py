"""
Validation utilities for SmartYAML constructors
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ..config import get_config
from ..exceptions import (
    ConstructorError,
    RecursionLimitError,
    TemplatePathError,
)


def validate_constructor_args(
    args: List[Any], expected_count: Union[int, tuple], constructor_name: str
) -> None:
    """
    Validate constructor arguments count and types.

    Args:
        args: List of arguments
        expected_count: Expected argument count (int) or range (tuple of min, max)
        constructor_name: Name of constructor for error messages

    Raises:
        ConstructorError: If argument validation fails
    """
    if isinstance(expected_count, int):
        if len(args) != expected_count:
            raise ConstructorError(
                f"{constructor_name} expects exactly {expected_count} argument(s), got {len(args)}"
            )
    elif isinstance(expected_count, tuple):
        min_count, max_count = expected_count
        if len(args) < min_count or len(args) > max_count:
            range_desc = (
                f"{min_count}-{max_count}" if min_count != max_count else str(min_count)
            )
            raise ConstructorError(
                f"{constructor_name} expects {range_desc} argument(s), got {len(args)}"
            )


def validate_filename(filename: Any, constructor_name: str) -> str:
    """
    Validate filename parameter.

    Args:
        filename: Filename to validate
        constructor_name: Constructor name for error messages

    Returns:
        Validated filename as string

    Raises:
        ConstructorError: If filename is invalid
    """
    if not filename or not isinstance(filename, str):
        raise ConstructorError(
            f"{constructor_name} requires a non-empty filename. "
            f"Example: !import config.yaml or !template base_config"
        )

    # Check for null bytes and other problematic characters
    if "\0" in filename:
        raise ConstructorError(
            f"{constructor_name} filename contains null byte, which is not allowed. "
            f"Please check your file path for binary characters."
        )

    return filename


def validate_file_before_read(file_path: Path, constructor_name: str) -> None:
    """
    Perform pre-flight validation on file before attempting to read it.

    Args:
        file_path: Path to file to validate
        constructor_name: Constructor name for error messages

    Raises:
        ConstructorError: If file validation fails
    """
    config = get_config()

    # Check if file exists
    if not file_path.exists():
        from ..exceptions import SmartYAMLFileNotFoundError

        raise SmartYAMLFileNotFoundError(
            f"File not found: {file_path}. "
            f"Please check the file path and ensure the file exists."
        )

    # Check if it's actually a file (not directory)
    if not file_path.is_file():
        raise ConstructorError(
            f"{constructor_name}: Path is not a file: {file_path}. "
            f"Please provide a path to a YAML file, not a directory."
        )

    # Check file permissions
    if not os.access(file_path, os.R_OK):
        raise ConstructorError(
            f"{constructor_name}: Permission denied reading file: {file_path}. "
            f"Please check file permissions."
        )

    # Check file size before reading
    try:
        file_size = file_path.stat().st_size
        max_size = config.max_file_size

        if file_size > max_size:
            size_mb = file_size / (1024 * 1024)
            limit_mb = max_size / (1024 * 1024)
            raise ConstructorError(
                f"{constructor_name}: File too large: {file_path} ({size_mb:.1f}MB). "
                f"Maximum allowed size is {limit_mb:.1f}MB. "
                f"Consider splitting the file or increasing max_file_size in config."
            )

        # Warn about large files (>1MB)
        if file_size > 1024 * 1024:  # 1MB
            size_mb = file_size / (1024 * 1024)
            # Note: We could add a warning system here in the future

    except OSError as e:
        raise ConstructorError(
            f"{constructor_name}: Error accessing file {file_path}: {e}. "
            f"Please check file permissions and disk status."
        ) from e


def validate_environment_variable(var_name: Any, constructor_name: str) -> str:
    """
    Validate environment variable name.

    Args:
        var_name: Variable name to validate
        constructor_name: Constructor name for error messages

    Returns:
        Validated variable name as string

    Raises:
        ConstructorError: If variable name is invalid
    """
    if not var_name or not isinstance(var_name, str):
        raise ConstructorError(
            f"{constructor_name} requires a non-empty variable name. "
            f"Example: !env MY_VARIABLE or !env [MY_VARIABLE, default_value]"
        )

    # Check for valid environment variable name characters (optimized)
    from smartyaml.performance_optimizations import optimized_patterns

    if not optimized_patterns.is_valid_env_var_name(var_name):
        raise ConstructorError(
            f"{constructor_name} invalid environment variable name: '{var_name}'. "
            f"Environment variable names must contain only letters, numbers, and underscores, "
            f"and cannot start with a number. Examples: MY_VAR, API_KEY, DB_HOST_1"
        )

    return var_name


def validate_template_name(template_name: Any, constructor_name: str) -> str:
    """
    Validate template name parameter.

    Args:
        template_name: Template name to validate
        constructor_name: Constructor name for error messages

    Returns:
        Validated template name as string

    Raises:
        ConstructorError: If template name is invalid
    """
    if not template_name or not isinstance(template_name, str):
        raise ConstructorError(f"{constructor_name} requires a non-empty template name")

    # Check for directory traversal attempts
    if ".." in template_name:
        raise ConstructorError(
            f"{constructor_name} template name cannot contain '..' (directory traversal)"
        )

    # Check for backslashes (use forward slashes only)
    if "\\" in template_name:
        raise ConstructorError(
            f"{constructor_name} template name cannot contain backslashes, use forward slashes"
        )

    # Check for absolute paths
    if template_name.startswith("/"):
        raise ConstructorError(
            f"{constructor_name} template name cannot be an absolute path"
        )

    # Check for leading/trailing separators that could cause issues
    if template_name.startswith("/") or template_name.endswith("/"):
        raise ConstructorError(
            f"{constructor_name} template name cannot start or end with path separators"
        )

    # Check for empty path components (e.g., "a//b")
    if "//" in template_name:
        raise ConstructorError(
            f"{constructor_name} template name cannot contain empty path components"
        )

    return template_name


def check_recursion_limit(
    import_stack: Set[Path], file_path: Path, max_depth: Optional[int] = None
) -> None:
    """
    Check if import would exceed recursion limits or create cycles.

    Args:
        import_stack: Set of files currently being imported
        file_path: Path being imported
        max_depth: Maximum recursion depth (uses config default if None)

    Raises:
        RecursionLimitError: If recursion limit would be exceeded or cycle detected
    """
    config = get_config()

    if max_depth is None:
        max_depth = config.max_recursion_depth

    # Check for cycles
    if file_path in import_stack:
        raise RecursionLimitError(f"Circular import detected: {file_path}")

    # Check recursion depth
    if len(import_stack) >= max_depth:
        stack_list = list(import_stack)
        raise RecursionLimitError(
            f"Maximum recursion depth ({max_depth}) exceeded. "
            f"Import stack: {' -> '.join(str(p) for p in stack_list)} -> {file_path}"
        )


def get_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable with optional default (cached).

    Args:
        var_name: Environment variable name
        default: Default value if variable is not set

    Returns:
        Environment variable value or default
    """
    from smartyaml.performance_optimizations import cached_operations

    return cached_operations.resolve_env_var(var_name, default)


def is_truthy(value: Optional[str]) -> bool:
    """
    Check if a string value should be considered True.

    Args:
        value: String value to check

    Returns:
        True if value is truthy according to configuration
    """
    if value is None:
        return False

    config = get_config()
    value = value.lower().strip()
    return value in config.truthy_values


def validate_template_path(template_path: Optional[Path]) -> Path:
    """
    Validate and return template path.

    Args:
        template_path: Optional template path (overrides config/env var)

    Returns:
        Validated template path

    Raises:
        TemplatePathError: If template path is not configured or invalid
    """
    config = get_config()

    if template_path:
        if not template_path.exists():
            raise TemplatePathError(
                f"Template path does not exist: {template_path}. "
                f"Please create the directory or check the path spelling."
            )
        return template_path

    # Check config first, then environment variable
    if config.template_base_path and config.template_base_path.exists():
        return config.template_base_path

    # Check environment variable for backward compatibility
    tmpl_env = get_env_var("SMARTYAML_TMPL")
    if tmpl_env:
        tmpl_path = Path(tmpl_env)
        if tmpl_path.exists():
            return tmpl_path
        else:
            raise TemplatePathError(
                f"SMARTYAML_TMPL path does not exist: {tmpl_path}. "
                f"Please create the directory or update the environment variable."
            )

    raise TemplatePathError(
        "Template path not configured. To fix this, either:\n"
        "1. Set SMARTYAML_TMPL environment variable to your templates directory\n"
        "2. Pass template_path parameter to load() function\n"
        "3. Configure template_base_path in SmartYAML config\n"
        "Example: export SMARTYAML_TMPL=/path/to/templates"
    )


def add_context_to_error(error: Exception, context: Dict[str, Any]) -> Exception:
    """
    Add context information to an exception.

    Args:
        error: Original exception
        context: Dictionary with context information

    Returns:
        Exception with enhanced message
    """
    config = get_config()

    # Limit context items to prevent overly verbose error messages
    limited_context = dict(list(context.items())[: config.max_error_context_items])

    context_str = ", ".join(
        f"{k}={v}" for k, v in limited_context.items() if v is not None
    )

    enhanced_message = str(error)
    if context_str:
        enhanced_message += f" (context: {context_str})"

    # Create new exception of same type with enhanced message
    new_error = type(error)(enhanced_message)
    new_error.__cause__ = error
    return new_error
