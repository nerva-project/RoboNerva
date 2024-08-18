from __future__ import annotations
from typing import Optional

import discord
from discord import ui


class TweetLinksModal(ui.Modal, title="Submit tweet links"):
    ctx: Optional[discord.Interaction] = None
    interaction: Optional[discord.Interaction] = None

    timeout: int = 5 * 60

    tweet_link_1 = ui.TextInput(
        label="Tweet link 1",
        placeholder="Enter the link to the first tweet",
        required=True,
    )

    tweet_link_2 = ui.TextInput(
        label="Tweet link 2",
        placeholder="Enter the link to the second tweet",
        required=False,
    )

    tweet_link_3 = ui.TextInput(
        label="Tweet link 3",
        placeholder="Enter the link to the third tweet",
        required=False,
    )

    async def on_submit(self, ctx: discord.Interaction) -> None:
        self.interaction = ctx

        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

    async def on_timeout(self) -> None:
        await self.ctx.followup.send(
            content="Timeout! Please try again.", ephemeral=True
        )
