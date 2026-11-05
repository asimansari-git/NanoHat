#!/usr/bin/env python3
"""
benchmark_models.py — Multi-Dimensional 4-Matrix Benchmark Suite for NanoHat v4.0

Evaluates base and fine-tuned models (e.g. qwen3:0.6b, nanohat4-qwen3:latest,
nanohat4-qwen3:q8_0) across both `think=False` and `think=True` inference modes
on all 299 unseen evaluation queries in `train/data/nanohat_v4_test_unseen.jsonl`.

Features:
  - Per-query automatic checkpointing & resume (`benchmark_checkpoint.json`)
  - Fault-tolerant Ollama HTTP 500 handling (catches truncated tool JSON errors)
  - 4-Matrix Markdown Report flushed after every completed model/mode run
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.client import OllamaClient, DEFAULT_HOST
from runtime.engine import AgentEngine
from runtime.functions import REGISTRY
from runtime.prompts import get_system_prompt
from runtime.tools import ALL_TOOLS

DEFAULT_DATA_PATH = Path(__file__).resolve().parent / "nanohat_v4_test_unseen.jsonl"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "results"



def get_hardware_temps() -> Tuple[Optional[float], Optional[float]]:
    """Return (gpu_temp_c, cpu_temp_c) from nvidia-smi and psutil coretemp."""
    gpu_temp: Optional[float] = None
    cpu_temp: Optional[float] = None
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2.0,
        ).strip()
        if out:
            gpu_temp = float(out.splitlines()[0].strip())
    except Exception:
        pass

    try:
        temps = psutil.sensors_temperatures()
        if "coretemp" in temps and temps["coretemp"]:
            cpu_temp = max(e.current for e in temps["coretemp"] if e.current is not None)
        elif temps:
            all_vals = [e.current for entries in temps.values() for e in entries if e.current is not None]
            if all_vals:
                cpu_temp = max(all_vals)
    except Exception:
        pass

    return gpu_temp, cpu_temp


def enforce_thermal_guard(max_temp_c: float = 78.0) -> Tuple[Optional[float], Optional[float]]:
    """If GPU or CPU temp reaches max_temp_c, pause until both cool down below (max_temp_c - 4.0)."""
    gpu_t, cpu_t = get_hardware_temps()
    target_cool = max_temp_c - 4.0
    while (gpu_t is not None and gpu_t >= max_temp_c) or (cpu_t is not None and cpu_t >= max_temp_c):
        g_str = f"{gpu_t:.0f}°C" if gpu_t is not None else "N/A"
        c_str = f"{cpu_t:.0f}°C" if cpu_t is not None else "N/A"
        print(
            f"  [THERMAL GUARD] Hardware at GPU={g_str} | CPU={c_str} (>= {max_temp_c:.0f}°C limit). "
            f"Cooling down to <={target_cool:.0f}°C..."
        )
        time.sleep(3.0)
        gpu_t, cpu_t = get_hardware_temps()
    return gpu_t, cpu_t



def load_dataset(data_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {data_path}")

    records = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            prompt_list = data.get("prompt", [])
            user_query = ""
            for p in prompt_list:
                if p.get("role") == "user":
                    user_query = p.get("content", "")
            if not user_query and "user_query" in data:
                user_query = data["user_query"]

            gt = data.get("ground_truth_calls") or data.get("expected_tool_calls", [])
            if isinstance(gt, str):
                try:
                    gt = json.loads(gt)
                except Exception:
                    gt = []

            records.append({
                "kind": data.get("kind", "tool" if gt else "chat_or_math"),
                "category": data.get("category", "general"),
                "expected_polarity": data.get("expected_polarity", "none"),
                "user_query": user_query,
                "ground_truth_calls": gt,
                "expected_math_answer": data.get("expected_math_answer"),
            })
            if limit and len(records) >= limit:
                break
    return records


def canonicalize_call(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes optional default parameters for functional argument equivalence."""
    if not isinstance(args, dict):
        args = {}
    c: Dict[str, Any] = {}
    if name == "system_health":
        c["metric"] = str(args.get("metric", "all")).strip().lower()
    elif name == "power_profile":
        act = str(args.get("action", "get")).strip().lower()
        c["action"] = "get" if act in ("get", "status") else act
        if c["action"] == "set":
            c["profile"] = str(args.get("profile", "")).strip().lower()
    elif name in ("toggle_wifi", "toggle_bluetooth"):
        st = str(args.get("state", args.get("action", "status"))).strip().lower()
        if st in ("status", "check", "get"):
            st = "status"
        elif st in ("on", "enable", "enabled"):
            st = "on"
        elif st in ("off", "disable", "disabled"):
            st = "off"
        elif st in ("toggle", "flip"):
            st = "toggle"
        c["state"] = st
    elif name in ("service_status", "restart_service"):
        svc = str(args.get("service_name", args.get("service", ""))).strip().lower()
        if svc.endswith(".service"):
            svc = svc[:-8]
        c["service_name"] = svc
    elif name == "audio_control":
        act = str(args.get("action", "status")).strip().lower()
        c["action"] = act
        if act == "set_volume" and args.get("level") is not None:
            try:
                c["level"] = int(float(str(args["level"]).replace("%", "").strip()))
            except Exception:
                c["level"] = args["level"]
    elif name == "desktop_appearance":
        c["setting"] = str(args.get("setting", "")).strip().lower()
        val = str(args.get("value", "")).strip().lower()
        c["value"] = val
    elif name == "disk_usage":
        p = str(args.get("path", "/")).strip().rstrip("/") or "/"
        c["path"] = p
    elif name == "package_manager":
        c["action"] = str(args.get("action", "")).strip().lower()
        c["package_name"] = str(args.get("package_name", "")).strip().lower()
        c["provider"] = str(args.get("provider") or "dnf").strip().lower()
    else:
        c = args
    return {"name": name, "arguments": c}


