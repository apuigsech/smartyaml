"""
Security Checker Utilities for SmartYAML.

Centralizes security constraint checking and policy enforcement,
replacing duplicated security validation logic across handlers.
"""

import re
from pathlib import Path
from typing import Any, List

from ..config import SmartYAMLConfig
from ..exceptions import SecurityViolationError
from .message_templates import MessageCategory, MessageTemplates


class SecurityViolationType:
    """Constants for different types of security violations."""

    SANDBOX_ENV_ACCESS = "sandbox_env_access"
    SANDBOX_FILE_ACCESS = "sandbox_file_access"
    SANDBOX_SECRET_ACCESS = "sandbox_secret_access"
    ENV_VAR_FORBIDDEN = "env_var_forbidden"
    ENV_VAR_NOT_ALLOWED = "env_var_not_allowed"
    SECRET_NOT_ALLOWED = "secret_not_allowed"
    FILE_ACCESS_DENIED = "file_access_denied"
    PATH_TRAVERSAL = "path_traversal"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"


class SecurityChecker:
    """
    Centralized security policy enforcement.

    Provides consistent security constraint checking across all SmartYAML
    components, replacing duplicated validation logic in directive handlers.
    """

    def __init__(self, config: SmartYAMLConfig, context_file_path: str = None):
        """
        Initialize security checker with configuration.

        Args:
            config: SmartYAML configuration with security settings
            context_file_path: File path for error context
        """
        self.config = config
        self.context_file_path = context_file_path or "unknown"

    def check_env_var_access(self, var_name: str, is_secret: bool = False) -> None:
        """
        Check if environment variable access is allowed.

        Args:
            var_name: Environment variable name to check
            is_secret: Whether this is a secret variable (!secret directive)

        Raises:
            SecurityViolationError: If access is not allowed
        """
        # Check sandbox mode first
        if self.config.security.sandbox_mode:
            violation_type = (
                SecurityViolationType.SANDBOX_SECRET_ACCESS
                if is_secret
                else SecurityViolationType.SANDBOX_ENV_ACCESS
            )
            operation = (
                "Secret variable access" if is_secret else "Environment variable access"
            )
            message = MessageTemplates.format_message(
                MessageCategory.SECURITY_VIOLATION,
                "sandbox_blocked",
                operation=operation,
            )
            raise SecurityViolationError(
                message, self.context_file_path, violation_type
            )

        # Check forbidden variables
        if self.config.security.forbidden_env_vars:
            if self._is_var_forbidden(
                var_name, self.config.security.forbidden_env_vars
            ):
                message = MessageTemplates.format_message(
                    MessageCategory.SECURITY_VIOLATION,
                    "env_var_forbidden",
                    var_name=var_name,
                )
                raise SecurityViolationError(
                    message,
                    self.context_file_path,
                    SecurityViolationType.ENV_VAR_FORBIDDEN,
                )

        # Check allowed variables (if allowlist is defined)
        if self.config.security.allowed_env_vars:
            if var_name not in self.config.security.allowed_env_vars:
                violation_type = (
                    SecurityViolationType.SECRET_NOT_ALLOWED
                    if is_secret
                    else SecurityViolationType.ENV_VAR_NOT_ALLOWED
                )
                template_key = (
                    "secret_not_allowed" if is_secret else "env_var_not_allowed"
                )
                message = MessageTemplates.format_message(
                    MessageCategory.SECURITY_VIOLATION, template_key, var_name=var_name
                )
                raise SecurityViolationError(
                    message, self.context_file_path, violation_type
                )

        # Additional strict security checks for secrets
        if is_secret and self.config.security.strict_security:
            # In strict mode, secrets require explicit allowlisting
            if not self.config.security.allowed_env_vars:
                raise SecurityViolationError(
                    "Secret variables require explicit allowlisting in strict security mode",
                    self.context_file_path,
                    SecurityViolationType.SECRET_NOT_ALLOWED,
                )

    def check_file_access(self, file_path: str) -> Path:
        """
        Check if file access is allowed and resolve path safely.

        Args:
            file_path: File path to check and resolve

        Returns:
            Resolved Path object if access is allowed

        Raises:
            SecurityViolationError: If access is not allowed
        """
        # Check sandbox mode
        if self.config.security.sandbox_mode:
            message = MessageTemplates.format_message(
                MessageCategory.SECURITY_VIOLATION,
                "sandbox_blocked",
                operation="File access",
            )
            raise SecurityViolationError(
                message,
                self.context_file_path,
                SecurityViolationType.SANDBOX_FILE_ACCESS,
            )

        # Resolve and validate path
        resolved_path = self._resolve_and_validate_path(file_path)

        # Check file size limits if configured
        if (
            resolved_path.exists()
            and hasattr(self.config, "max_file_size")
            and self.config.max_file_size
        ):
            file_size = resolved_path.stat().st_size
            if file_size > self.config.max_file_size:
                message = MessageTemplates.format_message(
                    MessageCategory.GENERAL,
                    "file_size_limit",
                    actual_size=self._format_file_size(file_size),
                    max_size=self._format_file_size(self.config.max_file_size),
                )
                raise SecurityViolationError(
                    message,
                    self.context_file_path,
                    SecurityViolationType.FILE_SIZE_EXCEEDED,
                )

        return resolved_path

    def check_template_access(self, template_name: str) -> None:
        """
        Check if template access is allowed.

        Args:
            template_name: Template name to check

        Raises:
            SecurityViolationError: If access is not allowed
        """
        # Check sandbox mode
        if self.config.security.sandbox_mode:
            message = MessageTemplates.format_message(
                MessageCategory.SECURITY_VIOLATION,
                "sandbox_blocked",
                operation="Template access",
            )
            raise SecurityViolationError(
                message,
                self.context_file_path,
                SecurityViolationType.SANDBOX_FILE_ACCESS,
            )

        # Validate template name format (no path traversal)
        if self._contains_path_traversal(template_name):
            message = MessageTemplates.format_message(
                MessageCategory.SECURITY_VIOLATION, "path_traversal", path=template_name
            )
            raise SecurityViolationError(
                message, self.context_file_path, SecurityViolationType.PATH_TRAVERSAL
            )

    def validate_directive_security(self, directive_name: str, args: Any) -> None:
        """
        Perform directive-specific security validation.

        Args:
            directive_name: Name of directive being processed
            args: Directive arguments

        Raises:
            SecurityViolationError: If security constraints are violated
        """
        if directive_name in ["env", "env_int", "env_float", "env_bool"]:
            if isinstance(args, list) and len(args) > 0:
                var_name = args[0]
                if isinstance(var_name, str):
                    self.check_env_var_access(var_name, is_secret=False)

        elif directive_name == "secret":
            if isinstance(args, list) and len(args) > 0:
                var_name = args[0]
                if isinstance(var_name, str):
                    self.check_env_var_access(var_name, is_secret=True)

        elif directive_name in [
            "include",
            "include_if",
            "include_yaml",
            "include_yaml_if",
        ]:
            file_path = None
            if isinstance(args, str):
                file_path = args
            elif isinstance(args, list) and len(args) > 1:
                file_path = args[1]  # For *_if directives

            if file_path:
                self.check_file_access(file_path)

        elif directive_name in ["template", "template_if"]:
            template_name = None
            if isinstance(args, str):
                template_name = args
            elif isinstance(args, list) and len(args) > 1:
                template_name = args[1]  # For template_if

            if template_name:
                self.check_template_access(template_name)

    def _is_var_forbidden(self, var_name: str, forbidden_patterns: List[str]) -> bool:
        """Check if variable name matches any forbidden patterns."""
        var_upper = var_name.upper()
        for pattern in forbidden_patterns:
            if isinstance(pattern, str):
                if pattern.upper() in var_upper:
                    return True
            else:
                # Assume regex pattern
                try:
                    if re.search(pattern, var_name, re.IGNORECASE):
                        return True
                except re.error:
                    # Treat as literal string if regex compilation fails
                    if pattern.upper() in var_upper:
                        return True
        return False

    def _resolve_and_validate_path(self, file_path: str) -> Path:
        """Resolve file path and validate for security issues."""
        path = Path(file_path)

        # Convert to absolute path
        if not path.is_absolute():
            # Use base path from config if available
            if hasattr(self.config, "base_path") and self.config.base_path:
                path = Path(self.config.base_path) / path
            else:
                path = Path.cwd() / path

        # Resolve to canonical path
        try:
            resolved_path = path.resolve()
        except (OSError, RuntimeError) as e:
            message = MessageTemplates.format_message(
                MessageCategory.FILE_OPERATION,
                "path_resolution",
                path=str(path),
                reason=str(e),
            )
            raise SecurityViolationError(
                message, self.context_file_path, SecurityViolationType.PATH_TRAVERSAL
            )

        # Check for path traversal if base path is configured
        if hasattr(self.config, "base_path") and self.config.base_path:
            base_path = Path(self.config.base_path).resolve()
            try:
                resolved_path.relative_to(base_path)
            except ValueError:
                message = MessageTemplates.format_message(
                    MessageCategory.SECURITY_VIOLATION, "path_traversal", path=file_path
                )
                raise SecurityViolationError(
                    message,
                    self.context_file_path,
                    SecurityViolationType.PATH_TRAVERSAL,
                )

        return resolved_path

    def _contains_path_traversal(self, name: str) -> bool:
        """Check if name contains path traversal sequences."""
        dangerous_sequences = ["../", "..\\", "..", "/", "\\"]
        return any(seq in name for seq in dangerous_sequences)

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size for human-readable display."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"


def create_security_checker(
    config: SmartYAMLConfig, context_file_path: str = None
) -> SecurityChecker:
    """
    Create a SecurityChecker instance.

    Convenience function for creating security checkers with consistent configuration.

    Args:
        config: SmartYAML configuration
        context_file_path: File path for error context

    Returns:
        Configured SecurityChecker instance
    """
    return SecurityChecker(config, context_file_path)


# Decorator for automatic security validation
def validate_security(**security_rules):
    """
    Decorator for automatic directive security validation.

    Args:
        **security_rules: Security validation rules

    Example:
        @validate_security(check_env_access=True, check_sandbox=True)
        def handle_env_directive(self, value, context):
            # Security is automatically validated
            pass
    """

    def decorator(handler_method):
        def wrapper(self, value, context):
            checker = create_security_checker(
                self.config, getattr(context, "file_path", None)
            )

            # Apply security validations
            if security_rules.get("check_directive_security", False):
                checker.validate_directive_security(self.directive_name, value)

            return handler_method(self, value, context)

        return wrapper

    return decorator
