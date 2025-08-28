# AGENTS.md

This file provides comprehensive guidance to AI agents when working with code in this repository.

## Project Overview

SmartYAML is a powerful YAML processing library that extends standard YAML parsing with advanced features for templating, variable substitution, environment variable integration, conditional logic, and schema validation. It processes input YAML files through a comprehensive pipeline to resolve all special constructs and output plain YAML data structures.

**Key Concepts:**
- **Metadata Fields**: Fields prefixed with `__` (e.g., `__vars`, `__template`, `__schema`) define processing behavior
- **Directives**: Custom YAML tags (e.g., `!env`, `!include`, `!merge`) trigger specific processing behaviors
- **Processing Pipeline**: 6-stage processing (parsing → metadata → templates → directives → variables → validation)
- **Variable Substitution**: Jinja-like syntax (`{{var}}`) with inheritance and precedence
- **Template System**: Powerful inheritance and overlay system with `__template`
- **Schema Validation**: JSON Schema validation of final resolved YAML

## Key Commands

### Testing
```bash
python -m pytest                    # Run all tests (230+ tests)
python -m pytest tests/test_directives.py  # Run specific test module
python -m pytest -v                 # Verbose test output
python -m pytest --cov=smartyaml    # Run with coverage (requires pytest-cov)
python -m pytest -k "env"           # Run tests matching pattern
```

### Installation & Setup
```bash
pip install -e .                    # Install in development mode
pip install -e ".[dev]"            # Install with development dependencies
pip install -e ".[test]"           # Install with testing dependencies
```

### Package Building
```bash
python -m build                     # Build distribution packages (requires build package)
pip install build                   # Install build tool if needed
python -m build --sdist            # Build source distribution only
python -m build --wheel            # Build wheel only
```

### Code Quality Tools
```bash
black smartyaml/                   # Format code with Black
isort smartyaml/                   # Sort imports with isort
flake8 smartyaml/                  # Lint code with flake8
mypy smartyaml/                    # Type check with mypy
```

### Running Examples
```bash
cd examples/
python -c "import smartyaml; print(smartyaml.load('basic_example.yaml'))"
```

## Architecture Overview

SmartYAML follows a modular, pipeline-based architecture with clear separation of concerns:

### Core Components

**Main API (`smartyaml/__init__.py`)**
- `load()`, `loads()`, `load_file()` - Primary loading functions
- `load_secure()`, `load_with_templates()` - Convenience functions
- Complete exception hierarchy export

**Configuration System (`smartyaml/config/`)**
- `core.py` - Core configuration classes (SecurityConfig, PathConfig, etc.)
- `main.py` - Main SmartYAMLConfig class
- `builder.py` - Fluent configuration builder with presets
- `security.py`, `processing.py`, `performance.py`, `paths.py` - Modular config components

**Processing Pipeline (`smartyaml/pipeline/`)**
- `processor.py` - Main SmartYAMLProcessor orchestrating the 6-stage pipeline
- `parser.py` - Stage 1: YAML parsing with custom constructors (SmartYAMLLoader)
- `metadata.py` - Stage 2: Metadata resolution (`__vars`, `__schema`, etc.)
- `templates.py` - Stage 3: Template processing and inheritance
- `directives.py` - Stage 4: Directive processing (recursive, depth-first)
- `variables.py` - Stage 5: Variable expansion with Jinja-like syntax
- `validator.py` - Stage 6: Schema validation using JSON Schema

**Error Handling System (`smartyaml/errors/`)**
- `context.py` - ErrorContext and ErrorContextBuilder for standardized error reporting
- `helpers.py` - Validation helpers and error utilities
- Integrated with all pipeline components for consistent error reporting

**Utilities (`smartyaml/utils/`)**
- `merge.py` - Unified DeepMerger with configurable strategies
- `recursion.py` - RecursiveProcessor utilities with cycle detection
- `validation.py` - Common validation helpers

### SmartYAML Processing Pipeline

The library processes YAML through 6 sequential stages:

**Stage 1: Initial Parsing & Version Check**
- Parse YAML with custom constructors for directives
- Extract metadata fields (`__*`)
- Check `__version` compatibility
- Build directive AST for later processing

**Stage 2: Metadata Resolution** 
- Resolve `__vars` (process directives within, merge with external variables)
- Resolve `__template` (load and prepare template inheritance)
- Resolve `__schema` (process directives to build JSON Schema)

**Stage 3: Template Processing**
- Load template files recursively
- Apply overlay logic (deep merge vs replace)
- Inherit variables from templates with proper precedence

**Stage 4: Directive Processing (Recursive, Depth-First)**
- Process all directives in dependency order
- Handle file inclusion, environment variables, conditionals, merging
- Recursive processing of included files through stages 1-4

**Stage 5: Variable Expansion**
- Global `{{var}}` substitution using resolved variables
- Support for nested variables and defaults
- Jinja-like syntax with proper escaping

**Stage 6: Schema Validation & Final Output**
- Validate against resolved `__schema` using jsonschema
- Remove metadata fields
- Return final resolved YAML structure

### SmartYAML Directives (SPECS-v1.md)

**Environment Variables:**
- `!env ['VAR_NAME', 'default']` - Environment variable access
- `!secret ['SECRET_VAR', 'default']` - Same as !env (future: secure stores)

**File Inclusion:**
- `!include 'file.yaml'` - Include and process file content
- `!include_if ['CONDITION', 'file.yaml']` - Conditional inclusion
- `!include_yaml 'file.yaml'` - Include raw YAML (no directive processing)
- `!include_yaml_if ['CONDITION', 'file.yaml']` - Conditional raw YAML

