"""
Template preprocessing service for SmartYAML loading pipeline.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml


class TemplatePreprocessor:
    """
    Handles template preprocessing for cross-file anchor sharing.

    This class centralizes template preprocessing logic that was previously
    embedded in the main load() function.
    """

    def __init__(self):
        # Cache for preprocessed templates to avoid re-parsing
        self._anchor_cache: Dict[str, Dict[str, Any]] = {}

    def preprocess_content(
        self, content: str, template_path: Optional[Path] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Preprocess content to extract template anchors for cross-file sharing.

        Args:
            content: Raw YAML content string
            template_path: Path to template directory

        Returns:
            Tuple of (processed_content, extracted_anchors)
        """
        if not template_path:
            # No template preprocessing without template path
            return content, {}

        # Import here to avoid circular dependencies
        from ..constructors.templates import TemplatePreProcessor

        preprocessor = TemplatePreProcessor()

        if not preprocessor.should_preprocess_document(content):
            return content, {}

        # Create loader context for preprocessing
        loader_context = {
            "template_path": template_path.resolve() if template_path else None,
            "max_file_size": None,  # Will use config defaults
            "max_recursion_depth": None,  # Will use config defaults
        }

        # Extract anchors from templates
        processed_content, template_anchors = (
            preprocessor.preprocess_document_for_anchors(content, loader_context)
        )

        return processed_content, template_anchors

    def get_cached_anchors(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached anchors for a template if available.

        Args:
            template_name: Name of the template

        Returns:
            Cached anchors if available, None otherwise
        """
        return self._anchor_cache.get(template_name)

    def cache_anchors(self, template_name: str, anchors: Dict[str, Any]) -> None:
        """
        Cache anchors for a template.

        Args:
            template_name: Name of the template
            anchors: Anchors to cache
        """
        self._anchor_cache[template_name] = anchors.copy()

    def clear_cache(self) -> None:
        """Clear the anchor cache."""
        self._anchor_cache.clear()

    def process_inline_templates(
        self,
        content: str,
        base_path: Path,
        template_path: Optional[Path] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Process __template blocks before main YAML parsing.

        This method extracts __template blocks, processes them through the full
        SmartYAML pipeline, and merges the results back into the main document
        before it gets parsed.

        Args:
            content: Raw YAML content string
            base_path: Base directory for resolving relative paths
            template_path: Path to template directory
            variables: Variables for expansion

        Returns:
            Processed YAML content with templates expanded
        """
        if not self._has_inline_template(content):
            return content

        try:
            # Parse the document to extract template blocks
            # Note: We can't use yaml.safe_load because content may have SmartYAML directives
            # Instead, we need to parse manually or use a more flexible approach

            # Try parsing with safe_load first (for simple cases)
            try:
                raw_data = yaml.safe_load(content)
            except Exception:
                # For now, if we can't parse with safe_load, skip preprocessing
                # The content will be processed in the main pipeline
                return content

            if not isinstance(raw_data, dict) or "__template" not in raw_data:
                return content

            # Extract template and document parts
            template_data = raw_data["__template"]
            document_data = {k: v for k, v in raw_data.items() if k != "__template"}

            # Validate template data
            if template_data is None:
                raise ValueError("__template cannot be null")
            if not isinstance(template_data, dict):
                raise ValueError(
                    f"__template must be a mapping, got {type(template_data).__name__}"
                )

            # Pre-collect variables from external templates and document __vars
            merged_variables = self._collect_template_variables(
                template_data, document_data, base_path, template_path, variables
            )

            # Process template through full SmartYAML pipeline with collected variables
            processed_template = self._process_template_through_smartyaml(
                template_data, base_path, template_path, merged_variables
            )

            # Merge template with document with extend support (document takes precedence)
            merged_data = self._deep_merge_with_extend_support(
                processed_template, document_data
            )

            # Convert back to YAML string
            return yaml.dump(merged_data, default_flow_style=False, allow_unicode=True)

        except Exception:
            # If template processing fails, return original content
            # The error will be caught during main YAML parsing
            return content

    def _has_inline_template(self, content: str) -> bool:
        """
        Check if content contains __template directive using regex.

        Args:
            content: YAML content string

        Returns:
            True if __template directive is found
        """
        # Use optimized pre-compiled pattern for performance
        from ..performance_optimizations import optimized_patterns

        return optimized_patterns.has_template_directive(content)

    def _process_template_through_smartyaml(
        self,
        template_data: Dict[str, Any],
        base_path: Path,
        template_path: Optional[Path] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process template data through SmartYAML loader directly.

        This method processes templates without going through the full pipeline
        to avoid circular dependencies.

        Args:
            template_data: Template data dictionary
            base_path: Base directory for resolving paths
            template_path: Template directory path
            variables: Variables for expansion

        Returns:
            Fully processed template data
        """
        # Convert template data to YAML string
        template_yaml = yaml.dump(
            template_data, default_flow_style=False, allow_unicode=True
        )

        # Import the SmartYAML loader directly to avoid circular dependencies
        from ..loader import SmartYAMLLoader

        # Create a custom loader class with the right context
        class TemplateSmartYAMLLoader(SmartYAMLLoader):
            def __init__(self, stream):
                super().__init__(stream)
                self.base_path = base_path
                if template_path:
                    self.template_path = template_path
                self.import_stack = set()
                self.expansion_variables = variables or {}
                self.accumulated_vars = (variables or {}).copy()

        try:
            # Parse template YAML directly with SmartYAML loader
            processed_template = yaml.load(
                template_yaml, Loader=TemplateSmartYAMLLoader
            )

            # Process deferred expansions if needed
            if variables:
                from .. import process_deferred_expansions

                processed_template = process_deferred_expansions(
                    processed_template, variables
                )

            # Ensure result is a dictionary
            if not isinstance(processed_template, dict):
                return {"_template_value": processed_template}

            return processed_template

        except Exception as e:
            # If template processing fails, return original data
            # The error will be propagated up
            raise ValueError(f"Template processing failed: {str(e)}") from e

    def _collect_template_variables(
        self,
        template_data: Dict[str, Any],
        document_data: Dict[str, Any],
        base_path: Path,
        template_path: Optional[Path] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Pre-collect variables from external templates and document __vars.

        This solves the chicken-and-egg problem where inline template processing
        needs variables from external templates, but those templates haven't been
        loaded yet during preprocessing.

        Args:
            template_data: Template data dictionary
            document_data: Document data dictionary
            base_path: Base directory for resolving paths
            template_path: Template directory path
            variables: Function-level variables

        Returns:
            Merged variables dictionary with proper precedence
        """
        # Start with function-level variables (highest priority)
        merged_variables = (variables or {}).copy()

        # Extract document __vars (medium priority)
        if isinstance(document_data, dict) and "__vars" in document_data:
            document_vars = document_data["__vars"]
            if isinstance(document_vars, dict):
                # Document __vars have lower priority than function variables
                for key, value in document_vars.items():
                    if key not in merged_variables:
                        merged_variables[key] = value

        # Pre-load external template variables (lowest priority)
        if template_path:
            template_vars = self._extract_template_variables_from_content(
                template_data, base_path, template_path
            )
            for key, value in template_vars.items():
                if key not in merged_variables:
                    merged_variables[key] = value

        return merged_variables

    def _extract_template_variables_from_content(
        self, template_data: Dict[str, Any], base_path: Path, template_path: Path
    ) -> Dict[str, Any]:
        """
        Extract variables from external templates referenced in template_data.

        Uses regex-based parsing to extract !template() references and load their variables.

        Args:
            template_data: Template data to scan for !template() references
            base_path: Base directory for resolving paths
            template_path: Template directory path

        Returns:
            Dictionary of variables from external templates
        """
        external_vars = {}

        # Convert template_data back to YAML string for regex scanning
        import yaml

        template_yaml = yaml.dump(
            template_data, default_flow_style=False, allow_unicode=True
        )

        # Find all !template() references using regex
        import re

        template_pattern = r"!template\(([^)]+)\)"
        template_names = re.findall(template_pattern, template_yaml)

        # Load variables from each referenced template
        for template_name in template_names:
            self._load_template_variables_recursive(
                template_name, external_vars, template_path, set()
            )

        return external_vars

    def _load_template_variables_recursive(
        self,
        template_name: str,
        external_vars: Dict[str, Any],
        template_path: Path,
        visited: set,
    ) -> None:
        """
        Recursively load variables from a template and its dependencies.

        Args:
            template_name: Name of template to load (without .yaml extension)
            external_vars: Dictionary to accumulate variables into
            template_path: Template directory path
            visited: Set of visited templates to prevent cycles
        """
        template_file = template_path / f"{template_name}.yaml"
        template_key = str(template_file.resolve())

        # Prevent circular references
        if template_key in visited:
            return
        visited.add(template_key)

        try:
            # Read template file content
            from ..utils.file_utils import read_file

            template_content = read_file(template_file, max_size=None)

            # Extract __vars using regex (since we can't use safe_load on SmartYAML content)
            self._extract_vars_from_content(template_content, external_vars)

            # Find nested !template() references and recursively load them
            import re

            template_pattern = r"!template\(([^)]+)\)"
            nested_templates = re.findall(template_pattern, template_content)

            for nested_template in nested_templates:
                self._load_template_variables_recursive(
                    nested_template, external_vars, template_path, visited
                )

        except Exception:
            # If template loading fails, silently continue
            # The error will be caught during normal template processing
            pass
        finally:
            visited.discard(template_key)

    def _extract_vars_from_content(
        self, content: str, vars_dict: Dict[str, Any]
    ) -> None:
        """
        Extract __vars section from YAML content using regex.

        This method parses __vars without using yaml.safe_load to avoid
        issues with SmartYAML directives in the content.

        Args:
            content: YAML content string
            vars_dict: Dictionary to add extracted variables to
        """
        import re

        import yaml

        # Use regex to find the __vars section
        vars_pattern = r"^__vars:\s*\n((?:[ ]{2}.*\n?)*)"
        match = re.search(vars_pattern, content, re.MULTILINE)

        if match:
            vars_section = "__vars:\n" + match.group(1)

            try:
                # Parse just the vars section with safe_load
                vars_result = yaml.safe_load(vars_section)
                if isinstance(vars_result, dict) and "__vars" in vars_result:
                    vars_data = vars_result["__vars"]
                    if isinstance(vars_data, dict):
                        # Add variables with lowest priority (don't overwrite existing)
                        for key, value in vars_data.items():
                            if key not in vars_dict:
                                vars_dict[key] = value
            except Exception:
                # If parsing fails, skip this vars section
                pass

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
