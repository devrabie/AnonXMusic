# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types
from aiogram.filters import Command
from anony import dp, lang, db, app


@dp.message(Command("restart"))
@lang.language()
async def restart_hndlr(m: types.Message):
    if str(m.from_user.id) != str(app.owner):
        return
    await m.reply(m.lang["restarting"])
    # Actual restart logic would go here
