"""
SmartYAML - Extended YAML format with custom directives
"""

from .loader import SmartYAMLLoader
from .exceptions import (
    SmartYAMLError, SmartYAMLFileNotFoundError, InvalidPathError,
    EnvironmentVariableError, TemplatePathError, Base64Error,
    ResourceLimitError, RecursionLimitError, ConstructorError
)
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union

__version__ = "0.1.0"
__all__ = [
    'load', 'loads', 'dump', 'SmartYAMLLoader', 'SmartYAMLError',
    'SmartYAMLFileNotFoundError', 'InvalidPathError', 'EnvironmentVariableError',
    'TemplatePathError', 'Base64Error', 'ResourceLimitError', 
    'RecursionLimitError', 'ConstructorError'
]


def load(stream: Union[str, Path], base_path: Optional[Union[str, Path]] = None, 
         template_path: Optional[Union[str, Path]] = None, max_file_size: Optional[int] = None,
         max_recursion_depth: Optional[int] = None) -> Any:
    """
    Load SmartYAML from file or string.
    
    Args:
        stream: YAML content as string or Path to file
        base_path: Base directory for resolving relative paths (defaults to file's directory)
        template_path: Base directory for templates (overrides SMARTYAML_TMPL env var)
        max_file_size: Maximum file size in bytes (default: 10MB)
        max_recursion_depth: Maximum import recursion depth (default: 10)
    
    Returns:
        Parsed YAML data with SmartYAML directives processed
    """
    if isinstance(stream, (str, Path)) and Path(stream).exists():
        # Load from file
        file_path = Path(stream).resolve()
        if base_path is None:
            base_path = file_path.parent
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        # Load from string
        content = str(stream)
        if base_path is None:
            base_path = Path.cwd()
    
    # Create a custom loader class with paths and limits set
    class ConfiguredSmartYAMLLoader(SmartYAMLLoader):
        def __init__(self, stream):
            super().__init__(stream)
            self.base_path = Path(base_path).resolve()
            if template_path:
                self.template_path = Path(template_path).resolve()
            self.import_stack = set()
            self.max_file_size = max_file_size
            self.max_recursion_depth = max_recursion_depth
    
    return yaml.load(content, Loader=ConfiguredSmartYAMLLoader)


def loads(content: str, base_path: Optional[Union[str, Path]] = None, 
          template_path: Optional[Union[str, Path]] = None, max_file_size: Optional[int] = None,
          max_recursion_depth: Optional[int] = None) -> Any:
    """
    Load SmartYAML from string content.
    
    Args:
        content: YAML content as string
        base_path: Base directory for resolving relative paths (defaults to current directory)
        template_path: Base directory for templates (overrides SMARTYAML_TMPL env var)
        max_file_size: Maximum file size in bytes (default: 10MB)
        max_recursion_depth: Maximum import recursion depth (default: 10)
    
    Returns:
        Parsed YAML data with SmartYAML directives processed
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Create a custom loader class with paths and limits set
    class ConfiguredSmartYAMLLoader(SmartYAMLLoader):
        def __init__(self, stream):
            super().__init__(stream)
            self.base_path = Path(base_path).resolve()
            if template_path:
                self.template_path = Path(template_path).resolve()
            self.import_stack = set()
            self.max_file_size = max_file_size
            self.max_recursion_depth = max_recursion_depth
    
    return yaml.load(content, Loader=ConfiguredSmartYAMLLoader)


def dump(data: Any, stream: Optional[Union[str, Path]] = None, **kwargs) -> Optional[str]:
    """
    Dump data to YAML format.
    
    Args:
        data: Data to serialize
        stream: Output file path or None to return string
        **kwargs: Additional arguments for yaml.dump
    
    Returns:
        YAML string if stream is None, otherwise None
    """
    kwargs.setdefault('default_flow_style', False)
    kwargs.setdefault('allow_unicode', True)
    
    if stream is None:
        return yaml.dump(data, **kwargs)
    else:
        with open(stream, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, **kwargs)