"""
Main loading pipeline for SmartYAML.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from .content_reader import ContentReader
from .inline_template_processor import InlineTemplateProcessor
from .template_preprocessor import TemplatePreprocessor
from .variable_merger import VariableMerger


class _ComponentSingletons:
    """Singleton manager for pipeline components to optimize performance."""

    def __init__(self):
        self._content_reader = None
        self._inline_template_processor = None
        self._template_preprocessor = None
        self._variable_merger = None

    def get_content_reader(self) -> ContentReader:
        """Get singleton ContentReader instance."""
        if self._content_reader is None:
            self._content_reader = ContentReader()
        return self._content_reader

    def get_template_preprocessor(self) -> TemplatePreprocessor:
        """Get singleton TemplatePreprocessor instance."""
        if self._template_preprocessor is None:
            self._template_preprocessor = TemplatePreprocessor()
        return self._template_preprocessor

    def get_inline_template_processor(self) -> InlineTemplateProcessor:
        """Get singleton InlineTemplateProcessor instance."""
        if self._inline_template_processor is None:
            self._inline_template_processor = InlineTemplateProcessor()
        return self._inline_template_processor

    def get_variable_merger(self) -> VariableMerger:
        """Get singleton VariableMerger instance."""
        if self._variable_merger is None:
            self._variable_merger = VariableMerger()
        return self._variable_merger


# Single instance of the component manager
_singletons = _ComponentSingletons()


class LoadPipeline:
    """
    Orchestrates the SmartYAML loading process through a composable pipeline.

    This class replaces the monolithic load() and loads() functions with a
    clean, testable, and maintainable architecture.
    """

    def __init__(
        self,
        content_reader: Optional[ContentReader] = None,
        inline_template_processor: Optional[InlineTemplateProcessor] = None,
        template_preprocessor: Optional[TemplatePreprocessor] = None,
        variable_merger: Optional[VariableMerger] = None,
    ):
        """
        Initialize the loading pipeline with pluggable components.

        Uses singleton components by default for better performance,
        but allows injection for testing or custom behavior.

        Args:
            content_reader: Content reading component
            inline_template_processor: Inline template processing component
            template_preprocessor: Template preprocessing component
            variable_merger: Variable merging component
        """
        self.content_reader = content_reader or _singletons.get_content_reader()
        self.inline_template_processor = (
            inline_template_processor or _singletons.get_inline_template_processor()
        )
        self.template_preprocessor = (
            template_preprocessor or _singletons.get_template_preprocessor()
        )
        self.variable_merger = variable_merger or _singletons.get_variable_merger()

    def load(
        self,
        stream: Union[str, Path],
        base_path: Optional[Union[str, Path]] = None,
        template_path: Optional[Union[str, Path]] = None,
        max_file_size: Optional[int] = None,
        max_recursion_depth: Optional[int] = None,
        remove_metadata: bool = True,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Load SmartYAML from file or string through the pipeline.

        Args:
            stream: YAML content as string or Path to file
            base_path: Base directory for resolving relative paths
            template_path: Base directory for templates
            max_file_size: Maximum file size in bytes
            max_recursion_depth: Maximum import recursion depth
            remove_metadata: Whether to remove fields prefixed with "__"
            variables: Dictionary of variables for expansion

        Returns:
            Parsed YAML data with SmartYAML directives processed
        """
        # Step 1: Read content
        content, resolved_base_path = self.content_reader.read_from_stream(
            stream, Path(base_path) if base_path else None
        )

        # Step 2: Preprocess templates (if needed)
        processed_content, template_anchors = (
            self.template_preprocessor.preprocess_content(
                content, Path(template_path) if template_path else None
            )
        )

        # Step 2.5: Process inline templates before main YAML parsing
        processed_content = self.template_preprocessor.process_inline_templates(
            processed_content,
            resolved_base_path,
            Path(template_path) if template_path else None,
            variables,
        )

        # Step 3: Create and configure loader
        loader_instance = self._create_loader(
            resolved_base_path=resolved_base_path,
            template_path=Path(template_path) if template_path else None,
            max_file_size=max_file_size,
            max_recursion_depth=max_recursion_depth,
            variables=variables,
            template_anchors=template_anchors,
        )

        # Step 4: Parse YAML
        result = yaml.load(processed_content, Loader=loader_instance)

        # Step 5: Process variables (needed before template processing)
        # Get the actual loader instance that was used during parsing
        actual_loader_instance = loader_instance._get_captured_instance()
        accumulated_variables = self.variable_merger.process_accumulated_variables(
            actual_loader_instance,  # Pass actual loader instance from parsing
            result,
            variables,
        )

        # Step 6: Process inline templates (__template directive)
        result = self._process_inline_template(
            result, resolved_base_path, template_path, accumulated_variables
        )

        # Step 7: Handle deferred expansions
        result = self._process_expansions(result, accumulated_variables)

        # Step 7.5: Clean up unprocessed extend markers
        result = self._process_unprocessed_extend_markers(result)

        # Step 8: Remove metadata if requested
        if remove_metadata:
            result = self._remove_metadata_fields(result)

        return result

    def _create_loader(
        self,
        resolved_base_path: Path,
        template_path: Optional[Path],
        max_file_size: Optional[int],
        max_recursion_depth: Optional[int],
        variables: Optional[Dict[str, Any]],
        template_anchors: Dict[str, Any],
    ):
        """Create and configure the YAML loader."""
        from ..loader import SmartYAMLLoader

        class ConfiguredSmartYAMLLoader(SmartYAMLLoader):
            def __init__(self, stream):
                super().__init__(stream)
                self.base_path = resolved_base_path
                if template_path:
                    self.template_path = template_path
                self.import_stack = set()
                self.max_file_size = max_file_size
                self.max_recursion_depth = max_recursion_depth
                self.expansion_variables = variables or {}
                self.accumulated_vars = (variables or {}).copy()
                # Pre-populate with template anchors for cross-file anchor sharing
                if template_anchors:
                    self.anchors.update(template_anchors)

        # Store captured loader instance at module level for variable processing
        _captured_loader_instance = None

        class LoaderWrapper(ConfiguredSmartYAMLLoader):
            def __init__(self, stream):
                super().__init__(stream)
                # Store reference for variable processing
                nonlocal _captured_loader_instance
                _captured_loader_instance = self

        # Store the capture reference on the class for pipeline access
        LoaderWrapper._get_captured_instance = lambda: _captured_loader_instance

        return LoaderWrapper

    def _process_inline_template(
        self,
        result: Any,
        resolved_base_path: Path,
        template_path: Optional[Path],
        accumulated_variables: Dict[str, Any],
    ) -> Any:
        """Process inline templates (__template directive)."""
        if not self.inline_template_processor.has_inline_template(result):
            return result

        # Build loader context for template processing
        loader_context = {
            "base_path": resolved_base_path,
            "template_path": template_path,
            "variables": accumulated_variables,  # Use accumulated variables including __vars
        }

        return self.inline_template_processor.process_inline_template(
            result, loader_context
        )

    def _process_expansions(
        self, result: Any, accumulated_variables: Dict[str, Any]
    ) -> Any:
        """Process deferred variable expansions."""
        from .. import process_deferred_expansions

        if accumulated_variables:
            # First expand variables that reference each other
            expanded_vars = self.variable_merger.expand_variables_recursively(
                accumulated_variables
            )
            # Then process deferred expansions in the main result
            result = process_deferred_expansions(result, expanded_vars)
        else:
            # Process deferred expansions with no variables (will raise errors if needed)
            result = process_deferred_expansions(result, {})

        return result

    def _remove_metadata_fields(self, data: Any) -> Any:
        """Remove metadata fields with "__" prefix."""
        from .. import remove_metadata_fields

        return remove_metadata_fields(data)

    def _process_unprocessed_extend_markers(self, data: Any) -> Any:
        """
        Process any remaining !extend markers that weren't handled during template merge.

        This handles cases where !extend is used without a template base to extend from,
        in which case the marker is converted to just the data array.

        Args:
            data: Data structure that may contain unprocessed extend markers

        Returns:
            Data with extend markers resolved
        """
        from ..constants import EXTEND_MARKER_KEY

        if isinstance(data, dict):
            # Check if this dict is an extend marker
            if EXTEND_MARKER_KEY in data and data[EXTEND_MARKER_KEY] is True:
                # This is an unprocessed extend marker - return just the data
                return data.get("data", [])
            else:
                # Recursively process nested dictionaries
                return {
                    key: self._process_unprocessed_extend_markers(value)
                    for key, value in data.items()
                }
        elif isinstance(data, list):
            # Recursively process list items
            return [self._process_unprocessed_extend_markers(item) for item in data]
        else:
            # Primitive value, return as-is
            return data
