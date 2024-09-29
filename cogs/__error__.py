from __future__ import annotations

from typing import TYPE_CHECKING

import random
import string
import traceback

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from bot import RoboNerva


class Error(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    async def cog_load(self):
        await self.global_app_command_error_handler(bot=self.bot)

    async def global_app_command_error_handler(self, bot: commands.AutoShardedBot):
        @bot.tree.error
        async def app_command_error(
            ctx: discord.Interaction,
            error: app_commands.AppCommandError,
        ):
            if isinstance(error, app_commands.CheckFailure):
                return

            else:
                embed = discord.Embed(colour=self.bot.embed_color)

                embed.title = "Oops! Something went wrong."
                embed.description = f"```css\n{error.__str__()}```"

                # noinspection PyUnresolvedReferences
                if ctx.response.is_done():
                    # noinspection PyUnresolvedReferences
                    await ctx.edit_original_response(embed=embed)
                else:
                    # noinspection PyUnresolvedReferences
                    await ctx.response.send_message(embed=embed, ephemeral=True)

                embed.title = "Error Report"
                embed.description = ""

                embed.add_field(
                    name="Command", value=f"`{ctx.command.name}`", inline=False
                )

                file_name = (
                    f"logs/errors/{ctx.command.name}-"
                    f"{''.join(random.choices(string.ascii_letters + string.digits, k=10))}.log"
                )

                with open(file_name, "w") as f:
                    f.write("".join(traceback.format_exception(error)))

                embed.add_field(
                    name="Log",
                    value=f"Saved to `{file_name}`",
                )

                return await self.bot.log_hook.send(embed=embed)


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(Error(bot))
