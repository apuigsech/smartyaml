"""
Directive Registry for SmartYAML directive handlers.

Manages registration, discovery, and instantiation of directive handlers,
providing a clean plugin-like architecture for directives.
"""

from typing import Dict, List, Optional, Type

from ..config import SmartYAMLConfig
from .base import BaseDirectiveHandler


class DirectiveRegistry:
    """
    Registry for SmartYAML directive handlers.

    Manages the collection of available directive handlers and provides
    methods for registration, lookup, and instantiation.
    """

    def __init__(self):
        self._handler_classes: Dict[str, Type[BaseDirectiveHandler]] = {}
        self._handler_instances: Dict[str, BaseDirectiveHandler] = {}

    def register(self, handler_class: Type[BaseDirectiveHandler]) -> None:
        """
        Register a directive handler class.

        Args:
            handler_class: Handler class to register

        Raises:
            ValueError: If directive name conflicts with existing handler
        """
        # Create temporary instance to get directive name
        try:
            from ..config import SmartYAMLConfig

            temp_instance = handler_class(SmartYAMLConfig())
            directive_name = temp_instance.directive_name
        except Exception as e:
            raise ValueError(
                f"Cannot determine directive name for {handler_class.__name__}: {e}"
            )

        if directive_name in self._handler_classes:
            existing_class = self._handler_classes[directive_name]
            raise ValueError(
                f"Directive '{directive_name}' already registered by {existing_class.__name__}"
            )

        self._handler_classes[directive_name] = handler_class

    def get_handler(
        self, directive_name: str, config: SmartYAMLConfig
    ) -> Optional[BaseDirectiveHandler]:
        """
        Get a handler instance for the specified directive.

        Args:
            directive_name: Name of the directive
            config: SmartYAML configuration

        Returns:
            Handler instance or None if not found
        """
        if directive_name not in self._handler_classes:
            return None

        # Create instance if not cached or config changed
        cache_key = f"{directive_name}_{id(config)}"
        if cache_key not in self._handler_instances:
            handler_class = self._handler_classes[directive_name]
            self._handler_instances[cache_key] = handler_class(config)

        return self._handler_instances[cache_key]

    def is_registered(self, directive_name: str) -> bool:
        """
        Check if a directive is registered.

        Args:
            directive_name: Name of the directive

        Returns:
            True if directive is registered
        """
        return directive_name in self._handler_classes

    def get_registered_directives(self) -> List[str]:
        """
        Get list of all registered directive names.

        Returns:
            List of directive names
        """
        return list(self._handler_classes.keys())

    def clear(self) -> None:
        """Clear all registered handlers and cached instances."""
        self._handler_classes.clear()
        self._handler_instances.clear()

    def unregister(self, directive_name: str) -> bool:
        """
        Unregister a directive handler.

        Args:
            directive_name: Name of the directive to unregister

        Returns:
            True if handler was unregistered, False if not found
        """
        if directive_name not in self._handler_classes:
            return False

        del self._handler_classes[directive_name]

        # Clear cached instances for this directive
        keys_to_remove = [
            k
            for k in self._handler_instances.keys()
            if k.startswith(f"{directive_name}_")
        ]
        for key in keys_to_remove:
            del self._handler_instances[key]

        return True


# Global registry instance
_global_registry = DirectiveRegistry()


def get_global_registry() -> DirectiveRegistry:
    """Get the global directive registry instance."""
    return _global_registry


def register_handler(handler_class: Type[BaseDirectiveHandler]) -> None:
    """
    Register a handler with the global registry.

    Args:
        handler_class: Handler class to register
    """
    _global_registry.register(handler_class)


def get_handler(
    directive_name: str, config: SmartYAMLConfig
) -> Optional[BaseDirectiveHandler]:
    """
    Get a handler from the global registry.

    Args:
        directive_name: Name of the directive
        config: SmartYAML configuration

    Returns:
        Handler instance or None if not found
    """
    return _global_registry.get_handler(directive_name, config)


def auto_register_builtin_handlers() -> None:
    """
    Auto-register all built-in directive handlers.

    This function discovers and registers all built-in handlers
    from the handlers package.
    """
    from .handlers import ALL_HANDLERS

    for handler_class in ALL_HANDLERS:
        try:
            register_handler(handler_class)
        except ValueError as e:
            # Handler already registered - this is expected for repeated calls
            if "already registered" not in str(e):
                raise
