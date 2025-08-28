"""
Processing Configuration

Settings related to processing behavior, variables, validation, and feature flags.
"""

from typing import Any, Dict, Optional

from .core import ConfigSection, ConfigurationError


class ProcessingConfig(ConfigSection):
    """Configuration for processing-related settings."""

    def __init__(
        self,
        strict_variables: bool = False,
        remove_metadata: bool = True,
        validate_schema: bool = False,
        require_schema_validation: bool = False,
        allow_remote_schemas: bool = False,
        keep_undefined_variables: bool = True,
        variables: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize processing configuration.

        Args:
            strict_variables: Raise errors for undefined variables
            remove_metadata: Remove __* metadata fields from output
            validate_schema: Enable schema validation
            require_schema_validation: Require schema to be present
            allow_remote_schemas: Allow loading schemas from remote URLs
            keep_undefined_variables: Keep undefined variables as {{var}} in output
            variables: External variable overrides
        """
        self.strict_variables = strict_variables
        self.remove_metadata = remove_metadata
        self.validate_schema = validate_schema
        self.require_schema_validation = require_schema_validation
        self.allow_remote_schemas = allow_remote_schemas
        self.keep_undefined_variables = keep_undefined_variables
        self.variables = variables or {}

        self.validate()

    def validate(self) -> None:
        """Validate processing configuration settings."""
        if not isinstance(self.variables, dict):
            raise ConfigurationError("variables must be a dictionary", "variables")

        if self.require_schema_validation and not self.validate_schema:
            raise ConfigurationError(
                "require_schema_validation requires validate_schema to be True",
                "require_schema_validation",
            )

    def merge_with(self, other: "ProcessingConfig") -> "ProcessingConfig":
        """Merge with another processing configuration."""
        # Merge variables with other's variables taking precedence
        merged_variables = {**self.variables, **other.variables}

        return ProcessingConfig(
            strict_variables=other.strict_variables,  # Use other's setting
            remove_metadata=other.remove_metadata,
            validate_schema=other.validate_schema,
            require_schema_validation=other.require_schema_validation,
            allow_remote_schemas=other.allow_remote_schemas,
            keep_undefined_variables=other.keep_undefined_variables,
            variables=merged_variables,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert processing configuration to dictionary."""
        return {
            "strict_variables": self.strict_variables,
            "remove_metadata": self.remove_metadata,
            "validate_schema": self.validate_schema,
            "require_schema_validation": self.require_schema_validation,
            "allow_remote_schemas": self.allow_remote_schemas,
            "keep_undefined_variables": self.keep_undefined_variables,
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessingConfig":
        """Create processing configuration from dictionary."""
        return cls(**data)

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable value with optional default."""
        return self.variables.get(name, default)

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value."""
        self.variables[name] = value

    def has_variable(self, name: str) -> bool:
        """Check if a variable exists."""
        return name in self.variables
