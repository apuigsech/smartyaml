"""
Base classes for SmartYAML directive handlers.

Provides common interfaces and functionality for all directive handlers,
reducing duplication and ensuring consistent behavior.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from ..config import SmartYAMLConfig
from ..errors import ErrorHelper


class DirectiveContext:
    """Context object passed to directive handlers with processing state."""

    def __init__(
        self,
        config: SmartYAMLConfig,
        file_path: Optional[str] = None,
        base_path: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        recursion_depth: int = 0,
        loaded_files: Optional[set] = None,
    ):
        self.config = config
        self.file_path = file_path
        self.base_path = base_path
        self.variables = variables or {}
        self.recursion_depth = recursion_depth
        self.loaded_files = loaded_files or set()

        # Additional tracking attributes for compatibility
        self._total_file_size = 0
        self._stage_times = {}
        self.metadata = {}  # For template metadata compatibility

    def check_recursion(self, operation: str) -> None:
        """Check if recursion limit has been exceeded."""
        if self.recursion_depth >= self.config.max_recursion_depth:
            from ..exceptions import RecursionLimitExceededError

            raise RecursionLimitExceededError(
                self.config.max_recursion_depth, operation, self.file_path or "unknown"
            )

    def check_timeout(self) -> None:
        """Check if processing timeout has been exceeded."""
        # For now, this is a no-op since timeout checking would require
        # more complex time tracking. Can be implemented later if needed.
        pass

    def track_file_size(self, file_path) -> int:
        """Track file size for memory limits."""
        from pathlib import Path

        size = Path(file_path).stat().st_size
        self._total_file_size += size

        # Check file size limits if configured
        if hasattr(self.config, "max_file_size") and self.config.max_file_size:
            if size > self.config.max_file_size:
                from ..exceptions import FileSizeExceededError

                raise FileSizeExceededError(
                    size, self.config.max_file_size, str(file_path)
                )

        return size

    def track_stage(self, stage_name: str) -> None:
        """Track processing stage completion."""
        import time

        self._stage_times[stage_name] = time.time()

    def decrease_recursion(self) -> None:
        """Decrease recursion depth counter."""
        self.recursion_depth = max(0, self.recursion_depth - 1)


class BaseDirectiveHandler(ABC):
    """
    Abstract base class for all SmartYAML directive handlers.

    Provides common functionality and enforces consistent interface
    for all directive implementations.
    """

    def __init__(self, config: SmartYAMLConfig):
        self.config = config

    @property
    @abstractmethod
    def directive_name(self) -> str:
        """Return the name of the directive this handler processes."""
        pass

    @abstractmethod
    def handle(self, value: Any, context: DirectiveContext) -> Any:
        """
        Process the directive with the given value and context.

        Args:
            value: The directive's argument value
            context: Processing context with state and configuration

        Returns:
            Processed result

        Raises:
            DirectiveSyntaxError: If directive syntax is invalid
            DirectiveProcessingError: If processing fails
        """
        pass

    def validate_arguments(self, value: Any, context: DirectiveContext) -> None:
        """
        Validate directive arguments before processing.

        Override this method to add directive-specific validation.
        Base implementation does nothing.

        Args:
            value: The directive's argument value
            context: Processing context

        Raises:
            DirectiveSyntaxError: If validation fails
        """
        pass

    def get_error_builder(self, context: DirectiveContext) -> ErrorHelper:
        """Get error helper for consistent error handling."""
        return ErrorHelper.directive_error_builder(self.directive_name, context)

    def process_recursive(self, value: Any, context: DirectiveContext) -> Any:
        """
        Placeholder for recursive processing - will be injected by processor.

        This method will be set by the DirectiveProcessor to enable
        recursive processing of nested structures.
        """
        raise NotImplementedError("Recursive processing not available")

    def expand_variables(self, value: Any, context: DirectiveContext) -> Any:
        """
        Placeholder for variable expansion - will be injected by processor.

        This method will be set by the DirectiveProcessor to enable
        variable expansion in directive arguments.
        """
        raise NotImplementedError("Variable expansion not available")


class ConditionalDirectiveHandler(BaseDirectiveHandler):
    """
    Base class for conditional directive handlers (if, switch).

    Provides common functionality for condition evaluation and
    argument parsing for conditional directives.
    """

    def evaluate_condition(self, condition_var: str, context: DirectiveContext) -> bool:
        """
        Evaluate a condition variable to boolean.

        Args:
            condition_var: Environment variable name or value to evaluate
            context: Processing context

        Returns:
            Boolean result of condition evaluation
        """
        if condition_var in context.variables:
            value = context.variables[condition_var]
        else:
            # Try environment variable
            import os

            value = os.environ.get(condition_var)

        if value is None:
            return False

        # Convert to boolean using standardized conversion utility
        from ..utils.conversion import convert_to_bool

        return convert_to_bool(
            value, f"condition variable '{condition_var}'", strict=False
        )

    def parse_array_or_object_syntax(self, value: Any) -> Dict[str, Any]:
        """
        Parse directive arguments that support both array and object syntax.

        Args:
            value: Directive arguments (list or dict)

        Returns:
            Normalized dictionary with parsed arguments

        Raises:
            DirectiveSyntaxError: If syntax is invalid
        """
        if isinstance(value, list):
            return self._parse_array_syntax(value)
        elif isinstance(value, dict):
            return self._parse_object_syntax(value)
        else:
            raise ValueError(f"Invalid argument type for {self.directive_name}")

    @abstractmethod
    def _parse_array_syntax(self, value: List[Any]) -> Dict[str, Any]:
        """Parse array-style arguments."""
        pass

    @abstractmethod
    def _parse_object_syntax(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Parse object-style arguments."""
        pass


