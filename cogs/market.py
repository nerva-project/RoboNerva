from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import time, datetime, timedelta

import aiohttp
from dateutil.parser import parse

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.menus.views import ViewMenuPages

from utils.cd import cooldown
from utils.paginators import TradeOgrePaginatorSource

if TYPE_CHECKING:
    from bot import RoboNerva

from config import COMMUNITY_GUILD_ID, MARKET_HISTORY_HOURS_AFTER_UTC


class Market(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @tasks.loop(time=time(hour=MARKET_HISTORY_HOURS_AFTER_UTC))
    async def _store_historical_data(self):
        yesterday_date = datetime.now() - timedelta(days=1)

        start_timestamp = int(
            yesterday_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ).timestamp()
        )
        end_timestamp = int(
            (yesterday_date + timedelta(days=1))
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
        )

        params = {"vs_currency": "usd", "from": start_timestamp, "to": end_timestamp}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.coingecko.com/api/v3/coins/nerva/market_chart/range",
                params=params,
            ) as res:
                data = await res.json()

                collection = self.bot.db["xnv_historical_price_data"]

                if "prices" not in data:
                    opening_price = None
                    closing_price = None
                    high_price = None
                    low_price = None
                    total_volume = None

                else:
                    prices = data["prices"]
                    total_volumes = data.get("total_volumes", [])

                    opening_price = prices[0][1]
                    closing_price = prices[-1][1]
                    high_price = max([price[1] for price in prices])
                    low_price = min([price[1] for price in prices])
                    total_volume = sum([volume[1] for volume in total_volumes])

                await collection.insert_one(
                    {
                        "date": yesterday_date.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        ),
                        "opening": round(opening_price, 4),
                        "closing": round(closing_price, 4),
                        "high": round(high_price, 4),
                        "low": round(low_price, 4),
                        "volume": round(total_volume),
                    }
                )

    @_store_historical_data.before_loop
    async def _before_store_historical_data(self):
        await self.bot.wait_until_ready()

    def cog_load(self) -> None:
        self._store_historical_data.start()

    def cog_unload(self) -> None:
        self._store_historical_data.cancel()

    @app_commands.command(name="coingecko")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _coingecko(self, ctx: discord.Interaction):
        """Shows various Nerva statistics from CoinGecko."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        embed = discord.Embed(colour=self.bot.embed_color)
        embed.title = "Nerva on CoinGecko"

        embed.set_author(name="RoboNerva", icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(
            url="https://encrypted-tbn0.gstatic.com/images?"
            "q=tbn:ANd9GcT9xV6Ut4_LMNqb9umIAXW3eu7-unDOiLeNjg&s"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=nerva"
            ) as res:
                data = await res.json()

                embed.add_field(
                    name="Current Price",
                    value=f"${round(float(data[0]['current_price']), 4)}",
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
                embed.add_field(
                    name="24h High", value=f"${round(float(data[0]['high_24h']), 4)}"
                )
                embed.add_field(
                    name="24h Low", value=f"${round(float(data[0]['low_24h']), 4)}"
                )
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
            icon_url="https://encrypted-tbn0.gstatic.com/images?"
            "q=tbn:ANd9GcT9xV6Ut4_LMNqb9umIAXW3eu7-unDOiLeNjg&s",
        )

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="CoinGecko",
                url="https://www.coingecko.com/en/coins/nerva",
            )
        )

        await ctx.edit_original_response(embed=embed, view=view)

    @app_commands.command(name="tradeogre")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _tradeogre(self, ctx: discord.Interaction):
        """Shows the current Nerva market data from TradeOgre."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        entries = list()

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://tradeogre.com/api/v1/ticker/xnv-btc"
            ) as res:
                data = await res.json(content_type=None)

                entry = {
                    "pair": "XNV-BTC",
                    "last_price": f"{round(float(data['price']) * 100_000_000)} sat",
                    "bid": f"{round(float(data['bid']) * 100_000_000)} sat",
                    "ask": f"{round(float(data['ask']) * 100_000_000)} sat",
                    "volume": f"{round(float(data['volume']), 5)} BTC",
                    "high": f"{round(float(data['high']) * 100_000_000)} sat",
                    "low": f"{round(float(data['low']) * 100_000_000)} sat",
                }

                entries.append(entry)

            async with session.get(
                "https://tradeogre.com/api/v1/ticker/xnv-usdt"
            ) as res:
                data = await res.json(content_type=None)

                entry = {
                    "pair": "XNV-USDT",
                    "last_price": f"${round(float(data['price']), 4)}",
                    "bid": f"${round(float(data['bid']), 4)}",
                    "ask": f"${round(float(data['ask']), 4)}",
                    "volume": f"${round(float(data['volume']), 4)}",
                    "high": f"${round(float(data['high']), 4)}",
                    "low": f"${round(float(data['low']), 4)}",
                }

                entries.append(entry)

        pages = TradeOgrePaginatorSource(entries=entries, ctx=ctx)
        paginator = ViewMenuPages(
            source=pages,
            timeout=300,
            delete_message_after=False,
            clear_reactions_after=True,
        )

        await ctx.edit_original_response(content="\U0001F44C")
        await paginator.start(ctx)

    @app_commands.command(name="xeggex")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _xeggex(self, ctx: discord.Interaction):
        """Shows the current Nerva market data from Xeggex."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        embed = discord.Embed(colour=self.bot.embed_color)
        embed.title = "XNV-USDT on Xeggex"

        embed.set_author(name="RoboNerva", icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(
            url="https://encrypted-tbn0.gstatic.com/images?"
            "q=tbn:ANd9GcQge9tw8HHcbwBXNALMQvysPoL6s-bFhJjA3g&s"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.xeggex.com/api/v2/market/getbysymbol/XNV_USDT"
            ) as res:
                data = await res.json()

                embed.add_field(
                    name="Last Price", value=f"${round(float(data['lastPrice']), 4)}"
                )
                embed.add_field(
                    name="Bid", value=f"${round(float(data['bestBid']), 4)}"
                )
                embed.add_field(
                    name="Ask", value=f"${round(float(data['bestAsk']), 4)}"
                )
                embed.add_field(
                    name="Volume", value=f"{round(float(data['volume']), 4)}"
                )
                embed.add_field(
                    name="High", value=f"${round(float(data['highPrice']), 4)}"
                )
                embed.add_field(
                    name="Low", value=f"${round(float(data['lowPrice']), 4)}"
                )
                embed.add_field(
                    name="Last Trade",
                    value=f"<t:{data['lastTradeAt'] // 1000}:F> "
                    f"(<t:{data['lastTradeAt'] // 1000}:R>)",
                )

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Xeggex (XNV-USDT)",
                url="https://xeggex.com/market/XNV_USDT",
            )
        )

        await ctx.edit_original_response(embed=embed, view=view)

    @app_commands.command(name="history")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _history(self, ctx: discord.Interaction):
        """Shows the historical Nerva market data."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        collection = self.bot.db["xnv_historical_price_data"]

        if (await collection.count_documents({})) == 0:
            return await ctx.edit_original_response(
                content="No historical data available yet."
            )

        entries = list()

        async for document in collection.find().sort("date", -1).limit(100):
            entry = {
                "date": document["date"],
                "opening": document["opening"],
                "closing": document["closing"],
                "high": document["high"],
                "low": document["low"],
                "volume": document["volume"],
            }

            entries.append(entry)

        pages = TradeOgrePaginatorSource(entries=entries, ctx=ctx)
        paginator = ViewMenuPages(
            source=pages,
            timeout=300,
            delete_message_after=False,
            clear_reactions_after=True,
        )

        await ctx.edit_original_response(content="\U0001F44C")
        await paginator.start(ctx)


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(Market(bot))
