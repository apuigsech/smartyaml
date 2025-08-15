"""
SmartYAML Loader with custom constructors
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

import yaml

if TYPE_CHECKING:
    pass

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

        # Global variable context for accumulating __vars during loading
        self.accumulated_vars: Dict[str, Any] = {}

    def accumulate_vars(self, new_vars: Dict[str, Any]) -> None:
        """
        Accumulate variables into the global context.
        Child variables override parent variables.

        Args:
            new_vars: Dictionary of variables to accumulate
        """
        if new_vars and isinstance(new_vars, dict):
            self.accumulated_vars.update(new_vars)

    def get_accumulated_vars(self) -> Dict[str, Any]:
        """
        Get all accumulated variables.

        Returns:
            Dictionary of all accumulated variables
        """
        return self.accumulated_vars.copy()

    def construct_mapping(self, node, deep=False):
        """
        Override mapping construction to handle SmartYAML directives in merge keys.

        This fixes the issue where PyYAML's merge operator (<<:) rejects SmartYAML
        directive nodes before calling their constructors.
        """
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        return super().construct_mapping(node, deep)

    def flatten_mapping(self, node):
        """
        Custom flatten_mapping that handles SmartYAML directives in merge keys.
        This is based on PyYAML's SafeLoader.flatten_mapping but extended for SmartYAML.
        """
        merge = []
        index = 0
        while index < len(node.value):
            key_node, value_node = node.value[index]
            if key_node.tag == "tag:yaml.org,2002:merge":
                del node.value[index]
                if value_node.tag == "tag:yaml.org,2002:merge":
                    # Handle nested merge
                    self.flatten_mapping(value_node)
                    merge.extend(value_node.value)
                elif value_node.tag in (
                    "tag:yaml.org,2002:map",
                    "tag:yaml.org,2002:omap",
                ):
                    # Regular mapping node
                    self.flatten_mapping(value_node)
                    merge.append(value_node)
                elif value_node.tag == "tag:yaml.org,2002:seq":
                    # Sequence of mappings
                    submerge = []
                    for subnode in value_node.value:
                        if subnode.tag not in (
                            "tag:yaml.org,2002:map",
                            "tag:yaml.org,2002:omap",
                        ):
                            raise yaml.constructor.ConstructorError(
                                None,
                                None,
                                "expected a mapping for merging, but found %s"
                                % subnode.tag,
                                subnode.start_mark,
                            )
                        self.flatten_mapping(subnode)
                        submerge.append(subnode)
                    merge.extend(submerge)
                else:
                    # Check if this is a SmartYAML directive node
                    if (
                        hasattr(value_node, "tag")
                        and value_node.tag
                        and value_node.tag.startswith("!")
                    ):
                        try:
                            # Construct the directive to get its value
                            if value_node.tag in self.yaml_constructors:
                                constructor = self.yaml_constructors[value_node.tag]
                                merge_value = constructor(self, value_node)
                            else:
                                # Try multi-constructor dispatch
                                tag_suffix = value_node.tag[1:]  # Remove leading !
                                merge_value = smart_constructor_dispatch(
                                    self, tag_suffix, value_node
                                )

                            # If the directive returns a mapping, create a mapping node for it
                            if isinstance(merge_value, dict):
                                # Convert the dict back to a mapping node for merging
                                pairs = []
                                for k, v in merge_value.items():
                                    key_node = yaml.ScalarNode(
                                        "tag:yaml.org,2002:str", str(k)
                                    )
                                    val_node = self.create_value_node(
                                        v, value_node.start_mark
                                    )
                                    pairs.append((key_node, val_node))
                                mapping_node = yaml.MappingNode(
                                    "tag:yaml.org,2002:map", pairs
                                )
                                merge.append(mapping_node)
                            else:
                                # Not a mapping, this will cause an error
                                raise yaml.constructor.ConstructorError(
                                    None,
                                    None,
                                    "expected a mapping for merging, "
                                    "but SmartYAML directive returned %s"
                                    % type(merge_value).__name__,
                                    value_node.start_mark,
                                )
                        except Exception as e:
                            # Re-raise as ConstructorError for consistency
                            raise yaml.constructor.ConstructorError(
                                None,
                                None,
                                "failed to construct SmartYAML directive for merging: %s"
                                % str(e),
                                value_node.start_mark,
                            )
                    else:
                        # Not a SmartYAML directive, use original error
                        raise yaml.constructor.ConstructorError(
                            None,
                            None,
                            "expected a mapping for merging, but found %s"
                            % value_node.tag,
                            value_node.start_mark,
                        )
            else:
                index += 1

        # Apply the merge at the beginning of the mapping
        if merge:
            # Merge needs to be flattened - each item in merge is a MappingNode with pairs
            merged_pairs = []
            for merge_node in merge:
                if isinstance(merge_node, yaml.MappingNode):
                    merged_pairs.extend(merge_node.value)
            node.value = merged_pairs + node.value

    def create_value_node(self, value, mark):
        """Create a YAML node from a Python value."""
        if isinstance(value, dict):
            pairs = []
            for k, v in value.items():
                # Handle None keys properly (though this is unusual)
                if k is None:
                    key_node = yaml.ScalarNode("tag:yaml.org,2002:null", "", mark)
                else:
                    key_node = yaml.ScalarNode("tag:yaml.org,2002:str", str(k), mark)
                val_node = self.create_value_node(v, mark)
                pairs.append((key_node, val_node))
            return yaml.MappingNode("tag:yaml.org,2002:map", pairs, mark)
        elif isinstance(value, list):
            items = [self.create_value_node(item, mark) for item in value]
            return yaml.SequenceNode("tag:yaml.org,2002:seq", items, mark)
        elif value is None:
            return yaml.ScalarNode("tag:yaml.org,2002:null", "", mark)
        elif isinstance(value, bool):
            return yaml.ScalarNode("tag:yaml.org,2002:bool", str(value).lower(), mark)
        elif isinstance(value, int):
            return yaml.ScalarNode("tag:yaml.org,2002:int", str(value), mark)
        elif isinstance(value, float):
            return yaml.ScalarNode("tag:yaml.org,2002:float", str(value), mark)
        else:
            return yaml.ScalarNode("tag:yaml.org,2002:str", str(value), mark)


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
