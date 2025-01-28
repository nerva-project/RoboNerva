from __future__ import annotations

from typing import TYPE_CHECKING

import re
from datetime import UTC, datetime

import discord
from discord.ext import tasks, commands

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

                await self.bot.log_hook.send(
                    f"**{member}** has been kicked for not verifying within 24h."
                )

    @_auto_mod_check_verified.before_loop
    async def _before_auto_mod_check_verified(self) -> None:
        await self.bot.wait_until_ready()

    def cog_load(self) -> None:
        self._auto_mod_check_verified.start()

    def cog_unload(self) -> None:
        self._auto_mod_check_verified.cancel()

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
                        "You have been banned from the Nerva community "
                        "server for having a blacklisted name."
                    )

                except (discord.Forbidden, discord.errors.Forbidden):
                    pass

                await member.ban(reason=f"Blacklisted name match.")

                await self.bot.automod_hook.send(
                    f"**{member}** matched against `{regex}`."
                )
                await self.bot.log_hook.send(
                    f"**{member}** has been banned for having a blacklisted name."
                )

                return

    @commands.Cog.listener()
    async def on_member_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        self.bot.log.info(
            f"Member update: {before.display_name} -> {after.display_name}"
        )

        if await before.guild.fetch_member(after.id) is None:
            return

        for regex in self.bot.config.NAME_BLACKLIST_REGEX:
            self.bot.log.info(
                f"Checking {after.display_name} against {regex} - "
                f"{bool(re.search(regex, after.display_name, re.IGNORECASE))}"
            )

            if re.search(regex, after.display_name, re.IGNORECASE):
                self.bot.log.info(
                    f"Banning {after} for having a blacklisted name match - {regex}."
                )

                try:
                    await after.send(
                        f"You have been banned from the Nerva community "
                        f"server for having a blacklisted name."
                    )

                except (discord.Forbidden, discord.errors.Forbidden):
                    pass

                await after.ban(reason=f"Blacklisted name match.")

                await self.bot.automod_hook.send(
                    f"**{after}** matched against `{regex}`."
                )
                await self.bot.log_hook.send(
                    f"**{after}** has been banned for having a blacklisted name."
                )

                return

        for role_id in self.bot.config.ADMIN_ROLE_IDS:
            role = after.guild.get_role(role_id)
            for member in role.members:
                if re.search(member.display_name, after.display_name, re.IGNORECASE):
                    self.bot.log.info(
                        f"Banning {after} for having an admins display name - {member.display_name}."
                    )

                    try:
                        await after.send(
                            f"You have been banned from the Nerva community "
                            f"server for having an admins display name."
                        )

                    except (discord.Forbidden, discord.errors.Forbidden):
                        pass

                    await after.ban(reason=f"Blacklisted name match.")

                    await self.bot.automod_hook.send(
                        f"**{after}** matched against `{member.display_name}`."
                    )
                    await self.bot.log_hook.send(
                        f"**{after}** has been banned for having an admins display name."
                    )

                    return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None:
            return

        if message.author.bot or is_admin(message.author):
            return

        for regex in self.bot.config.MESSAGE_BLACKLIST_REGEX:
            if re.search(regex, message.content, re.IGNORECASE):
                self.bot.log.info(
                    f"Deleting message from {message.author} for having a "
                    f"blacklisted message match - `{regex}`."
                )

                await message.delete()

                await self.bot.automod_hook.send(
                    f"**{message.author}**'s message matched against - `{regex}`."
                    f"Message content:\n"
                    f"```\n{message.content}\n```"
                )
                await self.bot.log_hook.send(
                    f"**{message.author}**'s message has been deleted "
                    f"for having a blacklisted message."
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
                        reason="3 warnings for blacklisted message matches."
                    )

                    await collection.delete_one({"_id": message.author.id})

                    await self.bot.log_hook.send(
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
                        f"Warning count: {warning_count}/3."
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
                    "verified": (
                        self.bot.config.VERIFIED_USER_ROLE_ID
                        in [role.id for role in message.author.roles]
                    ),
                    "tipped": False,
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
