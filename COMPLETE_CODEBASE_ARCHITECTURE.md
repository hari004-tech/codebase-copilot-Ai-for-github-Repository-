# CODEBASE COPILOT – COMPLETE ARCHITECTURE & SOURCE CODE BUNDLE

> **All-In-One Master Document**
> This single file contains the complete system architecture, flow diagrams, and full source code of all modules for the **Codebase Copilot** platform.

---

## 🏗️ 1. SYSTEM ARCHITECTURE & DESIGN

Codebase Copilot is structured as a multi-agent static intelligence engine. It analyzes public GitHub repositories and local source projects with zero paid AI APIs.

### Architecture Flow Diagram (Mermaid)
`mermaid
flowchart TD
    Client([Web Browser / Client])
    
    subgraph Frontend [Modern Dark-Mode Frontend]
        UI[Home & Dashboard UI]
        Charts[Chart.js Visualizations]
        Tree[Interactive File Explorer]
        Modal[Code Inspector Modal]
    end
    
    subgraph Backend [Python Flask Backend (app.py)]
        Validator[URL Validator & Sanitizer]
        Downloader[Safe Zip Streamer & Extractor]
        Orchestrator[Multi-Agent Orchestrator]
        Cache[(In-Memory Result Cache)]
    end
    
    subgraph Agents [6 Static Intelligence Agents]
        A1[Agent 1: Repository Scanner]
        A2[Agent 2: Code Understanding & AST]
        A3[Agent 3: Bug & Security Detector]
        A4[Agent 4: Code Reviewer & Complexity]
        A5[Agent 5: Documentation Generator]
        A6[Agent 6: Optimization Planner]
    end

    Client --> UI
    UI -->|POST /api/analyze| Validator
    Validator --> Downloader
    Downloader --> Orchestrator
    Orchestrator --> A1
    Orchestrator --> A2
    Orchestrator --> A3
    Orchestrator --> A4
    Orchestrator --> A5
    Orchestrator --> A6
    A1 & A2 & A3 & A4 & A5 & A6 --> Cache
    Cache -->|JSON Response| UI
    UI --> Charts & Tree & Modal
`

---

## 📂 2. DIRECTORY TREE STRUCTURE

`
codebase-copilot/
├── app.py                         # Flask server & API routes
├── test_app.py                    # Unit and integration test suite
├── requirements.txt               # Backend dependencies
├── README.md                      # Project manual
├── run.bat                        # Windows batch launcher
├── run.ps1                        # PowerShell launcher
├── agents/                        # 6 Dedicated Agent Modules
│   ├── __init__.py
│   ├── repository_agent.py        # Agent 1: Repo scanner & metrics
│   ├── code_understanding_agent.py# Agent 2: AST parser & heuristics
│   ├── bug_detection_agent.py     # Agent 3: Bug & security detector
│   ├── code_review_agent.py       # Agent 4: Complexity, duplicates, smells
│   ├── documentation_agent.py     # Agent 5: README & Mermaid doc generator
│   └── improvement_agent.py       # Agent 6: Optimization & diff generator
├── templates/                     # HTML Views
│   ├── index.html                 # Landing page
│   └── dashboard.html             # Analysis dashboard
├── static/                        # Static Assets
│   ├── css/style.css              # Custom styling
│   └── js/script.js               # Dynamic charts & interactions
└── sample_repo/                   # Demo Project
    ├── app.py
    ├── auth.py
    ├── models.py
    ├── utils.py
    ├── requirements.txt
    ├── services/payment_service.py
    └── static/main.js
`

---

## 💻 3. VERBATIM SOURCE CODE FOR ALL FILES

### File: requirements.txt\n\n`text\nFlask>=3.0.0
requests>=2.31.0
\n`\n\n---\n\n### File: run.bat\n\n`batch\n@echo off
title Codebase Copilot - AI for GitHub Repositories
echo =======================================================
echo    CODEBASE COPILOT - AI FOR GITHUB REPOSITORIES
echo =======================================================
echo.
echo Installing dependencies...
python -m pip install -r requirements.txt
echo.
echo Starting application server...
start http://localhost:5000
python app.py
pause
\n`\n\n---\n\n### File: run.ps1\n\n`powershell\nWrite-Host "=======================================================" -ForegroundColor Cyan
Write-Host "   CODEBASE COPILOT - AI FOR GITHUB REPOSITORIES" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt
Write-Host ""
Write-Host "Starting Codebase Copilot on http://localhost:5000 ..." -ForegroundColor Green
Start-Process "http://localhost:5000"
python app.py
\n`\n\n---\n\n### File: app.py\n\n`python\nimport os
import re
import sys
import uuid
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

import requests
from flask import Flask, render_template, request, jsonify, send_file, Response

from agents.repository_agent import RepositoryAgent
from agents.code_understanding_agent import CodeUnderstandingAgent
from agents.bug_detection_agent import BugDetectionAgent
from agents.code_review_agent import CodeReviewAgent
from agents.documentation_agent import DocumentationAgent
from agents.improvement_agent import ImprovementAgent

app = Flask(__name__)

# In-memory storage for analysis results and file directories
ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}
ANALYSIS_DIRS: Dict[str, str] = {}
RECENT_ANALYSES: list = []

MAX_ZIP_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max download limit
MAX_FILES_EXTRACTED = 500

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_REPO_DIR = BASE_DIR / "sample_repo"

def parse_github_url(url: str) -> Optional[Dict[str, str]]:
    """
    Validate and extract owner and repo from a GitHub URL or shorthand.
    Supports:
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - github.com/owner/repo
      - owner/repo
    """
    clean = url.strip()
    if clean.endswith(".git"):
        clean = clean[:-4]

    # Pattern for https://github.com/owner/repo or github.com/owner/repo
    pattern = r'^(?:https?:\/\/)?(?:www\.)?github\.com\/([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)(?:\/.*)?$'
    match = re.match(pattern, clean)
    if match:
        return {"owner": match.group(1), "repo": match.group(2)}

    # Shorthand: owner/repo
    shorthand_pattern = r'^([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)$'
    match_short = re.match(shorthand_pattern, clean)
    if match_short:
        return {"owner": match_short.group(1), "repo": match_short.group(2)}

    return None

def download_github_repo(owner: str, repo: str) -> str:
    """
    Safely download and extract public GitHub repository zip archive.
    Enforces size limits and prevents Zip Slip directory traversal.
    """
    headers = {
        "User-Agent": "Codebase-Copilot-Static-Analyzer/1.0",
        "Accept": "application/vnd.github.v3+json"
    }

    # Try default branches: main, then master
    branches_to_try = ["main", "master"]
    zip_resp = None
    last_status = None

    for branch in branches_to_try:
        url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        try:
            resp = requests.get(url, headers=headers, stream=True, timeout=15)
            last_status = resp.status_code
            if resp.status_code == 200:
                zip_resp = resp
                break
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error connecting to GitHub: {str(e)}")

    # Fallback to GitHub API zipball if direct branches failed
    if not zip_resp:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
        try:
            resp = requests.get(api_url, headers=headers, stream=True, timeout=15)
            last_status = resp.status_code
            if resp.status_code == 200:
                zip_resp = resp
        except requests.exceptions.RequestException:
            pass

    if not zip_resp:
        if last_status == 404:
            raise ValueError(f"Repository `{owner}/{repo}` not found or is private. Please verify the URL.")
        elif last_status == 403:
            raise ValueError(f"GitHub access limit reached (HTTP 403). Try analyzing our built-in sample repository.")
        else:
            raise ValueError(f"Could not download repository `{owner}/{repo}` (HTTP {last_status}).")

    # Download with size limit check
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    downloaded_size = 0
    try:
        for chunk in zip_resp.iter_content(chunk_size=65536):
            if chunk:
                downloaded_size += len(chunk)
                if downloaded_size > MAX_ZIP_SIZE_BYTES:
                    raise ValueError(f"Repository exceeds safe download limit of {MAX_ZIP_SIZE_BYTES // (1024*1024)}MB.")
                temp_zip.write(chunk)
        temp_zip.close()

        # Safe extraction directory
        extract_dir = tempfile.mkdtemp(prefix=f"copilot_{owner}_{repo}_")

        with zipfile.ZipFile(temp_zip.name, 'r') as z:
            # Check for zip bomb / member count
            members = z.namelist()
            if len(members) > 3000:
                # Limit extract count
                members = members[:3000]

            for member in members:
                # Prevent Zip Slip directory traversal
                member_path = Path(os.path.abspath(os.path.join(extract_dir, member)))
                if not str(member_path).startswith(os.path.abspath(extract_dir)):
                    continue  # Skip unsafe path traversal
                z.extract(member, extract_dir)

        # Locate root directory inside extracted zip (GitHub zips have a single root folder)
        entries = [os.path.join(extract_dir, d) for d in os.listdir(extract_dir)]
        if len(entries) == 1 and os.path.isdir(entries[0]):
            target_repo_dir = entries[0]
        else:
            target_repo_dir = extract_dir

        return target_repo_dir

    finally:
        if os.path.exists(temp_zip.name):
            try:
                os.remove(temp_zip.name)
            except OSError:
                pass

def run_all_agents(repo_name: str, repo_path: str) -> Dict[str, Any]:
    """Execute all 6 agents sequentially and gather insights."""
    # 1. Repository Analysis Agent
    repo_agent = RepositoryAgent(max_files=MAX_FILES_EXTRACTED)
    repo_data = repo_agent.analyze(repo_path)

    # 2. Code Understanding Agent
    understanding_agent = CodeUnderstandingAgent()
    understanding_data = understanding_agent.analyze(repo_path, repo_data["files"])

    # 3. Bug Detection Agent
    bug_agent = BugDetectionAgent()
    bug_data = bug_agent.analyze(repo_path, repo_data["files"])

    # 4. Code Review Agent
    review_agent = CodeReviewAgent()
    review_data = review_agent.analyze(repo_path, repo_data["files"])

    # 5. Documentation Generation Agent
    doc_agent = DocumentationAgent()
    doc_data = doc_agent.generate(
        repo_name=repo_name,
        repo_data=repo_data,
        understanding_data=understanding_data,
        bug_data=bug_data,
        review_data=review_data
    )

    # 6. Code Improvement Agent
    improvement_agent = ImprovementAgent()
    improvement_data = improvement_agent.analyze(repo_path, repo_data["files"])

    return {
        "repo_name": repo_name,
        "repository_analysis": repo_data,
        "code_understanding": understanding_data,
        "bug_detection": bug_data,
        "code_review": review_data,
        "documentation": doc_data,
        "code_improvement": improvement_data
    }

# ----------------- FLASK ROUTES -----------------

