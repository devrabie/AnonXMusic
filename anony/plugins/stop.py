# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types
from aiogram.filters import Command
from anony import dp, lang, db, anon


@dp.message(Command("stop", "end"))
async def stop_hndlr(m: types.Message, lang: dict):
    if not await db.get_call(m.chat.id):
        return await m.reply(lang["not_playing"])

    await anon.stop(m.chat.id)
    await m.reply(lang["play_stopped"].format(m.from_user.mention_html()))
