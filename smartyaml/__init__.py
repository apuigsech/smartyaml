"""
SmartYAML - Enhanced YAML processing with templates, variables, and directives

This is the main public API for SmartYAML v1.0 following SPECS-v1.md format.
Provides a clean interface for processing YAML files with advanced features.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import ConfigurationError, SmartYAMLConfig, SmartYAMLConfigBuilder
from .exceptions import (
    ConditionalEvaluationError,
    DirectiveProcessingError,
    DirectiveSyntaxError,
    FileNotFoundError,
    FileSizeExceededError,
    MergeConflictError,
    RecursionLimitExceededError,
    SchemaValidationError,
    SecurityViolationError,
    SmartYAMLError,
    VariableExpansionError,
    VariableNotFoundError,
    VersionMismatchError,
)
from .pipeline.processor import SmartYAMLProcessor

# Version information
__version__ = "1.0.0"
__all__ = [
    "load",
    "loads",
    "load_file",
    "SmartYAMLConfig",
    "SmartYAMLConfigBuilder",
    "SmartYAMLProcessor",
    "ConfigurationError",
    "SmartYAMLError",
    "DirectiveSyntaxError",
    "DirectiveProcessingError",
    "VariableExpansionError",
    "VariableNotFoundError",
    "VersionMismatchError",
    "FileNotFoundError",
    "RecursionLimitExceededError",
    "MergeConflictError",
    "ConditionalEvaluationError",
    "SchemaValidationError",
    "SecurityViolationError",
    "FileSizeExceededError",
    "__version__",
]


def load(
    file_path: Union[str, Path],
    variables: Optional[Dict[str, Any]] = None,
    config: Optional[SmartYAMLConfig] = None,
    **config_kwargs,
) -> Dict[str, Any]:
    """
    Load and process a SmartYAML file.

    Args:
        file_path: Path to the YAML file to load
        variables: External variables to inject (highest precedence)
        config: SmartYAMLConfig instance, or None to use default
        **config_kwargs: Configuration options passed to SmartYAMLConfig

    Returns:
        Processed YAML data as a dictionary

    Raises:
        SmartYAMLError: If processing fails
        FileNotFoundError: If file doesn't exist
    """
    # Create or merge configuration
    if config is None:
        config = SmartYAMLConfig(**config_kwargs)
    elif config_kwargs:
        # Merge provided config with kwargs
        updated_config = SmartYAMLConfig(**config_kwargs)
        config = config.merge_with(updated_config)

    # Add external variables to config
    if variables:
        config.variables.update(variables)

    # Create processor and process file
    processor = SmartYAMLProcessor(config)
    return processor.process_file(file_path)


def loads(
    yaml_content: str,
    variables: Optional[Dict[str, Any]] = None,
    base_path: Optional[Union[str, Path]] = None,
    config: Optional[SmartYAMLConfig] = None,
    **config_kwargs,
) -> Dict[str, Any]:
    """
    Load and process SmartYAML from a string.

    Args:
        yaml_content: YAML content as string
        variables: External variables to inject (highest precedence)
        base_path: Base path for resolving relative includes/templates
        config: SmartYAMLConfig instance, or None to use default
        **config_kwargs: Configuration options passed to SmartYAMLConfig

    Returns:
        Processed YAML data as a dictionary

    Raises:
        SmartYAMLError: If processing fails
    """
    # Create or merge configuration
    if config is None:
        config = SmartYAMLConfig(**config_kwargs)
    elif config_kwargs:
        # Merge provided config with kwargs
        updated_config = SmartYAMLConfig(**config_kwargs)
        config = config.merge_with(updated_config)

    # Add external variables to config
    if variables:
        config.variables.update(variables)

    # Set base path if provided
    if base_path:
        config.base_path = Path(base_path).resolve()

    # Create processor and process string
    processor = SmartYAMLProcessor(config)
    return processor.process_string(yaml_content, config.base_path)


def load_file(file_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
    """
    Alias for load() function for backward compatibility.

    Args:
        file_path: Path to the YAML file to load
        **kwargs: Same arguments as load()

    Returns:
        Processed YAML data as a dictionary
    """
    return load(file_path, **kwargs)


# Convenience functions for common configurations
def load_secure(
    file_path: Union[str, Path],
    variables: Optional[Dict[str, Any]] = None,
    allowed_env_vars: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Load YAML with enhanced security restrictions.

    Args:
        file_path: Path to the YAML file to load
        variables: External variables to inject
        allowed_env_vars: Whitelist of allowed environment variables

    Returns:
        Processed YAML data as a dictionary
    """
    config = SmartYAMLConfig(
        strict_security=True,
        strict_variables=True,
        sandbox_mode=True,
        allow_remote_schemas=False,
        allowed_env_vars=allowed_env_vars,
        forbidden_env_vars=[
            "PASSWORD",
            "SECRET",
            "TOKEN",
            "API_KEY",
            "PRIVATE_KEY",
            "CERT",
            "AUTH",
            "CREDENTIAL",
            "PASSWD",
        ],
    )

    return load(file_path, variables=variables, config=config)


def load_with_templates(
    file_path: Union[str, Path],
    template_path: Union[str, Path],
    variables: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Load YAML with template support enabled.

    Args:
        file_path: Path to the YAML file to load
        template_path: Base path for template files
        variables: External variables to inject

    Returns:
        Processed YAML data as a dictionary
    """
    config = SmartYAMLConfig(
        template_path=Path(template_path), validate_schema=True, enable_caching=True
    )

    return load(file_path, variables=variables, config=config)
