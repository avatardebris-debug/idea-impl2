"""
Web dashboard for pairenv.

Provides a web-based UI for monitoring and controlling IoT devices.
Built with a lightweight HTTP server (no external dependencies).
"""

import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional
from urllib.parse import urlparse, parse_qs

from .coordinator import MultiDeviceCoordinator

logger = logging.getLogger(__name__)


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard."""

    coordinator: Optional[MultiDeviceCoordinator] = None

    def log_message(self, format, *args):
        logger.debug("Dashboard: %s - %s", self.client_address[0], format % args)

    def _send_json(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        return json.loads(body.decode())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._serve_index()
        elif path == "/api/devices":
            self._handle_get_devices()
        elif path == "/api/status":
            self._handle_get_status()
        elif path == "/api/capabilities":
            self._handle_get_capabilities()
        elif path == "/api/history":
            self._handle_get_history()
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/command":
            self._handle_send_command()
        elif path == "/api/discover":
            self._handle_discover()
        else:
            self._send_json({"error": "Not found"}, 404)

    def _serve_index(self):
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>paienv Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; }
        .panel { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .device-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; }
        .device-card { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 15px; }
        .device-card.online { border-left: 4px solid #4CAF50; }
        .device-card.offline { border-left: 4px solid #f44336; }
        .device-card.busy { border-left: 4px solid #FF9800; }
        .device-card.error { border-left: 4px solid #9E9E9E; }
        .status-badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; color: white; }
        .status-online { background: #4CAF50; }
        .status-offline { background: #f44336; }
        .status-busy { background: #FF9800; }
        .status-error { background: #9E9E9E; }
        .command-form { display: flex; gap: 10px; margin-bottom: 10px; }
        .command-form input, .command-form select { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .command-form button { padding: 8px 16px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .command-form button:hover { background: #1976D2; }
        .response { background: #f9f9f9; padding: 10px; border-radius: 4px; margin-top: 10px; font-family: monospace; font-size: 12px; }
        .history-item { padding: 5px 0; border-bottom: 1px solid #eee; }
        .history-item:last-child { border-bottom: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>paienv Dashboard</h1>
        
        <div class="panel">
            <h2>Devices</h2>
            <div class="device-grid" id="devices"></div>
        </div>
        
        <div class="panel">
            <h2>Send Command</h2>
            <div class="command-form">
                <select id="device-select"></select>
                <input type="text" id="command-input" placeholder="Command (e.g., turn_on)">
                <button onclick="sendCommand()">Send</button>
            </div>
            <div class="response" id="response"></div>
        </div>
        
        <div class="panel">
            <h2>Command History</h2>
            <div id="history"></div>
        </div>
    </div>
    
    <script>
        async function loadDevices() {
            const res = await fetch('/api/devices');
            const devices = await res.json();
            const grid = document.getElementById('devices');
            grid.innerHTML = '';
            devices.forEach(d => {
                const card = document.createElement('div');
                card.className = 'device-card ' + d.status;
                card.innerHTML = '<strong>' + d.name + '</strong><br>' +
                    'Protocol: ' + d.protocol + '<br>' +
                    '<span class="status-badge status-' + d.status + '">' + d.status + '</span>';
                grid.appendChild(card);
            });
            const select = document.getElementById('device-select');
            select.innerHTML = '<option value="">Select device</option>';
            devices.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d.device_id;
                opt.textContent = d.name;
                select.appendChild(opt);
            });
        }
        
        async function loadHistory() {
            const res = await fetch('/api/history');
            const history = await res.json();
            const div = document.getElementById('history');
            div.innerHTML = '';
            history.forEach(h => {
                const item = document.createElement('div');
                item.className = 'history-item';
                item.innerHTML = '<strong>' + h.device_id + '</strong>: ' + h.command + ' -> ' + h.status;
                div.appendChild(item);
            });
        }
        
        async function sendCommand() {
            const device = document.getElementById('device-select').value;
            const command = document.getElementById('command-input').value;
            if (!device || !command) return;
            
            const res = await fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({device_id: device, command: command})
            });
            const data = await res.json();
            document.getElementById('response').textContent = JSON.stringify(data, null, 2);
            loadDevices();
            loadHistory();
        }
        
        loadDevices();
        loadHistory();
        setInterval(loadDevices, 5000);
        setInterval(loadHistory, 10000);
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(html.encode())

    def _handle_get_devices(self):
        if not self.coordinator:
            self._send_json({"error": "Coordinator not initialized"}, 500)
            return
        devices = self.coordinator.get_all_device_statuses()
        self._send_json(devices)

    def _handle_get_status(self):
        if not self.coordinator:
            self._send_json({"error": "Coordinator not initialized"}, 500)
            return
        status = {
            "devices": len(self.coordinator.devices),
            "plugins": len(self.coordinator.registry.get_active_plugins()),
        }
        self._send_json(status)

    def _handle_get_capabilities(self):
        if not self.coordinator:
            self._send_json({"error": "Coordinator not initialized"}, 500)
            return
        caps = self.coordinator.get_capabilities_summary()
        self._send_json(caps)

    def _handle_get_history(self):
        if not self.coordinator:
            self._send_json({"error": "Coordinator not initialized"}, 500)
            return
        history = self.coordinator.get_command_history(50)
        self._send_json(history)

    def _handle_send_command(self):
        if not self.coordinator:
            self._send_json({"error": "Coordinator not initialized"}, 500)
            return
        try:
            body = self._read_body()
            device_id = body.get("device_id")
            command = body.get("command")
            if not device_id or not command:
                self._send_json({"error": "device_id and command are required"}, 400)
                return
            result = self.coordinator.send_command(device_id, command)
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_discover(self):
        if not self.coordinator:
            self._send_json({"error": "Coordinator not initialized"}, 500)
            return
        try:
            devices = self.coordinator.discover_devices()
            self._send_json({"discovered": len(devices), "devices": devices})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)


class WebDashboard:
    """
    Web dashboard for monitoring and controlling IoT devices.

    Features:
        - Real-time device status monitoring
        - Command execution via web UI
        - Command history
        - Device discovery
        - Responsive web interface
    """

    def __init__(self, coordinator: MultiDeviceCoordinator, host: str = "0.0.0.0", port: int = 8080):
        self.coordinator = coordinator
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the web dashboard server."""
        DashboardRequestHandler.coordinator = self.coordinator
        self.server = HTTPServer((self.host, self.port), DashboardRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info("Web dashboard started at http://%s:%d", self.host, self.port)

    def stop(self) -> None:
        """Stop the web dashboard server."""
        if self.server:
            self.server.shutdown()
            logger.info("Web dashboard stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
