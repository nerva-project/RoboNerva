from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime, UTC

import re

import discord
from discord.ext import commands, tasks

from utils.tools import is_admin

if TYPE_CHECKING:
    from bot import RoboNerva

from config import COMMUNITY_GUILD_ID


class AutoMod(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @tasks.loop(hours=24)
    async def _auto_mod_check_verified(self):
        guild = self.bot.get_guild(COMMUNITY_GUILD_ID)
        unverified_role = guild.get_role(self.bot.config.UNVERIFIED_USER_ROLE_ID)
        verified_role = guild.get_role(self.bot.config.VERIFIED_USER_ROLE_ID)

        async for member in guild.fetch_members(limit=None):
            if member.bot or is_admin(member):
                continue

            if verified_role in member.roles and unverified_role not in member.roles:
                continue

            if member.joined_at is None:
                continue

            if (datetime.now(UTC) - member.joined_at).days >= 1:
                self.bot.log.info(f"Kicking {member} for not verifying within 24h.")

                await member.kick(reason="Not verified within 24h.")

                await self.bot.webhook.send(
                    f"**{member}** has been kicked for not verifying within 24h."
                )

    @_auto_mod_check_verified.before_loop
    async def _before_auto_mod_check_verified(self) -> None:
        await self.bot.wait_until_ready()

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

                except discord.errors.DiscordServerError:
                    continue

            else:
                try:
                    data = await member_collection.find_one({"_id": member.id})
                    oldest_message = await guild.get_channel(
                        data["last_message"]["channel_id"]
                    ).fetch_message(data["last_message"]["id"])

                except discord.errors.NotFound:
                    oldest_message = None

            if oldest_message is None:
                continue

            if (datetime.now(UTC) - oldest_message.created_at).days > 180:
                warnings = await inactivity_collection.find_one({"_id": member.id})

                if warnings is not None and warnings["count"] >= 2:
                    self.bot.log.info(f"Kicking {member} for being inactive for 6M.")

                    # await member.kick(reason="Inactive for 6M.")

                    await inactivity_collection.delete_one({"_id": member.id})

                    await self.bot.webhook.send(
                        f"[SANDBOX] **{member}** has been kicked for being inactive for 6M.\n"
                        f"Oldest message: {oldest_message.jump_url}\n"
                        f"Days since last message: {(datetime.now(UTC) - oldest_message.created_at).days}"
                    )

                else:
                    if warnings is not None and warnings["count"] == 1:
                        self.bot.log.info(
                            f"Warning {member} for being inactive for 6M. "
                            f"Warning count: 2/2."
                        )

                        await inactivity_collection.update_one(
                            {"_id": member.id}, {"$inc": {"count": 1}}
                        )

                        await member.send(
                            "Hi! This is a friendly reminder that you have been inactive "
                            "for the last 6 months in the Nerva community server. "
                            f"You have not sent any message since `{oldest_message.created_at}`. "
                            "If you would like to stay please post something within the next "
                            "24 hours, or else I will remove you."
                        )

                    else:
                        self.bot.log.info(
                            f"Warning {member} for being inactive for 6M. "
                            f"Warning count: 1/2."
                        )

                        await inactivity_collection.insert_one(
                            {"_id": member.id, "count": 1}
                        )

                        await member.send(
                            "Hi! This is a friendly reminder that you have been inactive "
                            "for the last 6 months in the Nerva community server. "
                            f"You have not sent any message since `{oldest_message.created_at}`. "
                            "If you would like to stay please post something within the next "
                            "three days, or else I will remove you."
                        )

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

            elif (datetime.now(UTC) - oldest_message.created_at).days > 177:
                self.bot.log.info(
                    f"Warning {member} for being inactive for 6M. "
                    f"Warning count: 1/2."
                )

                warnings = await inactivity_collection.find_one({"_id": member.id})

                if warnings:
                    await inactivity_collection.delete_one({"_id": member.id})

                await inactivity_collection.insert_one({"id": member.id, "count": 1})

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

            else:
                pass

    @_auto_mod_prune_inactive.before_loop
    async def _before_auto_mod_prune_inactive(self) -> None:
        await self.bot.wait_until_ready()

    def cog_load(self) -> None:
        self._auto_mod_check_verified.start()
        self._auto_mod_prune_inactive.start()

    def cog_unload(self) -> None:
        self._auto_mod_check_verified.cancel()
        self._auto_mod_prune_inactive.cancel()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        self.bot.log.info(f"Member join: {member} - {member.display_name}")

        for regex in self.bot.config.NAME_BLACKLIST_REGEX:
            self.bot.log.info(
                f"Checking {member.display_name} against {regex} - "
                f"{bool(re.search(regex, member.display_name, re.IGNORECASE))}"
            )

            if re.search(regex, member.display_name, re.IGNORECASE):
                self.bot.log.info(
                    f"Banning {member} for having a blacklisted name match - {regex}."
                )

                try:
                    await member.send(
                        f"You have been banned from the Nerva community server "
                        f"for having a blacklisted name match - `{regex}`."
                    )

                except (discord.Forbidden, discord.errors.Forbidden):
                    pass

                await member.ban(reason=f"Blacklisted name match - {regex}.")

                return await self.bot.webhook.send(
                    f"**{member}** has been banned for having a blacklisted name match - `{regex}`."
                )

    @commands.Cog.listener()
    async def on_member_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        self.bot.log.info(
            f"Member update: {before.display_name} -> {after.display_name}"
        )

        if before.display_name == after.display_name:
            return

        for regex in self.bot.config.NAME_BLACKLIST_REGEX:
            self.bot.log.info(
                f"Checking {after.display_name} against {regex} - "
                f"{bool(re.search(regex, after.display_name, re.IGNORECASE))}"
            )

            if re.search(regex, after.display_name, re.IGNORECASE):
                self.bot.log.info(
                    f"Kicking {after} for having a blacklisted name match - {regex}."
                )

                try:
                    await after.send(
                        f"You have been banned from the Nerva community server "
                        f"for having a blacklisted name match - `{regex}`."
                    )

                except (discord.Forbidden, discord.errors.Forbidden):
                    pass

                await after.ban(reason=f"Blacklisted name match - {regex}.")

                return await self.bot.webhook.send(
                    f"**{after}** has been banned for having a blacklisted name match - `{regex}`."
                )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
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

        for regex in self.bot.config.MESSAGE_BLACKLIST_REGEX:
            if re.search(regex, message.content, re.IGNORECASE):
                self.bot.log.info(
                    f"Deleting message from {message.author} for having a "
                    f"blacklisted message match - `{regex}`."
                )

                await message.delete()

                await self.bot.webhook.send(
                    f"**{message.author}**'s message has been deleted for having a "
                    f"blacklisted message match - `{regex}`."
                )

                collection = self.bot.db.get_collection(
                    "member_blacklisted_message_warnings"
                )

                if await collection.find_one({"_id": message.author.id}):
                    await collection.update_one(
                        {"_id": message.author.id}, {"$inc": {"count": 1}}
                    )

                else:
                    await collection.insert_one(
                        {"_id": message.author.id, "count": 1}
                    )

                if await collection.find_one({"_id": message.author.id, "count": 3}):
                    self.bot.log.info(
                        f"Banning {message.author} for having 3 warnings for blacklisted messages."
                    )

                    try:
                        await message.author.send(
                            "You have been banned from the Nerva community server "
                            "for receiving 3 warnings for blacklisted message matches."
                        )

                    except (discord.Forbidden, discord.errors.Forbidden):
                        pass

                    await message.author.ban(
                        reason="3 warnings received for blacklisted message matches."
                    )

                    await collection.delete_one({"_id": message.author.id})

                    await self.bot.webhook.send(
                        f"**{message.author}** has been banned for receiving "
                        f"3 warnings for blacklisted message matches."
                    )

                else:
                    warning_count = (
                        await collection.find_one({"_id": message.author.id})
                    )["count"]

                    self.bot.log.info(
                        f"Warning {message.author} for blacklisted message match. "
                        f"Matched regex: `{regex}`. "
                        f"Warning count: **{warning_count}/3**."
                    )

                    try:
                        await message.author.send(
                            "Your message has been deleted because it matched a blacklisted message.\n"
                            "Please refrain from posting such messages in the future.\n"
                            "You have received a warning for this message.\n"
                            f"Warning count: **{warning_count}/3**\n"
                            "If you receive 3 warnings, you will be banned from the server.\n"
                            "If you believe this was a mistake, please contact a moderator."
                            "Your message:\n"
                            f"```\n{message.content}\n```"
                        )

                    except (discord.Forbidden, discord.errors.Forbidden):
                        pass

        collection = self.bot.db.get_collection("guild_members")

        if (await collection.find_one({"_id": message.author.id})) is None:
            await collection.insert_one(
                {
                    "_id": message.author.id,
                    "verified": True,
                    "last_message": {
                        "id": message.id,
                        "channel_id": message.channel.id,
                    },
                }
            )

        else:
            await collection.update_one(
                {"_id": message.author.id},
                {
                    "$set": {
                        "last_message": {
                            "id": message.id,
                            "channel_id": message.channel.id,
                        }
                    }
                },
            )


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(AutoMod(bot))
