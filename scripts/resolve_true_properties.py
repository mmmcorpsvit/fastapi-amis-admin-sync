#!/usr/bin/env python3
"""
Resolve properties defined as 'true' from base schemas via allOf.

In JSON Schema, when a property is defined as `true`, it means "accept any value".
However, many schemas use `allOf` to inherit from base schemas that define
these properties with proper types. We need to resolve these.
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
    """Load JSON schema."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_ref(ref: str, definitions: Dict[str, Any]) -> Any:
    """Resolve a $ref reference."""
    if not ref.startswith("#/definitions/"):
        return None
    def_name = ref.split("/")[-1]
    return definitions.get(def_name)


def get_properties_from_allof(
    schema: Dict[str, Any],
    definitions: Dict[str, Any],
    visited: Set[str],
    depth: int = 0,
    max_depth: int = 10,
) -> Dict[str, Any]:
    """
    Extract and merge properties from allOf schemas.
    
    This resolves properties that are defined as 'true' by finding their
    actual definitions in base schemas via allOf.
    """
    if depth > max_depth:
        return {}
    
    properties = {}
    
    # If schema has properties directly, use them
    if "properties" in schema:
        properties.update(schema["properties"])
    
    # Process allOf to merge properties
    if "allOf" in schema:
        for item in schema.get("allOf", []):
            if isinstance(item, dict):
                # Resolve $ref if present
                if "$ref" in item:
                    ref = item["$ref"]
                    def_name = ref.split("/")[-1] if "/" in ref else ref
                    if def_name not in visited:
                        visited.add(def_name)
                        resolved = resolve_ref(ref, definitions)
                        if resolved:
                            # Recursively get properties from resolved schema
                            resolved_props = get_properties_from_allof(
                                resolved, definitions, visited, depth + 1, max_depth
                            )
                            # Merge: resolved properties override current (base overrides derived)
                            # Actually, we want current to override base, so merge the other way
                            for key, value in resolved_props.items():
                                if key not in properties:
                                    properties[key] = value
                            # Also get direct properties from resolved
                            if "properties" in resolved:
                                for key, value in resolved["properties"].items():
                                    if key not in properties:
                                        properties[key] = value
                        visited.remove(def_name)
                else:
                    # Direct schema in allOf
                    item_props = get_properties_from_allof(
                        item, definitions, visited, depth + 1, max_depth
                    )
                    for key, value in item_props.items():
                        if key not in properties:
                            properties[key] = value
                    if "properties" in item:
                        for key, value in item["properties"].items():
                            if key not in properties:
                                properties[key] = value
    
    return properties


def resolve_true_properties_in_schema(
    schema: Dict[str, Any],
    definitions: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Resolve properties defined as 'true' by looking them up in base schemas.
    """
    logger.info("Resolving 'true' properties from base schemas...")
    
    # First, build a map of all properties from base schemas
    base_properties = {}
    
    # Find BaseSchema and similar base definitions
    base_schema_names = [
        "BaseSchema",
        "BaseSchemaWithoutType",
        "SchemaObject",
        "ActionSchema",
    ]
    
    for base_name in base_schema_names:
        if base_name in definitions:
            base_schema = definitions[base_name]
            base_props = get_properties_from_allof(base_schema, definitions, set())
            base_properties.update(base_props)
            # Also get direct properties
            if "properties" in base_schema:
                for key, value in base_schema["properties"].items():
                    if key not in base_properties:
                        base_properties[key] = value
    
    logger.info(f"Found {len(base_properties)} base properties")
    
    # Now process all definitions and replace 'true' with actual types
    resolved_definitions = {}
    true_count = 0
    resolved_count = 0
    
    for def_name, def_obj in definitions.items():
        if not isinstance(def_obj, dict):
            resolved_definitions[def_name] = def_obj
            continue
        
        resolved_def = json.loads(json.dumps(def_obj))  # Deep copy
        
        # Process properties
        if "properties" in resolved_def:
            for prop_name, prop_value in resolved_def["properties"].items():
                if prop_value is True:
                    true_count += 1
                    # Try to find this property in base schemas
                    if prop_name in base_properties:
                        resolved_def["properties"][prop_name] = json.loads(
                            json.dumps(base_properties[prop_name])
                        )  # Deep copy
                        resolved_count += 1
                    # Also check camelCase variants
                    elif prop_name.lower() in [k.lower() for k in base_properties.keys()]:
                        for base_key, base_value in base_properties.items():
                            if base_key.lower() == prop_name.lower():
                                resolved_def["properties"][prop_name] = json.loads(
                                    json.dumps(base_value)
                                )
                                resolved_count += 1
                                break
        
        # Also process allOf to resolve properties there
        if "allOf" in resolved_def:
            for i, allof_item in enumerate(resolved_def["allOf"]):
                if isinstance(allof_item, dict) and "properties" in allof_item:
                    for prop_name, prop_value in allof_item["properties"].items():
                        if prop_value is True:
                            if prop_name in base_properties:
                                resolved_def["allOf"][i]["properties"][prop_name] = json.loads(
                                    json.dumps(base_properties[prop_name])
                                )
        
        resolved_definitions[def_name] = resolved_def
    
    logger.info(f"Found {true_count} 'true' properties, resolved {resolved_count} from base schemas")
    
    return {
        "$schema": schema.get("$schema", "http://json-schema.org/draft-07/schema#"),
        "definitions": resolved_definitions,
        **{k: v for k, v in schema.items() if k not in ("definitions", "$schema")},
    }


def main() -> int:
    """Main function."""
    logger.info("=" * 60)
    logger.info("Resolve 'true' Properties from Base Schemas")
    logger.info("=" * 60)
    
    schema = load_schema(SCHEMA_PATH)
    resolved = resolve_true_properties_in_schema(schema, schema.get("definitions", {}))
    
    # Save to simplified schema (this should be run before simplify_schema.py)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(resolved, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Resolved schema saved to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

