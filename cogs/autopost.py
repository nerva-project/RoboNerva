from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime, UTC

import aiohttp
from dateutil.parser import parse

import discord
from discord.ext import commands, tasks

if TYPE_CHECKING:
    from bot import RoboNerva


class AutoPost(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @tasks.loop(hours=24)
    async def _autopost_vote_reminder(self):
        channel = self.bot.get_channel(
            self.bot.config.AUTOPOST_VOTE_REMINDER_CHANNEL_ID
        )

        if not channel:
            return

        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(
            name="Nerva",
            icon_url="https://raw.githubusercontent.com/nerva-project/resources/master/Logos/GradientBackground/"
            "nerva-logo-white-on-blue-violet-1024x1024.png",
        )

        embed.title = (
            f"{datetime.now(UTC).strftime('%b %d, %Y')} - Vote for Nerva on CML!"
        )

        embed.description = """
        Interact on X: 
https://x.com/NervaCurrency/status/1824394199480811528
https://x.com/R0BC0D3R/status/1824519475640578192
https://x.com/Evanation81/status/1824563433791950934

Search for crypto related tweets and plug Nerva where appropriate or search for Nerva related posts and interact: 
https://x.com/search?q=(%23Nerva%20OR%20%24XNV)%20OR%20(%40NervaCurrency)&src=typed_query&f=live
        """

        view = discord.ui.View()

        view.add_item(
            discord.ui.Button(
                label="CoinMarketLeague",
                url="https://coinmarketleague.com/coin/nerva",
            )
        )
        view.add_item(
            discord.ui.Button(
                label="X (Twitter)",
                url="https://x.com/search?q=(%23Nerva%20OR%20%24XNV)%20OR%20(%40NervaCurrency)&src=typed_query&f=live",
            )
        )

        await channel.send("@everyone", embed=embed, view=view)

    @_autopost_vote_reminder.before_loop
    async def _before_autopost_vote_reminder(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def _autopost_price_update(self):
        channel = self.bot.get_channel(
            self.bot.config.AUTOPOST_PRICE_UPDATE_CHANNEL_ID
        )

        if not channel:
            return

        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(
            name="Nerva",
            icon_url="https://raw.githubusercontent.com/nerva-project/resources/master/Logos/GradientBackground/"
            "nerva-logo-white-on-blue-violet-1024x1024.png",
        )

        embed.title = f"{datetime.now(UTC).strftime('%b %d, %Y')} - Price Update"

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=nerva"
            ) as res:
                data = await res.json()

                embed.add_field(
                    name="Current Price", value=f"${data[0]['current_price']}"
                )
                embed.add_field(
                    name="Last Updated",
                    value=f"<t:{int(parse(data[0]['last_updated']).timestamp())}:R>",
                )
                embed.add_field(name="Market Cap", value=f"${data[0]['market_cap']}")
                embed.add_field(
                    name="Market Cap Rank", value=data[0]["market_cap_rank"]
                )
                embed.add_field(
                    name="Market Cap Change (24h)",
                    value=f"{round(float(data[0]['market_cap_change_percentage_24h']), 2)}%",
                )
                embed.add_field(name="24h High", value=f"${data[0]['high_24h']}")
                embed.add_field(name="24h Low", value=f"${data[0]['low_24h']}")
                embed.add_field(
                    name="Price Change (24h)",
                    value=f"{round(float(data[0]['price_change_percentage_24h']), 2)}%",
                )
                embed.add_field(
                    name="24h Trading Volume", value=f"${data[0]['total_volume']}"
                )
                embed.add_field(
                    name="Circulating Supply",
                    value=f"{data[0]['circulating_supply']} XNV",
                )
                embed.add_field(
                    name="Total Supply", value=f"{data[0]['total_supply']} XNV"
                )

        embed.set_footer(
            text="Powered by the CoinGecko API",
            icon_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT9xV6Ut4_LMNqb9umIAXW3eu7-unDOiLeNjg&s",
        )

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="CoinGecko",
                url="https://www.coingecko.com/en/coins/nerva",
                row=0,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="TradeOgre (XNV-BTC)",
                url="https://tradeogre.com/exchange/XNV-BTC",
                row=0,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="TradeOgre (XNV-USDT)",
                url="https://tradeogre.com/exchange/XNV-USDT",
                row=1,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="XeggeX (XNV-USDT)",
                url="https://xeggex.com/market/XNV_USDT",
                row=1,
            )
        )

        await channel.send(embed=embed, view=view)

    @_autopost_price_update.before_loop
    async def _before_autopost_price_update(self) -> None:
        await self.bot.wait_until_ready()

    def cog_load(self) -> None:
        self._autopost_vote_reminder.start()
        self._autopost_price_update.start()

    def cog_unload(self) -> None:
        self._autopost_vote_reminder.cancel()
        self._autopost_price_update.cancel()


async def setup(bot: RoboNerva):
    await bot.add_cog(AutoPost(bot))
