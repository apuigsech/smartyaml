"""
Error Helper Functions

Convenience functions and utilities for consistent error handling.
"""

from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union

from .context import ErrorContext, ErrorContextBuilder

T = TypeVar("T")


def create_error_context(
    file_path: Optional[Union[str, Path]] = None,
    field_path: Optional[str] = None,
    operation: Optional[str] = None,
    directive: Optional[str] = None,
    **additional_context,
) -> ErrorContext:
    """Create an error context with the given parameters."""
    return ErrorContext(
        file_path=file_path,
        field_path=field_path,
        operation=operation,
        directive=directive,
        additional_context=additional_context,
    )


class ErrorHelper:
    """
    Collection of helper functions for common error scenarios.

    Provides pre-configured error builders for common SmartYAML operations.
    """

    @staticmethod
    def directive_error_builder(
        directive: str, context, field_path: Optional[str] = None
    ) -> ErrorContextBuilder:
        """Create an error builder for directive processing errors."""
        builder = ErrorContextBuilder()
        if hasattr(context, "file_path") and context.file_path:
            builder.in_file(context.file_path)
        if field_path or (hasattr(context, "field_path") and context.field_path):
            builder.at_field(field_path or context.field_path)

        return builder.in_directive(directive).during_operation(
            f"processing !{directive}"
        )

    @staticmethod
    def file_operation_error_builder(
        operation: str, file_path: Union[str, Path], context=None
    ) -> ErrorContextBuilder:
        """Create an error builder for file operation errors."""
        builder = ErrorContextBuilder().during_operation(operation)

        if context and hasattr(context, "file_path") and context.file_path:
            builder.in_file(context.file_path)

        return builder.with_context("target_file", str(file_path))

    @staticmethod
    def variable_error_builder(
        variable_name: str, context, field_path: Optional[str] = None
    ) -> ErrorContextBuilder:
        """Create an error builder for variable-related errors."""
        builder = ErrorContextBuilder()
        if hasattr(context, "file_path") and context.file_path:
            builder.in_file(context.file_path)
        if field_path:
            builder.at_field(field_path)

        return builder.during_operation("variable expansion").with_context(
            "variable_name", variable_name
        )

    @staticmethod
    def validation_error_builder(
        field_name: str, context, operation: str = "validation"
    ) -> ErrorContextBuilder:
        """Create an error builder for validation errors."""
        builder = ErrorContextBuilder()
        if hasattr(context, "file_path") and context.file_path:
            builder.in_file(context.file_path)

        return builder.at_field(field_name).during_operation(operation)

    @staticmethod
    def security_error_builder(
        violation_type: str, context, operation: str = "security check"
    ) -> ErrorContextBuilder:
        """Create an error builder for security-related errors."""
        builder = ErrorContextBuilder()
        if hasattr(context, "file_path") and context.file_path:
            builder.in_file(context.file_path)

        return builder.during_operation(operation).with_context(
            "violation_type", violation_type
        )


