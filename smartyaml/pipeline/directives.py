"""
Stage 4: Directive Processing

Processes all SmartYAML directives with the new registry-based architecture
in depth-first, recursive manner. Uses modular handlers for clean separation
of concerns and extensibility.
"""

from typing import Any, Dict

from ..config import SmartYAMLConfig
from ..directives import DirectiveContext, get_handler
from ..errors import ErrorHelper
from ..exceptions import SmartYAMLError


class DirectiveProcessor:
    """Stage 4: Process all SmartYAML directives using registry-based architecture."""

    def __init__(self, config: SmartYAMLConfig):
        self.config = config

    def process(self, data: Any, context) -> Any:
        """Process all directives in the data structure recursively."""
        return self._process_recursive(data, context)

    def process_value(self, value: Any, context) -> Any:
        """Process a single value (used by metadata processor)."""
        return self._process_recursive(value, context)

    def _process_recursive(self, data: Any, context) -> Any:
        """Recursively process directives depth-first."""
        if isinstance(data, dict):
            if "__directive__" in data:
                # This is a directive, process it
                return self._process_directive(data, context)
            else:
                # Regular dict, process each value
                result = {}
                for key, value in data.items():
                    result[key] = self._process_recursive(value, context)
                return result

        elif isinstance(data, list):
            # Process each item in the list
            return [self._process_recursive(item, context) for item in data]

        else:
            # Scalar value, return as-is
            return data

    def _process_directive(self, directive_data: Dict[str, Any], context) -> Any:
        """Process a single directive using the registry system."""
        directive_name = directive_data["__directive__"]
        directive_value = directive_data["__value__"]

        # Get handler from registry
        handler = get_handler(directive_name, self.config)
        if handler is None:
            error_builder = ErrorHelper.directive_error_builder(directive_name, context)
            error_builder.raise_directive_syntax_error(
                directive_name,
                "known directive",
                f"unknown directive '{directive_name}'",
            )

        try:
            # Create directive context
            directive_context = DirectiveContext(
                config=self.config,
                file_path=getattr(context, "file_path", None),
                base_path=getattr(context, "base_path", None),
                variables=getattr(context, "variables", {}),
                recursion_depth=getattr(context, "recursion_depth", 0),
                loaded_files=getattr(context, "loaded_files", set()),
            )

            # Inject recursive processing and variable expansion methods
            handler.process_recursive = self._process_recursive
            handler.expand_variables = self._expand_variables_in_arguments

            # Special handling for directives that need raw values
            if directive_name in ["if", "switch", "expand"]:
                # Skip recursive processing and variable expansion for these directives
                # - Conditionals need raw values for proper evaluation
                # - !expand needs raw template strings for deferred expansion
                result = handler.handle(directive_value, directive_context)
            else:
                # Process directive arguments recursively first
                processed_value = self._process_recursive(directive_value, context)

                # Expand variables in directive arguments
                processed_value = self._expand_variables_in_arguments(
                    processed_value, context
                )

                # Execute directive handler
                result = handler.handle(processed_value, directive_context)

            return result

        except SmartYAMLError:
            raise
        except Exception as e:
            error_builder = ErrorHelper.directive_error_builder(directive_name, context)
            error_builder.raise_generic_error(
                f"Error processing !{directive_name} directive: {e}"
            )

    def _expand_variables_in_arguments(self, args, context) -> Any:
        """Expand variables in directive arguments."""
        # Import the variable processor to expand variables
        from .variables import VariableProcessor

        variable_processor = VariableProcessor(self.config)

        # Only expand if variables are available
        if hasattr(context, "variables") and context.variables:
            return variable_processor._expand_recursive(
                args, context.variables, context
            )
        else:
            return args
