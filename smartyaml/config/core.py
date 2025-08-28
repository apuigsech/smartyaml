"""
Core Configuration System

Base classes and interfaces for SmartYAML configuration management.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol


class ConfigSection(ABC):
    """Base class for configuration sections."""

    @abstractmethod
    def validate(self) -> None:
        """Validate configuration section settings."""
        pass

    @abstractmethod
    def merge_with(self, other: "ConfigSection") -> "ConfigSection":
        """Merge with another configuration section."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration section to dictionary."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSection":
        """Create configuration section from dictionary."""
        pass


class ConfigValidator(Protocol):
    """Protocol for configuration validators."""

    def validate(self, value: Any, field_name: str) -> Any:
        """Validate a configuration value."""
        ...


class ConfigBuilder(ABC):
    """Abstract base for configuration builders."""

    @abstractmethod
    def build(self) -> Any:
        """Build the final configuration object."""
        pass

    @abstractmethod
    def reset(self) -> "ConfigBuilder":
        """Reset the builder to initial state."""
        pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field
