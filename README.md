# CODEBASE COPILOT – AI FOR GITHUB REPOSITORIES

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