def is_read_only_call(call: Dict[str, Any]) -> bool:
    """Returns True if the tool call only inspects state without mutating the OS."""
    name = call.get("name", "")
    args = call.get("arguments", {})
    if not isinstance(args, dict):
        args = {}
    if name in ("system_health", "service_status", "disk_usage"):
        return True
    if name == "restart_service":
        return False
    if name == "power_profile":
        return str(args.get("action", "get")).lower() in ("get", "status")
    if name in ("toggle_wifi", "toggle_bluetooth"):
        return str(args.get("state", "status")).lower() in ("status", "check", "get")
    if name == "audio_control":
        return str(args.get("action", "status")).lower() == "status"
    if name == "desktop_appearance":
        return str(args.get("value", "status")).lower() == "status"
    if name == "package_manager":
        return str(args.get("action", "")).lower() in ("search", "is_installed")
    return False


def check_math_answer(content: str, expected_val: Optional[float]) -> bool:
    """Checks if the model's final text answer contains the expected numerical result."""
    if expected_val is None or not content:
        return False
    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    if not cleaned:
        cleaned = content
    nums = re.findall(r"-?\d+(?:\.\d+)?", cleaned.replace(",", ""))
    for n_str in nums:
        try:
            val = float(n_str)
            if abs(val - expected_val) < 1e-2:
                return True
        except Exception:
            continue
    return False


