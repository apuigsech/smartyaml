"""
Stage 6: JSON Schema Validation

Validates processed YAML data against JSON Schema Draft 2020-12 specifications
with comprehensive error reporting and security considerations.
"""

import json
from pathlib import Path
from typing import Any, Dict

from ..config import SmartYAMLConfig
from ..exceptions import SchemaValidationError, SmartYAMLError


class SchemaValidator:
    """Stage 6: Validate data against JSON Schema."""

    def __init__(self, config: SmartYAMLConfig):
        self.config = config
        self._compiled_schemas = {}  # Cache for compiled schemas

    def validate(self, data: Any, schema: Dict[str, Any], context) -> None:
        """Validate data against the provided schema."""
        if not schema:
            return

        try:
            # Import jsonschema with error handling
            import jsonschema  # noqa: F401
        except ImportError:
            if self.config.require_schema_validation:
                raise SmartYAMLError(
                    "jsonschema library required for schema validation. Install with: pip install jsonschema",
                    str(context.file_path),
                )
            else:
                # Skip validation if jsonschema not available and not required
                return

        # Get or compile validator
        validator = self._get_validator(schema, context)

        # Perform validation
        errors = list(validator.iter_errors(data))

        if errors:
            # Format validation errors
            error_messages = []
            for error in errors:
                path = (
                    ".".join(str(p) for p in error.absolute_path)
                    if error.absolute_path
                    else "root"
                )
                error_messages.append(f"At '{path}': {error.message}")

            raise SchemaValidationError(error_messages, str(context.file_path))

    def prepare_schema(self, schema_config: Dict[str, Any], context) -> Dict[str, Any]:
        """Prepare and load schema from configuration."""
        if isinstance(schema_config, dict):
            if "path" in schema_config:
                # Load schema from file
                return self._load_schema_file(schema_config["path"], context)
            elif "url" in schema_config:
                # Load schema from URL (if enabled)
                if self.config.allow_remote_schemas:
                    return self._load_schema_url(schema_config["url"], context)
                else:
                    raise SmartYAMLError(
                        "Remote schema loading disabled in configuration",
                        str(context.file_path),
                        "__schema.url",
                    )
            elif "inline" in schema_config:
                # Inline schema definition
                return schema_config["inline"]
            else:
                # Direct schema object
                return schema_config
        elif isinstance(schema_config, str):
            # String path to schema file
            return self._load_schema_file(schema_config, context)
        else:
            raise SmartYAMLError(
                "__schema must be a path, URL, or inline schema object",
                str(context.file_path),
                "__schema",
            )

    def _get_validator(self, schema: Dict[str, Any], context):
        """Get or create a validator for the schema."""
        import jsonschema

        # Create cache key
        schema_str = json.dumps(schema, sort_keys=True)
        cache_key = hash(schema_str)

        if cache_key in self._compiled_schemas:
            return self._compiled_schemas[cache_key]

        # Determine schema draft version
        draft_version = schema.get(
            "$schema", "https://json-schema.org/draft/2020-12/schema"
        )

        # Select appropriate validator class
        if "2020-12" in draft_version:
            ValidatorClass = jsonschema.Draft202012Validator
        elif "2019-09" in draft_version:
            ValidatorClass = jsonschema.Draft201909Validator
        elif "draft-07" in draft_version:
            ValidatorClass = jsonschema.Draft7Validator
        elif "draft-06" in draft_version:
            ValidatorClass = jsonschema.Draft6Validator
        elif "draft-04" in draft_version:
            ValidatorClass = jsonschema.Draft4Validator
        else:
            # Default to latest supported
            ValidatorClass = jsonschema.Draft202012Validator

        # Create validator instance
        try:
            validator = ValidatorClass(schema)

            # Cache the validator
            self._compiled_schemas[cache_key] = validator
            return validator

        except jsonschema.SchemaError as e:
            raise SchemaValidationError(
                [f"Invalid schema: {e.message}"], str(context.file_path)
            )

    def _load_schema_file(self, schema_path: str, context) -> Dict[str, Any]:
        """Load schema from a file path."""
        path = Path(schema_path)

        if not path.is_absolute():
            path = context.base_path / path

        path = path.resolve()

        if not path.exists():
            from ..exceptions import FileNotFoundError

            raise FileNotFoundError(str(path), str(context.base_path), "schema")

        # Security check: ensure schema file is within allowed paths
        if self.config.schema_base_path:
            try:
                path.relative_to(self.config.schema_base_path)
            except ValueError:
                from ..exceptions import SecurityViolationError

                raise SecurityViolationError(
                    "path_traversal",
                    f"Schema file '{path}' is outside allowed schema directory",
                    str(context.file_path),
                )

        # Check file size
        file_size = path.stat().st_size
        if file_size > self.config.max_schema_size:
            from ..exceptions import FileSizeExceededError

            raise FileSizeExceededError(
                str(path), file_size, self.config.max_schema_size
            )

        try:
            content = path.read_text()

            # Parse as JSON or YAML
            if path.suffix.lower() == ".json":
                return json.loads(content)
            else:
                # Parse as YAML
                import yaml

                return yaml.safe_load(content)

        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise SmartYAMLError(
                f"Invalid schema file format: {e}", str(context.file_path)
            ) from e

    def _load_schema_url(self, schema_url: str, context) -> Dict[str, Any]:
        """Load schema from a URL (if remote schemas are enabled)."""
        try:
            import urllib.parse
            import urllib.request
        except ImportError:
            raise SmartYAMLError(
                "urllib required for remote schema loading", str(context.file_path)
            )

        # Basic URL validation
        parsed_url = urllib.parse.urlparse(schema_url)
        if parsed_url.scheme not in ("http", "https"):
            raise SmartYAMLError(
                "Only HTTP/HTTPS URLs allowed for remote schemas",
                str(context.file_path),
                "__schema.url",
            )

        try:
            with urllib.request.urlopen(
                schema_url, timeout=self.config.remote_timeout
            ) as response:
                content = response.read().decode("utf-8")

            # Parse response
            content_type = response.headers.get("content-type", "").lower()

            if "json" in content_type:
                return json.loads(content)
            else:
                # Try YAML
                import yaml

                return yaml.safe_load(content)

        except Exception as e:
            raise SmartYAMLError(
                f"Failed to load remote schema from '{schema_url}': {e}",
                str(context.file_path),
            ) from e

    def clear_cache(self):
        """Clear the compiled schema cache."""
        self._compiled_schemas.clear()
