ENGINEERING_HEURISTICS = {
    "low_latency": "Prefer O(1) or O(log n) lookups. Avoid GC heavy operations (like massive HashMaps).",
    "embedded": "Strict Memory limit. Avoid Recursion. Prefer In-place algorithms (O(1) Space).",
    "high_throughput": "Minimize locking. Use localized data structures to prevent cache misses.",
    "real_time": "Deterministic execution required. Avoid amortized analysis.",
    "large_dataset": "Streaming algorithms required. Cannot load all into RAM.",
    "threading": "Avoid shared mutable state. Prefer Immutable data structures."
}

def consult_heuristics_db(constraints: list) -> str:
    advice = []
    normalized_constraints = [c.lower() for c in constraints]
    for key, rule in ENGINEERING_HEURISTICS.items():
        for constraint in normalized_constraints:
            if key in constraint or key.replace("_", " ") in constraint:
                advice.append(f"RULE [{key.upper()}]: {rule}")
    return "\n".join(advice) if advice else "Optimize for standard Time/Space balance."
