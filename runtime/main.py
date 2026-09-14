#!/usr/bin/env python3
"""
main.py — CLI entry point for fuge-nanohat FunctionGemma test harness.
"""

import argparse
import sys
try:
    from .client import OllamaClient
    from .engine import AgentEngine
    from .prompts import PROMPTS, DEFAULT_VERSION
except (ImportError, ValueError):
    from client import OllamaClient
    from engine import AgentEngine
    from prompts import PROMPTS, DEFAULT_VERSION



def main():
    parser = argparse.ArgumentParser(
        description="fuge-nanohat: FunctionGemma 270M Native Function Calling Test Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python main.py -p "What is 45 * 12?"
  python main.py -p "Calculate 2 ** 10" --verbose
  python main.py -p "What is 15 percent of 800?" -v v2
"""
    )
    parser.add_argument("-p", "--prompt", type=str, help="User query/prompt")
    parser.add_argument("-v", "--version", type=str, default=DEFAULT_VERSION, choices=list(PROMPTS.keys()),
                        help=f"System prompt version (default: {DEFAULT_VERSION})")
    parser.add_argument("--model", type=str, default="functiongemma:latest",
                        help="Ollama model name (default: functiongemma:latest)")
    parser.add_argument("--verbose", action="store_true", help="Print detailed tool call & execution steps")

    args = parser.parse_args()

    if not args.prompt:
        parser.print_help()
        sys.exit(0)

    client = OllamaClient(model=args.model)
    engine = AgentEngine(client=client, prompt_version=args.version, verbose=args.verbose)

    try:
        result = engine.run(args.prompt)
        print(result)
    except Exception as e:
        print(f"\033[91mError: {e}\033[0m", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
