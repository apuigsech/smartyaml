"""
Security Configuration

Settings related to security limits, environment variable access, and sandbox mode.
"""

from typing import Any, Dict, List, Optional

from .core import ConfigSection, ConfigurationError


class SecurityConfig(ConfigSection):
    """Configuration for security-related settings."""

    def __init__(
        self,
        max_file_size: int = 5 * 1024 * 1024,  # 5MB
        max_schema_size: int = 1 * 1024 * 1024,  # 1MB
        max_recursion_depth: int = 20,
        max_variable_depth: int = 10,
        max_nested_levels: int = 10,
        processing_timeout: float = 60.0,  # seconds
        remote_timeout: int = 10,  # seconds
        allowed_env_vars: Optional[List[str]] = None,
        forbidden_env_vars: Optional[List[str]] = None,
        strict_security: bool = True,
        sandbox_mode: bool = False,
    ):
        """
        Initialize security configuration.

        Args:
            max_file_size: Maximum allowed file size in bytes
            max_schema_size: Maximum allowed schema size in bytes
            max_recursion_depth: Maximum recursion depth for processing
            max_variable_depth: Maximum depth for variable expansion
            max_nested_levels: Maximum nesting levels in data structures
            processing_timeout: Timeout for processing operations
            remote_timeout: Timeout for remote operations
            allowed_env_vars: List of allowed environment variables (None = all allowed)
            forbidden_env_vars: List of forbidden environment variables
            strict_security: Enable strict security checks
            sandbox_mode: Enable sandbox mode (restricts file and env access)
        """
        self.max_file_size = max_file_size
        self.max_schema_size = max_schema_size
        self.max_recursion_depth = max_recursion_depth
        self.max_variable_depth = max_variable_depth
        self.max_nested_levels = max_nested_levels
        self.processing_timeout = processing_timeout
        self.remote_timeout = remote_timeout
        self.allowed_env_vars = allowed_env_vars
        self.forbidden_env_vars = forbidden_env_vars
        self.strict_security = strict_security
        self.sandbox_mode = sandbox_mode

        self.validate()

    def validate(self) -> None:
        """Validate security configuration settings."""
        if self.max_file_size <= 0:
            raise ConfigurationError("max_file_size must be positive", "max_file_size")

        if self.max_schema_size <= 0:
            raise ConfigurationError(
                "max_schema_size must be positive", "max_schema_size"
            )

        if self.max_recursion_depth <= 0:
            raise ConfigurationError(
                "max_recursion_depth must be positive", "max_recursion_depth"
            )

        if self.max_variable_depth <= 0:
            raise ConfigurationError(
                "max_variable_depth must be positive", "max_variable_depth"
            )

        if self.max_nested_levels <= 0:
            raise ConfigurationError(
                "max_nested_levels must be positive", "max_nested_levels"
            )

        if self.processing_timeout <= 0:
            raise ConfigurationError(
                "processing_timeout must be positive", "processing_timeout"
            )

        if self.remote_timeout <= 0:
            raise ConfigurationError(
                "remote_timeout must be positive", "remote_timeout"
            )

        # Validate environment variable lists
        if self.allowed_env_vars is not None:
            if not isinstance(self.allowed_env_vars, list):
                raise ConfigurationError(
                    "allowed_env_vars must be a list", "allowed_env_vars"
                )

            for var in self.allowed_env_vars:
                if not isinstance(var, str) or not var:
                    raise ConfigurationError(
                        "allowed_env_vars must contain non-empty strings",
                        "allowed_env_vars",
                    )

        if self.forbidden_env_vars is not None:
            if not isinstance(self.forbidden_env_vars, list):
                raise ConfigurationError(
                    "forbidden_env_vars must be a list", "forbidden_env_vars"
                )

            for var in self.forbidden_env_vars:
                if not isinstance(var, str) or not var:
                    raise ConfigurationError(
                        "forbidden_env_vars must contain non-empty strings",
                        "forbidden_env_vars",
                    )

        # Check for conflicts
        if (
            self.allowed_env_vars is not None
            and self.forbidden_env_vars is not None
            and any(var in self.allowed_env_vars for var in self.forbidden_env_vars)
        ):
            raise ConfigurationError(
                "Environment variables cannot be both allowed and forbidden", "env_vars"
            )

    def merge_with(self, other: "SecurityConfig") -> "SecurityConfig":
        """Merge with another security configuration."""
        # Merge environment variable lists
        merged_forbidden = None
        if self.forbidden_env_vars is not None and other.forbidden_env_vars is not None:
            merged_forbidden = list(
                set(self.forbidden_env_vars + other.forbidden_env_vars)
            )
        elif self.forbidden_env_vars is not None:
            merged_forbidden = self.forbidden_env_vars[:]
        elif other.forbidden_env_vars is not None:
            merged_forbidden = other.forbidden_env_vars[:]

        # For allowed vars, None means "all allowed", so take the most restrictive
        merged_allowed = None
        if self.allowed_env_vars is not None and other.allowed_env_vars is not None:
            # Both have restrictions - take intersection (most restrictive)
            merged_allowed = list(
                set(self.allowed_env_vars) & set(other.allowed_env_vars)
            )
        elif self.allowed_env_vars is not None:
            merged_allowed = self.allowed_env_vars[:]  # Copy
        elif other.allowed_env_vars is not None:
            merged_allowed = other.allowed_env_vars[:]  # Copy

        return SecurityConfig(
            max_file_size=min(
                self.max_file_size, other.max_file_size
            ),  # Most restrictive
            max_schema_size=min(self.max_schema_size, other.max_schema_size),
            max_recursion_depth=min(
                self.max_recursion_depth, other.max_recursion_depth
            ),
            max_variable_depth=min(self.max_variable_depth, other.max_variable_depth),
            max_nested_levels=min(self.max_nested_levels, other.max_nested_levels),
            processing_timeout=min(self.processing_timeout, other.processing_timeout),
            remote_timeout=min(self.remote_timeout, other.remote_timeout),
            allowed_env_vars=merged_allowed,
            forbidden_env_vars=merged_forbidden,
            strict_security=self.strict_security
            or other.strict_security,  # Most restrictive
            sandbox_mode=self.sandbox_mode or other.sandbox_mode,  # Most restrictive
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert security configuration to dictionary."""
        return {
            "max_file_size": self.max_file_size,
            "max_schema_size": self.max_schema_size,
            "max_recursion_depth": self.max_recursion_depth,
            "max_variable_depth": self.max_variable_depth,
            "max_nested_levels": self.max_nested_levels,
            "processing_timeout": self.processing_timeout,
            "remote_timeout": self.remote_timeout,
            "allowed_env_vars": self.allowed_env_vars,
            "forbidden_env_vars": self.forbidden_env_vars,
            "strict_security": self.strict_security,
            "sandbox_mode": self.sandbox_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityConfig":
        """Create security configuration from dictionary."""
        return cls(**data)

    def is_env_var_allowed(self, var_name: str) -> bool:
        """Check if an environment variable is allowed to be accessed."""
        if self.sandbox_mode:
            return False

        if self.forbidden_env_vars and var_name in self.forbidden_env_vars:
            return False

        if self.allowed_env_vars is not None:
            return var_name in self.allowed_env_vars

        return True
