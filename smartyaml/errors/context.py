"""
Error Context Management

Provides standardized error context building for consistent error reporting.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..exceptions import (
    ConditionalEvaluationError,
    DirectiveProcessingError,
    DirectiveSyntaxError,
    FileNotFoundError,
    MergeConflictError,
    RecursionLimitExceededError,
    SecurityViolationError,
    SmartYAMLError,
    VariableExpansionError,
    VariableNotFoundError,
)


@dataclass
class ErrorContext:
    """
    Standardized error context information.

    Provides consistent structure for error reporting across SmartYAML.
    """

    file_path: Optional[Union[str, Path]] = None
    field_path: Optional[str] = None
    operation: Optional[str] = None
    directive: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary."""
        return {
            "file_path": str(self.file_path) if self.file_path else None,
            "field_path": self.field_path,
            "operation": self.operation,
            "directive": self.directive,
            "additional_context": self.additional_context,
        }

    def get_location_info(self) -> str:
        """Get formatted location information."""
        parts = []
        if self.file_path:
            parts.append(f"file: {self.file_path}")
        if self.field_path:
            parts.append(f"field: {self.field_path}")
        if self.directive:
            parts.append(f"directive: {self.directive}")
        if self.operation:
            parts.append(f"operation: {self.operation}")

        return " | ".join(parts) if parts else "unknown location"


class ErrorContextBuilder:
    """
    Builder for creating standardized error contexts and raising exceptions.

    Provides a fluent interface for building error contexts with consistent
    information and raising appropriately typed exceptions.
    """

    def __init__(self):
        self.reset()

    def reset(self) -> "ErrorContextBuilder":
        """Reset the builder to initial state."""
        self._context = ErrorContext()
        return self

    def in_file(self, file_path: Union[str, Path]) -> "ErrorContextBuilder":
        """Set the file path where the error occurred."""
        self._context.file_path = file_path
        return self

    def at_field(self, field_path: str) -> "ErrorContextBuilder":
        """Set the field path where the error occurred."""
        self._context.field_path = field_path
        return self

    def during_operation(self, operation: str) -> "ErrorContextBuilder":
        """Set the operation that was being performed."""
        self._context.operation = operation
        return self

    def in_directive(self, directive: str) -> "ErrorContextBuilder":
        """Set the directive being processed."""
        self._context.directive = directive
        return self

    def with_context(self, key: str, value: Any) -> "ErrorContextBuilder":
        """Add additional context information."""
        self._context.additional_context[key] = value
        return self

    def with_multiple_context(self, context: Dict[str, Any]) -> "ErrorContextBuilder":
        """Add multiple context items at once."""
        self._context.additional_context.update(context)
        return self

    def get_context(self) -> ErrorContext:
        """Get the current error context."""
        return self._context

    # Exception raising methods with standardized context

    def raise_directive_syntax_error(
        self,
        directive: str,
        expected: str,
        received: Any,
        message: Optional[str] = None,
    ) -> None:
        """Raise a DirectiveSyntaxError with standardized context."""
        if not message:
            message = f"Invalid syntax for !{directive}: expected {expected}, got {type(received).__name__}"

        raise DirectiveSyntaxError(
            directive=f"!{directive}",
            expected_format=expected,
            received=received,
            file_path=str(self._context.file_path) if self._context.file_path else None,
            field_path=self._context.field_path,
        )

    def raise_directive_processing_error(
        self, directive: str, reason: str, value: Any = None
    ) -> None:
        """Raise a DirectiveProcessingError with standardized context."""
        raise DirectiveProcessingError(
            directive=directive,
            reason=reason,
            value=value,
            file_path=str(self._context.file_path) if self._context.file_path else None,
            field_path=self._context.field_path,
        )

    def raise_file_not_found_error(
        self,
        file_path: Union[str, Path],
        base_path: Optional[Union[str, Path]] = None,
        directive: Optional[str] = None,
    ) -> None:
        """Raise a FileNotFoundError with standardized context."""
        raise FileNotFoundError(
            file_path=str(file_path),
            base_path=str(base_path) if base_path else None,
            directive=directive or self._context.directive,
        )

    def raise_security_violation_error(self, violation_type: str, details: str) -> None:
        """Raise a SecurityViolationError with standardized context."""
        raise SecurityViolationError(
            violation_type=violation_type,
            details=details,
            file_path=str(self._context.file_path) if self._context.file_path else None,
        )

    def raise_variable_not_found_error(
        self, variable_name: str, context_info: Optional[str] = None
    ) -> None:
        """Raise a VariableNotFoundError with standardized context."""
        raise VariableNotFoundError(
            variable_name=variable_name,
            context_path=context_info or self._context.field_path,
            file_path=str(self._context.file_path) if self._context.file_path else None,
        )

    def raise_variable_expansion_error(self, variable_name: str, reason: str) -> None:
        """Raise a VariableExpansionError with standardized context."""
        raise VariableExpansionError(
            variable_name=variable_name,
            reason=reason,
            file_path=str(self._context.file_path) if self._context.file_path else None,
        )

    def raise_recursion_limit_exceeded_error(
        self, max_depth: int, operation: Optional[str] = None
    ) -> None:
        """Raise a RecursionLimitExceededError with standardized context."""
        operation = operation or self._context.operation or "processing"

        raise RecursionLimitExceededError(
            max_depth=max_depth,
            operation=operation,
            file_path=str(self._context.file_path) if self._context.file_path else None,
            field_path=self._context.field_path,
        )

    def raise_merge_conflict_error(
        self, field_path: str, type1: str, type2: str
    ) -> None:
        """Raise a MergeConflictError with standardized context."""
        raise MergeConflictError(
            field_path=field_path,
            type1=type1,
            type2=type2,
            file_path=str(self._context.file_path) if self._context.file_path else None,
        )

    def raise_conditional_evaluation_error(
        self, directive: str, condition: str, reason: str
    ) -> None:
        """Raise a ConditionalEvaluationError with standardized context."""
        raise ConditionalEvaluationError(
            directive=directive,
            condition=condition,
            reason=reason,
            file_path=str(self._context.file_path) if self._context.file_path else None,
            field_path=self._context.field_path,
        )

    def raise_generic_error(self, message: str) -> None:
        """Raise a generic SmartYAMLError with standardized context."""
        # Enhance message with context information
        location = self._context.get_location_info()
        if location != "unknown location":
            message = f"{message} ({location})"

        raise SmartYAMLError(
            message=message,
            file_path=str(self._context.file_path) if self._context.file_path else None,
            field_path=self._context.field_path,
            context=self._context.additional_context,
        )

    def raise_custom_error(self, exception_class: type, *args, **kwargs) -> None:
        """Raise a custom exception with context information injected."""
        # Try to inject common context parameters if the exception supports them
        if hasattr(exception_class, "__init__"):
            import inspect

            sig = inspect.signature(exception_class.__init__)

            # Inject file_path if supported
            if "file_path" in sig.parameters and "file_path" not in kwargs:
                if self._context.file_path:
                    kwargs["file_path"] = str(self._context.file_path)

            # Inject field_path if supported
            if "field_path" in sig.parameters and "field_path" not in kwargs:
                if self._context.field_path:
                    kwargs["field_path"] = self._context.field_path

            # Inject context if supported
            if "context" in sig.parameters and "context" not in kwargs:
                if self._context.additional_context:
                    kwargs["context"] = self._context.additional_context

        raise exception_class(*args, **kwargs)
