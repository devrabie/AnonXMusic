# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
from aiogram import types, F
from aiogram.filters import Command

from anony import dp, config, db, anon, yt, tg, queue
from anony.helpers import buttons, checkUB, utils


@dp.message(Command("play", "vplay", "playforce", "vplayforce", "fplay", "fvplay"))
@checkUB
async def play_hndlr(m: types.Message, lang: dict, force, m3u8, video, url):
    chat_id = m.chat.id

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
            return await m.reply(lang["play_unsupported"])

        sent = await m.reply(lang["play_searching"])
        media = await yt.details(url, video)
        if not media:
            return await sent.edit_text(lang["play_not_found"].format(config.SUPPORT_CHAT))
        media.user = m.from_user.mention_html()
        await sent.delete()
    else:
        sent = await m.reply(lang["play_searching"])
        query_text = m.text.split(maxsplit=1)[1]
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
