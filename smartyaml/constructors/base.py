"""
Base constructor class implementing template method pattern for SmartYAML constructors
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from ..error_context import ErrorContextBuilder, enhance_error_with_context
from ..exceptions import ConstructorError
from ..processing import ParameterExtractor, ParameterValidator, TypeConverter


class BaseConstructor(ABC):
    """
    Abstract base class for SmartYAML constructors implementing template method pattern.

    This class provides a consistent workflow for all constructors:
    1. Extract and validate parameters
    2. Apply security checks
    3. Execute constructor logic
    4. Handle errors with context
    """

    def __init__(
        self,
        directive_name: str,
        parameter_extractor: Optional[ParameterExtractor] = None,
        parameter_validator: Optional[ParameterValidator] = None,
        type_converter: Optional[TypeConverter] = None,
    ) -> None:
        """
        Initialize base constructor with optional processing components.

        Args:
            directive_name: The SmartYAML directive name (e.g., '!import')
            parameter_extractor: Optional parameter extraction component
            parameter_validator: Optional parameter validation component
            type_converter: Optional type conversion component
        """
        self.directive_name = directive_name
        self.parameter_extractor = parameter_extractor
        self.parameter_validator = parameter_validator
        self.type_converter = type_converter

    def __call__(self, loader: yaml.SafeLoader, node: yaml.Node) -> Any:
        """
        Template method that defines the standard constructor workflow.

        Args:
            loader: YAML loader instance
            node: YAML node containing the directive

        Returns:
            Result from executing the constructor logic

        Raises:
            ConstructorError: If constructor execution fails
        """
        try:
            # Step 1: Extract parameters from YAML node
            if self.parameter_extractor:
                params = self.parameter_extractor.extract_parameters(
                    loader, node, self.directive_name
                )
                # Also run custom extraction if needed
                custom_params = self.extract_parameters(loader, node)
                params.update(custom_params)
            else:
                params = self.extract_parameters(loader, node)

            # Step 2: Validate parameters
            if self.parameter_validator:
                self.parameter_validator.validate(params, self.directive_name)
            self.validate_parameters(params)

            # Step 3: Apply type conversions
            if self.type_converter and hasattr(self, "TYPE_SPECS"):
                params = self.type_converter.convert_parameters(
                    params, self.TYPE_SPECS, self.directive_name
                )

            # Step 4: Apply security checks
            self.apply_security_checks(loader, params)

            # Step 4: Execute the main constructor logic
            result = self.execute(loader, params)

            # Step 5: Post-process result if needed
            return self.post_process(result, params)

        except Exception as e:
            # Step 6: Handle errors with context
            context = ErrorContextBuilder.build_constructor_context(
                self.directive_name,
                loader,
                params if "params" in locals() else {},
                node,
            )
            raise enhance_error_with_context(e, context) from e

    @abstractmethod
    def extract_parameters(
        self, loader: yaml.SafeLoader, node: yaml.Node
    ) -> Dict[str, Any]:
        """
        Extract parameters from the YAML node.

        Args:
            loader: YAML loader instance
            node: YAML node containing directive parameters

        Returns:
            Dictionary of extracted parameters

        Raises:
            ConstructorError: If parameter extraction fails
        """

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """
        Validate extracted parameters.

        Args:
            params: Dictionary of parameters to validate

        Raises:
            ConstructorError: If parameters are invalid
        """
        # Default implementation - can be overridden

    def apply_security_checks(self, loader, params: Dict[str, Any]) -> None:
        """
        Apply security checks before execution.

        Args:
            loader: YAML loader instance
            params: Dictionary of parameters

        Raises:
            SecurityError: If security checks fail
        """
        # Default implementation - can be overridden

    @abstractmethod
    def execute(self, loader: yaml.SafeLoader, params: Dict[str, Any]) -> Any:
        """
        Execute the main constructor logic.

        Args:
            loader: YAML loader instance
            params: Dictionary of validated parameters

        Returns:
            The constructed value
        """

    def post_process(self, result: Any, params: Dict[str, Any]) -> Any:
        """
        Post-process the result if needed.

        Args:
            result: The result from execute()
            params: Dictionary of parameters

        Returns:
            The final processed result
        """
        # Default implementation - return as-is
        return result

    def build_error_context(self, loader, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build error context information.

        Args:
            loader: YAML loader instance
            params: Dictionary of parameters

        Returns:
            Dictionary of context information
        """
        context = {
            "directive": self.directive_name,
            "base_path": getattr(loader, "base_path", None),
        }

        # Add relevant parameters to context
        if "filename" in params:
            context["filename"] = params["filename"]
        if "condition" in params:
            context["condition"] = params["condition"]
        if "var_name" in params:
            context["var_name"] = params["var_name"]

        return context


class FileBasedConstructor(BaseConstructor):
    """
    Base class for constructors that work with files.
    Provides common file handling and security checks.
    """

    def apply_security_checks(self, loader, params: Dict[str, Any]) -> None:
        """Apply file-based security checks."""
        from ..utils.path_utils import resolve_path
        from ..utils.validation_utils import (
            check_recursion_limit,
            validate_file_before_read,
        )

        if "filename" not in params:
            return

        base_path = getattr(loader, "base_path", Path.cwd())
        import_stack = getattr(loader, "import_stack", set())
        max_recursion_depth = getattr(loader, "max_recursion_depth", None)

        file_path = resolve_path(params["filename"], base_path)

        # Pre-flight file validation
        validate_file_before_read(file_path, self.directive_name)

        check_recursion_limit(import_stack, file_path, max_recursion_depth)

        # Store resolved path for use in execute()
        params["resolved_file_path"] = file_path

    def get_loader_context(self, loader) -> Dict[str, Any]:
        """Get loader context information."""
        return {
            "base_path": getattr(loader, "base_path", Path.cwd()),
            "template_path": getattr(loader, "template_path", None),
            "import_stack": getattr(loader, "import_stack", set()),
            "max_file_size": getattr(loader, "max_file_size", None),
            "max_recursion_depth": getattr(loader, "max_recursion_depth", None),
        }


class EnvironmentBasedConstructor(BaseConstructor):
    """
    Base class for constructors that work with environment variables.
    """

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate environment variable parameters."""
        if "var_name" in params:
            var_name = params["var_name"]
            if not var_name or not isinstance(var_name, str):
                raise ConstructorError(
                    f"{self.directive_name} requires a non-empty variable name"
                )


class ConditionalConstructor(FileBasedConstructor):
    """
    Base class for conditional constructors that check environment variables.
    """

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate conditional parameters."""
        super().validate_parameters(params)

        if "condition" not in params or "filename" not in params:
            raise ConstructorError(
                f"{self.directive_name} requires both condition and filename"
            )

        condition = params["condition"]
        filename = params["filename"]

        if not condition or not isinstance(condition, str):
            raise ConstructorError(
                f"{self.directive_name} condition must be a non-empty string"
            )
        if not filename or not isinstance(filename, str):
            raise ConstructorError(
                f"{self.directive_name} filename must be a non-empty string"
            )

    def should_include(self, condition: str) -> bool:
        """Check if condition is met for inclusion."""
        from ..utils.validation_utils import get_env_var, is_truthy

        env_value = get_env_var(condition)
        return is_truthy(env_value)
