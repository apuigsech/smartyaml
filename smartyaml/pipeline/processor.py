"""
Main SmartYAML Processing Pipeline

Orchestrates the 6-stage processing pipeline with proper error handling,
security checks, and resource management.
"""

import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..cache import CacheManager
from ..config import SmartYAMLConfig
from ..debug import ErrorAnalyzer, SmartYAMLDebugger
from ..exceptions import RecursionLimitExceededError, SmartYAMLError
from .directives import DirectiveProcessor
from .metadata import MetadataProcessor
from .parser import YAMLParser
from .templates import TemplateProcessor
from .validator import SchemaValidator
from .variables import VariableProcessor


class ProcessingContext:
    """Context object that carries state through the processing pipeline."""

    def __init__(self, config: SmartYAMLConfig, file_path: Optional[Path] = None):
        self.config = config
        self.file_path = file_path
        # Set base_path with fallback to current working directory
        if file_path:
            self.base_path = file_path.parent
        elif config.base_path:
            self.base_path = config.base_path
        else:
            # Fallback to current working directory when no base path is provided
            self.base_path = Path.cwd()

        # Processing state
        self.recursion_depth = 0
        self.loaded_files = set()  # Track loaded files to prevent cycles
        self.variables = {}  # Merged variable context
        self.metadata = {}  # Extracted metadata
        self.schema = None  # Compiled schema

        # Performance tracking
        self.start_time = time.time()
        self.stage_times = {}

        # File size tracking for cumulative limits
        self.cumulative_file_size = 0

        # Thread safety
        self.lock = threading.RLock()

    def check_timeout(self):
        """Check if processing has exceeded timeout limit."""
        if time.time() - self.start_time > self.config.security.processing_timeout:
            raise SmartYAMLError(
                f"Processing timeout exceeded ({self.config.security.processing_timeout}s)"
            )

    def check_recursion(self, operation: str = "processing"):
        """Check and increment recursion depth."""
        if self.recursion_depth >= self.config.security.max_recursion_depth:
            raise RecursionLimitExceededError(
                self.config.security.max_recursion_depth, operation, str(self.file_path)
            )
        self.recursion_depth += 1

    def decrease_recursion(self):
        """Decrease recursion depth."""
        self.recursion_depth -= 1

    def track_stage(self, stage_name: str):
        """Track processing time for a stage."""
        self.stage_times[stage_name] = time.time() - self.start_time

    def track_file_size(self, file_path: Path):
        """Track cumulative file size for file size limits."""
        file_size = file_path.stat().st_size
        self.cumulative_file_size += file_size

        # Check cumulative file size limit
        if self.cumulative_file_size > self.config.security.max_file_size:
            from ..exceptions import FileSizeExceededError

            raise FileSizeExceededError(
                str(file_path),
                self.cumulative_file_size,
                self.config.security.max_file_size,
            )

        return file_size


