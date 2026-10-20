#!/usr/bin/env python3
"""
main.py - CLI interface for NanoHat v4.0 (Linux Fedora OS Agent).
"""
import argparse
import os
import sys

try:
    from runtime.client import OllamaClient, DEFAULT_HOST, DEFAULT_MODEL
    from runtime.engine import AgentEngine
except (ImportError, ModuleNotFoundError):
    from client import OllamaClient, DEFAULT_HOST, DEFAULT_MODEL
    from engine import AgentEngine


def check_ollama_preflight(client: OllamaClient) -> None:
    """Pre-flight check to verify Ollama daemon is reachable and model is available."""
    try:
        models_resp = client.client.list()
        available_models = []
        models_list = getattr(models_resp, "models", [])
        if not models_list and isinstance(models_resp, dict):
            models_list = models_resp.get("models", [])

        for m in models_list:
            name = getattr(m, "model", None) or (m.get("model") if isinstance(m, dict) else None) or (m.get("name") if isinstance(m, dict) else None)
            if name:
                available_models.append(name)

        target = client.model
        matched = any(target in m or m in target for m in available_models)
        if not matched and available_models:
            print(
                f"[\033[93m!\033[0m] Notice: Model '{target}' not found in local Ollama library.\n"
                f"    To pull the recommended NanoHat v4 model:\n"
                f"    \033[1mollama pull {target}\033[0m\n",
                file=sys.stderr,
            )
    except Exception as e:
        err_msg = str(e).lower()
        if "connect" in err_msg or "refused" in err_msg or "failed to communicate" in err_msg:
            print(
                f"[\033[91m!\033[0m] Error: Cannot connect to Ollama daemon at {client.host}.\n"
                f"    NanoHat v4.0 requires an active Ollama instance for local, private Linux inference.\n\n"
                f"    To install Ollama:  curl -fsSL https://ollama.com/install.sh | sh\n"
                f"    To start daemon:    systemctl start ollama   (or run 'ollama serve')\n",
                file=sys.stderr,
            )
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="nanohat",
        description="NanoHat v4.0 — Linux Fedora OS Agent",
    )
    parser.add_argument("query", nargs="*", type=str, help="User instruction or natural query")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Ollama model tag (default: {DEFAULT_MODEL})")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Ollama server URL (default: http://127.0.0.1:11434)")
    parser.add_argument("--sandbox", action="store_true", help="Enable dry-run sandbox for mutating OS actions")
    parser.add_argument("-v", "--verbose", action="store_true", help="Log execution details")
    args = parser.parse_args()

    if args.sandbox:
        os.environ["NANOHAT_SANDBOX"] = "1"

    user_query = " ".join(args.query).strip()
    if not user_query:
        parser.print_help()
        sys.exit(0)

    client = OllamaClient(host=args.host, model=args.model)
    check_ollama_preflight(client)

    engine = AgentEngine(client=client, verbose=args.verbose)

    try:
        result = engine.run(user_query)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()