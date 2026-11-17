"""
Progressive cool-down after a request is declined.

Each time `to_user` declines `from_user` the strike count goes up and so does
the wait before `from_user` may ask again:

    1st decline -> 2 min, 2nd -> 5 min, 3rd -> 15 min, 4th -> 1 h, 5th+ -> 6 h

Strikes are forgotten after STRIKE_MEMORY without a new decline, or as soon as
the two users successfully connect. Two kinds are tracked separately:
"chat" (waiting-room invitations) and "friend" (friend requests).
"""
import time

from django.core.cache import cache

STEPS = [2 * 60, 5 * 60, 15 * 60, 60 * 60, 6 * 60 * 60]
STRIKE_MEMORY = 24 * 60 * 60


def _key(kind, from_user, to_user):
    return f"cooldown:{kind}:{from_user}:{to_user}"


def record_decline(kind, from_user, to_user):
    """Registers a decline; returns the cool-down (seconds) now in force."""
    key = _key(kind, from_user, to_user)
    state = cache.get(key) or {"strikes": 0, "until": 0}
    state["strikes"] += 1
    wait = STEPS[min(state["strikes"], len(STEPS)) - 1]
    state["until"] = time.time() + wait
    cache.set(key, state, timeout=STRIKE_MEMORY + wait)
    return wait


def remaining(kind, from_user, to_user):
    """Seconds until `from_user` may ask `to_user` again (0 = allowed now)."""
    state = cache.get(_key(kind, from_user, to_user))
    if not state:
        return 0
    return max(0, int(state["until"] - time.time()))


def strikes(kind, from_user, to_user):
    state = cache.get(_key(kind, from_user, to_user))
    return state["strikes"] if state else 0


def clear(kind, user_a, user_b):
    """Forget strikes in both directions (the users connected successfully)."""
    cache.delete_many([_key(kind, user_a, user_b), _key(kind, user_b, user_a)])


def humanize(seconds):
    seconds = max(1, int(seconds))
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    minutes = -(-seconds // 60)  # round up
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    hours = minutes / 60
    if hours < 1.5:
        return "1 hour"
    return f"{round(hours)} hours"
