"""
Standardized Error Message Templates for SmartYAML.

Provides consistent error message formatting with templated strings,
reducing duplication and improving maintainability of error messages.
"""

from enum import Enum
from typing import Any


class MessageCategory(Enum):
    """Categories of error messages for different contexts."""

    DIRECTIVE_SYNTAX = "directive_syntax"
    DIRECTIVE_PROCESSING = "directive_processing"
    TYPE_VALIDATION = "type_validation"
    SECURITY_VIOLATION = "security_violation"
    FILE_OPERATION = "file_operation"
    CONFIGURATION = "configuration"
    GENERAL = "general"


class MessageTemplates:
    """
    Standardized message templates with placeholder substitution.

    Provides consistent error message formatting across all SmartYAML components,
    with support for internationalization and customization.
    """

    # Template strings with placeholders
    TEMPLATES = {
        # Directive syntax errors
        MessageCategory.DIRECTIVE_SYNTAX: {
            "invalid_type": "{field} must be {expected}, got {actual}",
            "invalid_length": "{field} requires {constraint}, got {actual_length} {items}",
            "missing_keys": "{field} missing required keys: {missing_keys}",
            "unexpected_keys": "{field} contains unexpected keys: {unexpected_keys}",
            "invalid_pattern": "{field} must {pattern_description}, got '{value}'",
            "invalid_choice": "{field} must be one of: {choices}, got '{value}'",
            "unknown_directive": "Unknown directive '!{directive_name}'. Available directives: {available}",
        },
        # Directive processing errors
        MessageCategory.DIRECTIVE_PROCESSING: {
            "processing_failed": "Failed to process !{directive} directive: {reason}",
            "conversion_failed": "Cannot convert {value_type} '{value}' to {target_type}{context}: {reason}",
            "env_var_not_found": "Environment variable '{var_name}' not found and no default provided",
            "env_var_conversion": "Cannot convert environment variable '{var_name}' "
            "value '{value}' to {target_type}: {reason}",
        },
        # Type validation errors
        MessageCategory.TYPE_VALIDATION: {
            "wrong_type": "{field} must be {expected_type}, got {actual_type}",
            "list_length": "{field} length must be {constraint}, got {length}",
            "dict_validation": "{field} dictionary validation failed: {reason}",
        },
        # Security violation errors
        MessageCategory.SECURITY_VIOLATION: {
            "sandbox_blocked": "{operation} blocked in sandbox mode",
            "env_var_forbidden": "Access to environment variable '{var_name}' is forbidden",
            "env_var_not_allowed": "Environment variable '{var_name}' not in allowlist",
            "file_access_denied": "File access to '{file_path}' denied by security policy",
            "path_traversal": "Path '{path}' attempts to access files outside the allowed directory",
        },
        # File operation errors
        MessageCategory.FILE_OPERATION: {
            "file_not_found": "File not found: {file_path}",
            "file_read_error": "Failed to read file {file_path}: {reason}",
            "invalid_file_type": "Expected {expected_type}, got {actual_type}: {file_path}",
            "path_resolution": "Cannot resolve file path '{path}' - {reason}",
        },
        # Configuration errors
        MessageCategory.CONFIGURATION: {
            "missing_config": "{config_name} must be configured to use {feature}",
            "invalid_config": "Invalid {config_name} configuration: {reason}",
            "config_conflict": "Configuration conflict: {description}",
        },
        # General errors
        MessageCategory.GENERAL: {
            "recursion_limit": "Maximum recursion depth ({limit}) exceeded during {operation}",
            "timeout": "Processing timeout exceeded during {operation}",
            "file_size_limit": "File size {actual_size} exceeds limit {max_size}",
        },
    }

    @classmethod
    def format_message(
        self, category: MessageCategory, template_key: str, **kwargs: Any
    ) -> str:
        """
        Format a message using the specified template.

        Args:
            category: Message category
            template_key: Key within the category
            **kwargs: Template placeholder values

        Returns:
            Formatted message string

        Raises:
            KeyError: If template is not found
            ValueError: If required placeholders are missing
        """
        try:
            template = self.TEMPLATES[category][template_key]
        except KeyError:
            raise KeyError(f"Template not found: {category.value}.{template_key}")

        try:
            return template.format(**kwargs)
        except KeyError as e:
            missing_key = str(e).strip("'")
            raise ValueError(
                f"Missing placeholder '{missing_key}' for template {category.value}.{template_key}"
            )

    @classmethod
    def directive_syntax_error(
        self,
        directive_name: str,
        expected: str,
        actual: str,
        field_name: str = None,
        **kwargs: Any,
    ) -> str:
        """Format a directive syntax error message."""
        field = field_name or f"!{directive_name} directive"
        return self.format_message(
            MessageCategory.DIRECTIVE_SYNTAX,
            "invalid_type",
            field=field,
            expected=expected,
            actual=actual,
            **kwargs,
        )

    @classmethod
    def directive_processing_error(
        self, directive_name: str, reason: str, **kwargs: Any
    ) -> str:
        """Format a directive processing error message."""
        return self.format_message(
            MessageCategory.DIRECTIVE_PROCESSING,
            "processing_failed",
            directive=directive_name,
            reason=reason,
            **kwargs,
        )

    @classmethod
    def type_conversion_error(
        self,
        value: Any,
        target_type: str,
        reason: str,
        context: str = None,
        **kwargs: Any,
    ) -> str:
        """Format a type conversion error message."""
        context_str = f" for {context}" if context else ""
        return self.format_message(
            MessageCategory.DIRECTIVE_PROCESSING,
            "conversion_failed",
            value_type=type(value).__name__,
            value=str(value),
            target_type=target_type,
            context=context_str,
            reason=reason,
            **kwargs,
        )

    @classmethod
    def security_violation_error(self, violation_type: str, **kwargs: Any) -> str:
        """Format a security violation error message."""
        return self.format_message(
            MessageCategory.SECURITY_VIOLATION, violation_type, **kwargs
        )

    @classmethod
    def file_operation_error(self, error_type: str, **kwargs: Any) -> str:
        """Format a file operation error message."""
        return self.format_message(MessageCategory.FILE_OPERATION, error_type, **kwargs)

    @classmethod
    def validation_error(
        self, field_name: str, expected_type: str, actual_value: Any, **kwargs: Any
    ) -> str:
        """Format a validation error message."""
        return self.format_message(
            MessageCategory.TYPE_VALIDATION,
            "wrong_type",
            field=field_name,
            expected_type=expected_type,
            actual_type=type(actual_value).__name__,
            **kwargs,
        )


