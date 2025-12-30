#!/usr/bin/env python3
"""
Fix primitive types in anyOf arrays in BadgeObject and other definitions.

JSON Schema anyOf should contain schema objects, not primitive type strings.
This script converts primitive type strings to proper schema objects.
"""
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "schema_simplified.json"


def load_schema(path: Path) -> dict:
    """Load JSON schema from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_schema(schema: dict, path: Path) -> None:
    """Save JSON schema to file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)


def convert_primitive_types_to_schemas(any_of_array):
    """
    Convert primitive type strings to proper JSON Schema objects.

    Converts:
    - "string" -> {"type": "string"}
    - "number" -> {"type": "number"}
    - "boolean" -> {"type": "boolean"}
    - "integer" -> {"type": "integer"}
    - "array" -> {"type": "array"}
    - "object" -> {"type": "object"}
    - "null" -> {"type": "null"}
    """
    converted = []
    for item in any_of_array:
        if isinstance(item, str):
            # Convert primitive type string to schema object
            schema_obj = {"type": item}
            converted.append(schema_obj)
            logger.debug(f"Converted primitive '{item}' to schema object")
        elif isinstance(item, dict):
            # Already a schema object, keep as is
            converted.append(item)
        else:
            # Unknown type, keep as is for now
            converted.append(item)
    return converted


def fix_anyof_primitive_types(schema_obj: dict) -> tuple:
    """
    Fix anyOf arrays that contain primitive type strings.
    """
    if not isinstance(schema_obj, dict):
        return schema_obj, 0

    fixed_count = 0

    def fix_recursive(obj):
        nonlocal fixed_count
        if isinstance(obj, dict):
            # Check for anyOf arrays with primitive types
            if "anyOf" in obj and isinstance(obj["anyOf"], list):
                original_anyof = obj["anyOf"]
                converted_anyof = convert_primitive_types_to_schemas(original_anyof)

                # Check if anything was actually converted
                if converted_anyof != original_anyof:
                    obj["anyOf"] = converted_anyof
                    fixed_count += 1
                    logger.debug(f"Fixed anyOf with {len([x for x in original_anyof if isinstance(x, str)])} primitive types")

            # Recursively fix nested objects
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    fix_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                fix_recursive(item)

    fix_recursive(schema_obj)
    return schema_obj, fixed_count


def fix_badge_object_specific(schema: dict) -> dict:
    """
    Specifically fix BadgeObject definition.
    """
    definitions = schema.get("definitions", {})

    if "BadgeObject" in definitions:
        badge_obj = definitions["BadgeObject"]
        logger.info("Fixing BadgeObject definition...")

        # Fix the BadgeObject properties
        if "properties" in badge_obj:
            properties = badge_obj["properties"]

            # Fix text property
            if "text" in properties:
                text_def = properties["text"]
                if "anyOf" in text_def and isinstance(text_def["anyOf"], list):
                    text_def["anyOf"] = convert_primitive_types_to_schemas(text_def["anyOf"])
                    logger.debug("Fixed BadgeObject.text anyOf")

            # Fix offset property
            if "offset" in properties:
                offset_def = properties["offset"]
                if "items" in offset_def and isinstance(offset_def["items"], dict):
                    items_def = offset_def["items"]
                    if "anyOf" in items_def and isinstance(items_def["anyOf"], list):
                        items_def["anyOf"] = convert_primitive_types_to_schemas(items_def["anyOf"])
                        logger.debug("Fixed BadgeObject.offset.items anyOf")

    return schema


def main():
    """Main function to fix primitive types in anyOf arrays."""
    logger.info("=" * 60)
    logger.info("Fixing Primitive Types in anyOf Arrays")
    logger.info("=" * 60)

    # Load the schema
    logger.info(f"Loading schema from {SCHEMA_PATH}")
    schema = load_schema(SCHEMA_PATH)

    # Fix BadgeObject specifically
    logger.info("Fixing BadgeObject definition...")
    schema = fix_badge_object_specific(schema)

    # Fix general anyOf primitive type issues
    logger.info("Fixing general anyOf primitive type issues...")
    fixed_schema, general_fixes = fix_anyof_primitive_types(schema)
    logger.info(f"Fixed {general_fixes} anyOf arrays with primitive types")

    # Save the fixed schema
    logger.info(f"Saving fixed schema to {SCHEMA_PATH}")
    save_schema(fixed_schema, SCHEMA_PATH)

    logger.info("=" * 60)
    logger.info("✅ Primitive types in anyOf arrays fixed!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
