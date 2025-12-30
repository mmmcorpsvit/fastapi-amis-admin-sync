#!/usr/bin/env python3
"""
Highly optimized, fully iterative schema standardization for AMIS schema.

This script uses a professional, graph-based approach to be extremely fast and robust:
1.  Builds a lightweight dependency graph of all definitions.
2.  Runs a fast cycle detection algorithm on the small graph to identify all
    definitions that are part of any cycle.
3.  Performs a single, fast, and FULLY ITERATIVE pass over the schema to apply all
    fixes, making it immune to recursion depth errors.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Set, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INPUT_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "schema_translated.json"
OUTPUT_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "schema_simplified.json"

def create_valid_badge_object() -> Dict[str, Any]:
    """Creates a known-good schema for the Badge object."""
    return {
        "type": "object",
        "properties": {
            "text": {"anyOf": [{"type": "string"}, {"type": "number"}]},
            "level": {"type": "string", "enum": ["success", "warning", "danger", "info", "primary"]},
        },
        "additionalProperties": True,
    }

def find_all_refs(obj: Any) -> Set[str]:
    """Recursively finds all unique $ref values within a JSON object."""
    refs = set()
    if isinstance(obj, dict):
        if "$ref" in obj and isinstance(obj["$ref"], str):
            refs.add(obj["$ref"].split("/")[-1])
        for value in obj.values():
            refs.update(find_all_refs(value))
    elif isinstance(obj, list):
        for item in obj:
            refs.update(find_all_refs(item))
    return refs

def find_cyclic_definitions(definitions: Dict[str, Any]) -> Set[str]:
    """
    Finds all definitions that are part of any cycle using a graph-based approach.
    Returns a set of the names of all definitions involved in at least one cycle.
    """
    logger.info("Building schema dependency graph...")
    graph = {name: find_all_refs(defn) for name, defn in definitions.items()}

    visiting = set()
    visited = set()
    cyclic_nodes = set()

    def dfs(node):
        visiting.add(node)
        for neighbor in graph.get(node, []):
            if neighbor in cyclic_nodes:
                cyclic_nodes.add(node)
                continue
            if neighbor in visiting:
                cyclic_nodes.add(neighbor)
                cyclic_nodes.add(node)
                continue
            if neighbor not in visited:
                if dfs(neighbor):
                    cyclic_nodes.add(node)
        visiting.remove(node)
        visited.add(node)
        return node in cyclic_nodes

    logger.info("Detecting all cyclic definitions in the graph...")
    for node in graph:
        if node not in visited:
            dfs(node)
            
    logger.info(f"Found {len(cyclic_nodes)} definitions involved in cycles.")
    return cyclic_nodes

def apply_fixes_iterative(schema: Dict[str, Any], cyclic_definitions: Set[str]) -> Tuple[Dict[str, Any], int]:
    """
    Performs a single, fully iterative pass to fix structural issues and wrap cyclic $refs.
    This is immune to RecursionError.
    """
    fixes_applied = 0
    stack = [schema]
    processed_ids = set()

    logger.info("Applying all fixes in a single, non-recursive pass...")
    
    while stack:
        obj = stack.pop()
        
        obj_id = id(obj)
        if obj_id in processed_ids:
            continue
        
        if isinstance(obj, dict):
            processed_ids.add(obj_id)
            # Fix structural issue: `type: ["string", "number"]`
            if "type" in obj and isinstance(obj["type"], list):
                obj["anyOf"] = [{"type": t} for t in obj.pop("type")]
                fixes_applied += 1
            
            # Fix cyclic $ref
            if "$ref" in obj and isinstance(obj["$ref"], str):
                ref_name = obj["$ref"].split("/")[-1]
                if ref_name in cyclic_definitions:
                    ref = obj.pop("$ref")
                    obj["anyOf"] = [{"$ref": ref}]
                    fixes_applied += 1
            
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(obj, list):
            processed_ids.add(obj_id)
            for item in obj:
                if isinstance(item, (dict, list)):
                    stack.append(item)

    return schema, fixes_applied

def main() -> int:
    """Main function to run the schema standardization."""
    logger.info("=" * 70)
    logger.info("Comprehensive AMIS Schema Standardization (Optimized & Iterative)")
    logger.info("=" * 70)

    if not INPUT_SCHEMA_PATH.exists():
        logger.error(f"Input schema not found: {INPUT_SCHEMA_PATH}")
        return 1

    logger.info(f"Loading schema from: {INPUT_SCHEMA_PATH}")
    schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    definitions = schema.get("definitions", {})

    # --- Run Optimized Passes ---
    cyclic_defs = find_cyclic_definitions(definitions)
    schema, total_fixes = apply_fixes_iterative(schema, cyclic_defs)

    # --- Final Targeted Fixes ---
    logger.info("Applying final targeted fixes...")
    if 'TplSchema' in definitions:
        tpl_schema = definitions['TplSchema']
        if 'allOf' in tpl_schema:
            for item in tpl_schema.get('allOf', []):
                if 'properties' in item and 'badge' in item['properties']:
                    if item['properties']['badge'] != create_valid_badge_object():
                        item['properties']['badge'] = create_valid_badge_object()
                        total_fixes += 1
    
    # --- Save ---
    logger.info(f"Saving standardized schema to: {OUTPUT_SCHEMA_PATH}")
    OUTPUT_SCHEMA_PATH.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("\n" + "=" * 70)
    logger.info("✅ Schema standardization complete!")
    logger.info(f"Total fixes applied: {total_fixes}")
    logger.info(f"Output written to: {OUTPUT_SCHEMA_PATH}")
    logger.info("=" * 70)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
