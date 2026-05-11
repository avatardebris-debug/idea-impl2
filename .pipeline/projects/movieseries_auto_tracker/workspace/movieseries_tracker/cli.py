"""Command-line interface for the Movie/Series auto-tracker."""

import sys
import argparse
from typing import List

from .models import Title, WatchlistEntry
from .search import StreamingSearchService
from .watchlist import WatchlistManager


def _format_title(title: Title) -> str:
    """Format a Title for display."""
    lines = [
        f"  Title: {title.title}",
        f"  Type: {title.type}",
        f"  Year: {title.year}",
        f"  Rating: {title.rating}/10",
        f"  Genres: {', '.join(title.genres)}",
        f"  Description: {title.description}",
    ]
    if title.streaming_services:
        services = []
        for s in title.streaming_services:
            services.append(f"{s.name} ({s.type})")
        lines.append(f"  Available on: {', '.join(services)}")
    if title.affiliate_link:
        lines.append(f"  Watch here: {title.affiliate_link}")
    return "\n".join(lines)


def _format_watchlist_entry(entry: WatchlistEntry) -> str:
    """Format a WatchlistEntry for display."""
    lines = [
        f"  Title: {entry.title}",
        f"  Type: {entry.title_type}",
        f"  Year: {entry.year}",
    ]
    if entry.progress == "Watching":
        lines.append(f"  Progress: {entry.progress} ({entry.progress_percentage:.0f}%)")
    elif entry.progress == "Completed":
        lines.append("  Progress: Completed")
    else:
        lines.append("  Progress: Not started")
    if entry.last_watched_at:
        lines.append(f"  Last watched: {entry.last_watched_at}")
    if entry.added_at:
        lines.append(f"  Added: {entry.added_at}")
    if entry.notes:
        lines.append(f"  Notes: {entry.notes}")
    if entry.rating_given > 0:
        lines.append(f"  Your rating: {entry.rating_given}/10")
    return "\n".join(lines)


def cmd_search(args, search_service: StreamingSearchService, watchlist_manager: WatchlistManager) -> None:
    """Handle the 'search' command."""
    results = search_service.search(
        query=args.query,
        title_type=args.type,
        platform=args.platform,
        availability=args.availability,
    )
    if not results:
        print("No results found.")
        return
    print(f"\nFound {len(results)} result(s):\n")
    for i, title in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print(_format_title(title))
        print()


def cmd_watchlist(args, search_service: StreamingSearchService, watchlist_manager: WatchlistManager) -> None:
    """Handle the 'watchlist' command."""
    entries = watchlist_manager.get_all()
    if not entries:
        print("Your watchlist is empty.")
        return
    print(f"\nYour watchlist ({len(entries)} titles):\n")
    for i, entry in enumerate(entries, 1):
        print(f"--- {i} ---")
        print(_format_watchlist_entry(entry))
        print()


def cmd_add(args, search_service: StreamingSearchService, watchlist_manager: WatchlistManager) -> None:
    """Handle the 'add' command."""
    # Try to find the title in the search database
    results = search_service.search(query=args.title)
    title_obj = None
    for r in results:
        if r.title.lower() == args.title.lower():
            title_obj = r
            break

    title_type = title_obj.type if title_obj else "unknown"
    year = title_obj.year if title_obj else 0

    entry = watchlist_manager.add(
        title_id=title_obj.id if title_obj else f"custom_{args.title.lower().replace(' ', '_')}",
        title=args.title,
        title_type=title_type,
        year=year,
        notes=args.notes if hasattr(args, "notes") and args.notes else "",
    )
    print(f"Added '{entry.title}' to your watchlist.")


def cmd_remove(args, search_service: StreamingSearchService, watchlist_manager: WatchlistManager) -> None:
    """Handle the 'remove' command."""
    # Try to find by title name
    entry = watchlist_manager.get_by_title_name(args.title)
    if entry:
        watchlist_manager.remove(entry.title_id)
        print(f"Removed '{entry.title}' from your watchlist.")
    else:
        print(f"Title '{args.title}' not found in watchlist.")


def cmd_continue(args, search_service: StreamingSearchService, watchlist_manager: WatchlistManager) -> None:
    """Handle the 'continue' command."""
    entries = watchlist_manager.get_continue_watching()
    if not entries:
        print("No titles to continue watching. Add titles to your watchlist and track progress!")
        return
    print("\nContinue Watching:\n")
    for i, entry in enumerate(entries, 1):
        print(f"--- {i} ---")
        print(_format_watchlist_entry(entry))
        print()


def cmd_details(args, search_service: StreamingSearchService, watchlist_manager: WatchlistManager) -> None:
    """Handle the 'details' command."""
    results = search_service.search(query=args.title)
    title_obj = None
    for r in results:
        if r.title.lower() == args.title.lower():
            title_obj = r
            break

    if title_obj:
        print(f"\nDetails for '{title_obj.title}':\n")
        print(_format_title(title_obj))
    else:
        print(f"Title '{args.title}' not found in database.")


def main(argv=None) -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="movieseries-tracker",
        description="Movie/Series auto-tracker: search streaming platforms, manage watchlist, and continue watching.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # search command
    search_parser = subparsers.add_parser("search", help="Search for titles across streaming platforms")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", choices=["movie", "series"], help="Filter by type")
    search_parser.add_argument("--platform", help="Filter by streaming platform")
    search_parser.add_argument("--availability", choices=["paid", "free", "freemium"], help="Filter by availability")

    # watchlist command
    watchlist_parser = subparsers.add_parser("watchlist", help="List all titles in your watchlist")

    # add command
    add_parser = subparsers.add_parser("add", help="Add a title to your watchlist")
    add_parser.add_argument("title", help="Title name to add")
    add_parser.add_argument("--notes", default="", help="Optional notes")

    # remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a title from your watchlist")
    remove_parser.add_argument("title", help="Title name to remove")

    # continue command
    subparsers.add_parser("continue", help="Show what to watch next")

    # details command
    details_parser = subparsers.add_parser("details", help="Show details for a title")
    details_parser.add_argument("title", help="Title name")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    search_service = StreamingSearchService()
    watchlist_manager = WatchlistManager()

    commands = {
        "search": cmd_search,
        "watchlist": cmd_watchlist,
        "add": cmd_add,
        "remove": cmd_remove,
        "continue": cmd_continue,
        "details": cmd_details,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args, search_service, watchlist_manager)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
