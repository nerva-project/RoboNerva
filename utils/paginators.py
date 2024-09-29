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

        embed.set_footer(text=f"Page {page_no}/{self.total_pages}")

        return embed

    def is_paginating(self) -> bool:
        return True


class TradeOgrePaginatorSource(ListPageSource):
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

        embed = discord.Embed(colour=EMBED_COLOR)
        embed.title = f"**{item['pair']}** on TradeOgre"
        embed.url = f"https://tradeogre.com/exchange/{item['pair']}"

        embed.set_author(name="RoboNerva", icon_url=self.ctx.guild.me.avatar.url)
        embed.set_thumbnail(
            url="https://nerva.one/content/images/tradeogre-logo.png"
        )

        embed.add_field(name="Last Price", value=item["last_price"])
        embed.add_field(name="Bid", value=item["bid"])
        embed.add_field(name="Ask", value=item["ask"])
        embed.add_field(name="Volume", value=item["volume"])
        embed.add_field(name="High", value=item["high"])
        embed.add_field(name="Low", value=item["low"])

        embed.set_footer(text=f"Entry {page_no}/{self.total_pages}")

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
