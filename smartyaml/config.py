"""
Centralized configuration system for SmartYAML
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Set

from .exceptions import SmartYAMLError


@dataclass
class SmartYAMLConfig:
    """
    Centralized configuration for SmartYAML with sensible defaults.

    This class manages all configurable aspects of SmartYAML behavior,
    including security limits, performance settings, and feature flags.
    """

    # Security settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB default
    max_recursion_depth: int = 10
    allow_absolute_paths: bool = False
    restricted_paths: Set[str] = field(
        default_factory=lambda: {
            "/etc/",
            "/proc/",
            "/sys/",
            "/dev/",  # Unix system paths
            "c:\\windows\\",
            "c:\\program files\\",  # Windows system paths
        }
    )

    # Performance settings
    enable_file_caching: bool = True
    cache_ttl_seconds: int = 60  # 1 minute for better development workflow
    max_cache_size_mb: int = 100
    cache_cleanup_interval: int = 60  # 1 minute

    # Feature flags
    enable_yaml_merging: bool = True
    enable_conditional_inclusion: bool = True
    enable_template_system: bool = True
    enable_environment_variables: bool = True
    enable_base64_operations: bool = True

    # Debugging and development
    debug_mode: bool = False
    enable_performance_tracking: bool = False
    log_import_chains: bool = False

    # Template system
    template_base_path: Optional[Path] = None
    template_file_extension: str = ".yaml"

    # Environment variable settings
    env_var_prefix: str = "SMARTYAML_"
    truthy_values: Set[str] = field(
        default_factory=lambda: {"1", "true", "yes", "on", "enabled"}
    )

    # Error handling
    include_stack_traces: bool = True
    max_error_context_items: int = 10

    def __post_init__(self):
        """Initialize configuration from environment variables."""
        self._load_from_environment()
        self._validate_config()

    def _load_from_environment(self):
        """Load configuration values from environment variables."""
        # Security settings
        if env_val := os.getenv(f"{self.env_var_prefix}MAX_FILE_SIZE"):
            self.max_file_size = self._parse_size(env_val)

        if env_val := os.getenv(f"{self.env_var_prefix}MAX_RECURSION_DEPTH"):
            self.max_recursion_depth = int(env_val)

        if env_val := os.getenv(f"{self.env_var_prefix}ALLOW_ABSOLUTE_PATHS"):
            self.allow_absolute_paths = self._parse_bool(env_val)

        # Performance settings
        if env_val := os.getenv(f"{self.env_var_prefix}ENABLE_CACHING"):
            self.enable_file_caching = self._parse_bool(env_val)

        if env_val := os.getenv(f"{self.env_var_prefix}CACHE_TTL"):
            self.cache_ttl_seconds = int(env_val)

        # Template path
        if env_val := os.getenv("SMARTYAML_TMPL"):
            self.template_base_path = Path(env_val)

        # Debug mode
        if env_val := os.getenv(f"{self.env_var_prefix}DEBUG"):
            self.debug_mode = self._parse_bool(env_val)

    def _validate_config(self):
        """Validate configuration values."""
        if self.max_file_size < 0:
            raise SmartYAMLError("max_file_size cannot be negative")

        if self.max_recursion_depth < 1:
            raise SmartYAMLError("max_recursion_depth must be at least 1")

        if self.cache_ttl_seconds < 0:
            raise SmartYAMLError("cache_ttl_seconds cannot be negative")

        if self.max_cache_size_mb < 0:
            raise SmartYAMLError("max_cache_size_mb cannot be negative")

    def _parse_bool(self, value: str) -> bool:
        """Parse boolean value from string."""
        return value.lower() in self.truthy_values

    def _parse_size(self, value: str) -> int:
        """Parse size value with optional suffix (K, M, G)."""
        value = value.upper().strip()

        if value.endswith("K"):
            return int(value[:-1]) * 1024
        elif value.endswith("M"):
            return int(value[:-1]) * 1024 * 1024
        elif value.endswith("G"):
            return int(value[:-1]) * 1024 * 1024 * 1024
        else:
            return int(value)

    def update(self, **kwargs) -> "SmartYAMLConfig":
        """Create a new config instance with updated values."""
        current_values = {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
        current_values.update(kwargs)
        return SmartYAMLConfig(**current_values)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for field_obj in self.__dataclass_fields__.values():
            value = getattr(self, field_obj.name)
            if isinstance(value, Path):
                value = str(value)
            elif isinstance(value, set):
                value = list(value)
            result[field_obj.name] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SmartYAMLConfig":
        """Create configuration from dictionary."""
        # Convert paths and sets back from serialized form
        if "template_base_path" in data and data["template_base_path"]:
            data["template_base_path"] = Path(data["template_base_path"])

        if "restricted_paths" in data:
            data["restricted_paths"] = set(data["restricted_paths"])

        if "truthy_values" in data:
            data["truthy_values"] = set(data["truthy_values"])

        return cls(**data)

    def is_path_restricted(self, path: Path) -> bool:
        """Check if a path is in the restricted paths."""
        path_str = str(path).lower()
        return any(
            path_str.startswith(restricted) for restricted in self.restricted_paths
        )


# Global default configuration instance
DEFAULT_CONFIG = SmartYAMLConfig()


def get_config() -> SmartYAMLConfig:
    """Get the current global configuration."""
    return DEFAULT_CONFIG


def set_config(config: SmartYAMLConfig):
    """Set the global configuration."""
    global DEFAULT_CONFIG
    DEFAULT_CONFIG = config


def update_config(**kwargs) -> SmartYAMLConfig:
    """Update the global configuration with new values."""
    global DEFAULT_CONFIG
    DEFAULT_CONFIG = DEFAULT_CONFIG.update(**kwargs)
    return DEFAULT_CONFIG
