# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

SmartYAML is an extended YAML format library that adds custom directives for file imports, environment variables, conditional processing, and templates. It extends standard YAML with powerful features while maintaining full compatibility.

## Key Commands

### Testing
```bash
python -m pytest                    # Run all tests
python -m pytest tests/test_imports.py  # Run specific test file
python -m pytest -v                 # Verbose test output
python -m pytest --cov=smartyaml    # Run with coverage (requires pytest-cov)
```

### Installation & Setup
```bash
pip install -e .                    # Install in development mode
pip install -e ".[dev]"            # Install with development dependencies
pip install -e ".[test]"           # Install with testing dependencies
```

### Package Building
```bash
python -m build                    # Build distribution packages (requires build package)
pip install build                  # Install build tool if needed
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

### Core Components

- **smartyaml/__init__.py**: Main API with `load()`, `loads()`, and `dump()` functions
- **smartyaml/loader.py**: `SmartYAMLLoader` class that extends `yaml.SafeLoader` with custom constructors
- **smartyaml/constructors/**: Directory containing all custom YAML constructors:
  - `imports.py`: `!import` and `!import_yaml` for file inclusion
  - `environment.py`: `!env` for environment variables
  - `conditional.py`: `!include_if` and `!include_yaml_if` for conditional includes
  - `templates.py`: `!template` for centralized template loading
  - `encoding.py`: `!base64` and `!base64_decode` for encoding operations
- **smartyaml/merge.py**: YAML merging logic for `!import_yaml` with local overrides
- **smartyaml/exceptions.py**: Custom exception hierarchy
- **smartyaml/utils/**: Utility modules for file operations, path resolution, and validation

### SmartYAML Directives

The library supports these custom YAML tags:
- `!import(file)`: Load text file content as string
- `!import_yaml(file)`: Load and merge YAML files with local overrides
- `!env(VAR, default)`: Read environment variables with optional defaults
- `!include_if(condition, file)`: Conditional text file inclusion
- `!include_yaml_if(condition, file)`: Conditional YAML file inclusion
- `!template(name)`: Load templates from `$SMARTYAML_TMPL` directory
- `!base64(data)` / `!base64_decode(data)`: Base64 encoding/decoding

### Metadata Fields

SmartYAML automatically removes fields prefixed with `__` (double underscore) from the final parsed result. These metadata fields serve as annotations and documentation within YAML files but don't appear in the loaded data structure.

**Features:**
- Fields starting with `__` are removed during post-processing
- Metadata fields can contain SmartYAML directives (processed then removed)
- Removal works recursively through nested structures and lists
- Can be disabled by setting `remove_metadata=False` in `load()` or `loads()`

**Examples:**
```yaml
# Input YAML
app_name: "MyApp"
__version: "1.2.3"           # Metadata - removed
__build_info: !env(BUILD_DATE) # Metadata with directive - removed
database:
  host: "localhost"
  __notes: "Primary DB"      # Nested metadata - removed

# Resulting data structure
{
  'app_name': 'MyApp',
  'database': {
    'host': 'localhost'
  }
}
```

### Testing Structure

Tests are organized by constructor type:
- `tests/test_imports.py`: File import functionality
- `tests/test_environment.py`: Environment variable handling
- `tests/test_conditional.py`: Conditional inclusion logic
- `tests/test_encoding.py`: Base64 encoding/decoding
- `tests/test_metadata.py`: Metadata field removal functionality
- `tests/test_advanced_features.py`: Advanced testing scenarios
- `tests/fixtures/`: Test YAML files and sample data

### Security Features

- File size limits (default 10MB, configurable)
- Import recursion depth limits (default 10 levels)
- Path traversal protection
- Circular import detection
- Safe YAML parsing (extends SafeLoader)
- Environment variable access only (no code execution)

## Development Notes

- The project uses modern packaging with `pyproject.toml` (PEP 517/518)
- PyYAML 5.1+ as core dependency
- Python 3.7+ required for pathlib and f-string support
- All custom constructors receive a `loader` and `node` parameter
- Base paths are resolved relative to the main YAML file's directory
- Template paths can be set via `SMARTYAML_TMPL` environment variable
- Error handling provides detailed context through custom exception classes
- Comprehensive type hints with `py.typed` marker

## Important File Locations

- Core API: `smartyaml/__init__.py` (load function)
- Loader setup: `smartyaml/loader.py` (constructor registration)
- Package config: `pyproject.toml` (modern packaging configuration)
- Type definitions: `smartyaml/type_annotations.py`
- Testing utilities: `smartyaml/testing_utils.py`
- Performance optimizations: `smartyaml/performance_optimizations.py`
- Registry system: `smartyaml/registry.py`
- Error context: `smartyaml/error_context.py`

## Build and Quality Assurance

Always run these commands before committing:
1. `python -m pytest` - Ensure all tests pass
2. `black smartyaml/` - Format code
3. `isort smartyaml/` - Sort imports
4. `flake8 smartyaml/` - Lint code
5. `mypy smartyaml/` - Type check
6. `python -m build` - Verify package builds cleanly