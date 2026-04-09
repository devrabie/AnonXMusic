# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from aiogram.filters import Command
from anony import dp, db, app


@dp.message(Command("blacklist", "unblacklist"))
async def blacklist_hndlr(m: types.Message, lang: dict):
    if m.from_user.id != int(app.owner):
        return

    command = m.text.split()
    if len(command) < 2:
        return await m.reply(lang["bl_usage"].format(command[0][1:]))

    target = int(command[1])
    if "un" in command[0]:
        await db.unblacklist_chat(target)
        await m.reply(lang["bl_removed"])
    else:
        await db.blacklist_chat(target)
        await m.reply(lang["bl_added"])
