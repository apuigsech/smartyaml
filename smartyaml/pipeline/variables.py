"""
Stage 5: Variable Processing

Handles {{variable}} expansion with proper precedence rules according to SPECS-v1.md.
Supports recursive expansion and security controls.
"""

import copy
from typing import Any, Dict

from ..config import SmartYAMLConfig
from ..exceptions import (
    RecursionLimitExceededError,
    VariableExpansionError,
    VariableNotFoundError,
)
from ..utils.merge import DeepMerger, MergeStrategy


class VariableProcessor:
    """Stage 5: Expand {{variable}} placeholders with proper precedence."""

    # Variable expansion pattern: {{variable_name}} or {{variable.nested}}
    # Note: We'll use a more sophisticated parser for variables with nested braces

    def __init__(self, config: SmartYAMLConfig):
        self.config = config
        self.expansion_cache = {}  # Cache for performance

    def process(self, data: Any, context) -> Any:
        """Process variable expansion throughout the data structure."""
        # Create enhanced variables that include the processed data structure for cross-references
        enhanced_variables = copy.deepcopy(context.variables)
        if isinstance(data, dict):
            # Add flattened access to processed data (but don't override variables)
            self._add_data_context(enhanced_variables, data)

        return self._expand_recursive(data, enhanced_variables, context)

    def expand_string(self, template: str, variables: Dict[str, Any], context) -> str:
        """Expand a single string template with variables."""
        return self._expand_string_template(template, variables, context, set(), 0)

    def _expand_recursive(self, data: Any, variables: Dict[str, Any], context) -> Any:
        """Recursively expand variables in data structure."""
        if isinstance(data, dict):
            # Check for deferred expansion marker
            if "__expand_deferred__" in data and len(data) == 1:
                # This is a deferred expansion from !expand directive
                template = data["__expand_deferred__"]
                return self._expand_string_template(
                    template, variables, context, set(), 0
                )

            result = {}
            for key, value in data.items():
                # Expand both key and value
                expanded_key = self._expand_recursive(key, variables, context)
                expanded_value = self._expand_recursive(value, variables, context)
                result[expanded_key] = expanded_value
            return result

        elif isinstance(data, list):
            return [self._expand_recursive(item, variables, context) for item in data]

        elif isinstance(data, str):
            return self._expand_string_template(data, variables, context, set(), 0)

        else:
            # Scalar values (int, float, bool, None)
            return data

    def _expand_string_template(
        self,
        template: str,
        variables: Dict[str, Any],
        context,
        visited_vars: set,
        depth: int = 0,
    ) -> Any:
        """Expand variables in a string template."""
        if not isinstance(template, str):
            return template

        # Check variable expansion depth limit
        if depth > self.config.max_variable_depth:
            raise RecursionLimitExceededError(
                self.config.max_variable_depth,
                "variable expansion depth",
                str(context.file_path),
            )

        # Check for variable references
        if "{{" not in template:
            return template

        # Find all variable patterns with balanced braces
        variables_found = self._find_variables_in_template(template)

        # If it's a single variable, return the value with original type
        if (
            len(variables_found) == 1
            and variables_found[0]["start"] == 0
            and variables_found[0]["end"] == len(template)
        ):
            var_path = variables_found[0]["content"]

            value = self._resolve_variable_with_default(var_path, variables, context)

            # Check for recursion only if the value contains the same variable
            if isinstance(value, str) and "{{" in value:
                # Check for circular reference
                if var_path in visited_vars:
                    # If the resolved value is exactly the same as the template, it's undefined, not circular
                    if value == template:
                        # But if the variable actually exists, then it's a true self-reference
                        if var_path in variables:
                            from ..exceptions import VariableNotFoundError

                            raise VariableNotFoundError(
                                var_path,
                                f"Circular reference detected: variable '{var_path}' references itself",
                                str(context.file_path),
                            )
                        else:
                            return template
                    else:
                        # True circular reference
                        from ..exceptions import VariableNotFoundError

                        raise VariableNotFoundError(
                            var_path,
                            "Circular reference detected in variable expansion",
                            str(context.file_path),
                        )

                # Check for indirect circular reference (e.g., var1 -> result1 -> var2 -> result2 -> var1)
                # If this variable references a data field that contains variables, check for cycles
                variables_in_value = self._find_variables_in_template(value)
                for var_ref in variables_in_value:
                    ref_var_path = var_ref["content"]
                    if ref_var_path in visited_vars:
                        # Indirect circular reference detected
                        from ..exceptions import VariableNotFoundError

                        raise VariableNotFoundError(
                            var_path,
                            f"Circular reference detected: {var_path} -> {ref_var_path} creates a cycle",
                            str(context.file_path),
                        )

                new_visited = visited_vars | {var_path}
                return self._expand_string_template(
                    value, variables, context, new_visited, depth + 1
                )
            return value

        # Replace all variables in the template
        result = template
        # Process in reverse order to maintain positions
        for var_info in reversed(variables_found):
            var_path = var_info["content"]

            # Check for recursive expansion
            if var_path in visited_vars:
                raise RecursionLimitExceededError(
                    self.config.max_recursion_depth,
                    f"variable expansion for '{var_path}'",
                    str(context.file_path),
                )

            # Resolve variable value
            try:
                value = self._resolve_variable_with_default(
                    var_path, variables, context
                )

                # If value contains variables, expand them too
                if isinstance(value, str) and "{{" in value:
                    new_visited = visited_vars | {var_path}
                    value = self._expand_string_template(
                        value, variables, context, new_visited, depth + 1
                    )

                replacement = str(value) if value is not None else ""
                result = (
                    result[: var_info["start"]]
                    + replacement
                    + result[var_info["end"] :]
                )

            except VariableExpansionError:
                raise
            except Exception as e:
                raise VariableExpansionError(var_path, str(e), str(context.file_path))

        return result

    def _find_variables_in_template(self, template: str) -> list:
        """Find all {{variable}} patterns in template with balanced braces."""
        variables = []
        i = 0

        while i < len(template) - 1:
            # Look for opening {{
            if template[i : i + 2] == "{{":
                start_pos = i
                i += 2  # Skip {{
                brace_depth = 1
                content_start = i

                # Find the matching }}
                while i < len(template) - 1 and brace_depth > 0:
                    if template[i : i + 2] == "{{":
                        brace_depth += 1
                        i += 2
                    elif template[i : i + 2] == "}}":
                        brace_depth -= 1
                        if brace_depth == 0:
                            content_end = i
                            end_pos = i + 2

                            variables.append(
                                {
                                    "start": start_pos,
                                    "end": end_pos,
                                    "content": template[
                                        content_start:content_end
                                    ].strip(),
                                }
                            )
                            i += 2
                            break
                        else:
                            i += 2
                    else:
                        i += 1

                if brace_depth > 0:
                    # Unmatched braces, treat as regular text
                    i = start_pos + 1
            else:
                i += 1

        return variables

    def _resolve_variable(
        self, var_path: str, variables: Dict[str, Any], context
    ) -> Any:
        """Resolve a variable path like 'var' or 'nested.var'."""
        # Check cache first
        cache_key = (var_path, id(variables))
        if cache_key in self.expansion_cache:
            return self.expansion_cache[cache_key]

        # First, check if the exact variable name exists (handles dots in variable names)
        if var_path in variables:
            self.expansion_cache[cache_key] = variables[var_path]
            return variables[var_path]

        # If not found as exact match, try as nested path
        path_parts = var_path.split(".")
        current = variables

        for i, part in enumerate(path_parts):
            # Handle dictionary access
            if isinstance(current, dict):
                if part not in current:
                    # Variable not found
                    if self.config.strict_variables:
                        from ..exceptions import VariableNotFoundError

                        raise VariableNotFoundError(
                            var_path,
                            f"Variable '{'.'.join(path_parts[:i+1])}' not found",
                            str(context.file_path),
                        )
                    else:
                        # Return placeholder or empty string in non-strict mode
                        result = (
                            f"{{{{{var_path}}}}}"
                            if self.config.keep_undefined_variables
                            else ""
                        )
                        self.expansion_cache[cache_key] = result
                        return result
                current = current[part]
            # Handle array/list access
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(current):
                        # Index out of bounds
                        if self.config.strict_variables:
                            raise VariableNotFoundError(
                                var_path,
                                f"Array index '{index}' out of bounds for '{'.'.join(path_parts[:i])}'",
                                str(context.file_path),
                            )
                        else:
                            result = (
                                f"{{{{{var_path}}}}}"
                                if self.config.keep_undefined_variables
                                else ""
                            )
                            self.expansion_cache[cache_key] = result
                            return result
                    current = current[index]
                except ValueError:
                    # Not a numeric index
                    if self.config.strict_variables:
                        raise VariableNotFoundError(
                            var_path,
                            f"Invalid array index '{part}' for '{'.'.join(path_parts[:i])}'",
                            str(context.file_path),
                        )
                    else:
                        result = (
                            f"{{{{{var_path}}}}}"
                            if self.config.keep_undefined_variables
                            else ""
                        )
                        self.expansion_cache[cache_key] = result
                        return result
            else:
                # Neither dict nor list - can't access nested property
                # This is always an error regardless of strict mode
                from ..exceptions import VariableNotFoundError

                raise VariableNotFoundError(
                    var_path,
                    f"Cannot access property '{part}' on non-object/non-array "
                    f"value at '{'.'.join(path_parts[:i])}'",
                    str(context.file_path),
                )

        # Cache and return the resolved value
        self.expansion_cache[cache_key] = current
        return current

    def _resolve_variable_strict(
        self, var_path: str, variables: Dict[str, Any], context
    ) -> Any:
        """Resolve a variable path strictly - always raises exception if not found."""
        # First, check if the exact variable name exists (handles dots in variable names)
        if var_path in variables:
            return variables[var_path]

        # If not found as exact match, try as nested path
        path_parts = var_path.split(".")
        current = variables

        for i, part in enumerate(path_parts):
            # Handle dictionary access
            if isinstance(current, dict):
                if part not in current:
                    # Variable not found - always raise exception
                    raise VariableNotFoundError(
                        var_path,
                        f"Variable '{'.'.join(path_parts[:i+1])}' not found",
                        str(context.file_path),
                    )
                current = current[part]
            # Handle array/list access
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(current):
                        # Index out of bounds - always raise exception
                        raise VariableNotFoundError(
                            var_path,
                            f"Array index '{index}' out of bounds for '{'.'.join(path_parts[:i])}'",
                            str(context.file_path),
                        )
                    current = current[index]
                except ValueError:
                    # Not a numeric index - always raise exception
                    raise VariableNotFoundError(
                        var_path,
                        f"Invalid array index '{part}' for '{'.'.join(path_parts[:i])}'",
                        str(context.file_path),
                    )
            else:
                # Neither dict nor list - can't access nested property - always raise exception
                raise VariableNotFoundError(
                    var_path,
                    f"Cannot access property '{part}' on non-object/non-array "
                    f"value at '{'.'.join(path_parts[:i])}'",
                    str(context.file_path),
                )

        return current

    def _resolve_variable_with_default(
        self, var_path: str, variables: Dict[str, Any], context
    ) -> Any:
        """Resolve a variable with optional default syntax: 'var|default'."""
        # Check if there's a default value specified
        if "|" in var_path:
            # Find the first pipe that's not inside quotes or braces
            pipe_pos = self._find_default_separator(var_path)
            if pipe_pos == -1:
                # No valid separator found, treat as regular variable
                return self._resolve_variable(var_path, variables, context)

            var_name = var_path[:pipe_pos].strip()
            default_value = var_path[pipe_pos + 1 :].strip()

            # Parse the default value
            default_parsed = self._parse_default_value(default_value)

            # Always try to resolve, but return default if not found
            try:
                return self._resolve_variable_strict(var_name, variables, context)
            except VariableNotFoundError:
                # Variable not found, process the default value for variables
                if isinstance(default_parsed, str) and "{{" in default_parsed:
                    # Default contains variables, expand them
                    return self._expand_string_template(
                        default_parsed, variables, context, set(), 0
                    )
                return default_parsed
        else:
            # No default specified, use the regular resolution logic
            return self._resolve_variable(var_path, variables, context)

    def _find_default_separator(self, var_path: str) -> int:
        """Find the pipe separator that's not inside quotes or braces."""
        brace_depth = 0
        quote_char = None
        escaped = False
        i = 0

        while i < len(var_path):
            char = var_path[i]

            if escaped:
                escaped = False
                i += 1
                continue

            if char == "\\":
                escaped = True
                i += 1
                continue

            if quote_char:
                # Inside quotes
                if char == quote_char:
                    quote_char = None
            else:
                # Outside quotes
                if char in ["'", '"']:
                    quote_char = char
                elif char == "{" and i + 1 < len(var_path) and var_path[i + 1] == "{":
                    brace_depth += 1
                    i += 1  # Skip the next brace too
                elif char == "}" and i + 1 < len(var_path) and var_path[i + 1] == "}":
                    brace_depth -= 1
                    i += 1  # Skip the next brace too
                elif char == "|" and brace_depth == 0:
                    return i

            i += 1

        return -1

    def _parse_default_value(self, default_str: str) -> Any:
        """Parse a default value string into appropriate type."""
        default_str = default_str.strip()

        # Handle quoted strings
        if (default_str.startswith('"') and default_str.endswith('"')) or (
            default_str.startswith("'") and default_str.endswith("'")
        ):
            return default_str[1:-1]  # Remove quotes

        # Handle special values
        if default_str.lower() == "null":
            return None
        elif default_str.lower() == "true":
            return True
        elif default_str.lower() == "false":
            return False

        # Try to parse as number
        try:
            if "." in default_str:
                return float(default_str)
            else:
                return int(default_str)
        except ValueError:
            pass

        # Return as string if nothing else matches
        return default_str

    def clear_cache(self):
        """Clear the variable expansion cache."""
        self.expansion_cache.clear()

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source dict into target dict using unified merger."""
        merger = DeepMerger(
            list_strategy=MergeStrategy.REPLACE,
            conflict_strategy=MergeStrategy.REPLACE,  # Variables allow overrides
        )
        merger.merge(target, source)

    def _add_data_context(
        self, variables: Dict[str, Any], data: Dict[str, Any]
    ) -> None:
        """Add flattened data context to variables for cross-references, preserving original variables."""
        # Create a copy to avoid modifying the original
        flattened_data = {}
        self._flatten_data_for_access(flattened_data, data)

        # Only add data that doesn't conflict with existing variables
        for key, value in flattened_data.items():
            if key not in variables and not key.startswith("__"):
                variables[key] = value

    def _flatten_data_for_access(
        self, target: Dict[str, Any], data: Dict[str, Any], prefix: str = ""
    ) -> None:
        """Recursively flatten data structure for easier variable access."""
        for key, value in data.items():
            if key.startswith("__"):  # Skip metadata
                continue

            full_key = f"{prefix}.{key}" if prefix else key

            # Add the full path
            if full_key not in target:
                target[full_key] = value

            # Add intermediate paths for cross-references (e.g., services.database.host -> database.host)
            if "." in full_key:
                # Split the full key and create intermediate aliases
                parts = full_key.split(".")
                for i in range(1, len(parts)):
                    # Create aliases like database.host from services.database.host
                    intermediate_key = ".".join(parts[i:])
                    if intermediate_key not in target:
                        target[intermediate_key] = value

            # Also add without prefix for direct access (but don't override existing)
            if key not in target and not prefix:
                target[key] = value

            # If it's a dict, recurse for nested access
            if isinstance(value, dict):
                self._flatten_data_for_access(target, value, full_key)

    def _extract_safe_data_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data fields that don't contain variables to avoid circular dependencies."""
        safe_data = {}
        for key, value in data.items():
            # Skip metadata fields
            if key.startswith("__"):
                continue
            # Only include fields that don't contain variable templates
            if not self._contains_variables(value):
                safe_data[key] = value
        return safe_data

    def _contains_variables(self, value: Any) -> bool:
        """Check if a value contains variable templates that could cause circular dependencies."""
        if isinstance(value, str):
            return "{{" in value
        elif isinstance(value, dict):
            return any(self._contains_variables(v) for v in value.values())
        elif isinstance(value, list):
            return any(self._contains_variables(item) for item in value)
        else:
            return False

    def _create_flattened_aliases(self, merged_vars: Dict[str, Any]) -> None:
        """Create flattened aliases for nested objects to enable direct reference."""
        # Store original variables to protect them
        original_vars = {
            k: v
            for k, v in merged_vars.items()
            if not k.startswith("__") and not isinstance(v, dict)
        }

        # For each top-level key, if it contains nested dictionaries,
        # make those nested objects available directly at the top level
        for top_key, top_value in list(merged_vars.items()):
            if isinstance(top_value, dict):
                for nested_key, nested_value in top_value.items():
                    # Only add if it doesn't exist and doesn't conflict with original vars
                    if nested_key not in merged_vars and not nested_key.startswith(
                        "__"
                    ):
                        # Don't overwrite scalar variables with dict values or vice versa
                        if nested_key not in original_vars:
                            merged_vars[nested_key] = nested_value
