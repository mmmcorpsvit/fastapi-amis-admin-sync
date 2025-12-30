#!/usr/bin/env python3
"""
Fix the badge validation issue in the simplified schema.

This script identifies and fixes the problematic badge field definitions
that are causing validation errors during model generation.
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


def fix_badge_fields(schema: dict) -> dict:
    """
    Fix badge field definitions that are causing validation errors.

    The issue is that badge fields defined as "badge": true in properties
    should be consistent with their type definitions in the allOf sections.
    """
    definitions = schema.get("definitions", {})
    fixed_count = 0

    for def_name, def_obj in definitions.items():
        if not isinstance(def_obj, dict):
            continue

        # Look for allOf schemas that might have badge definitions
        if "allOf" in def_obj:
            for i, allof_item in enumerate(def_obj["allOf"]):
                if not isinstance(allof_item, dict):
                    continue

                # Check if this allOf item has properties with badge
                if "properties" in allof_item:
                    if "badge" in allof_item["properties"]:
                        badge_def = allof_item["properties"]["badge"]

                        # If badge is defined as just "true" or has inconsistent types, fix it
                        if badge_def is True:
                            # Convert to a more specific type that matches BadgeObject
                            allof_item["properties"]["badge"] = {
                                "type": "object",
                                "description": "Badge configuration object"
                            }
                            fixed_count += 1
                            logger.debug(f"Fixed badge field in {def_name} (allOf[{i}])")

                        elif isinstance(badge_def, dict):
                            # Check if the badge definition has type conflicts
                            if "type" in badge_def and badge_def["type"] == "object":
                                # This is likely correct, but ensure it has proper structure
                                if "properties" not in badge_def:
                                    # Add basic structure for BadgeObject
                                    badge_def["properties"] = {
                                        "text": {
                                            "anyOf": [
                                                {"type": "string"},
                                                {"type": "array", "items": {"type": "string"}},
                                                {"type": "object", "additionalProperties": True}
                                            ]
                                        },
                                        "level": {
                                            "type": "string",
                                            "enum": ["success", "warning", "danger", "info"]
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
                                        }
                                    }
                                    badge_def["additionalProperties"] = True
                                    fixed_count += 1
                                    logger.debug(f"Enhanced badge structure in {def_name} (allOf[{i}])")

    logger.info(f"Fixed {fixed_count} badge field definitions")
    return schema


def main():
    """Main function to fix badge validation issues."""
    logger.info("=" * 60)
    logger.info("Fixing Badge Validation Issues")
    logger.info("=" * 60)

    # Load the problematic schema
    logger.info(f"Loading schema from {SCHEMA_PATH}")
    schema = load_schema(SCHEMA_PATH)

    # Fix badge field definitions
    logger.info("Fixing badge field definitions...")
    fixed_schema = fix_badge_fields(schema)

    # Save the fixed schema
    logger.info(f"Saving fixed schema to {SCHEMA_PATH}")
    save_schema(fixed_schema, SCHEMA_PATH)

    logger.info("=" * 60)
    logger.info("✅ Badge validation issues fixed!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