@app.route("/")
def home():
    """Render home landing page."""
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    """Render dashboard page."""
    return render_template("dashboard.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Analyze a public GitHub repository."""
    data = request.get_json() or {}
    url = data.get("repo_url", "").strip()

    if not url:
        return jsonify({"error": "Please provide a valid GitHub repository URL."}), 400

    parsed = parse_github_url(url)
    if not parsed:
        return jsonify({
            "error": "Invalid GitHub repository URL format. Example: https://github.com/pallets/flask or owner/repo"
        }), 400

    owner = parsed["owner"]
    repo = parsed["repo"]
    repo_name = f"{owner}/{repo}"

    try:
        extracted_path = download_github_repo(owner, repo)
    except (ValueError, RuntimeError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred while fetching repo: {str(e)}"}), 500

    try:
        analysis_id = str(uuid.uuid4())[:8]
        results = run_all_agents(repo_name, extracted_path)

        # Store in cache
        ANALYSIS_CACHE[analysis_id] = results
        ANALYSIS_DIRS[analysis_id] = extracted_path

        RECENT_ANALYSES.insert(0, {
            "id": analysis_id,
            "repo_name": repo_name,
            "files": results["repository_analysis"]["total_files"],
            "loc": results["repository_analysis"]["total_lines"],
            "grade": results["code_review"]["maintainability_grade"]
        })

        return jsonify({
            "status": "success",
            "analysis_id": analysis_id,
            "data": results
        })
    except Exception as e:
        return jsonify({"error": f"Analysis execution failed: {str(e)}"}), 500

@app.route("/api/analyze-sample", methods=["POST"])
def analyze_sample():
    """Analyze the built-in demo sample repository instantly without network requests."""
    try:
        sample_path = str(SAMPLE_REPO_DIR)
        repo_name = "demo-user/ecommerce-microservice"
        analysis_id = "sample-repo"

        results = run_all_agents(repo_name, sample_path)
        ANALYSIS_CACHE[analysis_id] = results
        ANALYSIS_DIRS[analysis_id] = sample_path

        return jsonify({
            "status": "success",
            "analysis_id": analysis_id,
            "data": results
        })
    except Exception as e:
        return jsonify({"error": f"Sample repository analysis failed: {str(e)}"}), 500

@app.route("/api/results/<analysis_id>", methods=["GET"])
def get_results(analysis_id: str):
    """Retrieve cached analysis results."""
    if analysis_id in ANALYSIS_CACHE:
        return jsonify({"status": "success", "data": ANALYSIS_CACHE[analysis_id]})
    return jsonify({"error": f"No analysis found for ID: {analysis_id}"}), 404

@app.route("/api/file-content", methods=["GET"])
def get_file_content():
    """Retrieve raw file content for code inspection."""
    analysis_id = request.args.get("analysis_id")
    file_rel_path = request.args.get("path")

    if not analysis_id or not file_rel_path:
        return jsonify({"error": "Missing analysis_id or file path parameter"}), 400

    repo_dir = ANALYSIS_DIRS.get(analysis_id)
    if not repo_dir or not os.path.isdir(repo_dir):
        return jsonify({"error": "Repository files not found or expired"}), 404

    target_path = Path(os.path.abspath(os.path.join(repo_dir, file_rel_path)))
    # Prevent traversal
    if not str(target_path).startswith(os.path.abspath(repo_dir)):
        return jsonify({"error": "Unauthorized file access attempt"}), 403

    if not target_path.exists() or not target_path.is_file():
        return jsonify({"error": "File does not exist"}), 404

    try:
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return jsonify({
            "path": file_rel_path,
            "name": target_path.name,
            "content": content
        })
    except Exception as e:
        return jsonify({"error": f"Failed reading file: {str(e)}"}), 500

@app.route("/api/export-docs/<analysis_id>", methods=["GET"])
def export_docs(analysis_id: str):
    """Download generated README.md."""
    if analysis_id not in ANALYSIS_CACHE:
        return jsonify({"error": "Analysis not found"}), 404

    doc_data = ANALYSIS_CACHE[analysis_id].get("documentation", {})
    markdown_content = doc_data.get("readme_markdown", "# Project Documentation")
    repo_name = ANALYSIS_CACHE[analysis_id].get("repo_name", "repo").replace("/", "_")

    return Response(
        markdown_content,
        mimetype="text/markdown",
        headers={"Content-disposition": f"attachment; filename=README_{repo_name}.md"}
    )

@app.route("/api/export-json/<analysis_id>", methods=["GET"])
def export_json(analysis_id: str):
    """Download full JSON report."""
    if analysis_id not in ANALYSIS_CACHE:
        return jsonify({"error": "Analysis not found"}), 404

    return jsonify(ANALYSIS_CACHE[analysis_id])

@app.route("/api/history", methods=["GET"])
def get_history():
    """Get list of recent analyses."""
    return jsonify(RECENT_ANALYSES[:10])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Codebase Copilot server starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
\n`\n\n---\n\n### File: test_app.py\n\n`python\n"""
Unit and Integration Test Suite for Codebase Copilot.
Tests all 6 agents and Flask backend API endpoints.
"""
import os
import unittest
from pathlib import Path
from app import app, run_all_agents, parse_github_url, SAMPLE_REPO_DIR

class TestCodebaseCopilot(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.sample_path = str(SAMPLE_REPO_DIR)

    def test_url_parser(self):
        """Test GitHub URL parsing variants."""
        res1 = parse_github_url("https://github.com/pallets/flask")
        self.assertEqual(res1, {"owner": "pallets", "repo": "flask"})

        res2 = parse_github_url("https://github.com/pallets/flask.git")
        self.assertEqual(res2, {"owner": "pallets", "repo": "flask"})

        res3 = parse_github_url("pallets/flask")
        self.assertEqual(res3, {"owner": "pallets", "repo": "flask"})

        res4 = parse_github_url("invalid-url-here")
        self.assertIsNone(res4)

    def test_all_agents_on_sample_repo(self):
        """Test running all 6 agents against the sample repository."""
        data = run_all_agents("demo-user/ecommerce-microservice", self.sample_path)

        # 1. Repository Analysis Agent
        repo = data.get("repository_analysis", {})
        self.assertGreater(repo.get("total_files", 0), 0)
        self.assertGreater(repo.get("total_lines", 0), 0)
        self.assertIn("Python", [l["language"] for l in repo.get("languages", [])])

        # 2. Code Understanding Agent
        under = data.get("code_understanding", {})
        self.assertGreater(under.get("total_classes_found", 0), 0)
        self.assertGreater(under.get("total_functions_found", 0), 0)
        self.assertTrue(len(under.get("files", [])) > 0)

        # 3. Bug Detection Agent
        bugs = data.get("bug_detection", {})
        self.assertGreater(bugs.get("total_issues", 0), 0)
        self.assertIn("CRITICAL", bugs.get("severity_counts", {}))

        # 4. Code Review Agent
        review = data.get("code_review", {})
        self.assertIn("quality_score", review)
        self.assertIn("maintainability_grade", review)
        self.assertGreater(len(review.get("duplicate_blocks", [])), 0)

        # 5. Documentation Agent
        docs = data.get("documentation", {})
        self.assertIn("readme_markdown", docs)
        self.assertIn("mermaid_diagram", docs)

        # 6. Improvement Agent
        imp = data.get("code_improvement", {})
        self.assertGreater(imp.get("total_improvements", 0), 0)

    def test_home_route(self):
        """Test home landing page route."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"CODEBASE", resp.data)

    def test_dashboard_route(self):
        """Test dashboard route."""
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Dashboard", resp.data)

    def test_analyze_sample_api(self):
        """Test POST /api/analyze-sample endpoint."""
        resp = self.client.post("/api/analyze-sample")
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertEqual(json_data.get("status"), "success")
        self.assertIn("analysis_id", json_data)
        self.assertIn("data", json_data)

    def test_file_content_api(self):
        """Test GET /api/file-content endpoint with path safety."""
        # Initialize sample
        self.client.post("/api/analyze-sample")
        resp = self.client.get("/api/file-content?analysis_id=sample-repo&path=models.py")
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("class User", json_data.get("content", ""))

        # Test traversal prevention
        bad_resp = self.client.get("/api/file-content?analysis_id=sample-repo&path=../../app.py")
        self.assertEqual(bad_resp.status_code, 403)

    def test_export_docs_api(self):
        """Test export README endpoint."""
        self.client.post("/api/analyze-sample")
        resp = self.client.get("/api/export-docs/sample-repo")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "text/markdown")

if __name__ == "__main__":
    unittest.main()
\n`\n\n---\n\n### File: agents/__init__.py\n\n`python\n"""
Codebase Copilot Agents Package
Contains the 6 specialized static analysis and understanding agents.
"""

from .repository_agent import RepositoryAgent
from .code_understanding_agent import CodeUnderstandingAgent
from .bug_detection_agent import BugDetectionAgent
from .code_review_agent import CodeReviewAgent
from .documentation_agent import DocumentationAgent
from .improvement_agent import ImprovementAgent

__all__ = [
    "RepositoryAgent",
    "CodeUnderstandingAgent",
    "BugDetectionAgent",
    "CodeReviewAgent",
    "DocumentationAgent",
    "ImprovementAgent",
]
\n`\n\n---\n\n### File: agents/repository_agent.py\n\n`python\nimport os
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
\n`\n\n---\n\n### File: agents/code_understanding_agent.py\n\n`python\nimport os
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
\n`\n\n---\n\n### File: agents/bug_detection_agent.py\n\n`python\nimport os
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
\n`\n\n---\n\n### File: agents/code_review_agent.py\n\n`python\nimport os
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
\n`\n\n---\n\n### File: agents/documentation_agent.py\n\n`python\nimport os
from pathlib import Path
from typing import Dict, List, Any

class DocumentationAgent:
    """
    Agent 5: Documentation Generation Agent
    Synthesizes multi-source repository intelligence to generate:
    - High-level Project Executive Summary
    - Architecture Overview with Mermaid diagrams
    - README.md specification complete with setup and run instructions
    - File & Component catalog explaining critical modules
    - API & Function reference
    """

    def generate(
        self,
        repo_name: str,
        repo_data: Dict[str, Any],
        understanding_data: Dict[str, Any],
        bug_data: Dict[str, Any],
        review_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate complete project documentation and markdown documentation.
        """
        project_type = repo_data.get("project_type", "Software Application")
        total_files = repo_data.get("total_files", 0)
        total_loc = repo_data.get("total_lines", 0)
        languages = repo_data.get("languages", [])
        top_lang = languages[0]["language"] if languages else "Code"

        # Key files
        important_files = self._select_important_files(repo_data, understanding_data)

        # Overview summary
        overview = (
            f"**{repo_name}** is a {project_type} comprising approximately {total_loc:,} lines of code "
            f"across {total_files} tracked files, primarily authored in {top_lang}. "
            f"The codebase employs a {understanding_data.get('architecture_overview', {}).get('pattern', 'modular structure')} "
            f"with dedicated layers for operational logic, utilities, and configuration."
        )

        # Dependency & Setup Guide
        setup_instructions = self._generate_setup_guide(repo_data)

        # Architecture Mermaid Diagram
        mermaid_diagram = self._generate_architecture_diagram(understanding_data)

        # Generate Complete README.md markdown
        readme_markdown = self._build_readme_markdown(
            repo_name=repo_name,
            overview=overview,
            repo_data=repo_data,
            understanding_data=understanding_data,
            setup_instructions=setup_instructions,
            mermaid_diagram=mermaid_diagram,
            important_files=important_files,
            bug_data=bug_data,
            review_data=review_data
        )

        return {
            "project_name": repo_name,
            "project_overview": overview,
            "architecture_pattern": understanding_data.get("architecture_overview", {}).get("pattern", "Modular"),
            "important_files": important_files,
            "setup_instructions": setup_instructions,
            "mermaid_diagram": mermaid_diagram,
            "readme_markdown": readme_markdown
        }

    def _select_important_files(
        self, repo_data: Dict[str, Any], understanding_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify critical entrypoints and core application files."""
        important = []
        understood_files_map = {f["path"]: f for f in understanding_data.get("files", [])}

        # Check entrypoints first
        entrypoints = understanding_data.get("architecture_overview", {}).get("entrypoints", [])
        for ep in entrypoints:
            file_meta = understood_files_map.get(ep, {})
            important.append({
                "path": ep,
                "role": "Entrypoint & Application Setup",
                "summary": file_meta.get("summary", "Initializes configuration, middleware, and application runtime."),
                "classes": len(file_meta.get("classes", [])),
                "functions": len(file_meta.get("functions", []))
            })

        # Add models, controllers, and large logic files
        for f in understanding_data.get("files", []):
            if f["path"] in entrypoints:
                continue
            path_lower = f["path"].lower()
            if any(k in path_lower for k in ("auth", "model", "service", "api", "route", "util", "db")):
                important.append({
                    "path": f["path"],
                    "role": "Core Domain / Service",
                    "summary": f.get("summary", "Provides business logic and data persistence."),
                    "classes": len(f.get("classes", [])),
                    "functions": len(f.get("functions", []))
                })

        return important[:12]

    def _generate_setup_guide(self, repo_data: Dict[str, Any]) -> List[str]:
        """Infer installation and startup steps based on config markers."""
        markers = set(repo_data.get("config_markers", []))
        marker_names = {os.path.basename(m).lower() for m in markers}
        steps = []

        if "requirements.txt" in marker_names or "pyproject.toml" in marker_names or "setup.py" in marker_names:
            steps.extend([
                "1. Clone repository: `git clone <repo_url>` and navigate into folder.",
                "2. Create virtual environment: `python -m venv venv` and activate it.",
                "3. Install dependencies: `pip install -r requirements.txt`.",
                "4. Launch application: `python app.py` or `flask run`."
            ])
        elif "package.json" in marker_names:
            steps.extend([
                "1. Clone repository: `git clone <repo_url>` and navigate into folder.",
                "2. Install npm dependencies: `npm install`.",
                "3. Start development server: `npm start` or `npm run dev`."
            ])
        elif "go.mod" in marker_names:
            steps.extend([
                "1. Clone repository: `git clone <repo_url>`.",
                "2. Download Go modules: `go mod download`.",
                "3. Run main package: `go run main.go`."
            ])
        else:
            steps.extend([
                "1. Clone repository: `git clone <repo_url>`.",
                "2. Review source files and dependencies in root directory.",
                "3. Execute primary script according to language conventions."
            ])

        return steps

    def _generate_architecture_diagram(self, understanding_data: Dict[str, Any]) -> str:
        """Create a Mermaid diagram representing repository components."""
        arch = understanding_data.get("architecture_overview", {})
        entrypoints = arch.get("entrypoints", [])
        controllers = arch.get("controllers", [])
        models = arch.get("models", [])
        utilities = arch.get("utilities", [])

        lines = ["flowchart TD", "    User([Client / User])"]

        if entrypoints:
            ep_label = entrypoints[0].replace("/", "_").replace(".", "_")
            lines.append(f"    User --> {ep_label}[\"Entrypoint: {entrypoints[0]}\"]")
            if controllers:
                c_label = controllers[0].replace("/", "_").replace(".", "_")
                lines.append(f"    {ep_label} --> {c_label}[\"Routing / API: {controllers[0]}\"]")
                if models:
                    m_label = models[0].replace("/", "_").replace(".", "_")
                    lines.append(f"    {c_label} --> {m_label}[(\"Data Models / DB: {models[0]}\")]")
                if utilities:
                    u_label = utilities[0].replace("/", "_").replace(".", "_")
                    lines.append(f"    {c_label} --> {u_label}[\"Helpers & Utils: {utilities[0]}\"]")
            elif models:
                m_label = models[0].replace("/", "_").replace(".", "_")
                lines.append(f"    {ep_label} --> {m_label}[(\"Data Models: {models[0]}\")]")
        else:
            lines.append("    User --> App[\"Application Core\"]")
            lines.append("    App --> Logic[\"Business Services\"]")
            lines.append("    Logic --> Storage[(\"Storage / Utils\")]")

        return "\n".join(lines)

    def _build_readme_markdown(
        self,
        repo_name: str,
        overview: str,
        repo_data: Dict[str, Any],
        understanding_data: Dict[str, Any],
        setup_instructions: List[str],
        mermaid_diagram: str,
        important_files: List[Dict[str, Any]],
        bug_data: Dict[str, Any],
        review_data: Dict[str, Any]
    ) -> str:
        """Assemble full GitHub README markdown string."""
        lang_list = repo_data.get("languages", [])
        lang_bullets = "\n".join([f"- **{l['language']}**: {l['percentage']}% ({l['files']} files, {l['lines']} lines)" for l in lang_list[:5]])
        setup_text = "\n".join(setup_instructions)

        file_table_rows = []
        for f in important_files:
            file_table_rows.append(f"| `{f['path']}` | {f['role']} | {f['summary']} |")
        file_table = "\n".join(file_table_rows)

        readme = f"""# {repo_name}

> *Automated analysis and comprehensive documentation generated by Codebase Copilot.*

## 📋 Project Overview
{overview}

### Key Metrics
- **Primary Architecture:** {understanding_data.get('architecture_overview', {}).get('pattern', 'Modular')}
- **Total Lines of Code:** {repo_data.get('total_lines', 0):,} LOC
- **Files Tracked:** {repo_data.get('total_files', 0)} files in {repo_data.get('total_folders', 0)} directories
- **Code Quality Grade:** {review_data.get('maintainability_grade', 'N/A')} ({review_data.get('quality_score', 0)}/100)
- **Docstring Coverage:** {review_data.get('docstring_coverage_pct', 0)}%
- **Issues Found:** {bug_data.get('total_issues', 0)} potential bug(s) / vulnerabilities

---

## 🏗️ Architecture & Component Flow
```mermaid
{mermaid_diagram}
```

---

## 💻 Tech Stack & Languages
{lang_bullets}

---

## 🚀 Quickstart & Setup Guide
{setup_text}

---

## 📂 Key Modules & File Reference
| File | Role | Summary |
| :--- | :--- | :--- |
{file_table}

---

## 🔍 Code Health Summary
- **Bug Density:** {bug_data.get('bug_density_per_kloc', 0)} issues per 1,000 LOC
- **Critical Security Items:** {bug_data.get('severity_counts', {}).get('CRITICAL', 0)}
- **High Severity Bugs:** {bug_data.get('severity_counts', {}).get('HIGH', 0)}
- **Maintainability Suggestions:** {len(review_data.get('review_suggestions', []))} items flagged for refactoring

---
*Generated automatically with Codebase Copilot Static Intelligence Engine.*
"""
        return readme
\n`\n\n---\n\n### File: agents/improvement_agent.py\n\n`python\nimport os
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
\n`\n\n---\n\n### File: templates/index.html\n\n`html\n<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Copilot – AI for GitHub Repositories</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
</head>
<body class="landing-page">
    <!-- Navigation Bar -->
    <header class="navbar">
        <div class="nav-container">
            <div class="logo">
                <span class="logo-icon">⚡</span>
                <span class="logo-text">CODEBASE <strong>COPILOT</strong></span>
                <span class="badge-tag">AI Multi-Agent</span>
            </div>
            <nav class="nav-links">
                <a href="#features">Agent Capabilities</a>
                <a href="#how-it-works">How It Works</a>
                <button class="btn btn-outline-sm" onclick="runSampleDemo()">Try Demo Repo</button>
            </nav>
        </div>
    </header>

    <!-- Hero Section -->
    <main class="hero-section">
        <div class="hero-content">
            <div class="pill-badge">
                <span class="pulse-dot"></span> 100% Free • Rule-Based Static Intelligence • Zero API Keys
            </div>
            <h1 class="hero-title">
                Deep Intelligence for Any <br>
                <span class="gradient-text">GitHub Repository</span>
            </h1>
            <p class="hero-subtitle">
                Autonomous multi-agent code analysis: AST code understanding, security bug detection, 
                code review auditing, automated README generation, and performance optimization suggestions.
            </p>

            <!-- URL Input Box -->
            <div class="analysis-box">
                <form id="analyze-form" onsubmit="handleAnalyzeSubmit(event)">
                    <div class="input-wrapper">
                        <span class="input-icon">🔗</span>
                        <input 
                            type="text" 
                            id="repo-url-input" 
                            placeholder="Enter public GitHub URL (e.g. https://github.com/pallets/flask or pallets/flask)" 
                            required
                            autocomplete="off"
                        >
                        <button type="submit" id="analyze-btn" class="btn btn-primary">
                            <span class="btn-text">Analyze Repository</span>
                            <span class="btn-arrow">→</span>
                        </button>
                    </div>
                </form>

                <div class="sample-pills">
                    <span class="sample-label">Or try quick samples:</span>
                    <button class="pill-btn highlight" onclick="runSampleDemo()">
                        ✨ Built-in Demo Store (Instant)
                    </button>
                    <button class="pill-btn" onclick="quickFill('https://github.com/pallets/flask')">
                        pallets/flask
                    </button>
                    <button class="pill-btn" onclick="quickFill('https://github.com/psf/requests')">
                        psf/requests
                    </button>
                </div>
            </div>

            <!-- Loading & Progress State Overlay -->
            <div id="loading-container" class="loading-container hidden">
                <div class="spinner-orbit">
                    <div class="orbit-ring"></div>
                    <div class="orbit-core">⚡</div>
                </div>
                <h3 id="loading-status-title">Dispatching Analysis Agents...</h3>
                <p id="loading-status-desc">Validating repository metadata and checking accessibility...</p>
                
                <div class="agent-stepper">
                    <div class="step-item active" id="step-repo">
                        <span class="step-bullet">1</span>
                        <span class="step-label">Repo Scanner</span>
                    </div>
                    <div class="step-item" id="step-ast">
                        <span class="step-bullet">2</span>
                        <span class="step-label">AST Comprehension</span>
                    </div>
                    <div class="step-item" id="step-bugs">
                        <span class="step-bullet">3</span>
                        <span class="step-label">Bug & Security Agent</span>
                    </div>
                    <div class="step-item" id="step-review">
                        <span class="step-bullet">4</span>
                        <span class="step-label">Code Reviewer</span>
                    </div>
                    <div class="step-item" id="step-docs">
                        <span class="step-bullet">5</span>
                        <span class="step-label">Doc Synthesizer</span>
                    </div>
                    <div class="step-item" id="step-opt">
                        <span class="step-bullet">6</span>
                        <span class="step-label">Optimization Agent</span>
                    </div>
                </div>
            </div>

            <!-- Error Banner -->
            <div id="error-banner" class="error-banner hidden">
                <span class="error-icon">⚠️</span>
                <span id="error-message">Something went wrong.</span>
                <button class="error-dismiss" onclick="dismissError()">✕</button>
            </div>
        </div>

        <!-- 6 Agent Feature Cards Grid -->
        <section id="features" class="agents-grid-section">
            <h2 class="section-heading">Powered by 6 Specialized Analysis Agents</h2>
            <p class="section-subheading">Engineered with AST parsing, token heuristics, and deterministic static auditing.</p>

            <div class="cards-grid">
                <div class="agent-card">
                    <div class="card-icon blue">📁</div>
                    <h3>Repository Analysis Agent</h3>
                    <p>Scans full folder hierarchies, catalogues lines of code (SLOC, comments, blanks), detects project configurations, and breaks down programming languages.</p>
                </div>

                <div class="agent-card">
                    <div class="card-icon purple">🧠</div>
                    <h3>Code Understanding Agent</h3>
                    <p>Parses abstract syntax trees to explain function intent, extracts classes and methods, identifies dependencies, and generates human-like summaries.</p>
                </div>

                <div class="agent-card">
                    <div class="card-icon red">🐛</div>
                    <h3>Bug Detection Agent</h3>
                    <p>Pins down syntax errors, SQL injections, hardcoded credentials, bare exception traps, mutable defaults, and unsafe DOM manipulations with line numbers.</p>
                </div>

                <div class="agent-card">
                    <div class="card-icon amber">🔍</div>
                    <h3>Code Review Agent</h3>
                    <p>Audits cyclomatic complexity, uncovers duplicate code patterns, flags unused imports, checks docstring coverage, and computes a Maintainability Grade.</p>
                </div>

                <div class="agent-card">
                    <div class="card-icon teal">📖</div>
                    <h3>Documentation Agent</h3>
                    <p>Synthesizes comprehensive README.md specifications, architectural diagrams (Mermaid flowcharts), setup guides, and module catalogs.</p>
                </div>

                <div class="agent-card">
                    <div class="card-icon green">⚡</div>
                    <h3>Code Improvement Agent</h3>
                    <p>Formulates actionable Before & After refactoring suggestions: list comprehension speedups, $O(1)$ set lookups, f-string modernization, and CI/CD hygiene.</p>
                </div>
            </div>
        </section>
    </main>

    <!-- Footer -->
    <footer class="footer">
        <p>Codebase Copilot • Built for Developers • Pure Static Intelligence Engine</p>
    </footer>

    <script src="/static/js/script.js"></script>
</body>
</html>
\n`\n\n---\n\n### File: templates/dashboard.html\n\n`html\n<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard – Codebase Copilot</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="dashboard-page">

    <!-- Top Navigation Bar -->
    <header class="dash-header">
        <div class="dash-nav-left">
            <a href="/" class="dash-logo">
                <span class="logo-icon">⚡</span>
                <span class="logo-text">CODEBASE <strong>COPILOT</strong></span>
            </a>
            <div class="repo-badge-box">
                <span class="repo-icon">📦</span>
                <span id="repo-title-header" class="repo-name-text">Loading...</span>
                <span id="repo-type-tag" class="tech-tag">Repository</span>
            </div>
        </div>
        <div class="dash-nav-right">
            <button class="btn btn-outline-sm" onclick="exportMarkdownDoc()">
                ⬇️ Export README.md
            </button>
            <button class="btn btn-outline-sm" onclick="exportJsonReport()">
                📄 Export JSON Audit
            </button>
            <a href="/" class="btn btn-primary-sm">
                🔍 New Analysis
            </a>
        </div>
    </header>

    <div class="dash-layout">
        <!-- Sidebar Navigation Tabs -->
        <aside class="dash-sidebar">
            <div class="sidebar-menu">
                <button class="menu-item active" onclick="switchTab('tab-overview', this)">
                    <span class="menu-icon">📊</span>
                    <span class="menu-label">Overview & Metrics</span>
                </button>
                <button class="menu-item" onclick="switchTab('tab-repo', this)">
                    <span class="menu-icon">📁</span>
                    <span class="menu-label">Repository & Tree</span>
                </button>
                <button class="menu-item" onclick="switchTab('tab-understanding', this)">
                    <span class="menu-icon">🧠</span>
                    <span class="menu-label">Code Understanding</span>
                </button>
                <button class="menu-item" onclick="switchTab('tab-bugs', this)">
                    <span class="menu-icon">🐛</span>
                    <span class="menu-label">Bug Detection</span>
                    <span id="bug-count-badge" class="nav-badge red">0</span>
                </button>
                <button class="menu-item" onclick="switchTab('tab-review', this)">
                    <span class="menu-icon">🔍</span>
                    <span class="menu-label">Code Review & Smells</span>
                    <span id="review-grade-badge" class="nav-badge green">A</span>
                </button>
                <button class="menu-item" onclick="switchTab('tab-docs', this)">
                    <span class="menu-icon">📖</span>
                    <span class="menu-label">Generated Docs</span>
                </button>
                <button class="menu-item" onclick="switchTab('tab-improvements', this)">
                    <span class="menu-icon">⚡</span>
                    <span class="menu-label">Improvements</span>
                    <span id="imp-count-badge" class="nav-badge blue">0</span>
                </button>
            </div>

            <!-- Repository Quick Summary in Sidebar -->
            <div class="sidebar-card">
                <h4>Health Rating</h4>
                <div class="grade-meter-container">
                    <div id="grade-display" class="grade-circle">A</div>
                    <div class="grade-meta">
                        <div id="quality-score-text" class="score-num">-- / 100</div>
                        <div id="maintainability-text" class="score-sub">Maintainability</div>
                    </div>
                </div>
            </div>
        </aside>

        <!-- Main Content Area -->
        <main class="dash-main">

            <!-- Top Metric Counters Grid -->
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-icon blue">📁</div>
                    <div class="metric-info">
                        <span class="metric-value" id="stat-files">0</span>
                        <span class="metric-title">Total Files</span>
                    </div>
                    <span class="metric-sub" id="stat-folders">0 Folders</span>
                </div>

                <div class="metric-card">
                    <div class="metric-icon green">📝</div>
                    <div class="metric-info">
                        <span class="metric-value" id="stat-loc">0</span>
                        <span class="metric-title">Lines of Code</span>
                    </div>
                    <span class="metric-sub" id="stat-sloc">0 Code Lines</span>
                </div>

                <div class="metric-card">
                    <div class="metric-icon red">🐛</div>
                    <div class="metric-info">
                        <span class="metric-value" id="stat-issues">0</span>
                        <span class="metric-title">Issues Found</span>
                    </div>
                    <span class="metric-sub" id="stat-critical-count">0 Critical</span>
                </div>

                <div class="metric-card">
                    <div class="metric-icon purple">🧩</div>
                    <div class="metric-info">
                        <span class="metric-value" id="stat-functions">0</span>
                        <span class="metric-title">Functions & Classes</span>
                    </div>
                    <span class="metric-sub" id="stat-doc-coverage">0% Documented</span>
                </div>
            </div>

            <!-- 3 CHARTS SECTION -->
            <div class="charts-row">
                <!-- Chart 1: Connected Line Graph (LOC by File) -->
                <div class="chart-card">
                    <div class="chart-header">
                        <h3>📈 Connected Line Graph: Code Volume by Top Files</h3>
                        <span class="chart-tag">Distribution</span>
                    </div>
                    <div class="chart-canvas-wrapper">
                        <canvas id="lineChartLOC"></canvas>
                    </div>
                </div>

                <!-- Chart 2: Bug Severity Pie/Doughnut Chart -->
                <div class="chart-card">
                    <div class="chart-header">
                        <h3>🎯 Bug Severity Breakdown</h3>
                        <span class="chart-tag">Security & Bugs</span>
                    </div>
                    <div class="chart-canvas-wrapper">
                        <canvas id="pieChartBugs"></canvas>
                    </div>
                </div>

                <!-- Chart 3: File Type / Language Bar Chart -->
                <div class="chart-card">
                    <div class="chart-header">
                        <h3>📊 Language & File Type Distribution</h3>
                        <span class="chart-tag">Composition</span>
                    </div>
                    <div class="chart-canvas-wrapper">
                        <canvas id="barChartLanguages"></canvas>
                    </div>
                </div>
            </div>

            <!-- ================= TAB 1: OVERVIEW & METRICS ================= -->
            <section id="tab-overview" class="tab-pane active">
                <div class="pane-grid-2">
                    <div class="pane-card">
                        <h3>🏗️ Architecture & Component Overview</h3>
                        <p id="overview-arch-text" class="overview-paragraph">Analyzing architecture...</p>
                        <div class="tag-row" id="config-markers-tags"></div>
                    </div>

                    <div class="pane-card">
                        <h3>🏆 Top Largest Files by Line Count</h3>
                        <div class="table-container">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>File</th>
                                        <th>Language</th>
                                        <th>Lines</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody id="largest-files-tbody"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ================= TAB 2: REPOSITORY & TREE ================= -->
            <section id="tab-repo" class="tab-pane">
                <div class="pane-header-actions">
                    <h2>📁 Repository Directory Tree & File Inventory</h2>
                    <input type="text" id="file-search-input" placeholder="Search files by path or name..." oninput="filterFileList()" class="search-field">
                </div>
                <div class="repo-tree-layout">
                    <div class="tree-container">
                        <h3>File Tree Hierarchy</h3>
                        <div id="tree-view-root" class="tree-root"></div>
                    </div>
                    <div class="file-table-pane">
                        <h3>All Cataloged Files (<span id="file-catalog-count">0</span>)</h3>
                        <div class="table-scroll-wrap">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>File Path</th>
                                        <th>Type</th>
                                        <th>Size</th>
                                        <th>Lines</th>
                                        <th>Inspect</th>
                                    </tr>
                                </thead>
                                <tbody id="all-files-tbody"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ================= TAB 3: CODE UNDERSTANDING ================= -->
            <section id="tab-understanding" class="tab-pane">
                <div class="pane-header-actions">
                    <h2>🧠 Code Understanding & AST Symbol Catalog</h2>
                    <div class="filter-group">
                        <button class="filter-pill active" onclick="filterAST('all', this)">All</button>
                        <button class="filter-pill" onclick="filterAST('classes', this)">Classes</button>
                        <button class="filter-pill" onclick="filterAST('functions', this)">Functions</button>
                    </div>
                </div>

                <div class="pane-grid-2">
                    <!-- File Summaries Column -->
                    <div class="pane-card">
                        <h3>Module & File Summaries</h3>
                        <div id="file-summaries-list" class="stacked-list"></div>
                    </div>

                    <!-- Classes & Functions Column -->
                    <div class="pane-card">
                        <h3>Extracted Symbols & Explanations</h3>
                        <div id="ast-symbols-list" class="stacked-list"></div>
                    </div>
                </div>
            </section>

            <!-- ================= TAB 4: BUG DETECTION ================= -->
            <section id="tab-bugs" class="tab-pane">
                <div class="pane-header-actions">
                    <div>
                        <h2>🐛 Static Bug & Security Vulnerability Audit</h2>
                        <p class="subtitle-text">Deterministic rule-based checks: syntax errors, SQL injection, hardcoded secrets, mutable defaults, and unsafe DOM.</p>
                    </div>
                    <div class="filter-group">
                        <button class="filter-pill active" onclick="filterBugs('ALL', this)">All (<span id="filter-all-cnt">0</span>)</button>
                        <button class="filter-pill red" onclick="filterBugs('CRITICAL', this)">Critical (<span id="filter-crit-cnt">0</span>)</button>
                        <button class="filter-pill orange" onclick="filterBugs('HIGH', this)">High (<span id="filter-high-cnt">0</span>)</button>
                        <button class="filter-pill amber" onclick="filterBugs('MEDIUM', this)">Medium (<span id="filter-med-cnt">0</span>)</button>
                        <button class="filter-pill blue" onclick="filterBugs('LOW', this)">Low (<span id="filter-low-cnt">0</span>)</button>
                    </div>
                </div>

                <div id="bugs-list-container" class="cards-list"></div>
            </section>

            <!-- ================= TAB 5: CODE REVIEW & SMELLS ================= -->
            <section id="tab-review" class="tab-pane">
                <div class="pane-header-actions">
                    <h2>🔍 Automated Code Review & Maintainability Audit</h2>
                </div>

                <div class="pane-grid-2">
                    <div class="pane-card">
                        <h3>⚡ High Cyclomatic Complexity Hotspots</h3>
                        <p class="subtitle-text">Functions with complexity &gt; 10 requiring conditional branching refactoring.</p>
                        <div id="complex-functions-list" class="stacked-list"></div>
                    </div>

                    <div class="pane-card">
                        <h3>👥 Code Duplication Detection</h3>
                        <p class="subtitle-text">Identical code sequences repeated across files.</p>
                        <div id="duplicate-blocks-list" class="stacked-list"></div>
                    </div>
                </div>

                <div class="pane-card mt-20">
                    <h3>💡 Best Practice & Clean Code Suggestions</h3>
                    <div id="review-suggestions-list" class="cards-list"></div>
                </div>
            </section>

            <!-- ================= TAB 6: GENERATED DOCS ================= -->
            <section id="tab-docs" class="tab-pane">
                <div class="pane-header-actions">
                    <h2>📖 Generated Repository Documentation & README</h2>
                    <div class="btn-group">
                        <button class="btn btn-outline-sm" onclick="copyReadmeText()">📋 Copy Markdown</button>
                        <button class="btn btn-primary-sm" onclick="exportMarkdownDoc()">⬇️ Download README.md</button>
                    </div>
                </div>

                <div class="doc-viewer-card">
                    <pre id="readme-preview-content" class="doc-pre"></pre>
                </div>
            </section>

            <!-- ================= TAB 7: CODE IMPROVEMENTS ================= -->
            <section id="tab-improvements" class="tab-pane">
                <div class="pane-header-actions">
                    <h2>⚡ Concrete Code Improvements & Modernization Plans</h2>
                    <p class="subtitle-text">Actionable Before vs After refactoring optimizations for performance, memory, and code style.</p>
                </div>

                <div id="improvements-list-container" class="cards-list"></div>
            </section>

        </main>
    </div>

    <!-- CODE INSPECTOR MODAL / SLIDEOUT -->
    <div id="code-modal" class="modal-overlay hidden">
        <div class="modal-container">
            <div class="modal-header">
                <div class="modal-title-box">
                    <span class="file-icon">📄</span>
                    <span id="modal-filename">filename.py</span>
                    <span id="modal-filepath" class="modal-path">path/to/file.py</span>
                </div>
                <button class="modal-close" onclick="closeCodeModal()">✕</button>
            </div>
            <div class="modal-body">
                <div id="modal-code-lines" class="code-viewer-wrap"></div>
            </div>
        </div>
    </div>

    <script src="/static/js/script.js"></script>
</body>
</html>
\n`\n\n---\n\n### File: static/css/style.css\n\n`css\n/* Codebase Copilot Stylesheet - Modern Dark Developer Theme */
:root {
    --bg-main: #0b0f19;
    --bg-surface: #111827;
    --bg-card: #162032;
    --bg-card-hover: #1e293b;
    --border-color: #27354a;
    --border-light: #334155;
    
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    
    --primary: #3b82f6;
    --primary-hover: #2563eb;
    --primary-glow: rgba(59, 130, 246, 0.25);
    
    --accent-purple: #8b5cf6;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-red: #ef4444;
    --accent-cyan: #06b6d4;

    --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background-color: var(--bg-main);
    color: var(--text-primary);
    font-family: var(--font-sans);
    line-height: 1.5;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
}

/* Typography Helpers */
h1, h2, h3, h4, h5 {
    color: var(--text-primary);
    font-weight: 700;
}

a {
    color: var(--primary);
    text-decoration: none;
    transition: color 0.2s;
}

a:hover {
    color: var(--text-primary);
}

.gradient-text {
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-family: var(--font-sans);
    font-weight: 600;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
}

.btn-primary {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: #ffffff;
    padding: 14px 28px;
    font-size: 1rem;
    box-shadow: 0 4px 14px var(--primary-glow);
}

.btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.btn-primary-sm {
    background: #3b82f6;
    color: #ffffff;
    padding: 8px 16px;
    font-size: 0.875rem;
    border-radius: var(--radius-sm);
}

.btn-outline-sm {
    background: transparent;
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 8px 16px;
    font-size: 0.875rem;
    border-radius: var(--radius-sm);
}

.btn-outline-sm:hover {
    background: var(--bg-card);
    border-color: var(--text-muted);
}

/* Badges */
.badge-tag {
    background: rgba(99, 102, 241, 0.15);
    color: #818cf8;
    border: 1px solid rgba(99, 102, 241, 0.3);
    padding: 3px 8px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}

.tech-tag {
    background: #1e293b;
    color: var(--text-secondary);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    border: 1px solid var(--border-color);
}

/* ================= LANDING PAGE ================= */
.navbar {
    border-bottom: 1px solid var(--border-color);
    background: rgba(11, 15, 25, 0.8);
    backdrop-filter: blur(12px);
    position: sticky;
    top: 0;
    z-index: 50;
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.15rem;
    letter-spacing: -0.5px;
}

.logo-icon {
    font-size: 1.4rem;
}

.nav-links {
    display: flex;
    align-items: center;
    gap: 20px;
}

.hero-section {
    max-width: 1100px;
    margin: 0 auto;
    padding: 70px 24px 40px;
    text-align: center;
}

.pill-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid var(--border-color);
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-bottom: 24px;
}

.pulse-dot {
    width: 8px;
    height: 8px;
    background: var(--accent-emerald);
    border-radius: 50%;
    box-shadow: 0 0 10px var(--accent-emerald);
}

.hero-title {
    font-size: 3.5rem;
    line-height: 1.15;
    margin-bottom: 20px;
    font-weight: 800;
}

.hero-subtitle {
    font-size: 1.15rem;
    color: var(--text-secondary);
    max-width: 720px;
    margin: 0 auto 40px;
}

/* Analysis Input Box */
.analysis-box {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 24px;
    max-width: 780px;
    margin: 0 auto 30px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
}

.input-wrapper {
    display: flex;
    align-items: center;
    background: #0b0f19;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 6px 6px 6px 16px;
    transition: border-color 0.2s;
}

.input-wrapper:focus-within {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-glow);
}

.input-icon {
    font-size: 1.2rem;
    margin-right: 10px;
    opacity: 0.6;
}

.input-wrapper input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text-primary);
    font-size: 1rem;
    font-family: var(--font-sans);
}

.sample-pills {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    margin-top: 18px;
    font-size: 0.85rem;
}

.sample-label {
    color: var(--text-muted);
}

.pill-btn {
    background: #1e293b;
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 6px 12px;
    border-radius: 9999px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
}

.pill-btn:hover {
    background: #334155;
    color: var(--text-primary);
}

.pill-btn.highlight {
    background: rgba(59, 130, 246, 0.15);
    border-color: rgba(59, 130, 246, 0.4);
    color: #93c5fd;
}

/* Loading Stepper Container */
.loading-container {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 30px;
    max-width: 780px;
    margin: 20px auto;
    text-align: center;
}

.spinner-orbit {
    position: relative;
    width: 60px;
    height: 60px;
    margin: 0 auto 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.orbit-ring {
    position: absolute;
    width: 100%;
    height: 100%;
    border: 3px solid rgba(59, 130, 246, 0.2);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.orbit-core {
    font-size: 1.5rem;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.agent-stepper {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 8px;
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid var(--border-color);
}

.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    opacity: 0.4;
    transition: all 0.3s;
}

.step-item.active {
    opacity: 1;
    color: var(--primary);
}

.step-item.done {
    opacity: 0.9;
    color: var(--accent-emerald);
}

.step-bullet {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #1e293b;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
}

.step-item.active .step-bullet {
    background: var(--primary);
    color: #fff;
}

.step-item.done .step-bullet {
    background: var(--accent-emerald);
    color: #fff;
}

.step-label {
    font-size: 0.72rem;
    font-weight: 500;
}

/* Error Banner */
.error-banner {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #fca5a5;
    padding: 12px 18px;
    border-radius: var(--radius-md);
    max-width: 780px;
    margin: 16px auto;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.95rem;
}

.error-dismiss {
    margin-left: auto;
    background: transparent;
    border: none;
    color: #fca5a5;
    font-size: 1.1rem;
    cursor: pointer;
}

/* Feature Grid */
.agents-grid-section {
    margin-top: 60px;
}

.section-heading {
    font-size: 2rem;
    margin-bottom: 8px;
}

.section-subheading {
    color: var(--text-secondary);
    margin-bottom: 40px;
}

.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 20px;
    text-align: left;
}

.agent-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 24px;
    transition: transform 0.2s, border-color 0.2s;
}

.agent-card:hover {
    transform: translateY(-3px);
    border-color: var(--border-light);
}

.card-icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    margin-bottom: 16px;
}

.card-icon.blue { background: rgba(59, 130, 246, 0.15); }
.card-icon.purple { background: rgba(139, 92, 246, 0.15); }
.card-icon.red { background: rgba(239, 68, 68, 0.15); }
.card-icon.amber { background: rgba(245, 158, 11, 0.15); }
.card-icon.teal { background: rgba(20, 184, 166, 0.15); }
.card-icon.green { background: rgba(16, 185, 129, 0.15); }

.agent-card h3 {
    font-size: 1.15rem;
    margin-bottom: 10px;
}

.agent-card p {
    color: var(--text-secondary);
    font-size: 0.92rem;
    line-height: 1.5;
}

/* Footer */
.footer {
    border-top: 1px solid var(--border-color);
    padding: 30px 24px;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-top: 60px;
}

/* ================= DASHBOARD LAYOUT ================= */
.dash-header {
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border-color);
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 40;
}

.dash-nav-left {
    display: flex;
    align-items: center;
    gap: 20px;
}

.dash-logo {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.05rem;
    color: var(--text-primary);
}

.repo-badge-box {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #0b0f19;
    border: 1px solid var(--border-color);
    padding: 6px 12px;
    border-radius: var(--radius-sm);
}

.repo-name-text {
    font-weight: 700;
    font-family: var(--font-mono);
    font-size: 0.9rem;
    color: #60a5fa;
}

.dash-nav-right {
    display: flex;
    align-items: center;
    gap: 12px;
}

.dash-layout {
    display: flex;
    min-height: calc(100vh - 65px);
}

/* Sidebar */
.dash-sidebar {
    width: 250px;
    background: var(--bg-surface);
    border-right: 1px solid var(--border-color);
    padding: 20px 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    flex-shrink: 0;
}

.sidebar-menu {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.menu-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    font-family: var(--font-sans);
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    text-align: left;
    transition: all 0.2s;
    width: 100%;
}

.menu-item:hover {
    background: var(--bg-card);
    color: var(--text-primary);
}

.menu-item.active {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    font-weight: 600;
}

.nav-badge {
    margin-left: auto;
    font-size: 0.75rem;
    padding: 2px 7px;
    border-radius: 9999px;
    font-weight: 700;
}

.nav-badge.red { background: rgba(239, 68, 68, 0.2); color: #f87171; }
.nav-badge.green { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.nav-badge.blue { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }

/* Grade Circle Widget */
.sidebar-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 14px;
    text-align: center;
}

.sidebar-card h4 {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
}

.grade-meter-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
}

.grade-circle {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: #10b981;
    color: #ffffff;
    font-weight: 800;
    font-size: 1.3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}

.grade-meta {
    text-align: left;
}

.score-num {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
}

.score-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* Main Dashboard Area */
.dash-main {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    max-width: 1500px;
}

/* Metric Cards */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.metric-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 18px;
    display: flex;
    align-items: center;
    position: relative;
}

.metric-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    margin-right: 16px;
}

.metric-icon.blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.metric-icon.green { background: rgba(16, 185, 129, 0.15); color: #34d399; }
.metric-icon.red { background: rgba(239, 68, 68, 0.15); color: #f87171; }
.metric-icon.purple { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }

.metric-value {
    display: block;
    font-size: 1.6rem;
    font-weight: 800;
    line-height: 1.1;
}

.metric-title {
    display: block;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.metric-sub {
    position: absolute;
    bottom: 12px;
    right: 16px;
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* Charts Row */
.charts-row {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1.2fr;
    gap: 16px;
    margin-bottom: 24px;
}

@media (max-width: 1200px) {
    .charts-row {
        grid-template-columns: 1fr;
    }
}

.chart-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 16px 20px;
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}

.chart-header h3 {
    font-size: 0.95rem;
    font-weight: 600;
}

.chart-tag {
    font-size: 0.7rem;
    background: var(--bg-card);
    padding: 3px 8px;
    border-radius: 4px;
    color: var(--text-muted);
}

.chart-canvas-wrapper {
    height: 220px;
    position: relative;
}

/* Tab Panes */
.tab-pane {
    display: none;
}

.tab-pane.active {
    display: block;
    animation: fadeIn 0.2s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}

.pane-header-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 12px;
}

.subtitle-text {
    color: var(--text-secondary);
    font-size: 0.88rem;
    margin-top: 4px;
}

.pane-grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

@media (max-width: 900px) {
    .pane-grid-2 {
        grid-template-columns: 1fr;
    }
}

.pane-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 20px;
}

.pane-card h3 {
    font-size: 1.1rem;
    margin-bottom: 12px;
}

.mt-20 {
    margin-top: 20px;
}

/* Tables */
.table-container {
    overflow-x: auto;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
}

.data-table th {
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid var(--border-color);
    color: var(--text-muted);
    font-weight: 600;
}

.data-table td {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: var(--text-secondary);
}

.data-table tr:hover td {
    background: var(--bg-card);
    color: var(--text-primary);
}

/* Repo Tree & File Explorer */
.repo-tree-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 20px;
}

@media (max-width: 900px) {
    .repo-tree-layout {
        grid-template-columns: 1fr;
    }
}

.tree-container, .file-table-pane {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 18px;
    max-height: 600px;
    overflow-y: auto;
}

.tree-root ul {
    list-style: none;
    padding-left: 14px;
}

.tree-item {
    margin: 4px 0;
    font-size: 0.88rem;
    cursor: pointer;
    font-family: var(--font-mono);
}

.tree-folder {
    font-weight: 600;
    color: #93c5fd;
}

.tree-file {
    color: var(--text-secondary);
}

.tree-file:hover {
    color: var(--text-primary);
}

/* Search Field */
.search-field {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    padding: 8px 14px;
    color: var(--text-primary);
    font-family: var(--font-sans);
    font-size: 0.88rem;
    min-width: 280px;
}

.search-field:focus {
    outline: none;
    border-color: var(--primary);
}

/* Filter Groups */
.filter-group {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.filter-pill {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.filter-pill:hover, .filter-pill.active {
    background: var(--primary);
    color: #ffffff;
    border-color: var(--primary);
}

.filter-pill.red.active { background: var(--accent-red); border-color: var(--accent-red); }
.filter-pill.orange.active { background: #ea580c; border-color: #ea580c; }
.filter-pill.amber.active { background: var(--accent-amber); border-color: var(--accent-amber); }
.filter-pill.blue.active { background: var(--primary); border-color: var(--primary); }

/* Stacked Lists */
.stacked-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 550px;
    overflow-y: auto;
}

.stacked-item {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
}

.stacked-title {
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 4px;
    display: flex;
    justify-content: space-between;
}

.stacked-desc {
    font-size: 0.85rem;
    color: var(--text-secondary);
}

/* Issue / Bug Cards */
.cards-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.issue-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-left: 4px solid var(--primary);
    border-radius: var(--radius-md);
    padding: 18px 20px;
}

.issue-card.CRITICAL { border-left-color: var(--accent-red); }
.issue-card.HIGH { border-left-color: #ea580c; }
.issue-card.MEDIUM { border-left-color: var(--accent-amber); }
.issue-card.LOW { border-left-color: var(--primary); }

.issue-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.severity-pill {
    font-size: 0.72rem;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 4px;
    text-transform: uppercase;
}

.severity-pill.CRITICAL { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
.severity-pill.HIGH { background: rgba(234, 88, 12, 0.2); color: #fb923c; border: 1px solid rgba(234, 88, 12, 0.4); }
.severity-pill.MEDIUM { background: rgba(245, 158, 11, 0.2); color: #fde047; border: 1px solid rgba(245, 158, 11, 0.4); }
.severity-pill.LOW { background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }

.issue-location {
    font-family: var(--font-mono);
    font-size: 0.85rem;
    color: var(--text-muted);
}

.issue-title {
    font-size: 1.05rem;
    margin-bottom: 6px;
}

.issue-desc {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-bottom: 12px;
}

.code-snippet-box {
    background: #0b0f19;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    color: #e2e8f0;
    overflow-x: auto;
    margin-bottom: 12px;
}

.remediation-box {
    background: rgba(16, 185, 129, 0.08);
    border-left: 3px solid var(--accent-emerald);
    padding: 8px 12px;
    font-size: 0.85rem;
    color: #a7f3d0;
}

/* Improvement Diff Cards */
.diff-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 20px;
}

.diff-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.diff-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 14px;
}

@media (max-width: 800px) {
    .diff-grid {
        grid-template-columns: 1fr;
    }
}

.diff-box {
    border-radius: var(--radius-sm);
    overflow: hidden;
}

.diff-box-title {
    padding: 6px 12px;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.diff-box.before .diff-box-title {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
}

.diff-box.after .diff-box-title {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
}

.diff-pre {
    background: #0b0f19;
    padding: 12px;
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: #cbd5e1;
    overflow-x: auto;
    min-height: 70px;
}

/* Documentation Viewer */
.doc-viewer-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 24px;
}

.doc-pre {
    background: #0b0f19;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    padding: 20px;
    font-family: var(--font-mono);
    font-size: 0.88rem;
    color: #e2e8f0;
    white-space: pre-wrap;
    line-height: 1.6;
    max-height: 700px;
    overflow-y: auto;
}

/* Code Inspector Modal */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(6px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
}

.modal-container {
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    width: 90%;
    max-width: 960px;
    height: 80vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
}

.modal-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-title-box {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1rem;
    font-weight: 700;
}

.modal-path {
    font-size: 0.8rem;
    font-family: var(--font-mono);
    color: var(--text-muted);
}

.modal-close {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 1.2rem;
    cursor: pointer;
}

.modal-close:hover {
    color: var(--text-primary);
}

.modal-body {
    flex: 1;
    overflow-y: auto;
    padding: 0;
    background: #0b0f19;
}

.code-viewer-wrap {
    font-family: var(--font-mono);
    font-size: 0.85rem;
    line-height: 1.6;
    padding: 12px 0;
}

.code-line-row {
    display: flex;
    padding: 0 16px;
}

.code-line-row:hover {
    background: rgba(255, 255, 255, 0.04);
}

.line-num {
    width: 45px;
    color: var(--text-muted);
    user-select: none;
    text-align: right;
    padding-right: 16px;
    flex-shrink: 0;
}

.line-code {
    color: #e2e8f0;
    white-space: pre;
    flex: 1;
}

.tag-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 14px;
}

.hidden {
    display: none !important;
}
\n`\n\n---\n\n### File: static/js/script.js\n\n`javascript\n/* Codebase Copilot - Frontend Application Logic & Chart.js Integration */

let currentAnalysisId = null;
let currentAnalysisData = null;
let allFilesCache = [];
let allBugsCache = [];

// Chart instances
let locLineChart = null;
let bugPieChart = null;
let langBarChart = null;

// ================= LANDING PAGE HANDLERS =================

function quickFill(url) {
    const input = document.getElementById("repo-url-input");
    if (input) {
        input.value = url;
        input.focus();
    }
}

function dismissError() {
    const banner = document.getElementById("error-banner");
    if (banner) banner.classList.add("hidden");
}

function showError(msg) {
    const banner = document.getElementById("error-banner");
    const text = document.getElementById("error-message");
    if (banner && text) {
        text.innerText = msg;
        banner.classList.remove("hidden");
    } else {
        alert(msg);
    }
}

function animateLoadingSteps() {
    const stepIds = ["step-repo", "step-ast", "step-bugs", "step-review", "step-docs", "step-opt"];
    let currentStep = 0;

    const interval = setInterval(() => {
        if (currentStep < stepIds.length) {
            const el = document.getElementById(stepIds[currentStep]);
            if (el) {
                el.classList.add("active");
                if (currentStep > 0) {
                    const prev = document.getElementById(stepIds[currentStep - 1]);
                    if (prev) {
                        prev.classList.remove("active");
                        prev.classList.add("done");
                    }
                }
            }
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 1200);

    return interval;
}

async function handleAnalyzeSubmit(event) {
    if (event) event.preventDefault();
    dismissError();

    const input = document.getElementById("repo-url-input");
    const repoUrl = input ? input.value.trim() : "";

    if (!repoUrl) {
        showError("Please enter a valid GitHub repository URL.");
        return;
    }

    const loader = document.getElementById("loading-container");
    const btn = document.getElementById("analyze-btn");
    if (loader) loader.classList.remove("hidden");
    if (btn) btn.disabled = true;

    const timer = animateLoadingSteps();

    try {
        const resp = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repo_url: repoUrl })
        });

        const resData = await resp.json();
        clearInterval(timer);

        if (!resp.ok || resData.error) {
            if (loader) loader.classList.add("hidden");
            if (btn) btn.disabled = false;
            showError(resData.error || "Analysis failed. Please verify URL or network access.");
            return;
        }

        sessionStorage.setItem("lastAnalysisData", JSON.stringify(resData.data));
        sessionStorage.setItem("lastAnalysisId", resData.analysis_id);
        window.location.href = `/dashboard?id=${resData.analysis_id}`;

    } catch (err) {
        clearInterval(timer);
        if (loader) loader.classList.add("hidden");
        if (btn) btn.disabled = false;
        showError("Network error connecting to analysis server: " + err.message);
    }
}

async function runSampleDemo() {
    dismissError();
    const loader = document.getElementById("loading-container");
    const btn = document.getElementById("analyze-btn");
    if (loader) loader.classList.remove("hidden");
    if (btn) btn.disabled = true;

    const timer = animateLoadingSteps();

    try {
        const resp = await fetch("/api/analyze-sample", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        const resData = await resp.json();
        clearInterval(timer);

        if (!resp.ok || resData.error) {
            if (loader) loader.classList.add("hidden");
            if (btn) btn.disabled = false;
            showError(resData.error || "Sample analysis failed.");
            return;
        }

        sessionStorage.setItem("lastAnalysisData", JSON.stringify(resData.data));
        sessionStorage.setItem("lastAnalysisId", resData.analysis_id);
        window.location.href = `/dashboard?id=${resData.analysis_id}`;

    } catch (err) {
        clearInterval(timer);
        if (loader) loader.classList.add("hidden");
        if (btn) btn.disabled = false;
        showError("Failed launching sample analysis: " + err.message);
    }
}

// ================= DASHBOARD INITIALIZATION =================

document.addEventListener("DOMContentLoaded", () => {
    if (document.body.classList.contains("dashboard-page")) {
        initDashboard();
    }
});

async function initDashboard() {
    const urlParams = new URLSearchParams(window.location.search);
    const analysisId = urlParams.get("id");

    if (analysisId) {
        currentAnalysisId = analysisId;
        // Try fetching from server
        try {
            const resp = await fetch(`/api/results/${analysisId}`);
            if (resp.ok) {
                const res = await resp.json();
                renderDashboard(res.data, analysisId);
                return;
            }
        } catch (e) {
            console.warn("Could not fetch remote result, checking session storage", e);
        }
    }

    // Fallback to session storage
    const cached = sessionStorage.getItem("lastAnalysisData");
    const cachedId = sessionStorage.getItem("lastAnalysisId");
    if (cached) {
        currentAnalysisId = cachedId || "sample-repo";
        renderDashboard(JSON.parse(cached), currentAnalysisId);
    } else {
        // Automatically run sample repo if empty
        runSampleDemo();
    }
}

function renderDashboard(data, analysisId) {
    currentAnalysisData = data;
    currentAnalysisId = analysisId;

    const repo = data.repository_analysis || {};
    const understanding = data.code_understanding || {};
    const bugs = data.bug_detection || {};
    const review = data.code_review || {};
    const docs = data.documentation || {};
    const improvements = data.code_improvement || {};

    allFilesCache = repo.files || [];
    allBugsCache = bugs.issues || [];

    // Header info
    document.getElementById("repo-title-header").innerText = data.repo_name || "Repository Analysis";
    document.getElementById("repo-type-tag").innerText = repo.project_type || "Software Project";

    // Top counters
    document.getElementById("stat-files").innerText = (repo.total_files || 0).toLocaleString();
    document.getElementById("stat-folders").innerText = `${repo.total_folders || 0} Folders`;
    document.getElementById("stat-loc").innerText = (repo.total_lines || 0).toLocaleString();
    document.getElementById("stat-sloc").innerText = `${(repo.total_code_lines || 0).toLocaleString()} Code Lines`;
    document.getElementById("stat-issues").innerText = (bugs.total_issues || 0).toLocaleString();
    document.getElementById("stat-critical-count").innerText = `${bugs.severity_counts?.CRITICAL || 0} Critical`;

    const totalSymbols = (understanding.total_classes_found || 0) + (understanding.total_functions_found || 0);
    document.getElementById("stat-functions").innerText = totalSymbols.toLocaleString();
    document.getElementById("stat-doc-coverage").innerText = `${review.docstring_coverage_pct || 0}% Documented`;

    // Sidebar Health Grade
    const gradeLetter = (review.maintainability_grade || "A").substring(0, 1);
    const gradeEl = document.getElementById("grade-display");
    gradeEl.innerText = gradeLetter;
    if (gradeLetter === "A") gradeEl.style.background = "#10b981";
    else if (gradeLetter === "B") gradeEl.style.background = "#3b82f6";
    else if (gradeLetter === "C") gradeEl.style.background = "#f59e0b";
    else gradeEl.style.background = "#ef4444";

    document.getElementById("quality-score-text").innerText = `${review.quality_score || 0} / 100`;
    document.getElementById("bug-count-badge").innerText = bugs.total_issues || 0;
    document.getElementById("review-grade-badge").innerText = gradeLetter;
    document.getElementById("imp-count-badge").innerText = improvements.total_improvements || 0;

    // Filter counts for bugs
    document.getElementById("filter-all-cnt").innerText = bugs.total_issues || 0;
    document.getElementById("filter-crit-cnt").innerText = bugs.severity_counts?.CRITICAL || 0;
    document.getElementById("filter-high-cnt").innerText = bugs.severity_counts?.HIGH || 0;
    document.getElementById("filter-med-cnt").innerText = bugs.severity_counts?.MEDIUM || 0;
    document.getElementById("filter-low-cnt").innerText = bugs.severity_counts?.LOW || 0;

    // Render 3 Charts
    renderCharts(repo, bugs);

    // Tab 1: Overview
    renderOverview(repo, understanding);

    // Tab 2: Repo Tree & Files
    renderRepoTree(repo);

    // Tab 3: Code Understanding
    renderUnderstanding(understanding);

    // Tab 4: Bug Detection
    renderBugs(allBugsCache);

    // Tab 5: Code Review
    renderReview(review);

    // Tab 6: Generated Docs
    document.getElementById("readme-preview-content").innerText = docs.readme_markdown || "# Documentation Unavailable";

    // Tab 7: Improvements
    renderImprovements(improvements);
}

// ================= CHARTS =================

function renderCharts(repo, bugs) {
    // 1. Connected Line Chart: Top Files by LOC
    const topFiles = (repo.largest_files || []).slice(0, 8);
    const lineLabels = topFiles.map(f => f.name.length > 14 ? f.name.slice(0, 12) + "..." : f.name);
    const lineData = topFiles.map(f => f.lines);

    const ctxLine = document.getElementById("lineChartLOC").getContext("2d");
    if (locLineChart) locLineChart.destroy();
    locLineChart = new Chart(ctxLine, {
        type: "line",
        data: {
            labels: lineLabels,
            datasets: [{
                label: "Lines of Code (LOC)",
                data: lineData,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59, 130, 246, 0.15)",
                fill: true,
                tension: 0.35,
                pointBackgroundColor: "#60a5fa",
                pointBorderColor: "#ffffff",
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#94a3b8", font: { size: 10 } }
                },
                y: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#94a3b8" }
                }
            }
        }
    });

    // 2. Bug Severity Doughnut / Pie Chart
    const counts = bugs.severity_counts || { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    const ctxPie = document.getElementById("pieChartBugs").getContext("2d");
    if (bugPieChart) bugPieChart.destroy();
    bugPieChart = new Chart(ctxPie, {
        type: "doughnut",
        data: {
            labels: ["Critical", "High", "Medium", "Low"],
            datasets: [{
                data: [counts.CRITICAL || 0, counts.HIGH || 0, counts.MEDIUM || 0, counts.LOW || 0],
                backgroundColor: ["#ef4444", "#ea580c", "#f59e0b", "#3b82f6"],
                borderColor: "#111827",
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: { color: "#cbd5e1", font: { size: 11 }, boxWidth: 12 }
                }
            }
        }
    });

    // 3. File Type & Language Bar Chart
    const languages = (repo.languages || []).slice(0, 6);
    const barLabels = languages.map(l => l.language);
    const barData = languages.map(l => l.lines);

    const ctxBar = document.getElementById("barChartLanguages").getContext("2d");
    if (langBarChart) langBarChart.destroy();
    langBarChart = new Chart(ctxBar, {
        type: "bar",
        data: {
            labels: barLabels,
            datasets: [{
                label: "Lines",
                data: barData,
                backgroundColor: [
                    "#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ec4899", "#06b6d4"
                ],
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "#94a3b8", font: { size: 10 } }
                },
                y: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#94a3b8" }
                }
            }
        }
    });
}

// ================= TAB RENDERING =================

function renderOverview(repo, understanding) {
    const arch = understanding.architecture_overview || {};
    const archSummary = arch.summary || "Identified modular application structure.";
    document.getElementById("overview-arch-text").innerText = archSummary;

    // Config tags
    const tagsContainer = document.getElementById("config-markers-tags");
    tagsContainer.innerHTML = "";
    (repo.config_markers || []).forEach(marker => {
        const span = document.createElement("span");
        span.className = "tech-tag";
        span.innerText = `⚙️ ${marker}`;
        tagsContainer.appendChild(span);
    });

    // Largest files table
    const tbody = document.getElementById("largest-files-tbody");
    tbody.innerHTML = "";
    (repo.largest_files || []).forEach(f => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><code>${f.path}</code></td>
            <td><span class="tech-tag">${f.language}</span></td>
            <td><strong>${f.lines.toLocaleString()}</strong></td>
            <td><button class="btn btn-outline-sm" onclick="inspectFile('${f.path}')">Inspect</button></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderRepoTree(repo) {
    document.getElementById("file-catalog-count").innerText = (repo.files || []).length;
    const treeRoot = document.getElementById("tree-view-root");
    treeRoot.innerHTML = "";

    function buildNodeHtml(node) {
        const ul = document.createElement("ul");
        if (node.children) {
            node.children.forEach(child => {
                const li = document.createElement("li");
                li.className = "tree-item";
                if (child.type === "folder") {
                    li.innerHTML = `<span class="tree-folder">📁 ${child.name}/</span>`;
                    li.appendChild(buildNodeHtml(child));
                } else {
                    li.innerHTML = `<span class="tree-file" onclick="inspectFile('${child.path}')">📄 ${child.name} <small>(${child.lines} LOC)</small></span>`;
                }
                ul.appendChild(li);
            });
        }
        return ul;
    }

    if (repo.file_tree) {
        treeRoot.appendChild(buildNodeHtml(repo.file_tree));
    }

    // Populate all files table
    populateFilesTable(allFilesCache);
}

function populateFilesTable(files) {
    const tbody = document.getElementById("all-files-tbody");
    tbody.innerHTML = "";
    files.forEach(f => {
        const sizeKb = (f.size_bytes / 1024).toFixed(1);
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><code>${f.path}</code></td>
            <td><span class="tech-tag">${f.language}</span></td>
            <td>${sizeKb} KB</td>
            <td>${f.lines}</td>
            <td><button class="btn btn-outline-sm" onclick="inspectFile('${f.path}')">View</button></td>
        `;
        tbody.appendChild(tr);
    });
}

function filterFileList() {
    const query = document.getElementById("file-search-input").value.toLowerCase();
    const filtered = allFilesCache.filter(f => f.path.toLowerCase().includes(query) || f.name.toLowerCase().includes(query));
    populateFilesTable(filtered);
}

function renderUnderstanding(understanding) {
    const summariesList = document.getElementById("file-summaries-list");
    summariesList.innerHTML = "";

    (understanding.files || []).forEach(f => {
        const div = document.createElement("div");
        div.className = "stacked-item";
        div.innerHTML = `
            <div class="stacked-title">
                <span>📄 <code>${f.path}</code></span>
                <span class="tech-tag">${f.language}</span>
            </div>
            <p class="stacked-desc">${f.summary || "Source code module."}</p>
        `;
        summariesList.appendChild(div);
    });

    renderASTSymbols("all", understanding);
}

function renderASTSymbols(filter, understandingData) {
    const data = understandingData || currentAnalysisData?.code_understanding || {};
    const container = document.getElementById("ast-symbols-list");
    container.innerHTML = "";

    const items = [];
    if (filter === "all" || filter === "classes") {
        (data.classes || []).forEach(c => items.push({ type: "Class", ...c }));
    }
    if (filter === "all" || filter === "functions") {
        (data.functions || []).forEach(fn => items.push({ type: "Function", ...fn }));
    }

    if (items.length === 0) {
        container.innerHTML = "<p class='subtitle-text'>No AST symbols matching criteria.</p>";
        return;
    }

    items.forEach(item => {
        const isClass = item.type === "Class";
        const icon = isClass ? "🏛️" : "⚡";
        const argsText = item.args ? `(${item.args.join(", ")})` : "";
        const div = document.createElement("div");
        div.className = "stacked-item";
        div.innerHTML = `
            <div class="stacked-title">
                <span>${icon} <strong>${item.name}</strong>${argsText}</span>
                <span class="badge-tag">${item.file}:L${item.line}</span>
            </div>
            <p class="stacked-desc">${item.explanation || "Executable code routine."}</p>
        `;
        container.appendChild(div);
    });
}

function filterAST(type, btn) {
    document.querySelectorAll("#tab-understanding .filter-pill").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    renderASTSymbols(type);
}

function renderBugs(bugs) {
    const container = document.getElementById("bugs-list-container");
    container.innerHTML = "";

    if (bugs.length === 0) {
        container.innerHTML = "<div class='pane-card'><p>🎉 Zero security vulnerabilities or anti-patterns detected!</p></div>";
        return;
    }

    bugs.forEach(b => {
        const card = document.createElement("div");
        card.className = `issue-card ${b.severity}`;
        card.innerHTML = `
            <div class="issue-top">
                <span class="severity-pill ${b.severity}">${b.severity}</span>
                <span class="issue-location" onclick="inspectFile('${b.file}')" style="cursor:pointer;" title="Click to view file">
                    📄 ${b.file}:${b.line} ↗
                </span>
            </div>
            <h4 class="issue-title">${b.title}</h4>
            <p class="issue-desc">${b.description}</p>
            ${b.code_snippet ? `<pre class="code-snippet-box"><code>${escapeHtml(b.code_snippet)}</code></pre>` : ""}
            <div class="remediation-box">
                <strong>💡 Remediation:</strong> ${b.recommendation}
            </div>
        `;
        container.appendChild(card);
    });
}

function filterBugs(severity, btn) {
    document.querySelectorAll("#tab-bugs .filter-pill").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");

    if (severity === "ALL") {
        renderBugs(allBugsCache);
    } else {
        const filtered = allBugsCache.filter(b => b.severity === severity);
        renderBugs(filtered);
    }
}

function renderReview(review) {
    // Complex functions
    const compContainer = document.getElementById("complex-functions-list");
    compContainer.innerHTML = "";
    (review.complex_functions || []).forEach(cf => {
        const div = document.createElement("div");
        div.className = "stacked-item";
        div.innerHTML = `
            <div class="stacked-title">
                <span><code>${cf.function}()</code></span>
                <span class="badge-tag red">Complexity: ${cf.complexity}</span>
            </div>
            <p class="stacked-desc">${cf.recommendation}</p>
        `;
        compContainer.appendChild(div);
    });

    if (!review.complex_functions?.length) {
        compContainer.innerHTML = "<p class='subtitle-text'>No functions exceeded cyclomatic complexity threshold of 10.</p>";
    }

    // Duplicates
    const dupContainer = document.getElementById("duplicate-blocks-list");
    dupContainer.innerHTML = "";
    (review.duplicate_blocks || []).forEach(dp => {
        const div = document.createElement("div");
        div.className = "stacked-item";
        div.innerHTML = `
            <div class="stacked-title">
                <span><code>${dp.file_a}:L${dp.line_a}</code> ↔ <code>${dp.file_b}:L${dp.line_b}</code></span>
                <span class="badge-tag amber">${dp.lines_count} Lines</span>
            </div>
            <p class="stacked-desc">${dp.description} ${dp.suggestion}</p>
        `;
        dupContainer.appendChild(div);
    });

    if (!review.duplicate_blocks?.length) {
        dupContainer.innerHTML = "<p class='subtitle-text'>No duplicate code sequences found across files.</p>";
    }

    // Suggestions
    const suggContainer = document.getElementById("review-suggestions-list");
    suggContainer.innerHTML = "";
    (review.review_suggestions || []).forEach(s => {
        const div = document.createElement("div");
        div.className = "issue-card LOW";
        div.innerHTML = `
            <div class="issue-top">
                <span class="severity-pill LOW">${s.category || "Review"}</span>
                <span class="issue-location"><code>${s.file}:${s.line}</code></span>
            </div>
            <h4 class="issue-title">${s.title}</h4>
            <p class="issue-desc">${s.suggestion}</p>
        `;
        suggContainer.appendChild(div);
    });
}

function renderImprovements(improvements) {
    const container = document.getElementById("improvements-list-container");
    container.innerHTML = "";

    const list = improvements.improvements || [];
    if (list.length === 0) {
        container.innerHTML = "<div class='pane-card'><p>Codebase adheres to current idiomatic standards.</p></div>";
        return;
    }

    list.forEach(item => {
        const card = document.createElement("div");
        card.className = "diff-card";
        card.innerHTML = `
            <div class="diff-header">
                <div>
                    <span class="badge-tag">${item.category}</span>
                    <span class="issue-location" style="margin-left:8px;"><code>${item.file}:L${item.line}</code></span>
                </div>
                <span class="tech-tag" style="color:#34d399;">⚡ ${item.impact || "Optimization"}</span>
            </div>
            <h3 style="margin-bottom:6px;">${item.title}</h3>
            <p class="subtitle-text">${item.explanation}</p>
            <div class="diff-grid">
                <div class="diff-box before">
                    <div class="diff-box-title">Existing Pattern</div>
                    <pre class="diff-pre"><code>${escapeHtml(item.before || "")}</code></pre>
                </div>
                <div class="diff-box after">
                    <div class="diff-box-title">Improved / Optimized</div>
                    <pre class="diff-pre"><code>${escapeHtml(item.after || "")}</code></pre>
                </div>
            </div>
            <div class="remediation-box" style="margin-top:14px;">
                <strong>🚀 Expected Gain:</strong> ${item.benefit || "Improved performance and readability"}
            </div>
        `;
        container.appendChild(card);
    });
}

// ================= FILE INSPECTOR MODAL =================

async function inspectFile(filePath) {
    if (!currentAnalysisId) return;

    try {
        const resp = await fetch(`/api/file-content?analysis_id=${encodeURIComponent(currentAnalysisId)}&path=${encodeURIComponent(filePath)}`);
        if (!resp.ok) {
            alert("Could not load file contents.");
            return;
        }

        const fileData = await resp.json();
        document.getElementById("modal-filename").innerText = fileData.name;
        document.getElementById("modal-filepath").innerText = fileData.path;

        const linesContainer = document.getElementById("modal-code-lines");
        linesContainer.innerHTML = "";

        const lines = fileData.content.split("\n");
        lines.forEach((lineText, idx) => {
            const lineNo = idx + 1;
            const row = document.createElement("div");
            row.className = "code-line-row";
            row.id = `code-line-${lineNo}`;
            row.innerHTML = `
                <span class="line-num">${lineNo}</span>
                <span class="line-code">${escapeHtml(lineText || " ")}</span>
            `;
            linesContainer.appendChild(row);
        });

        document.getElementById("code-modal").classList.remove("hidden");
    } catch (e) {
        alert("Failed retrieving file content: " + e.message);
    }
}

function closeCodeModal() {
    document.getElementById("code-modal").classList.add("hidden");
}

// Close modal on escape key
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeCodeModal();
});

// ================= EXPORTS & TABS =================

function switchTab(tabId, btn) {
    document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));
    document.querySelectorAll(".sidebar-menu .menu-item").forEach(item => item.classList.remove("active"));

    const targetPane = document.getElementById(tabId);
    if (targetPane) targetPane.classList.add("active");
    if (btn) btn.classList.add("active");
}

function copyReadmeText() {
    const text = document.getElementById("readme-preview-content").innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert("README.md copied to clipboard!");
    });
}

function exportMarkdownDoc() {
    if (currentAnalysisId) {
        window.location.href = `/api/export-docs/${currentAnalysisId}`;
    }
}

function exportJsonReport() {
    if (currentAnalysisId) {
        window.location.href = `/api/export-json/${currentAnalysisId}`;
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
\n`\n\n---\n\n### File: sample_repo/requirements.txt\n\n`text\nflask==3.0.0
requests==2.31.0
pytest>=7.0.0
\n`\n\n---\n\n### File: sample_repo/app.py\n\n`python\n"""
Main Flask REST API server for Demo Store.
"""
from flask import Flask, jsonify, request
from models import User, Product
from auth import AuthService
from services.payment_service import PaymentProcessor
import utils

app = Flask(__name__)
auth_service = AuthService()
payment_service = PaymentProcessor()

@app.route("/health", methods=["GET"])
def health_check():
    """Service health probe."""
    return jsonify({"status": "healthy", "service": "store-api"})

@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate user credentials and issue session."""
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    token = "auth_tok_" + username
    auth_service.active_sessions[token] = 1700000000
    return jsonify({"token": token, "username": username})

@app.route("/api/products", methods=["GET"])
def list_products():
    """Return catalog of available merchandise."""
    p1 = Product(1, "Laptop Stand", 45.0, 15)
    p2 = Product(2, "Mechanical Keyboard", 120.0, 8)
    return jsonify({
        "products": [
            {"id": p1.product_id, "title": p1.title, "price": p1.price, "in_stock": p1.is_in_stock()},
            {"id": p2.product_id, "title": p2.title, "price": p2.price, "in_stock": p2.is_in_stock()}
        ]
    })

if __name__ == "__main__":
    app.run(port=5001, debug=True)
\n`\n\n---\n\n### File: sample_repo/auth.py\n\n`python\nimport hashlib
import time

# Security Risk: Hardcoded secret key
JWT_SECRET_KEY = "super_secret_production_key_12345"
API_KEY = "AKIA1234567890EXAMPLE"

class AuthService:
    """Manages user authentication, token issuance, and password verification."""

    def __init__(self):
        self.active_sessions = {}

    def hash_password(self, password: str) -> str:
        """Hash cleartext password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_token(self, token: str):
        """Verify token validity."""
        # Anti-pattern: == None comparison
        if token == None:
            return False

        try:
            timestamp = self.active_sessions.get(token)
            # Magic number 3600
            if timestamp and (time.time() - timestamp) < 3600:
                return True
        except:
            # Bug: Bare except clause suppresses exceptions
            pass
        return False
\n`\n\n---\n\n### File: sample_repo/models.py\n\n`python\n"""
Database Models for Ecommerce Demo Application.
"""

class User:
    """Represents an application user account with permissions and profile."""
    def __init__(self, user_id: int, username: str, email: str, role: str = "customer"):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role

    def get_display_name(self) -> str:
        """Return formatted display name."""
        return f"{self.username} ({self.role})"

    def is_admin(self) -> bool:
        """Check if user has administrative rights."""
        return self.role == "admin"


class Product:
    """Represents a store catalog inventory item."""
    def __init__(self, product_id: int, title: str, price: float, stock_quantity: int):
        self.product_id = product_id
        self.title = title
        self.price = price
        self.stock_quantity = stock_quantity

    def is_in_stock(self) -> bool:
        """Check inventory availability."""
        return self.stock_quantity > 0

    def deduct_inventory(self, quantity: int) -> bool:
        """Deduct purchased units from inventory."""
        if quantity <= self.stock_quantity:
            self.stock_quantity -= quantity
            return True
        return False
\n`\n\n---\n\n### File: sample_repo/utils.py\n\n`python\nimport math
import os
import sys  # Code smell: Unused import

def calculate_tax(amount: float, tax_rate: float) -> float:
    """Calculate tax for transaction."""
    if amount < 0:
        return 0.0
    subtotal = amount * (1.0 + tax_rate)
    tax_value = round(subtotal - amount, 2)
    return tax_value

def calculate_invoice_tax(amount: float, tax_rate: float) -> float:
    """Duplicate code pattern matching calculate_tax."""
    if amount < 0:
        return 0.0
    subtotal = amount * (1.0 + tax_rate)
    tax_value = round(subtotal - amount, 2)
    return tax_value

def filter_positive_numbers(numbers):
    """Performance optimization opportunity: loop append vs comprehension."""
    positive_nums = []
    for num in numbers:
        if num > 0:
            positive_nums.append(num)
    return positive_nums

def format_receipt_string(user_name, total_cost):
    """Legacy % string formatting."""
    return "User: %s purchased items totaling: $%s" % (user_name, total_cost)
\n`\n\n---\n\n### File: sample_repo/services/payment_service.py\n\n`python\n"""
Payment Processing Service Module.
"""
import sqlite3

class PaymentProcessor:
    """Handles credit card authorization, ledger updates, and batch settlements."""

    def __init__(self, db_path: str = "store.db"):
        self.db_path = db_path

    # Bug: Mutable default argument batch_items=[]
    def process_batch(self, customer_id: int, batch_items: list = []):
        """Process multiple transactions in a batch."""
        total = 0.0
        for item in batch_items:
            total += item.get("amount", 0)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Bug: SQL Injection vector with f-string formatting
        cursor.execute(f"SELECT balance FROM accounts WHERE customer_id = '{customer_id}'")
        row = cursor.fetchone()

        if row:
            current_balance = row[0]
            if current_balance >= total:
                # Deduct
                cursor.execute(f"UPDATE accounts SET balance = balance - {total} WHERE customer_id = '{customer_id}'")
                conn.commit()
                conn.close()
                return True
        conn.close()
        return False
\n`\n\n---\n\n### File: sample_repo/static/main.js\n\n`javascript\n// Frontend client interactions
var userSessionToken = "xyz-789";

function updateCartDisplay(cartItems) {
    var cartContainer = document.getElementById("cart-summary");
    if (!cartContainer) return;

    var total = 0;
    for (var i = 0; i < cartItems.length; i++) {
        total += cartItems[i].price;
    }

    // Code smell: loose equality check
    if (total == 0) {
        // Bug: innerHTML XSS risk
        cartContainer.innerHTML = "<p>Your shopping cart is currently empty.</p>";
        return;
    }

    cartContainer.innerHTML = "<h4>Total: $" + total + "</h4>";
}

function handleCheckout(userId) {
    if (userId == "") {
        console.log("No user ID provided");
        return;
    }
    fetch("/api/checkout", {
        method: "POST",
        body: JSON.stringify({ user_id: userId })
    });
}
\n`\n\n---\n\n### File: README.md\n\n`markdown\n# CODEBASE COPILOT – AI FOR GITHUB REPOSITORIES

**Codebase Copilot** is a full-stack, automated multi-agent code analysis platform designed to inspect, understand, audit, review, document, and optimize public GitHub repositories and local software projects.

It operates with **zero paid AI APIs or external API keys** by employing transparent, deterministic Abstract Syntax Tree (AST) parsing, token pattern heuristics, and static code metrics.

---

## 🌟 Key Features

1. **Home Landing Page**
   - Clean, modern, developer-centric interface.
   - GitHub repository URL input (supports `https://github.com/owner/repo`, `.git`, or shorthand `owner/repo`).
   - Built-in 1-Click Instant Demo Repository (test offline with no external network latency or GitHub rate limits).
   - Animated multi-agent progress stepper during scans.

2. **6 Specialized Analysis Agents**
   - 📁 **Repository Analysis Agent (`repository_agent.py`)**: Catalogs folders, files, lines of code (SLOC, blank, comments), file tree hierarchy, largest files, and programming language distributions.
   - 🧠 **Code Understanding Agent (`code_understanding_agent.py`)**: Uses Python's standard `ast` module and regex grammar to extract classes, functions, arguments, docstrings, imports, and synthesize plain-English summaries and architecture flow.
   - 🐛 **Bug Detection Agent (`bug_detection_agent.py`)**: Flags syntax errors, SQL injection vectors, hardcoded secrets/passwords/API keys, bare `except:` clauses, mutable default arguments, resource leaks, and unsafe DOM manipulations with line numbers and remediation tips.
   - 🔍 **Code Review Agent (`code_review_agent.py`)**: Computes cyclomatic complexity (> 10), detects duplicate code blocks across files, flags unused imports, checks docstring coverage, and computes a Maintainability Grade (A–F) and 0–100 Quality Score.
   - 📖 **Documentation Generation Agent (`documentation_agent.py`)**: Synthesizes project overviews, Mermaid architecture diagrams, installation guides, component references, and a full, exportable `README.md`.
   - ⚡ **Code Improvement Agent (`improvement_agent.py`)**: Formulates concrete Before & After refactoring cards for performance gains (e.g., list comprehensions, generator expressions, $O(1)$ set lookups, f-strings, and CI/CD hygiene).

3. **Analysis Dashboard & Charts**
   - **4 Live Metric Counters**: Total Files, Lines of Code, Issues Found, Functions & Classes.
   - **3 Interactive Chart.js Visualizations**:
     - 📈 **Connected Line Graph**: Code volume distribution across top files.
     - 🎯 **Bug Severity Doughnut Chart**: Critical, High, Medium, and Low severity breakdowns.
     - 📊 **Language Distribution Bar Chart**: Code lines across programming languages.
   - **Interactive File Tree & Code Inspector**: View source files with line numbers and inspect issues.
   - **One-Click Exports**: Download generated `README.md` and download full JSON audit reports.

---

## 🛡️ Security & Technical Safety

- **Safe Extraction**: Prevents directory traversal ("Zip Slip") by checking canonical path boundaries.
- **Strict Size Limits**: Restricts repository archive downloads to 25 MB max to prevent memory bloat or zip bombs.
- **No Code Execution**: Pure static analysis and AST parsing. Downloaded source code is never executed.
- **Graceful Error Handling**: Validates URLs, handles 404s, private repositories, and rate limits with user-friendly notices.

---

## 📁 Project Structure

```
codebase-copilot/
├── app.py                         # Flask server, routes, and GitHub repo manager
├── agents/                        # 6 Specialized Analysis Agents
│   ├── __init__.py
│   ├── repository_agent.py        # Agent 1: Repository Scanner & Tree Builder
│   ├── code_understanding_agent.py# Agent 2: AST Parser & Symbol Explainer
│   ├── bug_detection_agent.py     # Agent 3: Static Bug & Security Detector
│   ├── code_review_agent.py       # Agent 4: Complexity, Duplicates & Reviewer
│   ├── documentation_agent.py     # Agent 5: Markdown & Mermaid Doc Generator
│   └── improvement_agent.py       # Agent 6: Optimization & Modernization Plan
├── templates/
│   ├── index.html                 # Landing page & repository submission UI
│   └── dashboard.html             # Multi-tab dashboard with Chart.js charts
├── static/
│   ├── css/
│   │   └── style.css              # Custom modern dark-mode stylesheet
│   └── js/
│       └── script.js              # Client logic, Chart.js, tabs, and inspector
├── sample_repo/                   # Realistic test repository for instant testing
│   ├── app.py
│   ├── auth.py
│   ├── models.py
│   ├── utils.py
│   ├── services/
│   │   └── payment_service.py
│   ├── static/
│   │   └── main.js
│   └── requirements.txt
├── requirements.txt               # Backend dependencies (Flask, requests)
└── README.md                      # Documentation and run instructions
```

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- Python 3.9+ (tested on Python 3.14)
- Web browser (Chrome, Edge, Firefox, Safari)

### 2. Install Dependencies
Open your terminal in the `codebase-copilot` folder:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the Flask development server:
```bash
python app.py
```
By default, the server runs on:
👉 **`http://localhost:5000`**

---

## 🎬 How to Demonstrate the Project

1. **Open the App in your Browser**: Navigate to `http://localhost:5000`.
2. **Instant Demo**:
   - Click the **"✨ Built-in Demo Store (Instant)"** button on the home page.
   - Observe the 6-agent loading animation as each agent runs.
   - The dashboard opens automatically displaying real metrics, graphs, and audit results!
3. **Analyze a Public GitHub Repository**:
   - Enter any public repository such as `https://github.com/pallets/flask` or `psf/requests` and click **Analyze Repository**.
4. **Explore the Dashboard**:
   - **Charts**: View the Connected Line Graph of file lines, the Bug Severity Doughnut, and Language breakdown bar chart.
   - **Repository Tree**: Expand folders and click on any file to open the Code Inspector.
   - **Code Understanding**: See plain-English explanations of functions and classes extracted via AST.
   - **Bug Detection**: Filter bugs by Critical, High, Medium, Low. Inspect exact line numbers and remediation recommendations.
   - **Code Review**: Check cyclomatic complexity hotspots and duplicate code blocks.
   - **Generated Docs**: Preview the generated README.md and click "Download README.md".
   - **Improvements**: View Before vs After code diff cards with performance gain explanations.
\n`\n\n---\n\n