import cmd
import shlex
import json

from manuscriptdata_analyzer.database import Database
from manuscriptdata_analyzer.analytics import TrendAnalyzer, BookComparator, DemographicProfiler, ReportGenerator

class DashboardShell(cmd.Cmd):
    intro = "Welcome to ManuscriptData Analyzer Dashboard. Type help or ? to list commands.\n"
    prompt = "(manuscript) "

    def __init__(self, db_path: str):
        super().__init__()
        self.db = Database(db_path)

    def do_list(self, arg):
        """List all books in the database."""
        books = self.db.execute_query("SELECT book_id, title FROM books", fetch_all=True)
        if not books:
            print("No books found.")
            return
        print("Books:")
        for b in books:
            print(f" - [{b['book_id']}] {b['title']}")

    def do_report(self, arg):
        """View performance report. Usage: report"""
        generator = ReportGenerator(self.db)
        print(generator.generate_text_report())

    def do_export_json(self, arg):
        """Export analytics to JSON. Usage: export_json <output_file>"""
        if not arg:
            print("Please provide an output filename.")
            return
            
        generator = ReportGenerator(self.db)
        # Assuming ReportGenerator can output dict data, for now we will just use the csv logic to get data and dump to json
        # Since we don't have direct json export in Phase 2 ReportGenerator, let's dump book ranking as a proxy
        comparator = BookComparator(self.db)
        ranks = comparator.rank_by_revenue()
        with open(arg, 'w') as f:
            json.dump([dict(r) for r in ranks], f, indent=2)
        print(f"Exported to {arg}")

    def do_quit(self, arg):
        """Exit the dashboard."""
        print("Goodbye!")
        return True
        
    def do_exit(self, arg):
        """Exit the dashboard."""
        return self.do_quit(arg)

def start_dashboard(db_path: str):
    DashboardShell(db_path).cmdloop()
