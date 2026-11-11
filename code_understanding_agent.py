import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class CodeUnderstandingAgent:
    """
    Agent 2: Code Understanding Agent
    Parses code using AST for Python and regex/heuristics for other languages.
    Extracts classes, functions, arguments, docstrings, imports, generates function explanations,
    and produces high-level file summaries and architectural role analysis.
    """

    def __init__(self, max_files_to_deep_scan: int = 100):
        self.max_files_to_deep_scan = max_files_to_deep_scan

    def analyze(self, repo_path: str, files_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform deep code understanding on repository source files.
        """
        repo_dir = Path(repo_path).resolve()
        understood_files: List[Dict[str, Any]] = []
        all_classes: List[Dict[str, Any]] = []
        all_functions: List[Dict[str, Any]] = []
        module_dependencies: Dict[str, List[str]] = {}

        # Prioritize key code files (Python, JS/TS, Go, Java, etc.)
        code_files = [
            f for f in files_info
            if f.get("language") in {
                "Python", "JavaScript", "TypeScript", "JavaScript (React)",
                "TypeScript (React)", "Go", "Java", "C++", "C", "Rust"
            }
        ][:self.max_files_to_deep_scan]

        for file_info in code_files:
            rel_path = file_info["path"]
            full_path = repo_dir / rel_path
            lang = file_info["language"]

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue

            file_understanding = {
                "path": rel_path,
                "name": file_info["name"],
                "language": lang,
                "lines": file_info["lines"],
                "classes": [],
                "functions": [],
                "imports": [],
                "summary": "",
                "purpose": "General Source File"
            }

            if lang == "Python":
                self._parse_python_file(content, rel_path, file_understanding)
            elif lang in {"JavaScript", "TypeScript", "JavaScript (React)", "TypeScript (React)"}:
                self._parse_js_ts_file(content, rel_path, file_understanding)
            else:
                self._parse_generic_code_file(content, rel_path, file_understanding)

            # Generate plain-English summary for file
            file_understanding["summary"] = self._generate_file_summary(file_understanding)

            understood_files.append(file_understanding)
            all_classes.extend(file_understanding["classes"])
            all_functions.extend(file_understanding["functions"])
            module_dependencies[rel_path] = file_understanding["imports"]

        # High-level architecture map
        arch_overview = self._synthesize_architecture(understood_files)

        return {
            "scanned_files_count": len(understood_files),
            "total_classes_found": len(all_classes),
            "total_functions_found": len(all_functions),
            "files": understood_files,
            "classes": all_classes[:100],  # top classes
            "functions": all_functions[:150],  # top functions
            "dependencies": module_dependencies,
            "architecture_overview": arch_overview,
        }

    def _parse_python_file(self, content: str, rel_path: str, result: Dict[str, Any]):
        """Parse Python source using Python's built-in AST parser."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            result["summary"] = "File has Python syntax errors preventing complete AST parsing."
            return

        # Top-level docstring
        module_doc = ast.get_docstring(tree) or ""
        if module_doc:
            result["module_docstring"] = module_doc.strip()

        imports = []
        classes = []
        functions = []

        for node in tree.body:
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append(f"{mod}.{alias.name}" if mod else alias.name)

            # Classes
            elif isinstance(node, ast.ClassDef):
                cls_info = self._extract_python_class(node, rel_path)
                classes.append(cls_info)

            # Standalone Functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_info = self._extract_python_function(node, rel_path, is_method=False)
                functions.append(fn_info)

        result["imports"] = imports
        result["classes"] = classes
        result["functions"] = functions

    def _extract_python_class(self, node: ast.ClassDef, rel_path: str) -> Dict[str, Any]:
        """Extract metadata and explanation for Python class."""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{getattr(base.value, 'id', '')}.{base.attr}")

        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._extract_python_function(item, rel_path, is_method=True, class_name=node.name))

        doc = ast.get_docstring(node) or ""
        explanation = self._explain_class(node.name, bases, methods, doc)

        return {
            "name": node.name,
            "file": rel_path,
            "line": node.lineno,
            "bases": bases,
            "docstring": doc.strip() if doc else "",
            "methods_count": len(methods),
            "methods": methods,
            "explanation": explanation
        }

    def _extract_python_function(
        self,
        node: ast.FunctionDef,
        rel_path: str,
        is_method: bool = False,
        class_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract metadata and heuristic explanation for Python function/method."""
        args_list = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else '...'}"
            args_list.append(arg_str)

        decorators = []
        for dec in node.decorator_list:
            if hasattr(ast, 'unparse'):
                decorators.append(ast.unparse(dec))
            elif isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(f"{getattr(dec.value, 'id', '')}.{dec.attr}")

        doc = ast.get_docstring(node) or ""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        explanation = self._explain_function(node.name, args_list, is_async, is_method, class_name, doc, node)

        return {
            "name": node.name,
            "class_name": class_name,
            "file": rel_path,
            "line": node.lineno,
            "is_method": is_method,
            "is_async": is_async,
            "args": args_list,
            "decorators": decorators,
            "docstring": doc.strip() if doc else "",
            "explanation": explanation
        }

    def _explain_function(
        self,
        name: str,
        args: List[str],
        is_async: bool,
        is_method: bool,
        class_name: Optional[str],
        doc: str,
        node: ast.AST
    ) -> str:
        """Provide a clear, human-like explanation of what a function does."""
        if doc:
            first_line = doc.strip().split("\n")[0]
            if len(first_line) > 10:
                return first_line

        # Heuristic based on name prefix and keywords
        lower = name.lower()
        parts = lower.replace("__", "").split("_")
        verb = parts[0] if parts else ""

        prefix = "Async method" if (is_async and is_method) else "Method" if is_method else "Async function" if is_async else "Function"
        context = f" on `{class_name}`" if class_name else ""

        # Analyze internal calls/returns
        returns_val = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(node))
        has_loop = any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(node))
        has_try = any(isinstance(n, ast.Try) for n in ast.walk(node))

        detail = []
        if returns_val:
            detail.append("computes and returns a result")
        if has_loop:
            detail.append("iterates over data elements")
        if has_try:
            detail.append("handles runtime exceptions safely")

        detail_str = f" ({', '.join(detail)})" if detail else ""

        if verb in ("get", "fetch", "load", "read"):
            target = " ".join(parts[1:]) if len(parts) > 1 else "data"
            return f"{prefix}{context} that retrieves or queries {target}{detail_str}."
        elif verb in ("set", "save", "write", "store", "update"):
            target = " ".join(parts[1:]) if len(parts) > 1 else "state"
            return f"{prefix}{context} that updates or persists {target}."
        elif verb in ("create", "add", "insert", "build", "init"):
            target = " ".join(parts[1:]) if len(parts) > 1 else "new instances"
            return f"{prefix}{context} that initializes or constructs {target}."
        elif verb in ("delete", "remove", "drop", "clear"):
            target = " ".join(parts[1:]) if len(parts) > 1 else "records"
            return f"{prefix}{context} that removes or purges {target}."
        elif verb in ("is", "has", "check", "validate", "verify"):
            target = " ".join(parts[1:]) if len(parts) > 1 else "condition"
            return f"{prefix}{context} that validates {target} and checks boolean status."
        elif verb in ("handle", "on", "process"):
            target = " ".join(parts[1:]) if len(parts) > 1 else "event"
            return f"{prefix}{context} that processes incoming {target} requests or callbacks."
        elif verb in ("parse", "convert", "transform", "format"):
            target = " ".join(parts[1:]) if len(parts) > 1 else "data structure"
            return f"{prefix}{context} that transforms or parses {target}."
        elif name.startswith("__init__"):
            return f"Constructor{context} initializing instance attributes and configuration."

        target = " ".join(parts)
        return f"{prefix}{context} responsible for {target} operations{detail_str}."

    def _explain_class(self, name: str, bases: List[str], methods: List[Dict[str, Any]], doc: str) -> str:
        """Provide a clear explanation of what a class represents."""
        if doc:
            first_line = doc.strip().split("\n")[0]
            if len(first_line) > 10:
                return first_line

        base_str = f" inheriting from `{', '.join(bases)}`" if bases else ""
        lower = name.lower()

        if "model" in lower or any("model" in b.lower() for b in bases):
            return f"Data model class{base_str} representing core database entities with {len(methods)} methods."
        if "view" in lower or "controller" in lower or "handler" in lower or "route" in lower:
            return f"Controller / Handler class{base_str} managing user requests and view endpoints."
        if "service" in lower:
            return f"Business logic service layer{base_str} orchestrating domain operations."
        if "util" in lower or "helper" in lower:
            return f"Utility class{base_str} providing reusable helper routines."
        if "client" in lower or "api" in lower:
            return f"Client interface class{base_str} for external service or API integration."

        return f"Component class `{name}`{base_str} encapsulating state and {len(methods)} operational methods."

    def _parse_js_ts_file(self, content: str, rel_path: str, result: Dict[str, Any]):
        """Parse JavaScript and TypeScript files using regex patterns."""
        imports = []
        classes = []
        functions = []

        # Find imports: import ... from '...' or const x = require('...')
        import_patterns = [
            r'import\s+(?:[\w*\s{},]+)\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'(?:const|let|var)\s+(?:[\w\s{},]+)\s*=\s*require\([\'"]([^\'"]+)[\'"]\)'
        ]
        for pat in import_patterns:
            for match in re.finditer(pat, content):
                imports.append(match.group(1))

        # Find classes: class Name extends Base
        class_matches = re.finditer(r'class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$.]+))?\s*\{', content)
        for m in class_matches:
            line_no = content[:m.start()].count("\n") + 1
            cls_name = m.group(1)
            base = [m.group(2)] if m.group(2) else []
            classes.append({
                "name": cls_name,
                "file": rel_path,
                "line": line_no,
                "bases": base,
                "methods_count": 0,
                "explanation": f"JavaScript/TypeScript class `{cls_name}`{f' extending {base[0]}' if base else ''}."
            })

        # Find functions: function name(...) or const name = (...) => or async function
        fn_matches = re.finditer(
            r'(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)|(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>',
            content
        )
        for m in fn_matches:
            line_no = content[:m.start()].count("\n") + 1
            if m.group(1):
                fn_name = m.group(1)
                args = [a.strip() for a in m.group(2).split(",") if a.strip()]
            else:
                fn_name = m.group(3)
                args = [a.strip() for a in m.group(4).split(",") if a.strip()]

            functions.append({
                "name": fn_name,
                "file": rel_path,
                "line": line_no,
                "is_method": False,
                "args": args,
                "explanation": f"JavaScript/TypeScript routine `{fn_name}({', '.join(args)})` handling application logic."
            })

        result["imports"] = imports
        result["classes"] = classes
        result["functions"] = functions

    def _parse_generic_code_file(self, content: str, rel_path: str, result: Dict[str, Any]):
        """Fallback lightweight parser for other languages (Go, Java, C++, Rust)."""
        functions = []
        classes = []

        # Generic function detection heuristic
        fn_matches = re.finditer(r'(?:public|private|protected|static|func|def|fn)\s+(?:[A-Za-z0-9_<>[\]]+\s+)?([A-Za-z0-9_]+)\s*\(([^)]*)\)', content)
        for m in fn_matches:
            line_no = content[:m.start()].count("\n") + 1
            fn_name = m.group(1)
            if fn_name not in {"if", "for", "while", "switch", "catch"}:
                args = [a.strip() for a in m.group(2).split(",") if a.strip()]
                functions.append({
                    "name": fn_name,
                    "file": rel_path,
                    "line": line_no,
                    "args": args,
                    "explanation": f"Source routine `{fn_name}` defined at line {line_no}."
                })

        result["functions"] = functions
        result["classes"] = classes

    def _generate_file_summary(self, file_data: Dict[str, Any]) -> str:
        """Create a concise, intelligible summary of the file's primary purpose."""
        name = file_data["name"].lower()
        lang = file_data["language"]
        classes = file_data["classes"]
        functions = file_data["functions"]
        imports = file_data["imports"]

        # Check special filenames
        if name in ("app.py", "main.py", "server.js", "index.js", "main.go", "application.java"):
            return f"Primary application entrypoint ({lang}) setting up server, routing, and configurations with {len(functions)} routines."
        if name in ("auth.py", "auth.js", "authentication.py", "jwt.py"):
            return f"Security and authentication module managing user credentials, login sessions, and access control tokens."
        if name in ("models.py", "schema.py", "database.py", "db.py"):
            return f"Database persistence and ORM schema module defining {len(classes)} entity models."
        if "test" in name or name.startswith("test_"):
            return f"Automated test suite containing test fixtures and assertions."
        if "util" in name or "helper" in name or "common" in name:
            return f"Utility library encapsulating {len(functions)} reusable helper functions and formatting routines."
        if name in ("views.py", "routes.py", "api.py", "endpoints.py"):
            return f"API routing layer dispatching HTTP endpoints and controlling request/response lifecycles."

        parts = []
        if classes:
            cls_names = ", ".join([f"`{c['name']}`" for c in classes[:3]])
            parts.append(f"defines classes {cls_names}")
        if functions:
            parts.append(f"provides {len(functions)} callable functions")
        if imports:
            parts.append(f"integrates with {len(imports)} modules")

        if parts:
            return f"{lang} module that " + "; ".join(parts) + "."
        return f"{lang} source file containing {file_data['lines']} lines of code."

    def _synthesize_architecture(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize overall architectural roles."""
        entrypoints = []
        controllers = []
        models = []
        utilities = []
        tests = []

        for f in files:
            path_lower = f["path"].lower()
            if any(path_lower.endswith(e) for e in ("app.py", "main.py", "server.js", "index.js", "main.go")):
                entrypoints.append(f["path"])
            elif any(k in path_lower for k in ("controller", "route", "view", "api", "endpoint")):
                controllers.append(f["path"])
            elif any(k in path_lower for k in ("model", "schema", "entity", "db", "database")):
                models.append(f["path"])
            elif any(k in path_lower for k in ("util", "helper", "common", "tool")):
                utilities.append(f["path"])
            elif any(k in path_lower for k in ("test", "spec")):
                tests.append(f["path"])

        pattern = "Modular Application"
        if controllers and models:
            pattern = "Model-View-Controller (MVC) / Layered Architecture"
        elif entrypoints and utilities:
            pattern = "Script / Micro-Service Architecture"

        return {
            "pattern": pattern,
            "entrypoints": entrypoints,
            "controllers": controllers,
            "models": models,
            "utilities": utilities,
            "tests": tests,
            "summary": f"Identified {len(entrypoints)} entrypoints, {len(controllers)} route/controller files, and {len(models)} data models operating in a {pattern} structure."
        }
