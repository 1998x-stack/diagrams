from __future__ import annotations


def evaluate_condition(condition: str, state_dict: dict) -> bool:
    """
    Evaluate a Stage 3 RewardEvent condition string against a game state dict.

    Uses eval() with restricted builtins to reduce risk. Any exception
    (NameError, SyntaxError, TypeError, ZeroDivisionError, etc.) returns False.
    Never raises.

    Security note: condition strings are expected to originate from Stage 3
    (LLM-generated reward rules), not from untrusted user input. The
    {"__builtins__": {}} restriction reduces common attack surface but does
    not fully sandbox arbitrary untrusted Python. Callers are responsible for
    ensuring condition strings come from a trusted source.

    Args:
        condition: Python expression string, e.g. "'pizza' in inventory and oven == 'ready'"
        state_dict: game state variables, e.g. {"inventory": ["pizza"], "oven": "ready"}

    Returns:
        True if condition evaluates to a truthy value, False otherwise.
    """
    try:
        return bool(eval(condition, {"__builtins__": {}}, state_dict))
    except Exception:
        return False
