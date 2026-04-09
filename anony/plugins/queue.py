# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types
from aiogram.filters import Command
from anony import dp, lang, queue
from anony.helpers import buttons


@dp.message(Command("queue", "q"))
@lang.language()
async def _queue(m: types.Message):
    chat_id = m.chat.id
    _queue = queue.get_queue(chat_id)
    if not _queue:
        return await m.reply(m.lang["not_playing"])

    text = m.lang["queue_curr"].format(
        _queue[0].url,
        _queue[0].title,
        _queue[0].duration,
        _queue[0].user,
    )

    if len(_queue) > 1:
        for i, item in enumerate(_queue[1:], start=1):
            text += m.lang["queue_item"].format(
                i,
                item.title[:20],
                item.duration,
            )
            if i == 10:
                break

    await m.reply(
        text=text,
        reply_markup=buttons.queue_markup(chat_id, "Close", True), # simplified
        disable_web_page_preview=True
    )