class MessageBuilder:
    """
    Fluent interface for building error messages.

    Provides a chainable API for constructing complex error messages
    with consistent formatting and context.
    """

    def __init__(self):
        self._category = None
        self._template_key = None
        self._placeholders = {}
        self._context = {}

    def for_directive(self, directive_name: str) -> "MessageBuilder":
        """Set directive context."""
        self._context["directive_name"] = directive_name
        return self

    def for_field(self, field_name: str) -> "MessageBuilder":
        """Set field context."""
        self._context["field_name"] = field_name
        return self

    def with_expected(self, expected: str) -> "MessageBuilder":
        """Set expected value."""
        self._placeholders["expected"] = expected
        return self

    def with_actual(self, actual: Any) -> "MessageBuilder":
        """Set actual value."""
        self._placeholders["actual"] = str(actual)
        self._placeholders["actual_type"] = type(actual).__name__
        return self

    def with_reason(self, reason: str) -> "MessageBuilder":
        """Set reason/cause."""
        self._placeholders["reason"] = reason
        return self

    def with_value(self, value: Any) -> "MessageBuilder":
        """Set value context."""
        self._placeholders["value"] = str(value)
        self._placeholders["value_type"] = type(value).__name__
        return self

    def with_placeholder(self, key: str, value: Any) -> "MessageBuilder":
        """Set custom placeholder."""
        self._placeholders[key] = value
        return self

    def directive_syntax_error(self) -> str:
        """Build directive syntax error message."""
        field = (
            self._placeholders.get("field")
            or f"!{self._context.get('directive_name', 'unknown')} directive"
        )
        return MessageTemplates.format_message(
            MessageCategory.DIRECTIVE_SYNTAX,
            "invalid_type",
            field=field,
            **self._placeholders,
        )

    def processing_error(self) -> str:
        """Build processing error message."""
        directive = self._context.get("directive_name", "unknown")
        return MessageTemplates.format_message(
            MessageCategory.DIRECTIVE_PROCESSING,
            "processing_failed",
            directive=directive,
            **self._placeholders,
        )

    def validation_error(self) -> str:
        """Build validation error message."""
        field = self._context.get("field_name", "value")
        return MessageTemplates.format_message(
            MessageCategory.TYPE_VALIDATION,
            "wrong_type",
            field=field,
            **self._placeholders,
        )

    def security_error(self, violation_type: str) -> str:
        """Build security violation error message."""
        return MessageTemplates.format_message(
            MessageCategory.SECURITY_VIOLATION, violation_type, **self._placeholders
        )

    def file_error(self, error_type: str) -> str:
        """Build file operation error message."""
        return MessageTemplates.format_message(
            MessageCategory.FILE_OPERATION, error_type, **self._placeholders
        )


# Convenience functions for common message types
def format_directive_error(
    directive_name: str, expected: str, actual: str, field_name: str = None
) -> str:
    """Format a standard directive syntax error."""
    return MessageTemplates.directive_syntax_error(
        directive_name, expected, actual, field_name
    )


def format_type_error(field_name: str, expected_type: str, actual_value: Any) -> str:
    """Format a standard type validation error."""
    return MessageTemplates.validation_error(field_name, expected_type, actual_value)


def format_conversion_error(
    value: Any, target_type: str, reason: str, context: str = None
) -> str:
    """Format a standard type conversion error."""
    return MessageTemplates.type_conversion_error(value, target_type, reason, context)


def create_message_builder() -> MessageBuilder:
    """Create a new message builder instance."""
    return MessageBuilder()
