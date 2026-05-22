"""Tests for the Email Tool Dashboard."""

import pytest
import os
import tempfile
from pathlib import Path
from datetime import datetime
from email_tool.dashboard.app import Dashboard, get_dashboard, create_app
from email_tool.config import load_config


class TestDashboard:
    """Tests for Dashboard class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.dashboard = Dashboard(base_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init_with_base_path(self):
        """Test initialization with base path."""
        dashboard = Dashboard(base_path=self.temp_dir)
        assert dashboard.base_path == Path(self.temp_dir)
    
    def test_init_without_base_path(self):
        """Test initialization without base path (uses config)."""
        dashboard = Dashboard()
        config = load_config()
        assert dashboard.base_path == Path(config.get_base_path())
    
    def test_get_email_counts_by_category_empty(self):
        """Test getting email counts from empty directory."""
        counts = self.dashboard.get_email_counts_by_category()
        assert counts == {}
    
    def test_get_email_counts_by_category_with_dirs(self):
        """Test getting email counts with category directories."""
        # Create category directories with files
        inbox_dir = Path(self.temp_dir) / "inbox"
        inbox_dir.mkdir()
        (inbox_dir / "email1.eml").touch()
        (inbox_dir / "email2.eml").touch()
        
        work_dir = Path(self.temp_dir) / "work"
        work_dir.mkdir()
        (work_dir / "email3.eml").touch()
        
        counts = self.dashboard.get_email_counts_by_category()
        
        assert counts["inbox"] == 2
        assert counts["work"] == 1
    
    def test_get_total_email_count_empty(self):
        """Test getting total email count from empty directory."""
        total = self.dashboard.get_total_email_count()
        assert total == 0
    
    def test_get_total_email_count_with_files(self):
        """Test getting total email count with files."""
        # Create category directories with files
        inbox_dir = Path(self.temp_dir) / "inbox"
        inbox_dir.mkdir()
        (inbox_dir / "email1.eml").touch()
        (inbox_dir / "email2.eml").touch()
        
        work_dir = Path(self.temp_dir) / "work"
        work_dir.mkdir()
        (work_dir / "email3.eml").touch()
        
        total = self.dashboard.get_total_email_count()
        assert total == 3
    
    def test_get_recent_activity_empty(self):
        """Test getting recent activity from empty directory."""
        activity = self.dashboard.get_recent_activity(limit=10)
        assert activity == []
    
    def test_get_recent_activity_with_files(self):
        """Test getting recent activity with files."""
        # Create files with different modification times
        inbox_dir = Path(self.temp_dir) / "inbox"
        inbox_dir.mkdir()
        
        email1 = inbox_dir / "email1.eml"
        email1.touch()
        
        # Wait a moment to ensure different timestamps
        import time
        time.sleep(0.1)
        
        email2 = inbox_dir / "email2.eml"
        email2.touch()
        
        activity = self.dashboard.get_recent_activity(limit=10)
        
        assert len(activity) == 2
        # Most recent should be first
        assert activity[0]["file"] == "email2.eml"
        assert activity[1]["file"] == "email1.eml"
    
    def test_get_recent_activity_limit(self):
        """Test limiting recent activity."""
        inbox_dir = Path(self.temp_dir) / "inbox"
        inbox_dir.mkdir()
        
        # Create 15 files
        for i in range(15):
            (inbox_dir / f"email{i}.eml").touch()
        
        activity = self.dashboard.get_recent_activity(limit=5)
        
        assert len(activity) == 5
    
    def test_get_rule_match_statistics(self):
        """Test getting rule match statistics."""
        stats = self.dashboard.get_rule_match_statistics()
        
        assert "total_rules" in stats
        assert "active_rules" in stats
        assert "last_match" in stats
        assert "matches_by_rule" in stats
    
    def test_get_system_health_healthy(self):
        """Test getting system health when everything is OK."""
        health = self.dashboard.get_system_health()
        
        assert health["status"] in ["healthy", "ok", "warning"]
        assert "checks" in health
    
    def test_get_system_health_base_path_missing(self):
        """Test getting system health when base path doesn't exist."""
        dashboard = Dashboard(base_path="/nonexistent/path")
        health = dashboard.get_system_health()
        
        assert health["status"] in ["warning", "error"]
        assert "base_path" in health["checks"]
    
    def test_get_statistics(self):
        """Test getting comprehensive statistics."""
        stats = self.dashboard.get_statistics()
        
        assert "email_counts_by_category" in stats
        assert "total_email_count" in stats
        assert "recent_activity" in stats
        assert "rule_match_statistics" in stats
        assert "system_health" in stats
    
    def test_get_statistics_with_data(self):
        """Test getting statistics with actual data."""
        # Create some test data
        inbox_dir = Path(self.temp_dir) / "inbox"
        inbox_dir.mkdir()
        (inbox_dir / "email1.eml").touch()
        
        stats = self.dashboard.get_statistics()
        
        assert stats["total_email_count"] >= 1
        assert "inbox" in stats["email_counts_by_category"]


