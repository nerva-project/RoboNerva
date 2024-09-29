from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.menus.views import ViewMenuPages

from utils.cd import cooldown
from utils.tools import (
    is_admin,
    calculate_hashrate,
    calculate_database_size,
    calculate_seconds_from_time_string,
)
from utils.paginators import IPBanPaginatorSource

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
            async with session.get(f"{self.bot.api_url}/daemon/get_info/") as res:
                data = (await res.json())["result"]

                embed.add_field(name="Height", value=data["height"])
                embed.add_field(name="Difficulty", value=data["difficulty"])
                embed.add_field(
                    name="Network Hashrate",
                    value=calculate_hashrate(data["difficulty"]),
                )
                embed.add_field(name="", value="")
                embed.add_field(
                    name="Database Size",
                    value=calculate_database_size(data["database_size"]),
                )
                embed.add_field(
                    name="Top Block Hash",
                    value=f"[`{data['top_block_hash']}`]"
                    f"(https://explorer.nerva.one/detail/{data['top_block_hash']})",
                    inline=False,
                )

            async with session.get(
                f"{self.bot.api_url}/daemon/get_last_block_header/"
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
            async with session.get(f"{self.bot.api_url}/daemon/get_info/") as res:
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
            async with session.get(f"{self.bot.api_url}/daemon/get_info/") as res:
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
            async with session.get(f"{self.bot.api_url}/daemon/get_info/") as res:
                data = (await res.json())["result"]

                hashrate = calculate_hashrate(data["difficulty"])

        await ctx.edit_original_response(
            content=f"The current network hashrate is `{hashrate}`."
        )

    @app_commands.command(name="supply")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _supply(self, ctx: discord.Interaction):
        """Shows the current circulating supply."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.bot.api_url}/daemon/get_generated_coins/"
            ) as res:
                supply = await res.json()

        await ctx.edit_original_response(
            content=f"The current circulating supply is `{supply} XNV`."
        )

    @app_commands.command(name="seeds")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _seeds(self, ctx: discord.Interaction):
        """Shows the list of seed nodes."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        if not self.bot.seed_nodes:
            return await ctx.edit_original_response(
                content="There are no seed nodes available at the moment."
            )

        embed = discord.Embed(color=self.bot.embed_color)
        embed.title = "Seed Nodes List"
        embed.description = ""

        embed.set_author(name="RoboNerva", icon_url=self.bot.user.avatar.url)

        for i, node in enumerate(self.bot.seed_nodes, start=1):
            embed.description += f"`{i}`. {node}\n"

        await ctx.edit_original_response(embed=embed)

    @app_commands.command(name="seedinfo")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _seed_info(self, ctx: discord.Interaction):
        """Shows information about the seed node."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        embed = discord.Embed(color=self.bot.embed_color)
        embed.title = "Seed Node Information"

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.bot.api_url}/daemon/get_info/") as res:
                data = (await res.json())["result"]

                embed.add_field(name="Version", value=data["version"])
                embed.add_field(
                    name="Height", value=f"{data['height']}/{data['target_height']}"
                )
                embed.add_field(
                    name="Incoming Connections",
                    value=data["incoming_connections_count"],
                )
                embed.add_field(
                    name="Outgoing Connections",
                    value=data["outgoing_connections_count"],
                )
                embed.add_field(
                    name="Network Hashrate",
                    value=calculate_hashrate(data["difficulty"]),
                )
                embed.add_field(
                    name="Top Block Hash",
                    value=f"[`{data['top_block_hash']}`]"
                    f"(https://explorer.nerva.one/detail/{data['top_block_hash']})",
                    inline=False,
                )

        await ctx.edit_original_response(embed=embed)

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
                f"{self.bot.api_url}/daemon/get_last_block_header/"
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

    @app_commands.command(name="inflation")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _inflation(self, ctx: discord.Interaction):
        """Shows the current inflation rate."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        new_xnv_per_year = 157788
        new_xnv_per_month = 13149
        new_xnv_per_week = 3024
        new_xnv_per_day = 432

        embed = discord.Embed(color=self.bot.embed_color)
        embed.title = "Nerva Inflation Information"
        embed.description = (
            "<:nerva:1274417479606603776> is already in tail emission which means that each block has "
            "0.3 XNV (+ transaction fee) miner reward. **Below numbers are estimates.**"
        )

        embed.set_author(name="RoboNerva", icon_url=self.bot.user.avatar.url)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.bot.api_url}/daemon/get_generated_coins/"
            ) as res:
                coins = await res.json()

                embed.add_field(
                    name="Current Annual Inflation Percentage",
                    value=f"{(new_xnv_per_year/coins) * 100:.3f}%",
                    inline=False,
                )

                embed.add_field(name="New XNV per year", value=new_xnv_per_year)
                embed.add_field(name="New XNV per month", value=new_xnv_per_month)
                embed.add_field(name="New XNV per week", value=new_xnv_per_week)
                embed.add_field(name="New XNV per day", value=new_xnv_per_day)

        await ctx.edit_original_response(embed=embed)

    @app_commands.command(name="bans")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _bans(self, ctx: discord.Interaction):
        """Shows the list of banned IP addresses."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.bot.api_url}/daemon/get_bans/") as res:
                bans = (await res.json())["result"]

        if "bans" not in bans.keys():
            return await ctx.edit_original_response(content="There are no IP bans.")

        pages = IPBanPaginatorSource(entries=bans, ctx=ctx)
        paginator = ViewMenuPages(
            source=pages,
            timeout=300,
            delete_message_after=False,
            clear_reactions_after=True,
        )

        await ctx.edit_original_response(content="\U0001f44c")
        await paginator.start(ctx)

    @app_commands.command(name="ban")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _ban(self, ctx: discord.Interaction, ip: str, time: str):
        """(ADMIN) Bans an IP address.

        Parameters
        ----------
        ip : str
            The IP address to ban.
        time : str
            The time to ban the IP address for. (eg: 1w, 3d 12h, 5m etc.)

        """
        if not is_admin(ctx.user):
            # noinspection PyUnresolvedReferences
            return await ctx.response.send_message(
                content="Only admins can use this command.",
                ephemeral=True,
            )

        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        node_count = len(self.bot.api_nodes)
        pass_count = 0

        async with aiohttp.ClientSession() as session:
            for node in self.bot.api_nodes:
                async with session.get(
                    f"{node}/daemon/set_bans?ip={ip}&ban=true&"
                    f"time={calculate_seconds_from_time_string(time)}"
                ) as res:
                    data = (await res.json())["result"]

                    if data["status"] == "OK":
                        pass_count += 1

        if pass_count == 0:
            return await ctx.edit_original_response(
                content="Failed to ban IP from all seed nodes."
            )

        elif pass_count < node_count:
            return await ctx.edit_original_response(
                content="Partially banned IP from seed nodes."
            )

        await ctx.edit_original_response(
            content="Successfully banned IP from all seed nodes."
        )

    @app_commands.command(name="unban")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _unban(self, ctx: discord.Interaction, ip: str):
        """Unbans an IP address.

        Parameters
        ----------
        ip : str
            The IP address to unban.

        """
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        node_count = len(self.bot.api_nodes)
        pass_count = 0

        async with aiohttp.ClientSession() as session:
            for node in self.bot.api_nodes:
                async with session.get(
                    f"{node}/daemon/set_bans?ip={ip}&ban=false&time=0"
                ) as res:
                    data = (await res.json())["result"]

                    if data["status"] == "OK":
                        pass_count += 1

        if pass_count == 0:
            return await ctx.edit_original_response(
                content="Failed to unban IP from all seed nodes."
            )

        elif pass_count < node_count:
            return await ctx.edit_original_response(
                content="Partially unbanned IP from seed nodes."
            )

        await ctx.edit_original_response(
            content="Successfully unbanned IP from all seed nodes."
        )


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(Network(bot))
