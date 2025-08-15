"""
Environment variable constructor for SmartYAML
"""

from typing import Any, Dict

from ..exceptions import ConstructorError
from ..processing import (
    ParameterExtractor,
    ParameterPattern,
    ParameterSpec,
    ParameterValidator,
)
from ..utils.validation_utils import (
    get_env_var,
    validate_environment_variable,
)
from .base import EnvironmentBasedConstructor


class EnvironmentConstructor(EnvironmentBasedConstructor):
    """
    Constructor for !env directive using standardized parameter processing.

    Supports two syntaxes:
    1. Simple: !env VAR_NAME (uses None as default)
    2. With default: !env [VAR_NAME, default_value]
    """

    def __init__(self):
        # Define parameter specifications
        specs = [
            ParameterSpec(name="var_name", param_type=str, required=True),
            ParameterSpec(name="default", param_type=str, required=False, default=None),
        ]

        # Create standardized extractor and validator
        extractor = ParameterExtractor(ParameterPattern.SCALAR_OR_SEQUENCE, specs)
        validator = ParameterValidator.create_standard_validator(
            required_params=["var_name"],
            type_specs={"var_name": str},
            custom_validators={
                "var_name": lambda v: validate_environment_variable(v, "!env")
            },
        )

        super().__init__("!env", extractor, validator)

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract parameters - handled by standardized extractor."""
        return {}  # Empty - handled by ParameterExtractor

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate parameters - handled by standardized validator."""
        pass  # Empty - handled by ParameterValidator

    def execute(self, loader, params: Dict[str, Any]) -> Any:
        """Get environment variable value or default."""
        var_name = params["var_name"]
        default = params["default"]

        value = get_env_var(var_name, default)

        if value is None and default is None:
            raise ConstructorError(
                directive_name=self.directive_name,
                message=(
                    f"Environment variable '{var_name}' not found and no default provided. "
                    f"To fix this, either:\n"
                    f"1. Set the environment variable: export {var_name}=your_value\n"
                    f"2. Provide a default: !env [{var_name}, default_value]\n"
                    f"3. Use conditional inclusion: !include_if [{var_name}, config.yaml]"
                ),
                location=None,
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
