# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from aiogram.filters import Command
from anony import dp, db, app


@dp.message(Command("resume"))
@admin_check
async def resume_hndlr(m: types.Message, lang: dict):
    if not await db.get_call(m.chat.id):
        return await m.reply(lang["not_playing"])
    if not await db.is_paused(m.chat.id):
        return await m.reply(lang["play_not_paused"])

    await anon.resume(m.chat.id)
    await m.reply(lang["play_resumed"].format(m.from_user.mention_html()))