class SmartYAMLProcessor:
    """Main processor that orchestrates the complete pipeline."""

    def __init__(self, config: Optional[SmartYAMLConfig] = None):
        self.config = config or SmartYAMLConfig()
        self.config.validate()

        # Initialize caching
        self.cache_manager = CacheManager(self.config)

        # Initialize debugging
        self.debugger = SmartYAMLDebugger(self.config)

        # Initialize pipeline components
        self.parser = YAMLParser(self.config)
        self.metadata_processor = MetadataProcessor(self.config)
        self.template_processor = TemplateProcessor(self.config)
        self.directive_processor = DirectiveProcessor(self.config)
        self.variable_processor = VariableProcessor(self.config)
        self.schema_validator = SchemaValidator(self.config)

    def process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Process a YAML file through the complete pipeline."""
        file_path = Path(file_path)

        if not file_path.exists():
            from ..exceptions import FileNotFoundError

            raise FileNotFoundError(str(file_path))

        # Try to get content from cache first
        yaml_content = None
        if self.cache_manager.is_enabled():
            yaml_content = self.cache_manager.file_cache.get_file_content(file_path)

        # Read file if not in cache
        if yaml_content is None:
            yaml_content = file_path.read_text()
            if self.cache_manager.is_enabled():
                self.cache_manager.file_cache.put_file_content(file_path, yaml_content)

        # Initialize processing context
        context = ProcessingContext(self.config, file_path)
        context.track_file_size(file_path)  # Track main file size

        # Check processed data cache
        if self.cache_manager.is_enabled():
            content_hash = self.cache_manager.processed_cache.compute_content_hash(
                yaml_content
            )
            config_hash = self.cache_manager.processed_cache.compute_config_hash(
                self.config
            )
            dependencies = ()  # TODO: Track file dependencies

            cached_result = self.cache_manager.processed_cache.get_processed_data(
                content_hash, config_hash, dependencies
            )
            if cached_result is not None:
                return cached_result

        try:
            result = self._process_with_context(yaml_content, context)

            # Cache the result
            if self.cache_manager.is_enabled():
                self.cache_manager.processed_cache.put_processed_data(
                    content_hash, config_hash, dependencies, result
                )

            return result
        except SmartYAMLError:
            raise
        except Exception as e:
            raise SmartYAMLError(
                f"Unexpected error processing file: {e}", str(file_path)
            ) from e

    def process_string(
        self, yaml_content: str, base_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Process YAML content from string through the complete pipeline."""
        context = ProcessingContext(self.config)
        if base_path:
            context.base_path = base_path

        try:
            return self._process_with_context(yaml_content, context)
        except SmartYAMLError:
            raise
        except Exception as e:
            raise SmartYAMLError(f"Unexpected error processing YAML: {e}") from e

    def _process_with_context(
        self, yaml_content: str, context: ProcessingContext
    ) -> Dict[str, Any]:
        """Execute the complete processing pipeline."""
        context.check_recursion("initial processing")

        # Debug: analyze input content
        if self.debugger.enabled:
            content_analysis = self.debugger.analyze_yaml_content(yaml_content)
            self.debugger.trace_step("analysis", "content_analysis", **content_analysis)

        try:
            # Stage 1: Initial Parsing & Version Check
            self.debugger.trace_step(
                "parsing", "start", file_path=str(context.file_path)
            )
            context.check_timeout()
            data = self.parser.parse(yaml_content, context)
            context.track_stage("parsing")
            self.debugger.trace_step(
                "parsing",
                "complete",
                data_keys=list(data.keys()) if isinstance(data, dict) else None,
            )

            # Stage 2: Metadata Resolution
            self.debugger.trace_step("metadata", "start")
            context.check_timeout()
            data = self.metadata_processor.process(data, context)
            context.track_stage("metadata")
            self.debugger.trace_step(
                "metadata",
                "complete",
                variables_count=len(context.variables),
                metadata_fields=list(context.metadata.keys()),
            )

            # Stage 3: Template Processing
            self.debugger.trace_step("templates", "start")
            context.check_timeout()
            data = self.template_processor.process(data, context)
            context.track_stage("templates")
            self.debugger.trace_step("templates", "complete")

            # Stage 4: Directive Resolution
            self.debugger.trace_step("directives", "start")
            context.check_timeout()
            data = self.directive_processor.process(data, context)
            context.track_stage("directives")
            self.debugger.trace_step("directives", "complete")

            # Stage 5: Variable Expansion
            self.debugger.trace_step("variables", "start")
            context.check_timeout()
            data = self.variable_processor.process(data, context)
            context.track_stage("variables")

            # Debug: analyze variables
            if self.debugger.enabled and context.variables:
                var_analysis = self.debugger.analyze_variables(context.variables)
                self.debugger.trace_step("variables", "complete", **var_analysis)
            else:
                self.debugger.trace_step("variables", "complete")

            # Stage 6: Schema Validation
            if context.metadata.get("__schema") and self.config.validate_schema:
                self.debugger.trace_step("validation", "start")
                context.check_timeout()
                schema = self.schema_validator.prepare_schema(
                    context.metadata["__schema"], context
                )
                self.schema_validator.validate(data, schema, context)
                context.track_stage("validation")
                self.debugger.trace_step("validation", "complete")
            else:
                self.debugger.trace_step("validation", "skipped", reason="no_schema")

            # Final cleanup - remove metadata fields
            if self.config.remove_metadata:
                self.debugger.trace_step("cleanup", "removing_metadata")
                data = self._remove_metadata_fields(data)

            self.debugger.trace_step(
                "processing",
                "complete",
                total_time=sum(context.stage_times.values()) if context.stage_times else 0,
            )

            return data

        except Exception as e:
            # Enhanced error handling with debugging
            self.debugger.trace_error(
                e,
                file_path=str(context.file_path),
                recursion_depth=context.recursion_depth,
                variables=list(context.variables.keys()),
            )

            # Generate helpful error report if it's a SmartYAML error
            if isinstance(e, SmartYAMLError) and self.config.debug_mode:
                error_report = ErrorAnalyzer.format_error_report(
                    e,
                    {
                        "processing_context": {
                            "file_path": str(context.file_path),
                            "stage_times": context.stage_times,
                            "loaded_files": [str(f) for f in context.loaded_files],
                        }
                    },
                )
                print(f"\n{error_report}\n")

            raise
        finally:
            context.decrease_recursion()

    def _remove_metadata_fields(self, data: Any) -> Any:
        """Remove all fields starting with __ from the data structure."""
        if isinstance(data, dict):
            return {
                key: self._remove_metadata_fields(value)
                for key, value in data.items()
                if not key.startswith("__")
            }
        elif isinstance(data, list):
            return [self._remove_metadata_fields(item) for item in data]
        else:
            return data
