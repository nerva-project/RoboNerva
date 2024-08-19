from __future__ import annotations

import validators

import discord

from config import ADMIN_ROLE_IDS


def is_admin(member: discord.Member) -> bool:
    """Check if user is admin."""
    return any(role.id in ADMIN_ROLE_IDS for role in member.roles)


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


def calculate_banned_time_from_seconds(seconds: int) -> str:
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


def calculate_seconds_from_time_string(time_string: str) -> int:
    """Calculate seconds from time string."""
    time = time_string.split(" ")

    seconds = 0

    for t in time:
        if t.endswith("s"):
            seconds += int(t[:-1])

        if t.endswith("m"):
            seconds += int(t[:-1]) * 60

        if t.endswith("h"):
            seconds += int(t[:-1]) * 3600

        if t.endswith("d"):
            seconds += int(t[:-1]) * 86400

    return seconds
