"""
Environment variable constructor for SmartYAML
"""

from typing import Any, Dict

import yaml

from ..exceptions import EnvironmentVariableError
from ..utils.validation_utils import (
    get_env_var,
    validate_constructor_args,
    validate_environment_variable,
)
from .base import EnvironmentBasedConstructor


class EnvironmentConstructor(EnvironmentBasedConstructor):
    """
    Constructor for !env directive.

    Supports two syntaxes:
    1. Simple: !env VAR_NAME (uses None as default)
    2. With default: !env [VAR_NAME, default_value]
    """

    def __init__(self):
        super().__init__("!env")

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract variable name and optional default from YAML node."""
        if isinstance(node, yaml.ScalarNode):
            # Simple case: !env VAR_NAME
            var_name = loader.construct_scalar(node)
            default = None
        elif isinstance(node, yaml.SequenceNode):
            # With default: !env [VAR_NAME, default]
            sequence = loader.construct_sequence(node)
            validate_constructor_args(sequence, (1, 2), self.directive_name)
            var_name = sequence[0]
            default = sequence[1] if len(sequence) > 1 else None
        else:
            raise EnvironmentVariableError(
                f"{self.directive_name} expects a scalar or sequence"
            )

        return {"var_name": var_name, "default": default}

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate environment variable parameters."""
        super().validate_parameters(params)
        validate_environment_variable(params["var_name"], self.directive_name)

    def execute(self, loader, params: Dict[str, Any]) -> Any:
        """Get environment variable value or default."""
        var_name = params["var_name"]
        default = params["default"]

        value = get_env_var(var_name, default)

        if value is None and default is None:
            raise EnvironmentVariableError(
                f"Environment variable '{var_name}' not found and no default provided"
            )

        return value

    def build_error_context(self, loader, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build error context for environment operations."""
        context = super().build_error_context(loader, params)
        if "default" in params:
            context["has_default"] = params["default"] is not None
        return context


# Create instance for registration
env_constructor = EnvironmentConstructor()
