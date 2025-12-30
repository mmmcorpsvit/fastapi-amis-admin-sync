#!/usr/bin/env python3
"""
Deep analysis of why Any types are generated.

This script:
1. Analyzes the original schema.json structure
2. Traces how types are lost during simplification
3. Identifies specific patterns that lead to Any
4. Checks what the generator sees vs what we have
"""
import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ORIGINAL_SCHEMA = Path(__file__).parent.parent / "schema" / "schema.json"
TRANSLATED_SCHEMA = Path(__file__).parent.parent / "schema" / "schema_translated.json"
SIMPLIFIED_SCHEMA = Path(__file__).parent.parent / "schema" / "schema_simplified.json"
GENERATED_MODELS = Path(__file__).parent.parent / "fastapi_amis_admin" / "amis" / "auto_generated_models.py"


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_any_types_in_generated() -> Dict[str, List[str]]:
    """Find all Any types in generated models and their context."""
    if not GENERATED_MODELS.exists():
        return {}
    
    with open(GENERATED_MODELS, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find all lines with : Any
    any_pattern = re.compile(r'^\s+(\w+):\s+Any(?:\s+\|\s+None)?(?:\s*=\s*Field\([^)]+\))?', re.MULTILINE)
    matches = any_pattern.findall(content)
    
    # Get context around each match
    lines = content.split('\n')
    any_fields = defaultdict(list)
    
    for i, line in enumerate(lines):
        if ': Any' in line:
            # Extract field name
            field_match = re.search(r'(\w+):\s+Any', line)
            if field_match:
                field_name = field_match.group(1)
                # Get class name (look backwards for class definition)
                class_name = None
                for j in range(i, max(0, i-20), -1):
                    class_match = re.search(r'^class\s+(\w+)', lines[j])
                    if class_match:
                        class_name = class_match.group(1)
                        break
                
                if class_name:
                    any_fields[class_name].append(field_name)
    
    return dict(any_fields)


def analyze_field_in_schema(
    def_name: str,
    field_name: str,
    schema: Dict[str, Any],
    path: str = "",
    depth: int = 0,
    max_depth: int = 10,
) -> Dict[str, Any]:
    """Deeply analyze a specific field in the schema."""
    if depth > max_depth:
        return {"error": "max_depth exceeded"}
    
    result = {
        "field_name": field_name,
        "definition": def_name,
        "path": path,
        "has_type": False,
        "type_value": None,
        "has_anyOf": False,
        "has_oneOf": False,
        "has_allOf": False,
        "has_ref": False,
        "ref_target": None,
        "additionalProperties": None,
        "is_primitive": False,
        "issues": [],
    }
    
    if not isinstance(schema, dict):
        result["issues"].append(f"Schema is not a dict: {type(schema)}")
        return result
    
    # Check for type
    if "type" in schema:
        result["has_type"] = True
        result["type_value"] = schema["type"]
        if schema["type"] in ("string", "number", "integer", "boolean", "null"):
            result["is_primitive"] = True
    
    # Check for unions
    for union_key in ["anyOf", "oneOf", "allOf"]:
        if union_key in schema:
            result[f"has_{union_key}"] = True
            union_items = schema[union_key]
            if isinstance(union_items, list):
                result[f"{union_key}_count"] = len(union_items)
                result[f"{union_key}_items"] = []
                for idx, item in enumerate(union_items[:5]):  # First 5
                    item_analysis = analyze_field_in_schema(
                        def_name, field_name, item, f"{path}.{union_key}[{idx}]", depth + 1, max_depth
                    )
                    result[f"{union_key}_items"].append(item_analysis)
    
    # Check for $ref
    if "$ref" in schema:
        result["has_ref"] = True
        result["ref_target"] = schema["$ref"]
    
    # Check additionalProperties
    if "additionalProperties" in schema:
        ap = schema["additionalProperties"]
        if isinstance(ap, bool):
            result["additionalProperties"] = ap
            if ap is True:
                result["issues"].append("additionalProperties: true (allows any value)")
        elif isinstance(ap, dict):
            result["additionalProperties"] = "object"
            ap_analysis = analyze_field_in_schema(
                def_name, field_name, ap, f"{path}.additionalProperties", depth + 1, max_depth
            )
            result["additionalProperties_schema"] = ap_analysis
    
    # Check if it's just "true" (allows any)
    if schema is True:
        result["issues"].append("Schema is 'true' (allows any value)")
    
    # Check for missing type info
    if not result["has_type"] and not result["has_anyOf"] and not result["has_oneOf"] and not result["has_allOf"] and not result["has_ref"]:
        if "additionalProperties" not in schema or schema.get("additionalProperties") is True:
            result["issues"].append("No type information, only additionalProperties: true")
    
    return result


def trace_field_to_schema(
    class_name: str,
    field_name: str,
    original_schema: Dict[str, Any],
    simplified_schema: Dict[str, Any],
) -> Dict[str, Any]:
    """Trace a field from generated model back to schema definitions."""
    result = {
        "class_name": class_name,
        "field_name": field_name,
        "found_in_original": False,
        "found_in_simplified": False,
        "original_analysis": None,
        "simplified_analysis": None,
        "differences": [],
    }
    
    orig_defs = original_schema.get("definitions", {})
    simp_defs = simplified_schema.get("definitions", {})
    
    # Try to find the class definition
    # Class names often map to schema definitions
    def_name = class_name.replace("Schema", "").replace("Loose", "")
    
    # Try exact match first
    if class_name in orig_defs:
        def_name = class_name
    elif def_name in orig_defs:
        pass  # Use def_name
    else:
        # Try variations
        for key in orig_defs.keys():
            if class_name.lower() in key.lower() or key.lower() in class_name.lower():
                def_name = key
                break
    
    if def_name in orig_defs:
        result["found_in_original"] = True
        orig_def = orig_defs[def_name]
        
        # Find the field in properties
        if "properties" in orig_def:
            orig_props = orig_def["properties"]
            # Convert field_name to schema name (camelCase or snake_case)
            schema_field_names = [
                field_name,  # Original
                field_name.replace("_", ""),  # Remove underscores
                "".join(word.capitalize() if i > 0 else word for i, word in enumerate(field_name.split("_"))),  # camelCase
            ]
            
            for schema_field in schema_field_names:
                if schema_field in orig_props:
                    result["original_analysis"] = analyze_field_in_schema(
                        def_name, schema_field, orig_props[schema_field], f"definitions.{def_name}.properties.{schema_field}"
                    )
                    break
    
    if def_name in simp_defs:
        result["found_in_simplified"] = True
        simp_def = simp_defs[def_name]
        
        if "properties" in simp_def:
            simp_props = simp_def["properties"]
            schema_field_names = [
                field_name,
                field_name.replace("_", ""),
                "".join(word.capitalize() if i > 0 else word for i, word in enumerate(field_name.split("_"))),
            ]
            
            for schema_field in schema_field_names:
                if schema_field in simp_props:
                    result["simplified_analysis"] = analyze_field_in_schema(
                        def_name, schema_field, simp_props[schema_field], f"definitions.{def_name}.properties.{schema_field}"
                    )
                    break
    
    # Compare original vs simplified
    if result["original_analysis"] and result["simplified_analysis"]:
        orig = result["original_analysis"]
        simp = result["simplified_analysis"]
        
        if orig.get("type_value") != simp.get("type_value"):
            result["differences"].append(f"Type changed: {orig.get('type_value')} -> {simp.get('type_value')}")
        
        if orig.get("has_anyOf") != simp.get("has_anyOf"):
            result["differences"].append(f"anyOf presence changed: {orig.get('has_anyOf')} -> {simp.get('has_anyOf')}")
        
        if orig.get("anyOf_count", 0) != simp.get("anyOf_count", 0):
            result["differences"].append(f"anyOf count changed: {orig.get('anyOf_count')} -> {simp.get('anyOf_count')}")
    
    return result


def analyze_common_any_patterns() -> Dict[str, Any]:
    """Analyze common patterns that lead to Any types."""
    logger.info("Loading schemas...")
    original = load_json(ORIGINAL_SCHEMA)
    simplified = load_json(SIMPLIFIED_SCHEMA)
    
    logger.info("Finding Any types in generated models...")
    any_fields = find_any_types_in_generated()
    
    logger.info(f"Found {sum(len(fields) for fields in any_fields.values())} Any fields across {len(any_fields)} classes")
    
    # Analyze top 10 classes with most Any fields
    top_classes = sorted(any_fields.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    
    analysis = {
        "total_any_fields": sum(len(fields) for fields in any_fields.values()),
        "total_classes_with_any": len(any_fields),
        "top_classes": {},
    }
    
    logger.info("Analyzing top classes with Any fields...")
    for class_name, fields in top_classes:
        logger.info(f"  Analyzing {class_name} with {len(fields)} Any fields...")
        class_analysis = {
            "field_count": len(fields),
            "fields": {},
        }
        
        # Analyze first 5 fields
        for field_name in fields[:5]:
            trace = trace_field_to_schema(class_name, field_name, original, simplified)
            class_analysis["fields"][field_name] = trace
        
        analysis["top_classes"][class_name] = class_analysis
    
    return analysis


def find_schema_patterns_leading_to_any(schema: Dict[str, Any]) -> Dict[str, List[str]]:
    """Find patterns in schema that will lead to Any types."""
    patterns = defaultdict(list)
    definitions = schema.get("definitions", {})
    
    for def_name, def_obj in definitions.items():
        if not isinstance(def_obj, dict):
            continue
        
        # Pattern 1: additionalProperties: true
        if def_obj.get("additionalProperties") is True:
            patterns["additionalProperties_true"].append(def_name)
        
        # Pattern 2: No type, no anyOf, just object
        if "type" not in def_obj and "anyOf" not in def_obj and "oneOf" not in def_obj:
            if "properties" not in def_obj or not def_obj.get("properties"):
                patterns["no_type_info"].append(def_name)
        
        # Pattern 3: Check properties
        if "properties" in def_obj:
            for prop_name, prop_schema in def_obj["properties"].items():
                if isinstance(prop_schema, dict):
                    # Property with additionalProperties: true
                    if prop_schema.get("additionalProperties") is True:
                        patterns["property_additionalProperties_true"].append(f"{def_name}.{prop_name}")
                    
                    # Property that's just true
                    if prop_schema is True:
                        patterns["property_is_true"].append(f"{def_name}.{prop_name}")
                    
                    # Property with no type and no union
                    if "type" not in prop_schema and "anyOf" not in prop_schema and "oneOf" not in prop_schema and "$ref" not in prop_schema:
                        if prop_schema.get("additionalProperties") is True:
                            patterns["property_no_type"].append(f"{def_name}.{prop_name}")
    
    return dict(patterns)


def main() -> int:
    """Main analysis function."""
    logger.info("=" * 80)
    logger.info("DEEP ANALYSIS: Why Any Types Are Generated")
    logger.info("=" * 80)
    
    # Load schemas
    logger.info("\n1. Loading schemas...")
    original = load_json(ORIGINAL_SCHEMA)
    simplified = load_json(SIMPLIFIED_SCHEMA)
    
    # Find patterns in original schema
    logger.info("\n2. Analyzing patterns in original schema...")
    orig_patterns = find_schema_patterns_leading_to_any(original)
    
    print("\n" + "=" * 80)
    print("PATTERNS IN ORIGINAL SCHEMA THAT LEAD TO ANY:")
    print("=" * 80)
    for pattern_type, items in sorted(orig_patterns.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{pattern_type}: {len(items)}")
        for item in items[:10]:
            print(f"  - {item}")
        if len(items) > 10:
            print(f"  ... and {len(items) - 10} more")
    
    # Analyze Any types in generated code
    logger.info("\n3. Analyzing Any types in generated models...")
    any_analysis = analyze_common_any_patterns()
    
    print("\n" + "=" * 80)
    print("ANY TYPES IN GENERATED MODELS:")
    print("=" * 80)
    print(f"\nTotal Any fields: {any_analysis['total_any_fields']}")
    print(f"Classes with Any: {any_analysis['total_classes_with_any']}")
    
    print("\nTop classes with Any fields:")
    for class_name, class_data in any_analysis["top_classes"].items():
        print(f"\n{class_name}: {class_data['field_count']} Any fields")
        for field_name, trace in list(class_data["fields"].items())[:3]:
            print(f"  - {field_name}:")
            if trace.get("original_analysis"):
                orig = trace["original_analysis"]
                print(f"    Original: type={orig.get('type_value')}, anyOf={orig.get('has_anyOf')}, issues={orig.get('issues')}")
            if trace.get("simplified_analysis"):
                simp = trace["simplified_analysis"]
                print(f"    Simplified: type={simp.get('type_value')}, anyOf={simp.get('has_anyOf')}, issues={simp.get('issues')}")
            if trace.get("differences"):
                print(f"    Differences: {trace['differences']}")
    
    # Save detailed report
    report_path = Path(__file__).parent.parent / "any_types_analysis_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "patterns": orig_patterns,
            "any_analysis": any_analysis,
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nDetailed report saved to: {report_path}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

