# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
from aiogram import types, F
from aiogram.filters import Command
from anony import dp, app, logger


@dp.message(Command("logs"), F.from_user.id == int(app.owner))
async def logs_hndlr(m: types.Message, lang: dict):
    if not os.path.exists("log.txt"):
        return await m.reply(lang["log_not_found"])

    from aiogram.types import FSInputFile
    await m.reply_document(
        document=FSInputFile("log.txt"),
        caption=lang["log_sent"].format(app.name)
    )

@dp.message(Command("restart"), F.from_user.id == int(app.owner))
async def restart_hndlr(m: types.Message, lang: dict):
    await m.reply(lang["restarting"])
    os.system("pkill -f 'python3 -m anony' && python3 -m anony &")
