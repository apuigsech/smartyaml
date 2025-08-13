"""
Loader utilities for SmartYAML
"""

from pathlib import Path
from typing import Any, Dict, Optional, Set


def create_loader_context(
    base_loader,
    base_path: Path,
    template_path: Optional[Path] = None,
    import_stack: Optional[Set[Path]] = None,
    max_file_size: Optional[int] = None,
    max_recursion_depth: Optional[int] = None,
    expansion_variables: Optional[Dict[str, Any]] = None,
    parent_loader=None,
):
    """
    Create a configured loader with context information.

    Args:
        base_loader: The SmartYAMLLoader class to extend
        base_path: Base path for resolving relative imports
        template_path: Path for template resolution
        import_stack: Current import stack for cycle detection
        max_file_size: Maximum file size limit
        max_recursion_depth: Maximum recursion depth
        expansion_variables: Variables available for expansion
        parent_loader: Parent loader to inherit accumulated variables from

    Returns:
        Configured loader class
    """

    class ConfiguredLoader(base_loader):
        def __init__(self, stream):
            super().__init__(stream)
            self.base_path = base_path
            if template_path:
                self.template_path = template_path
            self.import_stack = import_stack or set()
            self.max_file_size = max_file_size
            self.max_recursion_depth = max_recursion_depth
            self.expansion_variables = expansion_variables or {}

            # Initialize accumulated vars with parent's accumulated variables
            if parent_loader and hasattr(parent_loader, "accumulated_vars"):
                self.accumulated_vars = parent_loader.accumulated_vars.copy()
            else:
                self.accumulated_vars = (expansion_variables or {}).copy()

    return ConfiguredLoader
