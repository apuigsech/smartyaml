"""
Inline template processor for SmartYAML __template directive.
"""

from typing import Any, Dict, Optional

from ..exceptions import ConstructorError


class InlineTemplateProcessor:
    """
    Processes __template directive for inline template inheritance.

    The __template directive allows defining a base template within the same YAML file,
    which is then merged with the rest of the document using deep merge semantics.
    """

    def __init__(self):
        self.template_key = "__template"

    def has_inline_template(self, data: Any) -> bool:
        """
        Check if the data contains an __template directive.

        Args:
            data: Parsed YAML data

        Returns:
            True if __template is present at root level
        """
        return isinstance(data, dict) and self.template_key in data

    def process_inline_template(
        self, data: Dict[str, Any], loader_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process the __template directive and merge with document.

        NOTE: As of the new architecture, inline templates are processed during
        preprocessing (before YAML parsing). This method is kept for backwards
        compatibility and as a fallback for edge cases where preprocessing
        might be skipped.

        Args:
            data: Parsed YAML document containing __template
            loader_context: Context from the YAML loader

        Returns:
            Merged document with template as base, or original data if already processed

        Raises:
            ConstructorError: If template processing fails
        """
        if not self.has_inline_template(data):
            return data

        # Note: In the new architecture, templates should already be processed
        # during preprocessing. If we get here with a __template block, it means
        # either:
        # 1. Preprocessing was skipped (edge case)
        # 2. There was an error during preprocessing
        # 3. This is a nested template scenario

        # For now, we'll fall back to the original processing logic
        # but this path should rarely be taken

        try:
            # Extract template and document parts
            template_data = data[self.template_key]
            document_data = {k: v for k, v in data.items() if k != self.template_key}

            # Validate template data
            self._validate_template_data(template_data)

            # For backwards compatibility, process template content
            # In the new architecture, this should usually be already resolved
            processed_template = self._process_template_content_simple(template_data)

            # Deep merge template with document with extend support (document takes precedence)
            merged_result = self._deep_merge_with_extend_support(
                processed_template, document_data
            )

            return merged_result

        except Exception as e:
            if isinstance(e, ConstructorError):
                raise
            raise ConstructorError(
                directive_name="__template",
                message=f"Failed to process inline template: {str(e)}",
                location=None,
            ) from e

    def _validate_template_data(self, template_data: Any) -> None:
        """
        Validate that template data is in correct format.

        Args:
            template_data: The __template content

        Raises:
            ConstructorError: If template data is invalid
        """
        if template_data is None:
            raise ConstructorError(
                directive_name="__template",
                message="__template cannot be null. Remove the __template key if not needed.",
                location=None,
            )

        if not isinstance(template_data, dict):
            raise ConstructorError(
                directive_name="__template",
                message=(
                    f"__template must be a YAML mapping/object, got {type(template_data).__name__}. "
                    f"Example: __template:\n  key: value\n  nested:\n    field: data"
                ),
                location=None,
            )

    def _process_template_content_simple(
        self, template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simple template content processing for backwards compatibility.

        In the new architecture, templates are processed during preprocessing.
        This simplified version is kept as a fallback.

        Args:
            template_data: Template data dictionary

        Returns:
            Template data (mostly as-is, since directives should be pre-processed)
        """
        # In the new architecture, template data should already be processed
        # This is just a safety fallback
        if not isinstance(template_data, dict):
            return {"_template_value": template_data}

        return template_data

    def _contains_directives(self, data: Any) -> bool:
        """
        Check if data contains SmartYAML directives that need processing.

        Args:
            data: Data to check for directives

        Returns:
            True if directives are found
        """
        if isinstance(data, dict):
            # Check for deferred expansion markers
            if "__smartyaml_expand_deferred" in data:
                return True
            # Check for SmartYAML YAML node markers (used by constructors like !import_yaml)
            for key, value in data.items():
                if hasattr(value, "yaml_tag") and value.yaml_tag.startswith("!"):
                    return True
            # Recursively check nested dictionaries
            return any(self._contains_directives(v) for v in data.values())
        elif isinstance(data, list):
            # Recursively check list items
            return any(self._contains_directives(item) for item in data)
        elif hasattr(data, "yaml_tag") and data.yaml_tag.startswith("!"):
            # Direct YAML node with tag
            return True

        return False

    def _deep_merge_with_extend_support(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries with support for !extend array concatenation.

        This enhanced merge function handles the special case where arrays marked
        with !extend should be concatenated instead of replaced.

        Args:
            base: Base dictionary (template data)
            override: Override dictionary (document data)

        Returns:
            Merged dictionary with extend support
        """
        import copy

        from ..constants import EXTEND_MARKER_KEY

        # Start with a deep copy of base
        result = copy.deepcopy(base)

        # Process each key in override
        for key, value in override.items():
            if key not in result:
                # Key doesn't exist in base, just add it
                result[key] = copy.deepcopy(value)
            else:
                # Key exists in both, need to merge
                base_value = result[key]

                # Check if value is marked for extension
                if (
                    isinstance(value, dict)
                    and EXTEND_MARKER_KEY in value
                    and value[EXTEND_MARKER_KEY] is True
                ):

                    # Handle !extend array concatenation
                    extend_data = value.get("data", [])

                    if isinstance(base_value, list) and isinstance(extend_data, list):
                        # Concatenate arrays: base + extend
                        result[key] = base_value + extend_data
                    else:
                        # If types don't match, fallback to replacement
                        result[key] = extend_data

                elif isinstance(base_value, dict) and isinstance(value, dict):
                    # Both are dicts, recursively merge
                    result[key] = self._deep_merge_with_extend_support(
                        base_value, value
                    )
                else:
                    # Different types or not both dicts, override wins
                    result[key] = copy.deepcopy(value)

        return result
