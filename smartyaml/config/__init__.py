"""
SmartYAML Configuration System

Modular configuration system with builder pattern and grouped settings.
"""

from .builder import SmartYAMLConfigBuilder, create_config
from .core import ConfigBuilder, ConfigSection, ConfigurationError, ConfigValidator
from .main import SmartYAMLConfig
from .paths import PathConfig
from .performance import PerformanceConfig
from .processing import ProcessingConfig
from .security import SecurityConfig

# Backward compatibility - export the main config as the old name
# This allows existing code to import SmartYAMLConfig without changes
__all__ = [
    # Core interfaces
    "ConfigSection",
    "ConfigBuilder",
    "ConfigValidator",
    "ConfigurationError",
    # Configuration sections
    "SecurityConfig",
    "PathConfig",
    "ProcessingConfig",
    "PerformanceConfig",
    # Main configuration
    "SmartYAMLConfig",
    # Builder
    "SmartYAMLConfigBuilder",
    "create_config",
]

# Default configuration instance for backward compatibility
DEFAULT_CONFIG = SmartYAMLConfig()
