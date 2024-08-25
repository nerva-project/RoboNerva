from __future__ import annotations
from typing import Optional

import discord
from discord import ui

from config import (
    VERIFIED_USER_ROLE_ID,
    UNVERIFIED_USER_ROLE_ID,
    TIPBOT_USER_ID,
    TIPBOT_CHANNEL_ID,
)


class EvalModal(ui.Modal, title="Evaluate Code"):
    ctx: Optional[discord.Interaction] = None
    interaction: Optional[discord.Interaction] = None

    timeout: int = 5 * 60

    code = ui.TextInput(
        label="Code",
        placeholder="Enter the code to evaluate",
        style=discord.TextStyle.paragraph,
        required=True,
    )

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

    async def on_timeout(self):
        await self.ctx.followup.send(
            content="Timeout! Please try again.", ephemeral=True
        )


class ExecModal(ui.Modal, title="Execute Shell Commands"):
    ctx: Optional[discord.Interaction] = None
    interaction: Optional[discord.Interaction] = None

    timeout: int = 5 * 60

    sh_commands = ui.TextInput(
        label="Command(s)",
        placeholder="Enter the command(s) to execute",
        style=discord.TextStyle.paragraph,
        required=True,
    )

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

    async def on_timeout(self):
        await self.ctx.followup.send(
            content="Timeout! Please try again.", ephemeral=True
        )


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


class VerificationModal(ui.Modal, title="User Verification"):
    ctx: Optional[discord.Interaction] = None
    interaction: Optional[discord.Interaction] = None

    timeout: int = 5 * 60

    text = ui.TextInput(
        label="Type 'I agree to the rules' below: ",
        placeholder="I agree to the rules",
        required=True,
    )

    async def on_submit(self, ctx: discord.Interaction) -> None:
        self.interaction = ctx

        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        if self.text.value.lower() != "i agree to the rules":
            await ctx.followup.send(
                content="You must type 'I agree to the rules' to continue.",
                ephemeral=True,
            )
            return

        verified_user_role = ctx.guild.get_role(VERIFIED_USER_ROLE_ID)
        await ctx.user.add_roles(verified_user_role)

        unverified_user_role = ctx.guild.get_role(UNVERIFIED_USER_ROLE_ID)
        await ctx.user.remove_roles(unverified_user_role)

        tipbot = ctx.guild.get_member(TIPBOT_USER_ID)
        tipbot_channel = ctx.guild.get_channel(TIPBOT_CHANNEL_ID)

        await ctx.followup.send(
            content=f"{tipbot.mention} tip 1.00 XNV {ctx.user.mention}. "
            f"Welcome to the <:nerva:1274417479606603776> community server. "
            f"You're now verified. Here's 1 XNV to get you started. "
            f"Head over to {tipbot_channel.mention} for help with these funds. "
            f"Enjoy your stay!",
            ephemeral=True,
        )

    async def on_timeout(self) -> None:
        await self.ctx.followup.send(
            content="Timeout! Please try again.", ephemeral=True
        )
