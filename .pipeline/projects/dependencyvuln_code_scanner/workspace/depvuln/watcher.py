import time
import os
import sys
import click
from threading import Thread

def watch_directory(path: str, callback: callable):
    """Watches a directory for changes and triggers callback."""
    # MVP Watcher using simple polling
    # In production, use `watchdog` library
    
    click.echo(f"Watching {path} for changes...")
    
    last_mtimes = {}
    
    def check_files():
        supported_files = [
            "requirements.txt", "Pipfile", "setup.py",
            "package-lock.json", "yarn.lock", "package.json",
            "pom.xml", "build.gradle", "Cargo.toml", "go.mod", "Podfile"
        ]
        
        while True:
            changed = False
            for root, _, files in os.walk(path):
                for file in files:
                    if file in supported_files:
                        fpath = os.path.join(root, file)
                        try:
                            mtime = os.path.getmtime(fpath)
                            if fpath not in last_mtimes:
                                last_mtimes[fpath] = mtime
                            elif mtime > last_mtimes[fpath]:
                                last_mtimes[fpath] = mtime
                                changed = True
                                click.echo(f"\n[Watch] Detected change in {fpath}")
                        except OSError:
                            pass
            
            if changed:
                callback(path)
                
            time.sleep(2)
            
    thread = Thread(target=check_files, daemon=True)
    thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nStopping watch mode.")
        sys.exit(0)
