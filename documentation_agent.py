import os
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
