"""
In-memory sliding-window rate limiter for auth endpoints.
"""

import time
from collections import defaultdict
from fastapi import HTTPException, status

_attempts = defaultdict(list)


def check_rate_limit(identifier: str, max_attempts: int = 5, window_seconds: int = 60):
    """Limit auth endpoint calls to max_attempts per window_seconds per user/IP."""
    now = time.time()
    ident = identifier.lower().strip()

    # Clean old timestamps
    _attempts[ident] = [t for t in _attempts[ident] if now - t < window_seconds]

    if len(_attempts[ident]) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login/signup attempts. Please wait {window_seconds} seconds.",
        )

    _attempts[ident].append(now)
