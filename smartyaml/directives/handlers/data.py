"""
Data manipulation directive handlers.

Implements !merge, !concat, and !expand directives for data manipulation,
merging, and string expansion operations.
"""

from typing import Any, List

from ...errors import require_type
from ...exceptions import MergeConflictError
from ...utils.merge import DeepMerger, MergeStrategy
from ..base import DataDirectiveHandler, DirectiveContext


class MergeHandler(DataDirectiveHandler):
    """Handler for !merge directive - merge multiple data structures."""

    @property
    def directive_name(self) -> str:
        return "merge"

    def handle(self, value: Any, context: DirectiveContext) -> Any:
        """
        Handle !merge directive: merge multiple structures.

        Args:
            value: List of dictionaries to merge
            context: Processing context

        Returns:
            Merged dictionary result
        """
        error_builder = self.get_error_builder(context)

        # Validate that we have a list
        items = self.validate_list_argument(value, context)

        if not items:
            return {}

        # Ensure all items are dictionaries
        self.ensure_compatible_types(items, dict, context)

        result = {}
        merger = DeepMerger(
            list_strategy=MergeStrategy.REPLACE,
            conflict_strategy=MergeStrategy.ERROR_ON_CONFLICT,
        )

        for i, item in enumerate(items):
            try:
                merger.merge(result, item, f"merge[{i}]")
            except MergeConflictError as e:
                # Re-raise with enhanced context
                error_builder.at_field(
                    f"merge[{i}].{e.field_path}"
                ).raise_merge_conflict_error(e.field_path, e.type1, e.type2)

        return result


class ConcatHandler(DataDirectiveHandler):
    """Handler for !concat directive - concatenate lists."""

    @property
    def directive_name(self) -> str:
        return "concat"

    def handle(self, value: Any, context: DirectiveContext) -> List[Any]:
        """
        Handle !concat directive: concatenate lists.

        Args:
            value: List of items to concatenate
            context: Processing context

        Returns:
            Concatenated list result
        """
        # Validate that we have a list
        items = self.validate_list_argument(value, context)

        result = []

        for item in items:
            if isinstance(item, list):
                result.extend(item)
            else:
                result.append(item)

        return result


class ExpandHandler(DataDirectiveHandler):
    """Handler for !expand directive - expand strings with variables."""

    @property
    def directive_name(self) -> str:
        return "expand"

    def handle(self, value: Any, context: DirectiveContext) -> Any:
        """
        Handle !expand directive: expand string with variables.

        Args:
            value: String to expand
            context: Processing context

        Returns:
            Special marker for deferred expansion during variable stage
        """
        error_builder = self.get_error_builder(context)

        require_type(value, str, "!expand directive", error_builder)

        # Instead of expanding immediately, return a special marker
        # that will be processed during the variable expansion stage
        # when all data is available
        return {"__expand_deferred__": value}


class VarHandler(DataDirectiveHandler):
    """
    Handler for !var directive.

    Resolve variables with original type preservation.
    """

    @property
    def directive_name(self) -> str:
        return "var"

    def handle(self, value: Any, context: DirectiveContext) -> Any:
        """
        Handle !var directive: resolve variable preserving original type.

        Args:
            value: Variable name to resolve
            context: Processing context

        Returns:
            Variable value in its original type
        """
        error_builder = self.get_error_builder(context)

        require_type(value, str, "!var directive", error_builder)

        # Resolve variable using context variables with proper precedence
        # Import here to avoid circular imports
        from ...pipeline.variables import VariableProcessor

        # Create a temporary variable processor to use its resolution logic
        variable_processor = VariableProcessor(self.config)

        try:
            # Use the same resolution logic as variable expansion
            resolved_value = variable_processor._resolve_variable_with_default(
                value, context.variables, context
            )
            return resolved_value
        except Exception as e:
            # Convert any resolution errors to directive syntax errors
            error_builder.raise_directive_syntax_error(
                f"!var directive failed to resolve variable '{value}': {e}"
            )
