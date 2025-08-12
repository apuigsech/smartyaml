"""
Main loading pipeline for SmartYAML.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from .content_reader import ContentReader
from .template_preprocessor import TemplatePreprocessor
from .variable_merger import VariableMerger

# Global singleton components for performance optimization
_content_reader = None
_template_preprocessor = None  
_variable_merger = None

def get_content_reader() -> ContentReader:
    """Get singleton ContentReader instance."""
    global _content_reader
    if _content_reader is None:
        _content_reader = ContentReader()
    return _content_reader

def get_template_preprocessor() -> TemplatePreprocessor:
    """Get singleton TemplatePreprocessor instance."""
    global _template_preprocessor
    if _template_preprocessor is None:
        _template_preprocessor = TemplatePreprocessor()
    return _template_preprocessor

def get_variable_merger() -> VariableMerger:
    """Get singleton VariableMerger instance."""
    global _variable_merger
    if _variable_merger is None:
        _variable_merger = VariableMerger()
    return _variable_merger


class LoadPipeline:
    """
    Orchestrates the SmartYAML loading process through a composable pipeline.
    
    This class replaces the monolithic load() and loads() functions with a
    clean, testable, and maintainable architecture.
    """
    
    def __init__(
        self,
        content_reader: Optional[ContentReader] = None,
        template_preprocessor: Optional[TemplatePreprocessor] = None,
        variable_merger: Optional[VariableMerger] = None
    ):
        """
        Initialize the loading pipeline with pluggable components.
        
        Uses singleton components by default for better performance,
        but allows injection for testing or custom behavior.
        
        Args:
            content_reader: Content reading component
            template_preprocessor: Template preprocessing component
            variable_merger: Variable merging component
        """
        self.content_reader = content_reader or get_content_reader()
        self.template_preprocessor = template_preprocessor or get_template_preprocessor()
        self.variable_merger = variable_merger or get_variable_merger()
    
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
        processed_content, template_anchors = self.template_preprocessor.preprocess_content(
            content, Path(template_path) if template_path else None
        )
        
        # Step 3: Create and configure loader
        loader_instance = self._create_loader(
            resolved_base_path=resolved_base_path,
            template_path=Path(template_path) if template_path else None,
            max_file_size=max_file_size,
            max_recursion_depth=max_recursion_depth,
            variables=variables,
            template_anchors=template_anchors
        )
        
        # Step 4: Parse YAML
        result = yaml.load(processed_content, Loader=loader_instance)
        
        # Step 5: Process variables
        accumulated_variables = self.variable_merger.process_accumulated_variables(
            loader_instance._wrapped_loader_instance if hasattr(loader_instance, '_wrapped_loader_instance') else None,
            result,
            variables
        )
        
        # Step 6: Handle deferred expansions
        result = self._process_expansions(result, accumulated_variables)
        
        # Step 7: Remove metadata if requested
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
        template_anchors: Dict[str, Any]
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
        
        # Wrapper to capture loader instance for variable processing
        class LoaderWrapper(ConfiguredSmartYAMLLoader):
            def __init__(self, stream):
                super().__init__(stream)
                # Store reference for variable processing
                LoaderWrapper._wrapped_loader_instance = self
        
        return LoaderWrapper
    
    def _process_expansions(self, result: Any, accumulated_variables: Dict[str, Any]) -> Any:
        """Process deferred variable expansions."""
        from .. import process_deferred_expansions
        
        if accumulated_variables:
            # First expand variables that reference each other
            expanded_vars = self.variable_merger.expand_variables_recursively(accumulated_variables)
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