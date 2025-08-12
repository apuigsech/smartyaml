# SmartYAML Architecture Documentation

## Table of Contents
- [Overview](#overview)
- [Core Architecture](#core-architecture)
- [The Loading Process](#the-loading-process)
- [Component Deep Dive](#component-deep-dive)
- [Constructor System](#constructor-system)
- [Security Model](#security-model)
- [Performance Design](#performance-design)
- [Design Decisions](#design-decisions)

## Overview

SmartYAML extends standard YAML with custom directives for file imports, environment variables, templates, and variable expansion. The architecture is built around a **pipeline-based design** that processes YAML content through multiple stages, each handling specific aspects of SmartYAML functionality.

### Key Features
- **Extended YAML Syntax**: Custom directives like `!import`, `!env`, `!expand`, `!template`
- **Template System**: Support for both inline (`__template`) and external templates
- **Variable Processing**: Sophisticated variable inheritance and expansion
- **Security-First**: Built-in protections against file system attacks
- **Performance Optimized**: Caching, singleton patterns, pre-compiled regex

## Core Architecture

SmartYAML follows a **modular pipeline architecture** that replaced the original monolithic design:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Entry Points  │───▶│   LoadPipeline  │───▶│ Final Processing│
│  load()/loads() │    │   Orchestrator  │    │ & Result Output │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼──────────────┐
                │               │              │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼─────┐
        │ Content      │ │ Template    │ │ Variable  │
        │ Reading      │ │ Processing  │ │ Merging   │
        └──────────────┘ └─────────────┘ └───────────┘
                                │              │
                        ┌───────▼────────┐     │
                        │  SmartYAML     │     │
                        │  Loader        │     │
                        └───────┬────────┘     │
                                │              │
                        ┌───────▼────────┐     │
                        │ Constructor    │     │
                        │ Registry &     │     │
                        │ Dispatch       │     │
                        └───────┬────────┘     │
                                │              │
                        ┌───────▼────────┐     │
                        │ Deferred       │◄────┘
                        │ Expansion      │
                        └───────┬────────┘
                                │
                        ┌───────▼────────┐
                        │ Metadata       │
                        │ Cleanup        │
                        └────────────────┘
```

## The Loading Process

### 1. Entry Points (`smartyaml/__init__.py`)

**Functions: `load()` and `loads()`**

These are thin wrapper functions that provide the public API:

```python
def load(
    stream: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
    template_path: Optional[Union[str, Path]] = None,
    max_file_size: Optional[int] = None,
    max_recursion_depth: Optional[int] = None,
    remove_metadata: bool = True,
    variables: Optional[Dict[str, Any]] = None,
) -> Any:
    """Load SmartYAML from file or string."""
    from .loading import LoadPipeline

    pipeline = LoadPipeline()
    return pipeline.load(stream=stream, ...)
```

**Key Responsibilities:**
- Parameter validation and defaults
- LoadPipeline instantiation
- Result delegation

### 2. Pipeline Orchestration (`smartyaml/loading/pipeline.py`)

**Class: `LoadPipeline`**

The heart of the SmartYAML loading system. Orchestrates the complete loading process through **8 sequential steps**:

#### Component Architecture

Uses singleton pattern for performance optimization:

```python
class _ComponentSingletons:
    """Singleton manager for pipeline components."""

    def get_content_reader(self) -> ContentReader
    def get_template_preprocessor(self) -> TemplatePreprocessor
    def get_inline_template_processor(self) -> InlineTemplateProcessor
    def get_variable_merger(self) -> VariableMerger
```

**Design Benefits:**
- **Performance**: Expensive component creation happens once
- **Memory**: Shared component instances across pipeline invocations
- **Testability**: Dependency injection support for unit testing

#### The 8-Step Loading Process

##### Step 1: Content Reading
```python
content, resolved_base_path = self.content_reader.read_from_stream(
    stream, Path(base_path) if base_path else None
)
```

**Purpose**: Unified content reading from files or strings
- Detects if input is file path vs. string content
- Reads file content with size validation
- Resolves absolute base path for relative imports
- Handles encoding and error cases

##### Step 2: Template Preprocessing
```python
processed_content, template_anchors = self.template_preprocessor.preprocess_content(
    content, Path(template_path) if template_path else None
)
```

**Purpose**: Extract and process external template references
- Scans content for `!template(name)` references
- Loads external template files from `template_path`
- Extracts YAML anchors for cross-file sharing
- Returns preprocessed content and anchor mapping

**Why First**: External templates must be loaded before YAML parsing to make anchors available during composition.

##### Step 2.5: Inline Template Processing
```python
processed_content = self.template_preprocessor.process_inline_templates(
    processed_content, resolved_base_path, template_path, variables
)
```

**Purpose**: Process `__template` directives before main parsing
- Extracts `__template` blocks from YAML
- Processes template data through full SmartYAML pipeline
- Deep merges template with document (document takes precedence)
- Converts result back to YAML string for parsing

**Critical Timing**: Must happen before YAML parsing because `__template` affects document structure.

##### Step 3: Loader Creation
```python
loader_instance = self._create_loader(
    resolved_base_path, template_path, max_file_size,
    max_recursion_depth, variables, template_anchors
)
```

**Purpose**: Configure SmartYAML loader with context
- Creates `SmartYAMLLoader` class extending `yaml.SafeLoader`
- Sets up base paths for file resolution
- Initializes variable context and import tracking
- Configures security limits and template anchors
- **Implements loader instance capture**: Uses closure to capture the actual loader instance created during parsing for variable access

##### Step 4: YAML Parsing
```python
result = yaml.load(processed_content, Loader=loader_instance)
```

**Purpose**: Parse YAML with constructor invocation
- Uses PyYAML's standard parsing with custom loader
- SmartYAML constructors are invoked during parsing
- Handles directives: `!import`, `!env`, `!expand`, etc.
- Variables accumulate in loader context
- Security checks applied per constructor

**Constructor Processing Order:**
1. PyYAML encounters directive tag (e.g., `!expand`)
2. Tag dispatched to SmartYAML constructor via registry
3. Constructor processes parameters and executes logic
4. Result integrated into YAML structure

##### Step 5: Variable Processing
```python
# Get the actual loader instance that was used during parsing
actual_loader_instance = loader_instance._get_captured_instance()
accumulated_variables = self.variable_merger.process_accumulated_variables(
    actual_loader_instance, result, variables
)
```

**Purpose**: Merge variables from all sources with precedence
- **Highest Priority**: Function variables (`load(file, variables={...})`)
- **Medium Priority**: Document variables (`__vars` in main file)
- **Lowest Priority**: Accumulated variables (from `__vars` in imports)
- Result: Single merged variable context for deferred expansion

**Critical Fix**: The pipeline captures the actual loader instance used during parsing to access `accumulated_vars` from imported templates, solving the variable inheritance issue.

##### Step 6: Template Post-Processing (Fallback)
```python
result = self._process_inline_template(result, ...)
```

**Purpose**: Safety fallback for remaining `__template` directives
- Usually empty since templates are preprocessed in Step 2.5
- Handles edge cases where preprocessing was skipped
- Maintains backward compatibility

##### Step 7: Deferred Expansion Processing
```python
result = self._process_expansions(result, accumulated_variables)
```

**Purpose**: Resolve deferred `!expand` directives
- Processes `__smartyaml_expand_deferred` markers
- Uses complete variable context from Step 5
- Supports recursive variable expansion (variables referencing variables)
- Handles missing variable errors with rich context

**Why Deferred**: `!expand` directives encountered during parsing may need variables defined later in `__vars` sections.

##### Step 8: Metadata Cleanup
```python
if remove_metadata:
    result = self._remove_metadata_fields(result)
```

**Purpose**: Clean internal metadata fields
- Removes fields with `__` prefix (`__vars`, `__template`)
- Returns clean final data structure
- Optional via `remove_metadata` parameter

### 3. YAML Loader (`smartyaml/loader.py`)

**Class: `SmartYAMLLoader` extends `yaml.SafeLoader`**

The core YAML parsing engine that integrates SmartYAML functionality with PyYAML.

#### Key Features

**Constructor Integration:**
```python
# Multi-constructor registration for all ! tags
add_multi_constructor("!", smart_constructor_dispatch)

def smart_constructor_dispatch(loader, tag_suffix, node):
    """Dispatch ! tags to registry system."""
    parsed_tag = _tag_parser.parse_tag(tag_suffix)
    constructor = _registry.get_constructor(parsed_tag.base_tag)
    return constructor(loader, node)
```

**Variable Accumulation:**
```python
def accumulate_vars(self, new_vars: Dict[str, Any]):
    """Accumulate variables during parsing."""
    if self.accumulated_vars is None:
        self.accumulated_vars = {}
    self.accumulated_vars.update(new_vars)
```

- Called by constructors when processing `__vars` sections
- Maintains global variable context across file imports
- Enables variable inheritance in template chains

**Enhanced Merge Key Support:**
```python
def flatten_mapping(self, node):
    """Enhanced merge key processing for SmartYAML directives."""
    # Standard PyYAML merge processing
    # PLUS: Handle SmartYAML directives in merge keys
    # Example: <<: !import file.yaml
```

#### Security Integration

**Import Tracking:**
- `import_stack`: Set of currently importing files
- Prevents circular import loops
- Enforces recursion depth limits

**Context Preservation:**
- Maintains file paths, template paths, and variable contexts
- Passes security context to constructors
- Enables proper error location reporting

### 4. Constructor Registry (`smartyaml/registry.py`)

**Class: `ConstructorRegistry`**

Centralized system for managing SmartYAML directive constructors.

#### Registration System
```python
def register_default_constructors():
    """Register all built-in SmartYAML constructors."""
    constructors = {
        "!import": import_constructor,
        "!import_yaml": import_yaml_constructor,
        "!env": env_constructor,
        "!expand": expand_constructor,
        "!template": template_constructor,
        "!include_if": include_if_constructor,
        "!include_yaml_if": include_yaml_if_constructor,
        "!base64": base64_constructor,
        "!base64_decode": base64_decode_constructor,
    }
    _registry.register_multiple(constructors)
```

#### Dispatch Logic
1. **Tag Parsing**: Parse complex tags like `!env(VAR_NAME, default_value)`
2. **Constructor Lookup**: Find appropriate constructor in registry
3. **Node Processing**: Create YAML node with parameters
4. **Constructor Invocation**: Call constructor with loader and node
5. **Result Integration**: Return result for YAML structure

### 5. Tag Parsing (`smartyaml/parsing/tag_parser.py`)

**Class: `TagParser`**

Handles complex SmartYAML tag syntax:

```python
class TagParser:
    # Patterns for different tag syntaxes
    PARENTHESES_PATTERN = re.compile(r"^(![\w_]+)\((.+)\)$")  # !tag(args)
    BRACKETS_PATTERN = re.compile(r"^(![\w_]+)\s*\[(.+)\]$")   # !tag [args]
```

**Supported Syntaxes:**
- **Simple**: `!env` → `ParsedTag(base_tag="!env", parameters=None)`
- **Parentheses**: `!env(VAR_NAME, default)` → parameters extracted
- **Brackets**: `!import [file.yaml, key]` → parameters extracted

**PyYAML Integration Challenge:**
- PyYAML splits tags at certain characters
- TagParser reconstructs original tag from suffix
- Enables complex parameter syntax

## Component Deep Dive

### Content Reader (`smartyaml/loading/content_reader.py`)

**Purpose**: Unified content reading with validation

**Key Methods:**
```python
def read_from_stream(self, stream: Union[str, Path], base_path: Optional[Path]) -> Tuple[str, Path]:
    """Read content from file path or string."""
    if self._is_file_path(stream):
        # File reading with validation
        return self._read_from_file(Path(stream), base_path)
    else:
        # String content processing
        return str(stream), base_path or Path.cwd()
```

**Features:**
- File vs. string detection
- Path resolution and validation
- Error handling with context
- Base path determination

### Template Preprocessor (`smartyaml/loading/template_preprocessor.py`)

**Purpose**: Handle external templates and inline template preprocessing

#### External Template Processing:
```python
def preprocess_content(self, content: str, template_path: Optional[Path]) -> Tuple[str, Dict[str, Any]]:
    """Extract template anchors for cross-file sharing."""
    # 1. Scan for !template(name) references
    # 2. Load template files from template_path
    # 3. Extract YAML anchors using AnchorCapturingLoader
    # 4. Return content and anchor mapping
```

#### Inline Template Processing:
```python
def process_inline_templates(self, content: str, ...) -> str:
    """Process __template blocks before YAML parsing."""
    # 1. Parse YAML to extract __template blocks
    # 2. Process template through full SmartYAML pipeline
    # 3. Deep merge template with document
    # 4. Convert back to YAML string
```

**Critical Design**: Inline templates must be processed before YAML parsing because they modify document structure.

### Variable Merger (`smartyaml/loading/variable_merger.py`)

**Purpose**: Handle complex variable precedence and merging

```python
def merge_variables(
    self,
    function_variables: Optional[Dict[str, Any]],
    accumulated_variables: Dict[str, Any],
    document_vars: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Merge variables with proper precedence."""
    # Priority order (highest to lowest):
    # 1. Function variables (passed to load())
    # 2. Accumulated variables (from __vars in imports)
    # 3. Document vars (from __vars in main document)
```

**Advanced Features:**
```python
def expand_variables_recursively(self, variables: Dict[str, Any], max_iterations: int = 10) -> Dict[str, Any]:
    """Expand variables that reference other variables."""
    # Handles: greeting: "Hello {{name}}", name: "{{user}}", user: "Alice"
    # Result: greeting: "Hello Alice", name: "Alice", user: "Alice"
```

### Inline Template Processor (`smartyaml/loading/inline_template_processor.py`)

**Purpose**: Process `__template` directives within documents

```python
def process_inline_template(self, data: Dict[str, Any], loader_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Process __template directive and merge with document."""
    # 1. Extract __template and document parts
    # 2. Process template through SmartYAML pipeline
    # 3. Deep merge template with document (document wins)
    # 4. Return merged result
```

**Merge Strategy**: Document values take precedence over template values, enabling template customization.

## Constructor System

### Base Constructor Pattern

All SmartYAML constructors follow the **Template Method Pattern**:

```python
class BaseConstructor:
    def __call__(self, loader, node):
        """Template method defining constructor workflow."""
        try:
            # Step 1: Extract parameters from YAML node
            params = self.extract_parameters(loader, node)

            # Step 2: Validate parameters
            self.validate_parameters(params)

            # Step 3: Apply security checks
            self.apply_security_checks(loader, params)

            # Step 4: Execute main logic
            result = self.execute(loader, params)

            # Step 5: Post-process result
            return self.post_process(result, params)

        except Exception as e:
            # Step 6: Enhanced error handling
            context = ErrorContextBuilder.build_constructor_context(...)
            raise enhance_error_with_context(e, context) from e
```

### Specialized Base Classes

**FileBasedConstructor**: For file operations
```python
class FileBasedConstructor(BaseConstructor):
    def apply_security_checks(self, loader, params):
        """Enhanced file security validation."""
        # - Path traversal prevention
        # - File existence validation
        # - Size limit enforcement
        # - Recursion depth checking
```

**EnvironmentBasedConstructor**: For environment variables
```python
class EnvironmentBasedConstructor(BaseConstructor):
    def should_include(self, condition: str) -> bool:
        """Evaluate environment-based conditions."""
        # Supports various condition formats
```

### Key Constructors

#### `!import` - Text File Import
```python
class ImportConstructor(FileBasedConstructor):
    def execute(self, loader, params):
        """Import text file content."""
        file_path = params["resolved_file_path"]
        return read_file(file_path, loader_context["max_file_size"])
```

#### `!import_yaml` - YAML File Import
```python
class ImportYamlMergeConstructor(FileBasedConstructor):
    def execute(self, loader, params):
        """Import and parse YAML file."""
        # 1. Read YAML file
        # 2. Create new loader with recursion tracking
        # 3. Parse with SmartYAML processing
        # 4. Extract and accumulate __vars
        # 5. Return parsed data
```

#### `!env` - Environment Variables
```python
class EnvironmentConstructor(EnvironmentBasedConstructor):
    def execute(self, loader, params):
        """Resolve environment variable."""
        var_name = params["var_name"]
        default = params.get("default")
        return os.environ.get(var_name, default)
```

#### `!expand` - Variable Expansion
```python
class ExpandConstructor(BaseConstructor):
    def execute(self, loader, params):
        """Expand variables in string."""
        content = params["content"]

        # Try immediate expansion if variables available
        if hasattr(loader, 'expansion_variables') and loader.expansion_variables:
            # Attempt expansion with current variables

        # Defer expansion for post-processing
        return {"__smartyaml_expand_deferred": content}
```

**Deferred Expansion Design**: Variables from `__vars` sections aren't available during parsing, so expansion is deferred until post-processing.

#### `!template` - External Templates
```python
class TemplateConstructor(BaseConstructor):
    def execute(self, loader, params):
        """Load external template with anchors."""
        template_name = params["template_name"]
        # Template anchors were extracted during preprocessing
        # Return reference that PyYAML can resolve
```

## Security Model

SmartYAML implements **defense-in-depth security** across multiple layers:

### File System Protection

**Path Traversal Prevention:**
```python
def resolve_path(file_path: str, base_path: Path) -> Path:
    """Resolve file path with traversal protection."""
    resolved = (base_path / file_path).resolve()

    # Ensure resolved path is within base_path
    if not str(resolved).startswith(str(base_path.resolve())):
        raise InvalidPathError(f"Path traversal detected: {file_path}")

    return resolved
```

**File Size Limits:**
```python
def read_file(file_path: Path, max_size: Optional[int] = None) -> str:
    """Read file with size validation."""
    if max_size is None:
        max_size = get_config().max_file_size  # Default: 10MB

    file_size = file_path.stat().st_size
    if file_size > max_size:
        raise ResourceLimitError(f"File too large: {file_size} > {max_size}")
```

### Import Protection

**Circular Import Detection:**
```python
def check_recursion_limit(import_stack: Set[Path], file_path: Path, max_depth: Optional[int]):
    """Prevent circular imports and deep recursion."""
    if file_path in import_stack:
        raise RecursionLimitError(f"Circular import: {file_path}")

    if max_depth and len(import_stack) >= max_depth:
        raise RecursionLimitError(f"Max recursion depth exceeded: {max_depth}")
```

### Safe Parsing

**YAML Safety:**
- Uses `yaml.SafeLoader` as base (no code execution)
- No `!!python/` tags or unsafe constructors
- All custom constructors are explicitly safe

**Environment Variable Access:**
- Only reads environment variables (no system commands)
- No write access to environment or files
- Controlled through explicit directives only

## Performance Design

### Singleton Pattern for Components

**Problem**: Component creation is expensive
**Solution**: Singleton pattern with lazy initialization

```python
class _ComponentSingletons:
    def get_content_reader(self) -> ContentReader:
        if self._content_reader is None:
            self._content_reader = ContentReader()
        return self._content_reader
```

**Benefits:**
- Components created once per application
- Memory efficient for repeated pipeline usage
- Testable through dependency injection

### Caching Strategy

**File Content Caching:**
```python
class FileCache:
    """Thread-safe file cache with TTL and size limits."""
    def get(self, file_path: Path) -> Optional[str]:
        # Check cache with timestamp validation
        # Return cached content if valid

    def put(self, file_path: Path, content: str):
        # Cache with size and TTL management
```

**Template Anchor Caching:**
```python
class TemplatePreprocessor:
    def cache_anchors(self, template_name: str, anchors: Dict[str, Any]):
        """Cache extracted anchors to avoid re-parsing."""
        self._anchor_cache[template_name] = anchors.copy()
```

### Pre-compiled Patterns

**Regex Optimization:**
```python
class OptimizedPatterns:
    # Pre-compile frequently used patterns
    TEMPLATE_DIRECTIVE_PATTERN = re.compile(r'^\s*__template\s*:', re.MULTILINE)
    VARS_SECTION_PATTERN = re.compile(r'^__vars:\s*\n((?:[ ]{2}.*\n)*)', re.MULTILINE)

    @staticmethod
    def has_template_directive(yaml_content: str) -> bool:
        return bool(OptimizedPatterns.TEMPLATE_DIRECTIVE_PATTERN.search(yaml_content))
```

**Performance Impact:**
- Eliminates regex compilation overhead
- Significant improvement for template-heavy files
- Used in performance-critical parsing paths

### String Optimization

**Memory-Efficient Operations:**
```python
class StringOptimizations:
    @staticmethod
    def join_with_separator(parts: list, separator: str = ", ") -> str:
        """Memory-efficient string joining with pre-allocation."""
        if not parts:
            return ""
        if len(parts) == 1:
            return str(parts[0])

        # Pre-calculate capacity for better memory efficiency
        total_len = sum(len(str(part)) for part in parts) + len(separator) * (len(parts) - 1)

        # Use join which is more efficient than concatenation
        return separator.join(str(part) for part in parts)
```

## Design Decisions

### 1. Pipeline Architecture

**Decision**: Replace monolithic `load()` function with composable pipeline
**Reasoning**:
- **Testability**: Each component can be unit tested independently
- **Maintainability**: Clear separation of concerns
- **Extensibility**: New processing steps can be added easily
- **Debugging**: Easier to trace issues through specific pipeline stages

### 2. Deferred Expansion

**Decision**: Process `!expand` directives after YAML parsing
**Reasoning**:
- **Variable Availability**: `__vars` sections aren't parsed during directive processing
- **Precedence Handling**: Need complete variable context from all sources
- **Recursive Resolution**: Variables can reference other variables

**Alternative Considered**: Immediate expansion during parsing
**Rejected Because**: Would require multiple parsing passes or complex variable pre-extraction

### 3. Template Preprocessing

**Decision**: Process templates before YAML parsing
**Reasoning**:
- **Anchor Availability**: External template anchors needed during YAML composition
- **Structure Modification**: `__template` blocks change document structure
- **Performance**: Single-pass parsing after preprocessing

### 4. Registry-Based Constructors

**Decision**: Use centralized registry instead of manual dispatcher
**Previous Approach**: Large switch statement in loader
**Benefits**:
- **Cleaner Code**: Eliminates complex manual dispatch logic
- **Dynamic Registration**: Constructors can be registered at runtime
- **Extensibility**: Third-party constructors can be easily added

### 5. Security-First Design

**Decision**: Build security into every file operation
**Reasoning**:
- **Production Safety**: Must be safe for untrusted YAML files
- **Attack Prevention**: Multiple layers prevent various attack vectors
- **Fail-Safe**: Restrictive defaults with explicit permissions

**Security Features**:
- Path traversal prevention
- File size limits
- Recursion depth limits
- Circular import detection
- Safe-only YAML parsing

### 6. Error Context System

**Decision**: Rich error context with file locations and YAML snippets
**Reasoning**:
- **Debugging Experience**: Complex nested loading makes errors hard to trace
- **User Experience**: Clear error messages with actionable information
- **Development Productivity**: Faster debugging and issue resolution

**Error Context Components**:
- File paths and line numbers
- YAML content snippets
- Constructor-specific context
- Variable resolution context

### 7. Variable Precedence Model

**Decision**: Three-tier variable precedence system
**Reasoning**:
- **Flexibility**: Allows override at multiple levels
- **Predictability**: Clear precedence rules
- **Template Support**: Enables template customization

**Precedence Order** (highest to lowest):
1. **Function Variables**: `load(file, variables={...})`
2. **Document Variables**: From `__vars` in main document
3. **Accumulated Variables**: From `__vars` in imported files

This model supports complex scenarios like template chains where each level can define and override variables.

### 8. Loader Instance Capture Pattern

**Decision**: Capture loader instances using closure-based approach
**Problem**: PyYAML's `yaml.load()` creates loader instances internally, but the pipeline needs access to accumulated variables after parsing
**Solution**:
```python
# Closure-based instance capture in _create_loader()
_captured_loader_instance = None

class LoaderWrapper(ConfiguredSmartYAMLLoader):
    def __init__(self, stream):
        super().__init__(stream)
        nonlocal _captured_loader_instance
        _captured_loader_instance = self

LoaderWrapper._get_captured_instance = lambda: _captured_loader_instance
```

**Benefits**:
- Enables variable inheritance from imported templates
- Maintains clean separation between loader creation and instance access
- Solves the fundamental issue where template variables weren't available for expansion

**Critical for**: Template variable inheritance, where variables from `!template()` and `!import_yaml()` need to be accessible for `!expand` processing in the main document.

## Conclusion

The SmartYAML architecture successfully handles the complexity of extended YAML processing through:

- **Modular Design**: Clear separation of concerns across pipeline components
- **Security Integration**: Built-in protections against common attack vectors
- **Performance Optimization**: Caching, singleton patterns, and optimized operations
- **Rich Error Handling**: Comprehensive error context for debugging
- **Extensible Framework**: Registry-based constructors and pluggable components

The pipeline architecture enables maintainable, testable, and performant processing of complex YAML documents with SmartYAML's extended feature set. The design successfully balances functionality, security, and performance requirements for production use.
