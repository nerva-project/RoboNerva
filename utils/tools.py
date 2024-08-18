from __future__ import annotations

import validators


def validate_tweet_links(tweet_links: list[str]) -> bool:
    """Validate tweet links."""
    for link in tweet_links:
        if link and not validators.url(link):
            return False

    return True


def calculate_hashrate(difficulty: int) -> str:
    """Calculate network hashrate."""
    hr = difficulty / 60

    res = f"{hr:.2f} H/s"

    if hr > 1_000:
        res = f"{hr / 1_000:.2f} KH/s"

    if hr > 1_000_000:
        res = f"{hr / 1_000_000:.2f} MH/s"

    return res


def calculate_database_size(size: int) -> str:
    """Calculate database size."""
    return f"{size / 1_000_000_000:.2f} GB"
