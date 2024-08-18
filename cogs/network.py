from __future__ import annotations
from typing import TYPE_CHECKING

import aiohttp

import discord
from discord import app_commands
from discord.ext import commands

from utils.cd import cooldown
from utils.tools import calculate_hashrate, calculate_database_size

if TYPE_CHECKING:
    from bot import RoboNerva

from config import COMMUNITY_GUILD_ID


class Network(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @app_commands.command(name="info")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _info(self, ctx: discord.Interaction):
        """Shows various network information."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        embed = discord.Embed(color=self.bot.embed_color)
        embed.title = "Nerva Network Information"

        embed.set_author(name="Nerva", icon_url=self.bot.user.avatar.url)

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nerva.one/daemon/get_info/") as res:
                data = (await res.json())["result"]

                embed.add_field(name="Height", value=data["height"])
                embed.add_field(name="Difficulty", value=data["difficulty"])
                embed.add_field(
                    name="Hashrate", value=calculate_hashrate(data["difficulty"])
                )
                embed.add_field(name="", value="")
                embed.add_field(
                    name="Database Size",
                    value=calculate_database_size(data["database_size"]),
                )
                embed.add_field(
                    name="Top Block",
                    value=f"[`{data['top_block_hash']}`]"
                    f"(https://explorer.nerva.one/detail/{data['top_block_hash']})",
                    inline=False,
                )

            async with session.get(
                "https://api.nerva.one/daemon/get_last_block_header/"
            ) as res:
                data = (await res.json())["result"]["block_header"]

                embed.set_field_at(
                    3,
                    name="Last Block Timestamp",
                    value=f"<t:{data['timestamp']}:F> "
                    f"(<t:{data['timestamp']}:R>)",
                )

        await ctx.edit_original_response(embed=embed)

    @app_commands.command(name="height")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _height(self, ctx: discord.Interaction):
        """Shows the network height."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nerva.one/daemon/get_info/") as res:
                data = (await res.json())["result"]

                height = data["height"]

        await ctx.edit_original_response(
            content=f"The current block height is `{height}`."
        )

    @app_commands.command(name="difficulty")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _difficulty(self, ctx: discord.Interaction):
        """Shows the network difficulty."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nerva.one/daemon/get_info/") as res:
                data = (await res.json())["result"]

                difficulty = data["difficulty"]

        await ctx.edit_original_response(
            content=f"The current network difficulty is `{difficulty}`."
        )

    @app_commands.command(name="hashrate")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _hashrate(self, ctx: discord.Interaction):
        """Shows the network hashrate."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nerva.one/daemon/get_info/") as res:
                data = (await res.json())["result"]

                hashrate = calculate_hashrate(data["difficulty"])

        await ctx.edit_original_response(
            content=f"The current network hashrate is `{hashrate}`."
        )

    @app_commands.command(name="lastblock")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _lastblock(self, ctx: discord.Interaction):
        """Shows information about the last block found on the network."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(name="RoboNerva", icon_url=self.bot.user.avatar.url)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.nerva.one/daemon/get_last_block_header/"
            ) as res:
                data = (await res.json())["result"]["block_header"]

                embed.title = f"Block {data['height']}"

                embed.add_field(name="Difficulty", value=data["difficulty"])
                embed.add_field(name="Size", value=f"{data['block_size']} bytes")
                embed.add_field(name="Nonce", value=data["nonce"])
                embed.add_field(
                    name="Number of Transactions", value=data["num_txes"]
                )
                embed.add_field(
                    name="Timestamp",
                    value=f"<t:{data['timestamp']}:F> "
                    f"(<t:{data['timestamp']}:R>)",
                )
                embed.add_field(
                    name="Hash",
                    value=f"[`{data['hash']}`]"
                    f"(https://explorer.nerva.one/detail/{data['hash']})",
                    inline=False,
                )
                embed.add_field(
                    name="Miner Transaction Hash",
                    value=f"[`{data['miner_tx_hash']}`]"
                    f"(https://explorer.nerva.one/detail/{data['miner_tx_hash']})",
                    inline=False,
                )

        await ctx.edit_original_response(embed=embed)


async def setup(bot: RoboNerva):
    await bot.add_cog(Network(bot))
