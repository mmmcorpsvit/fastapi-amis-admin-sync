#!/usr/bin/env python3
"""
Find actual duplicate field definitions in generated models.
"""
import ast
import re
from collections import defaultdict
from pathlib import Path

GENERATED_MODELS = Path(__file__).parent.parent / "fastapi_amis_admin" / "amis" / "auto_generated_models.py"


def find_duplicate_fields():
    """Find classes with duplicate field names."""
    with open(GENERATED_MODELS, "r", encoding="utf-8") as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error: {e}")
        return
    
    duplicates_found = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            field_names = []
            field_lines = {}
            
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    field_name = item.target.id
                    field_names.append(field_name)
                    if field_name not in field_lines:
                        field_lines[field_name] = []
                    field_lines[field_name].append(item.lineno)
            
            # Find duplicates
            seen = set()
            duplicates = {}
            for field_name in field_names:
                if field_name in seen:
                    if field_name not in duplicates:
                        duplicates[field_name] = []
                    duplicates[field_name].append(field_lines[field_name][-1])
                else:
                    seen.add(field_name)
            
            if duplicates:
                duplicates_found.append({
                    "class": node.name,
                    "line": node.lineno,
                    "duplicates": duplicates,
                })
    
    if duplicates_found:
        print("=" * 80)
        print("DUPLICATE FIELD DEFINITIONS FOUND:")
        print("=" * 80)
        for dup in duplicates_found:
            print(f"\nClass {dup['class']} (line {dup['line']}):")
            for field, lines in dup['duplicates'].items():
                print(f"  - {field}: appears on lines {lines}")
    else:
        print("No duplicate field definitions found in AST.")
    
    # Also check using regex for fields that appear multiple times
    print("\n" + "=" * 80)
    print("CHECKING FOR MULTIPLE FIELD DEFINITIONS (regex):")
    print("=" * 80)
    
    lines = content.split('\n')
    current_class = None
    class_fields = defaultdict(lambda: defaultdict(list))
    
    for i, line in enumerate(lines, 1):
        class_match = re.match(r'^class\s+(\w+)', line)
        if class_match:
            current_class = class_match.group(1)
            continue
        
        if current_class:
            field_match = re.match(r'^\s+(\w+):\s+', line)
            if field_match:
                field_name = field_match.group(1)
                class_fields[current_class][field_name].append(i)
    
    for class_name, fields in class_fields.items():
        duplicates = {name: lines for name, lines in fields.items() if len(lines) > 1}
        if duplicates:
            print(f"\nClass {class_name}:")
                for field, line_nums in duplicates.items():
                    print(f"  - {field}: appears on lines {line_nums}")


if __name__ == "__main__":
    find_duplicate_fields()

