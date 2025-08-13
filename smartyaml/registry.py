"""
Constructor registry system for SmartYAML
"""

from functools import lru_cache
from typing import Any, Callable, Dict, Optional

import yaml

from .exceptions import ConstructorError
from .parsing import ParsedTag, TagParser


class ConstructorRegistry:
    """
    Centralized registry for SmartYAML constructors.

    This class manages constructor registration and dispatching,
    replacing the complex manual dispatch logic in the loader.
    """

    def __init__(self):
        self._constructors: Dict[str, Callable] = {}
        self._tag_parser = TagParser()

    def register(self, tag: str, constructor: Callable) -> None:
        """
        Register a constructor for a specific tag.

        Args:
            tag: The YAML tag (e.g., '!import', '!env')
            constructor: The constructor function to handle the tag
        """
        if not tag.startswith("!"):
            tag = "!" + tag
        self._constructors[tag] = constructor

    def register_multiple(self, constructors: Dict[str, Callable]) -> None:
        """
        Register multiple constructors at once.

        Args:
            constructors: Dictionary mapping tags to constructor functions
        """
        for tag, constructor in constructors.items():
            self.register(tag, constructor)

    @lru_cache(maxsize=64)
    def get_constructor(self, tag: str) -> Optional[Callable]:
        """
        Get the constructor for a specific tag (cached).

        Args:
            tag: The YAML tag to look up

        Returns:
            The constructor function if found, None otherwise
        """
        if not tag.startswith("!"):
            tag = "!" + tag
        return self._constructors.get(tag)

    def dispatch(
        self, loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node
    ) -> Any:
        """
        Dispatch to the appropriate constructor based on the tag.

        This replaces the large smart_constructor_dispatch function with
        a cleaner registry-based approach.

        Args:
            loader: The YAML loader instance
            tag_suffix: The tag suffix from PyYAML multi-constructor
            node: The YAML node containing the tag value

        Returns:
            The result from the appropriate constructor

        Raises:
            ConstructorError: If no constructor is found for the tag
        """
        # Parse the tag to get structured information
        parsed_tag = self._tag_parser.parse_tag(tag_suffix, node)
        if not parsed_tag:
            raise ConstructorError(
                None,
                None,
                f"Failed to parse tag: {tag_suffix}",
                getattr(node, "start_mark", None),
            )

        # Look up the constructor
        constructor = self.get_constructor(parsed_tag.base_tag)
        if not constructor:
            raise ConstructorError(
                None,
                None,
                f"Unknown tag: {parsed_tag.base_tag}",
                getattr(node, "start_mark", None),
            )

        # Create appropriate node for the constructor
        constructor_node = self._create_constructor_node(parsed_tag, node)

        # Call the constructor
        return constructor(loader, constructor_node)

    def _create_constructor_node(
        self, parsed_tag: ParsedTag, original_node: yaml.Node
    ) -> yaml.Node:
        """
        Create the appropriate YAML node for the constructor based on the parsed tag.

        Args:
            parsed_tag: The parsed tag information
            original_node: The original YAML node

        Returns:
            A YAML node formatted for the constructor
        """
        start_mark = getattr(original_node, "start_mark", None)

        # If no parameters, return the original node
        if not parsed_tag.parameters:
            return original_node

        # For single parameter, create a scalar node
        if len(parsed_tag.parameters) == 1:
            return yaml.ScalarNode(
                tag=parsed_tag.base_tag,
                value=parsed_tag.parameters[0],
                start_mark=start_mark,
            )

        # For multiple parameters, create a sequence node
        param_nodes = [
            yaml.ScalarNode(
                tag="tag:yaml.org,2002:str", value=param, start_mark=start_mark
            )
            for param in parsed_tag.parameters
        ]

        return yaml.SequenceNode(
            tag=parsed_tag.base_tag, value=param_nodes, start_mark=start_mark
        )

    def get_registered_tags(self) -> list[str]:
        """Get a list of all registered tags."""
        return list(self._constructors.keys())

    def clear(self) -> None:
        """Clear all registered constructors."""
        self._constructors.clear()


# Global registry instance
_registry = ConstructorRegistry()


def get_registry() -> ConstructorRegistry:
    """Get the global constructor registry instance."""
    return _registry


def register_constructor(tag: str, constructor: Callable) -> None:
    """
    Convenience function to register a constructor with the global registry.

    Args:
        tag: The YAML tag (e.g., '!import', '!env')
        constructor: The constructor function to handle the tag
    """
    _registry.register(tag, constructor)


def register_default_constructors() -> None:
    """Register all default SmartYAML constructors with the global registry."""
    from .constructors import (
        base64_constructor,
        base64_decode_constructor,
        env_constructor,
        expand_constructor,
        extend_constructor,
        import_constructor,
        import_yaml_constructor,
        include_if_constructor,
        include_yaml_if_constructor,
        template_constructor,
    )

    constructors = {
        "!import": import_constructor,
        "!import_yaml": import_yaml_constructor,
        "!env": env_constructor,
        "!include_if": include_if_constructor,
        "!include_yaml_if": include_yaml_if_constructor,
        "!template": template_constructor,
        "!base64": base64_constructor,
        "!base64_decode": base64_decode_constructor,
        "!expand": expand_constructor,
        "!extend": extend_constructor,
    }

    _registry.register_multiple(constructors)
