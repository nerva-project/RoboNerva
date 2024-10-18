from __future__ import annotations

from typing import TYPE_CHECKING

import math
from datetime import UTC, datetime

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from utils.cd import cooldown

from config import COMMUNITY_GUILD_ID

if TYPE_CHECKING:
    from bot import RoboNerva


class General(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @app_commands.command(name="ping")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _ping(self, ctx: discord.Interaction):
        """Shows the API and bot latency."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        embed = discord.Embed(colour=self.bot.embed_color)
        embed.description = "**Pong!**"

        ms = self.bot.latency * 1000

        embed.add_field(name="API latency (Heartbeat)", value=f"`{int(ms)} ms`")

        t1 = datetime.now(UTC).strftime("%f")

        await ctx.edit_original_response(embed=embed)

        t2 = datetime.now(UTC).strftime("%f")
        diff = int(math.fabs((int(t2) - int(t1)) / 1000))

        embed.add_field(name="Bot latency (Round-trip)", value=f"`{diff} ms`")

        await ctx.edit_original_response(embed=embed)

    @app_commands.command(name="uptime")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _uptime(self, ctx: discord.Interaction):
        """Shows how long has RoboNerva has been up for."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        await ctx.edit_original_response(
            content=f"I have been up since "
            f"<t:{int(self.bot.launch_time.timestamp())}:F> "
            f"(<t:{int(self.bot.launch_time.timestamp())}:R>)."
        )

    @app_commands.command(name="web")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _web(self, ctx: discord.Interaction):
        """Shows the links to various Nerva resources on the web."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(label="Website", url="https://nerva.one", row=0)
        )
        view.add_item(
            discord.ui.Button(
                label="Explorer", url="https://explorer.nerva.one", row=0
            )
        )
        view.add_item(
            discord.ui.Button(label="Docs", url="https://docs.nerva.one", row=0)
        )
        view.add_item(
            discord.ui.Button(
                label="GitHub", url="https://github.com/nerva-project", row=1
            )
        )
        view.add_item(
            discord.ui.Button(
                label="X (Twitter)", url="https://x.com/NervaCurrency", row=1
            )
        )
        view.add_item(
            discord.ui.Button(
                label="YouTube",
                url="https://www.youtube.com/channel/UC84v_i1iNZrLUUA9XbhuCAQ",
                row=1,
            )
        )

        await ctx.edit_original_response(
            content="Here are the links to various Nerva resources on the web:",
            view=view,
        )

    @app_commands.command(name="community")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _community(self, ctx: discord.Interaction):
        """Sends the invite to the Nerva community server."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Community Server Invite", url="https://discord.gg/ufysfvcFwe"
            )
        )

        await ctx.edit_original_response(
            content="Join the community server for help & updates!", view=view
        )

    @app_commands.command(name="exchanges")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _exchanges(self, ctx: discord.Interaction):
        """Shows the links to various Nerva exchanges."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        view = discord.ui.View()

        for pair in self.bot.config.TRADEOGRE_MARKET_PAIRS:
            view.add_item(
                discord.ui.Button(
                    label=f"TradeOgre ({pair})",
                    url=f"https://tradeogre.com/exchange/{pair}",
                )
            )

        for pair in self.bot.config.XEGGEX_MARKET_PAIRS:
            view.add_item(
                discord.ui.Button(
                    label=f"XeggeX ({pair})",
                    url=f"https://xeggex.com/market/{pair.replace('-', '_')}",
                )
            )

        await ctx.edit_original_response(
            content="Here are the links to various Nerva trading pairs!", view=view
        )

    @app_commands.command(name="downloads")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _downloads(self, ctx: discord.Interaction):
        """Shows the links to various Nerva downloads."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        embed = discord.Embed(colour=self.bot.embed_color)
        embed.title = "Nerva Downloads"

        embed.set_author(name="RoboNerva", icon_url=self.bot.user.avatar.url)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.github.com/repos/nerva-project/nerva/releases/latest",
                headers={"Authorization": f"Bearer {self.bot.config.GITHUB_TOKEN}"},
            ) as res:
                data = await res.json()

                cli_version = data["tag_name"]
                cli_prerelease = data["prerelease"]

            async with session.get(
                "https://api.github.com/repos/nerva-project/NervaOneWalletMiner/releases/latest",
                headers={"Authorization": f"Bearer {self.bot.config.GITHUB_TOKEN}"},
            ) as res:
                data = await res.json()

                gui_version = data["tag_name"]
                gui_prerelease = data["prerelease"]

        embed.description = (
            f"Latest CLI version: **{cli_version} "
            f"({'prerelease' if cli_prerelease else 'stable'})**"
            f"\nLatest GUI version: **{gui_version} "
            f"({'prerelease' if gui_prerelease else 'stable'})**"
        )

        view = discord.ui.View()

        view.add_item(
            discord.ui.Button(
                label="CLI: Windows, 64-bit",
                url=f"https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/nerva-windows-x64-{cli_version}.zip",
                row=0,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="CLI: Windows, 32-bit",
                url=f"https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/nerva-windows-x32-{cli_version}.zip",
                row=0,
            )
        )

        view.add_item(
            discord.ui.Button(
                label="CLI: macOS, Intel",
                url=f"https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/nerva-macos-x64-{cli_version}.tar.bz2",
                row=0,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="CLI: macOS, ARM",
                url=f"https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/nerva-macos-armv8-{cli_version}.tar.bz2",
                row=0,
            )
        )

        view.add_item(
            discord.ui.Button(
                label="CLI: FreeBSD, 64-bit",
                url=f"https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/nerva-freebsd-x86_64-{cli_version}.tar.bz2",
                row=0,
            )
        )

        view.add_item(
            discord.ui.Button(
                label="CLI: Linux, 64-bit",
                url=f"https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/nerva-linux-x86_64-{cli_version}.tar.bz2",
                row=1,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="CLI: Linux, 32-bit",
                url=f"https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/nerva-linux-i686-{cli_version}.tar.bz2",
                row=1,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="CLI: Linux, armv7",
                url=f"https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/nerva-linux-armv7-{cli_version}.tar.bz2",
                row=1,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="CLI: Linux, armv8",
                url=f"https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/nerva-linux-armv8-{cli_version}.tar.bz2",
                row=1,
            )
        )

        view.add_item(
            discord.ui.Button(
                label="GUI: Windows",
                url=f"https://github.com/nerva-project/NervaOneWalletMiner/releases/download/"
                f"{gui_version}/nervaone-desktop-{gui_version}_win-x64.zip",
                row=2,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="GUI: Linux",
                url=f"https://github.com/nerva-project/NervaOneWalletMiner/releases/download/"
                f"{gui_version}/nervaone-desktop-{gui_version}_linux-x64.zip",
                row=2,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="GUI: macOS",
                url=f"https://github.com/nerva-project/NervaOneWalletMiner/releases/download/"
                f"{gui_version}/nervaone-desktop-{gui_version}_osx-x64.zip",
                row=2,
            )
        )

        view.add_item(
            discord.ui.Button(
                label="Utils: p2pstate file",
                url="https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/p2pstate.nerva.v11.bin",
                row=3,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="Utils: Quicksync",
                url="https://github.com/nerva-project/nerva/releases/download/"
                f"{cli_version}/p2pstate.nerva.v11.bin",
                row=3,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="Utils: Blockchain database",
                url="https://nerva.one/database/nerva_blockchain_db.zip",
                row=3,
            )
        )

        await ctx.edit_original_response(embed=embed, view=view)


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(General(bot))
