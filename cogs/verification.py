from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils.cd import cooldown
from utils.tools import is_admin
from utils.buttons import VerifyButton

if TYPE_CHECKING:
    from bot import RoboNerva

from config import COMMUNITY_GUILD_ID


class Verification(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        welcome_channel = self.bot.get_channel(self.bot.config.WELCOME_CHANNEL_ID)

        if not welcome_channel:
            return

        unverified_user_role = member.guild.get_role(
            self.bot.config.UNVERIFIED_USER_ROLE_ID
        )
        await member.add_roles(unverified_user_role)

        view = discord.ui.View()
        view.add_item(VerifyButton())

        await welcome_channel.send(
            f"Welcome, {member.mention}! Please read <#{self.bot.config.RULES_CHANNEL_ID}>, "
            f"and then press the **Verify** button below to get access to the rest of the server.",
            view=view,
        )

    @app_commands.command(name="revoke")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _revoke(self, ctx: discord.Interaction, member: discord.Member):
        """(ADMIN) Revoke a user's verification.

        Parameters
        ----------
        member : discord.Member
            The member to revoke verification from.

        """
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        if not is_admin(ctx.user):
            return await ctx.edit_original_response(
                content="Only admins can use this command."
            )

        verified_user_role = ctx.guild.get_role(
            self.bot.config.VERIFIED_USER_ROLE_ID
        )
        unverified_user_role = ctx.guild.get_role(
            self.bot.config.UNVERIFIED_USER_ROLE_ID
        )

        if verified_user_role not in member.roles:
            return await ctx.edit_original_response(
                content=f"{member.mention} is not verified."
            )

        await member.remove_roles(verified_user_role)
        await member.add_roles(unverified_user_role)

        await ctx.edit_original_response(
            content=f"{member.mention}'s verification has been revoked."
        )


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(Verification(bot))
