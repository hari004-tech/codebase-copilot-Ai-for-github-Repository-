import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

IGNORE_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules", "venv", ".venv",
    "env", ".env", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".idea", ".vscode", "dist", "build", "target", "bin", "obj",
    "coverage", ".tox", ".eggs", "site-packages", ".next", ".nuxt"
}

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".bmp",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".pdf", ".exe", ".dll", ".so", ".dylib", ".bin", ".dat",
    ".pyc", ".pyo", ".pyd", ".class", ".jar", ".war",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp3", ".mp4", ".mov", ".avi", ".wav",
    ".lock", ".sqlite", ".db"
}

LANGUAGE_MAP = {
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".json": "JSON",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".txt": "Text",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".sql": "SQL",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".hpp": "C++ Header",
    ".cc": "C++",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".dart": "Dart",
    ".r": "R",
    ".dockerfile": "Dockerfile",
}

COMMENT_PREFIXES = {
    "Python": ("#",),
    "Shell": ("#",),
    "YAML": ("#",),
    "Ruby": ("#",),
    "R": ("#",),
    "JavaScript": ("//", "/*", "*"),
    "TypeScript": ("//", "/*", "*"),
    "JavaScript (React)": ("//", "/*", "*"),
    "TypeScript (React)": ("//", "/*", "*"),
    "Java": ("//", "/*", "*"),
    "C": ("//", "/*", "*"),
    "C++": ("//", "/*", "*"),
    "C#": ("//", "/*", "*"),
    "Go": ("//", "/*", "*"),
    "Rust": ("//", "/*", "*"),
    "Swift": ("//", "/*", "*"),
    "Kotlin": ("//", "/*", "*"),
    "PHP": ("//", "/*", "*", "#"),
    "CSS": ("/*", "*"),
    "SCSS": ("//", "/*", "*"),
    "HTML": ("<!--",),
    "XML": ("<!--",),
    "SQL": ("--", "/*", "*"),
}

SPECIAL_FILENAMES = {
    "dockerfile": "Dockerfile",
    "makefile": "Makefile",
    "jenkinsfile": "Jenkinsfile",
    "vagrantfile": "Vagrantfile",
    "cmakelists.txt": "CMake",
}