def with_error_context(context_builder_func: Callable[[], ErrorContextBuilder]):
    """
    Decorator that provides error context for functions.

    Usage:
        @with_error_context(lambda: ErrorHelper.directive_error_builder("env", context))
        def process_env_directive(value, context):
            # Function implementation
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # If it's already a SmartYAML exception, re-raise as is
                if hasattr(e, "__class__") and issubclass(e.__class__, Exception):
                    # Check if it's one of our exceptions
                    from ..exceptions import SmartYAMLError

                    if isinstance(e, SmartYAMLError):
                        raise

                # For other exceptions, wrap with context
                builder = context_builder_func()
                builder.raise_generic_error(f"Unexpected error: {str(e)}")

        return wrapper

    return decorator


def require_type(
    value: Any,
    expected_type: Union[type, tuple],
    field_name: str,
    context_builder: ErrorContextBuilder,
) -> None:
    """
    Validate that a value is of the expected type, raising a standardized error if not.

    Args:
        value: Value to check
        expected_type: Expected type or tuple of types
        field_name: Name of the field for error messages
        context_builder: Error context builder to use for raising errors
    """
    if not isinstance(value, expected_type):
        if isinstance(expected_type, tuple):
            type_names = " or ".join(t.__name__ for t in expected_type)
        else:
            type_names = expected_type.__name__

        # Check if this is a directive validation - raise DirectiveSyntaxError
        if (
            hasattr(context_builder._context, "directive")
            and context_builder._context.directive
        ):
            context_builder.raise_directive_syntax_error(
                context_builder._context.directive, type_names, value
            )
        else:
            context_builder.raise_generic_error(
                f"{field_name} must be {type_names}, got {type(value).__name__}"
            )


def require_list_length(
    value: list,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    exact_length: Optional[int] = None,
    field_name: str = "list",
    context_builder: Optional[ErrorContextBuilder] = None,
) -> None:
    """
    Validate list length requirements, raising a standardized error if not met.

    Args:
        value: List to check
        min_length: Minimum required length
        max_length: Maximum allowed length
        exact_length: Exact required length
        field_name: Name of the field for error messages
        context_builder: Error context builder to use for raising errors
    """
    if context_builder is None:
        context_builder = ErrorContextBuilder()

    length = len(value)

    if exact_length is not None:
        if length != exact_length:
            # Check if this is a directive validation - raise DirectiveSyntaxError
            if (
                hasattr(context_builder._context, "directive")
                and context_builder._context.directive
            ):
                context_builder.raise_directive_syntax_error(
                    context_builder._context.directive,
                    f"array with exactly {exact_length} elements",
                    f"array with {length} elements",
                )
            else:
                context_builder.raise_generic_error(
                    f"{field_name} must have exactly {exact_length} elements, got {length}"
                )
    else:
        if min_length is not None and length < min_length:
            # Check if this is a directive validation - raise DirectiveSyntaxError
            if (
                hasattr(context_builder._context, "directive")
                and context_builder._context.directive
            ):
                context_builder.raise_directive_syntax_error(
                    context_builder._context.directive,
                    f"array with at least {min_length} elements",
                    f"array with {length} elements",
                )
            else:
                context_builder.raise_generic_error(
                    f"{field_name} must have at least {min_length} elements, got {length}"
                )

        if max_length is not None and length > max_length:
            # Check if this is a directive validation - raise DirectiveSyntaxError
            if (
                hasattr(context_builder._context, "directive")
                and context_builder._context.directive
            ):
                context_builder.raise_directive_syntax_error(
                    context_builder._context.directive,
                    f"array with at most {max_length} elements",
                    f"array with {length} elements",
                )
            else:
                context_builder.raise_generic_error(
                    f"{field_name} must have at most {max_length} elements, got {length}"
                )


def require_file_exists(
    file_path: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
    context_builder: Optional[ErrorContextBuilder] = None,
) -> Path:
    """
    Validate that a file exists, raising a standardized error if not.

    Args:
        file_path: Path to the file
        base_path: Base path for relative resolution
        context_builder: Error context builder to use for raising errors

    Returns:
        Resolved Path object
    """
    if context_builder is None:
        context_builder = ErrorContextBuilder()

    path = Path(file_path)
    if not path.exists():
        context_builder.raise_file_not_found_error(file_path, base_path)

    return path


# Context manager for automatic error context
class error_context:
    """
    Context manager that automatically provides error context for operations.

    Usage:
        with error_context().in_file("config.yaml").during_operation("loading"):
            # Operations here will have standardized error context
            process_config()
    """

    def __init__(self):
        self._builder = ErrorContextBuilder()

    def in_file(self, file_path: Union[str, Path]) -> "error_context":
        self._builder.in_file(file_path)
        return self

    def at_field(self, field_path: str) -> "error_context":
        self._builder.at_field(field_path)
        return self

    def during_operation(self, operation: str) -> "error_context":
        self._builder.during_operation(operation)
        return self

    def in_directive(self, directive: str) -> "error_context":
        self._builder.in_directive(directive)
        return self

    def with_context(self, **context) -> "error_context":
        self._builder.with_multiple_context(context)
        return self

    def __enter__(self) -> ErrorContextBuilder:
        return self._builder

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If an exception occurred and it's not already a SmartYAML exception,
        # we could wrap it here, but that might interfere with normal flow
        # For now, just let exceptions propagate normally
        pass
