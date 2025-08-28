"""
Configuration Builder

Fluent builder pattern for constructing SmartYAML configurations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .core import ConfigBuilder
from .main import SmartYAMLConfig
from .paths import PathConfig
from .performance import PerformanceConfig
from .processing import ProcessingConfig
from .security import SecurityConfig


class SmartYAMLConfigBuilder(ConfigBuilder):
    """
    Fluent builder for SmartYAML configuration.

    Provides a convenient way to construct configurations with method chaining
    and grouped settings for better organization.
    """

    def __init__(self):
        """Initialize the configuration builder."""
        self.reset()

    def reset(self) -> "SmartYAMLConfigBuilder":
        """Reset the builder to initial state."""
        self._security_config = {}
        self._paths_config = {}
        self._processing_config = {}
        self._performance_config = {}
        return self

    def build(self) -> SmartYAMLConfig:
        """Build the final SmartYAML configuration."""
        return SmartYAMLConfig(
            security=SecurityConfig(**self._security_config),
            paths=PathConfig(**self._paths_config),
            processing=ProcessingConfig(**self._processing_config),
            performance=PerformanceConfig(**self._performance_config),
        )

    # Security configuration methods

    def with_security_limits(
        self,
        max_file_size: Optional[int] = None,
        max_schema_size: Optional[int] = None,
        max_recursion_depth: Optional[int] = None,
        max_variable_depth: Optional[int] = None,
        max_nested_levels: Optional[int] = None,
    ) -> "SmartYAMLConfigBuilder":
        """Set security limits."""
        if max_file_size is not None:
            self._security_config["max_file_size"] = max_file_size
        if max_schema_size is not None:
            self._security_config["max_schema_size"] = max_schema_size
        if max_recursion_depth is not None:
            self._security_config["max_recursion_depth"] = max_recursion_depth
        if max_variable_depth is not None:
            self._security_config["max_variable_depth"] = max_variable_depth
        if max_nested_levels is not None:
            self._security_config["max_nested_levels"] = max_nested_levels
        return self

    def with_timeouts(
        self,
        processing_timeout: Optional[float] = None,
        remote_timeout: Optional[int] = None,
    ) -> "SmartYAMLConfigBuilder":
        """Set timeout values."""
        if processing_timeout is not None:
            self._security_config["processing_timeout"] = processing_timeout
        if remote_timeout is not None:
            self._security_config["remote_timeout"] = remote_timeout
        return self

    def with_env_var_controls(
        self,
        allowed_env_vars: Optional[List[str]] = None,
        forbidden_env_vars: Optional[List[str]] = None,
    ) -> "SmartYAMLConfigBuilder":
        """Set environment variable access controls."""
        if allowed_env_vars is not None:
            self._security_config["allowed_env_vars"] = allowed_env_vars
        if forbidden_env_vars is not None:
            self._security_config["forbidden_env_vars"] = forbidden_env_vars
        return self

    def with_security_modes(
        self,
        strict_security: Optional[bool] = None,
        sandbox_mode: Optional[bool] = None,
    ) -> "SmartYAMLConfigBuilder":
        """Set security modes."""
        if strict_security is not None:
            self._security_config["strict_security"] = strict_security
        if sandbox_mode is not None:
            self._security_config["sandbox_mode"] = sandbox_mode
        return self

    # Path configuration methods

    def with_paths(
        self,
        base_path: Optional[Union[str, Path]] = None,
        template_path: Optional[Union[str, Path]] = None,
        schema_base_path: Optional[Union[str, Path]] = None,
        templates_dir: Optional[str] = None,
    ) -> "SmartYAMLConfigBuilder":
        """Set file paths."""
        if base_path is not None:
            self._paths_config["base_path"] = (
                Path(base_path) if isinstance(base_path, str) else base_path
            )
        if template_path is not None:
            self._paths_config["template_path"] = (
                Path(template_path) if isinstance(template_path, str) else template_path
            )
        if schema_base_path is not None:
            self._paths_config["schema_base_path"] = (
                Path(schema_base_path)
                if isinstance(schema_base_path, str)
                else schema_base_path
            )
        if templates_dir is not None:
            self._paths_config["templates_dir"] = templates_dir
        return self

    def with_base_path(self, path: Union[str, Path]) -> "SmartYAMLConfigBuilder":
        """Set base path for relative file resolution."""
        self._paths_config["base_path"] = Path(path) if isinstance(path, str) else path
        return self

    def with_template_path(self, path: Union[str, Path]) -> "SmartYAMLConfigBuilder":
        """Set template directory path."""
        self._paths_config["template_path"] = (
            Path(path) if isinstance(path, str) else path
        )
        return self

    # Processing configuration methods

    def with_variables(self, variables: Dict[str, Any]) -> "SmartYAMLConfigBuilder":
        """Set variable overrides."""
        self._processing_config["variables"] = variables
        return self

    def add_variable(self, name: str, value: Any) -> "SmartYAMLConfigBuilder":
        """Add a single variable."""
        if "variables" not in self._processing_config:
            self._processing_config["variables"] = {}
        self._processing_config["variables"][name] = value
        return self

    def with_processing_options(
        self,
        strict_variables: Optional[bool] = None,
        remove_metadata: Optional[bool] = None,
        keep_undefined_variables: Optional[bool] = None,
    ) -> "SmartYAMLConfigBuilder":
        """Set processing behavior options."""
        if strict_variables is not None:
            self._processing_config["strict_variables"] = strict_variables
        if remove_metadata is not None:
            self._processing_config["remove_metadata"] = remove_metadata
        if keep_undefined_variables is not None:
            self._processing_config["keep_undefined_variables"] = (
                keep_undefined_variables
            )
        return self

    def with_schema_options(
        self,
        validate_schema: Optional[bool] = None,
        require_schema_validation: Optional[bool] = None,
        allow_remote_schemas: Optional[bool] = None,
    ) -> "SmartYAMLConfigBuilder":
        """Set schema validation options."""
        if validate_schema is not None:
            self._processing_config["validate_schema"] = validate_schema
        if require_schema_validation is not None:
            self._processing_config["require_schema_validation"] = (
                require_schema_validation
            )
        if allow_remote_schemas is not None:
            self._processing_config["allow_remote_schemas"] = allow_remote_schemas
        return self

    # Performance configuration methods

    def with_caching(
        self, enable_caching: Optional[bool] = None, cache_size: Optional[int] = None
    ) -> "SmartYAMLConfigBuilder":
        """Set caching options."""
        if enable_caching is not None:
            self._performance_config["enable_caching"] = enable_caching
        if cache_size is not None:
            self._performance_config["cache_size"] = cache_size
        return self

    def with_debug_options(
        self, audit_logging: Optional[bool] = None, debug_mode: Optional[bool] = None
    ) -> "SmartYAMLConfigBuilder":
        """Set debugging and logging options."""
        if audit_logging is not None:
            self._performance_config["audit_logging"] = audit_logging
        if debug_mode is not None:
            self._performance_config["debug_mode"] = debug_mode
        return self

    # Convenience methods for common configurations

    def development_mode(self) -> "SmartYAMLConfigBuilder":
        """Configure for development environment."""
        return (
            self.with_security_modes(strict_security=False, sandbox_mode=False)
            .with_processing_options(strict_variables=False, remove_metadata=False)
            .with_debug_options(debug_mode=True, audit_logging=True)
            .with_caching(enable_caching=True, cache_size=50)
        )

    def production_mode(self) -> "SmartYAMLConfigBuilder":
        """Configure for production environment."""
        return (
            self.with_security_modes(strict_security=True, sandbox_mode=False)
            .with_processing_options(strict_variables=True, remove_metadata=True)
            .with_schema_options(validate_schema=True, require_schema_validation=True)
            .with_debug_options(debug_mode=False, audit_logging=True)
            .with_caching(enable_caching=True, cache_size=200)
        )

    def sandbox_mode(self) -> "SmartYAMLConfigBuilder":
        """Configure for sandbox/restricted environment."""
        return (
            self.with_security_modes(strict_security=True, sandbox_mode=True)
            .with_env_var_controls(allowed_env_vars=[], forbidden_env_vars=[])
            .with_processing_options(strict_variables=True)
            .with_schema_options(allow_remote_schemas=False)
            .with_security_limits(max_file_size=1024 * 1024, max_recursion_depth=10)
        )

    # Legacy compatibility method

    @classmethod
    def from_legacy_config(cls, **kwargs) -> "SmartYAMLConfigBuilder":
        """Create builder from legacy configuration parameters."""
        builder = cls()

        # Map legacy parameters to new structure
        security_params = {
            "max_file_size",
            "max_schema_size",
            "max_recursion_depth",
            "max_variable_depth",
            "max_nested_levels",
            "processing_timeout",
            "remote_timeout",
            "allowed_env_vars",
            "forbidden_env_vars",
            "strict_security",
            "sandbox_mode",
        }

        paths_params = {
            "base_path",
            "template_path",
            "schema_base_path",
            "templates_dir",
        }

        processing_params = {
            "strict_variables",
            "remove_metadata",
            "validate_schema",
            "require_schema_validation",
            "allow_remote_schemas",
            "keep_undefined_variables",
            "variables",
        }

        performance_params = {
            "enable_caching",
            "cache_size",
            "audit_logging",
            "debug_mode",
        }

        for key, value in kwargs.items():
            if key in security_params:
                builder._security_config[key] = value
            elif key in paths_params:
                builder._paths_config[key] = value
            elif key in processing_params:
                builder._processing_config[key] = value
            elif key in performance_params:
                builder._performance_config[key] = value

        return builder


# Convenience function for creating configurations
def create_config(**kwargs) -> SmartYAMLConfig:
    """Create a SmartYAML configuration with legacy parameter support."""
    return SmartYAMLConfigBuilder.from_legacy_config(**kwargs).build()
