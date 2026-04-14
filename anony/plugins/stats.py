# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types
from aiogram.filters import Command
from anony import dp, lang, db, app


@dp.message(Command("stats"))
async def stats_hndlr(m: types.Message, lang: dict):
    # Simplified stats for migration
    await m.reply(lang["stats_user"].format(app.name, 0, 0, 0, 0, 0, 0, 0))
