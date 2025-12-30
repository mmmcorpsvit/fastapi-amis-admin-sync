#!/usr/bin/env python3
"""
Comprehensive fix for badge validation issues in the simplified schema.

This script specifically targets the TplSchema and fixes all nested
badge field definitions that are causing validation errors.
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


def fix_tpl_schema_badge_field(schema_obj: dict) -> dict:
    """
    Fix the specific badge field in TplSchema that's causing validation errors.

    The error occurs at: allOf.1.properties.badge.JsonSchemaObject
    This means there's a nested structure within the badge field that needs fixing.
    """
    if not isinstance(schema_obj, dict):
        return schema_obj

    # Create a proper BadgeObject structure
    badge_object = {
        "type": "object",
        "properties": {
            "text": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string"}},
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
                "anyOf": [
                    {"type": "array", "items": {"type": ["number", "string"]}},
                    {"type": "object", "additionalProperties": True},
                    {"type": "string"}
                ]
            }
        },
        "additionalProperties": True
    }

    # Apply the fix to all badge fields found in the object
    fixed_count = 0

    def fix_recursive(obj):
        nonlocal fixed_count
        if isinstance(obj, dict):
            # Check if this is a badge property that needs fixing
            if "badge" in obj:
                badge_def = obj["badge"]
                if badge_def is True or (isinstance(badge_def, dict) and badge_def.get("type") != "object"):
                    obj["badge"] = badge_object.copy()
                    fixed_count += 1
                    logger.debug(f"Fixed badge field in properties")

            # Recursively fix nested objects
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    fix_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                fix_recursive(item)

    fix_recursive(schema_obj)
    return schema_obj, fixed_count


def fix_schema_wide_badge_issues(schema: dict) -> dict:
    """
    Fix badge field definitions across the entire schema.
    """
    definitions = schema.get("definitions", {})
    total_fixed = 0

    for def_name, def_obj in definitions.items():
        if not isinstance(def_obj, dict):
            continue

        # Special handling for TplSchema
        if def_name == "TplSchema":
            logger.info("Fixing TplSchema badge field specifically...")
            fixed_def, count = fix_tpl_schema_badge_field(def_obj)
            definitions[def_name] = fixed_def
            total_fixed += count
            logger.info(f"Fixed {count} badge fields in TplSchema")

        # General badge field fixes
        if "allOf" in def_obj:
            for allof_item in def_obj["allOf"]:
                if isinstance(allof_item, dict) and "properties" in allof_item:
                    if "badge" in allof_item["properties"]:
                        badge_def = allof_item["properties"]["badge"]
                        if badge_def is True:
                            # Convert to proper BadgeObject structure
                            allof_item["properties"]["badge"] = {
                                "type": "object",
                                "description": "Badge configuration object"
                            }
                            total_fixed += 1
                            logger.debug(f"Fixed badge in {def_name}")

    logger.info(f"Total badge fields fixed: {total_fixed}")
    return schema


def main():
    """Main function to fix comprehensive badge validation issues."""
    logger.info("=" * 60)
    logger.info("Comprehensive Badge Validation Fix")
    logger.info("=" * 60)

    # Load the problematic schema
    logger.info(f"Loading schema from {SCHEMA_PATH}")
    schema = load_schema(SCHEMA_PATH)

    # Fix badge field definitions across the entire schema
    logger.info("Fixing badge field definitions...")
    fixed_schema = fix_schema_wide_badge_issues(schema)

    # Save the fixed schema
    logger.info(f"Saving fixed schema to {SCHEMA_PATH}")
    save_schema(fixed_schema, SCHEMA_PATH)

    logger.info("=" * 60)
    logger.info("✅ Comprehensive badge validation issues fixed!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
