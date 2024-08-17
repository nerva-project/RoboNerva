from typing import Optional

import discord
from discord import app_commands


async def cooldown(
    ctx: discord.Interaction,
) -> Optional[app_commands.Cooldown]:
    if ctx.client.owner == ctx.user:
        return

    else:
        return app_commands.Cooldown(1, 5.0)
