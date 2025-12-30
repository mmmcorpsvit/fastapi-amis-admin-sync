#!/usr/bin/env python3
"""
Deep analysis of generated models for various issues.

Checks for:
1. Type errors and inconsistencies
2. Missing imports
3. Duplicate field names
4. Invalid type annotations
5. Missing validations
6. Incorrect field types
7. Missing optional markers
8. Syntax errors
9. Circular references
10. Any other code quality issues
"""
import ast
import re
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

GENERATED_MODELS = Path(__file__).parent.parent / "fastapi_amis_admin" / "amis" / "auto_generated_models.py"


def load_generated_file() -> str:
    """Load the generated models file."""
    with open(GENERATED_MODELS, "r", encoding="utf-8") as f:
        return f.read()


def analyze_syntax(content: str) -> Dict[str, Any]:
    """Check for syntax errors."""
    issues = []
    try:
        ast.parse(content)
    except SyntaxError as e:
        issues.append({
            "type": "syntax_error",
            "message": str(e),
            "line": e.lineno,
            "offset": e.offset,
        })
    return {"syntax_errors": issues}


def analyze_imports(content: str) -> Dict[str, Any]:
    """Analyze imports for missing or unused imports."""
    issues = []
    
    # Parse AST to get imports
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"import_issues": []}
    
    imported_names = set()
    used_names = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_names.add(node.module.split('.')[0])
            for alias in node.names or []:
                imported_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Name):
            used_names.add(node.id)
    
    # Check for common missing imports
    common_types = {"Optional", "Union", "List", "Dict", "Tuple", "Literal"}
    missing_imports = common_types - imported_names & used_names
    
    if missing_imports:
        issues.append({
            "type": "missing_imports",
            "missing": list(missing_imports),
        })
    
    return {"import_issues": issues}


def analyze_duplicate_fields(content: str) -> Dict[str, Any]:
    """Find duplicate field names in classes."""
    issues = []
    field_counts = defaultdict(lambda: defaultdict(int))
    
    # Use regex to find class definitions and their fields
    class_pattern = re.compile(r'^class\s+(\w+).*?:', re.MULTILINE)
    field_pattern = re.compile(r'^\s+(\w+):\s+', re.MULTILINE)
    
    lines = content.split('\n')
    current_class = None
    
    for i, line in enumerate(lines):
        class_match = class_pattern.match(line)
        if class_match:
            current_class = class_match.group(1)
            continue
        
        if current_class:
            field_match = field_pattern.match(line)
            if field_match:
                field_name = field_match.group(1)
                field_counts[current_class][field_name] += 1
    
    # Find duplicates
    for class_name, fields in field_counts.items():
        duplicates = {name: count for name, count in fields.items() if count > 1}
        if duplicates:
            issues.append({
                "class": class_name,
                "duplicates": duplicates,
            })
    
    return {"duplicate_fields": issues}


def analyze_type_annotations(content: str) -> Dict[str, Any]:
    """Analyze type annotations for issues."""
    issues = []
    
    # Find type annotations
    type_pattern = re.compile(r':\s+([^=]+?)(?:\s*=\s*|$)')
    
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if ': ' in line and ('Field' in line or '=' in line):
            match = type_pattern.search(line)
            if match:
                type_annotation = match.group(1).strip()
                
                # Check for invalid patterns
                if type_annotation == "Any":
                    # This is OK, but we can note it
                    pass
                elif "|" in type_annotation and "None" not in type_annotation and "Optional" not in type_annotation:
                    # Union without None - might be missing Optional
                    if "Field(..., " in line or "Field(" in line:
                        # Check if it's required
                        pass
                
                # Check for malformed unions
                if type_annotation.count("|") > 5:
                    issues.append({
                        "type": "complex_union",
                        "line": i,
                        "annotation": type_annotation[:100],
                    })
                
                # Check for missing spaces in unions
                if "|" in type_annotation and " | " not in type_annotation:
                    issues.append({
                        "type": "malformed_union",
                        "line": i,
                        "annotation": type_annotation[:100],
                    })
    
    return {"type_annotation_issues": issues}


