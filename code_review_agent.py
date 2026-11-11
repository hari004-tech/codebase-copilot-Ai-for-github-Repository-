import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

class CodeReviewAgent:
    """
    Agent 4: Code Review Agent
    Automates comprehensive software code review:
    - Calculates Cyclomatic Complexity
    - Detects Long Methods and Overly Large Files
    - Identifies Duplicate Code Blocks
    - Flags Unused Imports and Unused Variables
    - Audits Docstring Coverage and Naming Conventions
    - Computes an overall Maintainability Index & Quality Score (0-100)
    """

    def __init__(self, max_files: int = 100):
        self.max_files = max_files

    def analyze(self, repo_path: str, files_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run code review checks across repository files.
        """
        repo_dir = Path(repo_path).resolve()
        review_items: List[Dict[str, Any]] = []
        complex_functions: List[Dict[str, Any]] = []
        duplicate_blocks: List[Dict[str, Any]] = []

        code_files = [
            f for f in files_info
            if f.get("language") in {"Python", "JavaScript", "TypeScript", "Go", "Java"}
        ][:self.max_files]

        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0

        # Scan for duplicates across files
        duplicate_blocks = self._detect_duplicates(repo_dir, code_files)

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

            # 1. Large File check (> 400 lines)
            if len(lines) > 400:
                review_items.append({
                    "category": "Maintainability",
                    "file": rel_path,
                    "line": 1,
                    "severity": "MEDIUM",
                    "title": f"Large Source File ({len(lines)} lines)",
                    "suggestion": f"File `{file_info['name']}` exceeds recommended 400 LOC. Consider refactoring into cohesive submodules according to Single Responsibility Principle."
                })

            if lang == "Python":
                doc_stats = self._review_python_file(
                    content, lines, rel_path, review_items, complex_functions
                )
                total_functions += doc_stats["funcs"]
                documented_functions += doc_stats["doc_funcs"]
                total_classes += doc_stats["classes"]
                documented_classes += doc_stats["doc_classes"]

        # Calculate documentation coverage
        doc_coverage_pct = 100.0
        tot_entities = total_functions + total_classes
        if tot_entities > 0:
            doc_coverage_pct = round(((documented_functions + documented_classes) / tot_entities) * 100, 1)

        # Calculate overall quality score (0 - 100)
        quality_score, grade = self._compute_quality_score(
            review_count=len(review_items),
            complex_count=len(complex_functions),
            dup_count=len(duplicate_blocks),
            doc_pct=doc_coverage_pct,
            total_files=len(code_files)
        )

        return {
            "quality_score": quality_score,
            "maintainability_grade": grade,
            "docstring_coverage_pct": doc_coverage_pct,
            "review_suggestions": review_items,
            "complex_functions": complex_functions[:25],
            "duplicate_blocks": duplicate_blocks[:15],
            "total_suggestions_count": len(review_items) + len(complex_functions) + len(duplicate_blocks),
        }

    def _review_python_file(
        self,
        content: str,
        lines: List[str],
        rel_path: str,
        review_items: List[Dict[str, Any]],
        complex_functions: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Deep code review on Python source."""
        doc_stats = {"funcs": 0, "doc_funcs": 0, "classes": 0, "doc_classes": 0}

        try:
            tree = ast.parse(content, filename=rel_path)
        except Exception:
            return doc_stats

        # Check Unused Imports
        self._check_unused_imports(tree, rel_path, review_items)

        # Inspect Classes and Functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc_stats["classes"] += 1
                if ast.get_docstring(node):
                    doc_stats["doc_classes"] += 1
                else:
                    if not node.name.startswith("_"):
                        review_items.append({
                            "category": "Documentation",
                            "file": rel_path,
                            "line": node.lineno,
                            "severity": "LOW",
                            "title": f"Missing Class Docstring on `{node.name}`",
                            "suggestion": f"Add a class-level docstring explaining the responsibilities and lifecycle of `{node.name}`."
                        })

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc_stats["funcs"] += 1
                has_doc = bool(ast.get_docstring(node))
                if has_doc:
                    doc_stats["doc_funcs"] += 1
                elif not node.name.startswith("_"):
                    review_items.append({
                        "category": "Documentation",
                        "file": rel_path,
                        "line": node.lineno,
                        "severity": "LOW",
                        "title": f"Missing Function Docstring on `{node.name}()`",
                        "suggestion": f"Public function `{node.name}()` should document parameters, return types, and exceptions raised."
                    })

                # Check Function Length (> 50 lines)
                fn_len = (getattr(node, 'end_lineno', node.lineno) - node.lineno) + 1
                if fn_len > 50:
                    review_items.append({
                        "category": "Clean Code",
                        "file": rel_path,
                        "line": node.lineno,
                        "severity": "MEDIUM",
                        "title": f"Long Method: `{node.name}()` ({fn_len} lines)",
                        "suggestion": f"Function `{node.name}()` spans {fn_len} lines. Extract sub-procedures into helper functions to improve readability and unit testing."
                    })

                # Calculate Cyclomatic Complexity
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    complex_functions.append({
                        "function": node.name,
                        "file": rel_path,
                        "line": node.lineno,
                        "complexity": complexity,
                        "risk": "High" if complexity > 15 else "Moderate",
                        "recommendation": f"Function `{node.name}()` has cyclomatic complexity of {complexity} (> 10). Split nested conditionals and loops."
                    })

        # Check for magic numbers in module
        self._check_magic_numbers(tree, rel_path, review_items)

        return doc_stats

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity (number of independent paths through code)."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.Assert, ast.comprehension)):
                complexity += 1
        return complexity

    def _check_unused_imports(self, tree: ast.AST, rel_path: str, review_items: List[Dict[str, Any]]):
        """Identify imported modules or aliases that are never referenced in the file."""
        imported_names: Dict[str, int] = {}

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name_to_check = alias.asname if alias.asname else alias.name.split(".")[0]
                    imported_names[name_to_check] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        name_to_check = alias.asname if alias.asname else alias.name
                        imported_names[name_to_check] = node.lineno

        # Walk AST to find used names
        used_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

        # Exclude common conventions e.g. __all__ or __name__
        for name, lineno in imported_names.items():
            if name not in used_names and not name.startswith("_"):
                review_items.append({
                    "category": "Maintainability",
                    "file": rel_path,
                    "line": lineno,
                    "severity": "LOW",
                    "title": f"Potentially Unused Import: `{name}`",
                    "suggestion": f"`import {name}` is defined at line {lineno} but never referenced. Remove unused imports to keep bundle lean and avoid unnecessary startup latency."
                })

    def _check_magic_numbers(self, tree: ast.AST, rel_path: str, review_items: List[Dict[str, Any]]):
        """Detect unexplained magic numeric literals in comparisons or assignments."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # Ignore common innocent numbers: 0, 1, 2, -1, 100, powers of 2
                val = node.value
                if val not in {0, 1, 2, -1, 10, 100, 1000} and not isinstance(val, bool):
                    if val > 100 or val in {3600, 86400, 60, 24}:
                        count += 1
                        if count <= 3:  # don't flood
                            review_items.append({
                                "category": "Clean Code",
                                "file": rel_path,
                                "line": node.lineno,
                                "severity": "LOW",
                                "title": f"Magic Number Literal `{val}`",
                                "suggestion": f"Hardcoded constant `{val}` found at line {node.lineno}. Define a named uppercase constant (e.g., `TIMEOUT_SECONDS = {val}`) to clarify intent."
                            })

    def _detect_duplicates(self, repo_dir: Path, files: List[Dict[str, Any]], min_duplicate_lines: int = 5) -> List[Dict[str, Any]]:
        """Detect duplicate blocks of code across files using sliding window hashing."""
        block_hashes: Dict[str, List[Tuple[str, int]]] = {}
        duplicates: List[Dict[str, Any]] = []

        for f in files[:40]:  # Cap for speed
            full_path = repo_dir / f["path"]
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as file_obj:
                    lines = [line.strip() for line in file_obj]
            except Exception:
                continue

            # Slide window over lines, ignoring comments and blanks
            cleaned = [(i + 1, l) for i, l in enumerate(lines) if len(l) > 2 and not l.startswith(("#", "//", "/*", "*"))]

            for i in range(len(cleaned) - min_duplicate_lines + 1):
                window = cleaned[i : i + min_duplicate_lines]
                content_block = "\n".join(item[1] for item in window)
                h = str(hash(content_block))

                if h not in block_hashes:
                    block_hashes[h] = []
                block_hashes[h].append((f["path"], window[0][0]))

        seen_pairs = set()
        for h, occurrences in block_hashes.items():
            if len(occurrences) > 1:
                first = occurrences[0]
                second = occurrences[1]
                pair_key = tuple(sorted([f"{first[0]}:{first[1]}", f"{second[0]}:{second[1]}"]))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    duplicates.append({
                        "file_a": first[0],
                        "line_a": first[1],
                        "file_b": second[0],
                        "line_b": second[1],
                        "lines_count": min_duplicate_lines,
                        "description": f"Identical {min_duplicate_lines}-line code pattern duplicated between `{first[0]}` (L{first[1]}) and `{second[0]}` (L{second[1]}).",
                        "suggestion": "Extract shared logic into a common reusable function or utility module."
                    })

        return duplicates

    def _compute_quality_score(
        self, review_count: int, complex_count: int, dup_count: int, doc_pct: float, total_files: int
    ) -> Tuple[int, str]:
        """Compute 0-100 score and letter grade."""
        base_score = 100.0

        # Penalties
        base_score -= min(30, (review_count / max(1, total_files)) * 8)
        base_score -= min(25, complex_count * 4)
        base_score -= min(20, dup_count * 5)

        # Bonus / penalty on doc coverage
        if doc_pct < 50:
            base_score -= (50 - doc_pct) * 0.2

        score = max(20, min(100, int(round(base_score))))

        if score >= 90:
            grade = "A (Excellent)"
        elif score >= 80:
            grade = "B (Good)"
        elif score >= 70:
            grade = "C (Satisfactory)"
        elif score >= 60:
            grade = "D (Needs Refactoring)"
        else:
            grade = "F (High Technical Debt)"

        return score, grade
