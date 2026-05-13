"""CLI entry point for the video ingestor."""

import argparse
import sys
from pathlib import Path

from .config import settings
from .ingestion import IngestionPipeline, IngestionError
from .storage import Storage


def main() -> None:
    parser = argparse.ArgumentParser(description="Video Ingestor CLI")
    subparsers = parser.add_subparsers(dest="command")

    # ingest subcommand
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a video")
    ingest_parser.add_argument("url", help="URL or path to the video")
    ingest_parser.add_argument("--model", default=settings.WHISPER_MODEL, help="Whisper model")

    # status subcommand
    status_parser = subparsers.add_parser("status", help="Check job status")
    status_parser.add_argument("job_id", help="Job ID to check")

    # list subcommand
    list_parser = subparsers.add_parser("list", help="List recent jobs")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of jobs to list")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    storage = Storage()
    storage.connect()

    try:
        if args.command == "ingest":
            pipeline = IngestionPipeline(storage)
            job_id = pipeline.ingest_from_url(args.url)
            print(f"Job created: {job_id}")
            print(f"Status: processing")

        elif args.command == "status":
            job = storage.get_job(args.job_id)
            if not job:
                print(f"Job {args.job_id} not found")
                sys.exit(1)
            print(f"Job: {job['job_id']}")
            print(f"Status: {job['status']}")
            if job["full_text"]:
                print(f"Transcript: {job['full_text'][:200]}...")
            if job["error"]:
                print(f"Error: {job['error']}")

        elif args.command == "list":
            jobs = storage.list_jobs(limit=args.limit)
            if not jobs:
                print("No jobs found")
                return
            for job in jobs:
                print(f"  {job['job_id'][:8]}...  {job['status']:10s}  {job['created_at']}")

    finally:
        storage.close()


if __name__ == "__main__":
    main()
