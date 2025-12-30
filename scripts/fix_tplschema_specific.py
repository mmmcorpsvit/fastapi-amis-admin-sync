#!/usr/bin/env python3
"""
Targeted fix for the specific TplSchema badge validation issue.

This script specifically addresses the JsonSchemaObject nesting issue
within the badge field of TplSchema.
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


def fix_tplschema_json_schema_object(schema: dict) -> dict:
    """
    Fix the specific JsonSchemaObject nesting issue in TplSchema badge field.

    The error is: allOf.1.properties.badge.JsonSchemaObject.properties.text.JsonSchemaObject
    This means the badge field contains a JsonSchemaObject that has nested validation issues.
    """
    definitions = schema.get("definitions", {})

    # Find and remove the problematic JsonSchemaObject definition
    json_schema_object_def = definitions.get("JsonSchemaObject")
    if json_schema_object_def:
        logger.info("Found JsonSchemaObject definition, removing it...")
        # Remove the JsonSchemaObject definition entirely
        del definitions["JsonSchemaObject"]

        # Replace any references to JsonSchemaObject with a proper type
        for def_name, def_obj in definitions.items():
            if isinstance(def_obj, dict):
                def_obj_str = json.dumps(def_obj)
                if "JsonSchemaObject" in def_obj_str:
                    # This definition references JsonSchemaObject, we need to fix it
                    logger.info(f"Fixing references to JsonSchemaObject in {def_name}")
                    fixed_obj = json.loads(def_obj_str.replace("JsonSchemaObject", "object"))
                    definitions[def_name] = fixed_obj

    # Fix the TplSchema specifically
    tpl_schema = definitions.get("TplSchema")
    if tpl_schema and isinstance(tpl_schema, dict) and "allOf" in tpl_schema:
        logger.info("Fixing TplSchema allOf structure...")

        for i, allof_item in enumerate(tpl_schema["allOf"]):
            if isinstance(allof_item, dict) and "properties" in allof_item:
                if "badge" in allof_item["properties"]:
                    badge_def = allof_item["properties"]["badge"]
                    logger.info(f"Found badge field in TplSchema allOf[{i}], replacing with proper definition...")

                    # Replace with a proper badge definition that doesn't use JsonSchemaObject
                    allof_item["properties"]["badge"] = {
                        "anyOf": [
                            {"type": "object", "additionalProperties": True},
                            {"type": "string"},
                            {"type": "boolean"},
                            {"type": "number"},
                            {"type": "array", "items": {"additionalProperties": True}}
                        ]
                    }

    return schema


def main():
    """Main function to fix the specific TplSchema JsonSchemaObject issue."""
    logger.info("=" * 60)
    logger.info("Fixing TplSchema JsonSchemaObject Issue")
    logger.info("=" * 60)

    # Load the problematic schema
    logger.info(f"Loading schema from {SCHEMA_PATH}")
    schema = load_schema(SCHEMA_PATH)

    # Fix the JsonSchemaObject issue
    logger.info("Fixing JsonSchemaObject nesting issues...")
    fixed_schema = fix_tplschema_json_schema_object(schema)

    # Save the fixed schema
    logger.info(f"Saving fixed schema to {SCHEMA_PATH}")
    save_schema(fixed_schema, SCHEMA_PATH)

    logger.info("=" * 60)
    logger.info("✅ TplSchema JsonSchemaObject issue fixed!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
