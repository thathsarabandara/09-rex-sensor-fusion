from typing import Dict, List


def majority_vote(history: List[bool]) -> bool:
    if not history:
        return False
    return history.count(True) > len(history) / 2


def get_debounced_state(
    current_state: Dict[str, bool], state_histories: Dict[str, List[bool]], window_size: int = 5
) -> Dict[str, bool]:
    result = {}
    for key in ["left_outer", "left_inner", "right_inner", "right_outer"]:
        history = state_histories.get(key, []) + [current_state.get(key, False)]
        if len(history) > window_size:
            history = history[-window_size:]
        state_histories[key] = history
        result[key] = majority_vote(history)
    return result


def calculate_normalized_error(debounced_state: Dict[str, bool]) -> float:
    weights = {"left_outer": -1.00, "left_inner": -0.33, "right_inner": 0.33, "right_outer": 1.00}

    active_weights = [weights[k] for k, v in debounced_state.items() if v]

    if not active_weights:
        return 0.0  # LOST

    return sum(active_weights) / len(active_weights)


def get_line_position(debounced_state: Dict[str, bool]) -> str:
    s = [
        debounced_state.get("left_outer", False),
        debounced_state.get("left_inner", False),
        debounced_state.get("right_inner", False),
        debounced_state.get("right_outer", False),
    ]

    if s == [False, False, False, False]:
        return "LOST"
    if s == [True, True, True, True]:
        return "WIDE"

    # Left logic
    if (s[0] and s[1] and not s[2] and not s[3]) or (s[0] and not s[1] and not s[2] and not s[3]):
        return "LEFT"

    # Right logic
    if (not s[0] and not s[1] and s[2] and s[3]) or (not s[0] and not s[1] and not s[2] and s[3]):
        return "RIGHT"

    return "CENTER"