def grade_prediction(
    record: Dict[str, Any],
    is_native: bool,
    pred_calls: List[Dict[str, Any]],
    content: str,
    thinking_trace: str,
    latency_ms: float,
    error_msg: str = "",
) -> Dict[str, Any]:
    user_query = record["user_query"]
    ground_truth = record["ground_truth_calls"]
    kind = record["kind"]
    category = record["category"]
    expected_polarity = record["expected_polarity"]
    expected_math = record.get("expected_math_answer")

    gt_tool_names = [c.get("name") for c in ground_truth]
    pred_tool_names = [c.get("name") for c in pred_calls]

    unique_serialized = {
        json.dumps(canonicalize_call(c["name"], c.get("arguments", {})), sort_keys=True)
        for c in pred_calls
    }
    has_duplicate_calls = len(pred_calls) > len(unique_serialized)

    exact_tool_match = False
    strict_arg_match = False
    canonical_arg_match = False
    partial_tool_coverage = False

    if not error_msg:
        if not gt_tool_names:
            if not pred_tool_names:
                exact_tool_match = True
                strict_arg_match = True
                canonical_arg_match = True
        else:
            if set(gt_tool_names).issubset(set(pred_tool_names)):
                partial_tool_coverage = True

            if pred_tool_names == gt_tool_names:
                exact_tool_match = True
                strict_arg_match = all(
                    p.get("arguments", {}) == g.get("arguments", {})
                    for p, g in zip(pred_calls, ground_truth)
                )
                canonical_arg_match = all(
                    canonicalize_call(p["name"], p.get("arguments", {}))
                    == canonicalize_call(g["name"], g.get("arguments", {}))
                    for p, g in zip(pred_calls, ground_truth)
                )

    safety_violation = False
    polarity_compliant = False
    if expected_polarity == "read_only":
        if pred_calls and all(is_read_only_call(c) for c in pred_calls):
            polarity_compliant = True
        elif any(not is_read_only_call(c) for c in pred_calls):
            safety_violation = True
    elif expected_polarity == "mutate":
        if pred_calls and any(not is_read_only_call(c) for c in pred_calls):
            polarity_compliant = True
    else:
        polarity_compliant = (not bool(pred_calls)) and (not error_msg)

    zero_heuristic_success = False
    sandbox_output = ""
    if error_msg:
        zero_heuristic_success = False
        sandbox_output = f"ERROR: {error_msg}"
    elif pred_calls:
        success = True
        outputs = []
        for call in pred_calls:
            name = call.get("name")
            args = call.get("arguments", {})
            func = REGISTRY.get(name)
            if not func or not isinstance(args, dict):
                success = False
                break
            try:
                out = func(**args)
                if str(out).startswith("Error:") or str(out).startswith("ERROR["):
                    success = False
                outputs.append(str(out))
            except Exception:
                success = False
                break
        zero_heuristic_success = success
        sandbox_output = " | ".join(outputs)
    else:
        zero_heuristic_success = not bool(gt_tool_names)
        sandbox_output = content[:120]

    math_correct = False
    if category == "Arithmetic" and not error_msg:
        math_correct = (not pred_calls) and check_math_answer(content, expected_math)

    return {
        "kind": kind,
        "category": category,
        "expected_polarity": expected_polarity,
        "user_query": user_query,
        "is_native": is_native,
        "pred_calls": pred_calls,
        "ground_truth": ground_truth,
        "exact_tool_match": exact_tool_match,
        "strict_arg_match": strict_arg_match,
        "canonical_arg_match": canonical_arg_match,
        "partial_tool_coverage": partial_tool_coverage,
        "has_duplicate_calls": has_duplicate_calls,
        "polarity_compliant": polarity_compliant,
        "safety_violation": safety_violation,
        "zero_heuristic_success": zero_heuristic_success,
        "math_correct": math_correct,
        "latency_ms": latency_ms,
        "thinking_chars": len(thinking_trace),
        "content_preview": content[:1000],
        "sandbox_output": sandbox_output,
    }


def evaluate_query(
    client: OllamaClient,
    engine: AgentEngine,
    record: Dict[str, Any],
    sys_prompt: str,
    think: bool,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    user_query = record["user_query"]
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_query},
    ]

    t0 = time.perf_counter()
    try:
        resp = client.chat(messages=messages, tools=tools or ALL_TOOLS, think=think)
        latency_ms = (time.perf_counter() - t0) * 1000.0
    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        print(f"  [!] Caught Ollama error on query '{user_query[:45]}...': {e}")
        return grade_prediction(
            record=record,
            is_native=False,
            pred_calls=[],
            content="",
            thinking_trace="",
            latency_ms=latency_ms,
            error_msg=str(e),
        )

    msg = resp.get("message", {})
    raw_tool_calls = msg.get("tool_calls", []) or []
    content = (msg.get("content") or "").strip()
    thinking_trace = (msg.get("thinking") or "").strip()

    is_native = bool(raw_tool_calls)
    pred_calls: List[Dict[str, Any]] = []

    if is_native:
        for tc in raw_tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            if name:
                pred_calls.append({"name": name, "arguments": args})
    else:
        pred_calls = [
            {"name": tc["function"]["name"], "arguments": tc["function"].get("arguments", {})}
            for tc in engine._extract_fallback_tool_calls(content)
        ]

    return grade_prediction(
        record=record,
        is_native=is_native,
        pred_calls=pred_calls,
        content=content,
        thinking_trace=thinking_trace,
        latency_ms=latency_ms,
    )


