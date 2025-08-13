"""
Enhanced error context system for SmartYAML
"""

from pathlib import Path
from typing import Any, Dict, Optional, Set

import yaml


class ErrorContextBuilder:
    """Builds consistent error context across all constructors."""

    @staticmethod
    def build_constructor_context(
        directive_name: str,
        loader,
        params: Dict[str, Any],
        node: Optional[yaml.Node] = None,
    ) -> Dict[str, Any]:
        """
        Build comprehensive error context for constructor errors.

        Args:
            directive_name: The SmartYAML directive name
            loader: The YAML loader instance
            params: The constructor parameters
            node: The YAML node (optional)

        Returns:
            Dictionary containing relevant error context
        """
        context = {
            "directive": directive_name,
        }

        # Add loader context
        if hasattr(loader, "base_path") and loader.base_path:
            context["base_path"] = str(loader.base_path)

        if hasattr(loader, "template_path") and loader.template_path:
            context["template_path"] = str(loader.template_path)

        # Add location information if available
        if node and hasattr(node, "start_mark") and node.start_mark:
            mark = node.start_mark
            context.update({"line": mark.line + 1, "column": mark.column + 1})

            # Add source name if available
            if hasattr(mark, "name") and mark.name:
                context["source"] = mark.name

            # Add YAML snippet context for better debugging
            yaml_snippet = ErrorContextBuilder._get_yaml_snippet(mark, context_lines=2)
            if yaml_snippet:
                context["yaml_snippet"] = yaml_snippet

        # Add relevant parameter information (avoid sensitive data)
        safe_params = [
            "filename",
            "var_name",
            "condition",
            "template_name",
            "operation",
        ]
        for param_name in safe_params:
            if param_name in params and params[param_name] is not None:
                context[param_name] = str(params[param_name])

        # Add import stack information if available
        if hasattr(loader, "import_stack"):
            import_stack = getattr(loader, "import_stack", set())
            if import_stack:
                context["import_depth"] = len(import_stack)
                # Show last few imports in chain for brevity
                chain_paths = [str(p) for p in list(import_stack)[-3:]]
                context["import_chain"] = " -> ".join(chain_paths)

        # Add recursion context if available
        if hasattr(loader, "max_recursion_depth"):
            context["max_recursion_depth"] = loader.max_recursion_depth

        return context

    @staticmethod
    def _get_yaml_snippet(mark: yaml.Mark, context_lines: int = 2) -> Optional[str]:
        """
        Extract YAML snippet around the error location for debugging.

        Args:
            mark: YAML mark with line/column information
            context_lines: Number of lines to show before/after error line

        Returns:
            Formatted YAML snippet or None if unavailable
        """
        if not mark or not hasattr(mark, "get_snippet"):
            return None

        try:
            # Try to get the buffer content from the mark
            if hasattr(mark, "buffer") and mark.buffer:
                lines = mark.buffer.splitlines()
                error_line = mark.line

                # Calculate snippet range
                start_line = max(0, error_line - context_lines)
                end_line = min(len(lines), error_line + context_lines + 1)

                # Build snippet with line numbers
                snippet_lines = []
                for i in range(start_line, end_line):
                    line_num = i + 1
                    line_content = lines[i] if i < len(lines) else ""

                    # Highlight the error line
                    marker = ">>> " if i == error_line else "    "
                    snippet_lines.append(f"{marker}{line_num:3d} | {line_content}")

                return "\n".join(snippet_lines)

        except (AttributeError, IndexError, TypeError):
            pass

        # Fallback: try to read source file if available
        try:
            if hasattr(mark, "name") and mark.name and mark.name != "<unicode string>":
                source_path = Path(mark.name)
                if source_path.exists() and source_path.is_file():
                    with open(source_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    error_line = mark.line
                    start_line = max(0, error_line - context_lines)
                    end_line = min(len(lines), error_line + context_lines + 1)

                    snippet_lines = []
                    for i in range(start_line, end_line):
                        line_num = i + 1
                        line_content = lines[i].rstrip() if i < len(lines) else ""

                        marker = ">>> " if i == error_line else "    "
                        snippet_lines.append(f"{marker}{line_num:3d} | {line_content}")

                    return "\n".join(snippet_lines)

        except (OSError, UnicodeDecodeError, IndexError):
            pass

        return None

    @staticmethod
    def format_context_string(
        context: Dict[str, Any], exclude_keys: Set[str] = None
    ) -> str:
        """
        Format context dictionary into a readable string.

        Args:
            context: The context dictionary
            exclude_keys: Keys to exclude from formatting

        Returns:
            Formatted context string
        """
        if not context:
            return ""

        exclude_keys = exclude_keys or {"directive"}  # Usually in main error message

        # Group related context
        location_info = []
        file_info = []
        import_info = []
        other_info = []
        yaml_snippet = None

        for key, value in context.items():
            if key in exclude_keys or value is None:
                continue

            if key == "yaml_snippet":
                yaml_snippet = value  # Handle separately for better formatting
            elif key in ["line", "column", "source"]:
                if key == "line" and "line" not in [
                    item.split("=")[0] for item in location_info
                ]:
                    line = context.get("line", "?")
                    col = context.get("column", "?")
                    location_info.append(f"line {line}:{col}")
                elif key == "source":
                    location_info.append(f"in {value}")
            elif key in ["filename", "base_path", "template_path"]:
                file_info.append(f"{key}={value}")
            elif key in ["import_depth", "import_chain", "max_recursion_depth"]:
                import_info.append(f"{key}={value}")
            else:
                other_info.append(f"{key}={value}")

        # Combine context parts efficiently
        from smartyaml.performance_optimizations import string_optimizations

        all_parts = []
        for part_list in [location_info, file_info, other_info, import_info]:
            all_parts.extend(part_list)

        context_str = string_optimizations.join_with_separator(all_parts, ", ")

        # Add YAML snippet on new line if available
        if yaml_snippet:
            if context_str:
                context_str += f"\nYAML context:\n{yaml_snippet}"
            else:
                context_str = f"YAML context:\n{yaml_snippet}"

        return context_str


def enhance_error_with_context(error: Exception, context: Dict[str, Any]) -> Exception:
    """
    Enhanced version of add_context_to_error with better formatting.

    Args:
        error: The exception to enhance
        context: The context dictionary

    Returns:
        Enhanced exception with context information
    """
    # Don't enhance errors that are already enhanced
    if hasattr(error, "_context_enhanced"):
        return error

    # Format context string
    context_str = ErrorContextBuilder.format_context_string(context)

    if context_str:
        enhanced_message = f"{str(error)} ({context_str})"

        # Create new exception of same type with enhanced message
        try:
            new_error = type(error)(enhanced_message)
            new_error.__cause__ = error
            new_error._context_enhanced = True

            # Copy over any custom attributes
            for attr_name in dir(error):
                if not attr_name.startswith("_") and hasattr(error, attr_name):
                    try:
                        attr_value = getattr(error, attr_name)
                        if not callable(attr_value):
                            setattr(new_error, attr_name, attr_value)
                    except (AttributeError, TypeError):
                        pass  # Skip attributes that can't be copied

            return new_error
        except TypeError:
            # If we can't create a new exception of the same type, return original
            return error

    return error
