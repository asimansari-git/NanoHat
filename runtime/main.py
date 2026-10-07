#!/usr/bin/env python3
"""
main.py - CLI interface for NanoHat v3.1.
"""
import argparse
import sys

from runtime.client import OllamaClient
from runtime.engine import AgentEngine

def main():
    parser = argparse.ArgumentParser(
        prog="nanohat",
        description="NanoHat v3.1.0 - Autonomous Linux OS Copilot",
    )
    parser.add_argument("query", nargs="*", type=str, help="User instruction")
    parser.add_argument("--model", type=str, default="functiongemma:latest")
    parser.add_argument("--verbose", action="store_true", help="Log execution details")
    args = parser.parse_args()

    user_query = " ".join(args.query).strip()
    if not user_query:
        parser.print_help()
        sys.exit(0)

    client = OllamaClient(model=args.model)
    engine = AgentEngine(client=client, verbose=args.verbose)

    try:
        result = engine.run(user_query)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()