class FileDirectiveHandler(BaseDirectiveHandler):
    """
    Base class for file-related directive handlers (include, template).

    Provides common functionality for file operations, path resolution,
    and security checks.
    """

    def resolve_file_path(self, file_path: str, context: DirectiveContext) -> str:
        """
        Resolve a relative file path to absolute path.

        Args:
            file_path: Relative or absolute file path
            context: Processing context with base path

        Returns:
            Resolved absolute file path
        """
        from pathlib import Path

        path = Path(file_path)
        if path.is_absolute():
            return str(path)

        # Resolve relative to base path
        if context.base_path:
            base = Path(context.base_path)
            resolved = (base / path).resolve()
            return str(resolved)

        # Fallback to current working directory
        return str(Path.cwd() / path)

    def check_security_constraints(
        self, file_path: str, context: DirectiveContext
    ) -> None:
        """
        Check if file access is allowed by security configuration.

        Args:
            file_path: File path to check
            context: Processing context with security config

        Raises:
            SecurityViolationError: If access is not allowed
        """
        # Check sandbox mode
        if self.config.security.sandbox_mode:
            from ..exceptions import SecurityViolationError

            raise SecurityViolationError(
                "File access blocked in sandbox mode",
                context.file_path or "unknown",
                "sandbox_file_access",
            )

        # Add other security checks as needed
        # - Path traversal protection
        # - File size limits
        # - Allowed directories

    def load_file_content(self, file_path: str, context: DirectiveContext) -> str:
        """
        Load content from a file with security checks.

        Args:
            file_path: Path to file to load
            context: Processing context

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist
            SecurityViolationError: If access denied
        """
        from pathlib import Path

        resolved_path = self.resolve_file_path(file_path, context)
        self.check_security_constraints(resolved_path, context)

        path_obj = Path(resolved_path)
        if not path_obj.exists():
            from ..exceptions import FileNotFoundError

            raise FileNotFoundError(
                resolved_path,
                context.base_path or "unknown",
                self.directive_name,
            )

        try:
            return path_obj.read_text(encoding="utf-8")
        except Exception as e:
            from ..exceptions import DirectiveProcessingError

            raise DirectiveProcessingError(
                f"Failed to read file {resolved_path}: {e}",
                context.file_path or "unknown",
                self.directive_name,
            )

    def _evaluate_condition(
        self, condition_var: str, context: "DirectiveContext"
    ) -> bool:
        """
        Evaluate a condition variable to boolean (used by file handlers with conditional logic).

        Args:
            condition_var: Environment variable name or value to evaluate
            context: Processing context

        Returns:
            Boolean result of condition evaluation
        """
        import os

        if condition_var in context.variables:
            value = context.variables[condition_var]
        else:
            # Try environment variable
            value = os.environ.get(condition_var)

        if value is None:
            return False

        # Convert to boolean using standardized conversion utility
        from ..utils.conversion import convert_to_bool

        return convert_to_bool(
            value, f"condition variable '{condition_var}'", strict=False
        )


