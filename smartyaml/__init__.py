"""
SmartYAML - Extended YAML format with custom directives
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from .exceptions import (
    Base64Error,
    ConstructorError,
    EnvironmentVariableError,
    InvalidPathError,
    RecursionLimitError,
    ResourceLimitError,
    SmartYAMLError,
    SmartYAMLFileNotFoundError,
    TemplatePathError,
)
from .loader import SmartYAMLLoader

__version__ = "0.1.0"
__all__ = [
    "load",
    "loads",
    "dump",
    "SmartYAMLLoader",
    "SmartYAMLError",
    "SmartYAMLFileNotFoundError",
    "InvalidPathError",
    "EnvironmentVariableError",
    "TemplatePathError",
    "Base64Error",
    "ResourceLimitError",
    "RecursionLimitError",
    "ConstructorError",
]


def remove_metadata_fields(data: Any) -> Any:
    """
    Recursively remove fields with "__" prefix from YAML data structures.

    Metadata fields are used for annotations and documentation but should not
    appear in the final parsed result. This function traverses the entire
    data structure and removes any dictionary keys that start with "__".

    Args:
        data: The parsed YAML data structure

    Returns:
        The data structure with all metadata fields removed
    """
    METADATA_PREFIX = "__"

    if isinstance(data, dict):
        # Remove keys starting with "__" and recursively process remaining values
        return {
            key: remove_metadata_fields(value)
            for key, value in data.items()
            if not key.startswith(METADATA_PREFIX)
        }
    elif isinstance(data, list):
        # Recursively process list items
        return [remove_metadata_fields(item) for item in data]
    else:
        # Return primitive types unchanged
        return data


def process_deferred_expansions(data: Any, variables: Dict[str, Any]) -> Any:
    """
    Process deferred expansion markers in parsed YAML data.

    Args:
        data: Parsed YAML data structure that may contain deferred expansions
        variables: Dictionary of variables for expansion

    Returns:
        Data structure with deferred expansions processed
    """
    from .constants import DEFERRED_EXPANSION_KEY

    if isinstance(data, dict):
        if DEFERRED_EXPANSION_KEY in data and len(data) == 1:
            # This is a deferred expansion marker
            content = data[DEFERRED_EXPANSION_KEY]
            if variables:
                from .utils.variable_substitution import VariableSubstitutionEngine

                engine = VariableSubstitutionEngine(variables)
                return engine.substitute_string(content)
            else:
                # Still no variables - check if expansion is needed
                from .utils.variable_substitution import VariableSubstitutionEngine

                engine = VariableSubstitutionEngine()
                if engine.has_variables(content):
                    missing_vars = engine.extract_variable_names(content)
                    from .exceptions import ConstructorError

                    # Build helpful debugging message
                    debug_info = f"Variables found in content: {missing_vars}"

                    # Add information about available variables if any exist
                    if variables:
                        available_vars = list(variables.keys())
                        debug_info += f"\nAvailable variables: {available_vars}"

                        # Show which specific variables are missing
                        truly_missing = [
                            var for var in missing_vars if var not in variables
                        ]
                        if truly_missing:
                            debug_info += f"\nMissing variables: {truly_missing}"
                    else:
                        debug_info += "\nNo variables provided to SmartYAML"

                    raise ConstructorError(
                        directive_name="!expand",
                        message=(
                            f"Variable expansion failed: {debug_info}\n"
                            f"To fix this, either:\n"
                            f"1. Pass variables to load() function: "
                            f"load(file, variables={{'key': 'value'}})\n"
                            f"2. Define __vars in your YAML: __vars: {{key: value}}\n"
                            f"3. Ensure all referenced variables are defined"
                        ),
                        location=None,
                    )
                return content
        else:
            # Regular dictionary - process recursively
            return {
                key: process_deferred_expansions(value, variables)
                for key, value in data.items()
            }
    elif isinstance(data, list):
        return [process_deferred_expansions(item, variables) for item in data]
    else:
        return data


def load(
    stream: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
    template_path: Optional[Union[str, Path]] = None,
    max_file_size: Optional[int] = None,
    max_recursion_depth: Optional[int] = None,
    remove_metadata: bool = True,
    variables: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Load SmartYAML from file or string.

    Args:
        stream: YAML content as string or Path to file
        base_path: Base directory for resolving relative paths (defaults to file's directory)
        template_path: Base directory for templates (overrides SMARTYAML_TMPL env var)
        max_file_size: Maximum file size in bytes (default: 10MB)
        max_recursion_depth: Maximum import recursion depth (default: 10)
        remove_metadata: Whether to remove fields prefixed with "__" (default: True)
        variables: Dictionary of variables for {{key}} expansion (default: None)

    Returns:
        Parsed YAML data with SmartYAML directives processed and metadata fields removed
    """
    from .loading import LoadPipeline

    pipeline = LoadPipeline()
    return pipeline.load(
        stream=stream,
        base_path=base_path,
        template_path=template_path,
        max_file_size=max_file_size,
        max_recursion_depth=max_recursion_depth,
        remove_metadata=remove_metadata,
        variables=variables,
    )


def loads(
    content: str,
    base_path: Optional[Union[str, Path]] = None,
    template_path: Optional[Union[str, Path]] = None,
    max_file_size: Optional[int] = None,
    max_recursion_depth: Optional[int] = None,
    remove_metadata: bool = True,
    variables: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Load SmartYAML from string content.

    Args:
        content: YAML content as string
        base_path: Base directory for resolving relative paths (defaults to current directory)
        template_path: Base directory for templates (overrides SMARTYAML_TMPL env var)
        max_file_size: Maximum file size in bytes (default: 10MB)
        max_recursion_depth: Maximum import recursion depth (default: 10)
        remove_metadata: Whether to remove fields prefixed with "__" (default: True)
        variables: Dictionary of variables for {{key}} expansion (default: None)

    Returns:
        Parsed YAML data with SmartYAML directives processed and metadata fields removed
    """
    from .loading import LoadPipeline

    pipeline = LoadPipeline()
    return pipeline.load(
        stream=content,
        base_path=base_path,
        template_path=template_path,
        max_file_size=max_file_size,
        max_recursion_depth=max_recursion_depth,
        remove_metadata=remove_metadata,
        variables=variables,
    )


def dump(
    data: Any, stream: Optional[Union[str, Path]] = None, **kwargs
) -> Optional[str]:
    """
    Dump data to YAML format.

    Args:
        data: Data to serialize
        stream: Output file path or None to return string
        **kwargs: Additional arguments for yaml.dump

    Returns:
        YAML string if stream is None, otherwise None
    """
    kwargs.setdefault("default_flow_style", False)
    kwargs.setdefault("allow_unicode", True)

    if stream is None:
        return yaml.dump(data, **kwargs)
    else:
        with open(stream, "w", encoding="utf-8") as f:
            yaml.dump(data, f, **kwargs)
