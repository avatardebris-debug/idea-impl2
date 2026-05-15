"""Unit tests for the daemon."""

import os
import time
import signal
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from email_tool.daemon import Daemon, create_daemon


class TestDaemonInitialization:
    """Tests for Daemon initialization."""

    def test_daemon_initialization(self):
        """Test Daemon initialization."""
        daemon = Daemon(interval=300)
        assert daemon.interval == 300
        assert daemon._running is False
        assert daemon._run_count == 0
        assert daemon._last_run is None
        assert daemon._thread is None
        assert daemon._stopped.is_set() is False

    def test_daemon_with_config(self):
        """Test Daemon with configuration."""
        config = MagicMock()
        config.get_log_level.return_value = 'INFO'
        daemon = Daemon(config=config, interval=600)
        assert daemon.interval == 600

    def test_daemon_default_interval(self):
        """Test Daemon with default interval."""
        daemon = Daemon()
        assert daemon.interval == 3600

    def test_daemon_pid_file(self):
        """Test Daemon PID file path."""
        daemon = Daemon()
        assert daemon.pid_file is not None
        assert isinstance(daemon.pid_file, Path)


class TestDaemonLifecycle:
    """Tests for daemon lifecycle."""

    def test_start_daemon(self):
        """Test starting the daemon."""
        daemon = Daemon(interval=1)
        daemon.start(foreground=True)
        assert daemon._running is True
        assert daemon._thread is not None
        assert daemon._thread.is_alive()
        daemon.stop()

    def test_start_already_running(self):
        """Test starting daemon that's already running."""
        daemon = Daemon(interval=1)
        daemon.start(foreground=True)
        with patch('email_tool.daemon.logger') as mock_logger:
            daemon.start(foreground=True)
            mock_logger.warning.assert_called()
        daemon.stop()

    def test_stop_daemon(self):
        """Test stopping the daemon."""
        daemon = Daemon(interval=1)
        daemon.start(foreground=True)
        time.sleep(0.5)
        daemon.stop()
        assert daemon._running is False
        assert daemon._thread is None or not daemon._thread.is_alive()

    def test_stop_daemon_timeout(self):
        """Test daemon stop with timeout."""
        daemon = Daemon(interval=1)
        daemon.start(foreground=True)
        time.sleep(0.5)
        daemon.stop()
        # Should stop gracefully within timeout

    def test_is_running_running(self):
        """Test is_running when daemon is running."""
        daemon = Daemon(interval=1)
        daemon.start(foreground=True)
        assert daemon.is_running() is True
        daemon.stop()

    def test_is_running_stopped(self):
        """Test is_running when daemon is stopped."""
        daemon = Daemon(interval=1)
        assert daemon.is_running() is False


class TestDaemonRunCycle:
    """Tests for daemon run cycle."""

    def test_run_cycle_initialization(self):
        """Test run cycle updates."""
        daemon = Daemon(interval=1)
        daemon._run_cycle()
        assert daemon._run_count == 1
        assert daemon._last_run is not None

    def test_run_cycle_no_sources(self):
        """Test run cycle with no sync sources."""
        daemon = Daemon(interval=1)
        daemon.config = MagicMock()
        daemon.config.get_sync_sources.return_value = []
        
        with patch('email_tool.daemon.logger') as mock_logger:
            daemon._run_cycle()
            mock_logger.warning.assert_called()

    def test_run_cycle_with_sources(self):
        """Test run cycle with sync sources."""
        daemon = Daemon(interval=1)
        daemon.config = MagicMock()
        daemon.config.get_sync_sources.return_value = ['/tmp/test_source']
        
        with patch.object(daemon, '_process_source') as mock_process:
            daemon._run_cycle()
            mock_process.assert_called_once_with('/tmp/test_source')

    def test_run_cycle_exception_handling(self):
        """Test exception handling in run cycle."""
        daemon = Daemon(interval=1)
        daemon.config = MagicMock()
        daemon.config.get_sync_sources.return_value = ['/tmp/test_source']
        daemon.config.get.return_value = 'DEBUG'
        
        with patch.object(daemon, '_process_source', side_effect=Exception("Test error")):
            with patch('email_tool.daemon.logger') as mock_logger:
                daemon._run_cycle()
                mock_logger.error.assert_called()


