#!/usr/bin/env python3
"""
Post-process generated models to fix union types that should include primitives.

This script fixes cases where fields should be `str | dict[str, Any]` but are
generated as just `dict[str, Any]` or `Any`.

It works by:
1. Finding fields with descriptions that mention "string or object"
2. Checking if the type is missing the string option
3. Fixing the type annotation
"""
import ast
import logging
import re
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Patterns that indicate a field should support string | dict
STRING_OR_OBJECT_PATTERNS = [
    r"string or object",
    r"configured as a string or object",
    r"can be.*string.*or.*object",
    r"string.*or.*object",
]

# Common field names that should be str | dict[str, Any]
COMMON_STRING_OR_DICT_FIELDS = {
    "class_name",
    "className",
    "static_class_name",
    "staticClassName",
    "body_class_name",
    "bodyClassName",
    "aside_class_name",
    "asideClassName",
    "header_class_name",
    "headerClassName",
    "toolbar_class_name",
    "toolbarClassName",
    "tooltip_class_name",
    "tooltipClassName",
    "static_label_class_name",
    "staticLabelClassName",
    "static_input_class_name",
    "staticInputClassName",
}


def should_be_string_or_dict(field_name: str, description: str | None) -> bool:
    """
    Check if a field should be str | dict[str, Any] based on name and description.
    
    Args:
        field_name: Name of the field
        description: Field description
    
    Returns:
        True if field should support string | dict
    """
    # Check common field names
    if field_name.lower() in COMMON_STRING_OR_DICT_FIELDS:
        return True
    
    # Check description patterns
    if description:
        desc_lower = description.lower()
        for pattern in STRING_OR_OBJECT_PATTERNS:
            if re.search(pattern, desc_lower):
                return True
    
    return False


def fix_type_annotation(node: ast.AnnAssign) -> ast.AnnAssign | None:
    """
    Fix type annotation for a field if it should be str | dict[str, Any].
    
    Args:
        node: AST node for field assignment
    
    Returns:
        Modified node or None if no change needed
    """
    if not isinstance(node.annotation, ast.BinOp):
        # Not a union type, might need fixing
        if isinstance(node.annotation, ast.Name) and node.annotation.id == "Any":
            # Check if this should be str | dict
            field_name = node.target.id if isinstance(node.target, ast.Name) else None
            description = None
            
            # Try to extract description from Field() call
            if isinstance(node.value, ast.Call):
                for keyword in node.value.keywords:
                    if keyword.arg == "description" and isinstance(keyword.value, ast.Constant):
                        description = keyword.value.value
            
            if should_be_string_or_dict(field_name or "", description):
                # Create str | dict[str, Any] | None
                return create_string_or_dict_union(node, make_optional=True)
        
        elif isinstance(node.annotation, ast.Subscript):
            # Check if it's dict[str, Any] and should include str
            if isinstance(node.annotation.value, ast.Name) and node.annotation.value.id == "dict":
                field_name = node.target.id if isinstance(node.target, ast.Name) else None
                description = None
                
                if isinstance(node.value, ast.Call):
                    for keyword in node.value.keywords:
                        if keyword.arg == "description" and isinstance(keyword.value, ast.Constant):
                            description = keyword.value.value
                
                if should_be_string_or_dict(field_name or "", description):
                    # Create str | dict[str, Any] | None
                    return create_string_or_dict_union(node, make_optional=True)
    
    return None


def create_string_or_dict_union(node: ast.AnnAssign, make_optional: bool = False) -> ast.AnnAssign:
    """
    Create a union type str | dict[str, Any] (optionally with None).
    
    Args:
        node: Original annotation node
        make_optional: Whether to add None to the union
    
    Returns:
        New annotation node
    """
    # Create str
    str_type = ast.Name(id="str", ctx=ast.Load())
    
    # Create dict[str, Any]
    dict_type = ast.Subscript(
        value=ast.Name(id="dict", ctx=ast.Load()),
        slice=ast.Tuple(
            elts=[
                ast.Name(id="str", ctx=ast.Load()),
                ast.Name(id="Any", ctx=ast.Load()),
            ],
            ctx=ast.Load(),
        ),
        ctx=ast.Load(),
    )
    
    # Create str | dict[str, Any]
    union = ast.BinOp(left=str_type, op=ast.BitOr(), right=dict_type)
    
    # Add None if needed
    if make_optional:
        union = ast.BinOp(
            left=union,
            op=ast.BitOr(),
            right=ast.Constant(value=None),
        )
    
    # Create new node with fixed annotation
    new_node = ast.AnnAssign(
        target=node.target,
        annotation=union,
        value=node.value,
        simple=node.simple,
    )
    
    return new_node


def fix_file(file_path: Path) -> bool:
    """
    Fix union types in a generated Python file.
    
    Args:
        file_path: Path to the generated models file
    
    Returns:
        True if file was modified, False otherwise
    """
    logger.info(f"Reading {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        logger.error(f"Syntax error in {file_path}: {e}")
        return False
    
    # Track if we made changes
    modified = False
    
    # Walk through AST and fix annotations
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            fixed = fix_type_annotation(node)
            if fixed:
                # Replace the node (this is simplified - actual replacement needs more work)
                logger.info(f"Would fix: {ast.unparse(node) if hasattr(ast, 'unparse') else node}")
                modified = True
    
    if modified:
        # For now, we'll use a simpler regex-based approach
        logger.info("Using regex-based fix instead of AST manipulation")
        return fix_file_regex(file_path)
    
    return False


def fix_file_regex(file_path: Path) -> bool:
    """
    Fix union types using regex (simpler but less precise).
    
    Args:
        file_path: Path to the generated models file
    
    Returns:
        True if file was modified, False otherwise
    """
    logger.info(f"Fixing union types in {file_path} using regex")
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        original_line = line
        
        # Look for className fields that are dict[str, Any] but should be str | dict[str, Any]
        if "class_name" in line or "className" in line:
            # Check if next few lines contain description about "string or object"
            lookahead = "".join(lines[i:min(i+5, len(lines))]).lower()
            
            if any(pattern in lookahead for pattern in STRING_OR_OBJECT_PATTERNS):
                # Check if current line has dict[str, Any] but not str |
                if "dict[str, Any]" in line and "str |" not in line:
                    # Replace dict[str, Any] with str | dict[str, Any]
                    line = line.replace("dict[str, Any]", "str | dict[str, Any]")
                    if line != original_line:
                        modified = True
                        logger.info(f"Fixed line {i+1}: {line.strip()}")
        
        new_lines.append(line)
        i += 1
    
    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        logger.info(f"✅ Fixed union types in {file_path}")
        return True
    
    return False


def main() -> int:
    """Main function."""
    import sys
    
    if len(sys.argv) < 2:
        logger.error("Usage: fix_union_types.py <path_to_generated_models.py>")
        return 1
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 1
    
    if fix_file_regex(file_path):
        logger.info("✅ Union types fixed successfully!")
        return 0
    else:
        logger.info("ℹ️  No changes needed")
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

