# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types
from aiogram.filters import Command
from anony import dp, lang, db, anon
from anony.helpers import admin_check


@dp.message(Command("resume"))
@lang.language()
@admin_check
async def resume_hndlr(m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply(m.lang["not_playing"])
    if not await db.is_paused(m.chat.id):
        return await m.reply(m.lang["play_not_paused"])

    await anon.resume(m.chat.id)
    await m.reply(m.lang["play_resumed"].format(m.from_user.mention_html()))
