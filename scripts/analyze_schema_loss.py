#!/usr/bin/env python3
"""
Deep analysis of what information is lost during schema simplification.

This script compares the original schema with the simplified schema to identify:
1. Missing definitions
2. Lost properties
3. Lost type information
4. Lost constraints (enum, min, max, etc.)
5. Lost descriptions
6. Lost examples
7. Truncated anyOf/oneOf/allOf unions
"""
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ORIGINAL_SCHEMA = Path(__file__).parent.parent / "schema" / "schema_translated.json"
SIMPLIFIED_SCHEMA = Path(__file__).parent.parent / "schema" / "schema_simplified.json"


def load_schema(path: Path) -> Dict[str, Any]:
    """Load JSON schema."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def count_keys(obj: Any, key_counts: Dict[str, int], path: str = "") -> None:
    """Recursively count all keys in schema."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_counts[key] = key_counts.get(key, 0) + 1
            count_keys(value, key_counts, f"{path}.{key}" if path else key)
    elif isinstance(obj, list):
        for item in obj:
            count_keys(item, key_counts, path)


def analyze_definition(
    def_name: str,
    original: Any,
    simplified: Any,
    issues: Dict[str, List[str]],
) -> None:
    """Analyze a single definition for lost information."""
    path_prefix = f"definitions.{def_name}"
    
    # Handle non-dict values
    if not isinstance(original, dict) or not isinstance(simplified, dict):
        if original != simplified:
            issues["value_changes"].append(
                f"{path_prefix}: Value changed from {type(original).__name__} to {type(simplified).__name__}"
            )
        return
    
    # Check for missing keys
    orig_keys = set(original.keys())
    simp_keys = set(simplified.keys())
    missing_keys = orig_keys - simp_keys
    
    if missing_keys:
        issues["missing_keys"].append(
            f"{path_prefix}: Missing keys {missing_keys}"
        )
    
    # Check for lost descriptions
    if "description" in original and "description" not in simplified:
        issues["lost_descriptions"].append(f"{path_prefix}: Lost description")
    elif "description" in original and "description" in simplified:
        if original["description"] != simplified["description"]:
            issues["modified_descriptions"].append(f"{path_prefix}: Description modified")
    
    # Check for lost examples
    if "examples" in original and "examples" not in simplified:
        issues["lost_examples"].append(f"{path_prefix}: Lost examples")
    
    # Check for lost enum
    if "enum" in original and "enum" not in simplified:
        issues["lost_enums"].append(f"{path_prefix}: Lost enum {original['enum']}")
    elif "enum" in original and "enum" in simplified:
        orig_enum = set(original["enum"])
        simp_enum = set(simplified["enum"])
        if orig_enum != simp_enum:
            issues["modified_enums"].append(
                f"{path_prefix}: Enum changed from {orig_enum} to {simp_enum}"
            )
    
    # Check for lost constraints
    constraint_keys = ["minimum", "maximum", "minLength", "maxLength", "pattern", "format"]
    for key in constraint_keys:
        if key in original and key not in simplified:
            issues["lost_constraints"].append(f"{path_prefix}: Lost {key}={original[key]}")
    
    # Check for lost default values
    if "default" in original and "default" not in simplified:
        issues["lost_defaults"].append(f"{path_prefix}: Lost default={original['default']}")
    
    # Check for truncated anyOf/oneOf/allOf
    for union_key in ["anyOf", "oneOf", "allOf"]:
        if union_key in original:
            orig_items = len(original[union_key]) if isinstance(original[union_key], list) else 0
            if union_key in simplified:
                simp_items = len(simplified[union_key]) if isinstance(simplified[union_key], list) else 0
                if simp_items < orig_items:
                    issues["truncated_unions"].append(
                        f"{path_prefix}: {union_key} truncated from {orig_items} to {simp_items} items"
                    )
            else:
                issues["lost_unions"].append(
                    f"{path_prefix}: Lost {union_key} with {orig_items} items"
                )
    
    # Recursively check properties
    if "properties" in original:
        orig_props = original["properties"]
        if "properties" in simplified:
            simp_props = simplified["properties"]
            
            # Check for missing properties
            missing_props = set(orig_props.keys()) - set(simp_props.keys())
            if missing_props:
                issues["missing_properties"].append(
                    f"{path_prefix}.properties: Missing {missing_props}"
                )
            
            # Recursively check each property
            for prop_name in orig_props.keys() & simp_props.keys():
                analyze_definition(
                    f"{def_name}.properties.{prop_name}",
                    orig_props[prop_name],
                    simp_props[prop_name],
                    issues,
                )
        else:
            issues["missing_properties"].append(
                f"{path_prefix}: All properties lost"
            )
    
    # Check items (for arrays)
    if "items" in original:
        if "items" not in simplified:
            issues["lost_items"].append(f"{path_prefix}: Lost items schema")
        else:
            analyze_definition(
                f"{def_name}.items",
                original["items"],
                simplified["items"],
                issues,
            )
    
    # Check additionalProperties
    if "additionalProperties" in original:
        orig_ap = original["additionalProperties"]
        if "additionalProperties" in simplified:
            simp_ap = simplified["additionalProperties"]
            if isinstance(orig_ap, dict) and isinstance(simp_ap, dict):
                analyze_definition(
                    f"{def_name}.additionalProperties",
                    orig_ap,
                    simp_ap,
                    issues,
                )
            elif orig_ap != simp_ap:
                issues["modified_additional_properties"].append(
                    f"{path_prefix}: additionalProperties changed"
                )


