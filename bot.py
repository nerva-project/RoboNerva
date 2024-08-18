from __future__ import annotations
from typing import Any

import logging
from datetime import datetime
from itertools import cycle

import aiohttp
import motor

import discord
from discord.ext import commands

import config


class RoboNerva(commands.AutoShardedBot):
    user: discord.ClientUser
    db: motor.MotorDatabase
    bot_app_info: discord.AppInfo
    session: aiohttp.ClientSession
    log: logging.Logger

    def __init__(self):
        description = "FumeStop Community Manager."

        intents = discord.Intents.all()

        # noinspection PyTypeChecker
        super().__init__(
            command_prefix=commands.when_mentioned,
            description=description,
            heartbeat_timeout=180.0,
            intents=intents,
            help_command=None,
        )

        self._launch_time: datetime = Any
        self._status_items: cycle = Any

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        self.bot_app_info = await self.application_info()

        for _extension in self.config.INITIAL_EXTENSIONS:
            try:
                await self.load_extension(_extension)
                self.log.info(f"Loaded extension {_extension}.")

            except Exception as e:
                self.log.error(f"Failed to load extension {_extension}.", exc_info=e)

    async def on_ready(self) -> None:
        self._launch_time = datetime.now()

        await self.change_presence(
            status=discord.Status.online, activity=discord.Game("https://nerva.one")
        )

        await self.tree.sync(guild=discord.Object(id=self.config.COMMUNITY_GUILD_ID))

        self.log.info("RoboNerva is ready.")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.guild and message.guild.me in message.mentions:
            await message.reply(
                content="Hello there! I'm the <:nerva:1274417479606603776> community manager bot."
            )

    async def start(self, **kwargs) -> None:
        await super().start(config.TOKEN, reconnect=True)

    async def close(self) -> None:
        await super().close()
        await self.session.close()

    @property
    def config(self):
        return __import__("config")

    @property
    def embed_color(self) -> int:
        return self.config.EMBED_COLOR

    @property
    def launch_time(self) -> datetime:
        return self._launch_time

    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner

    @discord.utils.cached_property
    def webhook(self) -> discord.Webhook:
        return discord.Webhook.partial(
            id=self.config.WEBHOOK_ID,
            token=self.config.WEBHOOK_TOKEN,
            session=self.session,
        )