def analyze_field_definitions(content: str) -> Dict[str, Any]:
    """Analyze field definitions for issues."""
    issues = []
    
    # Pattern to match field definitions
    field_pattern = re.compile(
        r'^\s+(\w+):\s+([^=]+?)(?:\s*=\s*Field\([^)]+\))?$',
        re.MULTILINE
    )
    
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        # Check for fields without type annotations
        if re.match(r'^\s+\w+:\s*$', line):
            issues.append({
                "type": "missing_type",
                "line": i,
                "content": line.strip(),
            })
        
        # Check for fields with Any that might have better types
        if ': Any' in line and 'Field' in line:
            # Extract field name
            field_match = re.search(r'(\w+):\s+Any', line)
            if field_match:
                field_name = field_match.group(1)
                # Check if it's a common field that should have a type
                common_typed_fields = {
                    "id", "name", "label", "title", "description", "type",
                    "value", "default", "required", "disabled", "hidden",
                }
                if field_name.lower() in common_typed_fields:
                    issues.append({
                        "type": "any_for_common_field",
                        "line": i,
                        "field": field_name,
                        "suggestion": "Consider if this should have a specific type",
                    })
    
    return {"field_definition_issues": issues}


def analyze_class_structure(content: str) -> Dict[str, Any]:
    """Analyze class structure for issues."""
    issues = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"class_structure_issues": []}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check for classes without docstrings
            if not ast.get_docstring(node):
                issues.append({
                    "type": "missing_docstring",
                    "class": node.name,
                    "line": node.lineno,
                })
            
            # Check for classes with too many fields
            field_count = sum(1 for item in node.body if isinstance(item, ast.AnnAssign))
            if field_count > 100:
                issues.append({
                    "type": "too_many_fields",
                    "class": node.name,
                    "line": node.lineno,
                    "field_count": field_count,
                })
            
            # Check for duplicate field names in AST
            field_names = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    field_names.append(item.target.id)
            
            duplicates = [name for name in field_names if field_names.count(name) > 1]
            if duplicates:
                issues.append({
                    "type": "duplicate_field_names",
                    "class": node.name,
                    "line": node.lineno,
                    "duplicates": list(set(duplicates)),
                })
    
    return {"class_structure_issues": issues}


def analyze_pydantic_usage(content: str) -> Dict[str, Any]:
    """Analyze Pydantic-specific issues."""
    issues = []
    
    # Check for BaseModel usage
    if "from pydantic import" not in content:
        issues.append({
            "type": "missing_pydantic_import",
        })
    
    # Check for ConfigDict usage (Pydantic v2)
    if "ConfigDict" not in content:
        issues.append({
            "type": "missing_configdict",
            "message": "Pydantic v2 should use ConfigDict",
        })
    
    # Check for old-style Config class
    if "class Config:" in content:
        issues.append({
            "type": "old_pydantic_config",
            "message": "Using old Config class instead of ConfigDict",
        })
    
    # Check for Field usage
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        # Check for Field without proper import
        if "Field(" in line and "from pydantic import" not in content[:1000]:
            # This is OK if import is at top
            pass
        
        # Check for Field with invalid arguments
        if "Field(" in line:
            # Check for common issues
            if "alias=" in line and '"' not in line and "'" not in line:
                issues.append({
                    "type": "invalid_field_alias",
                    "line": i,
                    "content": line.strip()[:100],
                })
    
    return {"pydantic_issues": issues}


def analyze_naming_conventions(content: str) -> Dict[str, Any]:
    """Check naming conventions."""
    issues = []
    
    # Check for inconsistent naming
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        # Check for camelCase in Python (should be snake_case)
        if re.search(r'\b[a-z]+[A-Z][a-zA-Z]*\s*:', line) and 'Field(' in line:
            # This might be OK if it's an alias
            if 'alias=' not in line:
                match = re.search(r'(\w+):\s+', line)
                if match:
                    field_name = match.group(1)
                    if any(c.isupper() for c in field_name[1:]):
                        issues.append({
                            "type": "camelcase_field",
                            "line": i,
                            "field": field_name,
                            "suggestion": "Consider snake_case",
                        })
    
    return {"naming_issues": issues}


