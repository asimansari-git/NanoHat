"""
precompute_tool_embeddings.py — Precomputes static 384-dimensional vector embeddings
for all 17 NanoHat v3.1.0 tools using BGE-small-en-v1.5.

Precomputes embeddings at build/setup time so inference incurs zero embedding overhead
for the tool catalog.

Outputs:
  - runtime/tool_embeddings.npy (N_aspects x 384 float32 matrix)
  - runtime/tool_metadata.json (tool mapping and aspect metadata)
"""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_EMBEDDINGS = PROJECT_ROOT / "runtime" / "tool_embeddings.npy"
OUTPUT_METADATA = PROJECT_ROOT / "runtime" / "tool_metadata.json"

TOOL_ASPECTS: dict[str, list[str]] = {
    "calculator": [
        "Calculate math expression: evaluate arithmetic, 45 * 12, 7+7*18, division, multiplication, sum, subtraction, percentages, math calculation.",
        "Solve math equation, calculate tip, compute numbers, calculate arithmetic, compute 100/4, math problem.",
    ],
    "system_health": [
        "Check battery status, what is my battery level, battery percentage, battery health, battery charging, betery status, is battery low, battery juice.",
        "Check current RAM usage, memory status, free RAM, memory usage percentage, physical RAM available, swap memory.",
        "Check CPU usage, CPU utilization percentage, why is my laptop heating up, laptop hot, processor load, overheating thermals, fan screaming.",
        "Overall system health check, hardware telemetry, check system resources, system diagnostics, laptop performance.",
    ],
    "power_profile": [
        "Get or set power profile: switch power profile to performance, power saver, balanced mode, powerprofilesctl.",
        "Change battery saving profile, energy saver mode, performance mode, system power management.",
    ],
    "get_datetime": [
        "What time is it right now? Current time, clock status, current hour and minute, timezone.",
        "What is the date today? Current date, day of the week, calendar date, today's date, what day is today.",
    ],
    "empty_trash": [
        "Empty the trash bin, clear trash, purge recycle bin, empty wastebasket, clean out junk to free disk space.",
        "Wipe recycling bin, purge items from desktop trash, clean rubbish, empty trash can.",
    ],
    "toggle_wifi": [
        "What is wifi status? Is wifi on or off? Check wireless network connection, wlan status.",
        "Turn on wifi, turn off wifi, enable wifi, disable wifi, toggle wifi radio, switch wireless network.",
    ],
    "toggle_bluetooth": [
        "What is bluetooth status? Is bluetooth powered on or off? Check bluetooth radio connection.",
        "Turn on bluetooth, turn off bluetooth, enable bluetooth, disable bluetooth, toggle bluetooth power, pair bluetooth.",
    ],
    "service_status": [
        "Check status of service: is pipewire running, is ollama active, check wireplumber status, is docker daemon active.",
        "Systemd unit status, service state, check if daemon is running, failed, dead, or active.",
    ],
    "restart_service": [
        "Restart service: restart pipewire, restart wireplumber, bounce ollama service, reload daemon.",
        "Reboot service, bounce audio daemon, restart allowlisted systemd user unit.",
    ],
    "memory_set": [
        "Remember that my favorite editor is neovim, my name is Milo, save preference to memory, store personal fact.",
        "Save note in user memory, remember my pet name, store information, keep note, yaad rakhna, recuerda.",
        "I prefer python over rust, I like neovim, store preference statement, remember my preference, personal choice.",
    ],
    "memory_get": [
        "What is my name? What is my favorite editor? Who am I? Recall my preference from memory.",
        "Get stored note, fetch memory by key, what did I tell you about my distro, do you recall my editor.",
    ],
    "memory_list": [
        "List all memories, show all saved notes, display stored user preferences, view memory entries.",
        "Show everything you remember, dump user memory, display saved facts and notes.",
    ],
    "memory_delete": [
        "Forget my favorite editor, delete memory for key, remove stored preference, clear note.",
        "Forget note, erase memory, delete user memory entry, bhool jao, olvida.",
    ],
    "task_add": [
        "Remind me to stretch at 5pm, add task buy groceries, schedule reminder for tomorrow, new todo item.",
        "Set alarm, schedule meeting, create new appointment, remind me to call doctor, add scheduled task.",
    ],
    "task_list": [
        "List scheduled tasks, show pending reminders, display todo list, view upcoming appointments.",
        "What are my tasks for today, show my reminders, check pending tasks, display scheduled alerts.",
    ],
    "task_cancel": [
        "Cancel task by ID, remove scheduled reminder, drop task #1, delete appointment, finish task.",
        "Cancel reminder, stop task, remove todo item by id, drop scheduled reminder.",
    ],
    "launch_app": [
        "Launch application: open firefox, start calculator, launch terminal, open file manager, run code editor.",
        "Open app, fire up program, start browser, open nautilus, launch vlc.",
    ],
}


def find_model_path() -> str:
    env_path = os.environ.get("NANO_EMBEDDING_MODEL_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    candidates = glob.glob(os.path.expanduser("~/.cache/huggingface/hub/models--unsloth--bge-small-en-v1.5/snapshots/*"))
    if candidates:
        return candidates[0]

    return "unsloth/bge-small-en-v1.5"


def precompute():
    model_path = find_model_path()
    print(f"[precompute] Loading embedding model from: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModel.from_pretrained(model_path, dtype=torch.float32)
    model.eval()

    aspect_texts: list[str] = []
    aspect_tools: list[str] = []
    tool_names = sorted(TOOL_ASPECTS.keys())

    for tool_name in tool_names:
        for text in TOOL_ASPECTS[tool_name]:
            aspect_texts.append(text)
            aspect_tools.append(tool_name)

    print(f"[precompute] Embedding {len(aspect_texts)} aspects across {len(tool_names)} tools...")
    inputs = tokenizer(aspect_texts, padding=True, truncation=True, max_length=128, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        cls_embeddings = outputs.last_hidden_state[:, 0]
        normed = torch.nn.functional.normalize(cls_embeddings, p=2, dim=1)

    embeddings_np = normed.cpu().numpy().astype(np.float32)
    print(f"[precompute] Generated embeddings shape: {embeddings_np.shape} (dtype: {embeddings_np.dtype})")

    OUTPUT_EMBEDDINGS.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT_EMBEDDINGS, embeddings_np)
    print(f"[precompute] Saved precomputed embeddings to: {OUTPUT_EMBEDDINGS} ({os.path.getsize(OUTPUT_EMBEDDINGS)} bytes)")

    metadata = {
        "model": model_path,
        "dimension": int(embeddings_np.shape[1]),
        "tool_count": len(tool_names),
        "aspect_count": len(aspect_texts),
        "tools": tool_names,
        "aspect_tools": aspect_tools,
    }
    with open(OUTPUT_METADATA, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[precompute] Saved metadata to: {OUTPUT_METADATA}")


if __name__ == "__main__":
    precompute()
