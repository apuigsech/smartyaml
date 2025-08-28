"""
Conditional directive handlers.

Implements !if and !switch directives for conditional data inclusion
based on environment variables and expressions.
"""

import os
from typing import Any, Dict, List

from ...errors import require_list_length, require_type
from ..base import ConditionalDirectiveHandler, DirectiveContext


class IfHandler(ConditionalDirectiveHandler):
    """Handler for !if directive - conditional inclusion."""

    @property
    def directive_name(self) -> str:
        return "if"

    def handle(self, value: Any, context: DirectiveContext) -> Any:
        """
        Handle !if directive: conditional inclusion.

        Supports both array and object syntax:
        - Array: !if ['ENV_VAR', then_value, else_value?]
        - Object: !if {var: 'ENV_VAR', then: value, else: value?}

        Args:
            value: Directive arguments (list or dict)
            context: Processing context

        Returns:
            Result based on condition evaluation
        """
        error_builder = self.get_error_builder(context)

        # Parse arguments using base class helper
        try:
            parsed_args = self.parse_array_or_object_syntax(value)
        except ValueError as e:
            error_builder.raise_directive_syntax_error(
                "if", "array or object", value, str(e)
            )

        condition_var = parsed_args["var"]
        then_value = parsed_args["then"]
        else_value = parsed_args.get("else")

        # Evaluate condition
        if self.evaluate_condition(condition_var, context):
            # Process and return the 'then' value
            processed_then = self.process_recursive(then_value, context)
            return self.expand_variables(processed_then, context)
        else:
            # Process and return the 'else' value if provided
            if else_value is not None:
                processed_else = self.process_recursive(else_value, context)
                return self.expand_variables(processed_else, context)
            else:
                return None

    def _parse_array_syntax(self, value: List[Any]) -> Dict[str, Any]:
        """Parse array-style arguments: !if ['ENV_VAR', then_value, else_value?]"""
        error_builder = self.get_error_builder(None)  # Will be set by caller

        require_list_length(
            value,
            min_length=2,
            max_length=3,
            field_name="!if directive",
            context_builder=error_builder,
        )

        condition_var = value[0]
        then_value = value[1]
        else_value = value[2] if len(value) > 2 else None

        require_type(condition_var, str, "!if condition variable", error_builder)

        return {
            "var": condition_var,
            "then": then_value,
            "else": else_value,
        }

    def _parse_object_syntax(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Parse object-style arguments: !if {var: 'ENV_VAR', then: value, else: value?}"""
        error_builder = self.get_error_builder(None)  # Will be set by caller

        if "var" not in value:
            error_builder.raise_directive_syntax_error(
                "if",
                "object with 'var' field",
                value,
                "Missing required 'var' field in !if directive",
            )

        if "then" not in value:
            error_builder.raise_directive_syntax_error(
                "if",
                "object with 'then' field",
                value,
                "Missing required 'then' field in !if directive",
            )

        condition_var = value["var"]
        then_value = value["then"]
        else_value = value.get("else")

        require_type(condition_var, str, "!if var field", error_builder)

        return {
            "var": condition_var,
            "then": then_value,
            "else": else_value,
        }


class SwitchHandler(ConditionalDirectiveHandler):
    """Handler for !switch directive - multi-way conditional."""

    @property
    def directive_name(self) -> str:
        return "switch"

    def handle(self, value: Any, context: DirectiveContext) -> Any:
        """
        Handle !switch directive: multi-way conditional.

        Supports both array and object syntax:
        - Array: !switch ['ENV_VAR', [cases]]
        - Object: !switch {var: 'ENV_VAR', cases: [...]}

        Args:
            value: Directive arguments (list or dict)
            context: Processing context

        Returns:
            Result from matching case or None
        """
        error_builder = self.get_error_builder(context)

        # Parse arguments using base class helper
        try:
            parsed_args = self.parse_array_or_object_syntax(value)
        except ValueError as e:
            error_builder.raise_directive_syntax_error(
                "switch", "array or object", value, str(e)
            )

        condition_var = parsed_args["var"]
        cases = parsed_args["cases"]

        # Get condition value from environment
        condition_value = os.environ.get(condition_var, "")

        # Find matching case
        for case in cases:
            if not isinstance(case, dict):
                continue

            if "case" in case and case["case"] == condition_value:
                # Remove 'case' key and return the rest
                result = {k: v for k, v in case.items() if k != "case"}
                final_result = result if len(result) != 1 else list(result.values())[0]
                # Process the selected case recursively to handle nested directives
                return self.process_recursive(final_result, context)

            elif "default" in case:
                # Default case - remove 'default' key and return the rest
                result = {k: v for k, v in case.items() if k != "default"}
                final_result = result if len(result) != 1 else list(result.values())[0]
                # Process the selected case recursively to handle nested directives
                return self.process_recursive(final_result, context)

        return None

    def _parse_array_syntax(self, value: List[Any]) -> Dict[str, Any]:
        """Parse array-style arguments: !switch ['ENV_VAR', [cases]]"""
        error_builder = self.get_error_builder(None)  # Will be set by caller

        require_list_length(
            value,
            min_length=2,
            field_name="!switch directive",
            context_builder=error_builder,
        )

        condition_var = value[0]
        cases = value[1] if len(value) > 1 else []

        require_type(condition_var, str, "!switch condition variable", error_builder)
        require_type(cases, list, "!switch cases", error_builder)

        return {
            "var": condition_var,
            "cases": cases,
        }

    def _parse_object_syntax(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Parse object-style arguments: !switch {var: 'ENV_VAR', cases: [...]}"""
        error_builder = self.get_error_builder(None)  # Will be set by caller

        if "var" not in value:
            error_builder.raise_directive_syntax_error(
                "switch",
                "object with 'var' field",
                value,
                "Missing required 'var' field in !switch directive",
            )

        if "cases" not in value:
            error_builder.raise_directive_syntax_error(
                "switch",
                "object with 'cases' field",
                value,
                "Missing required 'cases' field in !switch directive",
            )

        condition_var = value["var"]
        cases = value["cases"]

        require_type(condition_var, str, "!switch var field", error_builder)
        require_type(cases, list, "!switch cases field", error_builder)

        return {
            "var": condition_var,
            "cases": cases,
        }
