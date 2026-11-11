import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

SHADOWED_BUILTINS = {"list", "dict", "set", "str", "int", "float", "id", "dir", "file", "type", "input", "filter", "map", "format"}

class BugDetectionAgent:
    """
    Agent 3: Bug Detection Agent
    Performs static AST and pattern-based vulnerability and bug analysis.
    Identifies syntax errors, logic anti-patterns, resource leaks, SQL injection,
    insecure functions, hardcoded secrets, and classified by severity: CRITICAL, HIGH, MEDIUM, LOW.
    """

    def __init__(self, max_files_to_scan: int = 150):
        self.max_files_to_scan = max_files_to_scan

    def analyze(self, repo_path: str, files_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Scan repository files for bugs, security vulnerabilities, and code safety flaws.
        """
        repo_dir = Path(repo_path).resolve()
        issues: List[Dict[str, Any]] = []

        scannable = [
            f for f in files_info
            if f.get("language") in {
                "Python", "JavaScript", "TypeScript", "JavaScript (React)",
                "TypeScript (React)", "SQL", "Shell", "HTML"
            }
        ][:self.max_files_to_scan]

        for file_info in scannable:
            rel_path = file_info["path"]
            full_path = repo_dir / rel_path
            lang = file_info["language"]

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue

            lines = content.splitlines()

            # Generic checks across all code files (Secrets, API keys, Passwords)
            self._check_hardcoded_secrets(content, lines, rel_path, issues)

            if lang == "Python":
                self._check_python_bugs(content, lines, rel_path, issues)
            elif lang in {"JavaScript", "TypeScript", "JavaScript (React)", "TypeScript (React)"}:
                self._check_js_ts_bugs(content, lines, rel_path, issues)

        # Categorize by severity
        severity_counts = {
            "CRITICAL": sum(1 for i in issues if i["severity"] == "CRITICAL"),
            "HIGH": sum(1 for i in issues if i["severity"] == "HIGH"),
            "MEDIUM": sum(1 for i in issues if i["severity"] == "MEDIUM"),
            "LOW": sum(1 for i in issues if i["severity"] == "LOW"),
        }

        # Calculate a Bug Density Score (bugs per 1000 lines of code)
        total_loc = sum(f.get("lines", 0) for f in scannable) or 1
        density = round((len(issues) / total_loc) * 1000, 2)

        return {
            "total_issues": len(issues),
            "severity_counts": severity_counts,
            "bug_density_per_kloc": density,
            "issues": sorted(issues, key=lambda x: self._severity_sort_key(x["severity"])),
        }

    def _severity_sort_key(self, severity: str) -> int:
        order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        return order.get(severity, 4)

    def _get_line_snippet(self, lines: List[str], line_no: int, context_lines: int = 1) -> str:
        """Extract line with 1-line context."""
        if not lines or line_no < 1:
            return ""
        idx = line_no - 1
        start = max(0, idx - context_lines)
        end = min(len(lines), idx + context_lines + 1)
        return "\n".join(lines[start:end])

    def _check_hardcoded_secrets(self, content: str, lines: List[str], rel_path: str, issues: List[Dict[str, Any]]):
        """Search for hardcoded passwords, tokens, and API credentials."""
        secret_patterns = [
            (r'(?i)(password|passwd|pwd|secret|auth_token)\s*=\s*[\'"]([A-Za-z0-9@#$%^&+=_-]{6,})[\'"]',
             "Hardcoded Secret / Password", "CRITICAL",
             "Hardcoded credentials can easily leak through version control.",
             "Load credentials securely from environment variables using `os.getenv()` or a secrets manager."),
            (r'(?i)(api[_-]?key|access[_-]?token|client[_-]?secret)\s*=\s*[\'"]([A-Za-z0-9_-]{16,})[\'"]',
             "Hardcoded API Key / Token", "CRITICAL",
             "Exposing sensitive API tokens in repository files poses a critical security breach risk.",
             "Replace with configuration files excluded from git or inject via environment variables."),
            (r'AKIA[0-9A-Z]{16}',
             "AWS Access Key ID Detected", "CRITICAL",
             "Discovered unencrypted AWS Access Key ID in source code.",
             "Revoke this key immediately and switch to AWS IAM Roles or environment credentials."),
            (r'ghp_[A-Za-z0-9]{36}',
             "GitHub Personal Access Token Detected", "CRITICAL",
             "Exposed active GitHub Personal Access Token in repository.",
             "Revoke the token in GitHub Settings and load via GitHub Actions secrets."),
        ]

        for pattern, title, severity, desc, rec in secret_patterns:
            for match in re.finditer(pattern, content):
                # Don't flag if it looks like an environment variable default or placeholder
                matched_val = match.group(0).lower()
                if any(placeholder in matched_val for placeholder in ("dummy", "test", "fake", "placeholder", "xxx", "your_")):
                    continue
                line_no = content[:match.start()].count("\n") + 1
                issues.append({
                    "id": f"SEC-{len(issues)+1}",
                    "file": rel_path,
                    "line": line_no,
                    "severity": severity,
                    "rule": "HARDCODED_CREDENTIAL",
                    "title": title,
                    "description": desc,
                    "code_snippet": lines[line_no - 1].strip() if line_no <= len(lines) else "",
                    "recommendation": rec
                })

    def _check_python_bugs(self, content: str, lines: List[str], rel_path: str, issues: List[Dict[str, Any]]):
        """Perform AST inspection and pattern detection on Python code."""
        try:
            tree = ast.parse(content, filename=rel_path)
        except SyntaxError as e:
            issues.append({
                "id": f"BUG-{len(issues)+1}",
                "file": rel_path,
                "line": e.lineno or 1,
                "severity": "HIGH",
                "rule": "SYNTAX_ERROR",
                "title": f"Python Syntax Error: {e.msg}",
                "description": f"Code fails to parse syntactically at line {e.lineno}, column {e.offset}.",
                "code_snippet": e.text.strip() if e.text else "",
                "recommendation": "Correct the syntax error to allow Python interpreter execution."
            })
            return

        # Walk AST
        for node in ast.walk(tree):
            # 1. Mutable Default Arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults + node.args.kw_defaults:
                    if default is not None and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        line_no = getattr(default, 'lineno', node.lineno)
                        issues.append({
                            "id": f"BUG-{len(issues)+1}",
                            "file": rel_path,
                            "line": line_no,
                            "severity": "HIGH",
                            "rule": "MUTABLE_DEFAULT_ARG",
                            "title": f"Mutable Default Argument in `{node.name}()`",
                            "description": "Default arguments are evaluated once at module load time. Mutating this object retains state across invocations, causing unexpected bugs.",
                            "code_snippet": self._get_line_snippet(lines, line_no),
                            "recommendation": "Use `default=None` and initialize the container inside the function body (`if arg is None: arg = []`)."
                        })

                # Check if function arguments shadow Python built-in names
                for arg in node.args.args:
                    if arg.arg in SHADOWED_BUILTINS:
                        issues.append({
                            "id": f"BUG-{len(issues)+1}",
                            "file": rel_path,
                            "line": arg.lineno,
                            "severity": "LOW",
                            "rule": "SHADOW_BUILTIN",
                            "title": f"Argument `{arg.arg}` Shadows Built-in",
                            "description": f"Parameter `{arg.arg}` overwrites Python's built-in `{arg.arg}()` function within local scope.",
                            "code_snippet": self._get_line_snippet(lines, arg.lineno),
                            "recommendation": f"Rename parameter to something descriptive like `{arg.arg}_items` or `{arg.arg}_val`."
                        })

            # 2. Bare except: and swallowed exceptions
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    line_no = node.lineno
                    issues.append({
                        "id": f"BUG-{len(issues)+1}",
                        "file": rel_path,
                        "line": line_no,
                        "severity": "MEDIUM",
                        "rule": "BARE_EXCEPT",
                        "title": "Bare `except:` Catches BaseException",
                        "description": "A bare `except:` intercepts SystemExit and KeyboardInterrupt, preventing normal program termination.",
                        "code_snippet": self._get_line_snippet(lines, line_no),
                        "recommendation": "Catch specific exception classes (e.g. `except (KeyError, ValueError):`) or `except Exception:`."
                    })
                # Swallowed exception with pass
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    line_no = node.lineno
                    issues.append({
                        "id": f"BUG-{len(issues)+1}",
                        "file": rel_path,
                        "line": line_no,
                        "severity": "MEDIUM",
                        "rule": "SWALLOWED_EXCEPTION",
                        "title": "Silent Exception Suppression (`pass`)",
                        "description": "Ignoring exceptions silently hides critical runtime bugs and diagnostic tracing.",
                        "code_snippet": self._get_line_snippet(lines, line_no),
                        "recommendation": "Log the error message (`logger.error()`) or handle the fallback state properly."
                    })

            # 3. Dangerous Comparison to None or Booleans
            elif isinstance(node, ast.Compare):
                for op, comp in zip(node.ops, node.comparators):
                    if isinstance(op, (ast.Eq, ast.NotEq)):
                        if isinstance(comp, ast.Constant) and comp.value is None:
                            line_no = node.lineno
                            issues.append({
                                "id": f"BUG-{len(issues)+1}",
                                "file": rel_path,
                                "line": line_no,
                                "severity": "LOW",
                                "rule": "NONE_COMPARISON",
                                "title": "Equality Comparison with `None` (`== None`)",
                                "description": "Comparison with singleton `None` should always use identity operator `is` or `is not`.",
                                "code_snippet": self._get_line_snippet(lines, line_no),
                                "recommendation": "Change `== None` to `is None` and `!= None` to `is not None`."
                            })
                        elif isinstance(comp, ast.Constant) and isinstance(comp.value, bool):
                            line_no = node.lineno
                            issues.append({
                                "id": f"BUG-{len(issues)+1}",
                                "file": rel_path,
                                "line": line_no,
                                "severity": "LOW",
                                "rule": "BOOL_COMPARISON",
                                "title": f"Explicit Comparison to Boolean Literal (`== {comp.value}`)",
                                "description": "Comparing directly to True or False is anti-idiomatic in Python.",
                                "code_snippet": self._get_line_snippet(lines, line_no),
                                "recommendation": f"Use `if condition:` or `if not condition:` instead of `== {comp.value}`."
                            })

            # 4. Division by zero check
            elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                if isinstance(node.right, ast.Constant) and node.right.value == 0:
                    line_no = node.lineno
                    issues.append({
                        "id": f"BUG-{len(issues)+1}",
                        "file": rel_path,
                        "line": line_no,
                        "severity": "HIGH",
                        "rule": "ZERO_DIVISION",
                        "title": "Guaranteed ZeroDivisionError",
                        "description": "Denominator is explicitly numeric zero, which will crash with ZeroDivisionError.",
                        "code_snippet": self._get_line_snippet(lines, line_no),
                        "recommendation": "Guard the divisor with a non-zero validation condition."
                    })

            # 5. Insecure Functions: eval(), exec(), os.system()
            elif isinstance(node, ast.Call):
                fn_name = ""
                if isinstance(node.func, ast.Name):
                    fn_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    fn_name = node.func.attr

                if fn_name in ("eval", "exec"):
                    line_no = node.lineno
                    issues.append({
                        "id": f"BUG-{len(issues)+1}",
                        "file": rel_path,
                        "line": line_no,
                        "severity": "CRITICAL",
                        "rule": "DANGEROUS_EVAL",
                        "title": f"Insecure Code Execution via `{fn_name}()`",
                        "description": f"Using `{fn_name}()` executes dynamic arbitrary code and creates severe remote code execution (RCE) vectors.",
                        "code_snippet": self._get_line_snippet(lines, line_no),
                        "recommendation": "Refactor to use `ast.literal_eval()` or structured parsers (e.g. `json.loads`)."
                    })
                elif fn_name == "system" and hasattr(node.func, "value") and getattr(node.func.value, "id", "") == "os":
                    line_no = node.lineno
                    issues.append({
                        "id": f"BUG-{len(issues)+1}",
                        "file": rel_path,
                        "line": line_no,
                        "severity": "HIGH",
                        "rule": "COMMAND_INJECTION",
                        "title": "Potential Command Injection via `os.system()`",
                        "description": "`os.system()` runs commands in a subshell without input sanitization.",
                        "code_snippet": self._get_line_snippet(lines, line_no),
                        "recommendation": "Use `subprocess.run([...], shell=False)` with argument lists instead."
                    })

                # Check SQL formatting inside execute()
                if fn_name in ("execute", "executemany") and node.args:
                    first_arg = node.args[0]
                    # Check if first arg is an f-string or % formatted string
                    is_formatted = isinstance(first_arg, ast.JoinedStr) or (
                        isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Mod)
                    )
                    if is_formatted:
                        line_no = node.lineno
                        issues.append({
                            "id": f"BUG-{len(issues)+1}",
                            "file": rel_path,
                            "line": line_no,
                            "severity": "CRITICAL",
                            "rule": "SQL_INJECTION",
                            "title": "SQL Injection Vector in `execute()`",
                            "description": "SQL query uses string formatting / f-strings instead of parameterized queries, leaving database open to SQL injection.",
                            "code_snippet": self._get_line_snippet(lines, line_no),
                            "recommendation": "Pass query parameters as tuple/dict arguments: `cursor.execute('SELECT * FROM tbl WHERE id = ?', (id,))`."
                        })

    def _check_js_ts_bugs(self, content: str, lines: List[str], rel_path: str, issues: List[Dict[str, Any]]):
        """Pattern-based bug checks for JavaScript and TypeScript."""
        for idx, line in enumerate(lines):
            line_no = idx + 1
            stripped = line.strip()

            # 1. Dangerous innerHTML assignment
            if ".innerHTML" in stripped and "=" in stripped and not stripped.startswith("//"):
                issues.append({
                    "id": f"BUG-{len(issues)+1}",
                    "file": rel_path,
                    "line": line_no,
                    "severity": "HIGH",
                    "rule": "XSS_INNER_HTML",
                    "title": "Cross-Site Scripting (XSS) via `innerHTML`",
                    "description": "Directly assigning unsanitized dynamic markup to `innerHTML` can execute arbitrary injected scripts.",
                    "code_snippet": stripped,
                    "recommendation": "Use `.textContent` or `DOMPurify.sanitize()` before injecting dynamic strings."
                })

            # 2. Loose equality check ==
            if re.search(r'\b[a-zA-Z0-9_$]+\s*==\s*[a-zA-Z0-9_$]+', stripped) and "===" not in stripped and not stripped.startswith("//"):
                issues.append({
                    "id": f"BUG-{len(issues)+1}",
                    "file": rel_path,
                    "line": line_no,
                    "severity": "LOW",
                    "rule": "LOOSE_EQUALITY",
                    "title": "Loose Equality Operator (`==`)",
                    "description": "The `==` operator performs implicit type coercion which frequently causes subtle logic bugs (e.g. `0 == ''` is true).",
                    "code_snippet": stripped,
                    "recommendation": "Use strict equality `===` and strict inequality `!==`."
                })

            # 3. Debugger statements
            if re.match(r'^\s*debugger\s*;?', stripped):
                issues.append({
                    "id": f"BUG-{len(issues)+1}",
                    "file": rel_path,
                    "line": line_no,
                    "severity": "MEDIUM",
                    "rule": "DEBUGGER_STMT",
                    "title": "Dangling `debugger` Statement",
                    "description": "Debugger breakpoint left in source will halt script execution in browsers when devtools are open.",
                    "code_snippet": stripped,
                    "recommendation": "Remove debugging statements prior to staging or production deployment."
                })
