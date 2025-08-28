"""
SmartYAML Exception Hierarchy

All custom exceptions for SmartYAML processing as defined in SPECS-v1.md.
"""

from typing import Any, List, Optional


class SmartYAMLError(Exception):
    """Base exception for all SmartYAML errors."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        field_path: Optional[str] = None,
        context: Optional[dict] = None,
    ):
        super().__init__(message)
        self.file_path = file_path
        self.field_path = field_path
        self.context = context or {}

    def __str__(self) -> str:
        msg = super().__str__()
        if self.file_path:
            msg = f"{msg} (in file: {self.file_path})"
        if self.field_path:
            msg = f"{msg} (at field: {self.field_path})"
        return msg


class VersionMismatchError(SmartYAMLError):
    """Raised when __version requires a higher library version."""

    def __init__(
        self,
        required_version: str,
        current_version: str,
        file_path: Optional[str] = None,
    ):
        message = (
            f"Config requires SmartYAML version {required_version}, "
            f"but library version is {current_version}"
        )
        super().__init__(message, file_path)
        self.required_version = required_version
        self.current_version = current_version


class FileNotFoundError(SmartYAMLError):
    """Raised when a file referenced in directives doesn't exist."""

    def __init__(
        self,
        file_path: str,
        base_path: Optional[str] = None,
        directive: Optional[str] = None,
    ):
        if base_path:
            message = f"File '{file_path}' not found relative to '{base_path}'"
        else:
            message = f"File '{file_path}' not found"

        if directive:
            message = f"{message} (in {directive} directive)"

        super().__init__(message)
        self.missing_file_path = file_path
        self.base_path = base_path
        self.directive = directive


class RecursionLimitExceededError(SmartYAMLError):
    """Raised when recursion depth exceeds limit."""

    def __init__(
        self,
        max_depth: int,
        operation: str = "processing",
        file_path: Optional[str] = None,
        field_path: Optional[str] = None,
    ):
        message = f"Recursion limit exceeded (max: {max_depth}) during {operation}"
        super().__init__(message, file_path, field_path)
        self.max_depth = max_depth
        self.operation = operation


class VariableNotFoundError(SmartYAMLError):
    """Raised when a variable reference cannot be resolved."""

    def __init__(
        self,
        variable_name: str,
        context_path: Optional[str] = None,
        file_path: Optional[str] = None,
    ):
        message = f"Undefined variable '{variable_name}'"
        if context_path:
            message = f"{message} in '{context_path}'"
        super().__init__(message, file_path)
        self.variable_name = variable_name


class DirectiveSyntaxError(SmartYAMLError):
    """Raised for invalid directive syntax."""

    def __init__(
        self,
        directive: str,
        expected_format: str,
        received: Any,
        file_path: Optional[str] = None,
        field_path: Optional[str] = None,
    ):
        message = f"Invalid syntax for {directive}: expected {expected_format}, got {type(received).__name__}"
        super().__init__(message, file_path, field_path)
        self.directive = directive
        self.expected_format = expected_format
        self.received = received


class DirectiveProcessingError(SmartYAMLError):
    """Raised when directive processing fails (e.g., type conversion errors)."""

    def __init__(
        self,
        directive: str,
        reason: str,
        value: Any = None,
        file_path: Optional[str] = None,
        field_path: Optional[str] = None,
    ):
        if value is not None:
            message = f"Failed to process !{directive}: cannot convert '{value}' to expected type - {reason}"
        else:
            message = f"Failed to process !{directive}: {reason}"
        super().__init__(message, file_path, field_path)
        self.directive = directive
        self.reason = reason
        self.value = value


class MergeConflictError(SmartYAMLError):
    """Raised when !merge encounters unresolvable conflicts."""

    def __init__(
        self, field_path: str, type1: str, type2: str, file_path: Optional[str] = None
    ):
        message = (
            f"Cannot merge incompatible types at '{field_path}': {type1} and {type2}"
        )
        super().__init__(message, file_path, field_path)
        self.type1 = type1
        self.type2 = type2


class ConditionalEvaluationError(SmartYAMLError):
    """Raised for errors in conditional directives."""

    def __init__(
        self,
        directive: str,
        condition: str,
        reason: str,
        file_path: Optional[str] = None,
        field_path: Optional[str] = None,
    ):
        message = f"Failed to evaluate condition for {directive}: {reason}"
        super().__init__(message, file_path, field_path)
        self.directive = directive
        self.condition = condition
        self.reason = reason


class SchemaValidationError(SmartYAMLError):
    """Raised when schema validation fails."""

    def __init__(self, errors: List[str], file_path: Optional[str] = None):
        if len(errors) == 1:
            message = f"Schema validation failed: {errors[0]}"
        else:
            message = (
                f"Schema validation failed with {len(errors)} errors:\n"
                + "\n".join(f"  - {err}" for err in errors)
            )

        super().__init__(message, file_path)
        self.validation_errors = errors


class SecurityViolationError(SmartYAMLError):
    """Raised for security violations."""

    def __init__(
        self, violation_type: str, details: str, file_path: Optional[str] = None
    ):
        message = f"Security violation ({violation_type}): {details}"
        super().__init__(message, file_path)
        self.violation_type = violation_type


class FileSizeExceededError(SmartYAMLError):
    """Raised when a file exceeds maximum size limit."""

    def __init__(self, file_path: str, file_size: int, max_size: int):
        message = (
            f"File '{file_path}' exceeds max size ({file_size} > {max_size} bytes)"
        )
        super().__init__(message, file_path)
        self.file_size = file_size
        self.max_size = max_size


class VariableExpansionError(SmartYAMLError):
    """Raised when variable expansion fails."""

    def __init__(
        self, variable_name: str, reason: str, file_path: Optional[str] = None
    ):
        self.variable_name = variable_name
        self.reason = reason

        message = f"Variable expansion failed for '{{{{ {variable_name} }}}}': {reason}"
        super().__init__(message, file_path, f"{{{{ {variable_name} }}}}")
