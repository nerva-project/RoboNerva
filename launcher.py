from __future__ import annotations

import click
import logging
import asyncio
import contextlib
from datetime import datetime

import discord

from bot import RoboNerva

try:
    # noinspection PyUnresolvedReferences
    import uvloop

except ImportError:
    pass

else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name="discord.state")

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelname == "WARNING" and "referencing an unknown" in record.msg:
            return False
        return True


@contextlib.contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        handler = logging.FileHandler(
            filename=f"logs/robonerva-{datetime.now().strftime('%Y-%m-%d~%H-%M-%S')}.log",
            encoding="utf-8",
            mode="w",
        )

        discord.utils.setup_logging(handler=handler)

        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.WARNING)
        logging.getLogger("discord.state").addFilter(RemoveNoise())

        log.setLevel(logging.INFO)

        yield

    finally:
        handlers = log.handlers[:]
        for _handler in handlers:
            _handler.close()
            log.removeHandler(_handler)


async def run_bot():
    log = logging.getLogger()

    async with RoboNerva() as bot:
        bot.log = log
        await bot.start()


@click.group(invoke_without_command=True, options_metavar="[options]")
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        with setup_logging():
            asyncio.run(run_bot())


if __name__ == "__main__":
    main()
