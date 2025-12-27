"""
AMIS module - Auto-generated Pydantic models.

This module provides type-safe Pydantic models for AMIS components,
automatically generated from the official AMIS JSON Schema.

Models are generated from a simplified version of the schema to avoid
recursion issues. The simplification process:
1. Resolves circular $ref references
2. Limits nesting depth to 3 levels
3. Maintains all component types and properties

To regenerate models:
    python update_models.py
"""

# Use auto-generated models by default (452 models from simplified schema)
try:
    from .auto_generated_models import *
except ImportError:
    # Fallback to manual models if auto-generated not available
    import warnings

    warnings.warn(
        "Auto-generated models not found. Run 'python update_models.py' to generate them. "
        "Falling back to manual models.",
        ImportWarning,
    )
    from .generated_models import *
