"""
Variable substitution utilities for SmartYAML
"""

import re
from typing import Any, Dict, Optional


class VariableSubstitutionEngine:
    """
    Engine for performing variable substitution with {{key}} syntax.

    Supports:
    - Simple substitution: {{key}} -> value
    - Escaping: \\{{key}} -> {{key}} (literal)
    - Recursive substitution within values
    """

    # Regex patterns for variable substitution
    VARIABLE_PATTERN = re.compile(r"(?<!\\)\{\{([^}]+)\}\}")
    ESCAPE_PATTERN = re.compile(r"\\(\{\{[^}]+\}\})")

    def __init__(self, variables: Optional[Dict[str, Any]] = None):
        """
        Initialize the substitution engine with variables.

        Args:
            variables: Dictionary of variable names to values
        """
        self.variables = variables or {}

    def substitute_string(self, text: str) -> str:
        """
        Perform variable substitution on a string.

        Args:
            text: String containing {{key}} patterns to substitute

        Returns:
            String with variables substituted

        Raises:
            ValueError: If a variable is not found
        """
        if not isinstance(text, str):
            return text

        # Special case: if the entire text is a single variable reference {{var}}
        # and the value is a dictionary (like deferred expansion), return the dict directly
        match = self.VARIABLE_PATTERN.fullmatch(text)
        if match:
            var_name = match.group(1).strip()
            if var_name in self.variables:
                value = self.variables[var_name]
                # Return dictionaries directly (for deferred expansions)
                if isinstance(value, dict):
                    return value

        def replace_variable(match):
            var_name = match.group(1).strip()
            if var_name not in self.variables:
                raise ValueError(
                    f"Variable '{var_name}' not found in substitution context"
                )

            value = self.variables[var_name]

            # Convert non-string values to string
            if not isinstance(value, str):
                value = str(value)

            return value

        # First, substitute variables
        result = self.VARIABLE_PATTERN.sub(replace_variable, text)

        # Then, unescape literal braces
        result = self.ESCAPE_PATTERN.sub(r"\1", result)

        return result

    def substitute_recursive(self, data: Any) -> Any:
        """
        Recursively perform variable substitution on data structures.

        Args:
            data: Data structure to process (dict, list, str, or primitive)

        Returns:
            Data structure with variables substituted
        """
        if isinstance(data, dict):
            return {
                key: self.substitute_recursive(value) for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self.substitute_recursive(item) for item in data]
        elif isinstance(data, str):
            return self.substitute_string(data)
        else:
            # Return primitives unchanged
            return data

    def has_variables(self, text: str) -> bool:
        """
        Check if a string contains variable patterns.

        Args:
            text: String to check

        Returns:
            True if string contains {{key}} patterns
        """
        if not isinstance(text, str):
            return False
        return bool(self.VARIABLE_PATTERN.search(text))

    def extract_variable_names(self, text: str) -> list[str]:
        """
        Extract all variable names from a string.

        Args:
            text: String to analyze

        Returns:
            List of variable names found in the string
        """
        if not isinstance(text, str):
            return []

        matches = self.VARIABLE_PATTERN.findall(text)
        return [match.strip() for match in matches]

    def update_variables(self, new_variables: Dict[str, Any]) -> None:
        """
        Update the variables dictionary.

        Args:
            new_variables: Dictionary of new variables to add/update
        """
        self.variables.update(new_variables)

    def merge_variables(
        self,
        base_vars: Optional[Dict[str, Any]],
        override_vars: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Merge variable dictionaries with override priority.

        Args:
            base_vars: Base variables (lower priority)
            override_vars: Override variables (higher priority)

        Returns:
            Merged variables dictionary
        """
        result = {}

        if base_vars:
            result.update(base_vars)

        if override_vars:
            result.update(override_vars)

        return result


def substitute_variables_in_content(content: str, variables: Dict[str, Any]) -> str:
    """
    Convenience function to substitute variables in string content.

    Args:
        content: String content with {{key}} patterns
        variables: Dictionary of variables

    Returns:
        Content with variables substituted
    """
    engine = VariableSubstitutionEngine(variables)
    return engine.substitute_string(content)


def extract_vars_metadata(data: Any) -> Dict[str, Any]:
    """
    Extract __vars metadata from a data structure.

    Args:
        data: Parsed YAML data structure

    Returns:
        Dictionary of variables from __vars field, empty if not found
    """
    if isinstance(data, dict) and "__vars" in data:
        vars_data = data["__vars"]
        if isinstance(vars_data, dict):
            return vars_data

    return {}
