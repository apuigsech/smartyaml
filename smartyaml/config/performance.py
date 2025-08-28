"""
Performance Configuration

Settings related to caching, debugging, and performance optimization.
"""

from typing import Any, Dict

from .core import ConfigSection, ConfigurationError


class PerformanceConfig(ConfigSection):
    """Configuration for performance-related settings."""

    def __init__(
        self,
        enable_caching: bool = True,
        cache_size: int = 100,
        audit_logging: bool = False,
        debug_mode: bool = False,
    ):
        """
        Initialize performance configuration.

        Args:
            enable_caching: Enable processing result caching
            cache_size: Maximum number of items in cache
            audit_logging: Enable audit logging for security tracking
            debug_mode: Enable debug mode with verbose logging
        """
        self.enable_caching = enable_caching
        self.cache_size = cache_size
        self.audit_logging = audit_logging
        self.debug_mode = debug_mode

        self.validate()

    def validate(self) -> None:
        """Validate performance configuration settings."""
        if self.cache_size < 0:
            raise ConfigurationError("cache_size must be non-negative", "cache_size")

        if self.cache_size == 0 and self.enable_caching:
            raise ConfigurationError(
                "cache_size must be positive when caching is enabled", "cache_size"
            )

    def merge_with(self, other: "PerformanceConfig") -> "PerformanceConfig":
        """Merge with another performance configuration."""
        return PerformanceConfig(
            enable_caching=other.enable_caching,  # Use other's setting
            cache_size=max(self.cache_size, other.cache_size),  # Use larger cache
            audit_logging=self.audit_logging
            or other.audit_logging,  # Enable if either enables
            debug_mode=self.debug_mode or other.debug_mode,  # Enable if either enables
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert performance configuration to dictionary."""
        return {
            "enable_caching": self.enable_caching,
            "cache_size": self.cache_size,
            "audit_logging": self.audit_logging,
            "debug_mode": self.debug_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceConfig":
        """Create performance configuration from dictionary."""
        return cls(**data)
