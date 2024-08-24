from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime, time, UTC

import aiohttp
import twikit
from dateutil.parser import parse

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils.cd import cooldown
from utils.modals import TweetLinksModal
from utils.tools import is_admin, validate_tweet_links

if TYPE_CHECKING:
    from bot import RoboNerva

from config import COMMUNITY_GUILD_ID, AUTOPOST_MINUTES_AFTER_UTC


class AutoPost(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @tasks.loop(time=time(hour=0, minute=AUTOPOST_MINUTES_AFTER_UTC))
    async def _autopost_vote_reminder(self):
        channel = self.bot.get_channel(
            self.bot.config.AUTOPOST_VOTE_REMINDER_CHANNEL_ID
        )

        if not channel:
            return

        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(
            name="RoboNerva",
            icon_url=self.bot.user.avatar.url,
        )

        embed.title = (
            f"{datetime.now(UTC).strftime('%b %d, %Y')} - Vote for Nerva on CML!"
        )

        collection = self.bot.db.get_collection("autopost_tweet_links")
        data = await collection.find_one({})

        if data:
            embed.description = f"Interact on X:\n\n{data['tweet_link_1']}\n"

            if data["tweet_link_2"]:
                embed.description += f"{data['tweet_link_2']}\n"

            if data["tweet_link_3"]:
                embed.description += f"{data['tweet_link_3']}\n"

            embed.description += "\n"

        else:
            try:
                client = twikit.Client("en-US")

                await client.login(
                    auth_info_1=self.bot.config.TWITTER_USERNAME,
                    auth_info_2=self.bot.config.TWITTER_EMAIL,
                    password=self.bot.config.TWITTER_PASSWORD,
                )

                user = await client.get_user_by_screen_name("NervaCurrency")
                tweets = await client.get_user_tweets(user.id, "Tweets", count=1)

                post_id = tweets[0].id

            except twikit.TwitterException:
                post_id = self.bot.config.FALLBACK_TWEET_ID

            embed.description = (
                f"Interact on X:\n\nhttps://x.com/NervaCurrency/status/{post_id}\n\n"
            )

        embed.description += (
            "Search for crypto related tweets and plug Nerva where appropriate "
            "or search for Nerva related posts and interact:\n\nhttps://x.com/search"
            "?q=(%23Nerva%20OR%20%24XNV)%20OR%20(%40NervaCurrency)&src=typed_query&f=live"
        )

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
                url="https://x.com/search?q=(%23Nerva%20OR%20%24XNV)%20OR%20"
                    "(%40NervaCurrency)&src=typed_query&f=live",
            )
        )

        await collection.delete_many({})
        message = await channel.send("@everyone", embed=embed, view=view)

        await message.pin()

        for _message in await channel.pins():
            if _message.author.id == self.bot.user.id:
                if _message.id != message.id:
                    await _message.unpin()

    @_autopost_vote_reminder.before_loop
    async def _before_autopost_vote_reminder(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(time=time(hour=0, minute=AUTOPOST_MINUTES_AFTER_UTC))
    async def _autopost_price_update(self):
        channel = self.bot.get_channel(
            self.bot.config.AUTOPOST_PRICE_UPDATE_CHANNEL_ID
        )

        if not channel:
            return

        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(
            name="RoboNerva",
            icon_url=self.bot.user.avatar.url,
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
            icon_url="https://encrypted-tbn0.gstatic.com/images?"
            "q=tbn:ANd9GcT9xV6Ut4_LMNqb9umIAXW3eu7-unDOiLeNjg&s",
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

        message = await channel.send(embed=embed, view=view)

        await message.pin()

        for _message in await channel.pins():
            if _message.author.id == self.bot.user.id:
                if _message.id != message.id:
                    await _message.unpin()

    @_autopost_price_update.before_loop
    async def _before_autopost_price_update(self) -> None:
        await self.bot.wait_until_ready()

    def cog_load(self) -> None:
        self._autopost_vote_reminder.start()
        self._autopost_price_update.start()

    def cog_unload(self) -> None:
        self._autopost_vote_reminder.cancel()
        self._autopost_price_update.cancel()

    @app_commands.command(name="upload")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    @app_commands.checks.dynamic_cooldown(cooldown)
    async def _upload(self, ctx: discord.Interaction):
        """(ADMIN) Update tweet links for daily tasks autopost."""
        if not is_admin(ctx.user):
            # noinspection PyUnresolvedReferences
            return await ctx.response.send_message(
                "Only admins can use this command.",
                ephemeral=True,
            )

        modal = TweetLinksModal()
        modal.ctx = ctx

        # noinspection PyUnresolvedReferences
        await ctx.response.send_modal(modal)
        res = await modal.wait()

        if res:
            return

        if not validate_tweet_links(
            [
                modal.tweet_link_1.value,
                modal.tweet_link_2.value,
                modal.tweet_link_3.value,
            ]
        ):
            return await modal.interaction.edit_original_response(
                content="Invalid tweet links! Please try again."
            )

        collection = self.bot.db.get_collection("autopost_tweet_links")
        await collection.insert_one(
            {
                "tweet_link_1": modal.tweet_link_1.value,
                "tweet_link_2": modal.tweet_link_2.value,
                "tweet_link_3": modal.tweet_link_3.value,
            }
        )

        return await modal.interaction.edit_original_response(
            content="Tweet links have been saved."
        )


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(AutoPost(bot))