class TestDaemonProcessSource:
    """Tests for source processing."""

    def test_process_source_existing_path(self):
        """Test processing existing source path."""
        daemon = Daemon(interval=1)
        
        with patch('email_tool.daemon.Path') as mock_path:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance
            
            with patch('email_tool.daemon.logger') as mock_logger:
                daemon._process_source('/tmp/test_source')
                mock_logger.info.assert_called()

    def test_process_source_non_existing_path(self):
        """Test processing non-existing source path."""
        daemon = Daemon(interval=1)
        
        with patch('email_tool.daemon.Path') as mock_path:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value = mock_path_instance
            
            with patch('email_tool.daemon.logger') as mock_logger:
                daemon._process_source('/tmp/non_existing')
                mock_logger.warning.assert_called()


class TestDaemonStatus:
    """Tests for daemon status."""

    def test_get_status(self):
        """Test getting daemon status."""
        daemon = Daemon(interval=300)
        daemon._run_count = 5
        daemon._last_run = MagicMock()
        daemon._last_run.isoformat.return_value = "2024-01-01T00:00:00"
        
        status = daemon.get_status()
        assert status['running'] is False
        assert status['interval'] == 300
        assert status['run_count'] == 5
        assert status['pid'] == os.getpid()

    def test_log_status(self):
        """Test logging daemon status."""
        daemon = Daemon(interval=300)
        
        with patch('email_tool.daemon.logger') as mock_logger:
            daemon._log_status()
            mock_logger.debug.assert_called()


class TestDaemonPIDFile:
    """Tests for PID file handling."""

    def test_write_pid_file(self, tmp_path):
        """Test writing PID file."""
        daemon = Daemon(interval=1, pid_file=tmp_path / "test.pid")
        daemon._write_pid_file()
        
        assert daemon.pid_file.exists()
        with open(daemon.pid_file) as f:
            assert f.read().strip() == str(os.getpid())

    def test_remove_pid_file(self, tmp_path):
        """Test removing PID file."""
        daemon = Daemon(interval=1, pid_file=tmp_path / "test.pid")
        daemon._write_pid_file()
        assert daemon.pid_file.exists()
        
        daemon._remove_pid_file()
        assert not daemon.pid_file.exists()

    def test_remove_pid_file_missing(self, tmp_path):
        """Test removing non-existing PID file."""
        daemon = Daemon(interval=1, pid_file=tmp_path / "test.pid")
        
        with patch('email_tool.daemon.logger') as mock_logger:
            daemon._remove_pid_file()
            # Should not raise exception

    def test_pid_file_permission_error(self, tmp_path):
        """Test PID file permission error."""
        daemon = Daemon(interval=1, pid_file=tmp_path / "test.pid")
        
        # Make directory read-only
        tmp_path.chmod(0o444)
        
        with patch('email_tool.daemon.logger') as mock_logger:
            daemon._write_pid_file()
            # Should handle permission error gracefully


class TestDaemonRunLoop:
    """Tests for daemon main loop."""

    def test_run_loop_stops_on_signal(self):
        """Test daemon loop stops on signal."""
        daemon = Daemon(interval=1)
        daemon.start(foreground=True)
        time.sleep(0.5)
        daemon.stop()
        assert daemon._stopped.is_set() is True

    def test_run_loop_exception_handling(self):
        """Test exception handling in daemon loop."""
        daemon = Daemon(interval=1)
        daemon.config = MagicMock()
        daemon.config.get.return_value = 'DEBUG'
        
        def mock_run_cycle():
            daemon._stopped.set()
            raise Exception("Test error")
            
        with patch.object(daemon, '_run_cycle', side_effect=mock_run_cycle):
            with patch('email_tool.daemon.logger') as mock_logger:
                # Run loop should handle exception and exit because we set _stopped
                daemon._run_loop()
                mock_logger.error.assert_called()

    def test_run_loop_wait_timeout(self):
        """Test daemon loop wait timeout."""
        daemon = Daemon(interval=1)
        daemon.start(foreground=True)
        time.sleep(0.5)
        daemon.stop()
        # Should wait for interval or stop signal


