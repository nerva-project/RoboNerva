from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime, UTC

import discord
import re
from discord.ext import commands, tasks


if TYPE_CHECKING:
    from bot import RoboNerva

from config import (
    COMMUNITY_GUILD_ID,
    UNVERIFIED_USER_ROLE_ID,
    VERIFIED_USER_ROLE_ID,
    NAME_BLACKLIST_REGEX,
    MESSAGE_BLACKLIST_REGEX,
)


class AutoMod(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    @tasks.loop(hours=24)
    async def _auto_mod_check_verified(self):
        guild = self.bot.get_guild(COMMUNITY_GUILD_ID)
        unverified_role = guild.get_role(UNVERIFIED_USER_ROLE_ID)
        verified_role = guild.get_role(VERIFIED_USER_ROLE_ID)

        for member in guild.members:
            if member.bot:
                continue

            if verified_role in member.roles and unverified_role not in member.roles:
                continue

            if member.joined_at is None:
                continue

            if (datetime.now(UTC) - member.joined_at).days >= 1:
                self.bot.log.info(f"Kicking {member} for not verifying within 24h.")
                await member.kick(reason="Not verified within 24h.")

    @_auto_mod_check_verified.before_loop
    async def _before_auto_mod_check_verified(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def _auto_mod_prune_inactive(self):
        guild = self.bot.get_guild(COMMUNITY_GUILD_ID)

        for member in guild.members:
            if member.bot:
                continue

            oldest_message = None

            for channel in guild.text_channels:
                messages = [message async for message in channel.history(limit=300)]
                user_messages = [
                    message for message in messages if message.author == member
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

            if oldest_message is None:
                continue

            if (datetime.now(UTC) - oldest_message.created_at).days >= 180:
                self.bot.log.info(f"Kicking {member} for being inactive for 6M.")
                await member.kick(reason="Inactive for 6M.")

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
        for regex in NAME_BLACKLIST_REGEX:
            if re.search(regex, member.display_name, re.IGNORECASE):
                self.bot.log.info(
                    f"Banning {member} for having a blacklisted name match - {regex}."
                )

                try:
                    await member.send(
                        f"You have been banned from the Nerva community server "
                        f"for having a blacklisted name match - {regex}."
                    )

                except (discord.Forbidden, discord.errors.Forbidden):
                    pass

                await member.ban(reason=f"Blacklisted name match - {regex}.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        for regex in MESSAGE_BLACKLIST_REGEX:
            if re.search(regex, message.content, re.IGNORECASE):
                self.bot.log.info(
                    f"Deleting message from {message.author} for having a "
                    f"blacklisted message match - {regex}."
                )
                await message.delete()

                collection = self.bot.db.get_collection("member_warnings")

                if await collection.find_one({"_id": message.author.id}):
                    await collection.update_one(
                        {"_id": message.author.id}, {"$inc": {"warnings": 1}}
                    )

                else:
                    await collection.insert_one(
                        {"_id": message.author.id, "warnings": 1}
                    )

                if await collection.find_one(
                    {"_id": message.author.id, "warnings": 3}
                ):
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

                else:
                    warning_count = (
                        await collection.find_one({"_id": message.author.id})
                    )["warnings"]

                    try:
                        await message.author.send(
                            "Your message has been deleted because it matched a blacklisted message.\n"
                            "Please refrain from posting such messages in the future.\n"
                            "You have received a warning for this message.\n"
                            f"Warning count: {warning_count}/3\n"
                            "If you receive 3 warnings, you will be banned from the server.\n"
                        )

                    except (discord.Forbidden, discord.errors.Forbidden):
                        pass


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(AutoMod(bot))
