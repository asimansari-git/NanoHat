# Voice-to-Text Transcripts & Conversational ASR Filler - Evaluation Report

## Persona & ASR Voice Noise Linguistic Matrix
This stress test evaluated NanoHat v3's deterministic regex intent router against a matrix of voice transcription artifacts, including:
- **Hesitations & Filler Words:** 'uh', 'um', 'like', 'basically', 'so'
- **Stuttering & Repetitions:** 't-turn', 'uh uh'
- **Run-on & Conversational Speech:** 'hey listen can you...', 'can you just uh tell me if...'
- **Mid-Sentence Corrections (Retractions):** 'wait no', 'scratch that', 'i mean', 'actually'

These speech patterns introduce extreme variance and extraneous noise compared to clean text inputs.

## Executive Summary
- **Total Cases Executed:** 46
- **Passed Cases (Stable Routing/Graceful Fallback):** 36
- **Expected Failures (XFailed / Multi-Turn LLM Reasoning Required):** 10
- **Overall Pass Rate:** 78.3% (Excluding intended xfails, 100% stable router execution without crashes).

The router successfully maintains a strict ceiling of max 4 active tools, never overflowing the 270M model's cognitive context limit even under heavy ASR noise.

## Detailed Case Matrix

### 1. Telemetry & Power (Passed 7, XFailed 2)
The router handles filler words well for system metrics.
**Failures:** Intent bleed into user memory (memory_set/get) occurs when users say "my laptop is..." or use the word "memory" to refer to RAM (which conflicts with persistent memory notes).

### 2. Hardware & Radios (Passed 9, XFailed 1)
Stuttering ("t-turn") and conversational filler ("uh", "um") are reliably ignored.
**Failures:** Mid-sentence correction ("turn on blutooth wait no i mean wifi") causes the router to match both tools, since regexes cannot interpret the semantic negation of "wait no".

### 3. Services & Daemons (Passed 5, XFailed 2)
**Failures:** Phrases like "is docker running wait no just restart it" trigger both `service_status` and `restart_service`. Disambiguating the final user intent requires multi-turn LLM reasoning which the regex router cannot do.

### 4. Persistent Memory (Passed 7, XFailed 1)
**Failures:** "wait actually scratch that forget my favorite color" causes multi-intent collisions. The router matches `memory_delete` and `memory_set`.

### 5. Scheduling & Housekeeping (Passed 8, XFailed 4)
**Failures:** Heavy failures here due to mid-sentence corrections on specific task parameters ("buy milk wait no buy eggs", or "cancel task two wait no three"). The router simply activates `task_add` or `task_cancel`, but the LLM will struggle to decipher which entity the user actually wanted because both entities exist in the prompt context. Similarly, negations ("empty the bin wait actually no don't") still trigger `empty_trash`.

## Speech Filler Impact & Intent Bleed Analysis
1. **Filler words (uh, um, like)** are harmless. They do not trigger unintended tools because the regex patterns are highly targeted.
2. **"My [X] is..." collisions:** The phrase "my laptop is dying" triggers the `memory_set` statement ("my [X] is [Y]").
3. **"Memory" disambiguation:** Users saying "how much free memory" triggers both system_health and memory_get.
4. **Mid-sentence Retractions:** This is the critical weakness of the deterministic router. "Wait no", "scratch that", and "actually" represent semantic shifts that regex cannot resolve. It results in multiple conflicting tools being activated.

## Recommended Hardening Patches
1. **Update `router.py` STOPWORDS / Negative Lookaheads:** Add "laptop", "computer", "pc" to the negative lookahead for `RE_MEMORY_SET_STATEMENT`.
2. **Contextual RAM matching:** Refine `RE_MEMORY_WORDS` to strictly exclude matches if "RAM", "usage", or "free" are in the sentence, to prevent `memory_get` bleeding into system telemetry.
3. **Multi-turn LLM Pre-Processing:** For true mid-sentence retractions, a small language model is required to pre-process and "clean" the transcription (e.g. converting "add milk wait no eggs" to "add eggs") *before* the intent router sees it. This is beyond the scope of a regex router.