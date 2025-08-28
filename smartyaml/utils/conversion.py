"""
Type conversion utilities for SmartYAML.

Provides standardized type conversion logic with consistent behavior
across all components that need to convert between data types.
"""

from typing import Any, Dict, List, Set, Type


class BooleanConverter:
    """
    Standardized boolean conversion utility.

    Provides consistent boolean conversion logic with configurable
    truthy/falsy values and proper error handling.
    """

    # Default truthy values (case-insensitive)
    DEFAULT_TRUTHY: Set[str] = {"true", "yes", "1", "on", "enabled"}

    # Default falsy values (case-insensitive)
    DEFAULT_FALSY: Set[str] = {"false", "no", "0", "off", "disabled", ""}

    def __init__(
        self,
        truthy_values: Set[str] = None,
        falsy_values: Set[str] = None,
        strict: bool = True,
    ):
        """
        Initialize boolean converter with custom rules.

        Args:
            truthy_values: Custom set of truthy string values (case-insensitive)
            falsy_values: Custom set of falsy string values (case-insensitive)
            strict: If True, raise error for unrecognized values. If False, treat as falsy.
        """
        self.truthy = truthy_values or self.DEFAULT_TRUTHY
        self.falsy = falsy_values or self.DEFAULT_FALSY
        self.strict = strict

        # Convert to lowercase for case-insensitive comparison
        self.truthy = {v.lower() for v in self.truthy}
        self.falsy = {v.lower() for v in self.falsy}

    def convert(self, value: Any, context: str = None) -> bool:
        """
        Convert value to boolean using configured rules.

        Args:
            value: Value to convert to boolean
            context: Optional context string for error messages

        Returns:
            Boolean result

        Raises:
            ValueError: If strict=True and value cannot be converted
        """
        # Handle already-boolean values
        if isinstance(value, bool):
            return value

        # Handle numeric values
        if isinstance(value, (int, float)):
            return bool(value)

        # Handle string values
        if isinstance(value, str):
            value_lower = value.lower()

            if value_lower in self.truthy:
                return True
            elif value_lower in self.falsy:
                return False
            elif self.strict:
                all_valid = self.truthy | self.falsy
                valid_list = ", ".join(sorted(all_valid))
                context_msg = f" for {context}" if context else ""
                raise ValueError(
                    f"Invalid boolean value '{value}'{context_msg}. "
                    f"Valid values are: {valid_list}"
                )
            else:
                # Non-strict mode: treat unrecognized strings as falsy
                return False

        # Handle other types
        if value is None:
            return False

        # For lists, dicts, etc., use Python's built-in bool()
        if isinstance(value, (list, dict, set, tuple)):
            return bool(value)

        # For any other type, try built-in bool conversion
        try:
            return bool(value)
        except Exception:
            if self.strict:
                context_msg = f" for {context}" if context else ""
                raise ValueError(
                    f"Cannot convert {type(value).__name__} '{value}' to boolean{context_msg}"
                )
            else:
                return False

    def get_valid_values(self) -> List[str]:
        """Get list of all valid boolean string values."""
        return sorted(self.truthy | self.falsy)

    def is_valid_string(self, value: str) -> bool:
        """Check if string value is a valid boolean representation."""
        return value.lower() in (self.truthy | self.falsy)


class TypeConverter:
    """
    General-purpose type conversion utilities.

    Provides standardized type conversion with consistent error handling
    and support for SmartYAML-specific conversion rules.
    """

    def __init__(self):
        self.boolean_converter = BooleanConverter()

    def convert_to_type(
        self, value: Any, target_type: Type, context: str = None, strict: bool = True
    ) -> Any:
        """
        Convert value to the specified type with error handling.

        Args:
            value: Value to convert
            target_type: Target type for conversion
            context: Optional context string for error messages
            strict: Whether to use strict conversion rules

        Returns:
            Converted value

        Raises:
            ValueError: If conversion fails
            TypeError: If target_type is not supported
        """
        if target_type == bool:
            converter = BooleanConverter(strict=strict)
            return converter.convert(value, context)

        elif target_type == int:
            return self._convert_to_int(value, context)

        elif target_type == float:
            return self._convert_to_float(value, context)

        elif target_type == str:
            return str(value)

        elif target_type in (list, List):
            if isinstance(value, (list, tuple)):
                return list(value)
            elif isinstance(value, str):
                # Could implement string-to-list conversion if needed
                return [value]
            else:
                return [value]

        elif target_type in (dict, Dict):
            if isinstance(value, dict):
                return value
            else:
                context_msg = f" for {context}" if context else ""
                raise ValueError(
                    f"Cannot convert {type(value).__name__} to dict{context_msg}"
                )

        else:
            # Try direct type constructor
            try:
                return target_type(value)
            except Exception as e:
                context_msg = f" for {context}" if context else ""
                raise ValueError(
                    f"Cannot convert {type(value).__name__} '{value}' to "
                    f"{target_type.__name__}{context_msg}: {e}"
                )

    def _convert_to_int(self, value: Any, context: str = None) -> int:
        """Convert value to integer with error handling."""
        if isinstance(value, int):
            return value

        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            else:
                context_msg = f" for {context}" if context else ""
                raise ValueError(
                    f"Cannot convert float {value} to int without precision loss{context_msg}"
                )

        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                # Try float conversion first, then to int
                try:
                    float_val = float(value)
                    if float_val.is_integer():
                        return int(float_val)
                    else:
                        context_msg = f" for {context}" if context else ""
                        raise ValueError(
                            f"Cannot convert '{value}' to int without precision loss{context_msg}"
                        )
                except ValueError:
                    context_msg = f" for {context}" if context else ""
                    raise ValueError(f"Cannot convert '{value}' to int{context_msg}")

        context_msg = f" for {context}" if context else ""
        raise ValueError(
            f"Cannot convert {type(value).__name__} '{value}' to int{context_msg}"
        )

    def _convert_to_float(self, value: Any, context: str = None) -> float:
        """Convert value to float with error handling."""
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                context_msg = f" for {context}" if context else ""
                raise ValueError(f"Cannot convert '{value}' to float{context_msg}")

        context_msg = f" for {context}" if context else ""
        raise ValueError(
            f"Cannot convert {type(value).__name__} '{value}' to float{context_msg}"
        )


# Global instances for easy access
boolean_converter = BooleanConverter()
type_converter = TypeConverter()


def convert_to_bool(value: Any, context: str = None, strict: bool = True) -> bool:
    """
    Convert value to boolean using standard SmartYAML rules.

    Convenience function that uses the global boolean converter.

    Args:
        value: Value to convert
        context: Optional context for error messages
        strict: Whether to use strict conversion rules

    Returns:
        Boolean result

    Raises:
        ValueError: If strict=True and conversion fails
    """
    converter = BooleanConverter(strict=strict)
    return converter.convert(value, context)


def convert_value(
    value: Any, target_type: Type, context: str = None, strict: bool = True
) -> Any:
    """
    Convert value to specified type using standard SmartYAML rules.

    Convenience function that uses the global type converter.

    Args:
        value: Value to convert
        target_type: Target type for conversion
        context: Optional context for error messages
        strict: Whether to use strict conversion rules

    Returns:
        Converted value

    Raises:
        ValueError: If conversion fails
    """
    return type_converter.convert_to_type(value, target_type, context, strict)
