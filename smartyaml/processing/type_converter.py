"""
Type conversion system for SmartYAML parameters
"""

from pathlib import Path
from typing import Any, Callable, Dict, Union

from ..exceptions import ConstructorError


class TypeConverter:
    """
    Standardized type conversion system for SmartYAML parameters.

    This class provides consistent type conversion logic that can be
    used across all constructors to ensure uniform behavior.
    """

    # Standard type converters
    CONVERTERS: Dict[str, Callable[[Any], Any]] = {
        "str": str,
        "string": str,
        "int": int,
        "integer": int,
        "float": float,
        "bool": lambda x: str(x).lower() in ("true", "1", "yes", "on", "enabled"),
        "boolean": lambda x: str(x).lower() in ("true", "1", "yes", "on", "enabled"),
        "path": Path,
        "pathlib.Path": Path,
    }

    def __init__(self, custom_converters: Dict[str, Callable[[Any], Any]] = None):
        """
        Initialize the type converter.

        Args:
            custom_converters: Additional type converters to register
        """
        self.converters = self.CONVERTERS.copy()
        if custom_converters:
            self.converters.update(custom_converters)

    def register_converter(
        self, type_name: str, converter: Callable[[Any], Any]
    ) -> None:
        """
        Register a custom type converter.

        Args:
            type_name: The name of the type to convert to
            converter: Function that converts a value to the target type
        """
        self.converters[type_name] = converter

    def convert(
        self,
        value: Any,
        target_type: Union[str, type],
        directive_name: str = "",
        param_name: str = "",
    ) -> Any:
        """
        Convert a value to the specified target type.

        Args:
            value: The value to convert
            target_type: The target type (string name or type object)
            directive_name: The directive name for error messages
            param_name: The parameter name for error messages

        Returns:
            The converted value

        Raises:
            ConstructorError: If conversion fails
        """
        if value is None:
            return None

        # Handle type objects
        if isinstance(target_type, type):
            type_name = target_type.__name__
            converter = target_type
        else:
            type_name = str(target_type)
            converter = self.converters.get(type_name)

            if converter is None:
                raise ConstructorError(
                    None,
                    None,
                    f"{directive_name}: Unknown type '{type_name}' for parameter '{param_name}'",
                    None,
                )

        try:
            return converter(value)
        except (ValueError, TypeError) as e:
            context = f"{directive_name}: " if directive_name else ""
            param_context = f"parameter '{param_name}' " if param_name else ""
            raise ConstructorError(
                None,
                None,
                f"{context}Failed to convert {param_context}to {type_name}: {str(e)}",
                None,
            ) from e

    def convert_parameters(
        self,
        params: Dict[str, Any],
        type_specs: Dict[str, Union[str, type]],
        directive_name: str = "",
    ) -> Dict[str, Any]:
        """
        Convert multiple parameters according to their type specifications.

        Args:
            params: The parameters to convert
            type_specs: Dictionary mapping parameter names to target types
            directive_name: The directive name for error messages

        Returns:
            Dictionary with converted parameter values

        Raises:
            ConstructorError: If any conversion fails
        """
        converted = params.copy()

        for param_name, target_type in type_specs.items():
            if param_name in converted and converted[param_name] is not None:
                converted[param_name] = self.convert(
                    converted[param_name], target_type, directive_name, param_name
                )

        return converted

    def get_supported_types(self) -> list:
        """Get a list of supported type names."""
        return list(self.converters.keys())


# Global type converter instance
_global_converter = TypeConverter()


def get_type_converter() -> TypeConverter:
    """Get the global type converter instance."""
    return _global_converter


def convert_value(
    value: Any,
    target_type: Union[str, type],
    directive_name: str = "",
    param_name: str = "",
) -> Any:
    """
    Convenience function to convert a value using the global converter.

    Args:
        value: The value to convert
        target_type: The target type (string name or type object)
        directive_name: The directive name for error messages
        param_name: The parameter name for error messages

    Returns:
        The converted value
    """
    return _global_converter.convert(value, target_type, directive_name, param_name)
