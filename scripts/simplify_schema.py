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

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "schema_translated.json"
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


def is_primitive_type(schema: Any) -> bool:
    """
    Check if a schema represents a primitive type (string, number, boolean, null).
    
    Args:
        schema: Schema object to check
    
    Returns:
        True if it's a primitive type
    """
    if isinstance(schema, dict):
        schema_type = schema.get("type")
        # Check for primitive types
        if schema_type in ("string", "number", "integer", "boolean", "null"):
            return True
        # Check for enum (usually strings)
        if "enum" in schema and schema_type == "string":
            return True
    return False


# Metadata keys to always preserve
METADATA_KEYS = {
    "description",
    "title",
    "default",
    "examples",
    "enum",
    "const",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "pattern",
    "format",
    "required",
    "readOnly",
    "writeOnly",
}


def resolve_true_property_from_allof(
    schema: Dict[str, Any],
    property_name: str,
    definitions: Dict[str, Any],
    visited: Set[str],
    max_depth: int,
    current_depth: int,
) -> Any:
    """
    Resolve a property defined as 'true' by looking it up in allOf base schemas.
    
    Args:
        schema: Current schema object (should have allOf)
        property_name: Name of the property to resolve
        definitions: All definitions
        visited: Set of visited definitions
        max_depth: Maximum recursion depth
        current_depth: Current depth
    
    Returns:
        Resolved property schema or None if not found
    """
    if "allOf" not in schema:
        return None
    
    # Look through allOf items
    for allof_item in schema.get("allOf", []):
        if not isinstance(allof_item, dict):
            continue
        
        # Check if this allOf item has the property
        if "properties" in allof_item:
            if property_name in allof_item["properties"]:
                prop_schema = allof_item["properties"][property_name]
                if prop_schema is not True:  # Found actual type definition
                    return simplify_schema_recursive(
                        prop_schema, definitions, visited, max_depth, current_depth + 1
                    )
        
        # Check $ref in allOf
        if "$ref" in allof_item:
            ref = allof_item["$ref"]
            def_name = ref.split("/")[-1] if "/" in ref else ref
            
            if def_name not in visited:
                visited.add(def_name)
                resolved = resolve_ref(ref, definitions)
                if resolved:
                    # Recursively check this resolved schema
                    if isinstance(resolved, dict):
                        # Check properties directly
                        if "properties" in resolved:
                            if property_name in resolved["properties"]:
                                prop_schema = resolved["properties"][property_name]
                                if prop_schema is not True:
                                    result = simplify_schema_recursive(
                                        prop_schema, definitions, visited, max_depth, current_depth + 1
                                    )
                                    visited.remove(def_name)
                                    return result
                        
                        # Check allOf in resolved schema
                        if "allOf" in resolved:
                            result = resolve_true_property_from_allof(
                                resolved, property_name, definitions, visited, max_depth, current_depth + 1
                            )
                            if result is not None:
                                visited.remove(def_name)
                                return result
                
                visited.remove(def_name)
    
    return None


def preserve_metadata(original: Dict[str, Any], result: Dict[str, Any]) -> None:
    """
    Copy all metadata keys from original to result.
    
    Args:
        original: Original schema object
        result: Result schema object to update
    """
    for key in METADATA_KEYS:
        if key in original and key not in result:
            result[key] = original[key]


def simplify_schema_recursive(
    obj: Any,
    definitions: Dict[str, Any],
    visited: Set[str],
    max_depth: int = 5,  # Increased from 3 to preserve more structure
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
        # Instead of returning generic object, try to preserve type info
        if isinstance(obj, dict):
            result = {}
            # Preserve type if available
            if "type" in obj:
                result["type"] = obj["type"]
            # Preserve metadata
            preserve_metadata(obj, result)
            # If it's an object type, use additionalProperties
            if result.get("type") == "object":
                result["additionalProperties"] = True
            else:
                result["additionalProperties"] = True
            return result
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
                # Instead of generic object, preserve what we can
                result = {"type": "object", "additionalProperties": True}
                preserve_metadata(obj, result)
                return result
            
            # Resolve reference with cycle detection
            visited_copy = visited.copy()
            visited_copy.add(def_name)
            
            resolved = resolve_ref(ref, definitions)
            if resolved:
                resolved_schema = simplify_schema_recursive(
                    resolved, definitions, visited_copy, max_depth, current_depth + 1
                )
                # Merge resolved schema with any metadata from the $ref
                if isinstance(resolved_schema, dict):
                    result = {}
                    result.update(resolved_schema)
                    preserve_metadata(obj, result)
                    return result
                return resolved_schema
            # Couldn't resolve, preserve $ref and metadata
            result = {"$ref": ref}
            preserve_metadata(obj, result)
            return result
        
        # Process other keys
        for key, value in obj.items():
            if key in ("allOf", "anyOf", "oneOf"):
                # Better handling of union types - preserve primitive types
                if isinstance(value, list) and len(value) > 0:
                    simplified_items = []
                    primitive_items = []
                    object_items = []
                    
                    # Process items and categorize them
                    for item in value:
                        simplified = simplify_schema_recursive(
                            item, definitions, visited, max_depth, current_depth + 1
                        )
                        
                        if is_primitive_type(simplified):
                            primitive_items.append(simplified)
                        elif isinstance(simplified, dict) and simplified.get("type") == "object":
                            object_items.append(simplified)
                        else:
                            simplified_items.append(simplified)
                    
                    # Preserve ALL primitive types
                    if primitive_items:
                        simplified_items.extend(primitive_items)
                    
                    # Preserve more object types (up to 5 instead of 2)
                    if object_items:
                        simplified_items.extend(object_items[:5])
                    
                    # If we still have nothing, keep first items
                    if not simplified_items:
                        simplified_items = [
                            simplify_schema_recursive(
                                item, definitions, visited, max_depth, current_depth + 1
                            )
                            for item in value[:5]  # Increased from 2
                        ]
                    
                    # Keep up to 10 items total (increased from 3)
                    result[key] = simplified_items[:10]
                    
            elif key == "properties":
                # Recursively process properties, preserving all
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
            elif key == "additionalProperties":
                if isinstance(value, dict):
                    result[key] = simplify_schema_recursive(
                        value, definitions, visited, max_depth, current_depth + 1
                    )
                else:
                    # Preserve boolean true/false for additionalProperties
                    result[key] = value
            elif key == "required":
                # Preserve required fields
                result[key] = value
            elif key in METADATA_KEYS:
                # Preserve all metadata
                result[key] = value
            elif key == "$ref":
                # Preserve $ref if we couldn't resolve it earlier
                result[key] = value
            else:
                # Preserve other keys (like "type", etc.)
                if isinstance(value, (dict, list)):
                    result[key] = simplify_schema_recursive(
                        value, definitions, visited, max_depth, current_depth + 1
                    )
                else:
                    result[key] = value
        
        # Ensure metadata is preserved even if not explicitly copied
        preserve_metadata(obj, result)
        
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
            max_depth=5,  # Increased from 3 to preserve more structure
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
    
    # Preserve other top-level keys
    for key in ["title", "description", "type"]:
        if key in schema:
            simplified_schema[key] = schema[key]
    
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
