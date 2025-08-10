"""
Validation utilities for SmartYAML constructors
"""

import os
from typing import Union, Optional, Set, List, Any, Dict
from pathlib import Path
from ..config import get_config
from ..exceptions import (
    ConstructorError, EnvironmentVariableError, 
    RecursionLimitError, TemplatePathError
)


def validate_constructor_args(args: List[Any], expected_count: Union[int, tuple], 
                            constructor_name: str) -> None:
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
            range_desc = f"{min_count}-{max_count}" if min_count != max_count else str(min_count)
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
        raise ConstructorError(f"{constructor_name} requires a non-empty filename")
    
    # Check for null bytes and other problematic characters
    if '\0' in filename:
        raise ConstructorError(f"{constructor_name} filename contains null byte")
    
    return filename


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
        raise ConstructorError(f"{constructor_name} requires a non-empty variable name")
    
    # Check for valid environment variable name characters (optimized)
    from smartyaml.performance_optimizations import optimized_patterns
    if not optimized_patterns.is_valid_env_var_name(var_name):
        raise ConstructorError(f"{constructor_name} invalid environment variable name: {var_name}")
    
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
    
    # Check for path traversal attempts
    if '..' in template_name or '/' in template_name or '\\' in template_name:
        raise ConstructorError(f"{constructor_name} template name cannot contain path separators")
    
    return template_name


def check_recursion_limit(import_stack: Set[Path], file_path: Path, 
                         max_depth: Optional[int] = None) -> None:
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
            raise TemplatePathError(f"Template path does not exist: {template_path}")
        return template_path
    
    # Check config first, then environment variable
    if config.template_base_path and config.template_base_path.exists():
        return config.template_base_path
    
    # Check environment variable for backward compatibility
    tmpl_env = get_env_var('SMARTYAML_TMPL')
    if tmpl_env:
        tmpl_path = Path(tmpl_env)
        if tmpl_path.exists():
            return tmpl_path
        else:
            raise TemplatePathError(f"SMARTYAML_TMPL path does not exist: {tmpl_path}")
    
    raise TemplatePathError(
        "Template path not configured. Set template_base_path in config or SMARTYAML_TMPL environment variable"
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
    limited_context = dict(list(context.items())[:config.max_error_context_items])
    
    context_str = ", ".join(
        f"{k}={v}" for k, v in limited_context.items() 
        if v is not None
    )
    
    enhanced_message = str(error)
    if context_str:
        enhanced_message += f" (context: {context_str})"
    
    # Create new exception of same type with enhanced message
    new_error = type(error)(enhanced_message)
    new_error.__cause__ = error
    return new_error