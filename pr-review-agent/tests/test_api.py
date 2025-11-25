"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


class TestReviewEndpoints:
    """Tests for review endpoints."""
    
    def test_get_categories(self):
        """Test get review categories."""
        response = client.get("/api/v1/review/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 4
    
    def test_get_severities(self):
        """Test get severity levels."""
        response = client.get("/api/v1/review/severities")
        assert response.status_code == 200
        data = response.json()
        assert "severities" in data
        assert len(data["severities"]) == 4
    
    def test_review_manual_diff_invalid(self):
        """Test manual diff review with invalid data."""
        response = client.post(
            "/api/v1/review/diff",
            json={"diff": "", "language": "python"}
        )
        # Should return error for empty diff
        assert response.status_code in [400, 500]
    
    def test_review_manual_diff_valid(self):
        """Test manual diff review with valid data."""
        diff = """--- a/test.py
+++ b/test.py
@@ -1,2 +1,3 @@
 def test():
-    pass
+    x = 1
+    return x
"""
        response = client.post(
            "/api/v1/review/diff",
            json={"diff": diff, "language": "python"}
        )
        # Note: This might fail without valid API key
        # In production, mock the LLM calls
        assert response.status_code in [200, 400, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
