"""depvuln — Dependency vulnerability scanner."""
from depvuln.config import ConfigManager
from depvuln.scorer import VulnScorer
from depvuln.remediation import RemediationAdvisor
from depvuln.parsers import NpmParser, PipParser, MavenParser, CargoParser, GoParser, PodfileParser
from depvuln.cve import CveFetcher, NvdFetcher, CveDataMerger, CveCache
from depvuln.reports import JsonReportGenerator, TextReportGenerator, HtmlReportGenerator

__all__ = [
    "ConfigManager",
    "VulnScorer",
    "RemediationAdvisor",
    "NpmParser",
    "PipParser",
    "MavenParser",
    "CargoParser",
    "GoParser",
    "PodfileParser",
    "CveFetcher",
    "NvdFetcher",
    "CveDataMerger",
    "CveCache",
    "JsonReportGenerator",
    "TextReportGenerator",
    "HtmlReportGenerator",
]
