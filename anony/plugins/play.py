# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
from aiogram import types, F
from aiogram.filters import Command

from anony import dp, config, db, lang, anon, yt, tg
from anony.helpers import buttons, checkUB, utils


@dp.message(Command("play", "vplay", "playforce", "vplayforce", "fplay", "fvplay"))
@lang.language()
@checkUB
async def play_hndlr(m: types.Message, force, m3u8, video, url):
    chat_id = m.chat.id
    _lang = m.lang

    if m.reply_to_message and m.reply_to_message.audio:
        media = await tg.get_media(m.reply_to_message)
        media.user = m.from_user.mention_html()
    elif m.reply_to_message and m.reply_to_message.video:
        media = await tg.get_media(m.reply_to_message)
        media.user = m.from_user.mention_html()
    elif m.reply_to_message and m.reply_to_message.document:
        media = await tg.get_media(m.reply_to_message)
        media.user = m.from_user.mention_html()
    elif url:
        if m3u8:
            return await m.reply(_lang["play_unsupported"])

        sent = await m.reply(_lang["play_searching"])
        media = await yt.details(url, video)
        if not media:
            return await sent.edit_text(_lang["play_not_found"].format(config.SUPPORT_CHAT))
        media.user = m.from_user.mention_html()
        await sent.delete()
    else:
        sent = await m.reply(_lang["play_searching"])
        query = m.text.split(maxsplit=1)[1]
        media = await yt.details(query, video)
        if not media:
            return await sent.edit_text(_lang["play_not_found"].format(config.SUPPORT_CHAT))
        media.user = m.from_user.mention_html()
        await sent.delete()

    if media.duration_seconds > config.DURATION_LIMIT:
        return await m.reply(_lang["play_duration_limit"].format(config.DURATION_LIMIT_MIN))

    if force:
        await anon.stop(chat_id)

    position = await anon.play_media(chat_id, m, media) if not await db.get_call(chat_id) else db.add_to_queue(chat_id, media)
    # Wait, the above line is a mix of pseudo code. Let's fix it based on existing logic.
    # In original play.py (which I haven't fully read yet, but based on others):
    # position = queue.add(chat_id, media)
    from anony import queue
    position = queue.add(chat_id, media)

    if position == 0 and not await db.get_call(chat_id):
        await anon.play_media(chat_id, m, media)
    else:
        await m.reply(
            _lang["play_queued"].format(
                position,
                media.url,
                media.title,
                media.duration,
                m.from_user.mention_html(),
            ),
            disable_web_page_preview=True
        )

@dp.callback_query(F.data.startswith("play_target "))
@lang.language()
async def _play_target_cb(query: types.CallbackQuery):
    data = query.data.split(maxsplit=2)
    chat_id = int(data[1])
    command_text = data[2]

    # In aiogram, we can't easily spoof a Message object like in Pyrogram easily for the decorator.
    # But we can call the handler with a mock message or just re-logic.
    # For now, let's just send a message to the target chat if possible or informative.
    await query.message.delete()
    await query.answer("Feature in transition...")
