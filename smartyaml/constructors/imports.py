"""
Import constructors for SmartYAML
"""

from typing import Any, Dict

from ..processing import (
    ParameterExtractor,
    ParameterPattern,
    ParameterSpec,
    ParameterValidator,
)
from ..utils.file_utils import read_file
from ..utils.validation_utils import validate_filename
from .base import FileBasedConstructor
from .yaml_file_loader import YamlFileLoaderMixin


class ImportConstructor(FileBasedConstructor):
    """
    Constructor for !import filename directive.
    Loads the entire content of a file as a string.

    This is a modernized example using the standardized parameter processing system.
    """

    # Type specifications for automatic type conversion
    TYPE_SPECS = {"filename": str}

    def __init__(self):
        # Create parameter specification
        filename_spec = ParameterSpec(
            name="filename",
            param_type=str,
            required=True,
            validator=lambda f: validate_filename(f, "!import"),
            description="The file path to import",
        )

        # Create parameter extractor for single scalar pattern
        extractor = ParameterExtractor(
            pattern=ParameterPattern.SINGLE_SCALAR, specs=[filename_spec]
        )

        # Create parameter validator
        validator = ParameterValidator.create_standard_validator(
            required_params=["filename"],
            type_specs={"filename": str},
            custom_validators={"filename": lambda f: validate_filename(f, "!import")},
        )

        super().__init__("!import", extractor, validator)

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Custom parameter extraction (empty since using standardized extractor)."""
        return {}

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Custom validation (empty since using standardized validator)."""

    def execute(self, loader, params: Dict[str, Any]) -> str:
        """Load and return file content as string."""
        file_path = params["resolved_file_path"]
        loader_context = self.get_loader_context(loader)
        return read_file(file_path, loader_context["max_file_size"])


class ImportYamlConstructor(FileBasedConstructor, YamlFileLoaderMixin):
    """
    Constructor for !import_yaml filename directive.
    Loads YAML content from file.
    """

    def __init__(self):
        super().__init__("!import_yaml")

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract filename parameter from YAML node."""
        filename = loader.construct_scalar(node)
        return {"filename": filename}

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate the filename parameter."""
        validate_filename(params["filename"], self.directive_name)

    def execute(self, loader, params: Dict[str, Any]) -> Any:
        """Load and return YAML data from file."""
        file_path = params["resolved_file_path"]
        loader_context = self.get_loader_context(loader)

        # Use the mixin to load the YAML file (no anchor preprocessing for imports)
        return self.load_yaml_file(
            file_path=file_path,
            loader_context=loader_context,
            parent_loader=loader,
            enable_anchor_preprocessing=False,
        )


# Create instances for registration
import_constructor = ImportConstructor()
import_yaml_constructor = ImportYamlConstructor()
