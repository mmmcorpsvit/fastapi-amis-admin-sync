#!/usr/bin/env python3
"""
Comprehensive fix for all JsonSchemaObject validation issues.

This script removes all JsonSchemaObject definitions from the schema
and replaces them with proper type definitions.
"""
import json
import logging
from pathlib import Path
import re

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


def remove_all_json_schema_objects(schema_str: str) -> str:
    """
    Remove all JsonSchemaObject references and definitions from the schema string.
    """
    # Remove JsonSchemaObject definitions
    schema_str = re.sub(r'"JsonSchemaObject":\s*{[^}]*}', '', schema_str)

    # Replace JsonSchemaObject references with "object"
    schema_str = schema_str.replace('"JsonSchemaObject"', '"object"')

    # Fix any malformed structures that might result
    schema_str = re.sub(r',\s*}', '}', schema_str)
    schema_str = re.sub(r',\s*]', ']', schema_str)

    return schema_str


def fix_all_json_schema_object_issues(schema: dict) -> dict:
    """
    Fix all JsonSchemaObject validation issues in the schema.
    """
    # Convert to string for processing
    schema_str = json.dumps(schema)

    # Remove all JsonSchemaObject references
    logger.info("Removing all JsonSchemaObject definitions and references...")
    fixed_schema_str = remove_all_json_schema_objects(schema_str)

    # Parse back to JSON
    try:
        fixed_schema = json.loads(fixed_schema_str)
        logger.info("Successfully removed JsonSchemaObject issues")
        return fixed_schema
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse fixed schema: {e}")
        # If parsing fails, try a more conservative approach
        logger.info("Trying conservative approach...")
        return fix_json_schema_objects_conservative(schema)


def fix_json_schema_objects_conservative(schema: dict) -> dict:
    """
    Conservative approach to fix JsonSchemaObject issues by removing
    the definition entirely and letting the schema be more permissive.
    """
    definitions = schema.get("definitions", {})

    # Remove JsonSchemaObject definition if it exists
    if "JsonSchemaObject" in definitions:
        logger.info("Removing JsonSchemaObject definition...")
        del definitions["JsonSchemaObject"]

    # Replace any remaining references with "object"
    def replace_refs(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and value == "#/definitions/JsonSchemaObject":
                    obj[key] = "#/definitions/object"
                elif isinstance(value, (dict, list)):
                    replace_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                replace_refs(item)

    replace_refs(schema)

    # Also add a simple object definition if it doesn't exist
    if "object" not in definitions:
        logger.info("Adding simple object definition...")
        definitions["object"] = {
            "type": "object",
            "additionalProperties": True
        }

    return schema


def main():
    """Main function to fix all JsonSchemaObject issues."""
    logger.info("=" * 60)
    logger.info("Fixing All JsonSchemaObject Issues")
    logger.info("=" * 60)

    # Load the problematic schema
    logger.info(f"Loading schema from {SCHEMA_PATH}")
    schema = load_schema(SCHEMA_PATH)

    # Fix all JsonSchemaObject issues
    logger.info("Fixing JsonSchemaObject validation issues...")
    fixed_schema = fix_all_json_schema_object_issues(schema)

    # Save the fixed schema
    logger.info(f"Saving fixed schema to {SCHEMA_PATH}")
    save_schema(fixed_schema, SCHEMA_PATH)

    logger.info("=" * 60)
    logger.info("✅ All JsonSchemaObject issues fixed!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
