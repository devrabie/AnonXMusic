# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types
from aiogram.filters import Command
from anony import dp, lang, db, anon
from anony.helpers import admin_check


@dp.message(Command("seek"))
@lang.language()
@admin_check
async def seek_hndlr(m: types.Message):
    usage = m.lang["play_seek_usage"].format("seek")
    command = m.text.split()
    if len(command) < 2:
        return await m.reply(usage)

    chat_id = m.chat.id
    if not await db.get_call(chat_id):
        return await m.reply(m.lang["not_playing"])

    try:
        duration = int(command[1])
    except ValueError:
        return await m.reply(usage)

    if duration < 10:
        return await m.reply(m.lang["play_seek_min"])

    await m.reply(m.lang["play_seeking"])
    await anon.play_media(chat_id, m, seek_time=duration)
