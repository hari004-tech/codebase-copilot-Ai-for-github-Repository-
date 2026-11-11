import os
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

@app.route("/download-project", methods=["GET"])
def download_project_zip():
    """Download the complete project folder packaged as a zip file."""
    zip_path = BASE_DIR.parent / "codebase-copilot.zip"
    if not zip_path.exists():
        # Generate on the fly
        import shutil
        shutil.make_archive(str(BASE_DIR.parent / "codebase-copilot"), "zip", str(BASE_DIR))
    
    return send_file(
        str(zip_path),
        mimetype="application/zip",
        as_attachment=True,
        download_name="codebase-copilot-project.zip"
    )

@app.route("/download-bundle", methods=["GET"])
def download_bundle_file():
    """Download the standalone self-extracting single Python file."""
    bundle_path = BASE_DIR / "codebase_copilot_bundle.py"
    if not bundle_path.exists():
        bundle_path = BASE_DIR.parent / "codebase_copilot_bundle.py"
    
    return send_file(
        str(bundle_path),
        mimetype="text/x-python",
        as_attachment=True,
        download_name="codebase_copilot_bundle.py"
    )

@app.route("/download-architecture", methods=["GET"])
def download_architecture_doc():
    """Download the full source code and architecture in a single markdown document."""
    doc_path = BASE_DIR / "COMPLETE_CODEBASE_ARCHITECTURE.md"
    if not doc_path.exists():
        doc_path = BASE_DIR.parent / "COMPLETE_CODEBASE_ARCHITECTURE.md"

    return send_file(
        str(doc_path),
        mimetype="text/markdown",
        as_attachment=True,
        download_name="COMPLETE_CODEBASE_ARCHITECTURE.md"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Codebase Copilot server starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
