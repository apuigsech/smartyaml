"""
YAML File Loader Mixin - Common functionality for loading YAML files.

This module provides shared functionality for constructors that need to load 
YAML files, eliminating code duplication between TemplateConstructor and 
ImportYamlConstructor.
"""

from pathlib import Path
from typing import Any, Dict, Optional

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
        enable_anchor_preprocessing: bool = False
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
            if template_anchors and hasattr(parent_loader, 'anchors'):
                for anchor_name, anchor_value in template_anchors.items():
                    parent_loader.anchors[anchor_name] = anchor_value
        
        # Create a new loader with recursion tracking and parent context inheritance
        # Lazy import to avoid circular dependencies
        from ..loader import SmartYAMLLoader
        
        new_import_stack = loader_context["import_stack"].copy()
        new_import_stack.add(file_path)
        
        ConfiguredLoader = create_loader_context(
            SmartYAMLLoader,
            loader_context.get("base_path", file_path.parent),
            loader_context.get("template_path"),
            new_import_stack,
            loader_context["max_file_size"],
            loader_context["max_recursion_depth"],
            None,  # No expansion variables needed
            parent_loader,  # Pass parent loader for variable inheritance
        )
        
        # Load YAML - don't inherit anchors when preprocessing is enabled
        # (anchors are already transferred to parent loader during preprocessing)
        result = yaml.load(yaml_content, Loader=ConfiguredLoader)
        
        # Extract __vars from the loaded file and accumulate them in parent loader
        if isinstance(result, dict) and '__vars' in result:
            file_vars = result['__vars']
            if isinstance(file_vars, dict) and hasattr(parent_loader, 'accumulate_vars'):
                parent_loader.accumulate_vars(file_vars)
        
        return result
    
    def _extract_anchors_from_yaml_content(
        self, 
        yaml_content: str, 
        base_path: Path, 
        loader_context: Dict[str, Any]
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