"""
Encoding constructors for SmartYAML
"""

import base64
from typing import Any, Dict

from ..exceptions import Base64Error
from .base import BaseConstructor


class Base64Constructor(BaseConstructor):
    """
    Constructor for !base64(data) directive.
    Encodes string data to base64.
    """

    def __init__(self):
        super().__init__("!base64")

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract data to encode from YAML node."""
        if hasattr(node, "value") and isinstance(node.value, list):
            # For sequence node (multiple parameters), join them with comma
            # This handles cases like !base64(Hello, world!) where the comma is part of the data
            params = [loader.construct_scalar(param_node) for param_node in node.value]
            data = ", ".join(params)
        else:
            # For scalar node, use as-is
            data = loader.construct_scalar(node)
        return {"data": data}

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate data parameter."""
        if params["data"] is None:
            raise Base64Error(f"{self.directive_name} requires data to encode")
        if not isinstance(params["data"], str):
            raise Base64Error(f"{self.directive_name} data must be a string")

    def execute(self, loader, params: Dict[str, Any]) -> str:
        """Encode data to base64."""
        data = params["data"]

        try:
            # Encode string to bytes, then to base64, then back to string
            encoded_bytes = base64.b64encode(data.encode("utf-8"))
            return encoded_bytes.decode("ascii")
        except Exception as e:
            raise Base64Error(f"Failed to base64 encode data: {e}")


class Base64DecodeConstructor(BaseConstructor):
    """
    Constructor for !base64_decode(data) directive.
    Decodes base64 data to string.
    """

    def __init__(self):
        super().__init__("!base64_decode")

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract base64 data to decode from YAML node."""
        if hasattr(node, "value") and isinstance(node.value, list):
            # For sequence node (multiple parameters), join them (though unlikely for base64 data)
            params = [loader.construct_scalar(param_node) for param_node in node.value]
            b64_data = "".join(params)  # No comma separator for base64 data
        else:
            # For scalar node, use as-is
            b64_data = loader.construct_scalar(node)
        return {"b64_data": b64_data}

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate base64 data parameter."""
        if params["b64_data"] is None:
            raise Base64Error(f"{self.directive_name} requires base64 data to decode")
        if not isinstance(params["b64_data"], str):
            raise Base64Error(f"{self.directive_name} data must be a string")

    def execute(self, loader, params: Dict[str, Any]) -> str:
        """Decode base64 data to string."""
        b64_data = params["b64_data"]

        try:
            # Decode base64 to bytes, then decode bytes to string
            decoded_bytes = base64.b64decode(b64_data)
            return decoded_bytes.decode("utf-8")
        except Exception as e:
            raise Base64Error(f"Failed to base64 decode data: {e}")


# Create instances for registration
base64_constructor = Base64Constructor()
base64_decode_constructor = Base64DecodeConstructor()
