import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Any

class ImprovementAgent:
    """
    Agent 6: Code Improvement Agent
    Identifies concrete performance optimizations, modernization opportunities,
    type-safety enhancements, and repository architecture improvements.
    Generates actionable Before & After refactoring snippets.
    """

    def __init__(self, max_files: int = 80):
        self.max_files = max_files

    def analyze(self, repo_path: str, files_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze code and repository structure for optimization opportunities.
        """
        repo_dir = Path(repo_path).resolve()
        improvements: List[Dict[str, Any]] = []

        code_files = [
            f for f in files_info
            if f.get("language") in {"Python", "JavaScript", "TypeScript"}
        ][:self.max_files]

        # 1. Project-level Architecture & Hygiene Check
        self._check_repo_hygiene(repo_dir, files_info, improvements)

        # 2. File-level & AST Optimizations
        for file_info in code_files:
            rel_path = file_info["path"]
            full_path = repo_dir / rel_path
            lang = file_info["language"]

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue

            lines = content.splitlines()

            if lang == "Python":
                self._check_python_improvements(content, lines, rel_path, improvements)
            elif lang in {"JavaScript", "TypeScript"}:
                self._check_js_improvements(content, lines, rel_path, improvements)

        # Group by category
        categories = {}
        for imp in improvements:
            cat = imp.get("category", "General")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_improvements": len(improvements),
            "category_breakdown": categories,
            "improvements": improvements,
        }

    def _check_repo_hygiene(self, repo_dir: Path, files_info: List[Dict[str, Any]], improvements: List[Dict[str, Any]]):
        """Check repository-wide files (tests, gitignore, CI/CD, license)."""
        file_names = {os.path.basename(f["path"]).lower() for f in files_info}
        paths_lower = [f["path"].lower() for f in files_info]

        # Check for tests
        has_tests = any("test" in p for p in paths_lower)
        if not has_tests:
            improvements.append({
                "category": "Testing & QA",
                "file": "Repository Root",
                "line": 1,
                "title": "Missing Automated Test Suite",
                "impact": "High Reliability Risk",
                "explanation": "No automated test directory (e.g. `tests/`, `__tests__/`) or test files were identified.",
                "before": "# No tests found",
                "after": "# Add pytest or unittest test suite\n# e.g., tests/test_core.py\ndef test_feature():\n    assert run() == expected",
                "benefit": "Enables regression testing and safe continuous refactoring."
            })

        # Check for .gitignore
        if ".gitignore" not in file_names:
            improvements.append({
                "category": "DevOps",
                "file": ".gitignore",
                "line": 1,
                "title": "Missing `.gitignore` File",
                "impact": "Repository Cleanliness",
                "explanation": "Repository lacks a `.gitignore` file, which risks committing bytecode, `.env` secrets, and `node_modules`.",
                "before": "# Missing .gitignore",
                "after": "# Create .gitignore with:\n__pycache__/\n*.pyc\n.env\nvenv/\nnode_modules/\n.DS_Store",
                "benefit": "Prevents accidental credential leaks and workspace bloat in git history."
            })

        # Check for CI/CD workflow
        has_ci = any(".github/workflows" in p or "gitlab-ci" in p for p in paths_lower)
        if not has_ci:
            improvements.append({
                "category": "DevOps",
                "file": ".github/workflows/ci.yml",
                "line": 1,
                "title": "Missing Continuous Integration (CI) Pipeline",
                "impact": "Automation",
                "explanation": "Automated build and test workflows (GitHub Actions / GitLab CI) are not configured.",
                "before": "# Manual deployment and testing",
                "after": "name: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: pip install -r requirements.txt && pytest",
                "benefit": "Automates linting, test suites, and build verification on every pull request."
            })

    def _check_python_improvements(self, content: str, lines: List[str], rel_path: str, improvements: List[Dict[str, Any]]):
        """Analyze Python source for idiomatic modernization and performance gains."""
        try:
            tree = ast.parse(content, filename=rel_path)
        except Exception:
            return

        for node in ast.walk(tree):
            # 1. Loop append -> List comprehension optimization
            if isinstance(node, ast.For) and len(node.body) == 1:
                stmt = node.body[0]
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    call = stmt.value
                    if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
                        target_list = getattr(call.func.value, 'id', 'list_var')
                        item_expr = "..."
                        if hasattr(ast, 'unparse') and call.args:
                            item_expr = ast.unparse(call.args[0])
                        target_iter = "..."
                        if hasattr(ast, 'unparse'):
                            target_iter = ast.unparse(node.iter)
                            target_var = ast.unparse(node.target)
                        else:
                            target_var = "item"

                        line_no = node.lineno
                        improvements.append({
                            "category": "Performance",
                            "file": rel_path,
                            "line": line_no,
                            "title": "Replace `for` loop `.append()` with List Comprehension",
                            "impact": "2x-3x Faster Iteration",
                            "explanation": f"Using `.append()` in a loop incurs repeated method resolution overhead. List comprehensions are executed in C-level loops.",
                            "before": f"result = []\nfor {target_var} in {target_iter}:\n    result.append({item_expr})",
                            "after": f"result = [{item_expr} for {target_var} in {target_iter}]",
                            "benefit": "Significantly faster execution speed and more idiomatic Python."
                        })

            # 2. Generator expressions in aggregations (e.g. sum([x for x in ...]))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("sum", "any", "all", "min", "max") and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.ListComp):
                        line_no = node.lineno
                        improvements.append({
                            "category": "Memory Optimization",
                            "file": rel_path,
                            "line": line_no,
                            "title": f"Use Generator Expression inside `{node.func.id}()`",
                            "impact": "O(1) Memory Usage",
                            "explanation": f"`{node.func.id}([...])` allocates the entire list in memory before computing the aggregate.",
                            "before": f"{node.func.id}([x for x in iterable])",
                            "after": f"{node.func.id}(x for x in iterable)",
                            "benefit": "Streams data lazily without allocating intermediate memory buffers."
                        })

            # 3. Functions missing type annotations
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                unannotated_args = [a.arg for a in node.args.args if a.annotation is None and a.arg != "self"]
                if unannotated_args and node.returns is None:
                    line_no = node.lineno
                    if len(improvements) < 25:  # avoid spamming
                        improvements.append({
                            "category": "Type Safety",
                            "file": rel_path,
                            "line": line_no,
                            "title": f"Add Static Type Annotations to `{node.name}()`",
                            "impact": "Developer Experience & Reliability",
                            "explanation": f"Function `{node.name}` lacks type annotations for parameters (`{', '.join(unannotated_args[:3])}`) and return value.",
                            "before": f"def {node.name}({', '.join(unannotated_args[:2])}):\n    ...",
                            "after": f"def {node.name}({': str, '.join(unannotated_args[:2])}: str) -> bool:\n    ...",
                            "benefit": "Enables static type checking (mypy/pyright), improves IDE code-completion, and documents function contracts."
                        })

        # Regex checks on source lines
        for idx, line in enumerate(lines):
            line_no = idx + 1
            # 4. Outdated % formatting
            if re.search(r'[\'"][^\'"]*%[sd][^\'"]*[\'"]\s*%', line) and not line.strip().startswith("#"):
                if len(improvements) < 25:
                    improvements.append({
                        "category": "Modernization",
                        "file": rel_path,
                        "line": line_no,
                        "title": "Modernize `%` String Formatting to f-strings",
                        "impact": "Readability & Speed",
                        "explanation": "Python 3.6+ f-strings are faster, more readable, and less error-prone than legacy `%` formatting.",
                        "before": line.strip(),
                        "after": 'f"... {variable} ..."',
                        "benefit": "Improved readability and up to 30% faster string interpolation."
                    })

    def _check_js_improvements(self, content: str, lines: List[str], rel_path: str, improvements: List[Dict[str, Any]]):
        """Analyze JavaScript and TypeScript for modern ES6+ idioms."""
        for idx, line in enumerate(lines):
            line_no = idx + 1
            stripped = line.strip()

            # 1. Use of var instead of const/let
            if re.search(r'\bvar\s+[a-zA-Z0-9_$]+\s*=', stripped) and not stripped.startswith("//"):
                if len(improvements) < 25:
                    improvements.append({
                        "category": "Modernization",
                        "file": rel_path,
                        "line": line_no,
                        "title": "Replace Legacy `var` with `const` or `let`",
                        "impact": "Scope Safety",
                        "explanation": "`var` is function-scoped and hoisted, causing accidental variable leaks and shadowing bugs.",
                        "before": stripped,
                        "after": stripped.replace("var ", "const "),
                        "benefit": "Enforces block-scoping and prevents unintended mutation."
                    })
                    break
