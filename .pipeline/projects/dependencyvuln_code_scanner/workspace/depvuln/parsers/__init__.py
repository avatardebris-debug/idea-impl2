"""Dependency parsers package."""
from depvuln.parsers.base import DependencyParser
from depvuln.parsers.npm_parser import NpmParser
from depvuln.parsers.pip_parser import PipParser
from depvuln.parsers.maven_parser import MavenParser
from depvuln.parsers.cargo_parser import CargoParser
from depvuln.parsers.go_parser import GoParser
from depvuln.parsers.podfile_parser import PodfileParser

__all__ = [
    "DependencyParser",
    "NpmParser",
    "PipParser",
    "MavenParser",
    "CargoParser",
    "GoParser",
    "PodfileParser",
]
