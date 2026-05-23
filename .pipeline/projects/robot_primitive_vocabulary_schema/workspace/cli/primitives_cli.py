"""CLI for robot motion primitives."""

import argparse
import json
import sys
from pathlib import Path

# Ensure workspace is on sys.path
_ws = Path(__file__).resolve().parent.parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from pipeline.code.primitives import (
    VALID_PRIMITIVE_TYPES,
    create_primitive,
    load_schema,
    validate_primitive,
    validate_schema,
)


def main():
    parser = argparse.ArgumentParser(description="Robot Motion Primitives CLI")
    subparsers = parser.add_subparsers(dest="command")

    # create subcommand
    create_parser = subparsers.add_parser("create", help="Create a primitive")
    create_parser.add_argument("type", choices=sorted(VALID_PRIMITIVE_TYPES), help="Primitive type")
    create_parser.add_argument("--json", dest="json_file", help="JSON file with primitive data")
    create_parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    # validate subcommand
    validate_parser = subparsers.add_parser("validate", help="Validate a primitive")
    validate_parser.add_argument("json_file", help="JSON file to validate")

    # schema subcommand
    schema_parser = subparsers.add_parser("schema", help="Show the JSON schema")
    schema_parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    if args.command == "create":
        kwargs = {}
        if args.json_file:
            with open(args.json_file) as f:
                kwargs = json.load(f)
        prim = create_primitive(args.type, **kwargs)
        output = prim.to_json()
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)

    elif args.command == "validate":
        with open(args.json_file) as f:
            data = json.load(f)
        prim = create_primitive(data["primitive_type"], **data)
        errors = validate_primitive(prim)
        if errors:
            print("Validation errors:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print("Valid!")

    elif args.command == "schema":
        schema = load_schema()
        output = json.dumps(schema, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