class DataDirectiveHandler(BaseDirectiveHandler):
    """
    Base class for data manipulation directive handlers (merge, concat).

    Provides common functionality for data validation and processing.
    """

    def validate_list_argument(
        self, value: Any, context: DirectiveContext
    ) -> List[Any]:
        """
        Validate that argument is a list and return it.

        Args:
            value: Argument to validate
            context: Processing context

        Returns:
            Validated list

        Raises:
            DirectiveSyntaxError: If not a list
        """
        if not isinstance(value, list):
            error_builder = self.get_error_builder(context)
            error_builder.raise_directive_syntax_error(
                self.directive_name,
                "list",
                value,
                f"!{self.directive_name} directive requires a list argument",
            )
        return value

    def ensure_compatible_types(
        self, items: List[Any], expected_type: Type, context: DirectiveContext
    ) -> None:
        """
        Ensure all items in list are of compatible type.

        Args:
            items: List of items to check
            expected_type: Expected type for all items
            context: Processing context

        Raises:
            DirectiveSyntaxError: If types are incompatible
        """
        for i, item in enumerate(items):
            if not isinstance(item, expected_type):
                error_builder = self.get_error_builder(context)
                error_builder.raise_directive_syntax_error(
                    self.directive_name,
                    f"list of {expected_type.__name__}",
                    type(item).__name__,
                    f"!{self.directive_name} item {i} has incompatible type",
                )


class EnvironmentDirectiveHandler(BaseDirectiveHandler):
    """
    Base class for environment variable directive handlers (env, env_int, etc.).

    Provides common functionality for environment variable access and type conversion.
    """

    def get_env_value(
        self, var_name: str, default: Any, context: DirectiveContext
    ) -> str:
        """
        Get environment variable value with security checks.

        Args:
            var_name: Environment variable name
            default: Default value if not found
            context: Processing context

        Returns:
            Environment variable value or default

        Raises:
            SecurityViolationError: If variable access is forbidden
        """
        # Use centralized security checking
        from ..utils.security import create_security_checker

        security_checker = create_security_checker(self.config, context.file_path)
        security_checker.check_env_var_access(var_name, is_secret=False)

        import os

        return os.environ.get(var_name, default)

    def convert_to_type(
        self, value: str, target_type: Type, var_name: str, context: DirectiveContext
    ) -> Any:
        """
        Convert string value to target type with error handling.

        Args:
            value: String value to convert
            target_type: Target type for conversion
            var_name: Variable name for error reporting
            context: Processing context

        Returns:
            Converted value

        Raises:
            DirectiveProcessingError: If conversion fails
        """
        try:
            if target_type == int:
                return int(value)
            elif target_type == float:
                return float(value)
            elif target_type == bool:
                # Use standardized boolean conversion utility
                from ..utils.conversion import convert_to_bool

                return convert_to_bool(value, f"environment variable '{var_name}'")
            else:
                return value
        except (ValueError, TypeError) as e:
            from ..exceptions import DirectiveProcessingError

            raise DirectiveProcessingError(
                f"Cannot convert environment variable '{var_name}' value "
                f"'{value}' to {target_type.__name__}: {e}",
                context.file_path or "unknown",
                self.directive_name,
            )
