# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from aiogram.filters import Command, Filter
from anony import dp, db, app

class SudoFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in app.sudoers

@dp.message(Command("ac", "activevc"), SudoFilter())
async def _activevc(m: types.Message, lang: dict):
    # Simplified list for migration
    await m.reply(lang["vc_list"])
