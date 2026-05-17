"""pairenv CLI — Hardware-Software Bridge command-line interface.

Subcommands:
    pair   Register a new device
    send   Translate English → send to device
    list   Show paired devices
    status Show device state
"""

import argparse
import asyncio
import json
import sys
import os

# Ensure src is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pairenv.parser import EnglishParser
from pairenv.registry import DeviceRegistry
from pairenv.router import CommandRouter, MessageHandler


def cmd_pair(args: argparse.Namespace) -> None:
    """Register a new device."""
    registry = DeviceRegistry()
    transport_config = {}
    if args.port:
        transport_config["port"] = args.port
    if args.baudrate:
        transport_config["baudrate"] = args.baudrate
    if args.type:
        transport_config["type"] = args.type

    registry.add(args.name, args.type or "generic", transport_config)
    print(f"Device '{args.name}' registered successfully.")
    print(f"  Type: {args.type or 'generic'}")
    print(f"  Config: {json.dumps(transport_config, indent=2)}")


def cmd_send(args: argparse.Namespace) -> None:
    """Parse English command and route to device."""
    parser = EnglishParser()
    registry = DeviceRegistry()
    router = CommandRouter(registry)

    cmd = parser.parse(" ".join(args.text))
    if cmd is None:
        print(f"Error: Could not parse command: {' '.join(args.text)}")
        print("Supported templates:")
        for t in parser.list_templates():
            print(f"  - {t}")
        sys.exit(1)

    print(f"Parsed command: {json.dumps(cmd, indent=2)}")

    device_id = args.device or "default"
    device = registry.get(device_id)
    if not device:
        print(f"Warning: Device '{device_id}' not found. Using default transport.")

    response = asyncio.run(router.route(device_id, cmd))
    if response:
        formatted = MessageHandler.format_response(response)
        print(f"Response: {formatted}")
    else:
        print("No response from device (device may not be connected).")


def cmd_list(args: argparse.Namespace) -> None:
    """List all paired devices."""
    registry = DeviceRegistry()
    devices = registry.list_devices()
    if not devices:
        print("No paired devices.")
        return
    print(f"{'ID':<20} {'Type':<15} {'Connected':<10} {'Config'}")
    print("-" * 70)
    for d in devices:
        cfg = json.dumps(d["transport_config"])
        print(f"{d['device_id']:<20} {d['device_type']:<15} {str(d['connected']):<10} {cfg}")


def cmd_status(args: argparse.Namespace) -> None:
    """Show status of a specific device."""
    registry = DeviceRegistry()
    device_id = args.device or "default"
    device = registry.get(device_id)
    if not device:
        print(f"Device '{device_id}' not found.")
        return
    print(f"Device: {device['device_id']}")
    print(f"  Type: {device['device_type']}")
    print(f"  Connected: {device['connected']}")
    print(f"  Config: {json.dumps(device['transport_config'], indent=2)}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="pairenv",
        description="pairenv — Hardware-Software Bridge",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # pair
    pair_p = subparsers.add_parser("pair", help="Register a device")
    pair_p.add_argument("--name", required=True, help="Device name/ID")
    pair_p.add_argument("--type", default="arduino", help="Device type")
    pair_p.add_argument("--port", help="Serial port path")
    pair_p.add_argument("--baudrate", type=int, default=9600, help="Baud rate")

    # send
    send_p = subparsers.add_parser("send", help="Send English command to device")
    send_p.add_argument("text", nargs="+", help="Natural language command")
    send_p.add_argument("--device", default="default", help="Target device ID")

    # list
    subparsers.add_parser("list", help="List paired devices")

    # status
    status_p = subparsers.add_parser("status", help="Show device status")
    status_p.add_argument("--device", default="default", help="Device ID")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Normalize command to string for dispatch
    if isinstance(args.command, list):
        cmd_name = args.command[0] if args.command else None
    else:
        cmd_name = args.command

    if not cmd_name:
        parser.print_help()
        sys.exit(1)

    commands = {
        "pair": cmd_pair,
        "send": cmd_send,
        "list": cmd_list,
        "status": cmd_status,
    }
    cmd_func = commands.get(cmd_name)
    if not cmd_func:
        parser.print_help()
        sys.exit(1)
    cmd_func(args)


if __name__ == "__main__":
    main()