class TestDashboardSingleton:
    """Tests for dashboard singleton pattern."""
    
    def teardown_method(self):
        """Reset singleton between tests."""
        import email_tool.dashboard.app as app_module
        app_module._dashboard = None
    
    def test_get_dashboard_creates_instance(self):
        """Test that get_dashboard creates a new instance."""
        dashboard = get_dashboard()
        assert isinstance(dashboard, Dashboard)
    
    def test_get_dashboard_returns_same_instance(self):
        """Test that get_dashboard returns the same instance."""
        dashboard1 = get_dashboard()
        dashboard2 = get_dashboard()
        
        assert dashboard1 is dashboard2


class TestFastAPIApp:
    """Tests for FastAPI application creation."""
    
    def teardown_method(self):
        """Reset singleton between tests."""
        import email_tool.dashboard.app as app_module
        app_module._dashboard = None
    
    def test_create_app(self):
        """Test creating FastAPI application."""
        app = create_app()
        
        assert app.title == "Email Tool Dashboard"
        assert app.description == "Web dashboard for monitoring email organization"
        assert app.version == "0.1.0"
    
    def test_app_routes_exist(self):
        """Test that all expected routes exist."""
        app = create_app()
        
        routes = [route.path for route in app.routes]
        
        assert "/" in routes
        assert "/api/stats" in routes
        assert "/api/stats/emails" in routes
        assert "/api/stats/recent" in routes
        assert "/api/stats/health" in routes
        assert "/api/stats/rules" in routes
        assert "/api/health" in routes
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        from fastapi.testclient import TestClient
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_stats_endpoint(self):
        """Test stats endpoint."""
        from fastapi.testclient import TestClient
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "email_counts_by_category" in data
        assert "total_email_count" in data
        assert "recent_activity" in data
        assert "rule_match_statistics" in data
        assert "system_health" in data
    
    def test_email_stats_endpoint(self):
        """Test email stats endpoint."""
        from fastapi.testclient import TestClient
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/api/stats/emails")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "email_counts_by_category" in data
        assert "total_email_count" in data
    
    def test_recent_activity_endpoint(self):
        """Test recent activity endpoint."""
        from fastapi.testclient import TestClient
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/api/stats/recent")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "activity" in data
        assert "limit" in data
    
    def test_rule_stats_endpoint(self):
        """Test rule statistics endpoint."""
        from fastapi.testclient import TestClient
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/api/stats/rules")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_rules" in data
        assert "active_rules" in data
        assert "last_match" in data
        assert "matches_by_rule" in data
    
    def test_health_endpoint_with_invalid_base_path(self):
        """Test health endpoint with invalid base path."""
        from fastapi.testclient import TestClient
        
        # Set up dashboard with invalid path
        import email_tool.dashboard.app as app_module
        app_module._dashboard = Dashboard(base_path="/nonexistent/path")
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/api/stats/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "checks" in data


class TestDashboardWithRealData:
    """Tests with real email data."""
    
    def setup_method(self):
        """Set up test fixtures with real email data."""
        self.temp_dir = tempfile.mkdtemp()
        self.dashboard = Dashboard(base_path=self.temp_dir)
        
        # Create category directories
        (Path(self.temp_dir) / "inbox").mkdir()
        (Path(self.temp_dir) / "work").mkdir()
        (Path(self.temp_dir) / "personal").mkdir()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_get_statistics_with_real_emails(self):
        """Test statistics with real email files."""
        # Create real email files
        inbox_dir = Path(self.temp_dir) / "inbox"
        work_dir = Path(self.temp_dir) / "work"
        personal_dir = Path(self.temp_dir) / "personal"
        
        # Create 5 emails in inbox
        for i in range(5):
            (inbox_dir / f"email_{i}.eml").touch()
        
        # Create 3 emails in work
        for i in range(3):
            (work_dir / f"email_{i}.eml").touch()
        
        # Create 2 emails in personal
        for i in range(2):
            (personal_dir / f"email_{i}.eml").touch()
        
        stats = self.dashboard.get_statistics()
        
        assert stats["total_email_count"] == 10
        assert stats["email_counts_by_category"]["inbox"] == 5
        assert stats["email_counts_by_category"]["work"] == 3
        assert stats["email_counts_by_category"]["personal"] == 2
    
    def test_get_recent_activity_with_real_emails(self):
        """Test recent activity with real email files."""
        inbox_dir = Path(self.temp_dir) / "inbox"
        
        # Create emails with different timestamps
        for i in range(5):
            email_file = inbox_dir / f"email_{i}.eml"
            email_file.touch()
            # Add a small delay to ensure different timestamps
            import time
            time.sleep(0.01)
        
        activity = self.dashboard.get_recent_activity(limit=5)
        
        assert len(activity) == 5
        # Most recent should be first
        assert activity[0]["file"] == "email_4.eml"
        assert activity[1]["file"] == "email_3.eml"
    
    def test_get_email_counts_by_category_with_real_emails(self):
        """Test email counts with real email files."""
        inbox_dir = Path(self.temp_dir) / "inbox"
        work_dir = Path(self.temp_dir) / "work"
        
        # Create emails
        for i in range(10):
            (inbox_dir / f"email_{i}.eml").touch()
        
        for i in range(5):
            (work_dir / f"email_{i}.eml").touch()
        
        counts = self.dashboard.get_email_counts_by_category()
        
        assert counts["inbox"] == 10
        assert counts["work"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
