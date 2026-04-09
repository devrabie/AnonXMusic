# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types
from aiogram.filters import Command
from anony import dp, lang, db, anon
from anony.helpers import admin_check


@dp.message(Command("loop"))
@lang.language()
@admin_check
async def loop_hndlr(m: types.Message):
    usage = m.lang["loop_usage"]
    command = m.text.split()
    if len(command) < 2:
        return await m.reply(usage)

    chat_id = m.chat.id
    state = command[1].lower()
    if state == "off":
        await db.set_loop(chat_id, 0)
        return await m.reply(m.lang["loop_off"])

    try:
        count = int(state)
        if count < 1 or count > 10:
            return await m.reply(usage)
        await db.set_loop(chat_id, count)
        await m.reply(m.lang["loop_set"].format(count))
    except ValueError:
        await m.reply(usage)
