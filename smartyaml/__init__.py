"""
SmartYAML - Extended YAML format with custom directives
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
    if isinstance(data, dict):
        # Remove keys starting with "__" and recursively process remaining values
        return {
            key: remove_metadata_fields(value)
            for key, value in data.items()
            if not key.startswith("__")
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
    if isinstance(data, dict):
        if "__smartyaml_expand_deferred" in data and len(data) == 1:
            # This is a deferred expansion marker
            content = data["__smartyaml_expand_deferred"]
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

                    raise ConstructorError(
                        directive_name="!expand",
                        message=f"!expand directive found variables {missing_vars} but no variables provided. "
                        f"Pass variables to load() function or define __vars metadata.",
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
    if isinstance(stream, (str, Path)) and Path(stream).exists():
        # Load from file
        file_path = Path(stream).resolve()
        if base_path is None:
            base_path = file_path.parent

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        # Load from string
        content = str(stream)
        if base_path is None:
            base_path = Path.cwd()

    # Create a custom loader class with paths, limits, and variables set
    class ConfiguredSmartYAMLLoader(SmartYAMLLoader):
        def __init__(self, stream):
            super().__init__(stream)
            self.base_path = Path(base_path).resolve()
            if template_path:
                self.template_path = Path(template_path).resolve()
            self.import_stack = set()
            self.max_file_size = max_file_size
            self.max_recursion_depth = max_recursion_depth
            # Start with function variables, will be updated with __vars during parsing
            self.expansion_variables = variables or {}

    result = yaml.load(content, Loader=ConfiguredSmartYAMLLoader)

    # Extract __vars metadata after parsing and update variables if needed
    from .utils.variable_substitution import (
        VariableSubstitutionEngine,
        extract_vars_metadata,
    )

    vars_metadata = extract_vars_metadata(result)

    # Process deferred expansions if any __vars were found or variables were provided
    if vars_metadata or variables:
        engine = VariableSubstitutionEngine()
        merged_variables = engine.merge_variables(vars_metadata, variables)
        result = process_deferred_expansions(result, merged_variables)
    else:
        # Process deferred expansions with no variables (will raise errors if needed)
        result = process_deferred_expansions(result, {})

    # Remove metadata fields if requested (this removes __vars)
    if remove_metadata:
        result = remove_metadata_fields(result)

    return result


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
    if base_path is None:
        base_path = Path.cwd()

    # Create a custom loader class with paths, limits, and variables set
    class ConfiguredSmartYAMLLoader(SmartYAMLLoader):
        def __init__(self, stream):
            super().__init__(stream)
            self.base_path = Path(base_path).resolve()
            if template_path:
                self.template_path = Path(template_path).resolve()
            self.import_stack = set()
            self.max_file_size = max_file_size
            self.max_recursion_depth = max_recursion_depth
            # Start with function variables, will be updated with __vars during parsing
            self.expansion_variables = variables or {}

    result = yaml.load(content, Loader=ConfiguredSmartYAMLLoader)

    # Extract __vars metadata after parsing and update variables if needed
    from .utils.variable_substitution import (
        VariableSubstitutionEngine,
        extract_vars_metadata,
    )

    vars_metadata = extract_vars_metadata(result)

    # Process deferred expansions if any __vars were found or variables were provided
    if vars_metadata or variables:
        engine = VariableSubstitutionEngine()
        merged_variables = engine.merge_variables(vars_metadata, variables)
        result = process_deferred_expansions(result, merged_variables)
    else:
        # Process deferred expansions with no variables (will raise errors if needed)
        result = process_deferred_expansions(result, {})

    # Remove metadata fields if requested (this removes __vars)
    if remove_metadata:
        result = remove_metadata_fields(result)

    return result


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
