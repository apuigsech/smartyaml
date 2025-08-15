"""
Encoding constructors for SmartYAML
"""

import base64
from typing import Any, Dict

from ..exceptions import ConstructorError
from ..processing import (
    ParameterExtractor,
    ParameterPattern,
    ParameterSpec,
    ParameterValidator,
)
from .base import BaseConstructor


class Base64Constructor(BaseConstructor):
    """
    Constructor for !base64(data) directive using standardized parameter processing.
    Encodes string data to base64.
    """

    def __init__(self):
        # Define parameter specifications
        specs = [
            ParameterSpec(name="data", param_type=str, required=True),
        ]

        # Create standardized extractor and validator
        extractor = ParameterExtractor(ParameterPattern.SINGLE_SCALAR, specs)
        validator = ParameterValidator.create_standard_validator(
            required_params=["data"], type_specs={"data": str}
        )

        super().__init__("!base64", extractor, validator)

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract parameters - handled by standardized extractor."""
        return {}  # Empty - handled by ParameterExtractor

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate parameters - handled by standardized validator."""
        pass  # Empty - handled by ParameterValidator

    def execute(self, loader, params: Dict[str, Any]) -> str:
        """Encode data to base64."""
        data = params["data"]

        try:
            # Encode string to bytes, then to base64, then back to string
            encoded_bytes = base64.b64encode(data.encode("utf-8"))
            return encoded_bytes.decode("ascii")
        except Exception as e:
            raise ConstructorError(
                directive_name=self.directive_name,
                message=f"Failed to base64 encode data: {e}",
                location=None,
            ) from e


class Base64DecodeConstructor(BaseConstructor):
    """
    Constructor for !base64_decode(data) directive using standardized parameter processing.
    Decodes base64 data to string.
    """

    def __init__(self):
        # Define parameter specifications
        specs = [
            ParameterSpec(name="b64_data", param_type=str, required=True),
        ]

        # Create standardized extractor and validator
        extractor = ParameterExtractor(ParameterPattern.SINGLE_SCALAR, specs)
        validator = ParameterValidator.create_standard_validator(
            required_params=["b64_data"], type_specs={"b64_data": str}
        )

        super().__init__("!base64_decode", extractor, validator)

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract parameters - handled by standardized extractor."""
        return {}  # Empty - handled by ParameterExtractor

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate parameters - handled by standardized validator."""
        pass  # Empty - handled by ParameterValidator

    def execute(self, loader, params: Dict[str, Any]) -> str:
        """Decode base64 data to string."""
        b64_data = params["b64_data"]

        try:
            # Decode base64 to bytes, then decode bytes to string
            decoded_bytes = base64.b64decode(b64_data)
            return decoded_bytes.decode("utf-8")
        except Exception as e:
            raise ConstructorError(
                directive_name=self.directive_name,
                message=f"Failed to base64 decode data: {e}",
                location=None,
            ) from e


# Create instances for registration
base64_constructor = Base64Constructor()
base64_decode_constructor = Base64DecodeConstructor()