def analyze_schemas() -> Dict[str, List[str]]:
    """Compare original and simplified schemas."""
    logger.info("Loading schemas...")
    original = load_schema(ORIGINAL_SCHEMA)
    simplified = load_schema(SIMPLIFIED_SCHEMA)
    
    orig_defs = original.get("definitions", {})
    simp_defs = simplified.get("definitions", {})
    
    logger.info(f"Original definitions: {len(orig_defs)}")
    logger.info(f"Simplified definitions: {len(simp_defs)}")
    
    # Check for missing definitions
    missing_defs = set(orig_defs.keys()) - set(simp_defs.keys())
    if missing_defs:
        logger.warning(f"Missing definitions: {len(missing_defs)}")
    
    # Initialize issues tracker
    issues: Dict[str, List[str]] = defaultdict(list)
    
    if missing_defs:
        issues["missing_definitions"] = list(missing_defs)
    
    # Analyze each definition
    logger.info("Analyzing definitions...")
    for def_name in orig_defs.keys() & simp_defs.keys():
        analyze_definition(
            def_name,
            orig_defs[def_name],
            simp_defs[def_name],
            issues,
        )
    
    # Count keys in both schemas
    orig_key_counts: Dict[str, int] = {}
    simp_key_counts: Dict[str, int] = {}
    count_keys(original, orig_key_counts)
    count_keys(simplified, simp_key_counts)
    
    # Find keys that appear less frequently in simplified
    key_reduction = {}
    for key in orig_key_counts:
        orig_count = orig_key_counts[key]
        simp_count = simp_key_counts.get(key, 0)
        if simp_count < orig_count:
            key_reduction[key] = (orig_count, simp_count, orig_count - simp_count)
    
    if key_reduction:
        issues["key_reductions"] = [
            f"{key}: {orig} -> {simp} (lost {lost})"
            for key, (orig, simp, lost) in sorted(
                key_reduction.items(), key=lambda x: x[1][2], reverse=True
            )[:20]  # Top 20
        ]
    
    return dict(issues)


def print_report(issues: Dict[str, List[str]]) -> None:
    """Print analysis report."""
    print("\n" + "=" * 80)
    print("SCHEMA SIMPLIFICATION ANALYSIS REPORT")
    print("=" * 80)
    
    total_issues = sum(len(v) for v in issues.values())
    print(f"\nTotal issues found: {total_issues}\n")
    
    # Sort by severity/importance
    priority_order = [
        "missing_definitions",
        "missing_properties",
        "lost_enums",
        "truncated_unions",
        "lost_unions",
        "lost_constraints",
        "lost_defaults",
        "lost_descriptions",
        "modified_descriptions",
        "lost_examples",
        "lost_items",
        "missing_keys",
        "modified_additional_properties",
        "modified_enums",
        "key_reductions",
    ]
    
    for issue_type in priority_order:
        if issue_type in issues and issues[issue_type]:
            count = len(issues[issue_type])
            print(f"\n{issue_type.upper().replace('_', ' ')}: {count}")
            print("-" * 80)
            
            # Show first 10 examples
            for issue in issues[issue_type][:10]:
                print(f"  - {issue}")
            
            if count > 10:
                print(f"  ... and {count - 10} more")
    
    # Show any other issues
    for issue_type, issue_list in issues.items():
        if issue_type not in priority_order and issue_list:
            print(f"\n{issue_type.upper().replace('_', ' ')}: {len(issue_list)}")
            print("-" * 80)
            for issue in issue_list[:5]:
                print(f"  - {issue}")
            if len(issue_list) > 5:
                print(f"  ... and {len(issue_list) - 5} more")
    
    print("\n" + "=" * 80)


def main() -> int:
    """Main function."""
    if not ORIGINAL_SCHEMA.exists():
        logger.error(f"Original schema not found: {ORIGINAL_SCHEMA}")
        return 1
    
    if not SIMPLIFIED_SCHEMA.exists():
        logger.error(f"Simplified schema not found: {SIMPLIFIED_SCHEMA}")
        return 1
    
    issues = analyze_schemas()
    print_report(issues)
    
    # Save report to file
    report_path = Path(__file__).parent.parent / "schema_analysis_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("SCHEMA SIMPLIFICATION ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        for issue_type, issue_list in sorted(issues.items()):
            if issue_list:
                f.write(f"\n{issue_type.upper().replace('_', ' ')}: {len(issue_list)}\n")
                f.write("-" * 80 + "\n")
                for issue in issue_list:
                    f.write(f"  • {issue}\n")
    
    logger.info(f"\nFull report saved to: {report_path}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

