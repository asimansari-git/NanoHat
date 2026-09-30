"""
semantic_router.py — Bi-encoder semantic tool router and dynamic tool gater for NanoHat v3.1.0.

Provides dense semantic similarity tool retrieval using precomputed aspect vectors from
BGE-small-en-v1.5 combined with a micro-query fast-path for instantaneous latency.

Compatible with the standard NanoHat router interface:
    route_tools(query, all_tools, max_tools=4, history=None) -> List[Dict]
"""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EMBEDDINGS = PROJECT_ROOT / "runtime" / "tool_embeddings.npy"
DEFAULT_METADATA = PROJECT_ROOT / "runtime" / "tool_metadata.json"
FALLBACK_TOOL_NAMES = ["system_health", "get_datetime", "calculator"]

# Fast-path compiled patterns for instantaneous micro-query resolution (<0.05ms)
_FASTPATH_PATTERNS = [
    # Pure arithmetic: e.g. "45 * 12", "7+7*18", "100 / 4"
    (re.compile(r"^\s*(?:calculate|evaluate|calc|math)?\s*[\(\d\.\s]+[\+\-\*\/\^\%][\(\)\d\.\s\+\-\*\/\^\%]*\s*$", re.I), ["calculator"]),
    # Direct single-word or simple date/time query
    (re.compile(r"^\s*(?:time|date|clock|what time is it|current time|what is the time|current date|what day is it today)(?:\s+right now)?\??\s*$", re.I), ["get_datetime"]),
    # Direct battery query or common typo
    (re.compile(r"^\s*(?:battery|battery level|battery percentage|battery pct|battery status|betery|bttry status)\??\s*$", re.I), ["system_health"]),
    # Direct wifi/bluetooth toggle or status
    (re.compile(r"^\s*(?:wifi|wi-fi)\s*(?:on|off|status|toggle)?\??\s*$", re.I), ["toggle_wifi"]),
    (re.compile(r"^\s*(?:bluetooth|bt)\s*(?:on|off|status|toggle)?\??\s*$", re.I), ["toggle_bluetooth"]),
]


