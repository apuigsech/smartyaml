"""
Template constructor for SmartYAML
"""

from typing import Any, Dict, List, Tuple

import yaml

from ..utils.file_utils import read_file
from ..utils.loader_utils import create_loader_context
from ..utils.validation_utils import (
    check_recursion_limit,
    validate_template_name,
    validate_template_path,
)
from .base import FileBasedConstructor
from .yaml_file_loader import YamlFileLoaderMixin


class TemplatePreProcessor:
    """
    Pre-processes templates to enable cross-file anchor sharing.
    This solves the timing issue where anchor references are resolved
    during composition but templates are loaded during construction.
    """

    @staticmethod
    def should_preprocess_document(content: str) -> bool:
        """Check if document contains template directives that need preprocessing."""
        from ..performance_optimizations import optimized_patterns

        return optimized_patterns.has_template_references(content)

    @staticmethod
    def extract_template_references(content: str) -> List[str]:
        """Extract template names from !template directives in the document."""
        from ..performance_optimizations import optimized_patterns

        return optimized_patterns.extract_template_names(content)

    def preprocess_document_for_anchors(
        self, content: str, loader_context
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Pre-process document to extract template anchors and make them available.
        Returns modified content and collected template anchors.
        """
        # Extract template references from the document
        template_names = self.extract_template_references(content)

        if not template_names:
            return content, {}

        # Collect all template anchors
        all_template_anchors = {}

        for template_name in template_names:
            try:
                template_anchors = self._extract_anchors_from_template(
                    template_name, loader_context
                )
                all_template_anchors.update(template_anchors)
            except Exception:
                # If template loading fails, we'll let the normal template
                # constructor handle the error during actual loading
                continue

        return content, all_template_anchors

    def _extract_anchors_from_template(
        self, template_name: str, loader_context
    ) -> Dict[str, Any]:
        """Extract anchors from a specific template file."""
        try:
            # Validate template name
            validate_template_name(template_name, "!template")

            # Get and validate template base path
            template_base = validate_template_path(loader_context["template_path"])

            # Construct full path to template file
            template_file = template_base / f"{template_name}.yaml"
            template_file_resolved = template_file.resolve()

            # Security check
            template_base_resolved = template_base.resolve()
            try:
                template_file_resolved.relative_to(template_base_resolved)
            except ValueError:
                from ..exceptions import InvalidPathError

                raise InvalidPathError(
                    f"Template path '{template_name}' resolves outside the template directory"
                )

            # Read template file
            yaml_content = read_file(
                template_file_resolved, loader_context["max_file_size"]
            )

            # Create simple loader to extract anchors
            from ..loader import SmartYAMLLoader

            # Create extraction loader that captures anchors during composition
            ConfiguredLoader = create_loader_context(
                SmartYAMLLoader,
                template_base,
                loader_context["template_path"],
                set(),  # Empty import stack for extraction
                loader_context["max_file_size"],
                loader_context["max_recursion_depth"],
                None,
                None,
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

            # Parse template to capture anchors during composition
            yaml.load(yaml_content, Loader=AnchorCapturingLoader)

            # Return captured anchors
            return captured_anchors

        except Exception:
            # If extraction fails, return empty - normal template loading will handle errors
            pass

        return {}


class TemplateConstructor(FileBasedConstructor, YamlFileLoaderMixin):
    """
    Constructor for !template template_name directive.
    Equivalent to !import_yaml($SMARTYAML_TMPL/template_name.yaml)
    """

    def __init__(self):
        super().__init__("!template")

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract template name from YAML node."""
        template_name = loader.construct_scalar(node)
        return {"template_name": template_name}

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate template name parameter."""
        validate_template_name(params["template_name"], self.directive_name)

    def apply_security_checks(self, loader, params: Dict[str, Any]) -> None:
        """Apply template-specific security checks."""
        loader_context = self.get_loader_context(loader)

        # Get and validate template base path
        template_base = validate_template_path(loader_context["template_path"])

        # Construct full path to template file
        template_name = params["template_name"]
        template_file = template_base / f"{template_name}.yaml"

        # Resolve the path and ensure it stays within template_base
        template_file_resolved = template_file.resolve()
        template_base_resolved = template_base.resolve()

        try:
            # Verify that the resolved template file is within the template base directory
            template_file_resolved.relative_to(template_base_resolved)
        except ValueError:
            from ..exceptions import InvalidPathError

            raise InvalidPathError(
                f"Template path '{template_name}' resolves outside the template directory: "
                f"{template_file_resolved} is not within {template_base_resolved}"
            )

        # Check recursion limits
        check_recursion_limit(
            loader_context["import_stack"],
            template_file_resolved,
            loader_context["max_recursion_depth"],
        )

        # Store resolved paths for use in execute()
        params["template_base"] = template_base
        params["resolved_file_path"] = template_file_resolved

    def execute(self, loader, params: Dict[str, Any]) -> Any:
        """Load and parse template YAML file with anchor pre-processing and variable accumulation."""
        template_file = params["resolved_file_path"]
        loader_context = self.get_loader_context(loader)

        # Use the mixin to load the YAML file with anchor preprocessing enabled
        return self.load_yaml_file(
            file_path=template_file,
            loader_context=loader_context,
            parent_loader=loader,
            enable_anchor_preprocessing=True,
        )


# Create instance for registration
template_constructor = TemplateConstructor()
