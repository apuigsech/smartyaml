"""
Special import_yaml constructor that supports merging with sibling fields
"""

from typing import Any, Dict

import yaml

from ..exceptions import SmartYAMLError
from ..merge import merge_yaml_data
from ..utils.file_utils import read_file
from ..utils.path_utils import resolve_path
from ..utils.validation_utils import check_recursion_limit
from .base import FileBasedConstructor


class ImportYamlMergeConstructor(FileBasedConstructor):
    """
    Multi-constructor for !import_yaml that supports field merging.

    This handles the syntax:
    field: !import_yaml filename
      local_field: value

    The imported YAML is merged with local_field taking precedence.
    """

    def __init__(self):
        super().__init__("!import_yaml")

    def __call__(self, loader, tag_suffix, node):
        """
        Multi-constructor entry point that handles tag suffixes.
        """
        try:
            # Extract parameters including tag suffix
            params = self.extract_parameters_with_suffix(loader, tag_suffix, node)

            # Apply validations and security checks
            self.validate_parameters(params)
            self.apply_security_checks_for_merge(loader, params)

            # Execute the main logic
            result = self.execute(loader, params)

            return self.post_process(result, params)

        except Exception as e:
            # Handle errors with enhanced context
            from ..error_context import ErrorContextBuilder, enhance_error_with_context

            context = ErrorContextBuilder.build_constructor_context(
                self.directive_name,
                loader,
                params if "params" in locals() else {},
                node,
            )
            raise enhance_error_with_context(e, context) from e

    def extract_parameters_with_suffix(
        self, loader, tag_suffix, node
    ) -> Dict[str, Any]:
        """Extract parameters including handling of tag suffix."""
        if isinstance(node, yaml.ScalarNode):
            # Simple import without merging
            filename = loader.construct_scalar(node)
            local_data = {}
        elif isinstance(node, yaml.MappingNode):
            # Import with local field merging
            mapping = loader.construct_mapping(node)

            # The filename should be the tag suffix or the first unmapped key
            if tag_suffix:
                filename = tag_suffix
                local_data = mapping
            else:
                # Find filename in mapping (look for the key without a proper value)
                filename = None
                local_data = {}

                for key, value in mapping.items():
                    if value is None:  # This might be our filename
                        filename = key
                    else:
                        local_data[key] = value

                if filename is None:
                    raise SmartYAMLError(
                        f"{self.directive_name} mapping requires a filename"
                    )
        else:
            raise SmartYAMLError(
                f"{self.directive_name} expects a scalar filename or mapping with overrides"
            )

        return {"filename": filename, "local_data": local_data}

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Standard extract_parameters method (not used for multi-constructor)."""
        # This is required by the base class but not used in multi-constructor mode
        return {}

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate filename parameter."""
        if not params.get("filename") or not isinstance(params["filename"], str):
            raise SmartYAMLError(f"{self.directive_name} requires a non-empty filename")

    def apply_security_checks_for_merge(self, loader, params: Dict[str, Any]) -> None:
        """Apply file-based security checks for merge constructor."""
        if "filename" not in params:
            return

        loader_context = self.get_loader_context(loader)

        file_path = resolve_path(params["filename"], loader_context["base_path"])
        check_recursion_limit(
            loader_context["import_stack"],
            file_path,
            loader_context["max_recursion_depth"],
        )

        # Store resolved path for use in execute()
        params["resolved_file_path"] = file_path

    def execute(self, loader, params: Dict[str, Any]) -> Any:
        """Load YAML file and merge with local data."""
        file_path = params["resolved_file_path"]
        local_data = params["local_data"]
        loader_context = self.get_loader_context(loader)

        yaml_content = read_file(file_path, loader_context["max_file_size"])

        # Use shared YAML parsing utility
        from ..loader import SmartYAMLLoader
        from ..utils.yaml_parsing import (
            create_import_stack_copy,
            load_yaml_with_context,
        )

        new_import_stack = create_import_stack_copy(loader_context, file_path)

        imported_data = load_yaml_with_context(
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

        # Merge with local data if present
        return merge_yaml_data(imported_data, local_data)


# Function wrapper for multi-constructor registration
def import_yaml_merge_constructor(loader, tag_suffix, node):
    """Multi-constructor wrapper for registration."""
    constructor = ImportYamlMergeConstructor()
    return constructor(loader, tag_suffix, node)
