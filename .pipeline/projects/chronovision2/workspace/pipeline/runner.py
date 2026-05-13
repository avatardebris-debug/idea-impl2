"""
runner.py
CLI entry point for the Chronovision2 pipeline.

Usage:
    python pipeline/runner.py --provider ollama --model qwen3:32b
    python pipeline/runner.py --provider openai --model gpt-4o
    python pipeline/runner.py --provider claude --model claude-sonnet-4-20250514
    python pipeline/runner.py --provider gemini --model gemini-2.5-pro-preview-06-05
    python pipeline/runner.py --provider grok --model grok-3
"""

from __future__ import annotations

import argparse
import logging
import sys

from chronovision2.agent import Agent

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Chronovision2 Agent Pipeline")
    parser.add_argument(
        "--provider",
        choices=["openai", "claude", "gemini", "ollama", "grok"],
        default="ollama",
        help="LLM provider (default: ollama)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (uses provider default if not specified)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature (default: 0.2)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=20,
        help="Maximum tool-call iterations (default: 20)",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Task input (if not provided, enters interactive mode)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL for remote LLM instances (e.g., Ollama URL)",
    )
    parser.add_argument(
        "--num-ctx",
        type=int,
        default=16384,
        help="Context window size for Ollama (default: 16384)",
    )
    parser.add_argument(
        "--think",
        action="store_true",
        help="Enable thinking mode for Qwen3 models (Ollama only)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stdout,
    )

    # Build the agent
    agent = Agent(
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
        max_iterations=args.max_iterations,
    )

    # Run
    if args.input:
        result = agent.run(args.input)
        print("\n" + "=" * 60)
        print("RESULT:")
        print("=" * 60)
        print(result)
    else:
        # Interactive mode
        print("Chronovision2 Agent — Interactive Mode")
        print("Type your task and press Enter. Type 'quit' to exit.")
        print()
        while True:
            try:
                user_input = input(">>> ").strip()
                if user_input.lower() in ("quit", "exit", "q"):
                    break
                if not user_input:
                    continue
                result = agent.run(user_input)
                print("\n" + "=" * 60)
                print("RESULT:")
                print("=" * 60)
                print(result)
                print()
            except (KeyboardInterrupt, EOFError):
                print("\nBye!")
                break


if __name__ == "__main__":
    main()
