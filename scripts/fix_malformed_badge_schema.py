#!/usr/bin/env python3
"""
Fix the malformed badge field structures in the schema that are causing validation errors.

The comprehensive_badge_fix.py script created invalid JSON Schema structures:
- "type": [...] instead of "anyOf": [...]
- "items": {"type": {...}} instead of "items": {"anyOf": [...]}

This script fixes these structures to be valid JSON Schema.
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


def fix_malformed_anyof(schema_obj: dict) -> dict:
    """
    Fix malformed anyOf structures that were created by comprehensive_badge_fix.py

    Converts:
    - "type": [schema1, schema2] -> "anyOf": [schema1, schema2]
    - "items": {"type": schema} -> "items": {"anyOf": [schema]}
    """
    if not isinstance(schema_obj, dict):
        return schema_obj

    fixed_count = 0

    def fix_recursive(obj):
        nonlocal fixed_count
        if isinstance(obj, dict):
            # Fix type arrays (should be anyOf)
            if "type" in obj and isinstance(obj["type"], list):
                # This is a malformed union type
                obj["anyOf"] = obj.pop("type")
                fixed_count += 1
                logger.debug(f"Fixed type array -> anyOf")

            # Fix items with malformed type
            if "items" in obj and isinstance(obj["items"], dict):
                items = obj["items"]
                if "type" in items and isinstance(items["type"], dict):
                    # This is a malformed items type
                    items["anyOf"] = [items.pop("type")]
                    fixed_count += 1
                    logger.debug(f"Fixed items type -> anyOf")

            # Recursively fix nested objects
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    fix_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                fix_recursive(item)

    fix_recursive(schema_obj)
    return schema_obj, fixed_count


def fix_badge_specific_issues(schema: dict) -> dict:
    """
    Fix specific issues in badge field definitions.
    """
    definitions = schema.get("definitions", {})
    total_fixed = 0

    for def_name, def_obj in definitions.items():
        if not isinstance(def_obj, dict):
            continue

        # Fix any malformed anyOf structures
        if "allOf" in def_obj:
            for allof_item in def_obj["allOf"]:
                if isinstance(allof_item, dict) and "properties" in allof_item:
                    properties = allof_item["properties"]
                    if "badge" in properties:
                        badge_def = properties["badge"]
                        if isinstance(badge_def, dict) and "properties" in badge_def:
                            badge_props = badge_def["properties"]

                            # Fix text property
                            if "text" in badge_props:
                                text_def = badge_props["text"]
                                if isinstance(text_def, dict) and "type" in text_def:
                                    # Convert malformed type array to proper anyOf
                                    if isinstance(text_def["type"], list):
                                        text_def["anyOf"] = text_def.pop("type")
                                        total_fixed += 1
                                        logger.debug(f"Fixed badge.text anyOf in {def_name}")

                            # Fix offset property
                            if "offset" in badge_props:
                                offset_def = badge_props["offset"]
                                if isinstance(offset_def, dict) and "items" in offset_def:
                                    items_def = offset_def["items"]
                                    if isinstance(items_def, dict) and "type" in items_def:
                                        if isinstance(items_def["type"], dict):
                                            # Convert malformed items type to anyOf
                                            items_def["anyOf"] = [items_def.pop("type")]
                                            total_fixed += 1
                                            logger.debug(f"Fixed badge.offset items anyOf in {def_name}")
                                        elif isinstance(items_def["type"], list):
                                            # Already an array, convert to anyOf
                                            items_def["anyOf"] = items_def.pop("type")
                                            total_fixed += 1
                                            logger.debug(f"Fixed badge.offset items type array in {def_name}")

    logger.info(f"Total badge-specific issues fixed: {total_fixed}")
    return schema


def main():
    """Main function to fix malformed badge validation issues."""
    logger.info("=" * 60)
    logger.info("Fixing Malformed Badge Schema Structures")
    logger.info("=" * 60)

    # Load the schema
    logger.info(f"Loading schema from {SCHEMA_PATH}")
    schema = load_schema(SCHEMA_PATH)

    # Fix general malformed anyOf structures
    logger.info("Fixing general malformed anyOf structures...")
    fixed_schema, general_fixes = fix_malformed_anyof(schema)
    logger.info(f"Fixed {general_fixes} general anyOf issues")

    # Fix badge-specific issues
    logger.info("Fixing badge-specific issues...")
    final_schema = fix_badge_specific_issues(fixed_schema)

    # Save the fixed schema
    logger.info(f"Saving fixed schema to {SCHEMA_PATH}")
    save_schema(final_schema, SCHEMA_PATH)

    logger.info("=" * 60)
    logger.info("✅ Malformed badge schema structures fixed!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
