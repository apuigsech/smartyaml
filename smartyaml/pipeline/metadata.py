"""
Stage 2: Metadata Processing

Handles extraction and processing of __vars, __template, and __schema metadata
with proper precedence and directive resolution within metadata fields.
"""

import copy
from typing import Any, Dict

from ..config import SmartYAMLConfig
from ..utils.merge import DeepMerger, MergeStrategy


class MetadataProcessor:
    """Stage 2: Process and extract metadata fields."""

    def __init__(self, config: SmartYAMLConfig):
        self.config = config

    def process(self, data: Dict[str, Any], context) -> Dict[str, Any]:
        """Extract and process all metadata fields."""
        if not isinstance(data, dict):
            return data

        # Extract metadata into context
        self._extract_variables(data, context)
        self._extract_template_config(data, context)
        self._extract_schema_config(data, context)

        return data

    def _extract_variables(self, data: Dict[str, Any], context) -> None:
        """Extract and merge __vars with proper precedence."""
        local_vars = data.get("__vars", {})

        # Validate that __vars is a dictionary
        if local_vars is not None and not isinstance(local_vars, dict):
            from ..exceptions import DirectiveSyntaxError

            raise DirectiveSyntaxError(
                "__vars must be a dictionary/mapping", str(context.file_path), "__vars"
            )

        # Process any directives within __vars first
        if local_vars:
            local_vars = self._process_metadata_directives(local_vars, context)

        # Variable precedence: Parameter > Local > Template > Include
        # Start with any existing variables (from templates/includes)
        merged_vars = copy.deepcopy(context.variables)

        # Check if this is template processing with main file variable overrides
        if hasattr(context, "_main_variables"):
            # Template processing: Start with template variables, then apply main file overrides
            merged_vars = copy.deepcopy(local_vars)  # Template variables as base
            self._deep_merge(
                merged_vars, context._main_variables
            )  # Main file overrides
        else:
            # Normal processing: merge local variables (higher precedence than template/include)
            self._deep_merge(merged_vars, local_vars)

        # Merge external parameter variables (highest precedence)
        self._deep_merge(merged_vars, self.config.variables)

        context.variables = merged_vars
        context.metadata["__vars"] = local_vars

    def _extract_template_config(self, data: Dict[str, Any], context) -> None:
        """Extract __template configuration."""
        template_config = data.get("__template")
        if template_config:
            # Process any directives within __template
            template_config = self._process_metadata_directives(
                template_config, context
            )
            context.metadata["__template"] = template_config

    def _extract_schema_config(self, data: Dict[str, Any], context) -> None:
        """Extract and prepare __schema for validation."""
        schema_config = data.get("__schema")
        if schema_config:
            # Process any directives within __schema
            schema_config = self._process_metadata_directives(schema_config, context)
            context.metadata["__schema"] = schema_config

    def _process_metadata_directives(self, metadata_value: Any, context) -> Any:
        """Process directives within metadata fields."""
        # Import here to avoid circular imports
        from .directives import DirectiveProcessor

        if hasattr(self, "_directive_processor"):
            directive_processor = self._directive_processor
        else:
            directive_processor = DirectiveProcessor(self.config)
            self._directive_processor = directive_processor

        return directive_processor.process_value(metadata_value, context)

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source dict into target dict using unified merger."""
        merger = DeepMerger(
            list_strategy=MergeStrategy.REPLACE,
            conflict_strategy=MergeStrategy.REPLACE,  # Metadata allows overrides
        )
        merger.merge(target, source)