class RepositoryAgent:
    """
    Agent 1: Repository Analysis Agent
    Recursively scans repository files, catalogs folders/files, identifies programming
    languages, computes line counts (total, blank, comments, code), and builds a tree.
    """

    def __init__(self, max_files: int = 500, max_file_size_kb: int = 1024):
        self.max_files = max_files
        self.max_file_size_bytes = max_file_size_kb * 1024

    def analyze(self, repo_path: str) -> Dict[str, Any]:
        """
        Analyze the directory structure and files in a repository.
        """
        repo_dir = Path(repo_path).resolve()
        if not repo_dir.exists() or not repo_dir.is_dir():
            raise ValueError(f"Directory not found: {repo_path}")

        files_info: List[Dict[str, Any]] = []
        folders_set = set()
        lang_stats: Dict[str, Dict[str, int]] = {}
        ext_counts: Dict[str, int] = {}
        config_markers: List[str] = []

        total_lines = 0
        total_blank = 0
        total_comments = 0
        total_code = 0

        # Scan files
        for root, dirs, files in os.walk(repo_dir):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d.lower() not in IGNORE_DIRS and not d.startswith(".")]

            rel_root = os.path.relpath(root, repo_dir)
            if rel_root != ".":
                folders_set.add(rel_root.replace("\\", "/"))

            for file_name in files:
                if len(files_info) >= self.max_files:
                    break

                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, repo_dir).replace("\\", "/")
                ext = os.path.splitext(file_name)[1].lower()
                base_name = file_name.lower()

                # Detect config markers
                if base_name in {
                    "requirements.txt", "package.json", "setup.py", "pyproject.toml",
                    "cargo.toml", "go.mod", "pom.xml", "dockerfile", "docker-compose.yml",
                    "gemfile", "composer.json", "tsconfig.json", "license", "readme.md"
                }:
                    config_markers.append(rel_path)

                # Skip binaries & ignored extensions
                if ext in IGNORE_EXTENSIONS:
                    continue

                # Check file size
                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    continue

                if size > self.max_file_size_bytes:
                    continue

                # Identify language
                language = "Other"
                if base_name in SPECIAL_FILENAMES:
                    language = SPECIAL_FILENAMES[base_name]
                elif ext in LANGUAGE_MAP:
                    language = LANGUAGE_MAP[ext]

                # Count lines and classify
                file_lines, blank_cnt, comment_cnt, code_cnt = self._count_lines(full_path, language)

                total_lines += file_lines
                total_blank += blank_cnt
                total_comments += comment_cnt
                total_code += code_cnt

                # Aggregations
                if language not in lang_stats:
                    lang_stats[language] = {"files": 0, "lines": 0, "code_lines": 0}
                lang_stats[language]["files"] += 1
                lang_stats[language]["lines"] += file_lines
                lang_stats[language]["code_lines"] += code_cnt

                ext_key = ext if ext else "no_ext"
                ext_counts[ext_key] = ext_counts.get(ext_key, 0) + 1

                files_info.append({
                    "path": rel_path,
                    "name": file_name,
                    "language": language,
                    "extension": ext,
                    "size_bytes": size,
                    "lines": file_lines,
                    "blank_lines": blank_cnt,
                    "comment_lines": comment_cnt,
                    "code_lines": code_cnt,
                })

            if len(files_info) >= self.max_files:
                break

        # Calculate percentages
        languages_list = []
        for lang, data in sorted(lang_stats.items(), key=lambda item: item[1]["lines"], reverse=True):
            pct = round((data["lines"] / total_lines * 100), 2) if total_lines > 0 else 0
            languages_list.append({
                "language": lang,
                "files": data["files"],
                "lines": data["lines"],
                "code_lines": data["code_lines"],
                "percentage": pct
            })

        # Top largest files
        largest_files = sorted(files_info, key=lambda f: f["lines"], reverse=True)[:10]

        # Build directory tree structure
        file_tree = self._build_tree(files_info)

        # Detect primary project type
        project_type = self._detect_project_type(languages_list, config_markers)

        return {
            "total_files": len(files_info),
            "total_folders": len(folders_set),
            "total_lines": total_lines,
            "total_blank_lines": total_blank,
            "total_comment_lines": total_comments,
            "total_code_lines": total_code,
            "languages": languages_list,
            "file_types": ext_counts,
            "files": files_info,
            "largest_files": largest_files,
            "config_markers": sorted(list(set(config_markers))),
            "project_type": project_type,
            "file_tree": file_tree,
        }

    def _count_lines(self, file_path: str, language: str):
        """Safely read lines and count comments/blank lines."""
        lines = 0
        blank = 0
        comments = 0
        code = 0

        prefixes = COMMENT_PREFIXES.get(language, ("#", "//"))

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    lines += 1
                    stripped = line.strip()
                    if not stripped:
                        blank += 1
                    elif any(stripped.startswith(p) for p in prefixes):
                        comments += 1
                    else:
                        code += 1
        except Exception:
            return 0, 0, 0, 0

        return lines, blank, comments, code

    def _build_tree(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert list of relative file paths into a nested tree dictionary."""
        tree: Dict[str, Any] = {"name": "root", "type": "folder", "children": {}}

        for item in files:
            parts = item["path"].split("/")
            curr = tree["children"]
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # File node
                    curr[part] = {
                        "name": part,
                        "type": "file",
                        "path": item["path"],
                        "language": item["language"],
                        "lines": item["lines"],
                        "size": item["size_bytes"]
                    }
                else:
                    # Folder node
                    if part not in curr:
                        curr[part] = {
                            "name": part,
                            "type": "folder",
                            "children": {}
                        }
                    curr = curr[part]["children"]

        def to_list(node: Dict[str, Any]) -> Dict[str, Any]:
            if node.get("type") == "folder":
                children_list = [to_list(child) for child in node["children"].values()]
                children_list.sort(key=lambda x: (0 if x["type"] == "folder" else 1, x["name"].lower()))
                return {
                    "name": node["name"],
                    "type": "folder",
                    "children": children_list
                }
            return node

        return to_list(tree)

    def _detect_project_type(self, languages: List[Dict[str, Any]], markers: List[str]) -> str:
        """Infer project type from detected markers and top languages."""
        marker_names = {os.path.basename(m).lower() for m in markers}

        if "package.json" in marker_names:
            if any(l["language"] in ("TypeScript", "TypeScript (React)") for l in languages):
                return "TypeScript / Node.js Application"
            return "JavaScript / Node.js Application"
        if "requirements.txt" in marker_names or "setup.py" in marker_names or "pyproject.toml" in marker_names:
            return "Python Application / Library"
        if "go.mod" in marker_names:
            return "Go Application"
        if "cargo.toml" in marker_names:
            return "Rust Crate"
        if "pom.xml" in marker_names:
            return "Java Maven Project"

        if languages:
            top_lang = languages[0]["language"]
            return f"{top_lang} Project"

        return "General Software Repository"
