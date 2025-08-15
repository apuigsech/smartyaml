"""
Conditional inclusion constructors for SmartYAML
"""

from typing import Any, Dict

import yaml

from ..exceptions import SmartYAMLError
from ..utils.file_utils import read_file
from ..utils.validation_utils import validate_constructor_args
from .base import ConditionalConstructor


class IncludeIfConstructor(ConditionalConstructor):
    """
    Constructor for !include_if [condition, filename] directive.
    Includes text file only if condition (environment variable) is truthy.
    """

    def __init__(self):
        super().__init__("!include_if")

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract condition and filename from YAML node."""
        if isinstance(node, yaml.SequenceNode):
            sequence = loader.construct_sequence(node)
            validate_constructor_args(sequence, 2, self.directive_name)
            condition, filename = sequence
        else:
            raise SmartYAMLError(
                f"{self.directive_name} expects a sequence: [condition, filename]"
            )

        return {"condition": condition, "filename": filename}

    def execute(self, loader, params: Dict[str, Any]) -> Any:
        """Include file content if condition is met."""
        # Check condition first
        if not self.should_include(params["condition"]):
            return None

        # Load file content
        file_path = params["resolved_file_path"]
        loader_context = self.get_loader_context(loader)
        return read_file(file_path, loader_context["max_file_size"])


class IncludeYamlIfConstructor(ConditionalConstructor):
    """
    Constructor for !include_yaml_if [condition, filename] directive.
    Includes YAML file only if condition (environment variable) is truthy.
    """

    def __init__(self):
        super().__init__("!include_yaml_if")

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract condition and filename from YAML node."""
        if isinstance(node, yaml.SequenceNode):
            sequence = loader.construct_sequence(node)
            validate_constructor_args(sequence, 2, self.directive_name)
            condition, filename = sequence
        else:
            raise SmartYAMLError(
                f"{self.directive_name} expects a sequence: [condition, filename]"
            )

        return {"condition": condition, "filename": filename}

    def execute(self, loader, params: Dict[str, Any]) -> Any:
        """Include YAML data if condition is met."""
        # Check condition first
        if not self.should_include(params["condition"]):
            return None

        # Load and parse YAML file
        file_path = params["resolved_file_path"]
        loader_context = self.get_loader_context(loader)

        yaml_content = read_file(file_path, loader_context["max_file_size"])

        # Use shared YAML parsing utility
        from ..loader import SmartYAMLLoader
        from ..utils.yaml_parsing import (
            create_import_stack_copy,
            load_yaml_with_context,
        )

        new_import_stack = create_import_stack_copy(loader_context, file_path)

        return load_yaml_with_context(
            yaml_content=yaml_content,
            loader_class=SmartYAMLLoader,
            base_path=loader_context["base_path"],
            template_path=loader_context["template_path"],
            import_stack=new_import_stack,
            max_file_size=loader_context["max_file_size"],
            max_recursion_depth=loader_context["max_recursion_depth"],
            expansion_variables=None,  # No expansion variables needed
            parent_loader=loader,  # Pass parent loader for variable inheritance
            accumulate_vars=True,
        )


# Create instances for registration
include_if_constructor = IncludeIfConstructor()
include_yaml_if_constructor = IncludeYamlIfConstructor()
