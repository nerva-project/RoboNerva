from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils.cd import cooldown

if TYPE_CHECKING:
    from bot import RoboNerva


class Help(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @app_commands.command(name="help")
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _help(self, ctx: discord.Interaction):
        """Shows a list of all the commands provided by RoboNerva."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        embed = discord.Embed(colour=self.bot.embed_color)
        embed.title = "Command List"
        embed.description = (
            "Here's a list of available commands:\n\n(\U0001F31F = Admin only)"
        )

        embed.add_field(
            name="AutoPost", value=f"`/upload` (\U0001F31F)", inline=False
        )

        embed.add_field(
            name="General",
            value=f"`/ping`, `/uptime`, `/web`, `/community`, `/exchanges`, `/downloads`",
            inline=False,
        )

        embed.add_field(
            name="Market",
            value=f"`/coingecko`, `/tradeogre`, `/xeggex`",
            inline=False,
        )

        embed.add_field(
            name="Network",
            value=f"`/info`, `/height`, `/difficulty`, `/hashrate`, `/supply`, `/seeds`, "
            f"`/seed_info`, `/lastblock`, `/inflation`, `/bans`, `/ban` (\U0001F31F), `/unban`, ",
            inline=False,
        )

        embed.add_field(
            name="Verification", value=f"`/revoke` (\U0001F31F)", inline=False
        )

        await ctx.edit_original_response(embed=embed)


async def setup(bot: RoboNerva):
    await bot.add_cog(Help(bot))