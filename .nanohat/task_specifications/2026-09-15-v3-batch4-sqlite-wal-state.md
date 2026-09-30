---
title: "NanoHat v3.0.0 Batch 4: SQLite WAL Persistent State Engine (Memory & Tasks)"
date: 2026-09-15
branch: "v3-dev"
status: "#task/completed"
tags:
  - task/completed
  - milestone/v3.0.0
  - pillar/memory
  - pillar/tasks
related:
  - "[[00_INDEX]]"
  - "[[NANOHAT_MASTER_SPECIFICATION]]"
  - "[[ADR-006-Sub-1B-Dynamic-Tool-Gating-and-Dynamic-Prompts]]"
---

# NanoHat v3.0.0 Batch 4: SQLite WAL Persistent State Engine (Memory & Tasks)

- **Branch:** `v3-dev`
- **Date:** 2026-09-15
- **Status:** `#task/completed`
- **Epic / Milestone:** `[[00_INDEX]]`

---

## 🎯 Objective & Architecture

Implement a concurrency-safe, lock-free persistent state engine using **SQLite in WAL mode** (`~/.local/state/nanohat/state.db`) to power **Pillar 2 (Background Tasks)** and **Pillar 4 (User Memory & Preferences)**:

1. **User Memory (4 Units)**:
   - `memory_set(key: str, value: str)`: Persist key-value information.
   - `memory_get(key: str)`: Retrieve persisted information by key.
   - `memory_list()`: List all active keys and values.
   - `memory_delete(key: str)`: Remove a key from memory.

2. **Scheduled Tasks (3 Units)**:
   - `task_add(title: str, due_time: str, notify_minutes_before: int = 0)`: Schedule an alert/task.
   - `task_list(status: str = "pending")`: Inspect pending or completed tasks.
   - `task_cancel(task_id: int)`: Mark a task as cancelled.

---

## 🗄️ Database Specification

### Storage Location
* Respects XDG Base Directory specification:
  `os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state")) / "nanohat" / "state.db"`
* Auto-creates parent directories with `0700` permissions.

### Concurrency & WAL Pragmas
```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
```
* **Why WAL?**: Allows simultaneous non-blocking reads from multiple CLI invocations while the background daemon writes updates.

### Relational Schema
```sql
CREATE TABLE IF NOT EXISTS user_memory (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    due_time TEXT NOT NULL,
    notify_minutes_before INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🧭 Dynamic Tool Gating Integration

To maintain FunctionGemma 270M's strict $\le 3$ tool cognitive budget:
* **Memory Cluster**:
  - Trigger: `\b(remember|memory|recall|forget|note|preference)\b`
  - Gated Tools: `[memory_set, memory_get, memory_list, memory_delete]` (routed dynamically: `set`/`remember` $\rightarrow$ `memory_set`, `recall`/`get` $\rightarrow$ `memory_get`, `forget`/`delete` $\rightarrow$ `memory_delete`, `list`/`notes` $\rightarrow$ `memory_list`).
* **Task Cluster**:
  - Trigger: `\b(remind|reminder|task|schedule|alarm|todo)\b`
  - Gated Tools: `[task_add, task_list, task_cancel]` (routed dynamically: `remind`/`add` $\rightarrow$ `task_add`, `list`/`tasks` $\rightarrow$ `task_list`, `cancel`/`remove` $\rightarrow$ `task_cancel`).

---

## 🧪 Verification Strategy (100% Mocked / Isolated)
* Test suite `tests/test_phase2_batch4.py` uses temporary SQLite in-memory or tempfile databases (`:memory:` or `tempfile.NamedTemporaryFile`).
* Zero pollution of the host user's actual `~/.local/state/nanohat/state.db` during automated testing.

---

## 🛡️ Edge-Case Hardening & Sub-1B Cognitive Disambiguation
Following manual CLI testing on Fedora 44, 5 edge cases were diagnosed and resolved:
1. **Key Normalization (`_normalize_key`)**:
   - Lowercases, trims, and collapses `[\s\-]+` and `_+` to `_`.
   - Allows keys like `favorite_ distro` to match lookups for `favorite_distro`, `favorite distro`, and `favorite-distro`.
   - Includes fallback scan for legacy unnormalized keys already in SQLite.
2. **Service Intent Iteration (`finditer`)**:
   - Switched `_is_service_query` from `search` to `finditer`. Prevents leading stopword matches (e.g. `is the`) from swallowing target service queries like `status of java`.
3. **RAM & CPU Hardware Isolation**:
   - Disambiguated `system_health` from `power_profile`. Queries for RAM or CPU strictly exclude `power_profile` from the active schema to eliminate 270M tool confusion.
4. **User Identity & Memory Statements**:
   - Added `RE_MEMORY_SET_STATEMENT` (`my ... is ...`, `i am ...`) and typo-tolerant remember patterns (`\bremeb[a-z]*\b`).
   - Extended `RE_MEMORY_QUERY` to support standalone identity lookups (`Who am I?`, `whoami`).
5. **Tool Return Syntax for Sub-1B Synthesis**:
   - Refined `memory_get` to output `{key} is {value}.` instead of `Memory '{key}': {value}`, ensuring FunctionGemma 270M synthesizes the factual value directly rather than emitting canned acknowledgments.
6. **Smart Topic Fallback (`_match_key`)**:
   - Handles prefix, suffix, and `_name` variations (e.g., query `pet` resolves stored `pet_name`, query `editor` resolves stored `favorite_editor`).
7. **Multi-Word Identity Statements & Colloquial Regex**:
   - Upgraded `RE_MEMORY_SET_STATEMENT` to `r"\b((my|mah)\s+([a-zA-Z_\-]+\s+){1,4}is|i\s+am|call\s+me|i\s+like|i\s+prefer)\b"`, capturing multi-word subjects (`"My pet name is Nimo"`, `"Mah pet name is Nimo"`).
8. **Privacy De-Identification & Generic Examples**:
   - Fully stripped user personal names from prompts, schemas, and test assertions. Standardized on generic examples (`favorite_distro: fedora`, `pet_name: milo`, `editor: neovim`).