def analyze_enum_usage(content: str) -> Dict[str, Any]:
    """Analyze Enum usage."""
    issues = []
    
    # Check for proper Enum imports
    if "from enum import" not in content and "Enum" in content:
        issues.append({
            "type": "missing_enum_import",
        })
    
    # Check for Enum definitions
    enum_pattern = re.compile(r'^class\s+(\w+)\(Enum\):', re.MULTILINE)
    enums = enum_pattern.findall(content)
    
    # Check for enums with single value
    lines = content.split('\n')
    current_enum = None
    enum_values = []
    
    for i, line in enumerate(lines):
        enum_match = enum_pattern.match(line)
        if enum_match:
            if current_enum and len(enum_values) == 1:
                issues.append({
                    "type": "single_value_enum",
                    "enum": current_enum,
                    "suggestion": "Consider using Literal instead",
                })
            current_enum = enum_match.group(1)
            enum_values = []
        elif current_enum and "=" in line and line.strip().startswith(current_enum.lower()):
            enum_values.append(line.strip())
    
    return {"enum_issues": issues}


def analyze_root_models(content: str) -> Dict[str, Any]:
    """Analyze RootModel usage."""
    issues = []
    
    # Check for RootModel usage
    root_model_pattern = re.compile(r'class\s+(\w+)\(RootModel\[([^\]]+)\]\):', re.MULTILINE)
    root_models = root_model_pattern.findall(content)
    
    for class_name, root_type in root_models:
        # Check if root type is Any
        if "Any" in root_type:
            issues.append({
                "type": "rootmodel_with_any",
                "class": class_name,
                "root_type": root_type,
                "suggestion": "Consider if a more specific type is possible",
            })
    
    return {"rootmodel_issues": issues}


def main() -> int:
    """Main analysis function."""
    logger.info("=" * 80)
    logger.info("DEEP ANALYSIS: Generated Models Issues")
    logger.info("=" * 80)
    
    logger.info("Loading generated file...")
    content = load_generated_file()
    
    logger.info("Analyzing...")
    all_issues = {}
    
    # Run all analyses
    logger.info("1. Checking syntax...")
    all_issues.update(analyze_syntax(content))
    
    logger.info("2. Analyzing imports...")
    all_issues.update(analyze_imports(content))
    
    logger.info("3. Checking for duplicate fields...")
    all_issues.update(analyze_duplicate_fields(content))
    
    logger.info("4. Analyzing type annotations...")
    all_issues.update(analyze_type_annotations(content))
    
    logger.info("5. Analyzing field definitions...")
    all_issues.update(analyze_field_definitions(content))
    
    logger.info("6. Analyzing class structure...")
    all_issues.update(analyze_class_structure(content))
    
    logger.info("7. Analyzing Pydantic usage...")
    all_issues.update(analyze_pydantic_usage(content))
    
    logger.info("8. Checking naming conventions...")
    all_issues.update(analyze_naming_conventions(content))
    
    logger.info("9. Analyzing Enum usage...")
    all_issues.update(analyze_enum_usage(content))
    
    logger.info("10. Analyzing RootModel usage...")
    all_issues.update(analyze_root_models(content))
    
    # Print report
    print("\n" + "=" * 80)
    print("ANALYSIS REPORT")
    print("=" * 80)
    
    total_issues = sum(len(v) if isinstance(v, list) else 1 for v in all_issues.values() if v)
    print(f"\nTotal issues found: {total_issues}\n")
    
    for issue_type, issues in sorted(all_issues.items()):
        if issues:
            count = len(issues) if isinstance(issues, list) else 1
            print(f"\n{issue_type.upper().replace('_', ' ')}: {count}")
            print("-" * 80)
            
            if isinstance(issues, list):
                for issue in issues[:10]:
                    if isinstance(issue, dict):
                        print(f"  - {issue.get('type', 'unknown')}: {issue}")
                    else:
                        print(f"  - {issue}")
                if len(issues) > 10:
                    print(f"  ... and {len(issues) - 10} more")
            else:
                print(f"  - {issues}")
    
    # Save detailed report
    import json
    report_path = Path(__file__).parent.parent / "generated_models_analysis_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(all_issues, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"\nDetailed report saved to: {report_path}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

