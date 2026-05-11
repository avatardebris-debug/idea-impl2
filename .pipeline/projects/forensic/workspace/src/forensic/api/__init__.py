"""Forensic API - REST endpoints for fraud scores, red flags, and capital flows."""

import logging
from flask import Blueprint

logger = logging.getLogger("forensic.api")


def create_api(db):
    """Create and return the API blueprint (does not register it)."""
    api_bp = Blueprint("api", __name__, url_prefix="/api")

    @api_bp.route("/dashboard/summary")
    def dashboard_summary():
        """Get dashboard summary statistics."""
        try:
            summary = db.get_dashboard_summary()
            return jsonify(summary)
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {e}")
            return jsonify({"error": str(e)}), 500

    @api_bp.route("/fraud-scores")
    def get_fraud_scores():
        """Get fraud scores with optional filters."""
        from flask import request, jsonify
        ticker = request.args.get("ticker")
        risk_level = request.args.get("risk_level")
        limit = int(request.args.get("limit", 100))

        try:
            scores = db.get_fraud_scores(ticker=ticker, risk_level=risk_level, limit=limit)
            return jsonify({"scores": scores, "count": len(scores)})
        except Exception as e:
            logger.error(f"Error getting fraud scores: {e}")
            return jsonify({"error": str(e)}), 500

    @api_bp.route("/fraud-scores/<ticker>")
    def get_fraud_score_by_ticker(ticker):
        """Get fraud scores for a specific ticker."""
        from flask import jsonify
        try:
            scores = db.get_fraud_scores(ticker=ticker, limit=50)
            return jsonify({"ticker": ticker, "scores": scores, "count": len(scores)})
        except Exception as e:
            logger.error(f"Error getting fraud scores for {ticker}: {e}")
            return jsonify({"error": str(e)}), 500

    @api_bp.route("/red-flags")
    def get_red_flags():
        """Get red flags with optional filters."""
        from flask import request, jsonify
        ticker = request.args.get("ticker")
        category = request.args.get("category")
        severity = request.args.get("severity")
        limit = int(request.args.get("limit", 500))

        try:
            flags = db.get_red_flags(ticker=ticker, category=category, severity=severity, limit=limit)
            return jsonify({"flags": flags, "count": len(flags)})
        except Exception as e:
            logger.error(f"Error getting red flags: {e}")
            return jsonify({"error": str(e)}), 500

    @api_bp.route("/red-flags/<ticker>")
    def get_red_flags_by_ticker(ticker):
        """Get red flags for a specific ticker."""
        from flask import jsonify
        try:
            flags = db.get_red_flags(ticker=ticker, limit=200)
            return jsonify({"ticker": ticker, "flags": flags, "count": len(flags)})
        except Exception as e:
            logger.error(f"Error getting red flags for {ticker}: {e}")
            return jsonify({"error": str(e)}), 500

    @api_bp.route("/capital-flows")
    def get_capital_flows():
        """Get capital flows with optional filters."""
        from flask import request, jsonify
        ticker = request.args.get("ticker")
        limit = int(request.args.get("limit", 100))

        try:
            flows = db.get_capital_flows(ticker=ticker, limit=limit)
            return jsonify({"flows": flows, "count": len(flows)})
        except Exception as e:
            logger.error(f"Error getting capital flows: {e}")
            return jsonify({"error": str(e)}), 500

    @api_bp.route("/capital-flows/<ticker>")
    def get_capital_flows_by_ticker(ticker):
        """Get capital flows for a specific ticker."""
        from flask import jsonify
        try:
            flows = db.get_capital_flows(ticker=ticker, limit=50)
            return jsonify({"ticker": ticker, "flows": flows, "count": len(flows)})
        except Exception as e:
            logger.error(f"Error getting capital flows for {ticker}: {e}")
            return jsonify({"error": str(e)}), 500

    @api_bp.route("/companies")
    def get_companies():
        """Get list of companies."""
        from flask import jsonify
        try:
            conn = db._get_conn()
            companies = conn.execute("SELECT * FROM companies ORDER BY ticker").fetchall()
            return jsonify({"companies": [dict(c) for c in companies]})
        except Exception as e:
            logger.error(f"Error getting companies: {e}")
            return jsonify({"error": str(e)}), 500

    @api_bp.route("/stats")
    def get_stats():
        """Get overall statistics."""
        from flask import jsonify
        try:
            conn = db._get_conn()
            stats = {
                "total_filings": conn.execute("SELECT COUNT(*) FROM filings").fetchone()[0],
                "total_companies": conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0],
                "total_fraud_scores": conn.execute("SELECT COUNT(*) FROM fraud_scores").fetchone()[0],
                "total_red_flags": conn.execute("SELECT COUNT(*) FROM red_flags").fetchone()[0],
                "total_capital_flows": conn.execute("SELECT COUNT(*) FROM capital_flows").fetchone()[0],
            }
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return jsonify({"error": str(e)}), 500

    return api_bp