class TestCreateDaemon:
    """Tests for create_daemon function."""

    def test_create_daemon_default(self):
        """Test create_daemon with defaults."""
        with patch('email_tool.daemon.load_config') as mock_load:
            mock_load.return_value = MagicMock()
            daemon = create_daemon()
            assert isinstance(daemon, Daemon)

    def test_create_daemon_with_config(self):
        """Test create_daemon with config path."""
        with patch('email_tool.daemon.load_config') as mock_load:
            mock_load.return_value = MagicMock()
            daemon = create_daemon(config_path=Path("/tmp/config.yaml"))
            mock_load.assert_called_once_with(Path("/tmp/config.yaml"))
            assert isinstance(daemon, Daemon)

    def test_create_daemon_with_interval(self):
        """Test create_daemon with custom interval."""
        with patch('email_tool.daemon.load_config') as mock_load:
            mock_load.return_value = MagicMock()
            daemon = create_daemon(interval=1800)
            assert daemon.interval == 1800


class TestDaemonRunOnce:
    """Tests for run_once method."""

    def test_run_once(self):
        """Test running once and exiting."""
        daemon = Daemon(interval=1)
        
        def mock_run_cycle():
            daemon._run_count += 1
            
        with patch.object(daemon, '_run_cycle', side_effect=mock_run_cycle):
            result = daemon.run_once()
            assert result is True

    def test_run_once_no_cycle(self):
        """Test run_once when no cycle runs."""
        daemon = Daemon(interval=1)
        
        with patch.object(daemon, '_run_cycle', return_value=False):
            result = daemon.run_once()
            assert result is False


class TestDaemonEdgeCases:
    """Tests for daemon edge cases."""

    def test_daemon_multiple_start_stop(self):
        """Test multiple start/stop cycles."""
        daemon = Daemon(interval=1)
        
        for _ in range(3):
            daemon.start(foreground=True)
            time.sleep(0.1)
            daemon.stop()
            assert daemon._running is False

    def test_daemon_interrupted_wait(self):
        """Test daemon wait interrupted by signal."""
        daemon = Daemon(interval=1)
        daemon.start(foreground=True)
        time.sleep(0.5)
        daemon.stop()
        # Should handle interruption gracefully

    def test_daemon_concurrent_operations(self):
        """Test daemon with concurrent operations."""
        daemon = Daemon(interval=1)
        daemon.start(foreground=True)
        
        # Get status while running
        status = daemon.get_status()
        assert status['running'] is True
        
        daemon.stop()


class TestDaemonIntegration:
    """Integration tests for daemon."""

    def test_daemon_full_lifecycle(self):
        """Test complete daemon lifecycle."""
        daemon = Daemon(interval=1)
        
        # Start
        daemon.start(foreground=True)
        assert daemon.is_running()
        
        # Wait for at least one cycle
        time.sleep(1.5)
        assert daemon._run_count >= 1
        
        # Stop
        daemon.stop()
        assert not daemon.is_running()

    def test_daemon_with_custom_pid_file(self, tmp_path):
        """Test daemon with custom PID file location."""
        pid_file = tmp_path / "custom.pid"
        daemon = Daemon(interval=1, pid_file=pid_file)
        daemon.start(foreground=True)
        
        assert pid_file.exists()
        daemon.stop()
        assert not pid_file.exists()

    def test_daemon_log_level(self):
        """Test daemon with different log levels."""
        daemon = Daemon(interval=1)
        daemon.config = MagicMock()
        daemon.config.get_log_level.return_value = 'DEBUG'
        
        daemon.start(foreground=True)
        daemon.stop()
        # Should not raise exception
