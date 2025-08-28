"""
SmartYAML Processing Pipeline

The core 6-stage processing pipeline as defined in SPECS-v1.md:
1. Initial Parsing & Version Check
2. Metadata Resolution (__vars, __template, __schema)
3. Directive Resolution (recursive, depth-first)
4. Variable Expansion ({{...}})
5. Schema Validation
6. Final Output
"""

from .processor import SmartYAMLProcessor

__all__ = ["SmartYAMLProcessor"]
