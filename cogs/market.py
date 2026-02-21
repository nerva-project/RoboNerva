from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from datetime import UTC, time, datetime, timedelta

import aiohttp
from dateutil.parser import parse

import discord
from discord import app_commands
from discord.ext import tasks, commands
from discord.ext.menus.views import ViewMenuPages

from utils.cd import cooldown
from utils.paginators import (
    NervaExchangePaginatorSource,
    HistoricalPricePaginatorSource,
)

if TYPE_CHECKING:
    from bot import RoboNerva

from config import COMMUNITY_GUILD_ID, MARKET_HISTORY_HOURS_AFTER_UTC


class Market(commands.Cog):
    BASE_API_URL = "https://nervaapi.sn1f3rt.dev/market"

    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    async def _fetch_market(self, exchange: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_API_URL}/{exchange}") as res:
                data = await res.json()

                if data.get("status") != "success":
                    raise RuntimeError(f"API error for {exchange}")

                return data

    @tasks.loop(time=time(hour=MARKET_HISTORY_HOURS_AFTER_UTC))
    async def _store_historical_data(self):
        yesterday_date = datetime.now(UTC) - timedelta(days=1)

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
                headers={"x-cg-demo-api-key": self.bot.config.COINGECKO_API_KEY},
                params=params,
            ) as res:
                data = await res.json()

                collection = self.bot.db["xnv_historical_price_data"]

                if "prices" not in data:
                    opening_price = None
                    closing_price = None
                    high_price = None
                    low_price = None
                    volume = None

                else:
                    prices = data["prices"]
                    volumes = data["total_volumes"]

                    opening_price = prices[0][1]
                    closing_price = prices[-1][1]
                    high_price = max([price[1] for price in prices])
                    low_price = min([price[1] for price in prices])
                    volume = volumes[0][1]

                await collection.insert_one(
                    {
                        "_id": yesterday_date.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        ),
                        "opening": round(opening_price, 4),
                        "closing": round(closing_price, 4),
                        "high": round(high_price, 4),
                        "low": round(low_price, 4),
                        "volume": round(volume, 2),
                    }
                )

                self.bot.log.info(
                    f"Stored historical data for {yesterday_date.strftime('%Y-%m-%d')}"
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
                "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=nerva",
                headers={"x-cg-demo-api-key": self.bot.config.COINGECKO_API_KEY},
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
                    name="24h Trading Volume",
                    value=f"${round(float(data[0]['total_volume']), 4)}",
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

    @app_commands.command(name="nonkyc")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _nonkyc(self, ctx: discord.Interaction):
        """Shows the current Nerva market data from NonKYC."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        api_data = await self._fetch_market("nonkyc")

        market_data: List[Dict] = list()

        for pair in self.bot.config.NONKYC_MARKET_PAIRS:
            entry = api_data["result"][pair]

            market_data.append(
                {
                    "pair": pair,
                    "last_price": entry["last_price"],
                    "bid": entry["bid"],
                    "ask": entry["ask"],
                    "volume": entry["volume"],
                    "high": entry["high"],
                    "low": entry["low"],
                    "last_trade": int(parse(entry["last_trade"]).timestamp()),
                }
            )

        pages = NervaExchangePaginatorSource(
            entries=market_data,
            ctx=ctx,
            exchange_name="NonKYC",
            exchange_urls=self.bot.config.NONKYC_MARKET_LINKS,
            thumbnail_url="https://nonkyc.io/images/mediakit/NonKYC-logo-384.png",
        )

        paginator = ViewMenuPages(
            source=pages,
            timeout=300,
            delete_message_after=False,
            clear_reactions_after=True,
        )

        await ctx.edit_original_response(content="\U0001f44c")
        await paginator.start(ctx)

    @app_commands.command(name="cexswap")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _cexswap(self, ctx: discord.Interaction):
        """Shows the current Nerva market data from CexSwap."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        api_data = await self._fetch_market("cexswap")

        market_data: List[Dict] = list()

        for pair in self.bot.config.CEXSWAP_MARKET_PAIRS:
            entry = api_data["result"][pair]

            market_data.append(
                {
                    "pair": pair,
                    "last_price": entry["last_price"],
                    "volume": entry["volume"],
                    "high": entry["high"],
                    "low": entry["low"],
                }
            )

        pages = NervaExchangePaginatorSource(
            entries=market_data,
            ctx=ctx,
            exchange_name="CexSwap",
            exchange_urls=self.bot.config.CEXSWAP_MARKET_LINKS,
            thumbnail_url="https://cexswap.cc/icons/favicon-32x32.png",
        )

        paginator = ViewMenuPages(
            source=pages,
            timeout=300,
            delete_message_after=False,
            clear_reactions_after=True,
        )

        await ctx.edit_original_response(content="\U0001f44c")
        await paginator.start(ctx)

    @app_commands.command(name="history")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _history(self, ctx: discord.Interaction, days: int = 7):
        """Shows the historical Nerva market data."""
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True)

        collection = self.bot.db["xnv_historical_price_data"]

        if (await collection.count_documents({})) == 0:
            return await ctx.edit_original_response(
                content="No historical data available yet."
            )

        entries = list()

        async for document in collection.find().sort("_id", -1).limit(days):
            entry = {
                "date": document["_id"],
                "opening": document["opening"],
                "closing": document["closing"],
                "high": document["high"],
                "low": document["low"],
                "volume": document["volume"],
            }

            entries.append(entry)

        pages = HistoricalPricePaginatorSource(entries=entries, ctx=ctx)
        paginator = ViewMenuPages(
            source=pages,
            timeout=300,
            delete_message_after=False,
            clear_reactions_after=True,
        )

        await ctx.edit_original_response(content="\U0001f44c")
        await paginator.start(ctx)


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(Market(bot))
