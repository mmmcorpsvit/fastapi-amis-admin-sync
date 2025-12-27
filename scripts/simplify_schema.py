#!/usr/bin/env python3
"""
Preprocess AMIS schema.json to make it compatible with datamodel-code-generator.

This script:
1. Resolves $ref references to inline definitions
2. Removes circular references
3. Simplifies deep nesting
4. Extracts top-level component schemas
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "schema.json"
OUTPUT_PATH = Path(__file__).parent.parent / "schema" / "schema_simplified.json"


def load_schema(path: Path) -> Dict[str, Any]:
    """Load JSON schema from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_definitions(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Extract all definitions from schema."""
    return schema.get("definitions", {})


def resolve_ref(ref: str, definitions: Dict[str, Any]) -> Any:
    """
    Resolve a $ref reference.
    
    Args:
        ref: Reference string like "#/definitions/PageSchema"
        definitions: Dictionary of definitions
    
    Returns:
        The referenced definition or None if circular
    """
    if not ref.startswith("#/definitions/"):
        return None
    
    def_name = ref.split("/")[-1]
    return definitions.get(def_name)


def simplify_schema_recursive(
    obj: Any,
    definitions: Dict[str, Any],
    visited: Set[str],
    max_depth: int = 3,
    current_depth: int = 0,
) -> Any:
    """
    Recursively simplify schema by resolving refs and limiting depth.
    
    Args:
        obj: Current schema object
        definitions: All definitions
        visited: Set of visited definition names (to detect cycles)
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth
    
    Returns:
        Simplified schema object
    """
    if current_depth > max_depth:
        # Stop deep recursion - return simple type
        return {"type": "object", "additionalProperties": True}
    
    if isinstance(obj, dict):
        result = {}
        
        # Handle $ref
        if "$ref" in obj:
            ref = obj["$ref"]
            def_name = ref.split("/")[-1] if "/" in ref else ref
            
            # Detect circular reference
            if def_name in visited:
                logger.debug(f"Circular ref detected: {def_name}")
                return {"type": "object", "additionalProperties": True}
            
            # Resolve reference with cycle detection
            visited_copy = visited.copy()
            visited_copy.add(def_name)
            
            resolved = resolve_ref(ref, definitions)
            if resolved:
                return simplify_schema_recursive(
                    resolved, definitions, visited_copy, max_depth, current_depth + 1
                )
            return obj
        
        # Process other keys
        for key, value in obj.items():
            if key in ("allOf", "anyOf", "oneOf"):
                # Simplify union types - just take the first option
                if isinstance(value, list) and len(value) > 0:
                    result[key] = [
                        simplify_schema_recursive(
                            item, definitions, visited, max_depth, current_depth + 1
                        )
                        for item in value[:2]  # Limit to first 2 items
                    ]
            elif key == "properties":
                # Recursively process properties
                result[key] = {
                    prop_key: simplify_schema_recursive(
                        prop_val, definitions, visited, max_depth, current_depth + 1
                    )
                    for prop_key, prop_val in value.items()
                }
            elif key == "items":
                result[key] = simplify_schema_recursive(
                    value, definitions, visited, max_depth, current_depth + 1
                )
            elif key == "additionalProperties" and isinstance(value, dict):
                result[key] = simplify_schema_recursive(
                    value, definitions, visited, max_depth, current_depth + 1
                )
            else:
                result[key] = value
        
        return result
    
    elif isinstance(obj, list):
        return [
            simplify_schema_recursive(
                item, definitions, visited, max_depth, current_depth + 1
            )
            for item in obj
        ]
    
    return obj


def create_simplified_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a simplified version of the AMIS schema.
    
    Args:
        schema: Original AMIS schema
    
    Returns:
        Simplified schema suitable for datamodel-code-generator
    """
    definitions = extract_definitions(schema)
    
    logger.info(f"Found {len(definitions)} definitions in schema")
    
    # Create simplified definitions
    simplified_defs = {}
    
    # Process each definition with cycle detection
    for def_name, def_obj in definitions.items():
        logger.debug(f"Processing definition: {def_name}")
        
        simplified = simplify_schema_recursive(
            def_obj,
            definitions,
            visited=set([def_name]),  # Mark current def as visited
            max_depth=3,  # Limit depth to prevent deep recursion
        )
        
        simplified_defs[def_name] = simplified
    
    # Create new schema with simplified definitions
    simplified_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": simplified_defs,
    }
    
    # Add root reference if exists
    if "$ref" in schema:
        simplified_schema["$ref"] = schema["$ref"]
    
    return simplified_schema


def main():
    """Main function to simplify schema."""
    logger.info("=" * 60)
    logger.info("AMIS Schema Simplification")
    logger.info("=" * 60)
    
    # Load original schema
    logger.info(f"Loading schema from {SCHEMA_PATH}")
    schema = load_schema(SCHEMA_PATH)
    
    original_size = len(json.dumps(schema))
    logger.info(f"Original schema size: {original_size:,} bytes")
    
    # Simplify schema
    logger.info("Simplifying schema...")
    simplified = create_simplified_schema(schema)
    
    # Save simplified schema
    logger.info(f"Saving simplified schema to {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(simplified, f, indent=2, ensure_ascii=False)
    
    simplified_size = len(json.dumps(simplified))
    logger.info(f"Simplified schema size: {simplified_size:,} bytes")
    logger.info(f"Size reduction: {(1 - simplified_size/original_size)*100:.1f}%")
    
    logger.info("=" * 60)
    logger.info("✅ Schema simplification complete!")
    logger.info(f"Output: {OUTPUT_PATH}")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
