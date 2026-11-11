"""
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
