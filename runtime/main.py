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
        prog="nanohat",
        description="🎩 NanoHat v3.1.0 — Autonomous Linux OS Agent (FunctionGemma 270M)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  nanohat "What is 45 * 12?"
  nanohat "What is my current RAM usage?"
  nanohat "Check battery status"
  nanohat "Is bluetooth on?"
  nanohat "Remember my favorite editor is neovim"
  nanohat "What is my editor?"
  nanohat "Remind me to stretch at 5pm"
  nanohat --verbose "Status of pipewire"
"""
    )
    parser.add_argument("query", nargs="*", type=str, help="User query or instruction (quoted or unquoted)")
    parser.add_argument("-p", "--prompt", type=str, help="User query/prompt (flag syntax)")
    parser.add_argument("-V", "--version", action="version", version="%(prog)s v3.1.0 (FunctionGemma 270M)")
    parser.add_argument("-pv", "--prompt-version", type=str, default=DEFAULT_VERSION, choices=list(PROMPTS.keys()),
                        help=f"System prompt version (default: {DEFAULT_VERSION})")
    parser.add_argument("--model", type=str, default="functiongemma:latest",
                        help="Ollama model name (default: functiongemma:latest)")
    parser.add_argument("--router", choices=["regex", "semantic"], default="semantic",
                        help="Tool gating router: 'semantic' (BGE bi-encoder) or 'regex' (default: semantic)")
    parser.add_argument("--verbose", action="store_true", help="Print detailed tool call & execution steps")

    args = parser.parse_args()

    positional_query = " ".join(args.query).strip() if isinstance(args.query, list) and args.query else None
    user_query = positional_query or args.prompt
    if not user_query:
        parser.print_help()
        sys.exit(0)

    client = OllamaClient(model=args.model)
    engine = AgentEngine(
        client=client,
        prompt_version=args.prompt_version,
        verbose=args.verbose,
        router=args.router,
    )

    try:
        result = engine.run(user_query)
        print(result)
    except Exception as e:
        print(f"\033[91mError: {e}\033[0m", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
