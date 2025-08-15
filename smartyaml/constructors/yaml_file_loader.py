"""
YAML File Loader Mixin - Common functionality for loading YAML files.

This module provides shared functionality for constructors that need to load
YAML files, eliminating code duplication between TemplateConstructor and
ImportYamlConstructor.
"""

from pathlib import Path
from typing import Any, Dict

import yaml

from ..utils.file_utils import read_file
from ..utils.loader_utils import create_loader_context


class YamlFileLoaderMixin:
    """
    Mixin providing common YAML file loading functionality.

    This mixin extracts the common file loading logic used by both
    TemplateConstructor and ImportYamlConstructor, following the DRY principle
    while allowing each constructor to maintain its specific path resolution
    and validation logic.
    """

    def load_yaml_file(
        self,
        file_path: Path,
        loader_context: Dict[str, Any],
        parent_loader,
        enable_anchor_preprocessing: bool = False,
    ) -> Any:
        """
        Load and parse a YAML file with SmartYAML features.

        Args:
            file_path: Resolved path to the YAML file to load
            loader_context: Context information for the loader
            parent_loader: Parent loader for variable inheritance
            enable_anchor_preprocessing: Whether to enable cross-file anchor sharing

        Returns:
            Parsed YAML data with SmartYAML directives processed
        """
        # Read file content
        yaml_content = read_file(file_path, loader_context["max_file_size"])

        # Perform anchor preprocessing if enabled
        template_anchors = {}
        if enable_anchor_preprocessing:
            template_anchors = self._extract_anchors_from_yaml_content(
                yaml_content, file_path.parent, loader_context
            )

            # Transfer extracted anchors to parent loader BEFORE parsing
            # This enables cross-file anchor sharing
            if template_anchors and hasattr(parent_loader, "anchors"):
                for anchor_name, anchor_value in template_anchors.items():
                    parent_loader.anchors[anchor_name] = anchor_value

        # Create a new loader with recursion tracking and parent context inheritance
        # Lazy import to avoid circular dependencies
        from ..loader import SmartYAMLLoader

        new_import_stack = loader_context["import_stack"].copy()
        new_import_stack.add(file_path)

        # Pre-extract __vars from the YAML content to make them available during parsing
        file_vars = self._extract_vars_from_yaml_content(yaml_content)

        # Merge parent's accumulated vars with this file's vars for constructor availability
        # Parent variables should take precedence over file variables for inheritance
        expansion_variables = file_vars.copy() if file_vars else {}
        if (
            hasattr(parent_loader, "accumulated_vars")
            and parent_loader.accumulated_vars
        ):
            expansion_variables.update(parent_loader.accumulated_vars)

        ConfiguredLoader = create_loader_context(
            SmartYAMLLoader,
            loader_context.get("base_path", file_path.parent),
            loader_context.get("template_path"),
            new_import_stack,
            loader_context["max_file_size"],
            loader_context["max_recursion_depth"],
            expansion_variables,  # Pass merged variables for constructor use
            parent_loader,  # Pass parent loader for variable inheritance
        )

        # Load YAML - don't inherit anchors when preprocessing is enabled
        # (anchors are already transferred to parent loader during preprocessing)

        # Check if the content contains inline templates (__template:)
        # If so, we need to process templates, but avoid circular dependency with smartyaml.loads()
        if self._contains_inline_template(yaml_content):
            # Load with SmartYAML first
            result = yaml.load(yaml_content, Loader=ConfiguredLoader)

            # Then process templates using the inline template processor
            if isinstance(result, dict) and "__template" in result:
                from ..loading.inline_template_processor import InlineTemplateProcessor

                template_processor = InlineTemplateProcessor()

                # Merge parent's accumulated vars with this file's vars for template processing
                from ..utils.variable_substitution import extract_vars_metadata

                template_variables = getattr(
                    parent_loader, "accumulated_vars", {}
                ).copy()
                file_vars = extract_vars_metadata(result)
                if file_vars:
                    template_variables.update(file_vars)

                # Create a loader context for template processing
                template_context = {
                    "base_path": file_path.parent,
                    "template_path": loader_context.get("template_path"),
                    "variables": template_variables,
                }

                # Process the inline template
                result = template_processor.process_inline_template(
                    result, template_context
                )
        else:
            # Use standard YAML loading for files without templates
            result = yaml.load(yaml_content, Loader=ConfiguredLoader)

        # Extract __vars from the loaded file and accumulate them in parent loader
        from ..utils.yaml_parsing import extract_and_accumulate_vars

        extract_and_accumulate_vars(result, parent_loader)

        return result

    def _contains_inline_template(self, yaml_content: str) -> bool:
        """
        Check if YAML content contains __template directive.

        Args:
            yaml_content: YAML content string

        Returns:
            True if __template directive is found
        """
        # Use optimized pre-compiled pattern for performance
        from ..performance_optimizations import optimized_patterns

        return optimized_patterns.has_template_directive(yaml_content)

    def _extract_anchors_from_yaml_content(
        self, yaml_content: str, base_path: Path, loader_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract anchor definitions from YAML content by doing a preliminary parse.
        This allows anchors to be available during the main parsing phase.

        Args:
            yaml_content: Raw YAML content string
            base_path: Base directory for the YAML file
            loader_context: Loader context information

        Returns:
            Dictionary mapping anchor names to their YAML nodes
        """
        try:
            # Lazy import to avoid circular dependencies
            from ..loader import SmartYAMLLoader

            # Create a simple loader just for anchor extraction
            ConfiguredLoader = create_loader_context(
                SmartYAMLLoader,
                base_path,
                loader_context.get("template_path"),
                set(),  # Empty import stack for extraction
                loader_context["max_file_size"],
                loader_context["max_recursion_depth"],
                None,  # No expansion variables needed
                None,  # No parent loader needed for extraction
            )

            # Store captured anchors here
            captured_anchors = {}

            class AnchorCapturingLoader(ConfiguredLoader):
                def __init__(self, stream):
                    super().__init__(stream)

                def compose_mapping_node(self, anchor):
                    """Capture mapping anchors during composition."""
                    node = super().compose_mapping_node(anchor)
                    if anchor:
                        # Store the anchor and its node for later use
                        captured_anchors[anchor] = node
                    return node

                def compose_scalar_node(self, anchor):
                    """Capture scalar anchors during composition."""
                    node = super().compose_scalar_node(anchor)
                    if anchor:
                        captured_anchors[anchor] = node
                    return node

                def compose_sequence_node(self, anchor):
                    """Capture sequence anchors during composition."""
                    node = super().compose_sequence_node(anchor)
                    if anchor:
                        captured_anchors[anchor] = node
                    return node

            # Parse YAML content to capture anchors during composition
            yaml.load(yaml_content, Loader=AnchorCapturingLoader)

            # Return captured anchors
            return captured_anchors

        except Exception:
            # If extraction fails, return empty dict - normal loading will handle errors
            return {}

    def _extract_vars_from_yaml_content(self, yaml_content: str) -> Dict[str, Any]:
        """
        Pre-extract __vars from YAML content using regex parsing.

        This allows variables to be available to constructors during the main parse.
        Uses regex to avoid issues with unknown YAML constructors.

        Args:
            yaml_content: Raw YAML content string

        Returns:
            Dictionary of variables from __vars field, empty if not found or if parsing fails
        """
        try:
            pass

            import yaml

            # Use optimized pre-compiled pattern for performance
            from ..performance_optimizations import optimized_patterns

            vars_section = optimized_patterns.extract_vars_section(yaml_content)
            if vars_section:

                # Parse just the vars section with safe_load
                vars_result = yaml.safe_load(vars_section)
                if isinstance(vars_result, dict) and "__vars" in vars_result:
                    vars_data = vars_result["__vars"]
                    if isinstance(vars_data, dict):
                        return vars_data

        except Exception:
            # If extraction fails, return empty dict - main parsing will handle errors properly
            pass

        return {}
