/* Codebase Copilot - Frontend Application Logic & Chart.js Integration */

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
