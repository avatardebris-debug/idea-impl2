"""Forensic web application."""

import logging
from flask import Flask, render_template, jsonify, request
from forensic.database import ForensicDatabase
from forensic.api import create_api

logger = logging.getLogger("forensic.web")


def create_app(db: ForensicDatabase = None):
    """Create and configure the Flask application."""
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, "templates"), 
                static_folder=os.path.join(base_dir, "static"))
    app.config["SECRET_KEY"] = "forensic-suite-secret-key"

    # Initialize database
    if db is None:
        db = ForensicDatabase()
        db.connect()

    # Register API routes
    create_api(app, db)

    # ---- Web routes ----

    @app.route("/")
    def index():
        """Dashboard home page."""
        summary = db.get_dashboard_summary()
        return render_template("index.html", summary=summary)

    @app.route("/fraud-scores")
    def fraud_scores_page():
        """Fraud scores page."""
        ticker = request.args.get("ticker")
        risk_level = request.args.get("risk_level")
        scores = db.get_fraud_scores(ticker=ticker, risk_level=risk_level, limit=200)
        return render_template("fraud_scores.html", scores=scores, ticker=ticker, risk_level=risk_level)

    @app.route("/red-flags")
    def red_flags_page():
        """Red flags page."""
        ticker = request.args.get("ticker")
        category = request.args.get("category")
        severity = request.args.get("severity")
        flags = db.get_red_flags(ticker=ticker, category=category, severity=severity, limit=500)
        return render_template("red_flags.html", flags=flags, ticker=ticker, category=category, severity=severity)

    @app.route("/capital-flows")
    def capital_flows_page():
        """Capital flows page."""
        ticker = request.args.get("ticker")
        flows = db.get_capital_flows(ticker=ticker, limit=100)
        return render_template("capital_flows.html", flows=flows, ticker=ticker)

    @app.route("/companies")
    def companies_page():
        """Companies page."""
        conn = db._get_conn()
        companies = conn.execute("SELECT * FROM companies ORDER BY ticker").fetchall()
        return render_template("companies.html", companies=[dict(c) for c in companies])

    @app.route("/ticker/<ticker>")
    def ticker_detail(ticker):
        """Detail page for a specific ticker."""
        try:
            scores = db.get_fraud_scores(ticker=ticker, limit=50)
            flags = db.get_red_flags(ticker=ticker, limit=200)
            flows = db.get_capital_flows(ticker=ticker, limit=50)
            company = db.get_company_by_cik(ticker)  # CIK lookup
            return render_template(
                "ticker_detail.html",
                ticker=ticker,
                scores=scores,
                flags=flags,
                flows=flows,
                company=company,
            )
        except Exception as e:
            logger.error(f"Error getting ticker detail for {ticker}: {e}")
            return render_template("ticker_detail.html", ticker=ticker, scores=[], flags=[], flows=[], company=None)

    return app
