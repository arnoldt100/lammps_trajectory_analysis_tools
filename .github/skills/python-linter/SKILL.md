---
name: python-linter
description: Use this skill when asked to format, lint, audit, or check Python files for style and PEP 8 compliance.
---

# Python Linter Skill
This skill acts as a static analysis and linting companion for Python files to ensure code quality, readability, and performance.

## When to Use This Skill
- When checking a Python file or code block for syntax issues or style violations.
- Before preparing a Pull Request involving `.py` files.

## Guidelines & Rules
1. **PEP 8 Compliance:** Ensure variable names use `snake_case`, classes use `PascalCase`, and constants use `UPPER_CASE`.
2. **Imports Management:** Flag any unused imports. Ensure imports are grouped logically (standard library, third-party, local modules).
3. **Docstrings & Type Hints:** Check that all public functions, methods, and classes contain clear docstrings and comprehensive type hints.
4. **Complexity:** Alert the user if a function has high cognitive complexity (e.g., nested loops or deeply nested `if` statements).

## Example Suggestion Format
If a violation is found, output the feedback using this format:
- **File/Line:** [Filename or context]
- **Issue:** [Description of style or PEP 8 violation]
- **Suggested Fix:** [Provide a clean code block showing the corrected implementation]

