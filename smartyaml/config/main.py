"""
Main SmartYAML Configuration

Combines all configuration sections into a unified configuration object.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import PathConfig
from .performance import PerformanceConfig
from .processing import ProcessingConfig
from .security import SecurityConfig


class SmartYAMLConfig:
    """
    Main SmartYAML configuration combining all configuration sections.

    This replaces the original monolithic SmartYAMLConfig with a more organized
    approach using composition of specialized configuration sections.
    """

    def __init__(
        self,
        security: Optional[SecurityConfig] = None,
        paths: Optional[PathConfig] = None,
        processing: Optional[ProcessingConfig] = None,
        performance: Optional[PerformanceConfig] = None,
        **kwargs,
    ):
        """
        Initialize SmartYAML configuration.

        Args:
            security: Security-related settings
            paths: Path-related settings
            processing: Processing behavior settings
            performance: Performance and caching settings
            **kwargs: Legacy configuration parameters for backward compatibility
        """
        # Handle legacy parameter style
        if kwargs:
            # Import here to avoid circular imports
            from .builder import SmartYAMLConfigBuilder

            # Build using legacy parameters
            built_config = SmartYAMLConfigBuilder.from_legacy_config(**kwargs).build()
            self.security = built_config.security
            self.paths = built_config.paths
            self.processing = built_config.processing
            self.performance = built_config.performance
        else:
            # Use new style initialization
            self.security = security or SecurityConfig()
            self.paths = paths or PathConfig()
            self.processing = processing or ProcessingConfig()
            self.performance = performance or PerformanceConfig()

        # Current library version
        self.version: str = "1.0.0"

        self.validate()

    def validate(self) -> None:
        """Validate all configuration sections."""
        self.security.validate()
        self.paths.validate()
        self.processing.validate()
        self.performance.validate()

    def merge_with(self, other: "SmartYAMLConfig") -> "SmartYAMLConfig":
        """Create a new configuration by merging with another configuration."""
        return SmartYAMLConfig(
            security=self.security.merge_with(other.security),
            paths=self.paths.merge_with(other.paths),
            processing=self.processing.merge_with(other.processing),
            performance=self.performance.merge_with(other.performance),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "security": self.security.to_dict(),
            "paths": self.paths.to_dict(),
            "processing": self.processing.to_dict(),
            "performance": self.performance.to_dict(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SmartYAMLConfig":
        """Create configuration from dictionary."""
        return cls(
            security=SecurityConfig.from_dict(data.get("security", {})),
            paths=PathConfig.from_dict(data.get("paths", {})),
            processing=ProcessingConfig.from_dict(data.get("processing", {})),
            performance=PerformanceConfig.from_dict(data.get("performance", {})),
        )

    # Backward compatibility properties - delegate to appropriate sections
    # These maintain compatibility with the original SmartYAMLConfig interface

    @property
    def max_file_size(self) -> int:
        return self.security.max_file_size

    @property
    def max_schema_size(self) -> int:
        return self.security.max_schema_size

    @property
    def max_recursion_depth(self) -> int:
        return self.security.max_recursion_depth

    @property
    def max_variable_depth(self) -> int:
        return self.security.max_variable_depth

    @property
    def max_nested_levels(self) -> int:
        return self.security.max_nested_levels

    @property
    def processing_timeout(self) -> float:
        return self.security.processing_timeout

    @property
    def remote_timeout(self) -> int:
        return self.security.remote_timeout

    @property
    def base_path(self) -> Optional["Path"]:
        return self.paths.base_path

    @property
    def template_path(self) -> Optional["Path"]:
        return self.paths.template_path

    @property
    def schema_base_path(self) -> Optional["Path"]:
        return self.paths.schema_base_path

    @property
    def variables(self) -> Dict[str, Any]:
        return self.processing.variables

    @property
    def allowed_env_vars(self) -> Optional[List[str]]:
        return self.security.allowed_env_vars

    @property
    def forbidden_env_vars(self) -> List[str]:
        return self.security.forbidden_env_vars

    @property
    def strict_variables(self) -> bool:
        return self.processing.strict_variables

    @property
    def strict_security(self) -> bool:
        return self.security.strict_security

    @property
    def sandbox_mode(self) -> bool:
        return self.security.sandbox_mode

    @property
    def remove_metadata(self) -> bool:
        return self.processing.remove_metadata

    @property
    def validate_schema(self) -> bool:
        return self.processing.validate_schema

    @property
    def require_schema_validation(self) -> bool:
        return self.processing.require_schema_validation

    @property
    def allow_remote_schemas(self) -> bool:
        return self.processing.allow_remote_schemas

    @property
    def keep_undefined_variables(self) -> bool:
        return self.processing.keep_undefined_variables

    @property
    def enable_caching(self) -> bool:
        return self.performance.enable_caching

    @property
    def cache_size(self) -> int:
        return self.performance.cache_size

    @property
    def audit_logging(self) -> bool:
        return self.performance.audit_logging

    @property
    def debug_mode(self) -> bool:
        return self.performance.debug_mode
