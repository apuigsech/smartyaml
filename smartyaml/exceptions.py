"""
SmartYAML exceptions
"""

from typing import Optional

import yaml


class SmartYAMLError(Exception):
    """Base exception for SmartYAML errors."""


class SmartYAMLFileNotFoundError(SmartYAMLError):
    """Raised when a referenced file cannot be found."""


class InvalidPathError(SmartYAMLError):
    """Raised when an invalid or unsafe path is provided."""


class EnvironmentVariableError(SmartYAMLError):
    """Raised when an environment variable is not found and no default is provided."""


class TemplatePathError(SmartYAMLError):
    """Raised when SMARTYAML_TMPL is not set or invalid."""


class Base64Error(SmartYAMLError):
    """Raised when base64 encoding/decoding fails."""


class ResourceLimitError(SmartYAMLError):
    """Raised when resource limits are exceeded."""


class RecursionLimitError(SmartYAMLError):
    """Raised when import recursion depth is exceeded."""


class ConstructorError(SmartYAMLError):
    """
    Enhanced constructor error with context and location information.

    This exception provides detailed error context for constructor failures,
    including directive names, parameter information, and YAML location data.
    """

    def __init__(
        self,
        directive_name: Optional[str] = None,
        parameter_name: Optional[str] = None,
        message: str = "",
        location: Optional[yaml.Mark] = None,
    ):
        """
        Initialize constructor error with enhanced context.

        Args:
            directive_name: The SmartYAML directive that failed (e.g., '!import')
            parameter_name: The specific parameter that caused the error
            message: The error message
            location: YAML location where the error occurred
        """
        self.directive_name = directive_name
        self.parameter_name = parameter_name
        self.location = location

        # Build enhanced message
        enhanced_message = self._build_message(
            directive_name, parameter_name, message, location
        )
        super().__init__(enhanced_message)

    def _build_message(
        self,
        directive_name: Optional[str],
        parameter_name: Optional[str],
        message: str,
        location: Optional[yaml.Mark],
    ) -> str:
        """Build an enhanced error message with context information."""
        parts = []

        if directive_name:
            parts.append(f"[{directive_name}]")

        if parameter_name:
            parts.append(f"parameter '{parameter_name}'")

        if parts:
            prefix = " ".join(parts) + ": "
        else:
            prefix = ""

        result = prefix + message

        if location and hasattr(location, "line"):
            result += f" (line {location.line + 1}, column {location.column + 1})"

        return result


class ErrorMessages:
    """Standardized error message templates for consistent error reporting."""

    REQUIRED_PARAMETER = "Required parameter '{param}' is missing"
    INVALID_PARAMETER_TYPE = (
        "Parameter '{param}' must be {expected_type}, got {actual_type}"
    )
    INVALID_PARAMETER_VALUE = "Invalid value for parameter '{param}': {reason}"
    PARAMETER_VALIDATION_FAILED = "Parameter '{param}' validation failed - {details}"

    FILE_NOT_FOUND = "Cannot access file '{filepath}': {reason}"
    FILE_READ_ERROR = "Failed to read file '{filepath}': {reason}"
    FILE_PARSE_ERROR = "Failed to parse file '{filepath}': {reason}"

    ENVIRONMENT_VAR_NOT_FOUND = (
        "Environment variable '{var_name}' not found and no default provided"
    )
    ENVIRONMENT_VAR_INVALID = (
        "Environment variable '{var_name}' has invalid value: {reason}"
    )

    RECURSION_LIMIT_EXCEEDED = (
        "Maximum recursion depth ({limit}) exceeded. Import chain: {chain}"
    )
    RESOURCE_LIMIT_EXCEEDED = "Resource limit exceeded - {details}"

    ENCODING_FAILED = "{operation} failed - {details}"
    TEMPLATE_ERROR = "Template processing failed: {details}"
    CONDITION_EVALUATION_FAILED = "Condition evaluation failed: {details}"


class ErrorFactory:
    """Factory for creating standardized errors with consistent formatting."""

    @staticmethod
    def parameter_required(
        directive_name: str, param_name: str, location: Optional[yaml.Mark] = None
    ) -> ConstructorError:
        """Create error for missing required parameter."""
        message = ErrorMessages.REQUIRED_PARAMETER.format(param=param_name)
        return ConstructorError(directive_name, param_name, message, location)

    @staticmethod
    def parameter_type_mismatch(
        directive_name: str,
        param_name: str,
        expected_type: type,
        actual_type: type,
        location: Optional[yaml.Mark] = None,
    ) -> ConstructorError:
        """Create error for parameter type mismatch."""
        message = ErrorMessages.INVALID_PARAMETER_TYPE.format(
            param=param_name,
            expected_type=expected_type.__name__,
            actual_type=actual_type.__name__,
        )
        return ConstructorError(directive_name, param_name, message, location)

    @staticmethod
    def parameter_validation_failed(
        directive_name: str,
        param_name: str,
        details: str,
        location: Optional[yaml.Mark] = None,
    ) -> ConstructorError:
        """Create error for parameter validation failure."""
        message = ErrorMessages.PARAMETER_VALIDATION_FAILED.format(
            param=param_name, details=details
        )
        return ConstructorError(directive_name, param_name, message, location)

    @staticmethod
    def file_not_found(
        directive_name: str, filepath: str, reason: str = "File not found"
    ) -> SmartYAMLFileNotFoundError:
        """Create error for file access issues."""
        message = ErrorMessages.FILE_NOT_FOUND.format(filepath=filepath, reason=reason)
        error = SmartYAMLFileNotFoundError(message)
        error.directive_name = directive_name
        error.filepath = filepath
        return error

    @staticmethod
    def environment_variable_error(
        directive_name: str, var_name: str, reason: str = "not found"
    ) -> EnvironmentVariableError:
        """Create error for environment variable issues."""
        if reason == "not found":
            message = ErrorMessages.ENVIRONMENT_VAR_NOT_FOUND.format(var_name=var_name)
        else:
            message = ErrorMessages.ENVIRONMENT_VAR_INVALID.format(
                var_name=var_name, reason=reason
            )

        error = EnvironmentVariableError(message)
        error.directive_name = directive_name
        error.var_name = var_name
        return error

    @staticmethod
    def recursion_limit_exceeded(
        directive_name: str, limit: int, import_chain: str
    ) -> RecursionLimitError:
        """Create error for recursion limit exceeded."""
        message = ErrorMessages.RECURSION_LIMIT_EXCEEDED.format(
            limit=limit, chain=import_chain
        )
        error = RecursionLimitError(message)
        error.directive_name = directive_name
        error.recursion_limit = limit
        return error

    @staticmethod
    def encoding_error(
        directive_name: str, operation: str, details: str
    ) -> Base64Error:
        """Create error for encoding/decoding failures."""
        message = ErrorMessages.ENCODING_FAILED.format(
            operation=operation, details=details
        )
        error = Base64Error(message)
        error.directive_name = directive_name
        error.operation = operation
        return error
