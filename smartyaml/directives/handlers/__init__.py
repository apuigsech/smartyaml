"""
SmartYAML directive handlers package.

This package contains all individual directive handler implementations,
organized by category for better maintainability.
"""

# Conditional directive handlers
from .conditional import (
    IfHandler,
    SwitchHandler,
)

# Data manipulation handlers
from .data import (
    ConcatHandler,
    ExpandHandler,
    MergeHandler,
    VarHandler,
)

# Environment variable handlers
from .env import (
    EnvBoolHandler,
    EnvFloatHandler,
    EnvHandler,
    EnvIntHandler,
    SecretHandler,
)

# File operation handlers
from .file import (
    IncludeHandler,
    IncludeIfHandler,
    IncludeYamlHandler,
    IncludeYamlIfHandler,
    TemplateHandler,
    TemplateIfHandler,
)

# All handler classes for easy registration
ALL_HANDLERS = [
    # Environment handlers
    EnvHandler,
    EnvIntHandler,
    EnvFloatHandler,
    EnvBoolHandler,
    SecretHandler,
    # Conditional handlers
    IfHandler,
    SwitchHandler,
    # File handlers
    IncludeHandler,
    IncludeIfHandler,
    IncludeYamlHandler,
    IncludeYamlIfHandler,
    TemplateHandler,
    TemplateIfHandler,
    # Data handlers
    MergeHandler,
    ConcatHandler,
    ExpandHandler,
    VarHandler,
]

__all__ = [
    # Environment handlers
    "EnvHandler",
    "EnvIntHandler",
    "EnvFloatHandler",
    "EnvBoolHandler",
    "SecretHandler",
    # Conditional handlers
    "IfHandler",
    "SwitchHandler",
    # File handlers
    "IncludeHandler",
    "IncludeIfHandler",
    "IncludeYamlHandler",
    "IncludeYamlIfHandler",
    "TemplateHandler",
    "TemplateIfHandler",
    # Data handlers
    "MergeHandler",
    "ConcatHandler",
    "ExpandHandler",
    "VarHandler",
    # Collections
    "ALL_HANDLERS",
]
