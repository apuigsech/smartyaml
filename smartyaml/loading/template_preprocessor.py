"""
Template preprocessing service for SmartYAML loading pipeline.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional


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
        self, 
        content: str, 
        template_path: Optional[Path] = None
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
        processed_content, template_anchors = preprocessor.preprocess_document_for_anchors(
            content, loader_context
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