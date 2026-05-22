"""Daemon module for Email Tool.

This module provides background service functionality for periodic email synchronization
and processing. Supports systemd and cron integration.
"""

import os
import sys
import time
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Callable, Any
from threading import Thread, Event
import json

from email_tool.config import load_config, EmailToolConfig
from email_tool.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


class Daemon:
    """Background daemon for periodic email synchronization.
    
    This class manages a background service that runs at configurable intervals,
    processing emails and performing synchronization tasks.
    """
    
    def __init__(
        self,
        config: Optional[EmailToolConfig] = None,
        interval: int = 3600,
        pid_file: Optional[Path] = None,
        log_file: Optional[Path] = None
    ):
        """Initialize daemon.
        
        Args:
            config: Configuration instance. If None, loads from default location.
            interval: Sync interval in seconds.
            pid_file: Path to PID file for process management.
            log_file: Path to log file.
        """
        self.config = config or load_config()
        self.interval = interval
        self.pid_file = pid_file or Path("/tmp/email_tool_daemon.pid")
        self.log_file = log_file
        
        # State
        self._running = False
        self._stopped = Event()
        self._thread: Optional[Thread] = None
        self._last_run: Optional[datetime] = None
        self._run_count = 0
        
        # Signal handling
        self._setup_signals()
    
    def _setup_signals(self):
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        # SIGHUP is Unix-only; skip gracefully on Windows
        if hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, self._reload_config)
    
    def _signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received signal {sig_name}, initiating shutdown...")
        self.stop()
    
    def _reload_config(self, signum, frame):
        """Reload configuration on SIGHUP."""
        logger.info("Reloading configuration...")
        self.config = load_config()
        self.config.setup_logging()
    
    def _write_pid_file(self):
        """Write PID file."""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            logger.debug(f"PID file written: {self.pid_file}")
        except (IOError, OSError) as e:
            logger.warning(f"Could not write PID file: {e}")
    
    def _remove_pid_file(self):
        """Remove PID file."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                logger.debug(f"PID file removed: {self.pid_file}")
        except (IOError, OSError) as e:
            logger.warning(f"Could not remove PID file: {e}")
    
    def _run_cycle(self):
        """Execute a single sync cycle."""
        self._last_run = datetime.now()
        self._run_count += 1
        
        logger.info(f"Starting sync cycle #{self._run_count}")
        
        try:
            # Get sync sources
            sources = self.config.get_sync_sources()
            
            if not sources:
                logger.warning("No sync sources configured")
                return
            
            # Process each source
            for source in sources:
                logger.info(f"Processing source: {source}")
                self._process_source(source)
            
            logger.info(f"Sync cycle #{self._run_count} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in sync cycle: {e}")
            if self.config.get('log_level') == 'DEBUG':
                import traceback
                traceback.print_exc()
    
    def _process_source(self, source: str):
        """Process a single sync source.
        
        Args:
            source: Source identifier (path, URL, etc.)
        """
        # This is a placeholder for actual sync logic
        # In a full implementation, this would connect to email sources
        # and download/process emails
        
        source_path = Path(source)
        if source_path.exists():
            logger.info(f"Syncing from local path: {source_path}")
            # Process emails in the source directory
            # This would use the EmailProcessor or EmailOrganizer
        else:
            logger.warning(f"Source not found: {source}")
    
    def _log_status(self):
        """Log daemon status."""
        status = {
            'running': self._running,
            'interval': self.interval,
            'last_run': self._last_run.isoformat() if self._last_run else None,
            'run_count': self._run_count,
            'pid': os.getpid()
        }
        logger.debug(f"Daemon status: {json.dumps(status)}")
    
    def start(self, foreground: bool = False):
        """Start the daemon.
        
        Args:
            foreground: If True, run in foreground (no backgrounding).
        """
        if self._running:
            logger.warning("Daemon is already running")
            return
        
        logger.info("Starting daemon")
        
        # Write PID file
        self._write_pid_file()
        
        # Set up logging
        if self.log_file:
            setup_logging(
                log_level=self.config.get_log_level(),
                log_file=str(self.log_file)
            )
        else:
            self.config.setup_logging()
        
        # Start background thread
        self._running = True
        self._stopped.clear()
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        if not foreground:
            logger.info(f"Daemon started in background (PID: {os.getpid()})")
        else:
            logger.info(f"Daemon started in foreground (PID: {os.getpid()})")
    
    def _run_loop(self):
        """Main daemon loop."""
        while not self._stopped.is_set():
            try:
                # Run sync cycle
                self._run_cycle()
                
                # Wait for next interval
                logger.debug(f"Waiting {self.interval} seconds until next sync")
                
                # Use Event.wait for interruptible sleep
                if self._stopped.wait(timeout=self.interval):
                    break
                    
            except Exception as e:
                logger.error(f"Error in daemon loop: {e}")
                if self.config.get('log_level') == 'DEBUG':
                    import traceback
                    traceback.print_exc()
                
                # Wait before retrying
                self._stopped.wait(timeout=60)
        
        logger.info("Daemon loop ended")
    
    def stop(self):
        """Stop the daemon gracefully."""
        logger.info("Stopping daemon...")
        
        self._running = False
        self._stopped.set()
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        
        # Remove PID file
        self._remove_pid_file()
        
        logger.info("Daemon stopped")
    
    def is_running(self) -> bool:
        """Check if daemon is running."""
        return self._running and self._thread is not None and self._thread.is_alive()
    
    def get_status(self) -> dict:
        """Get daemon status."""
        return {
            'running': self._running,
            'interval': self.interval,
            'last_run': self._last_run.isoformat() if self._last_run else None,
            'run_count': self._run_count,
            'pid': os.getpid(),
            'pid_file': str(self.pid_file)
        }
    
    def run_once(self):
        """Run a single sync cycle and exit."""
        self._run_cycle()
        return self._run_count > 0


def create_daemon(
    config_path: Optional[Path] = None,
    interval: int = 3600,
    foreground: bool = False
) -> Daemon:
    """Create and configure a daemon instance.
    
    Args:
        config_path: Path to configuration file.
        interval: Sync interval in seconds.
        foreground: If True, run in foreground.
    
    Returns:
        Configured Daemon instance.
    """
    config = load_config(config_path) if config_path else load_config()
    return Daemon(config=config, interval=interval)


def main():
    """Main entry point for daemon CLI."""
    parser = argparse.ArgumentParser(
        description='Email Tool Daemon - Background service for periodic email synchronization'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=3600,
        help='Sync interval in seconds (default: 3600)'
    )
    
    parser.add_argument(
        '--foreground', '-f',
        action='store_true',
        help='Run in foreground (do not background)'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show daemon status'
    )
    
    parser.add_argument(
        '--stop',
        action='store_true',
        help='Stop running daemon'
    )
    
    parser.add_argument(
        '--pid-file',
        type=str,
        default='/tmp/email_tool_daemon.pid',
        help='Path to PID file'
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(Path(args.config)) if args.config else load_config()
    
    # Create daemon
    daemon = Daemon(
        config=config,
        interval=args.interval,
        pid_file=Path(args.pid_file)
    )
    
    # Handle commands
    if args.status:
        # Check if daemon is running
        pid_file = Path(args.pid_file)
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = int(f.read().strip())
                if os.path.exists(f'/proc/{pid}'):
                    print(f"Daemon is running (PID: {pid})")
                    print(json.dumps(daemon.get_status(), indent=2))
                else:
                    print(f"Daemon PID file exists but process not running")
            except (ValueError, IOError) as e:
                print(f"Error reading PID file: {e}")
        else:
            print("Daemon is not running")
        return 0
    
    if args.stop:
        # Stop daemon
        pid_file = Path(args.pid_file)
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                print(f"Sent SIGTERM to daemon (PID: {pid})")
            except (ValueError, OSError) as e:
                print(f"Error stopping daemon: {e}")
        else:
            print("No PID file found, daemon may not be running")
        return 0
    
    if args.once:
        # Run once and exit
        daemon.run_once()
        return 0
    
    # Start daemon
    daemon.start(foreground=args.foreground)
    
    # If not foreground, wait for signal
    if not args.foreground:
        try:
            while daemon.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            daemon.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
