from __future__ import annotations

from typing import TYPE_CHECKING

from datetime import UTC, time, datetime

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from dateutil.parser import parse

import discord
from discord import app_commands
from discord.ext import tasks, commands

from utils.cd import cooldown
from utils.tools import is_admin, validate_tweet_links
from utils.modals import TweetLinksModal

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

        embed.description = (
            "Vote for Nerva on CML:\nhttps://coinmarketleague.com/coin/nerva\n\n"
        )

        if data:
            embed.description += f"Interact on X:\n\n{data['tweet_link_1']}\n"

            if data["tweet_link_2"]:
                embed.description += f"{data['tweet_link_2']}\n"

            if data["tweet_link_3"]:
                embed.description += f"{data['tweet_link_3']}\n"

            embed.description += "\n"

        else:
            embed.description += (
                f"Interact with some replies that you like:\n"
                f"https://x.com/NervaCurrency/with_replies\n\n"
            )

        embed.description += (
            "Join the discussion on Reddit:\n"
            "https://www.reddit.com/r/NervaCrypto\n\n"
        )

        embed.description += "Thank you for supporting Nerva! \U0001f499"

        view = discord.ui.View()

        view.add_item(
            discord.ui.Button(
                label="CML (Nerva)",
                url="https://coinmarketleague.com/coin/nerva",
            )
        )
        view.add_item(
            discord.ui.Button(
                label="X (Twitter)",
                url="https://x.com/NervaCurrency/with_replies",
            )
        )
        view.add_item(
            discord.ui.Button(
                label="Reddit",
                url="https://www.reddit.com/r/NervaCrypto",
            )
        )

        await collection.delete_many({})
        await channel.send("@everyone", embed=embed, view=view)

        try:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "CML (Nerva)",
                        url="https://coinmarketleague.com/coin/nerva",
                    ),
                    InlineKeyboardButton(
                        "X (Twitter)",
                        url="https://x.com/NervaCurrency/with_replies",
                    ),
                    InlineKeyboardButton(
                        "Reddit",
                        url="https://www.reddit.com/r/NervaCrypto",
                    ),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = await self.bot.tg.send_message(
                chat_id=self.bot.config.TELEGRAM_CHAT_ID,
                text=f"Daily Tasks - {embed.title}\n\n{embed.description}",
                reply_markup=reply_markup,
            )

            await self.bot.tg.pin_chat_message(
                chat_id=self.bot.config.TELEGRAM_CHAT_ID,
                message_id=message.message_id,
            )

        except TelegramError as e:
            self.bot.log.error(f"Telegram error: {e}")

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
                "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=nerva",
                headers={"x-cg-demo-api-key": self.bot.config.COINGECKO_API_KEY},
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

        for pair in self.bot.config.TRADEOGRE_MARKET_PAIRS:
            view.add_item(
                discord.ui.Button(
                    label=f"TradeOgre ({pair})",
                    url=f"https://tradeogre.com/exchange/{pair}",
                    row=0,
                )
            )

        for pair in self.bot.config.XEGGEX_MARKET_PAIRS:
            view.add_item(
                discord.ui.Button(
                    label=f"XeggeX ({pair})",
                    url=f"https://xeggex.com/market/{pair.replace('-', '_')}",
                    row=1,
                )
            )

        await channel.send(embed=embed, view=view)

    @_autopost_price_update.before_loop
    async def _before_autopost_price_update(self) -> None:
        await self.bot.wait_until_ready()

    def cog_load(self) -> None:
        self._autopost_vote_reminder.start()
        # Temporarily disabling price update autoposts until CoinGecko listing is back
        # self._autopost_price_update.start()

    def cog_unload(self) -> None:
        self._autopost_vote_reminder.cancel()
        # Temporarily disabling price update autoposts until CoinGecko listing is back
        # self._autopost_price_update.cancel()

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

        await collection.delete_many({})
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
