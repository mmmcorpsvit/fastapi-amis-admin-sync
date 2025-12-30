#!/usr/bin/env python3
"""
Deep cleanup of the schema to remove all JsonSchemaObject references.

This script performs a comprehensive cleanup of the schema file to remove
all problematic JsonSchemaObject definitions and references.
"""
import json
import logging
from pathlib import Path
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "schema_simplified.json"


def deep_cleanup_schema():
    """
    Perform deep cleanup of the schema file.
    """
    logger.info("Loading schema for deep cleanup...")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    original_size = len(content)
    logger.info(f"Original schema size: {original_size:,} bytes")

    # Step 1: Remove JsonSchemaObject definitions entirely
    logger.info("Step 1: Removing JsonSchemaObject definitions...")
    content = re.sub(r'"JsonSchemaObject":\s*\{[^}]*\}', '', content)

    # Step 2: Remove JsonSchemaObject references
    logger.info("Step 2: Removing JsonSchemaObject references...")
    content = content.replace('"JsonSchemaObject"', '"object"')
    content = content.replace('JsonSchemaObject', 'object')

    # Step 3: Fix malformed structures
    logger.info("Step 3: Fixing malformed structures...")

    # Remove trailing commas before } or ]
    content = re.sub(r',(\s*[}\]])', r'\1', content)

    # Fix multiple consecutive commas
    content = re.sub(r',,+,', ',', content)

    # Fix empty objects
    content = re.sub(r'\{\s*,', '{', content)
    content = re.sub(r',\s*\}', '}', content)

    # Fix empty arrays
    content = re.sub(r'\[\s*,', '[', content)
    content = re.sub(r',\s*\]', ']', content)

    # Step 4: Ensure proper JSON structure
    logger.info("Step 4: Validating JSON structure...")
    try:
        schema = json.loads(content)
        logger.info("JSON structure is valid")
    except json.JSONDecodeError as e:
        logger.error(f"JSON validation failed: {e}")
        # Try to fix common issues
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        try:
            schema = json.loads(content)
            logger.info("JSON structure fixed and is now valid")
        except json.JSONDecodeError as e2:
            logger.error(f"Failed to fix JSON structure: {e2}")
            return False

    # Step 5: Add missing object definition if needed
    logger.info("Step 5: Ensuring object definition exists...")
    definitions = schema.get("definitions", {})
    if "object" not in definitions:
        definitions["object"] = {
            "type": "object",
            "additionalProperties": True
        }
        logger.info("Added object definition")

    # Step 6: Save cleaned schema
    logger.info("Step 6: Saving cleaned schema...")
    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    new_size = len(json.dumps(schema))
    logger.info(f"Cleaned schema size: {new_size:,} bytes")
    logger.info(f"Size change: {new_size - original_size:+,} bytes")

    return True


def main():
    """Main function for deep schema cleanup."""
    logger.info("=" * 60)
    logger.info("Deep Schema Cleanup")
    logger.info("=" * 60)

    success = deep_cleanup_schema()

    if success:
        logger.info("=" * 60)
        logger.info("✅ Deep schema cleanup completed successfully!")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("❌ Deep schema cleanup failed!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