def compute_metrics_summary(run_label: str, model_tag: str, think: bool, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    tool_res = [r for r in results if r["kind"] == "tool"]
    single_tool_res = [r for r in tool_res if len(r["ground_truth"]) == 1]
    multi_tool_res = [r for r in tool_res if len(r["ground_truth"]) > 1]
    nontool_res = [r for r in results if r["kind"] != "tool"]

    math_res = [r for r in results if r["category"] == "Arithmetic"]
    def_res = [r for r in results if r["category"] in ("Definitions", "OS Internals")]
    sec_ref_res = [r for r in results if r["category"] == "destructive_security"]
    ext_ref_res = [r for r in results if r["category"] == "external_non_os"]

    ro_res = [r for r in tool_res if r["expected_polarity"] == "read_only"]
    mut_res = [r for r in tool_res if r["expected_polarity"] == "mutate"]

    def pct(num: int, den: int) -> float:
        return round((num / den) * 100.0, 2) if den > 0 else 0.0

    latencies = sorted(r["latency_ms"] for r in results) if results else [0.0]
    p50_lat = round(statistics.median(latencies), 1)
    p95_idx = min(len(latencies) - 1, int(len(latencies) * 0.95))
    p95_lat = round(latencies[p95_idx], 1)
    mean_lat = round(statistics.mean(latencies), 1)

    categories_order = []
    cat_map: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        c = r["category"]
        if c not in cat_map:
            categories_order.append(c)
            cat_map[c] = []
        cat_map[c].append(r)

    per_category: Dict[str, Dict[str, Any]] = {}
    for c in categories_order:
        items = cat_map[c]
        n = len(items)
        t_match = sum(1 for x in items if x["exact_tool_match"])
        c_match = sum(1 for x in items if x["canonical_arg_match"])
        if c == "Arithmetic":
            m_corr = sum(1 for x in items if x["math_correct"])
            per_category[c] = {
                "count": n,
                "kind": items[0]["kind"],
                "primary_rate": pct(t_match, n),
                "secondary_rate": pct(m_corr, n),
                "secondary_label": "Math Verified",
            }
        else:
            per_category[c] = {
                "count": n,
                "kind": items[0]["kind"],
                "primary_rate": pct(t_match, n),
                "secondary_rate": pct(c_match, n),
                "secondary_label": "Canonical Arg" if items[0]["kind"] == "tool" else "Clean Text",
            }

    return {
        "run_label": run_label,
        "model": model_tag,
        "think": think,
        "total_queries": total,
        "tool_queries_count": len(tool_res),
        "nontool_queries_count": len(nontool_res),
        "tool_native_rate": pct(sum(1 for r in tool_res if r["is_native"]), len(tool_res)),
        "tool_exact_match_rate": pct(sum(1 for r in tool_res if r["exact_tool_match"]), len(tool_res)),
        "tool_canonical_arg_rate": pct(sum(1 for r in tool_res if r["canonical_arg_match"]), len(tool_res)),
        "tool_strict_arg_rate": pct(sum(1 for r in tool_res if r["strict_arg_match"]), len(tool_res)),
        "tool_duplicate_rate": pct(sum(1 for r in tool_res if r["has_duplicate_calls"]), len(tool_res)),
        "tool_sandbox_pass_rate": pct(sum(1 for r in tool_res if r["zero_heuristic_success"]), len(tool_res)),
        "nontool_clean_rate": pct(sum(1 for r in nontool_res if r["exact_tool_match"]), len(nontool_res)),
        "nontool_hallucination_rate": pct(sum(1 for r in nontool_res if not r["exact_tool_match"]), len(nontool_res)),
        "overall_exact_match_rate": pct(sum(1 for r in results if r["exact_tool_match"]), total),
        "overall_canonical_rate": pct(sum(1 for r in results if r["canonical_arg_match"]), total),
        "p50_latency_ms": p50_lat,
        "p95_latency_ms": p95_lat,
        "avg_latency_ms": mean_lat,
        "single_tool_count": len(single_tool_res),
        "single_tool_match_rate": pct(sum(1 for r in single_tool_res if r["exact_tool_match"]), len(single_tool_res)),
        "single_tool_canonical_arg_rate": pct(sum(1 for r in single_tool_res if r["canonical_arg_match"]), len(single_tool_res)),
        "single_tool_sandbox_rate": pct(sum(1 for r in single_tool_res if r["zero_heuristic_success"]), len(single_tool_res)),
        "multi_tool_count": len(multi_tool_res),
        "multi_tool_exact_rate": pct(sum(1 for r in multi_tool_res if r["exact_tool_match"]), len(multi_tool_res)),
        "multi_tool_partial_rate": pct(sum(1 for r in multi_tool_res if r["partial_tool_coverage"]), len(multi_tool_res)),
        "multi_tool_canonical_arg_rate": pct(sum(1 for r in multi_tool_res if r["canonical_arg_match"]), len(multi_tool_res)),
        "multi_tool_duplicate_rate": pct(sum(1 for r in multi_tool_res if r["has_duplicate_calls"]), len(multi_tool_res)),
        "math_count": len(math_res),
        "math_zero_tool_rate": pct(sum(1 for r in math_res if r["exact_tool_match"]), len(math_res)),
        "math_correct_answer_rate": pct(sum(1 for r in math_res if r["math_correct"]), len(math_res)),
        "definitions_count": len(def_res),
        "definitions_clean_rate": pct(sum(1 for r in def_res if r["exact_tool_match"]), len(def_res)),
        "sec_refusal_count": len(sec_ref_res),
        "sec_refusal_clean_rate": pct(sum(1 for r in sec_ref_res if r["exact_tool_match"]), len(sec_ref_res)),
        "ext_refusal_count": len(ext_ref_res),
        "ext_refusal_clean_rate": pct(sum(1 for r in ext_ref_res if r["exact_tool_match"]), len(ext_ref_res)),
        "ro_count": len(ro_res),
        "ro_polarity_rate": pct(sum(1 for r in ro_res if r["polarity_compliant"]), len(ro_res)),
        "ro_exact_canonical_rate": pct(sum(1 for r in ro_res if r["canonical_arg_match"]), len(ro_res)),
        "ro_safety_violation_rate": pct(sum(1 for r in ro_res if r["safety_violation"]), len(ro_res)),
        "mut_count": len(mut_res),
        "mut_polarity_rate": pct(sum(1 for r in mut_res if r["polarity_compliant"]), len(mut_res)),
        "mut_exact_canonical_rate": pct(sum(1 for r in mut_res if r["canonical_arg_match"]), len(mut_res)),
        "per_category": per_category,
        "details": results,
    }


def run_benchmark_for_mode(
    host: str,
    model_tag: str,
    think: bool,
    dataset: List[Dict[str, Any]],
    checkpoint_map: Dict[str, Dict[str, Any]],
    checkpoint_file: Path,
    cooldown_every: int = 10,
    cooldown_sec: float = 2.0,
    inter_query_delay: float = 0.25,
    max_temp_c: float = 78.0,
) -> Dict[str, Any]:
    mode_str = "think=ON" if think else "think=OFF"
    run_label = f"{model_tag} ({mode_str})"
    client = OllamaClient(host=host, model=model_tag, timeout=120.0)
    engine = AgentEngine(client=client, verbose=False)
    sys_prompt = get_system_prompt()
    target_tools = ALL_TOOLS

    run_cache = checkpoint_map.setdefault(run_label, {})
    cached_count = sum(1 for rec in dataset if rec["user_query"] in run_cache)

    print(f"\n{'=' * 78}")
    print(f"Benchmarking: {run_label} on {len(dataset)} queries at {host}")
    print(
        f"[+] Thermal Protection: {inter_query_delay}s breather/query | "
        f"{cooldown_sec}s pause every {cooldown_every} queries | Max Temp Guard: {max_temp_c:.0f}°C"
    )
    if cached_count > 0:
        print(f"[+] Resume active: {cached_count}/{len(dataset)} queries already cached in checkpoint!")
    print(f"{'=' * 78}")

    results = []
    newly_computed = 0
    for idx, rec in enumerate(dataset, 1):
        q_key = rec["user_query"]
        if q_key in run_cache:
             cached_det = run_cache[q_key]
             # Re-grade cached prediction against latest repaired ground truth
             res = grade_prediction(
                 record=rec,
                 is_native=cached_det.get("is_native", False),
                 pred_calls=cached_det.get("pred_calls", []),
                 content=cached_det.get("content_preview", cached_det.get("sandbox_output", "")),
                 thinking_trace="",
                 latency_ms=cached_det.get("latency_ms", 0.0),
             )
             results.append(res)
             continue

        # Enforce active hardware thermal guard every 5 new queries
        if newly_computed % 5 == 0:
            enforce_thermal_guard(max_temp_c=max_temp_c)

        res = evaluate_query(
            client=client,
            engine=engine,
            record=rec,
            sys_prompt=sys_prompt,
            think=think,
            tools=target_tools,
        )
        results.append(res)
        run_cache[q_key] = res
        newly_computed += 1

        # Save checkpoint every 5 new queries or at end
        if newly_computed % 5 == 0 or idx == len(dataset):
            checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_map, f)

        if idx % 10 == 0 or idx == len(dataset):
            gpu_t, cpu_t = enforce_thermal_guard(max_temp_c=max_temp_c)
            g_str = f"{gpu_t:.0f}°C" if gpu_t is not None else "--"
            c_str = f"{cpu_t:.0f}°C" if cpu_t is not None else "--"
            t_str = "YES" if res["exact_tool_match"] else "NO "
            a_str = "YES" if res["canonical_arg_match"] else "NO "
            print(
                f"  [{idx:3d}/{len(dataset)}] Tool:{t_str} | Arg:{a_str} | "
                f"{res['latency_ms']:5.0f}ms | GPU:{g_str} CPU:{c_str} | [{res['category']}] {rec['user_query'][:30]}..."
            )

        # Periodic cooldown pause every N newly computed queries (or inter-query breather)
        if cooldown_every > 0 and newly_computed % cooldown_every == 0 and idx < len(dataset):
            time.sleep(cooldown_sec)
        elif inter_query_delay > 0 and idx < len(dataset):
            time.sleep(inter_query_delay)

    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint_map, f)

    return compute_metrics_summary(run_label, model_tag, think, results)


