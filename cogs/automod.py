from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime, UTC

from discord.ext import commands, tasks


if TYPE_CHECKING:
    from bot import RoboNerva

from config import COMMUNITY_GUILD_ID, UNVERIFIED_USER_ROLE_ID, VERIFIED_USER_ROLE_ID


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


async def setup(bot: RoboNerva) -> None:
    await bot.add_cog(AutoMod(bot))
