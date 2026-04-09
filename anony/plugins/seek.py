# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types
from aiogram.filters import Command
from anony import dp, db, anon
from anony.helpers import admin_check


@dp.message(Command("seek"))
@admin_check
async def seek_hndlr(m: types.Message, lang: dict):
    usage = lang["play_seek_usage"].format("seek")
    command = m.text.split()
    if len(command) < 2:
        return await m.reply(usage)

    chat_id = m.chat.id
    if not await db.get_call(chat_id):
        return await m.reply(lang["not_playing"])

    try:
        duration = int(command[1])
    except ValueError:
        return await m.reply(usage)

    if duration < 10:
        return await m.reply(lang["play_seek_min"])

    await m.reply(lang["play_seeking"])
    await anon.play_media(chat_id, m, seek_time=duration)