class SemanticToolRouter:
    """Hybrid bi-encoder semantic router with precomputed static vector index and aspect aggregation."""

    def __init__(
        self,
        embeddings_path: str | Path | None = None,
        metadata_path: str | Path | None = None,
        model_path: str | None = None,
        threshold: float = 0.28,
        fallback_tools: List[str] | None = None,
        use_fast_path: bool = True,
    ) -> None:
        self.embeddings_path = Path(embeddings_path or DEFAULT_EMBEDDINGS)
        self.metadata_path = Path(metadata_path or DEFAULT_METADATA)
        self.threshold = threshold
        self.fallback_tools = list(fallback_tools or FALLBACK_TOOL_NAMES)
        self.use_fast_path = use_fast_path

        # Optimize CPU threads for sub-1B agent deployment
        if hasattr(torch, "set_num_threads") and torch.get_num_threads() > 4:
            torch.set_num_threads(4)

        if not self.embeddings_path.exists():
            raise FileNotFoundError(
                f"Tool embeddings not found at {self.embeddings_path}. Run scripts/precompute_tool_embeddings.py first."
            )
        self.tool_embeddings = np.load(self.embeddings_path).astype(np.float32)

        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Tool metadata not found at {self.metadata_path}.")
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        self.tool_names: List[str] = metadata["tools"]
        self.aspect_tools: List[str] = metadata.get("aspect_tools", self.tool_names)
        self.model_path = model_path or metadata.get("model") or self._discover_model_path()

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModel.from_pretrained(self.model_path, dtype=torch.float32)
        self.model.eval()

        self._query_cache: Dict[str, np.ndarray] = {}
        self._max_cache_size = 512

    def _discover_model_path(self) -> str:
        env_path = os.environ.get("NANO_EMBEDDING_MODEL_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
        candidates = glob.glob(
            os.path.expanduser("~/.cache/huggingface/hub/models--unsloth--bge-small-en-v1.5/snapshots/*")
        )
        if candidates:
            return candidates[0]
        return "unsloth/bge-small-en-v1.5"

    def embed_query(self, query: str) -> np.ndarray:
        """Embeds and L2-normalizes an incoming query string into a 384-dimensional vector."""
        cache_key = query.strip().lower()
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        inputs = self.tokenizer(
            [query],
            padding=True,
            truncation=True,
            max_length=64,
            return_tensors="pt",
        )
        with torch.inference_mode():
            outputs = self.model(**inputs)
            cls_emb = outputs.last_hidden_state[:, 0]
            normed = torch.nn.functional.normalize(cls_emb, p=2, dim=1)

        vec = normed.cpu().numpy().squeeze(0).astype(np.float32)

        if len(self._query_cache) >= self._max_cache_size:
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]
        self._query_cache[cache_key] = vec
        return vec

    def _aggregate_tool_scores(self, query_vec: np.ndarray) -> List[Tuple[str, float]]:
        """Calculates aspect dot products and takes the maximum similarity per unique tool."""
        aspect_scores = np.dot(self.tool_embeddings, query_vec)
        tool_scores: Dict[str, float] = {}
        for idx, score in enumerate(aspect_scores):
            tool = self.aspect_tools[idx]
            s = float(score)
            if tool not in tool_scores or s > tool_scores[tool]:
                tool_scores[tool] = s

        return sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)

    def route_names(
        self,
        query: str,
        max_tools: int = 4,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[List[str], bool]:
        """Selects top tool names for an incoming query, returning (names, is_fallback)."""
        clean = query.strip()

        # 1. Micro-query fast-path
        if self.use_fast_path:
            for pattern, tools in _FASTPATH_PATTERNS:
                if pattern.match(clean):
                    return tools[:max_tools], False

        # 2. Dense semantic retrieval
        query_vec = self.embed_query(clean)
        ranked = self._aggregate_tool_scores(query_vec)

        if not ranked:
            return self.fallback_tools[:max_tools], True

        top_score = ranked[0][1]
        if top_score < self.threshold:
            # Check for history anaphora before falling back
            if history:
                anaphoric = self._resolve_anaphora(clean, history)
                if anaphoric:
                    return anaphoric[:max_tools], False
            return self.fallback_tools[:max_tools], True

        selected = [tool for tool, score in ranked[:max_tools] if score >= self.threshold]

        # Safety filter (ADR-007): empty_trash requires trash/recycling intent, not generic file destruction
        if "empty_trash" in selected:
            is_generic_dir_deletion = bool(re.search(r"\b(home\s+directory|system|folder|drive|disk)\b", clean, re.IGNORECASE))
            has_trash_intent = bool(re.search(r"\b(trash|bin|recycle|recycling|rubbish|waste|wastebasket|garbo|junk)\b", clean, re.IGNORECASE))
            if is_generic_dir_deletion and not has_trash_intent:
                selected.remove("empty_trash")

        # Multi-turn history bridge: if query is anaphoric and top tools lack context, supplement
        if history and len(selected) < max_tools:
            anaphoric = self._resolve_anaphora(clean, history)
            if anaphoric:
                for t in anaphoric:
                    if t not in selected and len(selected) < max_tools:
                        selected.append(t)

        return (selected if selected else self.fallback_tools[:max_tools]), False

    def _resolve_anaphora(self, query: str, history: List[Dict[str, Any]]) -> Optional[List[str]]:
        """Resolves follow-up queries referring to previously used tools via pronouns."""
        has_pronoun = bool(re.search(r"\b(it|that|them|again|this|now|same)\b", query, re.IGNORECASE))
        if not has_pronoun:
            return None

        last_tool = None
        for msg in reversed(history):
            if msg.get("role") == "tool" and msg.get("name"):
                last_tool = msg.get("name")
                break
            tool_calls = msg.get("tool_calls") or msg.get("message", {}).get("tool_calls")
            if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
                last_tool = tool_calls[0].get("function", {}).get("name")
                break

        if last_tool:
            if last_tool in ["service_status", "restart_service"]:
                return ["restart_service", "service_status"]
            return [last_tool]
        return None

    def route_tools(
        self,
        query: str,
        all_tools: List[Dict[str, Any]],
        max_tools: int = 4,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Direct replacement for runtime.router.route_tools returning tool dict schemas."""
        tools_by_name = {t.get("function", {}).get("name"): t for t in all_tools}
        names, _ = self.route_names(query, max_tools=max_tools, history=history)
        return [tools_by_name[n] for n in names if n in tools_by_name]


# Module-level singleton instance for zero-reinitialization overhead
_ROUTER_INSTANCE: Optional[SemanticToolRouter] = None


def get_semantic_router() -> SemanticToolRouter:
    """Returns or lazily creates the process-level SemanticToolRouter singleton."""
    global _ROUTER_INSTANCE
    if _ROUTER_INSTANCE is None:
        _ROUTER_INSTANCE = SemanticToolRouter()
    return _ROUTER_INSTANCE


def route_tools(
    query: str,
    all_tools: List[Dict[str, Any]],
    max_tools: int = 4,
    history: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Drop-in functional replacement for runtime.router.route_tools.

    Falls back cleanly to the regex router if embeddings are missing.
    """
    try:
        router = get_semantic_router()
        return router.route_tools(query, all_tools, max_tools=max_tools, history=history)
    except Exception as e:
        # Graceful fallback to deterministic regex router on any initialization failure
        from .router import route_tools as regex_route_tools
        return regex_route_tools(query, all_tools, max_tools=max_tools, history=history)
