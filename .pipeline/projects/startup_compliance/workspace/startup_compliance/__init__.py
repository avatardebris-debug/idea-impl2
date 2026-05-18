"""
startup_compliance — Automated SOC2 and GDPR checklist generator.

Given a brief description of a startup's architecture, data handling, and team size,
this tool uses an LLM to generate a customized, actionable compliance checklist.

Usage:
    python -m startup_compliance generate --name "Acme Corp" --desc "B2B SaaS storing user emails in AWS"
    python -m startup_compliance generate --config company_profile.json
"""
__version__ = "0.1.0"