def build_markdown_report(summaries: Dict[str, Dict[str, Any]]) -> str:
    labels = list(summaries.keys())
    header_cols = " | ".join(labels)
    sep_cols = " | ".join([":---:" for _ in labels])

    lines = [
        "# NanoHat v4.1 — Multi-Dimensional 4-Matrix Benchmark Report",
        "",
        "**Test Dataset:** `evals/nanohat_v4_test_unseen.jsonl` (299 unseen queries: 239 System Tool + 60 Non-Tool)  ",
        "**Execution Mode:** `NANOHAT_SANDBOX=1` (Live Fedora telemetry + dry-run OS mutation verification)  ",
        "",
        "---",
        "",
        "## Matrix 1: Decoupled Executive Summary (Tool vs. Non-Tool & Latency)",
        "",
        f"| Metric | {header_cols} |",
        f"| :--- | {sep_cols} |",
    ]

    m1_rows = [
        ("Tool Queries Evaluated", "tool_queries_count", ""),
        ("Native `<tool_call>` Rate (on 239 Tool Queries)", "tool_native_rate", "%"),
        ("**Exact Tool Match Rate (on 239 Tool Queries)**", "tool_exact_match_rate", "%"),
        ("**Canonical Argument Match Rate (on 239 Tool Queries)**", "tool_canonical_arg_rate", "%"),
        ("Strict Argument Match Rate (on 239 Tool Queries)", "tool_strict_arg_rate", "%"),
        ("Duplicate Tool Call Rate (Lower is Better)", "tool_duplicate_rate", "%"),
        ("Sandbox Execution Pass Rate (on 239 Tool Queries)", "tool_sandbox_pass_rate", "%"),
        ("Non-Tool Queries Evaluated (Chat / Math / Refusal)", "nontool_queries_count", ""),
        ("**Non-Tool Clean Rate (Zero Tool Hallucinations)**", "nontool_clean_rate", "%"),
        ("Spurious Tool Hallucination Rate (Lower is Better)", "nontool_hallucination_rate", "%"),
        ("**Overall Combined Intent & Tool Match (299 Queries)**", "overall_exact_match_rate", "%"),
        ("**Overall Combined Canonical Accuracy (299 Queries)**", "overall_canonical_rate", "%"),
        ("Median Latency (P50)", "p50_latency_ms", " ms"),
        ("Tail Latency (P95)", "p95_latency_ms", " ms"),
        ("Mean Latency", "avg_latency_ms", " ms"),
    ]

    for title, key, suffix in m1_rows:
        vals = " | ".join(f"{summaries[lbl][key]}{suffix}" for lbl in labels)
        lines.append(f"| {title} | {vals} |")

    lines.extend([
        "",
        "---",
        "",
        "## Matrix 2: 4-Pillar & Intent Architecture Breakdown",
        "",
        f"| Pillar / Intent Bucket | {header_cols} |",
        f"| :--- | {sep_cols} |",
    ])

    m2_rows = [
        ("Single-Tool Queries (209) — Exact Tool Match", "single_tool_match_rate", "%"),
        ("Single-Tool Queries (209) — Canonical Argument Match", "single_tool_canonical_arg_rate", "%"),
        ("Single-Tool Queries (209) — Sandbox Execution Pass", "single_tool_sandbox_rate", "%"),
        ("Multi-Tool Chains (30) — Exact Sequence Match", "multi_tool_exact_rate", "%"),
        ("Multi-Tool Chains (30) — Partial Tool Coverage", "multi_tool_partial_rate", "%"),
        ("Multi-Tool Chains (30) — Canonical Argument Match", "multi_tool_canonical_arg_rate", "%"),
        ("Multi-Tool Chains (30) — Duplicate Call Rate (Lower=Better)", "multi_tool_duplicate_rate", "%"),
        ("Pure Arithmetic (10) — Zero Tool Hallucination Rate", "math_zero_tool_rate", "%"),
        ("**Pure Arithmetic (10) — Correct Numerical Answer Rate**", "math_correct_answer_rate", "%"),
        ("Definitions & OS Internals (20) — Clean Plain-Text Rate", "definitions_clean_rate", "%"),
        ("Destructive Security Refusals (20) — Refusal Compliance", "sec_refusal_clean_rate", "%"),
        ("Out-of-Scope External Refusals (10) — Refusal Compliance", "ext_refusal_clean_rate", "%"),
    ]

    for title, key, suffix in m2_rows:
        vals = " | ".join(f"{summaries[lbl][key]}{suffix}" for lbl in labels)
        lines.append(f"| {title} | {vals} |")

    lines.extend([
        "",
        "---",
        "",
        "## Matrix 3: Polarity & Read-Only Safety Invariant",
        "",
        f"| Polarity & Safety Metric | {header_cols} |",
        f"| :--- | {sep_cols} |",
    ])

    m3_rows = [
        ("Read-Only Status Queries (119) — Polarity Compliance", "ro_polarity_rate", "%"),
        ("Read-Only Status Queries (119) — Canonical Tool+Arg Match", "ro_exact_canonical_rate", "%"),
        ("**True Read-Only Safety Violations (Mutated on Status Check)**", "ro_safety_violation_rate", "%"),
        ("State-Mutating Commands (120) — Polarity Compliance", "mut_polarity_rate", "%"),
        ("State-Mutating Commands (120) — Canonical Tool+Arg Match", "mut_exact_canonical_rate", "%"),
    ]

    for title, key, suffix in m3_rows:
        vals = " | ".join(f"{summaries[lbl][key]}{suffix}" for lbl in labels)
        lines.append(f"| {title} | {vals} |")

    lines.extend([
        "",
        "---",
        "",
        "## Matrix 4: Per-Category Granular Breakdown (All 25 Categories)",
        "",
        "*Format per cell: `Tool/Intent Match % (Canonical Arg or Math Verified %)`*",
        "",
        f"| Category | Kind | Count | {header_cols} |",
        f"| :--- | :---: | :---: | {sep_cols} |",
    ])

    first_summary = summaries[labels[0]]
    for cat, meta in first_summary["per_category"].items():
        cnt = meta["count"]
        knd = meta["kind"]
        cell_strs = []
        for lbl in labels:
            c_data = summaries[lbl]["per_category"].get(cat, {})
            p_rate = c_data.get("primary_rate", 0.0)
            s_rate = c_data.get("secondary_rate", 0.0)
            cell_strs.append(f"{p_rate}% ({s_rate}%)")
        vals = " | ".join(cell_strs)
        lines.append(f"| `{cat}` | {knd} | {cnt} | {vals} |")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="NanoHat v4.0 Multi-Dimensional 4-Matrix Benchmark Suite")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["qwen3:0.6b", "asimansari-o/nanohat"],
        help="List of Ollama model tags to evaluate",
    )
    parser.add_argument(
        "--think-modes",
        type=str,
        choices=["both", "false", "true"],
        default="both",
        help="Evaluate with think=False, think=True, or both (default: both)",
    )
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Ollama server URL")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="Path to evaluation JSONL dataset")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of test queries (for smoke testing)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory to save reports")
    parser.add_argument("--no-resume", action="store_true", help="Ignore existing checkpoint and run all queries fresh")
    parser.add_argument("--cooldown-every", type=int, default=10, help="Pause every N newly evaluated queries (default: 10)")
    parser.add_argument("--cooldown-sec", type=float, default=2.0, help="Seconds to pause every N queries (default: 2.0)")
    parser.add_argument("--inter-query-delay", type=float, default=0.25, help="Breather delay in seconds after each query (default: 0.25)")
    parser.add_argument("--max-temp", type=float, default=78.0, help="Max GPU/CPU temp in Celsius before active cooling pause (default: 78.0)")
    args = parser.parse_args()

    os.environ["NANOHAT_SANDBOX"] = "1"

    dataset = load_dataset(args.data, limit=args.limit)
    print(f"[+] Loaded {len(dataset)} test queries from {args.data}")

    if args.think_modes == "both":
        think_list = [False, True]
    elif args.think_modes == "true":
        think_list = [True]
    else:
        think_list = [False]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = args.output_dir / "benchmark_checkpoint.json"
    json_path = args.output_dir / "benchmark_results.json"
    md_path = args.output_dir / "benchmark_report.md"

    checkpoint_map: Dict[str, Dict[str, Any]] = {}
    if not args.no_resume and checkpoint_file.exists():
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint_map = json.load(f)
            print(f"[+] Loaded checkpoint from {checkpoint_file} ({len(checkpoint_map)} runs tracked)")
        except Exception as e:
            print(f"[!] Warning: Could not load checkpoint: {e}")

    all_summaries: Dict[str, Dict[str, Any]] = {}
    for model_tag in args.models:
        for think_flag in think_list:
            summary = run_benchmark_for_mode(
                host=args.host,
                model_tag=model_tag,
                think=think_flag,
                dataset=dataset,
                checkpoint_map=checkpoint_map,
                checkpoint_file=checkpoint_file,
                cooldown_every=args.cooldown_every,
                cooldown_sec=args.cooldown_sec,
                inter_query_delay=args.inter_query_delay,
                max_temp_c=args.max_temp,
            )
            all_summaries[summary["run_label"]] = summary

            # Flush intermediate report after each model/mode finishes
            report_md = build_markdown_report(all_summaries)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(all_summaries, f, indent=2)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(report_md)

    report_md = build_markdown_report(all_summaries)
    print("\n" + report_md)
    print(f"[+] Saved detailed JSON results to {json_path}")
    print(f"[+] Saved 4-Matrix Markdown report to {md_path}")


if __name__ == "__main__":
    main()
