from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils.tools import is_admin

from config import COMMUNITY_GUILD_ID

if TYPE_CHECKING:
    from bot import RoboNerva


class Dev(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @app_commands.command(name="load")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    async def _load(self, ctx: discord.Interaction, extension: str):
        """Load an extension.

        Parameters
        ----------
        extension : str
            The name of the extension to load.

        """
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        if not is_admin(ctx.user):
            return await ctx.edit_original_response(
                content="Only admins can use this command."
            )

        try:
            await self.bot.load_extension(f"cogs.{extension}")

        except commands.ExtensionNotFound:
            return await ctx.edit_original_response(
                content="Sorry, no such extension found."
            )

        except commands.ExtensionAlreadyLoaded:
            return await ctx.edit_original_response(
                content="Sorry, this extension is already loaded."
            )

        await ctx.edit_original_response(content="The extension has been loaded.")

    @app_commands.command(name="unload")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    async def _unload(self, ctx: discord.Interaction, extension: str):
        """Unload an extension.

        Parameters
        ----------
        extension : str
            The name of the extension to unload.

        """
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        if not is_admin(ctx.user):
            return await ctx.edit_original_response(
                content="Only admins can use this command."
            )

        try:
            await self.bot.unload_extension(f"cogs.{extension}")

        except commands.ExtensionNotLoaded:
            return await ctx.edit_original_response(
                content="Sorry, no such extension is loaded."
            )

        await ctx.edit_original_response(content="The extension has been unloaded.")

    @app_commands.command(name="reload")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    async def _reload(self, ctx: discord.Interaction, extension: str):
        """Reload an extension.

        Parameters
        ----------
        extension : str
            The name of the extension to reload.

        """
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        if not is_admin(ctx.user):
            return await ctx.edit_original_response(
                content="Only admins can use this command."
            )

        try:
            await self.bot.reload_extension(f"cogs.{extension}")

        except commands.ExtensionNotLoaded:
            return await ctx.edit_original_response(
                content="Sorry, no such extension is loaded."
            )

        await ctx.edit_original_response(content="The extension has been reloaded.")

    @app_commands.command(name="sync")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    async def _sync(self, ctx: discord.Interaction):
        """Sync the server's app commands."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        if not is_admin(ctx.user):
            return await ctx.edit_original_response(
                content="Only admins can use this command."
            )

        await self.bot.tree.sync(guild=ctx.guild)

        await ctx.edit_original_response(content="Synced.")


async def setup(bot: RoboNerva):
    await bot.add_cog(Dev(bot))
