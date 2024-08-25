from __future__ import annotations
from typing import TYPE_CHECKING

import io
import inspect
import asyncio
import textwrap
import traceback
import subprocess
from contextlib import redirect_stdout

import discord
from discord import app_commands
from discord.ext import commands

from utils.tools import is_developer
from utils.modals import EvalModal, ExecModal

from config import COMMUNITY_GUILD_ID

if TYPE_CHECKING:
    from bot import RoboNerva


class Evaluate(commands.Cog):
    def __init__(self, bot: RoboNerva):
        self.bot: RoboNerva = bot

    # noinspection PyBroadException
    @app_commands.command(name="eval")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    async def _eval(self, ctx: discord.Interaction):
        """Evaluate a block of Python code."""
        if not is_developer(ctx.user):
            # noinspection PyUnresolvedReferences
            await ctx.response.send_message(
                content="Only developers can use this command.",
                ephemeral=True,
            )

        modal = EvalModal()
        modal.ctx = ctx

        # noinspection PyUnresolvedReferences
        await ctx.response.send_modal(modal)
        await modal.wait()

        env = {
            "discord": discord,
            "ctx": ctx,
            "bot": self.bot,
            "channel": ctx.channel,
            "user": ctx.user,
            "guild": ctx.guild,
            "message": ctx.message,
            "source": inspect.getsource,
            "asyncio": asyncio,
        }

        def _cleanup_code(content):
            content.replace("self.bot", "bot")

            if content.startswith("```") and content.endswith("```"):
                return "\n".join(content.split("\n")[1:-1])

            return content.strip("` \n")

        env.update(globals())

        body = _cleanup_code(modal.code.value)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        def _paginate(text: str):
            app_index = 0
            last = 0
            curr = 0
            pages = []

            for curr in range(0, len(text)):
                if curr % 1980 == 0:
                    pages.append(text[last:curr])
                    last = curr
                    app_index = curr

            if app_index != len(text) - 1:
                pages.append(text[last:curr])

            return list(filter(lambda a: a != "", pages))

        try:
            exec(to_compile, env)

        except Exception as e:
            await modal.interaction.edit_original_response(
                content=f"```py\n{e.__class__.__name__}: {e}\n```"
            )

        func = env["func"]

        try:
            with redirect_stdout(stdout):
                # noinspection PyUnresolvedReferences,PyArgumentList
                ret = await func()

        except Exception as _:
            value = stdout.getvalue()
            await modal.interaction.edit_original_response(
                content=f"```py\n{value}{traceback.format_exc()}\n```"
            )

        else:
            value = stdout.getvalue()

            if ret is None:
                if value:
                    try:
                        await modal.interaction.edit_original_response(
                            content=f"```py\n{value}\n```"
                        )

                    except Exception as _:
                        paginated_text = _paginate(value)

                        for page in paginated_text:
                            if page == paginated_text[-1]:
                                await modal.interaction.edit_original_response(
                                    content=f"```py\n{page}\n```"
                                )
                                break
                            await modal.interaction.edit_original_response(
                                content=f"```py\n{page}\n```"
                            )
                else:
                    await modal.interaction.edit_original_response(
                        content="\U00002705"
                    )

            else:
                try:
                    await modal.interaction.edit_original_response(
                        content=f"```py\n{value}{ret}\n```"
                    )

                except Exception as _:
                    paginated_text = _paginate(f"{value}{ret}")

                    for page in paginated_text:
                        if page == paginated_text[-1]:
                            await modal.interaction.edit_original_response(
                                content=f"```py\n{page}\n```"
                            )
                            break

                        await modal.interaction.edit_original_response(
                            content=f"```py\n{page}\n```"
                        )

    @app_commands.command(name="exec")
    @app_commands.guilds(COMMUNITY_GUILD_ID)
    async def _exec(self, ctx: discord.Interaction):
        """Execute a shell command."""
        if not is_developer(ctx.user):
            # noinspection PyUnresolvedReferences
            await ctx.response.send_message(
                content="Only developers can use this command.",
                ephemeral=True,
            )

        modal = ExecModal()
        modal.ctx = ctx

        # noinspection PyUnresolvedReferences
        await ctx.response.send_modal(modal)
        await modal.wait()

        process = subprocess.run(
            modal.sh_commands.value,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
        )

        stdout_value = process.stdout.decode("utf-8") + process.stderr.decode(
            "utf-8"
        )
        stdout_value = "\n".join(stdout_value.split("\n")[-25:])

        await modal.interaction.edit_original_response(
            content="```sh\n" + stdout_value + "```"
        )


async def setup(bot: RoboNerva):
    await bot.add_cog(Evaluate(bot))
