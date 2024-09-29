from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord import ui

from config import VERIFIED_USER_ROLE_ID

from .modals import VerificationModal

if TYPE_CHECKING:
    from motor import MotorCollection


class VerifyButton(ui.Button):
    def __init__(self, label="Verify!", **kwargs):
        super().__init__(label=label, **kwargs)

        self.style = discord.ButtonStyle.success
        self.collection: MotorCollection = Any

    async def callback(self, interaction: discord.Interaction):
        verified_role = interaction.guild.get_role(VERIFIED_USER_ROLE_ID)

        if verified_role in interaction.user.roles:
            # noinspection PyUnresolvedReferences
            return await interaction.response.send_message(
                "You are already verified!", ephemeral=True
            )

        modal = VerificationModal()
        modal.ctx = interaction
        modal.collection = self.collection

        # noinspection PyUnresolvedReferences
        await interaction.response.send_modal(modal)
        res = await modal.wait()

        if res:
            return
