# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
from aiogram import types, F, enums
from aiogram.filters import Command

from anony import dp, config, db, anon, yt, tg, queue, app
from anony.helpers import buttons, checkUB, utils


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

    chat_id = m.chat.id

    if m.reply_to_message and (m.reply_to_message.audio or m.reply_to_message.video or m.reply_to_message.document):
        sent = await m.reply(lang["play_downloading"])
        # We need to bridge aiogram and pyrogram for download.
        # For simplicity in this migration, let's just use yt.details for non-replies and fix this properly later if needed.
        # But wait, tg.download uses pyrogram types.
        # Let's use yt for searching for now if it's not a link.
        await sent.edit_text("Telegram media playback in transition...")
        return
    elif url:
        if m3u8:
            return await m.reply(lang["play_unsupported"])

        sent = await m.reply(lang["play_searching"])
        media = await yt.details(url, video)
        if not media:
            return await sent.edit_text(lang["play_not_found"].format(config.SUPPORT_CHAT))
        media.user = m.from_user.mention_html()
        await sent.delete()
    else:
        command_parts = m.text.split(maxsplit=1)
        if len(command_parts) < 2:
            return await m.reply(lang["play_usage"])

        sent = await m.reply(lang["play_searching"])
        query_text = command_parts[1]
        media = await yt.details(query_text, video)
        if not media:
            return await sent.edit_text(lang["play_not_found"].format(config.SUPPORT_CHAT))
        media.user = m.from_user.mention_html()
        await sent.delete()

    if media.duration_seconds > config.DURATION_LIMIT:
        return await m.reply(lang["play_duration_limit"].format(config.DURATION_LIMIT_MIN))

    if force:
        await anon.stop(chat_id)

    position = queue.add(chat_id, media)

    if position == 0 and not await db.get_call(chat_id):
        await anon.play_media(chat_id, m, media)
    else:
        await m.reply(
            lang["play_queued"].format(
                position,
                media.url,
                media.title,
                media.duration,
                m.from_user.mention_html(),
            ),
            disable_web_page_preview=True
        )
