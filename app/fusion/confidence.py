def calculate_confidence(freshness: str, health: str) -> float:
    base = 1.0
    if freshness == "FRESH":
        pass
    elif freshness == "AGING":
        base -= 0.2
    elif freshness == "STALE":
        base -= 0.5
    else:
        return 0.0

    if health == "DEGRADED":
        base -= 0.3
    elif health == "FAILED":
        return 0.0

    return max(0.0, min(1.0, base))
