"""
SmartYAML directives package.

This package provides a modular directive processing system with:
- Abstract base classes for consistent directive interfaces
- Registry pattern for plugin-like directive management
- Individual handlers for all SmartYAML directives
- Automatic registration of built-in handlers

The new architecture replaces the monolithic DirectiveProcessor with
a clean, extensible system that follows SOLID principles.
"""

from .base import (
    BaseDirectiveHandler,
    ConditionalDirectiveHandler,
    DataDirectiveHandler,
    DirectiveContext,
    EnvironmentDirectiveHandler,
    FileDirectiveHandler,
)
from .registry import (
    DirectiveRegistry,
    auto_register_builtin_handlers,
    get_global_registry,
    get_handler,
    register_handler,
)

# Auto-register all built-in handlers on import
auto_register_builtin_handlers()

__all__ = [
    # Base classes
    "BaseDirectiveHandler",
    "ConditionalDirectiveHandler",
    "FileDirectiveHandler",
    "DataDirectiveHandler",
    "EnvironmentDirectiveHandler",
    "DirectiveContext",
    # Registry
    "DirectiveRegistry",
    "get_global_registry",
    "register_handler",
    "get_handler",
    "auto_register_builtin_handlers",
]
