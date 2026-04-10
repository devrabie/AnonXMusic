# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
from aiogram import types, F, enums
from aiogram.filters import Command

from anony import dp, config, db, app
from anony.helpers import buttons, checkUB, process_play


@dp.message(Command("play", "vplay", "playforce", "vplayforce", "fplay", "fvplay"))
@checkUB
async def play_hndlr(m: types.Message, lang: dict, force, m3u8, video, url):
    if m.chat.type == enums.ChatType.PRIVATE:
        chats = await db.get_chats(user_id=m.from_user.id)
        if not chats:
            return await m.reply(lang["no_chats"])

        chat_list = []
        for chat_id in chats:
            try:
                chat = await app.get_chat(chat_id)
                chat_list.append((chat_id, chat.title))
            except Exception:
                continue

        return await m.reply(
            lang["play_chat_selection"],
            reply_markup=buttons.play_chat_markup(lang, chat_list, m.text)
        )

    await process_play(m, lang, m.chat.id, m.text, video, force, url)
