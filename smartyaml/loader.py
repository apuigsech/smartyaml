"""
SmartYAML Loader with custom constructors
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import yaml

if TYPE_CHECKING:
    from .type_annotations import YAMLLoader, YAMLNode

from .registry import get_registry, register_default_constructors


class SmartYAMLLoader(yaml.SafeLoader):
    """
    Custom YAML Loader with SmartYAML directives support.
    Extends SafeLoader for security while adding custom constructors.
    """

    def __init__(self, stream):
        super().__init__(stream)

        # Set default paths
        self.base_path: Optional[Path] = None
        self.template_path: Optional[Path] = None


# Smart constructor dispatch for tags with parameters
def smart_constructor_dispatch(
    loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node
) -> Any:
    """
    Registry-based constructor dispatch for SmartYAML tags.
    Replaced the complex manual dispatch with a cleaner registry system.

    Args:
        loader: YAML loader instance
        tag_suffix: The tag suffix to dispatch
        node: YAML node containing the directive

    Returns:
        Result from the appropriate constructor
    """
    ensure_registry_initialized()  # Lazy initialization
    registry = get_registry()
    return registry.dispatch(loader, tag_suffix, node)


# Register the multi-constructor to handle all SmartYAML tags
SmartYAMLLoader.add_multi_constructor("!", smart_constructor_dispatch)

# Lazy initialization flag
_registry_initialized = False


def ensure_registry_initialized() -> None:
    """Ensure the constructor registry is initialized (lazy loading)."""
    global _registry_initialized
    if not _registry_initialized:
        # Initialize the registry with default constructors
        register_default_constructors()

        # Get registry instance for direct constructor access
        registry = get_registry()

        # Also register direct constructors for space-separated syntax
        for tag in registry.get_registered_tags():
            constructor = registry.get_constructor(tag)
            SmartYAMLLoader.add_constructor(tag, constructor)

        _registry_initialized = True


# Register the loader as the default for SmartYAML
# This allows yaml.load(content, Loader=SmartYAMLLoader) to work properly