**Template System:**
- `!template 'template.name'` - Load from template directory
- `!template_if ['CONDITION', 'template.name']` - Conditional template loading

**Data Operations:**
- `!merge [item1, item2, ...]` - Deep merge multiple structures
- `!concat [item1, item2, ...]` - Concatenate arrays/lists

**Variable Operations:**
- `!expand 'text with {{variables}}'` - String expansion with variables

**Conditionals:**
- `!if ['ENV_VAR', value]` - Conditional inclusion
- `!switch ['ENV_VAR', [cases...]]` - Multi-way conditionals

### Metadata Fields

**Core Metadata (automatically removed from final output):**
- `__version: "1.0.0"` - Version compatibility check
- `__vars: {}` - Variable definitions with inheritance
- `__template: {}` - Template inheritance configuration  
- `__schema: {}` - JSON Schema for validation

**Variable System:**
Variables support inheritance and precedence:
1. Function parameters (highest precedence)
2. Document `__vars` (medium precedence) 
3. Template `__vars` (lowest precedence)

**Template System:**
```yaml
__template:
  path: 'templates/base.yaml'  # Direct path
  use: 'base.config'          # Template name (loads from template_path)
  overlay: true               # true = merge, false = replace
```

### Security Features

- **Path Sanitization**: All file paths normalized and validated
- **Directory Restrictions**: Prevent path traversal attacks
- **File Size Limits**: Configurable limits (default 10MB)
- **Recursion Protection**: Max depth limits prevent infinite recursion
- **Cycle Detection**: Prevents circular includes
- **Environment Variable Controls**: Whitelist/blacklist support
- **Sandbox Mode**: Restricts file and environment access
- **No Code Execution**: Safe YAML parsing only

### Testing Structure

Tests are comprehensively organized:
- `tests/test_directives.py` - All directive functionality
- `tests/test_errors.py` - Error handling and exceptions
- `tests/test_metadata.py` - Metadata field processing
- `tests/test_templates.py` - Template inheritance system
- `tests/test_variables.py` - Variable expansion system
- `tests/test_integration.py` - End-to-end scenarios
- `tests/test_security.py` - Security features
- `tests/test_processing_order.py` - Pipeline stage validation
- `tests/test_edge_cases.py` - Edge cases and error conditions
- `tests/fixtures/` - Test YAML files and sample data

### Error Handling

SmartYAML provides a comprehensive exception hierarchy:
- `SmartYAMLError` - Base exception with file/field context
- `VersionMismatchError` - Version compatibility issues
- `FileNotFoundError` - Missing referenced files
- `DirectiveSyntaxError` - Invalid directive syntax
- `VariableNotFoundError` - Undefined variable references
- `RecursionLimitExceededError` - Recursion/cycle detection
- `MergeConflictError` - Type conflicts in merging
- `SecurityViolationError` - Security policy violations
- `SchemaValidationError` - JSON Schema validation failures

## Development Notes

- **Modern Architecture**: Modular design with clear separation of concerns
- **Type Safety**: Comprehensive type hints throughout codebase
- **Error Context**: Standardized error reporting with file/field context
- **Configuration**: Fluent configuration builder with validation
- **Performance**: Optimized recursive processing with caching support
- **Security First**: Multiple layers of security controls
- **Extensibility**: Plugin system for custom directives (future)

### Important File Locations

**Core Files:**
- Main API: `smartyaml/__init__.py`
- Configuration: `smartyaml/config/main.py` (SmartYAMLConfig)
- Processor: `smartyaml/pipeline/processor.py` (main orchestrator)
- Package config: `pyproject.toml`

**Pipeline Components:**
- Parser: `smartyaml/pipeline/parser.py` (SmartYAMLLoader)
- Directives: `smartyaml/pipeline/directives.py` (DirectiveProcessor)  
- Variables: `smartyaml/pipeline/variables.py` (VariableProcessor)
- Templates: `smartyaml/pipeline/templates.py` (TemplateProcessor)

**Support Systems:**
- Error handling: `smartyaml/errors/` (context, helpers)
- Utilities: `smartyaml/utils/` (merge, validation, recursion)
- Configuration: `smartyaml/config/` (modular config system)

## Build and Quality Assurance

Always run these commands before committing:
1. `python -m pytest` - Ensure all tests pass (230+ tests)
2. `black smartyaml/` - Format code with Black
3. `isort smartyaml/` - Sort imports with isort  
4. `flake8 smartyaml/` - Lint code with flake8
5. `mypy smartyaml/` - Type check with mypy
6. `python -m build` - Verify package builds cleanly

## Implementation Standards

- **Follow SPECS-v1.md**: Complete specification compliance
- **Modern Python**: Use type hints, pathlib, f-strings (Python 3.7+)
- **Code Quality**: Black formatting, isort imports, flake8 linting, mypy typing
- **Testing**: Maintain 230+ passing tests, add tests for new features
- **Security**: Security-first approach with multiple validation layers
- **Error Handling**: Use standardized error context system
- **Documentation**: Comprehensive docstrings and type hints

## Package Configuration

- **Package Name**: `pysmartyaml` (PyPI availability)
- **Python Support**: 3.9+ (due to advanced type hints)
- **Dependencies**: PyYAML 5.1+, minimal external dependencies
- **Build System**: Modern `pyproject.toml` configuration
- **Testing**: pytest with coverage, xdist for parallel execution