# Consensus to not implement this feature.
# This is a placeholder for future use.

from __future__ import annotations

from typing import TYPE_CHECKING

from datetime import UTC, datetime

import discord
from discord.ext import tasks, commands

from utils.tools import is_admin

if TYPE_CHECKING:
    from bot import RoboNerva

from config import COMMUNITY_GUILD_ID


class Inactivity(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @tasks.loop(hours=24)
    async def _auto_mod_prune_inactive(self):
        guild = self.bot.get_guild(COMMUNITY_GUILD_ID)

        member_collection = self.bot.db.get_collection("guild_members")
        inactivity_collection = self.bot.db.get_collection(
            "member_inactivity_warnings"
        )

        async for member in guild.fetch_members(limit=None):
            if member.bot or is_admin(member):
                continue

            if (
                await member_collection.find_one({"_id": member.id})
            ) is None or "last_message" not in (
                await member_collection.find_one({"_id": member.id})
            ):
                oldest_message = None

                try:
                    for channel in guild.text_channels:
                        messages = [
                            message
                            async for message in channel.history(
                                limit=self.bot.config.AUTOMOD_CHANNEL_HISTORY_MESSAGE_LIMIT
                            )
                        ]
                        user_messages = [
                            message
                            for message in messages
                            if message.author == member
                        ]
                        user_messages.reverse()

                        if not user_messages:
                            continue

                        message = user_messages[0]

                        if oldest_message is None:
                            oldest_message = message

                        else:
                            if message.created_at > oldest_message.created_at:
                                oldest_message = message

                    if (
                        await member_collection.find_one({"_id": member.id}) is None
                        and oldest_message is not None
                    ):
                        await member_collection.update_one(
                            {"_id": member.id},
                            {
                                "$set": {
                                    "last_message": {
                                        "id": oldest_message.id,
                                        "channel_id": oldest_message.channel.id,
                                    }
                                }
                            },
                            upsert=True,
                        )

                except discord.errors.DiscordException:
                    continue

            else:
                try:
                    data = await member_collection.find_one({"_id": member.id})

                    channel = await guild.fetch_channel(
                        data["last_message"]["channel_id"]
                    )

                    if channel is None:
                        oldest_message = None

                    else:
                        oldest_message = await channel.fetch_message(
                            data["last_message"]["id"]
                        )

                except discord.errors.DiscordException:
                    await member_collection.update_one(
                        {"_id": member.id}, {"$unset": {"last_message": ""}}
                    )
                    oldest_message = None

            if oldest_message is None:
                continue

            if (datetime.now(UTC) - oldest_message.created_at).days > 180:
                warnings = await inactivity_collection.find_one({"_id": member.id})

                if warnings is not None and warnings["count"] >= 2:
                    self.bot.log.info(f"Kicking {member} for being inactive for 6M.")

                    # await member.kick(reason="Inactive for 6M.")

                    await inactivity_collection.delete_one({"_id": member.id})

                    await self.bot.log_hook.send(
                        f"[SANDBOX] **{member}** has been kicked for being inactive for 6M.\n"
                        f"Oldest message: {oldest_message.jump_url}\n"
                        f"Days since last message: {(datetime.now(UTC) - oldest_message.created_at).days}"
                    )

                    continue

                else:
                    if warnings is not None and warnings["count"] == 1:
                        self.bot.log.info(
                            f"Warning {member} for being inactive for 6M. "
                            f"Warning count: 2/2."
                        )

                        await inactivity_collection.update_one(
                            {"_id": member.id}, {"$inc": {"count": 1}}
                        )

                        await self.bot.log_hook.send(
                            f"**{member}** has been warned for being inactive for 6M. "
                            f"Warning count: 2/2.\n"
                            f"Oldest message: {oldest_message.jump_url}\n"
                        )

                        """
                        await member.send(
                            "Hi! This is a friendly reminder that you have been inactive "
                            "for the last 6 months in the Nerva community server. "
                            f"You have not sent any message since `{oldest_message.created_at}`. "
                            "If you would like to stay please post something within the next "
                            "24 hours, or else I will remove you."
                        )
                        """
                        continue

                    else:
                        self.bot.log.info(
                            f"Warning {member} for being inactive for 6M. "
                            f"Warning count: 1/2."
                        )

                        await inactivity_collection.insert_one(
                            {"_id": member.id, "count": 1}
                        )

                        await self.bot.log_hook.send(
                            f"**{member}** has been warned for being inactive for 6M. "
                            f"Warning count: 1/2.\n"
                            f"Oldest message: {oldest_message.jump_url}\n"
                        )

                        """
                        await member.send(
                            "Hi! This is a friendly reminder that you have been inactive "
                            "for the last 6 months in the Nerva community server. "
                            f"You have not sent any message since `{oldest_message.created_at}`. "
                            "If you would like to stay please post something within the next "
                            "three days, or else I will remove you."
                        )
                        """
                        continue

            elif (datetime.now(UTC) - oldest_message.created_at).days > 179:
                self.bot.log.info(
                    f"Warning {member} for being inactive for 6M. "
                    f"Warning count: 2/2."
                )

                warnings = await inactivity_collection.find_one({"_id": member.id})

                if warnings is not None:
                    await inactivity_collection.update_one(
                        {"_id": member.id}, {"$inc": {"count": 1}}
                    )

                else:
                    await inactivity_collection.insert_one(
                        {"_id": member.id, "count": 1}
                    )

                await self.bot.log_hook.send(
                    f"Warning {member} for being inactive for 6M. "
                    f"Warning count: 2/2."
                    f"Oldest message: {oldest_message.jump_url}"
                )

                """
                try:
                    await member.send(
                        "Hi! This is a friendly reminder that you have been inactive "
                        "for the last 6 months in the Nerva community server. "
                        f"You have not sent any message since `{oldest_message.created_at}`. "
                        "If you would like to stay please post something within the next "
                        "24 hours, or else I will remove you."
                    )

                except (discord.Forbidden, discord.errors.Forbidden):
                    pass
                """
                continue

            elif (datetime.now(UTC) - oldest_message.created_at).days > 177:
                self.bot.log.info(
                    f"Warning {member} for being inactive for 6M. "
                    f"Warning count: 1/2."
                )

                warnings = await inactivity_collection.find_one({"_id": member.id})

                if warnings:
                    await inactivity_collection.delete_one({"_id": member.id})

                await inactivity_collection.insert_one({"id": member.id, "count": 1})

                """
                try:
                    await member.send(
                        "Hi! This is a friendly reminder that you have been inactive "
                        "for the last 6 months in the Nerva community server. "
                        f"You have not sent any message since `{oldest_message.created_at}`. "
                        "If you would like to stay please post something within the next "
                        "three days, or else I will remove you."
                    )

                except (discord.Forbidden, discord.errors.Forbidden):
                    pass
                """
                continue

            else:
                continue

    @_auto_mod_prune_inactive.before_loop
    async def _before_auto_mod_prune_inactive(self) -> None:
        await self.bot.wait_until_ready()

    def cog_load(self) -> None:
        self._auto_mod_prune_inactive.start()

    def cog_unload(self) -> None:
        self._auto_mod_prune_inactive.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None:
            return

        if message.author.bot or is_admin(message.author):
            return

        collection = self.bot.db.get_collection("member_inactivity_warnings")

        if await collection.find_one({"_id": message.author.id}):
            await collection.delete_one({"_id": message.author.id})

            try:
                await message.author.send(
                    "Hi! Your post has been noted. Thank you for choosing to stay with us."
                )

            except (discord.Forbidden, discord.errors.Forbidden):
                pass


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(Inactivity(bot))
