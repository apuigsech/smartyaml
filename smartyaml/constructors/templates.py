"""
Template constructor for SmartYAML
"""

from pathlib import Path
from typing import Any, Dict

import yaml

from ..exceptions import SmartYAMLError
from ..utils.file_utils import read_file
from ..utils.loader_utils import create_loader_context
from ..utils.validation_utils import (
    check_recursion_limit,
    validate_template_name,
    validate_template_path,
)
from .base import FileBasedConstructor


class TemplateConstructor(FileBasedConstructor):
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
        """Load and parse template YAML file with variable accumulation."""
        template_file = params["resolved_file_path"]
        template_base = params["template_base"]
        loader_context = self.get_loader_context(loader)

        # Read template file content
        yaml_content = read_file(template_file, loader_context["max_file_size"])

        # Create a new loader with recursion tracking and parent context inheritance
        # Lazy import to avoid circular dependencies
        from ..loader import SmartYAMLLoader

        new_import_stack = loader_context["import_stack"].copy()
        new_import_stack.add(template_file)

        ConfiguredLoader = create_loader_context(
            SmartYAMLLoader,
            template_base,
            loader_context["template_path"],
            new_import_stack,
            loader_context["max_file_size"],
            loader_context["max_recursion_depth"],
            None,  # No expansion variables needed
            loader,  # Pass parent loader for variable inheritance
        )

        # Load template 
        result = yaml.load(yaml_content, Loader=ConfiguredLoader)
        
        # Extract __vars from the loaded template and accumulate them in parent loader
        if isinstance(result, dict) and '__vars' in result:
            template_vars = result['__vars']
            if isinstance(template_vars, dict) and hasattr(loader, 'accumulate_vars'):
                loader.accumulate_vars(template_vars)
        
        return result


# Create instance for registration
template_constructor = TemplateConstructor()
