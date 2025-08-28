"""
Deep Merge Utilities

Unified deep merge functionality used across the SmartYAML processing pipeline.
"""

import copy
from enum import Enum
from typing import Any, Dict, List, Optional

from ..exceptions import MergeConflictError


class MergeStrategy(Enum):
    """Strategy for handling different data types during merge operations."""

    REPLACE = "replace"  # Source completely replaces target
    MERGE_RECURSIVE = "merge_recursive"  # Recursively merge nested structures
    APPEND = "append"  # Append source to target (for lists)
    ERROR_ON_CONFLICT = "error_on_conflict"  # Raise error on type conflicts


class DeepMerger:
    """Unified deep merge implementation with configurable strategies."""

    def __init__(
        self,
        list_strategy: MergeStrategy = MergeStrategy.REPLACE,
        conflict_strategy: MergeStrategy = MergeStrategy.ERROR_ON_CONFLICT,
        preserve_types: bool = True,
        copy_strategy: str = "deep",
    ):
        """
        Initialize the deep merger.

        Args:
            list_strategy: How to handle list merging
            conflict_strategy: How to handle type conflicts
            preserve_types: Whether to preserve exact types during merge
            copy_strategy: "deep", "shallow", or "none" for copying values
        """
        self.list_strategy = list_strategy
        self.conflict_strategy = conflict_strategy
        self.preserve_types = preserve_types
        self.copy_strategy = copy_strategy

    def merge(
        self,
        target: Dict[str, Any],
        source: Dict[str, Any],
        context_path: Optional[str] = None,
    ) -> None:
        """
        Deep merge source dict into target dict.

        Args:
            target: Target dictionary to merge into (modified in-place)
            source: Source dictionary to merge from
            context_path: Current path for error reporting
        """
        for key, source_value in source.items():
            current_path = f"{context_path}.{key}" if context_path else key

            if key not in target:
                # Key doesn't exist in target, add it
                target[key] = self._copy_value(source_value)
            else:
                # Key exists, need to merge values
                target_value = target[key]
                merged_value = self._merge_values(
                    target_value, source_value, current_path
                )
                target[key] = merged_value

    def _merge_values(self, target_value: Any, source_value: Any, path: str) -> Any:
        """Merge two values based on their types and configured strategies."""
        target_type = type(target_value)
        source_type = type(source_value)

        # Handle identical types
        if target_type == source_type:
            if isinstance(target_value, dict) and isinstance(source_value, dict):
                # Recursively merge dictionaries
                result = (
                    self._copy_value(target_value)
                    if self.copy_strategy != "none"
                    else target_value
                )
                self.merge(result, source_value, path)
                return result
            elif isinstance(target_value, list) and isinstance(source_value, list):
                return self._merge_lists(target_value, source_value, path)
            else:
                # For scalar types, source replaces target
                return self._copy_value(source_value)

        # Handle type conflicts
        return self._handle_type_conflict(target_value, source_value, path)

    def _merge_lists(
        self, target_list: List[Any], source_list: List[Any], path: str
    ) -> List[Any]:
        """Merge two lists based on the configured list strategy."""
        if self.list_strategy == MergeStrategy.REPLACE:
            return self._copy_value(source_list)
        elif self.list_strategy == MergeStrategy.APPEND:
            result = self._copy_value(target_list)
            result.extend(self._copy_value(source_list))
            return result
        else:  # MERGE_RECURSIVE
            # For recursive merge, merge by index
            result = self._copy_value(target_list)
            for i, source_item in enumerate(source_list):
                if i < len(result):
                    result[i] = self._merge_values(
                        result[i], source_item, f"{path}[{i}]"
                    )
                else:
                    result.append(self._copy_value(source_item))
            return result

    def _handle_type_conflict(
        self, target_value: Any, source_value: Any, path: str
    ) -> Any:
        """Handle conflicts between different types."""
        if self.conflict_strategy == MergeStrategy.ERROR_ON_CONFLICT:
            # Only raise error for complex type mismatches
            target_is_complex = isinstance(target_value, (dict, list))
            source_is_complex = isinstance(source_value, (dict, list))

            if target_is_complex != source_is_complex:
                raise MergeConflictError(
                    path, type(target_value).__name__, type(source_value).__name__
                )

        # For other strategies or scalar conflicts, source replaces target
        return self._copy_value(source_value)

    def _copy_value(self, value: Any) -> Any:
        """Copy a value based on the configured copy strategy."""
        if self.copy_strategy == "deep":
            return copy.deepcopy(value)
        elif self.copy_strategy == "shallow":
            if isinstance(value, dict):
                return value.copy()
            elif isinstance(value, list):
                return value.copy()
            else:
                return value
        else:  # "none"
            return value


# Convenience functions for common merge scenarios
def merge_replace_lists(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Deep merge where lists in source replace lists in target."""
    merger = DeepMerger(list_strategy=MergeStrategy.REPLACE)
    merger.merge(target, source)


def merge_append_lists(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Deep merge where lists are appended together."""
    merger = DeepMerger(list_strategy=MergeStrategy.APPEND)
    merger.merge(target, source)


def merge_simple(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Simple deep merge that replaces conflicts without error checking."""
    merger = DeepMerger(
        list_strategy=MergeStrategy.REPLACE, conflict_strategy=MergeStrategy.REPLACE
    )
    merger.merge(target, source)
