from __future__ import annotations

import validators


def validate_tweet_links(tweet_links: list[str]) -> bool:
    """Validate tweet links."""
    for link in tweet_links:
        if link and not validators.url(link):
            return False

    return True


def validate_ip_address(ip: str) -> bool:
    """Validate IP address."""
    return validators.ipv4(ip) or validators.ipv6(ip)


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


def calculate_banned_time(seconds: int) -> str:
    """Calculate banned time."""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days == 0 and hours == 0 and minutes == 0:
        return f"{seconds}s"

    if days == 0 and hours == 0:
        return f"{minutes}m {seconds}s"

    if days == 0:
        return f"{hours}h {minutes}m {seconds}s"

    return f"{days}d {hours}h {minutes}m {seconds}s"
