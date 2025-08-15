"""
Shared YAML parsing utilities for SmartYAML.

This module consolidates common YAML parsing patterns to reduce code duplication
and improve maintainability across constructors and loaders.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Set, Type

import yaml

from ..loader import SmartYAMLLoader


def load_yaml_with_context(
    yaml_content: str,
    loader_class: Type[SmartYAMLLoader],
    base_path: Optional[Path] = None,
    template_path: Optional[Path] = None,
    import_stack: Optional[Set[Path]] = None,
    max_file_size: Optional[int] = None,
    max_recursion_depth: Optional[int] = None,
    expansion_variables: Optional[Dict[str, Any]] = None,
    parent_loader: Optional[SmartYAMLLoader] = None,
    accumulate_vars: bool = True,
) -> Any:
    """
    Load YAML content with a configured SmartYAML loader context.

    This function consolidates the common pattern of creating a configured
    loader and parsing YAML content with proper context propagation.

    Args:
        yaml_content: YAML content string to parse
        loader_class: Base SmartYAML loader class to configure
        base_path: Base directory for resolving relative paths
        template_path: Template directory path
        import_stack: Set of imported file paths for recursion detection
        max_file_size: Maximum file size limit
        max_recursion_depth: Maximum import recursion depth
        expansion_variables: Variables for template expansion
        parent_loader: Parent loader instance for context inheritance
        accumulate_vars: Whether to extract and accumulate __vars from result

    Returns:
        Parsed YAML data structure
    """
    # Import here to avoid circular dependencies
    from ..constructors.yaml_file_loader import create_loader_context

    # Create configured loader with context
    ConfiguredLoader = create_loader_context(
        loader_class,
        base_path=base_path,
        template_path=template_path,
        import_stack=import_stack or set(),
        max_file_size=max_file_size,
        max_recursion_depth=max_recursion_depth,
        expansion_variables=expansion_variables or {},
        parent_loader=parent_loader,
    )

    # Parse YAML with configured loader
    result = yaml.load(yaml_content, Loader=ConfiguredLoader)

    # Handle variable extraction and accumulation if requested
    if accumulate_vars and parent_loader:
        extract_and_accumulate_vars(result, parent_loader)

    return result


def extract_and_accumulate_vars(data: Any, parent_loader: SmartYAMLLoader) -> None:
    """
    Extract __vars from parsed data and accumulate them in parent loader.

    This function implements the common pattern of extracting __vars sections
    from loaded YAML data and accumulating them in the parent loader context.

    Args:
        data: Parsed YAML data that may contain __vars
        parent_loader: Parent loader instance to accumulate variables into
    """
    from .variable_substitution import extract_vars_metadata

    file_vars = extract_vars_metadata(data)
    if file_vars and hasattr(parent_loader, "accumulate_vars"):
        parent_loader.accumulate_vars(file_vars)


def create_import_stack_copy(
    loader_context: Dict[str, Any], file_path: Path
) -> Set[Path]:
    """
    Create a copy of import stack with new file added.

    This implements the common pattern of copying the import stack and
    adding a new file path for recursion tracking.

    Args:
        loader_context: Loader context dictionary containing import_stack
        file_path: File path to add to the import stack copy

    Returns:
        New import stack set with file_path added
    """
    import_stack = loader_context.get("import_stack", set())
    new_import_stack = import_stack.copy()
    new_import_stack.add(file_path)
    return new_import_stack


def create_anchor_capturing_loader(
    base_loader_class: Type[SmartYAMLLoader],
    captured_anchors: Dict[str, Any],
    **loader_kwargs,
) -> Type[SmartYAMLLoader]:
    """
    Create a dynamic anchor-capturing loader class.

    This factory function creates a loader class that captures YAML anchors
    during composition, implementing the common anchor extraction pattern.

    Args:
        base_loader_class: Base loader class to extend
        captured_anchors: Dictionary to store captured anchors
        **loader_kwargs: Additional arguments for loader initialization

    Returns:
        Configured anchor-capturing loader class
    """

    class AnchorCapturingLoader(base_loader_class):
        def __init__(self, stream):
            super().__init__(stream)
            # Apply any additional configuration
            for key, value in loader_kwargs.items():
                setattr(self, key, value)

        def compose_mapping_node(self, anchor):
            """Capture mapping node anchors during composition."""
            node = super().compose_mapping_node(anchor)
            if anchor:
                captured_anchors[anchor] = node
            return node

        def compose_sequence_node(self, anchor):
            """Capture sequence node anchors during composition."""
            node = super().compose_sequence_node(anchor)
            if anchor:
                captured_anchors[anchor] = node
            return node

        def compose_scalar_node(self, anchor):
            """Capture scalar node anchors during composition."""
            node = super().compose_scalar_node(anchor)
            if anchor:
                captured_anchors[anchor] = node
            return node

    return AnchorCapturingLoader


def safe_yaml_operation(operation_func, default_return=None, suppress_errors=True):
    """
    Execute a YAML operation with consistent error handling.

    This wrapper implements the common error handling pattern used across
    SmartYAML for YAML parsing operations that should fail gracefully.

    Args:
        operation_func: Function to execute (should be a callable)
        default_return: Value to return if operation fails
        suppress_errors: Whether to suppress exceptions and return default

    Returns:
        Result of operation_func, or default_return if it fails
    """
    try:
        return operation_func()
    except Exception:
        if suppress_errors:
            return default_return
        else:
            raise


def load_yaml_for_anchor_extraction(
    yaml_content: str, loader_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Load YAML content specifically for anchor extraction.

    This function implements the common pattern used for extracting anchors
    from YAML files during template preprocessing.

    Args:
        yaml_content: YAML content string to parse
        loader_context: Loader context dictionary

    Returns:
        Dictionary of captured anchors (anchor_name -> yaml_node)
    """
    captured_anchors = {}

    def extract_anchors():
        # Import here to avoid circular dependencies
        pass

        # Create anchor-capturing loader
        AnchorCapturingLoader = create_anchor_capturing_loader(
            SmartYAMLLoader,
            captured_anchors,
            base_path=loader_context.get("base_path"),
            template_path=loader_context.get("template_path"),
            import_stack=loader_context.get("import_stack", set()),
            max_file_size=loader_context.get("max_file_size"),
            max_recursion_depth=loader_context.get("max_recursion_depth"),
            expansion_variables=loader_context.get("expansion_variables", {}),
            accumulated_vars=loader_context.get("accumulated_vars", {}),
        )

        # Parse YAML to extract anchors (result is discarded)
        yaml.load(yaml_content, Loader=AnchorCapturingLoader)

        return captured_anchors

    # Use safe operation with empty dict as default
    return safe_yaml_operation(extract_anchors, default_return={})
