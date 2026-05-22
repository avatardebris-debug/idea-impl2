"""Command-line interface for job automation tool."""

import argparse
import json
import sys
from pathlib import Path

from .profile import Profile
from .parser import parse_job_description
from .matcher import match_profiles


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="job-tool",
        description="Job description parsing and profile matching tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Parse subcommand
    parse_parser = subparsers.add_parser("parse", help="Parse a job description file")
    parse_parser.add_argument("file", nargs="?", type=Path, help="Job description file (or stdin)")
    parse_parser.add_argument(
        "--output", "-o",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)"
    )

    # Match subcommand
    match_parser = subparsers.add_parser("match", help="Match candidate skills against job description")
    match_parser.add_argument("job_file", type=Path, help="Job description file")
    match_parser.add_argument("candidate_file", type=Path, help="Candidate skills file")
    match_parser.add_argument(
        "--output", "-o",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)"
    )

    return parser


def cmd_parse(args: argparse.Namespace) -> int:
    """Handle the parse subcommand."""
    if args.file:
        content = args.file.read_text()
    else:
        content = sys.stdin.read()

    result = parse_job_description(content)
    if result is None:
        print("Error: Failed to parse job description", file=sys.stderr)
        return 1

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Company: {result.get('company', 'N/A')}")
        print(f"Location: {result.get('location', 'N/A')}")
        print(f"Experience Level: {result.get('experience_level', 'N/A')}")
        print(f"Skills: {', '.join(result.get('skills', []))}")
        print(f"Responsibilities: {len(result.get('responsibilities', []))} items")

    return 0


def cmd_match(args: argparse.Namespace) -> int:
    """Handle the match subcommand."""
    job_content = args.job_file.read_text()
    candidate_content = args.candidate_file.read_text()

    job_profile = parse_job_description(job_content)
    if job_profile is None:
        print("Error: Failed to parse job description", file=sys.stderr)
        return 1

    candidate_skills = [s.strip() for s in candidate_content.strip().split("\n") if s.strip()]

    result = match_profiles(candidate_skills, "mid-level", job_profile)

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Match Score: {result['score']}/100")
        print(f"Matched Skills: {', '.join(result['matched_skills'])}")
        print(f"Missing Skills: {', '.join(result['missing_skills'])}")
        print(f"Salary Match: {'Yes' if result['salary_match'] else 'No'}")

    return 0


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "parse":
        return cmd_parse(args)
    elif args.command == "match":
        return cmd_match(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
