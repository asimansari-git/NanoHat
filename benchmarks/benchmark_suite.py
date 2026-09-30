"""
benchmark_suite.py — 80 curated benchmark queries across 4 difficulty tiers for NanoHat v3.1.0.

Tiers:
  - Tier 1 (Direct, 20 cases): canonical user queries matching standard vocabulary
  - Tier 2 (Slang & Typos, 20 cases): noisy ASR, phonetic spelling, abbreviations
  - Tier 3 (Implicit Diagnostics, 20 cases): indirect hardware, thermal, and OS requests
  - Tier 4 (Adversarial & Edge, 20 cases): polysemy, multi-topic, and negative constraints
"""

BENCHMARK_CASES = [
    # =========================================================================
    # Tier 1: Direct / Canonical Queries (20)
    # =========================================================================
    {"query": "What is 45 * 12?", "expected": ["calculator"], "tier": "direct"},
    {"query": "Calculate 7 + 7 * 18", "expected": ["calculator"], "tier": "direct"},
    {"query": "What is my current RAM usage?", "expected": ["system_health"], "tier": "direct"},
    {"query": "What is my battery level?", "expected": ["system_health"], "tier": "direct"},
    {"query": "Check system health", "expected": ["system_health"], "tier": "direct"},
    {"query": "Switch power profile to performance", "expected": ["power_profile"], "tier": "direct"},
    {"query": "Get active power profile", "expected": ["power_profile"], "tier": "direct"},
    {"query": "What time is it right now?", "expected": ["get_datetime"], "tier": "direct"},
    {"query": "What is today's date?", "expected": ["get_datetime"], "tier": "direct"},
    {"query": "Empty the trash bin", "expected": ["empty_trash"], "tier": "direct"},
    {"query": "Turn off wifi", "expected": ["toggle_wifi"], "tier": "direct"},
    {"query": "Check wifi radio status", "expected": ["toggle_wifi"], "tier": "direct"},
    {"query": "Is bluetooth powered on?", "expected": ["toggle_bluetooth"], "tier": "direct"},
    {"query": "Disable bluetooth radio", "expected": ["toggle_bluetooth"], "tier": "direct"},
    {"query": "Is pipewire running?", "expected": ["service_status"], "tier": "direct"},
    {"query": "Restart pipewire service", "expected": ["restart_service"], "tier": "direct"},
    {"query": "Remember that my favorite editor is neovim", "expected": ["memory_set"], "tier": "direct"},
    {"query": "What is my favorite editor?", "expected": ["memory_get"], "tier": "direct"},
    {"query": "Remind me to stretch at 5pm", "expected": ["task_add"], "tier": "direct"},
    {"query": "Show my scheduled tasks", "expected": ["task_list"], "tier": "direct"},

    # =========================================================================
    # Tier 2: Slang, Phonetic Variants & Typos (20)
    # =========================================================================
    {"query": "clac 394 * 22", "expected": ["calculator"], "tier": "slang_typo"},
    {"query": "eval (100 / 4) + 25", "expected": ["calculator"], "tier": "slang_typo"},
    {"query": "how mch ram lef on my rig", "expected": ["system_health"], "tier": "slang_typo"},
    {"query": "bttry pct remaining", "expected": ["system_health"], "tier": "slang_typo"},
    {"query": "What is my betery status?", "expected": ["system_health"], "tier": "slang_typo"},
    {"query": "wify off plz", "expected": ["toggle_wifi"], "tier": "slang_typo"},
    {"query": "is my blue-teeth on?", "expected": ["toggle_bluetooth"], "tier": "slang_typo"},
    {"query": "cut the bt radio", "expected": ["toggle_bluetooth"], "tier": "slang_typo"},
    {"query": "bounce wireplumber daemon", "expected": ["restart_service"], "tier": "slang_typo"},
    {"query": "is ollama svr dead or up", "expected": ["service_status"], "tier": "slang_typo"},
    {"query": "mah pet name is Nimo", "expected": ["memory_set"], "tier": "slang_typo"},
    {"query": "remeber my favorite color is teal", "expected": ["memory_set"], "tier": "slang_typo"},
    {"query": "whoami in your brain", "expected": ["memory_get"], "tier": "slang_typo"},
    {"query": "dump all stored notes", "expected": ["memory_list"], "tier": "slang_typo"},
    {"query": "yeet the trash can", "expected": ["empty_trash"], "tier": "slang_typo"},
    {"query": "drop task #3", "expected": ["task_cancel"], "tier": "slang_typo"},
    {"query": "tell me current clock right now", "expected": ["get_datetime"], "tier": "slang_typo"},
    {"query": "fire up firefox browser", "expected": ["launch_app"], "tier": "slang_typo"},
    {"query": "open up calc app", "expected": ["launch_app"], "tier": "slang_typo"},
    {"query": "battery juice level", "expected": ["system_health"], "tier": "slang_typo"},

    # =========================================================================
    # Tier 3: Implicit Intent & Hardware Diagnostics (20)
    # =========================================================================
    {"query": "Why my laptop is heating up?", "expected": ["system_health"], "tier": "implicit"},
    {"query": "My laptop feels burning hot on my lap", "expected": ["system_health"], "tier": "implicit"},
    {"query": "Fans are screaming at full blast", "expected": ["system_health"], "tier": "implicit"},
    {"query": "Why is my computer lagging so badly right now?", "expected": ["system_health"], "tier": "implicit"},
    {"query": "Do I have enough free memory to launch a Docker container?", "expected": ["system_health"], "tier": "implicit"},
    {"query": "Is my machine about to run out of battery power?", "expected": ["system_health"], "tier": "implicit"},
    {"query": "I need maximum CPU power for compilation", "expected": ["power_profile"], "tier": "implicit"},
    {"query": "Save my battery life while I travel", "expected": ["power_profile"], "tier": "implicit"},
    {"query": "I am unable to browse websites or access internet", "expected": ["toggle_wifi"], "tier": "implicit"},
    {"query": "My wireless mouse stopped responding completely", "expected": ["toggle_bluetooth"], "tier": "implicit"},
    {"query": "Audio just glitched out and stopped playing sound", "expected": ["restart_service"], "tier": "implicit"},
    {"query": "Check if our local LLM background engine is active", "expected": ["service_status"], "tier": "implicit"},
    {"query": "Free up some disk storage immediately", "expected": ["empty_trash"], "tier": "implicit"},
    {"query": "Keep in mind that I prefer Python 3.14 over 3.10", "expected": ["memory_set"], "tier": "implicit"},
    {"query": "Recall what we decided about my project directory", "expected": ["memory_get"], "tier": "implicit"},
    {"query": "Remind me before my flight leaves at noon tomorrow", "expected": ["task_add"], "tier": "implicit"},
    {"query": "What commitments do I have pending on my agenda?", "expected": ["task_list"], "tier": "implicit"},
    {"query": "Cancel my afternoon dentist appointment reminder", "expected": ["task_cancel"], "tier": "implicit"},
    {"query": "Start the web browser so I can look up docs", "expected": ["launch_app"], "tier": "implicit"},
    {"query": "How many hours and minutes until midnight?", "expected": ["get_datetime"], "tier": "implicit"},

    # =========================================================================
    # Tier 4: Adversarial, Polysemy & Negative Constraints (20)
    # =========================================================================
    {"query": "What is my memory usage? (not my personal memory)", "expected": ["system_health"], "tier": "adversarial"},
    {"query": "Remember that 45 * 12 is my secret code", "expected": ["memory_set"], "tier": "adversarial"},
    {"query": "Calculate my RAM requirement: 8 * 1024", "expected": ["calculator"], "tier": "adversarial"},
    {"query": "Launch the calculator program, do not evaluate math", "expected": ["launch_app"], "tier": "adversarial"},
    {"query": "Check wireplumber status without restarting it", "expected": ["service_status"], "tier": "adversarial"},
    {"query": "Do you remember the wifi password I gave you earlier?", "expected": ["memory_get"], "tier": "adversarial"},
    {"query": "Store a note: my wifi router name is Orbit5", "expected": ["memory_set"], "tier": "adversarial"},
    {"query": "What time does my upcoming task expire?", "expected": ["task_list"], "tier": "adversarial"},
    {"query": "Tell me what date I set the reminder for", "expected": ["task_list"], "tier": "adversarial"},
    {"query": "Forget all about my old bluetooth headset", "expected": ["memory_delete"], "tier": "adversarial"},
    {"query": "Is pipewire service active right now at this time?", "expected": ["service_status"], "tier": "adversarial"},
    {"query": "Compute 15 percent tip on a 85 dollar dinner", "expected": ["calculator"], "tier": "adversarial"},
    {"query": "How hot is my processor core 0?", "expected": ["system_health"], "tier": "adversarial"},
    {"query": "Clear all rubbish from my desktop wastebin", "expected": ["empty_trash"], "tier": "adversarial"},
    {"query": "Switch power profile to power-saver because battery is low", "expected": ["power_profile"], "tier": "adversarial"},
    {"query": "I am Asim, please keep this in mind", "expected": ["memory_set"], "tier": "adversarial"},
    {"query": "Display every preference you currently have saved", "expected": ["memory_list"], "tier": "adversarial"},
    {"query": "Stop reminder #4 immediately", "expected": ["task_cancel"], "tier": "adversarial"},
    {"query": "Open terminal window", "expected": ["launch_app"], "tier": "adversarial"},
    {"query": "What day of the week was 2026-09-20?", "expected": ["get_datetime"], "tier": "adversarial"},
]
