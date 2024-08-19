from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Any

import discord
from discord.ext.menus import ListPageSource

from utils.tools import calculate_banned_time_from_seconds

if TYPE_CHECKING:
    from discord.ext.menus import Menu

from config import EMBED_COLOR


class IPBanPaginatorSource(ListPageSource):
    def __init__(
        self,
        entries: list,
        ctx: discord.Interaction,
        per_page: Optional[int] = 1,
    ):
        super().__init__(entries, per_page=per_page)

        self.ctx = ctx

    async def format_page(self, menu: Menu, item: Any) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.title = f"IP {item['host']}"

        embed.set_author(
            name=self.ctx.guild.me, icon_url=self.ctx.guild.me.avatar.url
        )

        embed.add_field(name="IP Int32", value=item["ip"])
        embed.add_field(name="Reason", value=item["reason"])
        embed.add_field(
            name="Time Remaining",
            value=f"```css\n{calculate_banned_time_from_seconds(item['seconds'])}```",
            inline=False,
        )

        return embed

    def is_paginating(self) -> bool:
        return True
