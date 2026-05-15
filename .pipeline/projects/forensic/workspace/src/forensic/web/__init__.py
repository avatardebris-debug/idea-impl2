"""Forensic web application package."""

import os
from flask import Flask, render_template, jsonify
from forensic.api import create_api


def create_app(db=None):
    """Create and configure the Flask application."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    app = Flask(__name__,
                template_folder=os.path.join(parent_dir, "templates"),
                static_folder=os.path.join(parent_dir, "static"))
    app.config["SECRET_KEY"] = "forensic-suite-secret-key"

    if db is not None:
        # Register API blueprint
        api_bp = create_api(db)
        app.register_blueprint(api_bp)

    # --- Web routes ---
    @app.route("/")
    def index():
        """Dashboard index page."""
        summary = db.get_dashboard_summary() if db else {}
        return render_template("index.html", summary=summary)

    @app.route("/companies")
    def companies():
        """Companies list page."""
        companies = db.get_companies() if db else []
        return render_template("companies.html", companies=companies)

    @app.route("/fraud-scores")
    def fraud_scores():
        """Fraud scores page."""
        scores = db.get_fraud_scores() if db else []
        return render_template("fraud_scores.html", scores=scores)

    @app.route("/red-flags")
    def red_flags():
        """Red flags page."""
        flags = db.get_red_flags() if db else []
        return render_template("red_flags.html", flags=flags)

    @app.route("/capital-flows")
    def capital_flows():
        """Capital flows page."""
        flows = db.get_capital_flows() if db else []
        return render_template("capital_flows.html", flows=flows)

    @app.route("/ticker/<ticker>")
    def ticker_detail(ticker):
        """Ticker detail page."""
        return render_template("ticker_detail.html", ticker=ticker)

    @app.route("/company/<ticker>")
    def company_detail(ticker):
        """Company detail page."""
        return render_template("company_detail.html", ticker=ticker)

    return app
