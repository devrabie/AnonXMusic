# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import asyncio
from aiogram import types, F
from aiogram.filters import Command, Filter
from aiogram.exceptions import TelegramRetryAfter

from anony import app, dp, db, logger

class SudoFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in app.sudoers

@dp.message(Command("broadcast"), SudoFilter())
async def _broadcast(message: types.Message, lang: dict):
    global broadcasting
    if not message.reply_to_message:
        return await message.reply(lang["gcast_usage"])

    if broadcasting:
        return await message.reply(lang["gcast_active"])

    msg = message.reply_to_message
    count, ucount = 0, 0
    chats, groups, users = [], [], []
    sent = await message.reply(lang["gcast_start"])

    command = message.text.split()
    if "-nochat" not in command:
        groups.extend(await db.get_chats())
    if "-user" in command:
        users.extend(await db.get_users())

    chats.extend(groups + users)
    broadcasting = True

    try:
        log_msg = await msg.send_copy(chat_id=app.logger_id)
        # await log_msg.pin()
        await app.send_message(
            chat_id=app.logger_id,
            text=lang["gcast_log"].format(
                message.from_user.id,
                message.from_user.mention_html(),
                message.text,
            )
        )
    except:
        pass

    await asyncio.sleep(2)

    failed = ""
    for chat in chats:
        if not broadcasting:
            await sent.edit_text(lang["gcast_stopped"].format(count, ucount))
            break

        try:
            if "-copy" in message.text:
                await msg.send_copy(chat_id=chat, reply_markup=msg.reply_markup)
            else:
                await msg.forward(chat_id=chat)

            if chat in groups:
                count += 1
            else:
                ucount += 1
            await asyncio.sleep(0.1)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 5)
        except Exception as ex:
            failed += f"{chat} - {ex}\n"
            continue

    text = lang["gcast_end"].format(count, ucount)
    if failed:
        from aiogram.types import BufferedInputFile
        await message.reply_document(
            document=BufferedInputFile(failed.encode(), filename="errors.txt"),
            caption=text,
        )
    else:
        await sent.edit_text(text)
    broadcasting = False


@dp.message(Command("stop_gcast", "stop_broadcast"), SudoFilter())
async def _stop_gcast(message: types.Message, lang: dict):
    global broadcasting
    if not broadcasting:
        return await message.reply(lang["gcast_inactive"])

    broadcasting = False
    try:
        await app.send_message(
            chat_id=app.logger_id,
            text=lang["gcast_stop_log"].format(
                message.from_user.id,
                message.from_user.mention_html()
            )
        )
    except:
        pass
    await message.reply(lang["gcast_stop"])

broadcasting = False
