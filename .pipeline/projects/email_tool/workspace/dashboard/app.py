"""FastAPI web dashboard for Email Tool.

This module provides a web-based dashboard for monitoring email organization
statistics, recent activity, and system health metrics.
"""

import os
import json
import logging
import shutil
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.requests import Request

from email_tool.config import load_config, EmailToolConfig
from email_tool.logging_config import get_logger

logger = get_logger(__name__)


class Dashboard:
    """Dashboard data provider for Email Tool.
    
    Collects and provides statistics about email organization,
    recent activity, and system health.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """Initialize dashboard.
        
        Args:
            base_path: Base path for organized emails. If None, uses config.
        """
        self.base_path = Path(base_path) if base_path else None
        self.config = load_config()
        if not self.base_path:
            self.base_path = Path(self.config.get_base_path())
    
    def get_email_counts_by_category(self) -> Dict[str, int]:
        """Get email counts organized by category.
        
        Returns:
            Dictionary mapping category names to email counts.
        """
        counts: Dict[str, int] = defaultdict(int)
        
        if not self.base_path.exists():
            return counts
        
        for item in self.base_path.iterdir():
            if item.is_dir():
                count = sum(1 for _ in item.glob("*"))
                if count > 0:
                    counts[item.name] = count
        
        return dict(counts)
    
    def get_total_email_count(self) -> int:
        """Get total number of organized emails.
        
        Returns:
            Total email count.
        """
        total = 0
        if self.base_path.exists():
            for item in self.base_path.rglob("*"):
                if item.is_file():
                    total += 1
        return total
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent email processing activity.
        
        Args:
            limit: Maximum number of recent items to return.
        
        Returns:
            List of recent activity entries.
        """
        activity = []
        
        if not self.base_path.exists():
            return activity
        
        # Collect recent files
        files = []
        for item in self.base_path.rglob("*"):
            if item.is_file():
                try:
                    stat = item.stat()
                    files.append({
                        'path': str(item),
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'size': stat.st_size
                    })
                except (OSError, IOError):
                    continue
        
        # Sort by modification time
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        # Format activity entries
        for file_info in files[:limit]:
            activity.append({
                'file': Path(file_info['path']).name,
                'path': file_info['path'],
                'modified': file_info['modified'].isoformat(),
                'size': file_info['size']
            })
        
        return activity
    
    def get_rule_match_statistics(self) -> Dict[str, Any]:
        """Get statistics about rule matches.
        
        Returns:
            Dictionary with rule match statistics.
        """
        # This would typically come from a rules log or database
        # For now, return placeholder data
        return {
            'total_rules': 0,
            'active_rules': 0,
            'last_match': None,
            'matches_by_rule': {}
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics.
        
        Returns:
            Dictionary with system health information.
        """
        health = {
            'status': 'healthy',
            'checks': {}
        }
        
        # Check base path
        if self.base_path.exists():
            health['checks']['base_path'] = {
                'status': 'ok',
                'path': str(self.base_path)
            }
        else:
            health['checks']['base_path'] = {
                'status': 'warning',
                'path': str(self.base_path),
                'message': 'Base path does not exist'
            }
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(str(self.base_path))
            free_gb = free / (1024 ** 3)
            
            health['checks']['disk_space'] = {
                'status': 'ok' if free_gb > 1 else 'warning',
                'total_gb': total / (1024 ** 3),
                'used_gb': used / (1024 ** 3),
                'free_gb': free_gb
            }
        except Exception as e:
            health['checks']['disk_space'] = {
                'status': 'error',
                'message': str(e)
            }
        
        # Check Python version
        health['checks']['python_version'] = {
            'status': 'ok',
            'version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        
        # Overall status
        if any(check['status'] == 'error' for check in health['checks'].values()):
            health['status'] = 'error'
        elif any(check['status'] == 'warning' for check in health['checks'].values()):
            health['status'] = 'warning'
        
        return health
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics.
        
        Returns:
            Dictionary with all statistics.
        """
        return {
            'email_counts_by_category': self.get_email_counts_by_category(),
            'total_email_count': self.get_total_email_count(),
            'recent_activity': self.get_recent_activity(),
            'rule_match_statistics': self.get_rule_match_statistics(),
            'system_health': self.get_system_health()
        }


# Global dashboard instance
_dashboard: Optional[Dashboard] = None


def get_dashboard() -> Dashboard:
    """Get or create dashboard instance."""
    global _dashboard
    if _dashboard is None:
        _dashboard = Dashboard()
    return _dashboard


def create_app() -> FastAPI:
    """Create FastAPI application with dashboard routes.
    
    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="Email Tool Dashboard",
        description="Web dashboard for monitoring email organization",
        version="0.1.0"
    )
    
    # Initialize dashboard
    dashboard = get_dashboard()
    
    # Setup templates
    templates_dir = Path(__file__).parent / "templates"
    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
    else:
        templates = None
    
    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    @app.get("/")
    async def index(request: Request):
        """Render dashboard index page."""
        if templates:
            stats = dashboard.get_statistics()
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "stats": stats}
            )
        else:
            return HTMLResponse(
                content="<h1>Email Tool Dashboard</h1><p>Dashboard templates not found</p>"
            )
    
    @app.get("/api/stats")
    async def get_stats():
        """Get all statistics as JSON."""
        return JSONResponse(content=dashboard.get_statistics())
    
    @app.get("/api/stats/emails")
    async def get_email_stats():
        """Get email statistics."""
        return JSONResponse(content={
            'counts_by_category': dashboard.get_email_counts_by_category(),
            'total_count': dashboard.get_total_email_count()
        })
    
    @app.get("/api/stats/recent")
    async def get_recent(limit: int = 10):
        """Get recent activity."""
        return JSONResponse(content={
            'activity': dashboard.get_recent_activity(limit=limit)
        })
    
    @app.get("/api/stats/health")
    async def get_health():
        """Get system health."""
        return JSONResponse(content=dashboard.get_system_health())
    
    @app.get("/api/stats/rules")
    async def get_rule_stats():
        """Get rule match statistics."""
        return JSONResponse(content=dashboard.get_rule_match_statistics())
    
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "timestamp": datetime.now().isoformat()}
    
    return app


# For direct execution
if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
