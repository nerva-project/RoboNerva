from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from utils.buttons import VerifyButton

if TYPE_CHECKING:
    from bot import RoboNerva


class Verification(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        welcome_channel = self.bot.get_channel(self.bot.config.WELCOME_CHANNEL_ID)

        if not welcome_channel:
            return

        view = discord.ui.View()
        view.add_item(VerifyButton())

        await welcome_channel.send(
            f"Welcome, {member.mention}! Please read the instructions in "
            f"<#{self.bot.config.RULES_CHANNEL_ID}>, and then press the button below "
            f"in order to get verified and have access to the rest of the server.",
            view=view,
        )


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(Verification(bot))
