from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import discord
from discord.ext.menus import ListPageSource

from utils.tools import calculate_banned_time_from_seconds

if TYPE_CHECKING:
    from discord.ext.menus import Menu

from config import EMBED_COLOR


class HistoricalPricePaginatorSource(ListPageSource):
    def __init__(
        self,
        entries: list,
        ctx: discord.Interaction,
        per_page: Optional[int] = 1,
    ):
        entries = [tuple(entries[i : i + 5]) for i in range(0, len(entries), 5)]
        super().__init__(list(enumerate(entries, 1)), per_page=per_page)

        self.ctx = ctx
        self.total_pages = len(entries)

    async def format_page(self, menu: Menu, item: Any) -> discord.Embed:
        page_no, item = item

        embed = discord.Embed(colour=EMBED_COLOR)
        embed.title = f"Nerva Historical Price Data"

        embed.set_author(name="RoboNerva", icon_url=self.ctx.guild.me.avatar.url)
        embed.set_thumbnail(
            url="https://encrypted-tbn0.gstatic.com/images?"
            "q=tbn:ANd9GcT9xV6Ut4_LMNqb9umIAXW3eu7-unDOiLeNjg&s"
        )

        for entry in item:
            embed.add_field(
                name=entry["date"].strftime("%Y-%m-%d"),
                value=f"```css\n"
                f"Opening price: ${entry['opening']}\n"
                f"Closing price: ${entry['closing']}\n"
                f"High price: ${entry['high']}\n"
                f"Low price: ${entry['low']}\n"
                f"Volume: ${entry['volume']}\n"
                f"```",
                inline=False,
            )

        embed.set_footer(
            text=f"Page {page_no}/{self.total_pages} | Use \u25c0\ufe0f and \u25b6\ufe0f to navigate through the entries & \u23f9\ufe0f to stop the pagination"
        )

        return embed

    def is_paginating(self) -> bool:
        return True


class NervaExchangePaginatorSource(ListPageSource):
    def __init__(
        self,
        entries: list,
        ctx: discord.Interaction,
        exchange_name: str,
        exchange_urls: dict[str, Any],
        thumbnail_url: str,
        per_page: Optional[int] = 1,
    ):
        super().__init__(list(enumerate(entries, 1)), per_page=per_page)

        self.ctx = ctx
        self.exchange_name = exchange_name
        self.exchange_urls = exchange_urls
        self.thumbnail_url = thumbnail_url
        self.total_pages = len(entries)

    async def format_page(self, menu: Menu, item: Any) -> discord.Embed:
        page_no, item = item

        embed = discord.Embed(colour=EMBED_COLOR)

        embed.title = f"{item['pair']} on {self.exchange_name}"
        embed.url = self.exchange_urls[item["pair"]]

        embed.set_author(name="RoboNerva", icon_url=self.ctx.guild.me.avatar.url)
        embed.set_thumbnail(url=self.thumbnail_url)

        embed.add_field(
            name="Last Price",
            value=item.get("last_price", "N/A"),
        )

        if item.get("bid"):
            embed.add_field(
                name="Bid",
                value=item["bid"],
            )

        if item.get("ask"):
            embed.add_field(
                name="Ask",
                value=item["ask"],
            )

        embed.add_field(
            name="Volume",
            value=item.get("volume", "N/A"),
        )

        embed.add_field(
            name="High",
            value=item.get("high", "N/A"),
        )

        embed.add_field(
            name="Low",
            value=item.get("low", "N/A"),
        )

        if item.get("last_trade"):
            embed.add_field(
                name="Last Trade",
                value=f"<t:{item['last_trade']}:R>",
            )

        embed.set_footer(
            text=f"Page {page_no}/{self.total_pages} | Use \u25c0\ufe0f and \u25b6\ufe0f to navigate through the entries & \u23f9\ufe0f to stop the pagination"
        )

        return embed

    def is_paginating(self) -> bool:
        return True


class IPBanPaginatorSource(ListPageSource):
    def __init__(
        self,
        entries: list,
        ctx: discord.Interaction,
        per_page: Optional[int] = 1,
    ):
        super().__init__(list(enumerate(entries, 1)), per_page=per_page)

        self.ctx = ctx
        self.total_pages = len(entries)

    async def format_page(self, menu: Menu, item: Any) -> discord.Embed:
        page_no, item = item

        embed = discord.Embed(color=EMBED_COLOR)
        embed.title = f"IP {item['host']}"

        embed.set_author(name="RoboNerva", icon_url=self.ctx.guild.me.avatar.url)

        embed.add_field(name="IP Int32", value=item["ip"])
        embed.add_field(name="Reason", value=item["reason"])
        embed.add_field(
            name="Time Remaining",
            value=f"```css\n{calculate_banned_time_from_seconds(item['seconds'])}```",
            inline=False,
        )

        embed.set_footer(text=f"Entry {page_no}/{self.total_pages}")

        return embed

    def is_paginating(self) -> bool:
        return True
