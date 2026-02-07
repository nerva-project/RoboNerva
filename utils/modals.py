from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import discord
from discord import ui

from config import (
    TIPBOT_USER_ID,
    TIPBOT_CHANNEL_ID,
    WELCOME_TIP_AMOUNT,
    VERIFIED_USER_ROLE_ID,
    UNVERIFIED_USER_ROLE_ID,
)

if TYPE_CHECKING:
    from motor import MotorCollection


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

    collection: MotorCollection = None

    timeout: int = 5 * 60

    text = ui.TextInput(
        label="Type 'I agree' below: ",
        placeholder="I agree",
        required=True,
    )

    async def on_submit(self, ctx: discord.Interaction) -> None:
        self.interaction = ctx

        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True, ephemeral=True)

        if self.text.value.lower() != "i agree":
            await ctx.followup.send(content="You must type 'I agree' to continue.")
            return

        await self.ctx.delete_original_response()

        verified_user_role = ctx.guild.get_role(VERIFIED_USER_ROLE_ID)
        await ctx.user.add_roles(verified_user_role)

        unverified_user_role = ctx.guild.get_role(UNVERIFIED_USER_ROLE_ID)
        await ctx.user.remove_roles(unverified_user_role)

        if (await self.collection.find_one({"_id": ctx.user.id})) is None:
            await self.collection.insert_one(
                {"_id": ctx.user.id, "verified": True, "tipped": True}
            )

            tipbot = ctx.guild.get_member(TIPBOT_USER_ID)
            tipbot_channel = ctx.guild.get_channel(TIPBOT_CHANNEL_ID)

            await ctx.channel.send(
                content=f"{tipbot.mention} tip {WELCOME_TIP_AMOUNT} XNV {ctx.user.mention}. "
                f"Welcome to the <:nerva:1274417479606603776> community server, {ctx.user.mention}! "
                f"You're now verified. Here's {WELCOME_TIP_AMOUNT} XNV to get you started. "
                f"Head over to {tipbot_channel.mention} for help with these funds. "
                f"Enjoy your stay!"
            )

        elif (
            await self.collection.find_one({"_id": ctx.user.id, "tipped": False})
        ) is not None:
            await self.collection.update_one(
                {"_id": ctx.user.id}, {"$set": {"verified": True, "tipped": True}}
            )

            tipbot = ctx.guild.get_member(TIPBOT_USER_ID)
            tipbot_channel = ctx.guild.get_channel(TIPBOT_CHANNEL_ID)

            await ctx.channel.send(
                content=f"{tipbot.mention} tip {WELCOME_TIP_AMOUNT} XNV {ctx.user.mention}. "
                f"Welcome to the <:nerva:1274417479606603776> community server, {ctx.user.mention}! "
                f"You're now verified. Here's {WELCOME_TIP_AMOUNT} XNV to get you started. "
                f"Head over to {tipbot_channel.mention} for help with these funds. "
                f"Enjoy your stay!"
            )

        else:
            await self.collection.update_one(
                {"_id": ctx.user.id}, {"$set": {"verified": True}}
            )

            await ctx.channel.send(
                content=f"Welcome back, {ctx.user.mention}! You're now verified.",
            )

    async def on_timeout(self) -> None:
        await self.ctx.followup.send(
            content="Timeout! Please try again.", ephemeral=True
        )
