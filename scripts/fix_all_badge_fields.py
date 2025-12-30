#!/usr/bin/env python3
"""
Comprehensive fix for ALL badge field definitions across the entire schema.

This script fixes ALL instances of malformed badge fields, not just BadgeObject.
It handles:
1. TplSchema badge fields
2. All other schema definitions that have badge fields
3. Converts any malformed structures to valid JSON Schema
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


def create_valid_badge_object():
    """Create a valid BadgeObject schema."""
    return {
        "type": "object",
        "properties": {
            "text": {
                "description": "文本content",
                "anyOf": [
                    {"type": "string"},
                    {"type": "number"},
                    {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    {"type": "object", "additionalProperties": True}
                ]
            },
            "level": {
                "type": "string",
                "enum": ["success", "warning", "danger", "info", "primary"]
            },
            "visible": {
                "anyOf": [
                    {"type": "boolean"},
                    {"type": "string"}
                ]
            },
            "className": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "object", "additionalProperties": True}
                ]
            },
            "position": {
                "type": "string",
                "enum": ["top-right", "top-left", "bottom-right", "bottom-left"]
            },
            "offset": {
                "type": "array",
                "items": {
                    "anyOf": [
                        {"type": "number"},
                        {"type": "string"}
                    ]
                },
                "minItems": 2,
                "maxItems": 2
            },
            "size": {"type": "number"},
            "mode": {
                "type": "string",
                "enum": ["text", "dot", "ribbon"]
            },
            "overflowCount": {"type": "number"},
            "visibleOn": {"type": "string"},
            "animation": {"type": "boolean"},
            "style": {"type": "object"},
            "styleVars": {"type": "object"}
        },
        "additionalProperties": True
    }


def fix_badge_field_in_properties(properties: dict) -> int:
    """
    Fix badge field in a properties dictionary.
    Returns the number of fixes applied.
    """
    fixes_applied = 0

    if "badge" in properties:
        badge_def = properties["badge"]

        # Check if it's a malformed definition that needs fixing
        needs_fix = False

        if badge_def is True:
            # Boolean true should be replaced with proper object
            needs_fix = True
        elif isinstance(badge_def, dict):
            # Check for malformed structures
            if "type" in badge_def and isinstance(badge_def["type"], list):
                # Malformed: "type": [...] should be "anyOf": [...]
                needs_fix = True
            elif "properties" in badge_def:
                # Check nested properties for malformed anyOf
                badge_props = badge_def["properties"]
                if "text" in badge_props and isinstance(badge_props["text"], dict):
                    text_def = badge_props["text"]
                    if "type" in text_def and isinstance(text_def["type"], list):
                        needs_fix = True
                if "offset" in badge_props and isinstance(badge_props["offset"], dict):
                    offset_def = badge_props["offset"]
                    if "items" in offset_def and isinstance(offset_def["items"], dict):
                        items_def = offset_def["items"]
                        if "type" in items_def and isinstance(items_def["type"], dict):
                            needs_fix = True

        if needs_fix:
            # Replace with valid BadgeObject
            properties["badge"] = create_valid_badge_object()
            fixes_applied += 1
            logger.debug("Fixed malformed badge field")

    return fixes_applied


def fix_all_badge_fields(schema: dict) -> int:
    """
    Fix ALL badge field definitions across the entire schema.
    Returns the total number of fixes applied.
    """
    total_fixes = 0
    definitions = schema.get("definitions", {})

    for def_name, def_obj in definitions.items():
        if not isinstance(def_obj, dict):
            continue

        # Handle allOf structures
        if "allOf" in def_obj:
            for allof_item in def_obj["allOf"]:
                if isinstance(allof_item, dict) and "properties" in allof_item:
                    fixes = fix_badge_field_in_properties(allof_item["properties"])
                    total_fixes += fixes
                    if fixes > 0:
                        logger.info(f"Fixed {fixes} badge fields in {def_name}.allOf")

        # Handle direct properties
        if "properties" in def_obj:
            fixes = fix_badge_field_in_properties(def_obj["properties"])
            total_fixes += fixes
            if fixes > 0:
                logger.info(f"Fixed {fixes} badge fields in {def_name}.properties")

    # Also check root level properties
    if "properties" in schema:
        fixes = fix_badge_field_in_properties(schema["properties"])
        total_fixes += fixes
        if fixes > 0:
            logger.info(f"Fixed {fixes} badge fields in root properties")

    return total_fixes


def main():
    """Main function to fix all badge field definitions."""
    logger.info("=" * 60)
    logger.info("Comprehensive Badge Fields Fix")
    logger.info("=" * 60)

    # Load the schema
    logger.info(f"Loading schema from {SCHEMA_PATH}")
    schema = load_schema(SCHEMA_PATH)

    # Fix all badge field definitions
    logger.info("Fixing all badge field definitions...")
    total_fixes = fix_all_badge_fields(schema)
    logger.info(f"Total badge fields fixed: {total_fixes}")

    # Save the fixed schema
    logger.info(f"Saving fixed schema to {SCHEMA_PATH}")
    save_schema(schema, SCHEMA_PATH)

    logger.info("=" * 60)
    logger.info("✅ All badge field definitions fixed!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
