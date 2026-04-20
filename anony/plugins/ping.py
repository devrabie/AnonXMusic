# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import time
import psutil
from aiogram import types
from aiogram.filters import Command
from anony import dp, anon, boot
from anony.helpers import buttons, utils


@dp.message(Command("ping"))
async def ping_hndlr(m: types.Message, lang: dict):
    start_time = time.time()
    sent = await m.reply(lang["pinging"])
    end_time = time.time()

    latency = round((end_time - start_time) * 1000, 2)
    uptime = utils.get_readable_time(int(time.time() - boot))
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    tg_latency = 0

    await sent.edit_text(
        text=lang["ping_pong"].format(
            latency, uptime, cpu, mem, disk, tg_latency
        ),
        reply_markup=buttons.ping_markup(lang["support"]),
    )
